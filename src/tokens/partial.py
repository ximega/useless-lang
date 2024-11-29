"""Contains sub functions to add to 
/src/tokens/parts.py
"""

from typing import Literal

from src.rules import (
    ReservedSpace, Action, Keyword, Type,
    GLOBAL_OWNER,
    get_reserved_space_from_str,
)
from src.tokens.pointer import Pointer
from src.tokens.tokenclass import Token
from src.tokens.utils import (
    find_indent_value,
    get_link_names_inside_linkRS,
    make_link_subtokens,
    find_var_value,
)
from src.tokens.checks import PartialChecks


__all__ = [
    'tokenize_rs_indent',
    'tokenize_rs_links',
    'tokenize_rs_other',
    'tokenize_referenced_var',
    'tokenize_literal_var',
    'CurSpace',
    'SpacesDict',
]


type CurSpace = str | ReservedSpace
type SpacesDict = dict[CurSpace, Token]


def tokenize_rs_indent(
        chars: list[str], line: str, line_index: int, 
        indentation: int, cur_space: CurSpace | None, spaces: SpacesDict
    ) -> tuple[int, CurSpace, SpacesDict]:
    """Finds the value of indentation in _indent rs.\n
    As it is the only rs
    where writing after : is allowed and it cannot be followed with blocks under it\n
    """
    
    PartialChecks.RsIndent.indent_rs_no_colon(chars, line, line_index)

    indent_val: str = find_indent_value(chars)
    PartialChecks.RsIndent.is_value_given(indent_val, line, line_index)
    PartialChecks.RsIndent.indent_val_is_int(indent_val, line, line_index)
    
    indent: int = int(indent_val)
    PartialChecks.RsIndent.is_allowed_indent(indent, line, line_index)

    # repetition cause pylint complains
    indentation = indent

    cur_space = ReservedSpace.Indent

    spaces[ReservedSpace.Indent] = Token(
        Action.Spacing,
        GLOBAL_OWNER,
        Keyword.SpaceDefine,
        [
            ReservedSpace.Indent
        ],
        line_index,
        line
    )

    return (
        indentation,
        cur_space,
        spaces
    )

def tokenize_rs_links(
        line: str, line_index: int, pointer: Pointer, indentation: int,
        cur_space: CurSpace | None, spaces: SpacesDict
    ) -> tuple[CurSpace, SpacesDict]:
    """The only rs that is tokenized straightaway, 
    instead of later tokenizing with matching self.cur_space
    """

    links: list[str] = get_link_names_inside_linkRS(pointer, indentation)

    cur_space = ReservedSpace.Links

    spaces[ReservedSpace.Links] = Token(
        Action.Spacing,
        GLOBAL_OWNER,
        Keyword.SpaceDefine,
        [
            ReservedSpace.Links
        ],
        line_index,
        line
    ).set_subtokens(make_link_subtokens(links, line, line_index))

    return (
        cur_space,
        spaces
    )

def tokenize_rs_other(
        space_name: str, line: str, line_index: int,
        cur_space: CurSpace | None, spaces: SpacesDict,
    ) -> tuple[CurSpace, SpacesDict]:

    space: ReservedSpace = get_reserved_space_from_str(space_name)

    cur_space = space

    spaces[space] = Token(
        Action.Spacing,
        GLOBAL_OWNER,
        Keyword.SpaceDefine,
        [
            space
        ],
        line_index,
        line
    )  

    return (
        cur_space,
        spaces
    )

def tokenize_referenced_var(
        space: Literal[ReservedSpace.Consts, ReservedSpace.Pre],
        args: list[str], line: str, line_index: int, var_owner: str | Literal[ReservedSpace.Main],
        spaces: SpacesDict, 
    ) -> SpacesDict:
    """Tokenizes variables and puts them as subtokens to either _consts or _pre.\n
    The referenced variables are those, whose value was copied from another value with ~ (reference keyword)
    """

    reference_value_str: str = args[3][1:]
    reference_value_int: int = 0

    PartialChecks.ReferenceVar.four_args_in_var_defining(args, line, line_index)
    PartialChecks.ReferenceVar.reference_is_digit(reference_value_str, line, line_index)
    
    reference_value_int = int(reference_value_str)

    PartialChecks.ReferenceVar.forbidden_chars_in_reference(reference_value_str, reference_value_int, line, line_index)

    spaces[space].add_subtokens([Token(
        Action.Defining,
        var_owner,
        Keyword.VarSet,
        [
            (Keyword.Refer, reference_value_int)
        ],
        line_index,
        line
    )])

    return spaces

def tokenize_literal_var(
        space: Literal[ReservedSpace.Consts, ReservedSpace.Pre],
        args: list[str], line: str, line_index: int, var_type: Type, var_owner: str | Literal[ReservedSpace.Main], 
        spaces: SpacesDict,
    ) -> SpacesDict:
    """Literal values put by manually writing initial values inside _consts or _pre rs
    """

    var_value: str = find_var_value(args, line, line_index, var_type)
    
    spaces[space].add_subtokens([Token(
        Action.Defining,
        var_owner,
        Keyword.VarSet,
        [
            (var_type, var_value)
        ],
        line_index,
        line
    )])

    return spaces