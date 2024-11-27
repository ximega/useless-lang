"""Contains sub functions to add to 
/src/tokens/parts.py
"""

from typing import Literal

from src.errorutils import put_errored_code_line
from src.errors import (
    SyntaxException, SYNTAX_ERR,
    TokenizerException, TOKENIZER_ERR,
)
from src.rules import (
    ReservedSpace, Action, Keyword, Type,
    GLOBAL_OWNER, ALLOWED_INDENTATIONS,
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
    
    if chars[len("_indent")] != ":":
        raise SyntaxException(SYNTAX_ERR, "Expected a colon after _indent", *put_errored_code_line(line, line_index, "t", 0))                     
    
    indent_val: str = find_indent_value(chars)

    if indent_val.strip() == "":
        raise SyntaxException(SYNTAX_ERR, "No value given to _indent. Either remove the line or specify the value", *put_errored_code_line(line, line_index, line[-1], 0))

    if not indent_val.isdigit():
        raise SyntaxException(SYNTAX_ERR, "The value of _indent must be an integer", *put_errored_code_line(line, line_index, indent_val, -1))
    
    indent: int = int(indent_val)
    if indent not in ALLOWED_INDENTATIONS:
        raise SyntaxException(SYNTAX_ERR, f"Indentation must be one of {", ".join([str(x) for x in ALLOWED_INDENTATIONS])}", *put_errored_code_line(line, line_index, indent_val, -1))

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

    reference_value_str: str = args[3][1:]
    reference_value_int: int = 0

    if len(args) > 4: 
        raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {line_index}", *put_errored_code_line(line, line_index, args[4], -1))
    
    if not reference_value_str.isdigit():
        raise SyntaxException(SYNTAX_ERR, f"Referenced value is not an integer: {reference_value_str}", *put_errored_code_line(line, line_index, reference_value_str, -1))
    
    reference_value_int = int(reference_value_str)

    if len(reference_value_str) != len(str(reference_value_int)):
        raise SyntaxException(SYNTAX_ERR, f"Unnecessary characters during referencing", *put_errored_code_line(line, line_index, reference_value_str, -1))

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