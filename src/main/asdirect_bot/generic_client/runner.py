from . import Client
import discord as dc
import os

def main():
    token = os.environ.get('BOT_TOKEN')
    if token is None:
        raise LookupError("Environment variable BOT_TOKEN not found!")
    client = Client(
        intents=dc.Intents.default(),
        submodules={
            "asdirect_bot.reference_command_management.discord_commands",
            "asdirect_bot.periodic_event_manager.discord_commands"
        }
    )
    client.run(token,log_handler=client.log_handler)

if __name__ == "__main__":
    main()