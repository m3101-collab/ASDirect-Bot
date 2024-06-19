from typing import List
import behave
from behave.runner import Context
from unittest.mock import MagicMock,Mock,NonCallableMock,NonCallableMagicMock
import discord as dcd
import discord.ext.commands as cmd
from functools import reduce
from test_constants import *
from dataclasses import dataclass
import parse
behave.use_step_matcher("cfparse")
@parse.with_pattern(r".+")
def parse_anything(str):
    return str
behave.register_type(str=parse_anything)

@dataclass()
class Response:
    content:str
    embed:dcd.Embed
    view:dcd.ui.View
    ephemeral:bool

# Arbitrary constants
GUILD_ID = 0

## Dictionary for making user creation easier
USER_ROLES_BY_PRIVILEGE = {
    'command-editing':{EDITCOMMAND_ROLE},
    'reference command':{REFERENCE_ROLE}
}

def make_interaction(ctx:Context)->NonCallableMagicMock:
    assert_has_guild(ctx)
    assert_has_user(ctx)
    interaction = NonCallableMagicMock(dcd.Interaction)
    interaction.configure_mock(
        guild = ctx.guild,
        user = ctx.user,
        __class__ = dcd.Interaction
    )
    return interaction

@behave.given("we are in a server")
def addGuild(ctx:Context):
    ctx.guild = NonCallableMagicMock(dcd.Guild)
    ctx.guild.configure_mock(
        id=GUILD_ID,
        __class__ = dcd.Guild
    )

#behave.use_step_matcher("re")
#@behave.given(r"an? (?P<type>.+)? *user( +with (?P<privileges>.+) *privileges)?")

@behave.given("a {type:str?}user")
@behave.given("an {type:str?}user")
def addTypeUser(ctx:Context,type:str):
    addUser(ctx,type,"")
@behave.given("a {type:str?}user with {privileges} privileges")
@behave.given("an {type:str?}user with {privileges} privileges")
def addUser(ctx:Context,type:str,privileges:str):
    if type is None:
        type=""
    ctx.user = NonCallableMagicMock(dcd.Member)

    permissions = NonCallableMagicMock(dcd.Permissions())
    permissions.configure_mock(
        administrator = type.strip().lower()=="admin"
    )

    # Aggregate all privilege-related roles
    roles = reduce(
        lambda a,b:a.union(b),
        [
            (
                USER_ROLES_BY_PRIVILEGE[privilege]
                if privilege in USER_ROLES_BY_PRIVILEGE
                else set()
            )
            for and_split in privileges.split('and')
            for comma_split in and_split.split(",")
            for privilege in [comma_split.strip()]
        ],
        set()
    )

    ctx.user.configure_mock(
        id=42,
        guild_permissions=permissions,
        roles=roles,
        __class__ = dcd.Member
    )
#behave.use_step_matcher("parse")

def assert_has_user(ctx:Context):
    assert hasattr(ctx,'user'), "No simulated user is configured!"
    assert isinstance(ctx.user,dcd.Member), "Current simulated user is not a Member!"
def assert_has_guild(ctx:Context):
    assert hasattr(ctx,'guild'), "Test isn't happening within a guild!"
    assert isinstance(ctx.guild,dcd.Guild), "Guild the test is happening within is not a Guild!"