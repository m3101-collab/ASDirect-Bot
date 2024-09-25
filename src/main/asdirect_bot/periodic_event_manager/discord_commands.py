import logging
from typing import Type,Callable,Any,Set,Coroutine
from ..generic_client import Client
import discord as dc
from . import ui
from . import persistence as pers
from . import scheduler
import os
import pathlib as pl
import json
from ..permissions_mgt.persistence import permission,Permissions
from ..periodic_event_manager.ui import ArbitrarySetView

GENERIC_CLIENT_MODULE_NAME="EventManager"

CREATE_EVENT_PERM = permission("Create and manage events/scheduled commands","CREVT")
MSG_POOL_PERM = permission("Create and manage message pools for events","CREVTP")
async def setup(client:Client, logger: logging.Logger):
    logger.info("Setting up event management commands.")
    events_path = os.environ.get("EVENTS_PATH")
    if events_path is None:
        raise LookupError("Environment variable EVENTS_PATH not found!")
    client.periodic_events = {'servers':{}}
    if pl.Path(events_path).exists():
        with open(events_path,'r') as i_f:
            client.periodic_events = json.load(i_f)
    else:
        with open(events_path,'w') as o_f:
            json.dump(client.periodic_events,o_f,indent=4)
    client.periodic_events_path = events_path
    client.scheduler = scheduler.Scheduler(logger)
    await client.scheduler.reschedule(client)

    eventcommands = dc.app_commands.Group(
        name = "event",
        description = "Recurring event management commands"
    )
    eventcommands.command(
        name="add",
        description="Creates a new Event"
    )(add_event(client))

    eventcommands.command(
        name="pool",
        description="Manage message pools"
    )(message_pools(client))

    eventcommands.command(
        name="toggle",
        description="Opens an interface to toggle events on and off"
    )(enable_disable_events(client))

    client.command_tree.add_command(eventcommands)
async def test(interaction:dc.Interaction):
    await interaction.response.send_message(
        embed=dc.Embed(
            type='image'
        ).set_image(url="https://media.discordapp.net/attachments/638765872306978837/1254198989373575380/vK6ME3h.png?ex=66da2e54&is=66d8dcd4&hm=506a12c906f4198bff57d94b4f6e95fe055352de752be14eecf65be63f47c047")
    )

class EnableDisableView(ArbitrarySetView):
    def describe(self) -> str:
        return (
            "Current events' automation/scheduling status:\n"
            +
            '\n'.join([f"- {evt}: **{'✅Enabled' if evt in self.enabled else '❌ Disabled'}**" for evt in self.events])
            +
            "\nSelect an event below to toggle its status:"
        )
    def __init__(self, client:Client, events:Set[str], enabled:Set[str], cb: Callable[[dc.Interaction[Client], None], Coroutine[None, None, None]], type: Type = None, *, req: str = "", timeout: float | None = None, original_interaction: dc.Interaction[dc.Client]):
        super().__init__(self.done_cb, "permission", events, type, "", req=req, timeout=timeout, original_interaction=original_interaction)
        self.events=events
        self.enabled=enabled
        self.client=client
        self.final_cb = cb
    def confirmed(self):
        return []
    async def done_cb(self,interaction:dc.Interaction,sel:Set[str]):
        persistence:pers.Persistence = self.client.periodic_events
        guild = str(interaction.guild_id)
        if guild not in persistence["servers"]:
            await interaction.response.edit_message(
                content="This server has no configured events.",
                view=None
            )
            return
        for event in self.events:
            persistence['servers'][guild]['events'][event]['enabled']=event in self.enabled
        persistence_path = os.environ.get("EVENTS_PATH")
        if persistence_path is None:
            raise LookupError("Environment variable EVENTS_PATH not found!")
        with open(persistence_path,'w') as o_f:
            json.dump(persistence,o_f,indent=4)
        sched:scheduler.Scheduler = self.client.scheduler
        await sched.reschedule(self.client)
        await self.final_cb(interaction,None)
    async def selected_cb(self,sel:Set[str],interaction:dc.Interaction):
        selected = sel[0]
        if selected in self.enabled:
            self.enabled.remove(selected)
        else:
            self.enabled.add(selected)
        await interaction.response.edit_message(
            content = self.describe()
        )
