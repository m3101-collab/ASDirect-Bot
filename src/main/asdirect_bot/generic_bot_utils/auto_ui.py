"""
Generic tools for creating simple
CRUD UI views for discord
"""

import dataclasses
from typing import Coroutine,TypedDict,Type,Any,Dict,Callable,TypeVar,List,Tuple,Set,Iterable,is_typeddict,Literal
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
    def __init__(self, cb:Callable[[List[str],dc.Interaction],Coroutine[Any,Any,Any]],*, placeholder: str | None = None, min_values: int = 1, max_values: int = 1, options: List[dc.SelectOption] = [], disabled: bool = False, row: int | None = None) -> None:
        super().__init__(placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, disabled=disabled, row=row)
        self.cb=cb
    async def callback(self, interaction: dc.Interaction) -> Any:
        return await self.cb(self.values,interaction)

class BaseEditView[T](dc.ui.View):
    def describe(self)->str:
        return f"[THIS IS A PLACEHOLDER - describe() IS UNSET FOR {type(self)}]"
    def __init__(self, cb:Callable[[dc.Interaction,T],Coroutine[None,None,None]], type:Type=None, content:str="",*, req:str="", timeout: float|None = None, original_interaction:dc.Interaction):
        super().__init__(timeout=timeout)
        self.cb=cb
        self.requirements = req
        self.content=content
        self.orig_interaction = original_interaction
    def confirmed(self):
        return None
    @dc.ui.button(
        label="Cancel",
        row=4,
        style=dc.ButtonStyle.red
    )
    async def cancel(self,interaction:dc.Interaction, btn:dc.ui.Button):
        await self.cb(interaction,None)
    @dc.ui.button(
        label="Confirm",
        row=4,
        style=dc.ButtonStyle.blurple
    )
    async def confirm(self,interaction:dc.Interaction, btn:dc.ui.Button):
        val = self.confirmed()
        if val is None:
            await interaction.response.edit_message(
                embed=dc.Embed(
                    title="Error"
                ).add_field(
                    name="Invalid value",
                    value=self.requirements
                )
            )
        else:
            await self.cb(interaction,val)

