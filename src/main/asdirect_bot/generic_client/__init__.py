import importlib
from typing import Any,Set
import discord as dc
from ..reference_command_management import persistence as rcp
import pathlib as pl
import logging
import inspect
import os

class Client(dc.Client):
    def __init__(
            self, *,
            intents: dc.Intents,
            submodules:Set[str],
            **options: Any
        ) -> None:
        super().__init__(intents=intents, **options)
        self.log_handler = logging.StreamHandler()
        log_path = os.environ.get("LOG_PATH")
        if log_path is None:
            raise LookupError("Environment variable LOG_PATH not found!")
        self.file_log_handler = logging.FileHandler(log_path)
        self.logger = logging.getLogger("GenericClient")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(self.log_handler)
        self.logger.addHandler(self.file_log_handler)
        self.command_tree = dc.app_commands.CommandTree(self)
        self.submodules = submodules
        self.logger.info("Waiting for discord on-ready status...")
    async def on_ready(self):
        for module in self.submodules:
            self.logger.info(f"Setting up module: {module}")
            m = importlib.import_module(module)
            if hasattr(m,'setup') and hasattr(m,'GENERIC_CLIENT_MODULE_NAME'):
                logger = logging.getLogger(m.GENERIC_CLIENT_MODULE_NAME)
                logger.addHandler(self.log_handler)
                logger.addHandler(self.file_log_handler)
                logger.setLevel(self.logger.level)
                r = m.setup(self,logger)
                if inspect.isawaitable(r):
                    await r
            else:
                raise ImportError(f"Module {module} is not a proper generic_client module! It must include a setup(generic_client) function.")
        #Turning this off while I develop the bot.
        #await self.command_tree.sync()
        #self.logger.info("Sync sent. It might take up to 1h for global commands to update.")