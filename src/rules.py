from enum import Enum, auto
import string

from src.errors import RulesBreak, RULES_BREAK


__all__ = [
    'ALLOWED_CHARS', 'MAX_VAR', 'ALLOWED_LINK_CHARS', 'ALLOWED_RS_CHARS', 'ALLOWED_CUSTOM_SPACE_CHARS', 'LINK_CHAR_LEN', 
    'GLOBAL_OWNER', 'ALL_RESERVED_SPACES_AS_STR', 'ALLOWED_INDENTATIONS', 'DEFAULT_INDENTATION', 'THREE_LETTER_KEYWORDS',
    'ALLOWED_SUBTOKEN_INSTRUCTIONS', 
    'Type', 'ReservedSpace', 'Keyword', 'Action',
    'get_type_from_str', 'get_reserved_space_from_str', 'get_str_from_reserved_space', 'get_keyword_from_str',
    'get_str_from_keyword',
]


ALLOWED_CHARS: str = string.ascii_letters + string.digits + f"$_,[]\\!?~<>-=%\n: \"\'()&{{}}"

MAX_VAR = 65535

ALLOWED_LINK_CHARS: str = string.ascii_lowercase + string.digits

ALLOWED_RS_CHARS: str = string.ascii_letters + '_'
ALLOWED_CUSTOM_SPACE_CHARS: str = ALLOWED_RS_CHARS + '$'

LINK_CHAR_LEN = 3

GLOBAL_OWNER = "std"

ALL_RESERVED_SPACES_AS_STR: list[str] = [
    "_indent", "_links", "_consts", "_pre", "_stdin", "_main"
]

ALLOWED_INDENTATIONS: list[int] = [2, 4]
DEFAULT_INDENTATION: int = 4

THREE_LETTER_KEYWORDS: list[str] = [
    "inc", "dec"
]

class Type(Enum):
    Int = auto()
    Char = auto()
    Bool = auto()
    IntArray = auto()
    String = auto() # == char[]

def get_type_from_str(tp: str) -> Type:
    pairs: dict[str, Type] = {
        'int': Type.Int,
        'char': Type.Char,
        'bool': Type.Bool,
        'int[]': Type.IntArray,
        'char[]': Type.String,
    }
    try:
        return pairs[tp]
    except KeyError as exc:
        raise RulesBreak(RULES_BREAK, f"Not a type: {tp}", "", "") from exc

class ReservedSpace(Enum):
    Indent = auto()
    Links = auto()
    Consts = auto()
    Pre = auto()
    Stdin = auto()
    Main = auto()

def get_reserved_space_from_str(rs: str) -> ReservedSpace:
    pairs: dict[str, ReservedSpace] = {
        "_indent": ReservedSpace.Indent,
        "_links": ReservedSpace.Links,
        "_consts": ReservedSpace.Consts,
        "_pre": ReservedSpace.Pre,
        "_stdin": ReservedSpace.Stdin,
        "_main": ReservedSpace.Main
    }
    try:
        return pairs[rs]
    except KeyError as exc:
        raise RulesBreak(RULES_BREAK, f"Not a reserved space: {rs}", "", "") from exc
    
def get_str_from_reserved_space(rs: ReservedSpace) -> str:
    pairs: dict[ReservedSpace, str] = {
        ReservedSpace.Indent: "_indent",
        ReservedSpace.Links: "_links",
        ReservedSpace.Consts: "_consts",
        ReservedSpace.Pre: "_pre",
        ReservedSpace.Stdin: "_stdin",
        ReservedSpace.Main: "_main"
    }
    return pairs[rs]

class Action(Enum):
    Spacing = auto()
    Defining = auto()
    Instruction = auto()
    
class Keyword(Enum):
    SpaceDefine = auto() # _
    List = auto() # ,
    SpaceNameEnd = auto() # :
    OwnershipOpen = auto() # [
    OwnershipClose = auto() # ]
    ArrayOpen = auto() # {
    ArrayClose = auto() # }
    StringOpen = auto() # "
    StringClose = auto() # "
    ReferenceDef = auto() # number that comes first inside _consts, _pre, _stdin
    CustomSpaceDef = auto() # $_
    StdinArgumentInit = auto() # %
    StdinArgumentOpen = auto() # (
    StdioArgumentClose = auto() # )
    LinkOpen = auto() # <
    LinkClose = auto() # >
    LinkDef = auto() # actually an empty symbol. Just for tokenizer to understand
    ComprehensionOpen = auto() # (
    ComprehensionClose = auto() # )
    Refer = auto() # ~
    ReferStdinVar = auto() # &
    VarSet = auto() # ->

    PrintOut = auto() # stdout
    Increase = auto() # inc
    Decrease = auto() # dec
    Call = auto() # call
    Goto = auto() # goto
    IfStatement = auto() # if
    Describe = auto() # desc

ALLOWED_SUBTOKEN_INSTRUCTIONS: list[Keyword] = [
    Keyword.IfStatement,
]

def get_keyword_from_str(kw: str) -> Keyword:
    pairs: dict[str, Keyword] = {
        'stdout': Keyword.PrintOut,
        'inc': Keyword.Increase,
        'dec': Keyword.Decrease,
        'call': Keyword.Call,
        'goto': Keyword.Goto,
        'if': Keyword.IfStatement,
        'desc': Keyword.Describe,
    }
    try:
        return pairs[kw]
    except KeyError as exc:
        raise RulesBreak(RULES_BREAK, "Unknown keyword", "", "") from exc
    
def get_str_from_keyword(kw: Keyword) -> str:
    pairs: dict[Keyword, str] = {
        Keyword.PrintOut: 'stdout', 
        Keyword.Increase: 'inc', 
        Keyword.Decrease: 'dec', 
        Keyword.Call: 'call', 
        Keyword.Goto: 'goto', 
        Keyword.IfStatement: 'if',
        Keyword.Describe: 'desc',
    }
    return pairs[kw]