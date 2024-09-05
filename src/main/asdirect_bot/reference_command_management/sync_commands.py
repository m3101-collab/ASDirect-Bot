from ..generic_client import Client
import discord as dc
from .persistence import Command

def gen_command_callback(command:Command):
    async def handle_interaction(interaction:dc.Interaction):
        if command['image'] is None:
            await interaction.response.send_message(
                embed=dc.Embed(
                    title = command['title'],
                ).add_field(
                    name = "",
                    value = command['text_content']
                )
            )
        else:
            await interaction.response.send_message(
                embed=dc.Embed(
                    title = command['title'],
                ).add_field(
                    name = "",
                    value = command['text_content']
                ).set_image(url=command['image'])
            )
    return handle_interaction

async def sync_guild(client:Client, guild_id:int):
    if guild_id not in client.reference_command_persistence.servers:
        client.reference_command_persistence.servers[guild_id] = {}
        #raise LookupError("This server hasn't been configured yet!")
    guild_snowflake = dc.Object(guild_id,type=dc.Guild)
    commands = client.reference_command_persistence.servers[guild_id]
    skip = set()
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
                gen_command_callback(command)
            )
        await client.command_tree.sync(guild=guild_snowflake)