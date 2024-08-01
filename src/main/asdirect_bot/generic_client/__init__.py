import importlib
from typing import Any,Set
import discord as dc
from ..reference_command_management import persistence as rcp
import pathlib as pl
import logging
import inspect

class Client(dc.Client):
    def __init__(
            self, *,
            intents: dc.Intents,
            submodules:Set[str],
            reference_command_path: str,
            **options: Any
        ) -> None:
        super().__init__(intents=intents, **options)
        self.log_handler = logging.StreamHandler()
        self.logger = logging.getLogger("GenericClient")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.log_handler)
        self.command_tree = dc.app_commands.CommandTree(self)
        self.reference_command_persistence = rcp.Database()
        self.reference_command_path = reference_command_path
        self.submodules = submodules
        self.logger.info("Waiting for discord on-ready status...")
    async def on_ready(self):
        self.logger.info("Setting up persistence")
        if pl.Path(self.reference_command_path).exists():
            await self.reference_command_persistence.load_from_json(self.reference_command_path)
        else:
            self.reference_command_persistence.save_to_json(self.reference_command_path)
        for module in self.submodules:
            self.logger.info(f"Setting up module: {module}")
            m = importlib.import_module(module)
            if hasattr(m,'setup') and hasattr(m,'GENERIC_CLIENT_MODULE_NAME'):
                logger = logging.getLogger(m.GENERIC_CLIENT_MODULE_NAME)
                logger.addHandler(self.log_handler)
                logger.setLevel(self.logger.level)
                r = m.setup(self,logger)
                if inspect.isawaitable(r):
                    await r
            else:
                raise ImportError(f"Module {module} is not a proper generic_client module! It must include a setup(generic_client) function.")