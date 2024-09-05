from ..generic_bot_utils import auto_ui as aui
import discord as dc
from typing import Set,Callable,Any,Coroutine,List
NEXTPAGE = "__NEXTPAGE__SECRETVALUE"
class ChannelSelectView(aui.BaseEditView[int]):
    def describe(self) -> str:
        if self.selected is None:
            return "No channel has been selected yet."
        else:
            return f"<#{self.selected}>"
    def __init__(self, cb: Callable[[dc.Interaction, Set[int]], Coroutine[None, None, None]], type: aui.Type = None, content: str = "", *, req: str = "", timeout: float|None = None, original_interaction: dc.Interaction[dc.Client]):
        super().__init__(cb, type, content, req=req, timeout=timeout, original_interaction=original_interaction)
        self.roles = original_interaction.guild.channels #Yes, this is a perfect copy of the other one
        #I could do a generic thing, but at this point I just want to get this to work
        self.roles = {
            role.name:role
            for role in self.roles
        }
        self.roleoptions = [
            dc.SelectOption(label=name,value=name)
            for name in self.roles
        ]
        self.page = 0
        self.totalpages = ((len(self.roles)-1)//24)+1
        self.selected = None
        self.options = aui.CBSelect(
            self.selected_cb,
            max_values=1,
        )
        self.setup_options()
        self.add_item(self.options)
    def setup_options(self):
        self.options.options=(
            self.roleoptions[24*self.page:24*(self.page+1)]
            +[
                dc.SelectOption(label="Next Page",value=NEXTPAGE)
            ]
        )
    def confirmed(self):
        return self.selected
    async def selected_cb(self,opts:List[str],interaction:dc.Interaction):
        if opts[0] == NEXTPAGE:
            self.page+=1
            self.page%=self.totalpages
            self.setup_options()
        else:
            self.selected=self.roles[opts[0]].id
        await interaction.response.edit_message(
            content=self.content+'\n'+self.describe(),
            view=self
        )
class RoleSetView(aui.BaseEditView[List[int]]):
    def describe(self) -> str:
        if len(self.selected)==0:
            return "No roles have been selected yet.\nDue to limitations of Discord bots' UI tools, you must select the roles one at a time."
        else:
            return ",".join([f"<@&{id}>" for id in self.selected])+"\nDue to limitations of Discord bots' UI tools, you must select the roles one at a time."
    def __init__(self, cb: Callable[[dc.Interaction, Set[int]], Coroutine[None, None, None]], type: aui.Type = None, content: str = "", *, req: str = "", timeout: float|None = None, original_interaction: dc.Interaction[dc.Client]):
        super().__init__(cb, type, content, req=req, timeout=timeout, original_interaction=original_interaction)
        self.roles = original_interaction.guild.roles
        self.roles = {
            role.name:role
            for role in self.roles
        }
        self.roleoptions = [
            dc.SelectOption(label=name,value=name)
            for name in self.roles
        ]
        self.page = 0
        self.totalpages = ((len(self.roles)-1)//24)+1
        self.selected = set()
        self.options = aui.CBSelect(
            self.selected_cb,
            max_values=1,
        )
        self.setup_options()
        self.add_item(self.options)
    def setup_options(self):
        self.options.options=(
            self.roleoptions[24*self.page:24*(self.page+1)]
            +[
                dc.SelectOption(label="Next Page",value=NEXTPAGE)
            ]
        )
    def confirmed(self):
        return list(self.selected) if len(self.selected)>0 else None
    async def selected_cb(self,opts:List[str],interaction:dc.Interaction):
        if opts[0] == NEXTPAGE:
            self.page+=1
            self.page%=self.totalpages
            self.setup_options()
        else:
            self.selected=self.selected.union({self.roles[opts[0]].id})
        await interaction.response.edit_message(
            content=self.content+'\n'+self.describe(),
            view=self
        )
class ArbitrarySetView[str](aui.BaseEditView[List[str]]):
    def describe(self) -> str:
        if len(self.selected)==0:
            return f"No {self.objectname} have been selected yet.\nDue to limitations of Discord bots' UI tools, you must select the {self.objectname} one at a time."
        else:
            return ",".join([f"{id}" for id in self.selected])+f"\nDue to limitations of Discord bots' UI tools, you must select the {self.objectname} one at a time."
    def __init__(self, cb: Callable[[dc.Interaction, Set[int]], Coroutine[None, None, None]], objectname:str, choices:List[str], type: aui.Type = None, content: str = "", *, req: str = "", timeout: float|None = None, original_interaction: dc.Interaction[dc.Client]):
        super().__init__(cb, type, content, req=req, timeout=timeout, original_interaction=original_interaction)
        self.objectname=objectname
        self.roles = choices
        self.roles = {
            role:role
            for role in self.roles
        }
        self.roleoptions = [
            dc.SelectOption(label=name,value=name)
            for name in self.roles
        ]
        self.page = 0
        self.totalpages = ((len(self.roles)-1)//24)+1
        self.selected = set()
        self.options = aui.CBSelect(
            self.selected_cb,
            max_values=1,
        )
        self.setup_options()
        self.add_item(self.options)
    def setup_options(self):
        self.options.options=(
            self.roleoptions[24*self.page:24*(self.page+1)]
            +[
                dc.SelectOption(label="Next Page",value=NEXTPAGE)
            ]
        )
    def confirmed(self):
        return self.selected if len(self.selected)>0 else None
    async def selected_cb(self,opts:List[str],interaction:dc.Interaction):
        if opts[0] == NEXTPAGE:
            self.page+=1
            self.page%=self.totalpages
            self.setup_options()
        else:
            self.selected=self.selected.union({opts[0]})
        await interaction.response.edit_message(
            content=self.content+'\n'+self.describe(),
            view=self
        )
from . import persistence as pers

@aui.auto_view_for[pers.Event](pers.Event)
class EventView:
    pass
@aui.auto_view_for[pers.ScheduledAction](pers.ScheduledAction)
class ScheduledActionView:
    pass
@aui.auto_view_for[pers.Schedule](pers.Schedule)
class ScheduleView(aui.BaseEditView[pers.Schedule]):
    pass

import datetime
@aui.edit_viewer_for(pers.ScheduleDate)
class ScheduleDateView(aui.BaseEditView):
    def describe(self) -> str:
        now = datetime.datetime.now()
        time = int(datetime.datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=self.values.get('hour',0),
            minute=0,
            second=0
        ).timestamp())
        setdate = (
            f"{self.values.get('weekday','any day of the week')}, "
            f"day {self.values.get('day','? (any)')} of month "
            f"{self.values.get('month','? (any)')}, "
            f"at {self.values.get('hour','midnight')}."
        )
        return f"The hour you set is <t:{time}:t> in the bot's timezone.\n(<t:{time}:R>)\nIt's set to {setdate}\nDue to discord UI issues, you have to press this button to set a new schedule:"
    def __init__(self, cb: Callable[[dc.Interaction[dc.Client], Any], Coroutine[None, None, None]], type: aui.Type = None, content: str = "", *, req: str = "", timeout: float|None = None, original_interaction: dc.Interaction[dc.Client]):
        super().__init__(cb, type, content, req=req, timeout=timeout, original_interaction=original_interaction)
        self.set = aui.CBButton(self.clicked,label="Set Schedule")
        self.add_item(self.set)
        self.values = {}
        self.weekday = aui.CBSelect(self.selected,placeholder="Weekday",options=[
            dc.SelectOption(label=opt,value=opt)
            for opt in pers.ScheduleDate.__annotations__['weekday'].__args__
        ])
        self.add_item(self.weekday)
    async def selected(self,opts:List[str],interaction:dc.Interaction):
        self.values['weekday']=opts[0]
        await interaction.response.edit_message(
            content = self.content+"\n"+self.describe()
        )
    async def clicked(self,interaction:dc.Interaction):
        parentview = self
        class Modal(dc.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="Schedule")
                self.day = dc.ui.TextInput(label="Day",required=False,placeholder="13")
                self.month = dc.ui.TextInput(label="Month",required=False,placeholder="8")
                self.hour = dc.ui.TextInput(label="Hour",required=False,placeholder="22")
                self.add_item(self.day)
                self.add_item(self.month)
                self.add_item(self.hour)
            async def on_submit(self, interaction: dc.Interaction) -> None:
                error = False
                try:
                    val = int(self.month.value)
                    assert (val>=1) and (val<=12)
                    parentview.values['month']=val
                except:
                    error = True
                try: 
                    val = int(self.day.value)
                    assert (val>=1) and (val<=31)
                    parentview.values['day']=val
                except:
                    error = True
                try:
                    val = int(self.hour.value)
                    assert (val>=0) and (val<=23)
                    parentview.values['hour']=val
                except:
                    error = True
                if error:
                    await interaction.response.edit_message(
                        content = parentview.content+"\n"+parentview.describe(),
                        embed=dc.Embed(title="Invalid/Missing values",colour=dc.Colour.red()).add_field(
                            name="Some fields were ignored.",
                            value="All values must be numbers.\nDays have to be between 1 and 31\nMonth has to be between 1 and 1\nHour has to be between 0 and 23"
                        )
                    )
                else:
                    await interaction.response.edit_message(
                        content = parentview.content+"\n"+parentview.describe()
                    )
            
        await interaction.response.send_modal(Modal())
    def confirmed(self):
        return self.values

@aui.text_renderer_for(pers.ScheduleDate)
def DateRenderer(date:pers.ScheduleDate)->str:
    return (
        f"{date.get('weekday','any day of the week')}, "
        f"day {date.get('day','? (any)')} of month "
        f"{date.get('month','? (any)')}, "
        f"at {date.get('hour','midnight')}."
    )

@aui.text_renderer_for(pers.Command)
def RenderCommand(c:pers.Command)->str:
    return (
        (
            (
                f"Send a message at <#{c["params"]['channel_id']}>"
            )
            if c['type']=='Send Message'
            else
            (
                (
                    f"Manage permissions for <#{c['params']['channel_id']}>"
                )
                if c['type']=='Change Channel Permissions'
                else
                "IDFK"
            )
        )
    )

class SendMessageCommandView(aui.BaseEditView[pers.Command]):
    def describe(self) -> str:
        return (
            f"Message:\n```{self.values.get('message','')}```\n"
            f"At "+(
                f"<#{self.values['channel_id']}>"
                if 'channel_id' in self.values
                else "a channel yet to be determined"
            )+
            f"\nWith "+(
                f"the image hosted at {self.values['image']}"
                if 'image' in self.values
                else
                'no image.'
            )
        )
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: aui.Type = None, content: str = "", *, req: str = "", timeout: float|None = None, original_interaction: dc.Interaction[dc.Client]):
        super().__init__(cb, type, content, req=req, timeout=timeout, original_interaction=original_interaction)
        self.values={}
    async def chose_channel(self,interaction:dc.Interaction,cid:int|None):
        if cid is not None:
            self.values['channel_id']=cid
        await interaction.response.edit_message(
            content=self.content+'\n'+self.describe(),
            view=self
        )
    def confirmed(self):
        return (
            {'type':'Send Message','params':self.values} if (
                ('channel_id' in self.values)
                and
                ('message' in self.values)
            )
            else None
        )
    @dc.ui.button(label="Choose a channel")
    async def choosechannel(self,interaction:dc.Interaction,but:dc.ui.Button):
        view = ChannelSelectView(self.chose_channel,original_interaction=interaction)
        view.content = ""
        await interaction.response.edit_message(
            content=view.content+'\n'+view.describe(),
            view=view
        )
    @dc.ui.button(
        label="Add an image URL"
    )
    async def image(self,interaction:dc.Interaction,but:dc.ui.Button):
        parent=self
        class Modal(dc.ui.Modal):
            def __init__(self, *, timeout: float|None = None) -> None:
                super().__init__(title="URL", timeout=timeout)
                self.message = dc.ui.TextInput(
                    label="URL",
                    style=dc.TextStyle.short,
                    placeholder="https://www.youtube.com/watch?v=wKnkQdsITUE"
                )
                self.add_item(self.message)
            async def on_submit(self, interaction: dc.Interaction) -> Coroutine[Any, Any, None]:
                parent.values['image']=self.message.value
                await interaction.response.edit_message(
                    content=parent.content+'\n'+parent.describe()
                )
        await interaction.response.send_modal(Modal())
    @dc.ui.button(
        label="Edit the text"
    )
    async def message(self,interaction:dc.Interaction,but:dc.ui.Button):
        parent=self
        class Modal(dc.ui.Modal):
            def __init__(self, *, timeout: float | None = None) -> None:
                super().__init__(title="Message", timeout=timeout)
                self.message = dc.ui.TextInput(
                    label="Message",
                    style=dc.TextStyle.paragraph,
                    placeholder="What is this? Perhaps an easter egg?\nPerhaps it's delirium\nA sleepy programmer's mind..."
                )
                self.add_item(self.message)
            async def on_submit(self, interaction: dc.Interaction) -> Coroutine[Any, Any, None]:
                parent.values['message']=self.message.value
                await interaction.response.edit_message(
                    content=parent.content+'\n'+parent.describe()
                )
        await interaction.response.send_modal(Modal())
class PermissionsCommandView(aui.BaseEditView[pers.ChannelPermissionCommandParams]):
    pass
@aui.edit_viewer_for(pers.Command)
class CommandView(aui.BaseEditView):
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: aui.Type = None, content: str = "", *, req: str = "", timeout: float|None = None, original_interaction: dc.Interaction[dc.Client]):
        super().__init__(cb, type, content, req="A command must have been successfully configured.", timeout=timeout, original_interaction=original_interaction)
        self.command = {'__actualtype__':pers.Command}
    def describe(self) -> str:
        return RenderCommand(self.command) if 'params' in self.command else "Please select a command type"
    @dc.ui.select(
        options=[
            dc.SelectOption(label=typ,value=typ)
            for typ in pers.Command.__annotations__['type'].__args__
        ]
    )
    async def command_type_select(self,  interaction:dc.Interaction,selected:dc.ui.Select):
        selected=selected.values
        if selected[0]=="Send Message":
            view = SendMessageCommandView(self.command_configured,original_interaction=self.orig_interaction)
            await interaction.response.edit_message(
                content=self.content+'\n'+view.describe(),
                view=view
            )
        elif selected[0]=="Change Channel Permissions":
            view = ChangePermissionsView(self.command_configured,original_interaction=self.orig_interaction)
            await interaction.response.edit_message(
                content=self.content+'\n'+view.describe(),
                view=view
            )
        else:
            await interaction.response.edit_message()
    async def command_configured(self,interaction:dc.Interaction,o:pers.Command|None):
        if o is not None:
            self.command=o
        await interaction.response.edit_message(
            content=self.content+"\n"+self.describe(),
            view = self
        )
    def confirmed(self):
        if 'params' in self.command:
            return self.command|{'__actualtype__':pers.Command}
        else:
            return None

