from typing import TypedDict,List,Literal,Dict
from ..generic_bot_utils import auto_ui as aui
from datetime import datetime
import discord as dc
from . import ui
PERMISSION_NAMES = sorted([
    prop
    for prop in dir(dc.Permissions)
    if isinstance(getattr(dc.Permissions,prop),dc.permissions.flag_value)
])
@aui.annotate(
    "Channel Permission Command Settings",
    channel_id = aui.AutoUIProp(
        "Channel ID",
        "ID of the channel we'll be changing permissions for",
        required=True,
        custom_view=ui.ChannelSelectView
    ),
    role_ids= aui.AutoUIProp(
        "Role IDS",
        "IDs of the roles we'll be changing permissions for",
        required=True,
        custom_view=ui.RoleSetView
    )
)
class ChannelPermissionCommandParams(TypedDict):
    channel_id: int
    role_ids: List[int]
    permissions_to_add: List[str]
    permissions_to_remove: List[str]
@aui.annotate(
    "Message Command Settings",
    message = aui.AutoUIProp(
        "Message",
        "The message that will be sent",
        required=True
    ),
    channel_id = aui.AutoUIProp(
        "Channel ID",
        "Which channel to send the message in",
        required=True,
        custom_view=ui.ChannelSelectView
    ),
    image = aui.AutoUIProp(
        "Image",
        "An URL to a displayable image",
        required=False
    )
)
class MessageCommandParams(TypedDict):
    message: str
    channel_id: int
    image: None | str
class Command(TypedDict):
    type: Literal[
        "Send Message",
        "Change Channel Permissions"
    ]
    params: (
        MessageCommandParams
        |ChannelPermissionCommandParams
    )
@aui.annotate(
    "Date",
    weekday = aui.AutoUIProp(
        "Day of the week",
        "Will only be used in the weekly recurrence mode."
    ),
    day = aui.AutoUIProp(
        "Day of the month",
        "Will be used by the monthly and yearly recurrence modes."
    ),
    month = aui.AutoUIProp(
        "Month",
        "Will be used for the yearly recurrence mode."
    ),
    hour = aui.AutoUIProp(
        "Hour",
        "Always used. Relative to the bot's timezone, 24h format (e.g. 10, 20, 11)."
    )
)
class ScheduleDate(TypedDict):
    weekday:Literal[
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    ]
    day:int
    month:int
    hour:int
@aui.annotate(
    "Schedule",
    date = aui.AutoUIProp(
        "Date",
        "Irrelevant values will be ignored (e.g. month for weekly schedules)",
        required=True
    ),
    recurrence = aui.AutoUIProp(
        "Recurrence",
        "How frequently the event will happen.",
        required=True
    )
)
class Schedule(TypedDict):
    date:ScheduleDate
    recurrence:Literal[
        "Daily", # Will run at this time every day
        "Weekly", # Will run at this time and day of the week every week
        "Monthly", # Will run at this day, time and all every month
        "Yearly" # Will run at this date and time every year
    ]
@aui.annotate(
    "Scheduled Action",
    schedules = aui.AutoUIProp(
        "Schedules",
        "Which schedules will trigger the actions (the commands will be run at every scheduled trigger)",
        required=True
    ),
    commands = aui.AutoUIProp(
        "Commands",
        "Which commands will be run when triggered",
        required=True
    )
)
class ScheduledAction(TypedDict):
    schedules:List[Schedule] # Will run the commands at the earliest schedule resolution
    commands:List[Command]
@aui.annotate(
    "Event",
    actions = aui.AutoUIProp(
        "Steps",
        "Parts of the event, e.g. opening on Mondays, closing on Tuesdays",
        required=True
    )
)
class Event(TypedDict):
    name:str
    actions:List[ScheduledAction]

@aui.annotate(
    "Message Pool",
    name = aui.AutoUIProp(
        "Pool name",
        "The name that'll be referenced in the messages",
        required=True
    ),
    messages = aui.AutoUIProp(
        "Messages",
        "Set of messages"
    ),
    mode = aui.AutoUIProp(
        "Pool mode",
        "In a queue, messages are used only once. In a cycle, they go back to the end.",
        required=True
    ),
    defaultmessage = aui.AutoUIProp(
        "Default Message",
        "The message that will be used if there are none left in the queue.",
        required=True,
        custom_view=aui.LongStrView
    )
)
class MessagePool(TypedDict):
    name:str
    messages:List[str]
    mode:Literal['Queue','Cycle']
    defaultmessage:str
class Server(TypedDict):
    events:Dict[str,Event]
    pools:Dict[str,MessagePool]
class Persistence(TypedDict):
    servers:Dict[int,Server]