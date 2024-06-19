import unittest
import unittest.mock as mock
from asdirect_bot.reference_command_management import persistence
import asyncio
import time
import sys

default_serverdict = {
    0:{
        "test":{
            'content':"Test reference command"
        }
    },
    1:{
        "ref":{
            'content':"Test reference command 2"
        }
    }
}

def delay(a):
    def run(*args,**kwargs):
        time.sleep(0.1)
        return a(*args,**kwargs) if callable(a) else a
    return run
def asyncdelay(a):
    async def run(*args,**kwargs):
        time.sleep(0.1)
        return await a(*args,**kwargs) if callable(a) else a
    return run

persistence.json = mock.MagicMock()
persistence.json.configure_mock(
    dump = mock.MagicMock(),
    load = delay(default_serverdict)
)
persistence.open = mock.MagicMock()

class CommandSerialisationTest(unittest.IsolatedAsyncioTestCase):
    async def test_multiple_async_requests(self):
        db = persistence.Database(default_serverdict)
        with mock.patch.object(db,"update_command",mock.MagicMock(
            side_effect=asyncdelay(db.update_command)
        )):
            await db.load_from_json("test.json")
            await asyncio.gather(*[
                db.update_command(0,{'content':'test'},'_test')
                for i in range(10)
            ])
            await db.update_command(2,{'content':'test'},'_test')
            db.save_to_json("test.json")