class ChangePermissionsView(aui.BaseEditView[pers.Command]):
    def confirmed(self):
        if 'channel_id' in self.values:
            return {'type':"Change Channel Permissions",'params':self.values}
        else:
            return None
    def describe(self) -> str:
        return (
            f"Changing permissions for "+
            (f"<#{self.values['channel_id']}>" if 'channel_id' in self.values else "a yet to be defined channel")
            +
            "\nFor roles "
            +
            (",".join([f"<@&{id}>" for id in self.values['role_ids']]) if 'role_ids' in self.values else "yet to be defined")
            +
            "\n\nThe following permissions will be added to the role:\n"
            +
            ("\n".join([f"- {p}" for p in self.values['permissions_to_add']]) if 'permissions_to_add' in self.values else "- None")
            +
            "\nAnd the following permissions will be removed:\n"
            +
            ("\n".join([f"- {p}" for p in self.values['permissions_to_remove']]) if 'permissions_to_remove' in self.values else "- None")
            +'\n'
        )
    def __init__(self, cb: Callable[[dc.Interaction, pers.Command], Coroutine[None, None, None]], type: aui.Type = None, content: str = "", *, req: str = "", timeout: float|None = None, original_interaction: dc.Interaction[dc.Client]):
        super().__init__(cb, type, content, req=req, timeout=timeout, original_interaction=original_interaction)
        self.values={}
    async def sel_channel_cb(self,interaction:dc.Interaction,channel:int|None):
        if channel is not None:
            self.values['channel_id']=channel
        await interaction.response.edit_message(
            content=self.content+"\n"+self.describe(),
            view=self
        )
    @dc.ui.button(label="Select Channel")
    async def sel_channel(self,interaction:dc.Interaction,but:dc.ui.Button):
        view = ChannelSelectView(self.sel_channel_cb,original_interaction=interaction)
        await interaction.response.edit_message(
            content=view.describe(),
            view=view
        )
    async def sel_roles_cb(self,interaction:dc.Interaction,items:None|List[int]):
        if items is not None:
            self.values['role_ids']=items
        await interaction.response.edit_message(
            content=self.content+"\n"+self.describe(),
            view=self
        )
    @dc.ui.button(label="Set Roles")
    async def sel_roles(self,interaction:dc.Interaction,but:dc.ui.Button):
        view = RoleSetView(self.sel_roles_cb,original_interaction=interaction)
        await interaction.response.edit_message(
            content=view.describe(),
            view=view
        )
    async def sel_perm_allowed_cb(self,interaction:dc.Interaction,items:None|List[str]):
        if items is not None:
            self.values['permissions_to_add']=items
        await interaction.response.edit_message(
            content=self.content+"\n"+self.describe(),
            view=self
        )
    @dc.ui.button(label="Set Permissions to add")
    async def sel_perm_allowed(self,interaction:dc.Interaction,but:dc.ui.Button):
        view = ArbitrarySetView(self.sel_perm_allowed_cb,original_interaction=interaction,objectname="permissions",choices=list(pers.PERMISSION_NAMES))
        view.content = "# Adding permissions\n"
        await interaction.response.edit_message(
            content=view.content+"\n"+view.describe(),
            view=view
        )
    async def sel_perm_disallow_cb(self,interaction:dc.Interaction,items:None|List[str]):
        if items is not None:
            self.values['permissions_to_remove']=items
        await interaction.response.edit_message(
            content=self.content+"\n"+self.describe(),
            view=self
        )
    @dc.ui.button(label="Set Permissions to remove")
    async def sel_perm_disallow(self,interaction:dc.Interaction,but:dc.ui.Button):
        view = ArbitrarySetView(self.sel_perm_disallow_cb,original_interaction=interaction,objectname="permissions",choices=list(pers.PERMISSION_NAMES))
        view.content = "# Removing permissions\n"
        await interaction.response.edit_message(
            content=view.content+"\n"+view.describe(),
            view=view
        )

@aui.text_renderer_for(pers.Schedule)
def RenderScheduleR(v:pers.Schedule):
    return f"Triggers {v['recurrence']}, {DateRenderer(v['date'])}"

@aui.text_renderer_for(pers.ScheduledAction)
def RenderScheduledCOmmand(v:pers.ScheduledAction):
    return f"Action triggered by {len(v['schedules'])} schedule(s) with {len(v['commands'])} command(s)"

@aui.auto_view_for[pers.MessagePool](pers.MessagePool)
class PoolView(aui.BaseEditView[pers.MessagePool]):
    pass