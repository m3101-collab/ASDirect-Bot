import logging
from typing import Type
from ..generic_client import Client
import discord as dc
from . import ui
from . import persistence as pers
from . import scheduler
import os
import pathlib as pl
import json
GENERIC_CLIENT_MODULE_NAME="EventManager"
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
            json.dump(client.periodic_events,o_f)
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

    client.command_tree.add_command(eventcommands)
async def test(interaction:dc.Interaction):
    await interaction.response.send_message(
        embed=dc.Embed(
            type='image'
        ).set_image(url="https://media.discordapp.net/attachments/638765872306978837/1254198989373575380/vK6ME3h.png?ex=66da2e54&is=66d8dcd4&hm=506a12c906f4198bff57d94b4f6e95fe055352de752be14eecf65be63f47c047")
    )
def add_event(client:Client):
    async def closure(interaction: dc.Interaction):
        if not interaction.user.resolved_permissions.administrator:
            await interaction.response.send_message(
                content="You must be an administrator.",
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
        if interaction.guild_id not in client.periodic_events['servers']:
            client.periodic_events['servers'][str(interaction.guild_id)]={
                'events':{},
                'pools':{}
            }
        client.periodic_events['servers'][str(interaction.guild_id)]['events'][evt['name']]=evt
        with open(client.periodic_events_path,'w') as o_f:
            json.dump(client.periodic_events,o_f)
        client.scheduler.reschedule(client)
        await interaction.response.edit_message(content="Aight. Seems to be werkin'.",view=None)
    return closure
def message_pools(client:Client):
    async def closure(interaction:dc.Interaction):
        if not interaction.user.resolved_permissions.administrator:
            await interaction.response.send_message(
                content="You must be an administrator.",
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
                        json.dump(client.periodic_events,o_f)
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
                if interaction.guild_id not in client.periodic_events['servers']:
                    client.periodic_events['servers'][interaction.guild_id]={
                        'events':{},
                        'pools':{}
                    }
                client.periodic_events['servers'][str(interaction.guild_id)]['pools'][pool['name']]=pool
                with open(client.periodic_events_path,'w') as o_f:
                    json.dump(client.periodic_events,o_f)
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