"""Contains small functionalities for other /src/tokens/* modules
"""

from typing import Literal

from src.errors import (
    SyntaxException, SYNTAX_ERR,
    DuplicationException, DUPLICATION_ERR,
)
from src.rules import (
    ALLOWED_RS_CHARS, THREE_LETTER_KEYWORDS, ALLOWED_LINK_CHARS,
    Action, Keyword, ReservedSpace
)
from src.tokens.pointer import Pointer
from src.errorutils import put_errored_code_line
from src.tokens.tokenclass import Token


__all__ = [
    'get_rs_name',
    'find_indent_value',
    'get_link_names_inside_linkRS',
    'make_link_subtokens',
]


def get_rs_name(chars: list[str], line: str, line_index: int) -> str:
    """Finds space name of Reserved space given as string\n
    : or % breaks search as it is encountered, the name is actually finished

    Raises
        `SYNTAX_ERR`
        * Not allowed char (see `rules.ALLOWED_RS_CHARS`)
    """
    space_name = str()
    for char in chars:
        if char in (":", "%"): break
        if char not in ALLOWED_RS_CHARS:
            raise SyntaxException(SYNTAX_ERR, f"Invalid space name syntax: {space_name}", *put_errored_code_line(line, line_index, space_name, 0))
        space_name += char
    return space_name

def get_cs_name(args: list[str], line: str, line_index: int) -> str:
    """Finds the name of custom space, 
    as it starts with $, the first symbol is removed until it encounters '[',
    which signals that it is time for mentioning owner of the function

    Raises
        `SYNTAX_ERR`
        * Not allowed char (see `rules.ALLOWED_CUSTOM_SPACE_CHARS`)
    """
    return args[0][1:]

def find_indent_value(chars: list[str]) -> str:
    """Finds the value of indentation in the code\n
    In a list of chars\n
    Chars should not include any spaces\n
    The value will be at the index of len("_indent")
    """
    return "".join(chars[len("_indent")+1:])

def get_link_names_inside_linkRS(pointer: Pointer, indentation: int) -> list[str]:
    """Finds all links written inside _links Reserved space
    Which can be listed in new line or with commas

    Raises:
        `SYNTAX_ERR`
        * Not three char-long
        * If link overrides a keyword (see `rules.THREE_LETTER_KEYWORDS`)
        * Includes a forbidden character (see `rules.ALLOWED_LINK_CHARS)
        `DUPLICATION_ERR`
        * Two similar links
    """
    links: list[str] = []
    index: int = 1
    next_line, next_line_index = pointer.get_next(index)[index-1]

    while next_line.startswith(' '*indentation): # type: ignore

        line_args: list[str] = [x.strip() for x in next_line.split(',')]

        for arg in line_args:

            if arg[0].isdigit():
                raise SyntaxException(SYNTAX_ERR, f"First char cannot be a digit: {arg[0]}", *put_errored_code_line(next_line, next_line_index, arg[0], 0))

            if arg in THREE_LETTER_KEYWORDS:
                raise SyntaxException(SYNTAX_ERR, f"Cannot override a keyword: {arg}", *put_errored_code_line(next_line, next_line_index, arg, 0))

            if len(arg) != 3:
                raise SyntaxException(SYNTAX_ERR, f"The length of {arg} must be strongly 3 chars", *put_errored_code_line(next_line, next_line_index, arg, 0))
            for char in list(arg):
                if char not in ALLOWED_LINK_CHARS:
                    raise SyntaxException(SYNTAX_ERR, f"The link can not include {char} char", *put_errored_code_line(next_line, next_line_index, char, 0))
        
            if arg in links:
                raise DuplicationException(DUPLICATION_ERR, f"Can not two identical links: {arg}", *put_errored_code_line(next_line, next_line_index, arg, 0))

        links.extend(line_args)
        index += 1
        next_line, next_line_index = pointer.get_next(index)[index-1]

    return links

def make_link_subtokens(links: list[str], line: str, line_index: int)-> list[Token]:
    """Makes tokens with all links given through `links`"""
    return [
        Token(
            Action.Defining,
            ReservedSpace.Links,
            Keyword.LinkDef,
            [
                link,
            ],
            line_index,
            line
        )
        for link in links
    ]

def find_cs_owner(
        chars: list[str], args: list[str], line: str, line_index: int, space_name: str
    ) -> str | Literal[ReservedSpace.Main]:

    # removing from args[1] (which is supposed to be just owner)
    try:
        if chars[len(space_name)] == ":":
            raise SyntaxException(SYNTAX_ERR, f"Missing owner", *put_errored_code_line(line, line_index, chars[len(space_name)], -1))

        if args[1][0] != "[" or args[1][-1] != "]":
            raise SyntaxException(SYNTAX_ERR, f"Custom space initialization must follow with an owner: {space_name}", *put_errored_code_line(line, line_index, space_name[-1], -1))
        
        args[1] = args[1][1:-1]
    except IndexError:
        raise SyntaxError(SYNTAX_ERR, f"Missing owner", *put_errored_code_line(line, line_index, chars[len(space_name)], -1))
    
    return args[1] if args[1] != "_main" else ReservedSpace.Main