"""
Generic tools for creating simple
CRUD UI views for discord
"""

import dataclasses
from typing import Coroutine,TypedDict,Type,Any,Dict,Callable,TypeVar,List,Tuple,Set,Iterable
import discord as dc
import inspect

CANCELLED_OBJ = object()

class CBButton(dc.ui.Button):
    def __init__(self, cb:Callable[[dc.Interaction],Coroutine[Any,Any,Any]], *, style: dc.ButtonStyle = dc.ButtonStyle.secondary, label: str | None = None, disabled: bool = False, custom_id: str | None = None, url: str | None = None, emoji: str | dc.Emoji | dc.PartialEmoji | None = None, row: int | None = None):
        super().__init__(style=style, label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row)
        self.cb=cb
    async def callback(self, interaction: dc.Interaction):
        return await self.cb(interaction)

class CBSelect(dc.ui.Select):
    def __init__(self, cb:Callable[[List[str],dc.Interaction],Coroutine[Any,Any,Any]],*, custom_id: str = ..., placeholder: str | None = None, min_values: int = 1, max_values: int = 1, options: List[dc.SelectOption] = ..., disabled: bool = False, row: int | None = None) -> None:
        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, disabled=disabled, row=row)
        self.cb=cb
    async def callback(self, interaction: dc.Interaction) -> Any:
        return await self.cb(self.values,interaction)

class BaseEditView[T](dc.ui.View):
    def __init__(self, cb:Callable[[dc.Interaction,T],Coroutine[None,None,None]], type:Type=None,*, req:str="", timeout: float | None = 180):
        super().__init__(timeout=timeout)
        self.cb=cb
        self.requirements = req
    def confirmed(self):
        return None
    @dc.ui.button(
        label="Cancel",
        row=5,
        style=dc.ButtonStyle.red
    )
    async def cancel(self,interaction:dc.Interaction, btn:dc.ui.Button):
        await self.cb(interaction,None)
    @dc.ui.button(
        label="Confirm",
        row=5,
        style=dc.ButtonStyle.blurple
    )
    async def confirm(self,interaction:dc.Interaction, btn:dc.ui.Button):
        val = self.confirmed()
        if val is None:
            interaction.response.edit_message(
                embed=dc.Embed(
                    title="Error"
                ).add_field(
                    name="Invalid value",
                    value=self.requirements
                )
            )
        await self.cb(interaction,val)

class View[T](dc.ui.View):
    text_renderers:Dict[Type[Any],Callable[[Any],str]] = {}
    edit_viewer:Dict[Type[Any],Type[BaseEditView]] = {}

    def generate_typed_dict(self)->T:
        pass
    def generate_dataclass(self)->T:
        pass
    def __init__(self, structure:Type[T], done_cb:Callable[[dc.Interaction,T],Coroutine[Any,Any,Any]], *, timeout: float | None = 360):
        super().__init__(timeout=timeout)
        self.cb = done_cb
        self.generate:Callable[[],T] = lambda :None
        if issubclass(structure,TypedDict):
            self.generate = self.generate_typed_dict
        elif hasattr(structure,dataclasses._FIELDS):
            self.generate = self.generate_dataclass
        else:
            raise TypeError(
                f"Cannot create a UI view for a {structure}. It must be either a TypedDict or decorated with `dataclass.dataclass`."
            )
        self.name:str = (
            annotate.readable_names[structure]
            if structure in annotate.readable_names
            else str(structure)
        )
        self.values:Dict[str,Any] = {}
        self.types:Dict[str,Type] = {}
        self.viewtypes:Dict[str,Type] = {}
        self.options:Dict[str,str] = [] #prop name -> readable name
        self.props:Dict[str,AutoUIProp] = (
            annotate.registered_props[structure] 
            if structure in annotate.registered_props
            else {}
        )
        self.descriptions:Dict[str,str] = {}
        self.missing:Set[str] = set()

        for p,t in structure.__annotations__:
            self.types[p] = t
            if t not in View.edit_viewer:
                if (t.__class__ in View.edit_viewer) and hasattr(t,'__args__'):
                    self.viewtypes[p] = t.__class__
                else:
                    raise TypeError(f"Type \"{t}\" has no registered edit view.")
            else:
                self.viewtypes[p] = t
            self.options[p] = self.props[p].name if p in self.props else p
            if (p not in self.props) or (self.props[p].required):
                self.missing.add(p)
        self.current = self.options.keys().__iter__().__next__()

        self.selector = CBSelect(
            self.cb_select,
            options=[
                dc.SelectOption(
                    label=v,
                    value=k,
                    description=(
                        self.props[k].description
                        if k in self.props
                        else None
                    )
                )
                for k,v in self.options
            ]
        )
        self.confirm = CBButton(
            self.cb_confirm,
            style=dc.ButtonStyle.primary,
            label="Finish",
            disabled=len(self.missing)!=0
        )
    async def cb_confirm(self,interaction:dc.Interaction):
        val = self.generate()
        await self.cb(interaction,val)
    async def cb_select(self,opt:List[str],interaction:dc.Interaction):
        opt=opt[0]
        self.current=opt
        interaction.response.edit_message(
            content=(
                f"## {self.props[opt].name}\n{self.props[opt].description}"
                if opt in self.props
                else f"## {opt}"
            ),
            view=View.edit_viewer[self.viewtypes[opt]](self.set,self.types[opt])
        )
    def describe(self)->str:
        return (
            f"# {self.name}\n"
            "## Properties\n"
            +
            "\n".join(
                (
                    f"- {v}: {self.props[k].description}"
                    if k in self.props
                    else f"- {v}"
                ) for k,v in self.options.items()
            )
            +
            "\n## Missing\nThe following required settings are missing:\n"
            +
            "\n".join(
                f"- {self.options[k]}"
                for k in self.missing
            )
            +
            "\nSelect a property to edit:"
        )
    async def set(self, interaction:dc.Interaction,value:Any):
        self.selector.values=[]
        if value is None:
            interaction.response.edit_message(
                content=(
                    self.describe()
                    +
                    "\nThat not a valid value for this setting. Ignoring."
                ),
                view=self
            )
        else:
            self.values[self.current]=value
            if self.current in self.missing:
                self.missing.remove(self.current)
            interaction.response.edit_message(
                content=self.describe(),
                view=self
            )