class View[T](BaseEditView):
    text_renderers:Dict[Type[Any],Callable[[Any],str]] = {}
    edit_viewer:Dict[Type[Any],Type[BaseEditView]] = {}

    @classmethod
    def resolve_edit_viewer(cls, typ:Type)->Type[BaseEditView]:
        if typ in View.edit_viewer:
            return View.edit_viewer[typ]
        elif hasattr(typ,"__origin__") and (typ.__origin__ in View.edit_viewer):
            return View.edit_viewer[typ.__origin__]
        else:
            raise TypeError(f"Type {typ} has no registered edit viewer.")
    @classmethod
    def resolve_text_renderer(cls, typ:Type,default:Callable[[Any],str]|None = None)->Callable[[Any],str]:
        if typ in View.text_renderers:
            return View.text_renderers[typ]
        elif hasattr(typ,"__origin__") and (typ.__origin__ in View.text_renderers):
            return View.text_renderers[typ.__origin__]
        else:
            if default is not None:
                return default
            raise TypeError(f"Type {typ} has no registered text renderer.")

    def generate_typed_dict(self)->T:
        return self.values
    def generate_dataclass(self)->T:
        return self.structure(*self.values)
    def __init__(self, done_cb:Callable[[dc.Interaction,T],Coroutine[Any,Any,Any]], structure:Type[T],content:str="",*, timeout: float|None = None, original_interaction:dc.Interaction):
        super().__init__(done_cb,structure,content,req="All missing properties must be set.",original_interaction=original_interaction)
        self.done_cb=done_cb
        self.structure = structure
        self.orig_interaction = original_interaction
        self.generate:Callable[[],T] = lambda :None
        if is_typeddict(structure):
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
        self.values:Dict[str,Any] = {'__actualtype__':structure}
        self.types:Dict[str,Type] = {}
        self.viewtypes:Dict[str,Type] = {}
        self.options:Dict[str,str] = {} #prop name -> readable name
        self.props:Dict[str,AutoUIProp] = (
            annotate.registered_props[structure] 
            if structure in annotate.registered_props
            else {}
        )
        self.descriptions:Dict[str,str] = {}
        self.missing:Set[str] = set()

        for p,t in structure.__annotations__.items():
            self.types[p] = t
            if t not in View.edit_viewer:
                if (hasattr(t,'__origin__')) and (t.__origin__ in View.edit_viewer) and hasattr(t,'__args__'):
                    self.viewtypes[p] = t.__origin__
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
                for k,v in self.options.items()
            ]
        )
        self.add_item(self.selector)
    def confirmed(self):
        if(len(self.missing)==0):
            return self.generate()
        else:
            return None
    async def cb_select(self,opt:List[str],interaction:dc.Interaction):
        opt:str=opt[0]
        self.current=opt
        viewer = View.edit_viewer[self.viewtypes[opt]]
        view = viewer(self.set,type=self.types[opt],original_interaction=self.orig_interaction)
        view.content=(
            (
                f"### {self.props[opt].name}\n{self.props[opt].description}"
                if opt in self.props
                else f"### {opt}"
            )
        )
        await interaction.response.edit_message(
            content=view.content+'\n'+view.describe(),
            view=view
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
            ((
                "\n## Missing\nThe following required settings are missing:\n"
                +
                "\n".join(
                    f"- {self.options[k]}"
                    for k in self.missing
                )
            ) if len(self.missing) != 0 else "")
            +
            ((
                "\n## Current values\n\n"
                +
                "\n".join(
                    f"- {k}: {description}"
                    for k,v in [(k,v) for k,v in self.values.items() if k!='__actualtype__']
                    for type in [self.viewtypes[k]]
                    for describer in [
                        View.resolve_text_renderer(type,lambda a:f"No text renderer for {type}")
                    ]
                    for description in [describer(v)]
                )
            ))
            +
            "\nSelect a property to edit:"
        )
    async def set(self, interaction:dc.Interaction,value:Any):
        if value is None:
            await interaction.response.edit_message(
                content=(
                    self.content+"\n"+self.describe()
                ),
                view=self
            )
        else:
            self.values[self.current]=value
            if self.current in self.missing:
                self.missing.remove(self.current)
            await interaction.response.edit_message(
                content=self.content+"\n"+self.describe(),
                view=self,
                embed=None
            )

def edit_viewer_for[T](t:Type[T]):
    def wrapper(f:Type[BaseEditView[T]]):
        assert issubclass(f,BaseEditView), f"The class must be an instance of BaseEditView! ({f} isn't)"
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
    required:bool = False
    custom_view:Type[BaseEditView]|None = None
class annotate:
    registered_props:Dict[Type[Any],Dict[str,AutoUIProp]] = {}
    readable_names:Dict[Type[Any],str] = {}
    def __init__(self, _object_readable_name:str, **kwargs) -> None:
        self.props = kwargs
        self.readable_name = _object_readable_name
    def __call__[T](self, cls:T) -> T:
        for n,p in self.props.items():
            if n not in cls.__annotations__:
                raise LookupError(f"Class {cls} does not have a type-annotated \"{n}\" property!")
            if not isinstance(p,AutoUIProp):
                raise LookupError(f"Each given property must be an instance of `AutoUIProps`!")
        annotate.registered_props[cls]=self.props
        annotate.readable_names[cls]=self.readable_name
        return cls

class obsolete_view_for[T]:
    def __init__(self, typ:Type) -> None:
        self.type=typ
    def __call__(self, cls:Type) -> Type[BaseEditView[T]]:
        typ = self.type
        class PartialView(BaseEditView[T]):
            def __init__(self, done_cb: Callable[[dc.Interaction, Any], Coroutine[Any, Any, Any]], *, timeout: float|None = None):
                super().__init__(typ, done_cb, timeout=timeout)
        return PartialView
