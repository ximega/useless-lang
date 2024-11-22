from enum import Enum, auto


LINK_CHAR_LEN = 3

GLOBAL_OWNER = "std"


class Type(Enum):
    Int = auto()
    Char = auto()
    Bool = auto()
    IntArray = auto()
    String = auto() # == char[]
    BoolArray = auto()


class ReservedSpace(Enum):
    Indent = auto()
    Links = auto()
    Consts = auto()
    Pre = auto()
    Stdin = auto()
    Main = auto()


class Keywords(Enum):
    SpaceDefine = auto() # _
    List = auto() # ,
    SpaceNameEnd = auto() # :
    OwnershipOpen = auto() # [
    OwnershipClose = auto() # ]
    ArrayOpen = auto() # [
    ArrayClose = auto() # ]
    StringOpen = auto() # "
    StringClose = auto() # "
    ReferenceDef = auto() # number that comes first inside _consts, _pre, _stdin
    CustomSpaceDef = auto() # $
    StdinArgumentInit = auto() # %
    StdinArgumentOpen = auto() # (
    StdioArgumentClose = auto() # )
    LinkOpen = auto() # <
    LinkClose = auto() # >
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