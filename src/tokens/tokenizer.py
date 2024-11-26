import pprint, re # type: ignore
from typing import Literal, Self

from src.rules import *
from src.errors import (
    PointerEnd,
    SyntaxException, 
    TokenizerException, 
    RulesBreak, RULES_BREAK
)
from src.errors import (
    SYNTAX_ERR,
    TOKENIZER_ERR,
)
from src.errorutils import put_errored_code_line
from src.tokens.pointer import Pointer
from src.tokens.utils import *
from src.tokens.tokenclass import Token
from src.tokens.parts import *
        

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
                if self.line.startswith(" ") and (self.line.lstrip() in ("$", "_")):
                    raise SyntaxException(SYNTAX_ERR, f"Invalid indentation at {self.line_index}", *put_errored_code_line(self.line, self.line_index, " ", 0))

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
                    if self.line[self.indentation] == ' ': 
                        raise SyntaxException(SYNTAX_ERR, f"Invalid indentation, expected {self.indentation}", *put_errored_code_line(self.line, self.line_index, ' ', self.indentation))

                    # handling _consts rs
                    if self.cur_space == ReservedSpace.Consts:
                        if len(self.args) < 4: 
                            raise SyntaxException(SYNTAX_ERR, f"Expected 4 arguments to define a constant, {len(self.args)} were given", f"{self.line_index}| {self.line}", "^"*(len(self.line) + len(str(self.line_index)) + 2))

                        const_ref_str: str = self.args[0]
                        if not const_ref_str.isdigit():
                            raise SyntaxException(SYNTAX_ERR, f"Expected integer inside _const at reference", *put_errored_code_line(self.line, self.line_index, const_ref_str, 0))
                        
                        const_owner: str | Literal[ReservedSpace.Main] = self.args[1]
                        if const_owner[0] != '[' or const_owner[-1] != ']':
                            raise SyntaxException(SYNTAX_ERR, f"Expected owner of constant", f"{self.line_index}| {self.line}", "^"*(len(self.line) + len(str(self.line_index)) + 2))
                        else:
                            const_owner = const_owner[1:-1]
                        # reset to ReservedSpace.Main in case the string given is _main
                        if const_owner == "_main": 
                            const_owner = ReservedSpace.Main
                        
                        const_type_str = self.args[2]
                        const_type: Type | None = None
                        try:
                            const_type = get_type_from_str(const_type_str)
                        except RulesBreak as exc:
                            raise RulesBreak(RULES_BREAK, exc.args[1], *put_errored_code_line(self.line, self.line_index, const_type_str, 0)) from exc

                        # if the value was referenced with ~
                        # then specific path to add will be executed
                        # so i mean the following
                        if self.args[3].startswith('~'):
                            reference_value_str = self.args[3][1:]
                            reference_value_int: int = 0

                            if len(self.args) > 4: 
                                raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {self.line_index}", *put_errored_code_line(self.line, self.line_index, self.args[4], -1))
                            
                            if not reference_value_str.isdigit():
                                raise SyntaxException(SYNTAX_ERR, f"Referenced value is not an integer: {reference_value_str}", *put_errored_code_line(self.line, self.line_index, reference_value_str, -1))
                            
                            reference_value_int = int(reference_value_str)

                            if len(reference_value_str) != len(str(reference_value_int)):
                                raise SyntaxException(SYNTAX_ERR, f"Unnecessary characters during referencing", *put_errored_code_line(self.line, self.line_index, reference_value_str, -1))

                            self.spaces[ReservedSpace.Consts].add_subtokens([Token(
                                Action.Defining,
                                const_owner,
                                Keyword.VarSet,
                                [
                                    (Keyword.Refer, reference_value_int)
                                ],
                                self.line_index,
                                self.line
                            )])
                        
                        else:
                            const_value: str = ""

                            if const_type in (Type.Int, Type.Char, Type.Bool):
                                const_value = self.args[3]

                                if len(self.args) > 4: 
                                    raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {self.line_index}", *put_errored_code_line(self.line, self.line_index, self.args[4], -1))
                                
                                match const_type:
                                    case Type.Int:
                                        if not self.args[3].isdigit():
                                            raise SyntaxException(SYNTAX_ERR, "Incorrect value set for int", *put_errored_code_line(self.line, self.line_index, self.args[3], -1))
                                    case Type.Bool:
                                        if self.args[3] not in ('True', 'False', 'Null', 'Vague'):
                                            raise SyntaxException(SYNTAX_ERR, "Unknown bool value", *put_errored_code_line(self.line, self.line_index, self.args[3], -1))
                                    case Type.Char:
                                        if self.args[3][0] != "\'" or self.args[3][-1] != "\'":
                                            raise SyntaxException(SYNTAX_ERR, "Invalid char declaration", *put_errored_code_line(self.line, self.line_index, self.args[3], -1))

                            # int array
                            elif const_type == Type.IntArray:
                                arr_value_str: str = "".join(self.args[3:]).strip()
                                
                                if arr_value_str[0] != '{' or arr_value_str[-1] != '}':
                                    raise SyntaxException(SYNTAX_ERR, f"Invalid array declaration at {self.line_index}", *put_errored_code_line(self.line, self.line_index, arr_value_str, -1))
                                
                                arr_values: list[str] = arr_value_str[1:-1].split(',')

                                for val in arr_values:
                                    if not val.isdigit():
                                        raise SyntaxException(SYNTAX_ERR, f"Invalid declaration for int array: {val}", *put_errored_code_line(self.line, self.line_index, val, -1))
                                    
                                const_value = arr_value_str

                            # strings
                            else:
                                string_str: str = " ".join(self.args[3:]).strip()

                                if string_str[0] != '"' or string_str[-1] != '"':
                                    raise SyntaxException(SYNTAX_ERR, f"Invalid string declaration at {self.line_index}", *put_errored_code_line(self.line, self.line_index, string_str, -1))
                                
                                string_value: str = string_str[1:-1]

                                const_value = string_value
                            
                            self.spaces[ReservedSpace.Consts].add_subtokens([Token(
                                Action.Defining,
                                const_owner,
                                Keyword.VarSet,
                                [
                                    (const_type, const_value)
                                ],
                                self.line_index,
                                self.line
                            )])

                    elif self.cur_space == ReservedSpace.Pre:
                        if len(self.args) < 4: 
                            raise SyntaxException(SYNTAX_ERR, f"Expected 4 arguments to pre-define a variable, {len(self.args)} were given", f"{self.line_index}| {self.line}", "^"*(len(self.line) + len(str(self.line_index)) + 2))

                        var_ref_str: str = self.args[0]
                        if not var_ref_str.isdigit():
                            raise SyntaxException(SYNTAX_ERR, f"Expected integer inside _pre at reference", *put_errored_code_line(self.line, self.line_index, var_ref_str, 0))
                        
                        var_owner: str | Literal[ReservedSpace.Main] = self.args[1]
                        if var_owner[0] != '[' or var_owner[-1] != ']':
                            raise SyntaxException(SYNTAX_ERR, f"Expected owner of variable", f"{self.line_index}| {self.line}", "^"*(len(self.line) + len(str(self.line_index)) + 2))
                        else:
                            var_owner = var_owner[1:-1]
                        # reset to ReservedSpace.Main in case the string given is _main
                        if var_owner == "_main": 
                            var_owner = ReservedSpace.Main
                        
                        var_type_str: str = self.args[2]
                        var_type: Type | None = None
                        try:
                            var_type = get_type_from_str(var_type_str)
                        except RulesBreak as exc:
                            raise RulesBreak(RULES_BREAK, exc.args[1], *put_errored_code_line(self.line, self.line_index, var_type_str, 0)) from exc

                        # if the value was referenced with ~
                        # then specific path to add will be executed
                        # so i mean the following
                        if self.args[3].startswith('~'):
                            reference_value_str: str = self.args[3][1:]
                            reference_value_int: int = 0

                            if len(self.args) > 4: 
                                raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {self.line_index}", *put_errored_code_line(self.line, self.line_index, self.args[4], -1))
                            
                            if not reference_value_str.isdigit():
                                raise SyntaxException(SYNTAX_ERR, f"Referenced value is not an integer: {reference_value_str}", *put_errored_code_line(self.line, self.line_index, reference_value_str, -1))
                            
                            reference_value_int = int(reference_value_str)

                            if len(reference_value_str) != len(str(reference_value_int)):
                                raise SyntaxException(SYNTAX_ERR, f"Unnecessary characters during referencing", *put_errored_code_line(self.line, self.line_index, reference_value_str, -1))

                            self.spaces[ReservedSpace.Pre].add_subtokens([Token(
                                Action.Defining,
                                var_owner,
                                Keyword.VarSet,
                                [
                                    (Keyword.Refer, reference_value_int)
                                ],
                                self.line_index,
                                self.line
                            )])
                            
                        else:
                            var_value: str = ""
                            if var_type in (Type.Int, Type.Char, Type.Bool):
                                var_value = self.args[3]

                                if len(self.args) > 4: 
                                    raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {self.line_index}", *put_errored_code_line(self.line, self.line_index, self.args[4], -1))
                                
                                match var_type:
                                    case Type.Int:
                                        if not self.args[3].isdigit():
                                            raise SyntaxException(SYNTAX_ERR, f"Incorrect value set for int", *put_errored_code_line(self.line, self.line_index, self.args[3], -1))
                                    case Type.Bool:
                                        if self.args[3] not in ('True', 'False', 'Null', 'Vague'):
                                            raise SyntaxException(SYNTAX_ERR, f"Unknown bool value", *put_errored_code_line(self.line, self.line_index, self.args[3], -1))
                                    case Type.Char:
                                        if self.args[3][0] != "\'" or self.args[3][-1] != "\'":
                                            raise SyntaxException(SYNTAX_ERR, f"Invalid char declaration", *put_errored_code_line(self.line, self.line_index, self.args[3], -1))

                            # int array
                            elif var_type == Type.IntArray:
                                arr_value_list: list[str] = self.args[3:]
                                arr_value_str: str = "".join(arr_value_list).strip()
                                
                                if arr_value_str[0] != '{' or arr_value_str[-1] != '}':
                                    raise SyntaxException(SYNTAX_ERR, f"Invalid array declaration at {self.line_index}", *put_errored_code_line(self.line, self.line_index, arr_value_str, -1))
                                
                                arr_values: list[str] = arr_value_str[1:-1].split(',')

                                for val in arr_values:
                                    if not val.isdigit():
                                        raise SyntaxException(SYNTAX_ERR, f"Invalid declaration for int array: {val}", *put_errored_code_line(self.line, self.line_index, val, -1))
                                    
                                var_value = arr_value_str

                            # strings
                            else:
                                string_list: list[str] = self.args[3:]
                                string_str: str = " ".join(string_list).strip()

                                if string_str[0] != '"' or string_str[-1] != '"':
                                    raise SyntaxException(SYNTAX_ERR, f"Invalid string declaration at {self.line_index}", *put_errored_code_line(self.line, self.line_index, string_str, -1))
                                
                                string_value: str = string_str[1:-1]

                                var_value = string_value

                            self.spaces[ReservedSpace.Pre].add_subtokens([Token(
                                Action.Defining,
                                var_owner,
                                Keyword.VarSet,
                                [
                                    (var_type, var_value)
                                ],
                                self.line_index,
                                self.line
                            )])

                    elif self.cur_space == ReservedSpace.Stdin:
                        pass

                    # the rest of instructions
                    else:
                        pass

                else:
                    if self.line[0] == " ": 
                        raise SyntaxException(SYNTAX_ERR, f"Invalid indentation. Expected {self.indentation} indent", *put_errored_code_line(self.line, self.line_index, ' ', 0))

                    raise SyntaxException(SYNTAX_ERR, f"Unknown token at {self.line_index}", f"{self.line_index}| {self.line}", f"{"^"*(len(self.line) + len(str(self.line_index)) + 2)}")

                self.pointer.move()
                self.line, self.line_index = self.pointer.current()
                self.args: list[str] = self.line.strip().split(' ')
                self.chars: list[str] = [x for x in list(self.line) if x != " "]

            except PointerEnd:   
                break

        return list(self.spaces.values())