class auto_view[T]:
    def __init__(self, typ:Type) -> None:
        self.type=typ
    def __call__(self, cls: Type) -> Type[View[T]]:
        typ = self.type
        class AutoView(View[T]):
            def __init__(self, done_cb: Callable[[dc.Interaction[dc.Client], T], Coroutine[Any, Any, Any]], _typ:Type, *, timeout: float|None = None, original_interaction:dc.Interaction):
                super().__init__(done_cb, typ, timeout=timeout,original_interaction=original_interaction)
        return AutoView
class auto_view_for[T]:
    def __init__(self,typ:Type[T]):
        self.type=typ
    def __call__(self, c:Type)->Type[View[T]]:
        return edit_viewer_for(self.type)(auto_view(self.type)(c))

class LongStrView(BaseEditView[str]):
    def describe(self) -> str:
        return "Due to discord UI limitations, please click the button below for a text input field.\n"+(f"```{self.value}```" if self.value is not None else "")
    def confirmed(self):
        return self.value
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: Type=str,content:str="", *, timeout: float|None = None, original_interaction:dc.Interaction):
        super().__init__(cb, req="Must not be empty", content=content, timeout=timeout,original_interaction=original_interaction)
        self.value=""
    async def submitted(self,interaction:dc.Interaction,text:str):
        self.value = text
        await interaction.response.edit_message(content=self.content+"\n"+self.describe())
    @dc.ui.button(label="Open Modal")
    async def show_modal(self,interaction:dc.Interaction,btn):
        parent=self
        class Modal(dc.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="Text Input")
                self.value = dc.ui.TextInput(label="",style=dc.TextStyle.paragraph)
                self.add_item(self.value)
            async def on_submit(self, interaction: dc.Interaction) -> Coroutine[Any, Any, None]:
                await parent.submitted(interaction,self.value.value)
        await interaction.response.send_modal(Modal())
@edit_viewer_for(str)
class ShortStrView(BaseEditView[str]):
    def describe(self) -> str:
        return "Due to discord UI limitations, please click the button below for a text input field.\n"+(f"```{self.value}```" if self.value is not None else "")
    def confirmed(self):
        return self.value
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: Type=str,content:str="", *, timeout: float|None = None, original_interaction:dc.Interaction):
        super().__init__(cb, req="Must not be empty", content=content, timeout=timeout,original_interaction=original_interaction)
        self.value=""
    async def submitted(self,interaction:dc.Interaction,text:str):
        self.value = text
        await interaction.response.edit_message(content=self.content+"\n"+self.describe())
    @dc.ui.button(label="Open Modal")
    async def show_modal(self,interaction:dc.Interaction,btn):
        parent=self
        class Modal(dc.ui.Modal):
            def __init__(self) -> None:
                super().__init__(title="Text Input")
                self.value = dc.ui.TextInput(label="",style=dc.TextStyle.short)
                self.add_item(self.value)
            async def on_submit(self, interaction: dc.Interaction) -> Coroutine[Any, Any, None]:
                await parent.submitted(interaction,self.value.value)
        await interaction.response.send_modal(Modal())

@edit_viewer_for(int)
class IntView(BaseEditView[int]):
    def confirmed(self):
        try:
            return int(self.value.value)
        except:
            return None
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: Type, content:str="", *, timeout: float|None = None, original_interaction:dc.Interaction):
        super().__init__(cb, req="- Must not be empty\n- Must be a number", content=content, timeout=timeout, original_interaction=original_interaction)
        self.value = dc.ui.TextInput(label="Type a number:",style=dc.TextStyle.short)
        self.add_item(self.value)

