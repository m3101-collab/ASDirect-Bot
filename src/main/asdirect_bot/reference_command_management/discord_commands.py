import discord as dc
from ..generic_client import Client
from .sync_commands import sync_guild
from . import permissions
from .UI import management_admin_screen
from .sync_commands import sync_guild
import logging

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
        #TODO: Check for advanced permissions
        if not permissions.has_permission(interaction,{'admin'}):
            await interaction.response.send_message(
                ephemeral=True,
                content = "You do not have access to this command!\n"
                "Currently, only admins can run this command."
            )
            return
        await interaction.response.send_message(
            ephemeral=True,
            content="# Reference command admin menu",
            view=management_admin_screen.View(client)
        )
    return handler

async def setup(client:Client, logger: logging.Logger):
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
    await client.command_tree.sync()
    async for guild in client.fetch_guilds():
        client.command_tree.clear_commands(guild=guild)
        await sync_guild(client,guild.id)

    logger.info("Sync sent. It might take up to 1h for global commands to update.")