def edit_viewer_for[T](t:Type[T]):
    def wrapper(f:Type[BaseEditView[T]]):
        View.edit_viewer[t]=f
        return f
    return wrapper
def text_renderer_for[T](t:Type[T]):
    def wrapper(f:Callable[[T],str]):
        View.text_renderers[t]=f
        return f
    return wrapper

@dataclasses.dataclass
class AutoUIProp():
    name: str
    description: str
    required:bool = True
    custom_view:BaseEditView|None = None
class annotate:
    registered_props:Dict[Type[Any],Dict[str,AutoUIProp]] = {}
    readable_names:Dict[Type[Any],str] = {}
    def __init__(self, _object_readable_name:str, **kwargs) -> None:
        self.props = kwargs
        self.readable_name = _object_readable_name
    def __call__(self, cls:Type) -> Any:
        for n,p in self.props.items():
            if n not in cls.__annotations__:
                raise LookupError(f"Class {cls} does not have a type-annotated \"{n}\" property!")
            if not isinstance(p,AutoUIProp):
                raise LookupError(f"Each given property must be an instance of `AutoUIProps`!")
        annotate.registered_props[cls]=self.props
        annotate.readable_names[cls]=self.readable_name
        return cls

class view_for:
    def __init__(self, typ:Type) -> None:
        self.type=typ
    def __call__(self, cls:Type) -> Any:
        typ = self.type
        class PartialView(View):
            def __init__(self, done_cb: Callable[[dc.Interaction, Any], Coroutine[Any, Any, Any]], *, timeout: float | None = 360):
                super().__init__(typ, done_cb, timeout=timeout)
        return PartialView

class LongStrView(BaseEditView):
    def confirmed(self):
        return self.value.value
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: Type, *, timeout: float | None = 180):
        super().__init__(cb, req="Must not be empty", timeout=timeout)
        self.value = dc.ui.TextInput(style=dc.TextStyle.long)

@edit_viewer_for(str)
class ShortStrView(BaseEditView):
    def confirmed(self):
        return self.value.value
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: Type, *, timeout: float | None = 180):
        super().__init__(cb, req="Must not be empty", timeout=timeout)
        self.value = dc.ui.TextInput(style=dc.TextStyle.short)

@edit_viewer_for(int)
class IntView(BaseEditView):
    def confirmed(self):
        try:
            return int(self.value.value)
        except:
            return None
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: Type, *, timeout: float | None = 180):
        super().__init__(cb, req="- Must not be empty\n- Must be a number", timeout=timeout)
        self.value = dc.ui.TextInput(style=dc.TextStyle.short)

@edit_viewer_for(Set.__class__)
class SetView(BaseEditView):
    class RemoveView(dc.ui.View):
        def __init__(self, objs:Iterable[Any], cb:Callable[[dc.Interaction,List[Any]],Coroutine[Any,Any,Any]],*, timeout: float | None = 180):
            super().__init__(timeout=timeout)
            self.cb=cb
            self.objs=list(objs)
            self.sel=CBSelect(self.scb,
                options=[
                    dc.SelectOption(
                        label=str(o),
                        value=str(i)
                    )
                    for i,o in enumerate(self.objs)
                ]
            )
        async def scb(self,interaction:dc.Interaction,selected:List[Any]):
            self.cb(interaction,self.objs[int(selected[0])])
    def confirmed(self):
        return self.value
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: Type, *, timeout: float | None = 180):
        super().__init__(cb, req="", timeout=timeout)
        self.value = set()
        self.type=type
    @dc.ui.button(
        label="Remove Item (will show a selection screen)"
    )
    async def manage_items(self,interaction:dc.Interaction,btn:dc.ui.Button):
        await interaction.response.edit_message(
            view = self.__class__.RemoveView(self.value,self.remove_item)
        )
    async def remove_item(self,interaction:dc.Interaction,i:Any):
        self.value.remove(i)
        await interaction.response.edit_message(view=self)
    @dc.ui.button(
        label="Add item"
    )
    async def add_item(self,interaction:dc.Interaction,btn:dc.ui.Button):
        typ = self.type.__args__[0]
        vtyp = typ
        if typ not in View.edit_viewer:
            if (typ.__class__ in View.edit_viewer) and hasattr(typ,'__args__'):
                vtyp = typ.__class__
            else:
                raise TypeError(f"Cannot create custom UI for type {self.type}: {typ} has no registered edit view")
        await interaction.response.edit_message(
            view = View.edit_viewer[vtyp](self.subscreen_cb,typ)
        )
    async def subscreen_cb(self,interaction:dc.Interaction,v:Any):
        self.value.add(v)
        await interaction.response.edit_message(
            view=self
        )