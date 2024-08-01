import discord as dc
from typing import Set,Literal
PermissionSet = Set[Literal['admin']]
def has_permission(interaction:dc.Interaction, permission:PermissionSet)->bool:
    for p in permission:
        if p == 'admin':
            if  not interaction.user.resolved_permissions.administrator:
                return False
    return True