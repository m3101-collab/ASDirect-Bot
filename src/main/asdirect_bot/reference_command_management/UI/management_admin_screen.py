import discord as dc
import re

from  ...generic_client import Client
from ..persistence import Command
from ..sync_commands import sync_guild

commandname = re.compile(r'[a-z0-9_]+')

class View(dc.ui.View):
    def __init__(self, client:Client, *, timeout: float|None = None):
        super().__init__(timeout=timeout)
        self.client=client
    @dc.ui.button(
        label="New command"
    )
    async def newcommand(self,interaction:dc.Interaction,button:dc.ui.Button):
        await interaction.response.send_modal(CommandModal(self.client))
    @dc.ui.button(
        label="Manage existing\ncommand"
    )
    async def managecommand(self,interaction:dc.Interaction,button:dc.ui.Button):
        await interaction.response.edit_message(view=None,content="TODO")

class CommandModal(dc.ui.Modal, title = "Command Management"):
    name = dc.ui.TextInput(
        label="Command name",
        style=dc.TextStyle.short,
        placeholder="show_rule_11"
    )
    description = dc.ui.TextInput(
        label="Command description",
        style=dc.TextStyle.long,
        placeholder="Displays a link to Rule 11, as well as a summary"
    )
    cmd_title = dc.ui.TextInput(
        label="Title of the message",
        style=dc.TextStyle.short,
        placeholder="Rule 11"
    )
    reference = dc.ui.TextInput(
        label="Message that'll be shown",
        style=dc.TextStyle.paragraph,
        placeholder="Polarising topics are banned.\nMore information can be found in our FAQ: <#1127949243840204831>"
    )
    image = dc.ui.TextInput(
        label="Image URL (Optional)",
        style=dc.TextStyle.short,
        required=False
    )

    def __init__(self, client:Client, *, title: str = "Command Management", timeout: float | None = None) -> None:
        super().__init__(title=title, timeout=timeout)
        self.client=client

    async def on_submit(self, interaction: dc.Interaction) -> None:
        if commandname.match(self.name.value) is None:
            await interaction.response.edit_message(
                view=None,
                content="Invalid command name.\nIt must be alphanumeric, plus underscores (\\_).\nE.g. mycommand, my_command, command0"
            )
        else:
            await self.client.reference_command_persistence.update_command(
                interaction.guild_id,
                Command(
                    title=self.cmd_title.value,
                    text_content=self.reference.value,
                    description=self.description.value,
                    image=self.image.value
                ),
                self.name.value
            )
            self.client.reference_command_persistence.save_to_json(self.client.reference_command_path)
            await sync_guild(self.client,interaction.guild_id)
            await interaction.response.edit_message(
                view=None,
                content="Command added!"
            )