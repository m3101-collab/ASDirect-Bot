import json
import discord as dc
from ..generic_client import Client
from datetime import datetime,timedelta
from . import persistence as pers
from typing import List,Tuple,Dict,Callable,Coroutine,Any,Literal
import re
from logging import Logger
import asyncio

class Timer:
    def __init__(self, timeout, callback):
        self._timeout = timeout
        self._callback = callback
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback()

    def cancel(self):
        self._task.cancel()

async def handle_sendmesssage(logger:Logger,client:Client,command:pers.MessageCommandParams, guild_id:int, command_name:str):
    guild = client.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(command['channel_id'])
    if channel is None:
        return
    logger.info(f"Sending message at guild {guild.name}, channel {channel.name}")
    content:str = command['message']
    pools = client.periodic_events.get('servers',{}).get(str(guild_id),{}).get('pools',{})
    used_pools = {}
    for match in re.finditer(r"%%(.*?)%%",content):
        name = match.group(1)
        if name in used_pools:
            content = content.replace(f"%%{name}%%",used_pools[name])
        elif name in pools:
            pool:pers.MessagePool = pools[name]
            replacement = pool['defaultmessage']
            if len(pool['messages'])!=0:
                replacement = pool['messages'][0]
                pool['messages']=pool['messages'][1:]
                if pool['mode']=='Cycle':
                    pool['messages'].append(replacement)
                with open(client.periodic_events_path,'w') as o_f:
                    json.dump(client.periodic_events,o_f)
            content = content.replace(f"%%{name}%%",replacement)
            used_pools[name]=replacement
    try:
        await channel.send(
            content=content,
            embed = (
                dc.Embed(type='image').set_image(url=command['image'])
                if (('image' in command) and (command['image'] is not None)) else None
            )
        )
    except dc.errors.Forbidden as e:
        logger.error(f"Permissions insufficient for sending messages at guild {guild.name} (channel #{channel.name}) - {e.status} Code {e.code} {e.text}")

async def handle_changeperms(logger:Logger,client:Client,command:pers.ChannelPermissionCommandParams,guild_id:int, command_name:str):
    guild = client.get_guild(guild_id)
    if guild is None:
        return
    channel = guild.get_channel(command['channel_id'])
    if channel is None:
        return
    logger.info(f"Updating permissions at guild {guild.name}, channel {channel.name}")
    for role_id in command['role_ids']:
        role = guild.get_role(role_id)
        if role is not None:
            current = {
                perm:getattr(perms,perm)
                for perms in [channel.permissions_for(role)]
                for perm in pers.PERMISSION_NAMES
            }
            try: 
                await channel.set_permissions(
                    role,
                    reason=f"Scheduled command \"{command_name}\"",
                    **(
                        current
                        |{
                            name:True
                            for name in command.get('permissions_to_add',[])
                        }
                        |{
                            name:False
                            for name in command.get('permissions_to_remove',[])
                        }
                    )
                )
            except dc.errors.Forbidden as e:
                logger.error(f"Permissions insufficient for setting roles at guild {guild.name} (channel #{channel.name}) - {e.status} Code {e.code} {e.text}")
                return

class Scheduler:
    handlers:Dict[str,Callable[[Logger,Client,Any,int,str],Coroutine]] =   {
        "Send Message":handle_sendmesssage,
        "Change Channel Permissions":handle_changeperms
    }
    def __init__(self,logger:Logger) -> None:
        self.timer:Timer|None = None
        self.logger=logger
        self.scheduled:None|List[Tuple[datetime,str,pers.ScheduledAction,int]] = None
    async def check_schedules(self,client:Client):
        ran = False
        now = datetime.now()
        if self.scheduled is not None:
            for time,name,action,guild in self.scheduled:
                if time<=now:
                    for command in action['commands']:
                        if command['type'] in Scheduler.handlers:
                           ran=True
                           await Scheduler.handlers[command['type']](
                                self.logger,
                                client,
                                command['params'],
                                guild,
                                name
                           )
                        else:
                           self.logger.warn(f"No handler for command type \"{command['type']}\"")
                else:
                    break
        seconds_till_next = (
            60*60 if (
                (self.scheduled is None)
                or
                (len(self.scheduled)==0)
            ) else (
                (self.scheduled[0][0]-now).total_seconds()
            )
        )
        self.timer = Timer(
            min(60*60,seconds_till_next),
            (lambda:self.check_schedules(client))
            if not ran
            else
            (lambda:self.reschedule(client))
        )
    async def reschedule(self,client:Client):
        if self.timer is not None:
            try:
                self.timer.cancel()
            except:
                pass
        self.scheduled = resolve_schedules(client)
        if len(self.scheduled)>0:
            self.logger.info(f"Rescheduling events... Next event is at {self.scheduled[0][0]}")
        await self.check_schedules(client)

def set_datetime(base:datetime,year:None|int = None, month:None|int = None,day:None|int = None, hour:None|int=None)->datetime:
    return datetime(
        base.year if year is None else year,
        base.month if month is None else month,
        base.day if day is None else day,
        base.hour if hour is None else hour
    )
def weekday_to_datetime_num(
    weekday:Literal[
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    ]
)->int:
    return {
        "Sunday":6,
        "Monday":0,
        "Tuesday":1,
        "Wednesday":2,
        "Thursday":3,
        "Friday":4,
        "Saturday":5
    }[weekday]
def next_occurrence(now:datetime,schedule:pers.Schedule)->datetime:
    if schedule['recurrence']=='Daily':
        date = set_datetime(now,hour=schedule['date'].get('hour',0))
        if date<now:
            date += timedelta(days=1)
        return date
    elif schedule['recurrence']=='Weekly':
        date = set_datetime(
            now,
            hour=schedule['date'].get('hour',0)
        )
        weekday = weekday_to_datetime_num(schedule['date'].get('weekday','Monday'))
        if date.weekday()==weekday:
            if date<now:
                date+=timedelta(weeks=1)
            return date
        else:
            difference = (weekday-date.weekday())%7
            return date+timedelta(days=difference)
    elif schedule['recurrence']=='Monthly':
        date = set_datetime(
            now,
            hour=schedule['date'].get('hour',0),
            day=schedule['date'].get('day',1)
        )
        if(date<now):
            date = date+timedelta(weeks=4)
        return date
    elif schedule['recurrence']=='Yearly':
        date = set_datetime(
            now,
            month=schedule['date'].get('month',1),
            hour=schedule['date'].get('hour',0),
            day=schedule['date'].get('day',1)
        )
        if(date<now):
            date = date+timedelta(days=365)
        return date
def resolve_schedules(client:Client) -> List[Tuple[datetime,str,pers.ScheduledAction,int]]:
    if not hasattr(client,"periodic_events"):
        return []
    servers:Dict[int,pers.Server] = client.periodic_events.get('servers',{})
    now = datetime.now()
    return sorted([
        (schedule,name,action,int(id))
        for id,val in servers.items()
        for name,event in val['events'].items()
        for action in event['actions']
        for schedule in [sorted([next_occurrence(now,schedule) for schedule in action['schedules']])[0]]
    ])