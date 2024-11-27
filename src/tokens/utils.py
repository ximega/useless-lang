"""Contains small functionalities for other /src/tokens/* modules
"""

from typing import Literal, NoReturn
from collections.abc import Callable

from src.errors import (
    SyntaxException, SYNTAX_ERR,
    DuplicationException, DUPLICATION_ERR,
    TokenizerException, TOKENIZER_ERR,
)
from src.rules import (
    ALLOWED_RS_CHARS, THREE_LETTER_KEYWORDS, ALLOWED_LINK_CHARS,
    Action, Keyword, ReservedSpace, Type
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
    """Makes tokens with all links given through _links"""
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
    """Tries to find owner of the custom space (which are defined by initial $ symbol)
    
    Raises:
        `SYNTAX_ERR`
        * No owner found
    """

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

def find_var_value_simpletypes(args: list[str], line: str, line_index: int, var_type: Literal[Type.Int, Type.Bool, Type.Char]) -> str:
    """Finds a value of variable inside _consts or _pre for bool, int, char

    Raises 
        `SYNTAX_ERR`
        * Not int/bool/char value (if corresponding type was set)
        * More than 4 arguments
        * Invalid char declaration (must be with singular apostrophe, from both sides)
    """
    
    if len(args) > 4: 
        raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {line_index}", *put_errored_code_line(line, line_index, args[4], -1))
    
    match var_type:
        case Type.Int:
            if not args[3].isdigit():
                raise SyntaxException(SYNTAX_ERR, "Incorrect value set for int", *put_errored_code_line(line, line_index, args[3], -1))
        case Type.Bool:
            if args[3] not in ('True', 'False', 'Null', 'Vague'):
                raise SyntaxException(SYNTAX_ERR, "Unknown bool value", *put_errored_code_line(line, line_index, args[3], -1))
        case Type.Char:
            if args[3][0] != "\'" or args[3][-1] != "\'":
                raise SyntaxException(SYNTAX_ERR, "Invalid char declaration", *put_errored_code_line(line, line_index, args[3], -1))
            
    return args[3]

def find_var_value_intarray(args: list[str], line: str, line_index: int) -> str:
    """Finds a value of variable inside _consts or _pre for int[]

    Raises
        `SYNTAX_ERR`
        * Not declared with braces "{}"
        * A non-digit included inside braces
    """

    arr_value_str: str = "".join(args[3:]).strip()
        
    if arr_value_str[0] != '{' or arr_value_str[-1] != '}':
        raise SyntaxException(SYNTAX_ERR, f"Invalid array declaration at {line_index}", *put_errored_code_line(line, line_index, arr_value_str, -1))
    
    arr_values: list[str] = arr_value_str[1:-1].split(',')

    for val in arr_values:
        if not val.isdigit():
            raise SyntaxException(SYNTAX_ERR, f"Invalid declaration for int array: {val}", *put_errored_code_line(line, line_index, val, -1))
        
    return arr_value_str

def find_var_value_string(args: list[str], line: str, line_index: int) -> str:
    """Finds a value of variable inside _consts or _pre for char[] (which is string)

    Raises
        `SYNTAX_ERR`
        * String not declared with double-apostrophe, from both sides
    """

    string_str: str = " ".join(args[3:]).strip()

    if string_str[0] != '"' or string_str[-1] != '"':
        raise SyntaxException(SYNTAX_ERR, f"Invalid string declaration at {line_index}", *put_errored_code_line(line, line_index, string_str, -1))
    
    return string_str[1:-1]

def find_var_value(args: list[str], line: str, line_index: int, var_type: Type) -> str:
    def default_call() -> NoReturn:
        raise TokenizerException(TOKENIZER_ERR, f"Unknown type at {line_index}", *put_errored_code_line(line, line_index, line, 0))

    pairs: dict[Type, Callable[..., str]] = {
        Type.Int: find_var_value_simpletypes,
        Type.Bool: find_var_value_simpletypes,
        Type.Char: find_var_value_simpletypes,
        Type.IntArray: find_var_value_intarray,
        Type.String: find_var_value_string,
    }

    return pairs.get(var_type, default_call)() 