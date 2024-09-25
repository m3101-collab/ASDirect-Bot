from ..generic_client import Client
import discord as dc
from .persistence import Command
from ..permissions_mgt.persistence import Permissions
from.discord_commands import RUN_CMD_PERM

def gen_command_callback(client:Client,command:Command):
    async def handle_interaction(interaction:dc.Interaction):
        allowed,why = Permissions.check(client,interaction,{RUN_CMD_PERM.identifier})
        if not allowed:
            client.logger.warning(f"Blocked attempt to run custom command ({command['title']}) by uid {interaction.user.id} ({interaction.user.name}/{interaction.user.display_name})")
            await interaction.response.send_message(
                content=(
                    "You're not allowed to run this command. This attempt has been logged.\n"
                    f"Reason: {why}"
                ),
                ephemeral=True
            )
            return
        content = command['text_content']
        content = content if content!="." else ""
        if command['image'] is None:
            await interaction.response.send_message(
                content=content,
                embed=dc.Embed(
                    title = command['title'],
                )
            )
        else:
            await interaction.response.send_message(
                content=content,
                embed=dc.Embed(
                    title = command['title'],
                ).set_image(url=command['image'])
            )
    return handle_interaction

async def sync_guild(client:Client, guild_id:int):
    if str(guild_id) not in client.reference_command_persistence.servers:
        client.reference_command_persistence.servers[str(guild_id)] = {}
        #raise LookupError("This server hasn't been configured yet!")
    guild_snowflake = dc.Object(guild_id,type=dc.Guild)
    commands = client.reference_command_persistence.servers[str(guild_id)]
    skip = set()
    #client.command_tree.clear_commands(guild=guild_snowflake)
    for command in client.command_tree.get_commands(guild=guild_snowflake):
        if type(command) is dc.app_commands.Command:
            skip.add(command.name)
    if len(commands)>0:
        for name,command in commands.items():
            client.logger.info(f"Registering {name}")
            if name in skip:
                continue
            client.command_tree.command(
                name=name,
                description=command['description'],
                guild=guild_snowflake
            )(
                gen_command_callback(client,command)
            )
        await client.command_tree.sync(guild=guild_snowflake)