from ..generic_client import Client
import logging
import os
import pathlib as pl
import json
from typing import Coroutine, List, Set, Type,Callable
from .persistence import Persistence,Server,Permissions,permission
from ..periodic_event_manager.ui import ArbitrarySetView,RoleSetView,NEXTPAGE
from ..generic_bot_utils.auto_ui import BaseEditView
import discord as dc

GENERIC_CLIENT_MODULE_NAME="Bot Permissions"

MNG_PERMS_PERM = permission("Manage bot permissions (dangerous!)","BOT_PERM_ADMIN")


async def setup(client:Client,logger:logging.Logger):
    logger.info("Setting up bot permissions.")
    permissions_path = os.environ.get("PERMISSIONS_PATH")
    if permissions_path is None:
        raise LookupError("Environment variable PERMISSIONS_PATH not found!")
    client.permissions = {'servers':{}}
    if pl.Path(permissions_path).exists():
        with open(permissions_path,'r') as i_f:
            client.permissions = json.load(i_f)
    else:
        with open(permissions_path,'w') as o_f:
            json.dump(client.permissions,o_f,indent=4)
    client.command_tree.command(
        name="botpermissions",
        description="Manage which roles are associated with each bot-specific permissions"
    )(manage_permissions(client))
def manage_permissions(client:Client):
    async def closure(interaction:dc.Interaction):
        allowed,why = Permissions.check(client,interaction,{MNG_PERMS_PERM.identifier})
        if not allowed:
            client.logger.warning(f"Blocked attempt to run manage_permissions by uid {interaction.user.id} ({interaction.user.name}/{interaction.user.display_name})")
            await interaction.response.send_message(
                content=(
                    "You're not allowed to run this command. This attempt has been logged.\n"
                    f"Reason: {why}"
                ),
                ephemeral=True
            )
            return
        content = "Please select which roles to edit (as a group).\nDismiss to finish interacting."
        if interaction.message is None:
            await interaction.response.send_message(
                content=content,
                ephemeral=True,
                view=RoleSetView(role_selected(client),content=content,original_interaction=interaction)
            )
        else:
            await interaction.response.edit_message(
                content=content,
                view=RoleSetView(role_selected(client),content=content,original_interaction=interaction)
            )
    return closure
class EditPermissionsView(ArbitrarySetView):
    def describe(self) -> str:
        roles = ','.join([f'<@&{r}>' for r in self.roles])
        return (
            f"Editing permissions for role(s) {roles}\n"
            "Current state:\n"
            +
            '\n'.join([f"- {p.name}: **{'✅Authorised' if p.identifier in self.currentperms else '❌ Unauthorised'}**" for p in Permissions.permissions])
            +
            "\nSelect a permission below to toggle."
        )
    def __init__(self, client:Client, roles:Set[str], currentperms:Set[str], cb: Callable[[dc.Interaction[Client], None], Coroutine[None, None, None]], type: Type = None, *, req: str = "", timeout: float | None = None, original_interaction: dc.Interaction[dc.Client]):
        super().__init__(self.done_cb, "permission", [p.name for p in Permissions.permissions], type, "", req=req, timeout=timeout, original_interaction=original_interaction)
        self.roles=roles
        self.currentperms=currentperms
        self.client=client
        self.final_cb = cb
    def confirmed(self):
        return []
    async def done_cb(self,interaction:dc.Interaction,sel:Set[str]):
        permissions:Persistence = self.client.permissions
        guild = str(interaction.guild_id)
        if guild not in permissions["servers"]:
            permissions['servers'][guild]={'user_permissions':{}}
        for role in self.roles:
            permissions['servers'][guild]["user_permissions"][role]=list(self.currentperms)
        permissions_path = os.environ.get("PERMISSIONS_PATH")
        if permissions_path is None:
            raise LookupError("Environment variable PERMISSIONS_PATH not found!")
        with open(permissions_path,'w') as o_f:
            json.dump(permissions,o_f,indent=4)
        self.selected=self.currentperms
        await self.final_cb(interaction,self.currentperms)
    async def selected_cb(self,sel:Set[str],interaction:dc.Interaction):
        await super().selected_cb(sel,interaction,respond=False)
        if sel[0]==NEXTPAGE:
            return
        selected = permission(name=sel.pop())
        if selected.identifier in self.currentperms:
            self.currentperms.remove(selected.identifier)
        else:
            self.currentperms.add(selected.identifier)
        await interaction.response.edit_message(
            content = self.describe()
        )
        self.selected=sel
def role_selected(client:Client):
    async def closure(interaction:dc.Interaction,sel:Set[str]):
       permissions:Persistence = client.permissions
       currentperms = {
           perm
           for role in sel
           for perm in permissions['servers'].get(str(interaction.guild_id),{'user_permissions':{}})["user_permissions"].get(role,[])
       }
       view = EditPermissionsView(client,sel,currentperms,lambda a,_:manage_permissions(client)(a),original_interaction=interaction)
       await interaction.response.edit_message(
           content=view.describe(),
           view=view
       )
    return closure