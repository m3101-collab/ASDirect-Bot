from ..permissions_mgt.persistence import Permissions,permission
RUN_CMD_PERM = permission("Run custom bot commands","RCMD")
CREATE_CMD_PERM = permission("Create new custom commands","CCMD")
import discord as dc
import os
from ..generic_client import Client
from .sync_commands import sync_guild
from .persistence import Database
from .UI import management_admin_screen
from .sync_commands import sync_guild
import logging
import pathlib as pl

GENERIC_CLIENT_MODULE_NAME = "ReferenceCommands"


def sync_commands(client:Client):
    async def handler(interaction: dc.Interaction):
        try:
            await sync_guild(client,interaction.guild_id)
        except LookupError as e:
            await interaction.response.send_message(
                ephemeral=True,
                content=e.message
            )
            return
        await interaction.response.send_message(
            ephemeral=True,
            content="Sync successful!"
        )
    return handler
def management_screen(client:Client):
    async def handler(interaction: dc.Interaction):
        allowed,why = Permissions.check(client,interaction,{CREATE_CMD_PERM.identifier})
        if not allowed:
            client.logger.warning(f"Blocked attempt to run management_screen (command creation) by uid {interaction.user.id} ({interaction.user.name}/{interaction.user.display_name})")
            await interaction.response.send_message(
                content=(
                    "You're not allowed to run this command. This attempt has been logged.\n"
                    f"Reason: {why}"
                ),
                ephemeral=True
            )
            return
        await interaction.response.send_message(
            ephemeral=True,
            content="# Reference command admin menu",
            view=management_admin_screen.View(client)
        )
    return handler

async def setup(client:Client, logger: logging.Logger):
    ref_command_path = os.environ.get("REF_COMMANDS_PATH")
    if ref_command_path is None:
        raise LookupError("Environment variable REF_COMMANDS_PATH not found!")
    client.reference_command_persistence = Database()
    if pl.Path(ref_command_path).exists():
        await client.reference_command_persistence.load_from_json(ref_command_path)
    else:
        client.reference_command_persistence.save_to_json(ref_command_path)
    client.reference_command_path = ref_command_path
    logger.info("Setting up reference commands.")
    parent = dc.app_commands.Group(
        name="referencecommands",
        description="Commands for managing the \"Reference Commands\" module of the bot."
    )
    parent.command(
        name="sync",
        description="Prompts discord to update the available server commands."
    )(sync_commands(client))
    parent.command(
        name="manage",
        description="Opens a menu to create, edit and delete reference commands"
    )(management_screen(client))
    client.command_tree.add_command(parent)
    async for guild in client.fetch_guilds():
        client.command_tree.clear_commands(guild=guild)
        await sync_guild(client,guild.id)
