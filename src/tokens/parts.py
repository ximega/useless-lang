"""Contains functionality for
/src/tokens/tokenizer.py
"""

from typing import Literal

from src.rules import (
    ReservedSpace, Keyword, Action,
    ALL_RESERVED_SPACES_AS_STR, ALLOWED_CUSTOM_SPACE_CHARS
)
from src.errors import (
    SyntaxException, SYNTAX_ERR,
    DuplicationException, DUPLICATION_ERR,
    OwnershipException, OWNERSHIP_ERR,
)
from src.tokens.pointer import Pointer
from src.errorutils import put_errored_code_line
from src.tokens.tokenclass import Token
from src.tokens.utils import (
    get_rs_name, get_cs_name,
    find_cs_owner,
)
from src.tokens.partial import *


__all__ = [
    'tokenize_reserved_spaces',
    'tokenize_custom_spaces',
]


def tokenize_reserved_spaces(
        chars: list[str], line: str, line_index: int, pointer: Pointer,            
        indentation: int, cur_space: str | ReservedSpace | None, spaces: dict[str | ReservedSpace, Token]
    ) -> tuple[int, CurSpace, SpacesDict]:

    # the current space name is defined 
    space_name: str = get_rs_name(chars, line, line_index)

    # if rs does not exist
    if space_name not in ALL_RESERVED_SPACES_AS_STR:
        raise SyntaxException(SYNTAX_ERR, f"Not a reserved space: {space_name}", *put_errored_code_line(line, line_index, space_name, 0))
    # if the line has anything after : in a reserved space
    # causes an exception
    # _indent does not cause anything, as the value is given straight after :
    if chars[-1] != ":" and line[0:len("_indent")] != "_indent":
        raise SyntaxException(SYNTAX_ERR, f"Space {space_name} must end with a colon", *put_errored_code_line(line, line_index, chars[-1], -1))

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
    
    space_name: str = get_cs_name(args, line, line_index)

    if space_name in spaces.keys():
        raise DuplicationException(DUPLICATION_ERR, f"Can not have two similar spaces: {space_name}", *put_errored_code_line(line, line_index, space_name, 0))

    owner_name: str | Literal[ReservedSpace.Main] = find_cs_owner(chars, args, line, line_index, space_name)

    if owner_name == "": 
        raise OwnershipException(OWNERSHIP_ERR, f"Can not set a null space as owner", *put_errored_code_line(line, line_index, '[]', -1))

    if chars[-1] != ":":
        raise SyntaxException(SYNTAX_ERR, "Expected a colon", *put_errored_code_line(line, line_index, chars[-1], -1))

    if owner_name != ReservedSpace.Main:
        for char in owner_name:
            if char not in ALLOWED_CUSTOM_SPACE_CHARS:
                raise SyntaxException(SYNTAX_ERR, f"Invalid char at {line_index} for owner", *put_errored_code_line(line, line_index, char, 0))

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