import importlib
from typing import Any,Set
import discord as dc
from ..reference_command_management import persistence as rcp

class Client(dc.Client):
    def __init__(
            self, *,
            intents: dc.Intents,
            submodules:Set[str],
            reference_command_path: str,
            **options: Any
        ) -> None:
        super().__init__(intents=intents, **options)
        self.command_tree = dc.app_commands.CommandTree(self)
        self.reference_command_persistence = rcp.Database()
        self.reference_command_path = reference_command_path
        for module in submodules:
            m = importlib.import_module(module)
            try:
                m.setup(self)
            except:
                ImportError(f"Module {module} is not a proper generic_client module! It must include a setup(generic_client) function.")
    async def on_ready(self):
        print("Setting up persistence")
        await self.reference_command_persistence.load_from_json(self.reference_command_path)