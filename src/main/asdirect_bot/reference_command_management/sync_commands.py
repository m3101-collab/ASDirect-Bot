from ..generic_client import Client
import discord as dc
from .persistence import Command

def gen_command_callback(command:Command):
    async def handle_interaction(interaction:dc.Interaction):
        interaction.response.send_message(
            embed=dc.Embed(
                title = command['title'],
            ).add_field(
                value = command['text_content']
            )
        )
    return handle_interaction

def sync_guild(client:Client, guild_id:int):
    if guild_id not in client.reference_command_persistence:
        raise LookupError("This server hasn't been configured yet!")
    guild_snowflake = dc.Object(guild_id,type=dc.Guild)
    commands = client.reference_command_persistence.servers[guild_id]
    for command in client.command_tree.get_commands(guild=guild_snowflake):
        if type(command) is dc.app_commands.Command:
            del commands[command.name]
    if len(commands)>0:
        for name,command in commands.items():
            client.command_tree.add_command(
                client.command_tree.command(
                    name=name,
                    description=command['description'],
                    guild=guild_snowflake
                )(
                    gen_command_callback(command)
                ),
                guild=guild_snowflake
            )
        client.command_tree.sync(guild=guild_snowflake)