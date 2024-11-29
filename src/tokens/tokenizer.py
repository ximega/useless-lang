import pprint, re # type: ignore
from typing import Self

from src.rules import *
from src.errors import (
    PointerEnd,
    SyntaxException, SYNTAX_ERR,
)
from src.errorutils import put_errored_code_line
from src.tokens.pointer import Pointer
from src.tokens.utils import *
from src.tokens.tokenclass import Token
from src.tokens.parts import *
from src.tokens.checks import TokenizerChecks
        

__all__ = [
    'Tokenizer',
]


class Tokenizer:
    __instanced = False         

    def __new__(cls, pointer: Pointer) -> Self:
        if cls.__instanced:
            raise TypeError("Cannot create a second lexer")
        cls.__instanced = True
        return super().__new__(cls)
    
    def __init__(self, pointer: Pointer) -> None:
        self.pointer: Pointer = pointer

        self.line_index: int = 0
        self.line: str = ""

        self.line, self.line_index = self.pointer.current()
        self.args: list[str] = self.line.strip().split(' ')
        self.chars: list[str] = [x for x in list(self.line) if x != " "]

        self.indentation: int = DEFAULT_INDENTATION
        self.spaces: dict[str | ReservedSpace, Token] = {}
        self.cur_space: str | ReservedSpace | None = None

    def parse_to_tokens(self) -> list[Token]:
        while True:
            try:
                # any line containing space 
                # cannot start with any type of indentation
                # + line with zero-indent 
                # cannot be anything else than space defining
                TokenizerChecks.is_valid_space_indentation(self.line, self.line_index)

                # reserved spaces
                # all of them are specified in src/rules.py
                # also, they are stored in ALL_RESERVED_SPACES_AS_STR and in ReservedSpace enum
                if self.line.startswith("_"):
                    self.indentation, self.cur_space, self.spaces = tokenize_reserved_spaces(self.chars, self.line, self.line_index, self.pointer, self.indentation, self.cur_space, self.spaces)

                # handling custom spaces
                elif self.line.startswith('$_'):
                    self.cur_space, self.spaces = tokenize_custom_spaces(self.chars, self.args, self.line, self.line_index, self.cur_space, self.spaces)

                # handling definitions and instructions
                elif self.line.startswith(' '*self.indentation):
                    # it may correctly recognize first 2/4 symbols as correct 
                    # but if 5th or later symbols is space again, 
                    # it would mean that indentation is longer than allowed
                    TokenizerChecks.is_valid_instruction_indentation(self.indentation, self.line, self.line_index)

                    # handling _consts rs
                    match self.cur_space:
                        case ReservedSpace.Consts | ReservedSpace.Pre:
                            self.spaces = tokenize_subtokens_var(self.cur_space, self.args, self.line, self.line_index, self.spaces)
                        case ReservedSpace.Pre:
                            self.spaces = tokenize_subtokens_var(self.cur_space, self.args, self.line, self.line_index, self.spaces)
                        case ReservedSpace.Stdin:
                            # TODO: to implement
                            pass
                        case ReservedSpace.Links | ReservedSpace.Indent:
                            pass # it is already handled above with src.tokens.partial.tokenize_reserved_spaces()
                        case ReservedSpace.Main:
                            # TODO: to implement
                            pass 
                        case _:
                            # custom spaces
                            # TODO: to implement
                            pass

                else:
                    TokenizerChecks.invalid_indentations(self.indentation, self.line, self.line_index)

                    raise SyntaxException(SYNTAX_ERR, f"Unknown token at {self.line_index}", *put_errored_code_line(self.line, self.line_index, self.line, 0))

                self.pointer.move()
                self.line, self.line_index = self.pointer.current()
                self.args: list[str] = self.line.strip().split(' ')
                self.chars: list[str] = [x for x in list(self.line) if x != " "]

            except PointerEnd:   
                break

        return list(self.spaces.values())