def enable_disable_events(client:Client):
    async def closure(interaction:dc.Interaction):
        allowed,why = Permissions.check(client,interaction,{CREATE_EVENT_PERM.identifier})
        if not allowed:
            client.logger.warning(f"Blocked attempt to run enable_disable_events by uid {interaction.user.id} ({interaction.user.name}/{interaction.user.display_name})")
            await interaction.response.send_message(
                content=(
                    "You're not allowed to run this command. This attempt has been logged.\n"
                    f"Reason: {why}"
                ),
                ephemeral=True
            )
            return
        persistence:pers.Persistence = client.periodic_events
        view = EnableDisableView(
            client,
            set(persistence.get('servers',{})
            .get(str(interaction.guild_id),{})
            .get('events',{})),
            set(
                event
                for event in 
                persistence.get('servers',{})
                .get(str(interaction.guild_id),{})
                .get('events',{})
                if persistence.get('servers',{})
                .get(str(interaction.guild_id),{})
                .get('events',{}).get(event,{}).get('enabled',False)
            ),
            done,
            original_interaction=interaction
        )
        await interaction.response.send_message(
            ephemeral=True,
            content=view.describe(),
            view=view
        )
    return closure
async def done(interaction:dc.Interaction,whatever:Any):
    await interaction.response.edit_message(view=None,content="All set! Please dismiss this message.")

def add_event(client:Client):
    async def closure(interaction: dc.Interaction):
        allowed,why = Permissions.check(client,interaction,{CREATE_EVENT_PERM.identifier})
        if not allowed:
            client.logger.warning(f"Blocked attempt to run add_event by uid {interaction.user.id} ({interaction.user.name}/{interaction.user.display_name})")
            await interaction.response.send_message(
                content=(
                    "You're not allowed to run this command. This attempt has been logged.\n"
                    f"Reason: {why}"
                ),
                ephemeral=True
            )
            return
        view = ui.EventView(add_event_response(client),pers.Event,original_interaction=interaction)
        await interaction.response.send_message(
            content=view.describe(),
            view = view,
            ephemeral=True
        )
    return closure
def add_event_response(client:Client):
    async def closure(interaction: dc.Interaction, evt:pers.Event):
        evt = ui.aui.cleanup_dict(evt)
        if str(interaction.guild_id) not in client.periodic_events['servers']:
            client.periodic_events['servers'][str(interaction.guild_id)]={
                'events':{},
                'pools':{}
            }
        client.periodic_events['servers'][str(interaction.guild_id)]['events'][evt['name']]=evt
        with open(client.periodic_events_path,'w') as o_f:
            json.dump(client.periodic_events,o_f,indent=4)
        client.scheduler.reschedule(client)
        await interaction.response.edit_message(content="Aight. Seems to be werkin'.",view=None)
    return closure