@edit_viewer_for(Literal)
class LiteralView(BaseEditView[str]):
    def describe(self) -> str:
        return "Please select an option below" if self.selected is None else f"Current option: {self.selected}"
    def confirmed(self):
        return self.choices.values[0] if len(self.choices.values)>0 else None
    def __init__(self, cb: Callable[[dc.Interaction[dc.Client], str], Coroutine[None, None, None]], type: Type = None, content: str = "", *, timeout: float|None = None, original_interaction:dc.Interaction):
        super().__init__(cb, type, content, req="You must select an option", timeout=timeout,original_interaction=original_interaction)
        assert hasattr(type,"__args__"), f"Can only make Literal views for Literals. {type} is not a Literal."
        self.selected:str|None = None
        self.choices = CBSelect(
            self.select_cb,
            options=[
                dc.SelectOption(
                    label = opt,
                    value = opt,
                    description = ""
                )
                for opt in type.__args__
            ]
        )
        self.add_item(self.choices)
    async def select_cb(self,selected:List[str],interaction:dc.Interaction):
        self.selected = selected[0]
        await interaction.response.edit_message(content = self.content+"\n"+self.describe(),view=self)

@edit_viewer_for(list)
class SetView(BaseEditView[list]):
    def describe(self) -> str:
        if len(self.value) == 0 :
            return "Set is currently empty."
        else:
            return (
                "\n## Values:\n"+
                View.resolve_text_renderer(type(self.value))(self.value)
            )
    class RemoveView(dc.ui.View):
        def __init__(self, objs:Iterable[Any], cb:Callable[[dc.Interaction,List[Any]],Coroutine[Any,Any,Any]],*, timeout: float|None = None, original_interaction:dc.Interaction):
            super().__init__(timeout=timeout,original_interaction=original_interaction)
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
    def __init__(self, cb: Callable[[dc.Interaction, Any], Coroutine[None, None, None]], type: Type, content:str="", *, timeout: float|None = None, original_interaction:dc.Interaction):
        super().__init__(cb, content=content, req="", timeout=timeout,original_interaction=original_interaction)
        self.value = []
        self.orig_interaction = original_interaction
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
            if hasattr(typ,"__origin__") and (typ.__origin__ in View.edit_viewer) and hasattr(typ,'__args__'):
                vtyp = typ.__origin__
            else:
                raise TypeError(f"Cannot create custom UI for type {self.type}: {typ} has no registered edit view")
        viewer = View.edit_viewer[vtyp](self.subscreen_cb,typ,original_interaction=self.orig_interaction)
        viewer.content = ""
        await interaction.response.edit_message(
            view = viewer,
            content = viewer.content+viewer.describe(),
            embed=None
        )
    async def subscreen_cb(self,interaction:dc.Interaction,v:Any):
        self.value.append(v)
        await interaction.response.edit_message(
            content=self.content+self.describe(),
            view=self,
            embed=None
        )

def cleanup_dict(v:Dict)->Dict:
    if "__actualtype__" in v:
        del v['__actualtype__']
    for k,i in v.items():
        if type(i)==dict:
            v[k]=cleanup_dict(i)
        else:
            if type(i)!=str:
                try:
                    iter(i)
                    v[k]=[t if type(t)!=dict else cleanup_dict(t) for t in i]
                except:
                    continue
    return v

@text_renderer_for(float)
@text_renderer_for(int)
def RenderStringify(v:Any)->str:
    return str(v)
@text_renderer_for(str)
@text_renderer_for(Literal)
def RenderString(v:str)->str:
    return v
@text_renderer_for(list)
def RenderList(v:List[Any]):
    return ",".join([View.resolve_text_renderer(type(i))(i) for i in v])
@text_renderer_for(dict)
def RenderDict(v:Dict):
    if "__actualtype__" in v:
        try:
            return View.resolve_text_renderer(v['__actualtype__'])(v)
        except:
            pass
    return str(v)
@text_renderer_for(type(None))
@text_renderer_for(None)
def RenderNone(v:None):
    return "Nothing"