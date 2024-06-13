import discord as dcd
import behave
from behave.runner import Context
from test_constants import *
from discord_mock_steps import assert_has_guild,assert_has_user

@behave.given("startup has been run")
def startup(ctx:Context):
    #TODO: Call bot startup
    assert False, "Test is not yet implemented"

@behave.given("we've configured the required authorisations")
def configure_auth(ctx:Context):
    assert_has_guild(ctx)

    REFERENCE_ROLE #and
    EDITCOMMAND_ROLE
    #are our fake roles for the tests

    #TODO: Add roles to bot context
    assert False, "Test is not yet implemented"

@behave.given("a set of predefined test commands")
def add_test_commands(ctx:Context):
    assert_has_guild(ctx)
    #TODO: Add the test command that'll be used in other tests.
    assert False, "Test is not yet implemented"

@behave.when("the user runs a test command")
def user_runs_test_command(ctx:Context):
    assert_has_guild(ctx)
    assert_has_user(ctx)
    #TODO: Simulate running the test command
    assert False, "Test is not yet implemented"

COMMAND_ACTIONS = {'edits','adds','removes'}
@behave.when("the user {action} a command")
def user_does_command_action(ctx:Context,action:str):
    assert_has_guild(ctx)
    assert_has_user(ctx)
    #TODO: Simulate the user going through the interface and doing the required action with a test command
    assert False, "Test is not yet implemented"

@behave.then("the command is created")
def command_created(ctx:Context):
    #TODO: Check if the command was created correctly
    assert False, "Test is not yet implemented"

@behave.then("the command is updated")
def command_updated(ctx:Context):
    #TODO: Check if the command was updated correctly
    assert False, "Test is not yet implemented"

@behave.then("the command is removed")
def command_updated(ctx:Context):
    #TODO: Check if the command was removed correctly
    assert False, "Test is not yet implemented"

@behave.then("the user is informed they don't have the required privileges")
def unauthorised(ctx:Context):
    #TODO: Check if an error message was displayed. Use ctx.commandresponse to gather the last run command's response
    assert False, "Test is not yet implemented"

@behave.then("the expected test reference is brought up")
def ref_up(ctx:Context):
    #TODO: Check if the reference was displayed. Use ctx.commandresponse to gather the last run command's response
    assert False, "Test is not yet implemented"