def message_pools(client:Client):
    async def closure(interaction:dc.Interaction):
        allowed,why = Permissions.check(client,interaction,{MSG_POOL_PERM.identifier})
        if not allowed:
            client.logger.warning(f"Blocked attempt to run message_pools by uid {interaction.user.id} ({interaction.user.name}/{interaction.user.display_name})")
            await interaction.response.send_message(
                content=(
                    "You're not allowed to run this command. This attempt has been logged.\n"
                    f"Reason: {why}"
                ),
                ephemeral=True
            )
            return
        class AddToPoolView(ui.aui.BaseEditView):
            def confirmed(self):
                return self.pool
            def __init__(self, cb,pool:pers.MessagePool, type: Type = None, content: str = "", *, req: str = "", timeout: float | None = None, original_interaction: dc.Interaction[dc.Client]):
                super().__init__(cb, type, content, req=req, timeout=timeout, original_interaction=original_interaction)
                self.pool=pool
                if "messages" not in self.pool:
                    self.pool['messages']=[]
            def describe(self) -> str:
                return (
                    f"Pool {self.pool['name']}\n"
                    f"Current default message:\n```{self.pool['defaultmessage']}```\n"
                    f"Messages:\n"
                    +"\n".join([
                        f"```{message}```"
                        for message in self.pool['messages']
                    ])
                )
            @dc.ui.button(label="Add Message")
            async def add_msg(self,interaction:dc.Interaction,but):
                view=ui.aui.LongStrView(self.addmsgcb,original_interaction=interaction)
                await interaction.response.edit_message(
                    content=view.describe(),
                    view=view
                )
            async def addmsgcb(self,interaction:dc.Interaction,msg:str|None):
                if msg is not None:
                    self.pool['messages'].append(msg)
                await interaction.response.edit_message(
                    content=self.describe(),
                    view=self
                )
            @dc.ui.button(label="Change Default Message")
            async def change_default_message(self,interaction:dc.Interaction,but):
                view=ui.aui.LongStrView(self.chngmsgcb,original_interaction=interaction)
                await interaction.response.edit_message(
                    content=view.describe(),
                    view=view
                )
            async def chngmsgcb(self,interaction:dc.Interaction,msg:str|None):
                if msg is not None:
                    self.pool['defaultmessage']=msg
                await interaction.response.edit_message(
                    content=self.describe(),
                    view=self
                )
        class AddMsgView(ui.aui.BaseEditView):
            def describe(self) -> str:
                return "Select a pool to edit"
            def __init__(self, cb, type: Type = None, content: str = "", *, req: str = "", timeout: float | None = None, original_interaction: dc.Interaction[dc.Client]):
                super().__init__(cb, type, content, req=req, timeout=timeout, original_interaction=original_interaction)
                self.pools = client.periodic_events.get('servers',{}).get(str(interaction.guild_id),{'pools':{}})['pools']
                self.selector = ui.aui.CBSelect(
                    self.selected,
                    options=[
                        dc.SelectOption(label=pool,value=pool,description="")
                        for pool in self.pools|{"Don't click this":{}}
                    ]
                )
                self.add_item(self.selector)
            async def selected(self,selected:list[str],interaction:dc.Interaction):
                view = AddToPoolView(self.finished,self.pools[selected[0]],original_interaction=interaction)
                await interaction.response.edit_message(
                    content=view.describe(),
                    view=view
                )
            async def finished(self,interaction:dc.Interaction,pool:pers.MessagePool|None):
                if pool is not None:
                    client.periodic_events['servers'][str(interaction.guild_id)]['pools'][pool['name']]=pool
                    with open(client.periodic_events_path,'w') as o_f:
                        json.dump(client.periodic_events,o_f,indent=4)
                await interaction.response.edit_message(
                    content=self.describe(),
                    view=self
                )
        class Menu(dc.ui.View):
            @dc.ui.button(label="Add messages to an existing pool")
            async def add_message_to_pool(self,interaction:dc.Interaction,but):
                view = AddMsgView(self.done_adding,original_interaction=interaction)
                await interaction.response.edit_message(
                    content=view.describe(),
                    view=view
                )
            @dc.ui.button(label="Create a new pool")
            async def newpool(self,interaction:dc.Interaction,but):
                view = ui.PoolView(self.pool_made,pers.MessagePool,original_interaction=interaction)
                await interaction.response.edit_message(
                    content=view.describe(),
                    view=view
                )
            async def pool_made(self,interaction:dc.Interaction,pool:pers.MessagePool):
                pool=ui.aui.cleanup_dict(pool)
                if str(interaction.guild_id) not in client.periodic_events['servers']:
                    client.periodic_events['servers'][str(interaction.guild_id)]={
                        'events':{},
                        'pools':{}
                    }
                client.periodic_events['servers'][str(interaction.guild_id)]['pools'][pool['name']]=pool
                with open(client.periodic_events_path,'w') as o_f:
                    json.dump(client.periodic_events,o_f,indent=4)
                await self.done_adding(interaction,pool)
            async def done_adding(self,interaction:dc.Interaction,whatevs):
                await interaction.response.edit_message(
                    content="Message Pool Menu",
                    view=self
                )
        await interaction.response.send_message(
            content="Message Pool menu",
            view=Menu(),
            ephemeral=True
        )
    return closure