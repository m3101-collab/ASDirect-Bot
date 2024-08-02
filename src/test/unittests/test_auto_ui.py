import unittest
import unittest.mock as mock
import asyncio
import time
import sys
import generic_bot_utils.auto_ui as aui
import dataclasses

class AutoUITest(unittest.IsolatedAsyncioTestCase):
    async def test_decorators(self):
        @aui.edit_viewer_for(str)
        class TestView(aui.BaseEditView):
            pass
        assert aui.View.edit_viewer[str]==TestView , "Edit Viewer wasn't registered correctly!"
        @aui.text_renderer_for(str)
        def print_string(t:str):
            return t
        assert aui.View.text_renderers[str]==print_string, "Text renderer wasn't registered correctly!"
    async def test_properties_viewfor(self):
        @aui.annotate(
            "Test",
            a = aui.AutoUIProp("Property A", description="The first property"),
            b = aui.AutoUIProp("Property B", description="The second property")
        )
        @dataclasses.dataclass
        class Test:
            a: str
            b: int
        assert aui.annotate.registered_props[Test]['a'].name=="Property A", "Dataclass metadata annotation isn't being registered!"

        @aui.edit_viewer_for(Test)
        @aui.view_for(Test)
        class TestView:
            pass
        
        assert issubclass(TestView,aui.View), "view_for decorator failed."
        assert aui.View.edit_viewer[Test]==TestView, "Edit viewer for the Test class wasn't registered correctly"