import json
import dataclasses
from typing import Dict,TypedDict
import asyncio

class Command(TypedDict):
    text_content:str # The reference that will be shown
    title:str # The title of the embed that'll be shown
    description:str # The description that'll appear on the command
    image:str|None

@dataclasses.dataclass()
class Database:
    servers:Dict[int,Dict[str,Command]] = dataclasses.field(default_factory=dict)
    internal_lock:asyncio.Lock = asyncio.Lock()
    async def update_command(self,server_id:int,command:Command,command_name:str)->"Database":
        """
        Insert or update a command.
        Async-safe (can be used directly from simultanous asyncs without conflicts)
        """
        async with self.internal_lock:
            if server_id not in self.servers:
                self.servers[server_id]={}
            self.servers[server_id][command_name]=command
            return self
    async def load_from_json(self,path:str)->"Database":
        """
        Load a serialised command database from a JSON file.
        Async-safe.
        """
        async with self.internal_lock:
            with open(path,'r') as i_f:
                self.servers = json.load(i_f)
            return self
    def save_to_json(self,path:str)->"Database":
        """
        Serialise a command database into a JSON file.
        """
        with open(path,'w') as o_f:
            json.dump(self.servers,o_f,indent=4)