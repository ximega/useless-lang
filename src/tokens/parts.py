"""Contains functionality for
/src/tokens/tokenizer.py
"""

from typing import Literal

from src.rules import (
    ReservedSpace, Keyword, Action, Type,
    get_type_from_str,
)
from src.errors import (
    RulesBreak, RULES_BREAK,
)
from src.tokens.pointer import Pointer
from src.errorutils import put_errored_code_line
from src.tokens.tokenclass import Token
from src.tokens.utils import (
    get_rs_name, get_cs_name,
    find_cs_owner,
)
from src.tokens.partial import *
from src.tokens.checks import PartsChecks


__all__ = [
    'tokenize_reserved_spaces',
    'tokenize_custom_spaces',
    'tokenize_subtokens_var',
    'tokenize_subtokens_stdin',
]


def tokenize_reserved_spaces(
        chars: list[str], line: str, line_index: int, pointer: Pointer,            
        indentation: int, cur_space: str | ReservedSpace | None, spaces: dict[str | ReservedSpace, Token]
    ) -> tuple[int, CurSpace, SpacesDict]:
    """Depending on the rs name tokenizes them.\n
    Creates subtokens for _indent and _links straightaway, instead of later self.cur_space matching
    """

    # the current space name is defined 
    space_name: str = get_rs_name(chars, line, line_index)

    # if rs does not exist
    PartsChecks.RsSpace.is_rs(space_name, line, line_index)
    # if the line has anything after : in a reserved space
    # causes an exception
    # _indent does not cause anything, as the value is given straight after :
    PartsChecks.RsSpace.ends_with_colon(space_name, chars, line, line_index)

    # if it is _indent rs
    if space_name == "_indent":
        indentation, cur_space, spaces = tokenize_rs_indent(chars, line, line_index, indentation, cur_space, spaces)
    # _links rs
    elif space_name == "_links":
        cur_space, spaces = tokenize_rs_links(line, line_index, pointer, indentation, cur_space, spaces)
    # the rest of rs 'es
    else:
        cur_space, spaces = tokenize_rs_other(space_name, line, line_index, cur_space, spaces)

    return (indentation, cur_space, spaces)

def tokenize_custom_spaces(
        chars: list[str], args: list[str], line: str, line_index: int,     
        cur_space: str | ReservedSpace | None, spaces: dict[str | ReservedSpace, Token]
    ) -> tuple[CurSpace, SpacesDict]:
    """Spaces definition of which starts with $ are called custom
    """
    
    space_name: str = get_cs_name(args)

    PartsChecks.CustomSpace.not_a_duplicate(space_name, spaces.keys(), line, line_index)

    owner_name: str | Literal[ReservedSpace.Main] = find_cs_owner(chars, args, line, line_index, space_name)

    PartsChecks.CustomSpace.not_a_null_owner(owner_name, line, line_index)
    PartsChecks.CustomSpace.ends_with_colon(chars, line, line_index)
    PartsChecks.CustomSpace.for_allowed_chars(owner_name, line, line_index)

    cur_space = space_name

    spaces[space_name] = Token(
        Action.Spacing,
        owner_name,
        Keyword.SpaceDefine,
        [
            space_name
        ],
        line_index,
        line
    )

    return (cur_space, spaces)

def tokenize_subtokens_var(
        space: Literal[ReservedSpace.Consts, ReservedSpace.Pre],
        args: list[str], line: str, line_index: int, 
        spaces: dict[str | ReservedSpace, Token]
    ) -> SpacesDict:
    """Tokenizes variables and sets them as subtokens to either _consts or _pre"""

    PartsChecks.VarSubtokens.disallowed_args(args, line, line_index)

    var_ref_str: str = args[0]
    PartsChecks.VarSubtokens.is_int(var_ref_str, line, line_index)
    
    var_owner: str | Literal[ReservedSpace.Main] = args[1]
    PartsChecks.VarSubtokens.not_a_null_owner(var_owner, space, line, line_index)

    var_owner = var_owner[1:-1]
    # set to ReservedSpace.Main in case the string given is _main
    if var_owner == "_main": 
        var_owner = ReservedSpace.Main
    
    var_type_str: str = args[2]
    var_type: Type | None = None
    try:
        var_type = get_type_from_str(var_type_str)
    except RulesBreak as exc:
        raise RulesBreak(RULES_BREAK, exc.args[1], *put_errored_code_line(line, line_index, var_type_str, 0)) from exc

    # if the value was referenced with ~
    # then specific path to add will be executed
    # so i mean the following
    if args[3].startswith('~'):
        spaces = tokenize_referenced_var(space, args, line, line_index, int(var_ref_str), var_type, var_owner, spaces)
    else:
        spaces = tokenize_literal_var(space, args, line, line_index, int(var_ref_str), var_type, var_owner, spaces)

    return spaces

def tokenize_subtokens_stdin(
        args: list[str], line: str, line_index: int, 
        spaces: dict[str | ReservedSpace, Token]
    ) -> SpacesDict:
    """Tokenizes subtokens of _stdin"""

    PartsChecks.StdinSubtokens.disallowed_args(args, line, line_index)

    var_ref_str: str = args[0]
    PartsChecks.StdinSubtokens.is_int(var_ref_str, line, line_index)

    var_owner: str | Literal[ReservedSpace.Main] = args[1]
    PartsChecks.StdinSubtokens.not_a_null_owner(var_owner, line, line_index)

    var_type_str: str = args[2]
    var_type: Type | None = None
    try:
        var_type = get_type_from_str(var_type_str)
    except RulesBreak as exc:
        raise RulesBreak(RULES_BREAK, exc.args[1], *put_errored_code_line(line, line_index, var_type_str, 0)) from exc 

    spaces[ReservedSpace.Stdin].add_subtokens([Token(
        Action.Defining,
        var_owner,
        Keyword.VarSet,
        [
            (int(var_ref_str), var_type)
        ],
        line_index,
        line
    )]) 

    return spaces