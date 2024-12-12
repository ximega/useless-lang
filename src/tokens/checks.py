from collections.abc import KeysView
from typing import Literal

from src.errors import (
    TokenizerException, TOKENIZER_ERR,
    SyntaxException, SYNTAX_ERR,
    DuplicationException, DUPLICATION_ERR,
    OwnershipException, OWNERSHIP_ERR,
)
from src.errorutils import put_errored_code_line
from src.rules import (
    ALLOWED_INDENTATIONS, ALL_RESERVED_SPACES_AS_STR, ALLOWED_CUSTOM_SPACE_CHARS, ALLOWED_RS_CHARS, 
    THREE_LETTER_KEYWORDS, ALLOWED_LINK_CHARS,
    ReservedSpace,
)


__all__ = [
    'UtilsChecks',
    'PartialChecks',
    'PartsChecks',
    'TokenizerChecks',
]


class UtilsChecks:
    @staticmethod
    def allowed_rs_chars(space_name: str, char: str, line: str, line_index: int) -> None:
        if char not in ALLOWED_RS_CHARS:
            raise SyntaxException(SYNTAX_ERR, f"Invalid space name: {space_name}", *put_errored_code_line(line, line_index, space_name, 0))
        
    class LinkName:
        @staticmethod
        def first_not_digit(arg: str, next_line: str, next_line_index: int) -> None:
            if arg[0].isdigit():
                raise SyntaxException(SYNTAX_ERR, f"First char cannot be a digit: {arg[0]}", *put_errored_code_line(next_line, next_line_index, arg[0], 0))
            
        @staticmethod
        def not_override_kw(arg: str, next_line: str, next_line_index: int) -> None:
            if arg in THREE_LETTER_KEYWORDS:
                raise SyntaxException(SYNTAX_ERR, f"Cannot override a keyword: {arg}", *put_errored_code_line(next_line, next_line_index, arg, 0))

        @staticmethod
        def is_3_char_long(arg: str, next_line: str, next_line_index: int) -> None:
            if len(arg) != 3:
                raise SyntaxException(SYNTAX_ERR, f"The length of {arg} must be strongly 3 chars", *put_errored_code_line(next_line, next_line_index, arg, 0))
        
        @staticmethod
        def for_allowed_chars(arg: str, next_line: str, next_line_index: int) -> None:
            for char in list(arg):
                if char not in ALLOWED_LINK_CHARS:
                    raise SyntaxException(SYNTAX_ERR, f"The link can not include {char} char", *put_errored_code_line(next_line, next_line_index, char, 0))
                
        @staticmethod
        def not_a_duplicate(arg: str, links: list[str], next_line: str, next_line_index: int) -> None:
            if arg in links:
                raise DuplicationException(DUPLICATION_ERR, f"Can not two identical links: {arg}", *put_errored_code_line(next_line, next_line_index, arg, 0))
            
    class FindCsOwner:
        @staticmethod
        def owner_not_after_colon(chars: list[str], space_name: str, line: str, line_index: int) -> None:
            if chars[len(space_name)] == ":":
                raise SyntaxException(SYNTAX_ERR, f"Missing owner", *put_errored_code_line(line, line_index, chars[len(space_name)], -1))
            
        @staticmethod
        def follows_with_owner(args: list[str], space_name: str, line: str, line_index: int) -> None:
            if args[1][0] != "[" or args[1][-2:] != "]:":
                print(args)
                raise SyntaxException(SYNTAX_ERR, f"Custom space initialization must follow with an owner: {space_name}", *put_errored_code_line(line, line_index, space_name[-1], -1))

    class VarValue:
        class Simpletypes:
            @staticmethod
            def four_args_in_var_defining(args: list[str], line: str, line_index: int) -> None:
                if len(args) > 4:
                    raise TokenizerException(TOKENIZER_ERR, f"Unexpected token argument at {line_index}", *put_errored_code_line(line, line_index, args[4], -1))
                
            @staticmethod
            def for_int_is_integer(arg: str, line: str, line_index: int) -> None:
                if not arg.isdigit():
                    raise SyntaxException(SYNTAX_ERR, "Incorrect value set for int", *put_errored_code_line(line, line_index, arg, -1))

            @staticmethod
            def for_bool_is_bool(arg: str, line: str, line_index: int) -> None:
                if arg not in ('True', 'False', 'Null', 'Vague'):
                    raise SyntaxException(SYNTAX_ERR, "Unknown bool value", *put_errored_code_line(line, line_index, arg, -1))
            
            @staticmethod
            def for_char_is_char(arg: str, line: str, line_index: int) -> None:
                if (arg[0] != "\'" or arg[-1] != "\'") or (arg[1] != '\\' and len(arg) != 3) or (arg[1] == '\\' and len(arg) != 4):
                    raise SyntaxException(SYNTAX_ERR, "Invalid char declaration", *put_errored_code_line(line, line_index, arg, -1))
        
        class Intarray:
            @staticmethod
            def is_valid_declaration(arr_value_str: str, line: str, line_index: int) -> None:
                if arr_value_str[0] != '{' or arr_value_str[-1] != '}':
                    raise SyntaxException(SYNTAX_ERR, f"Invalid array declaration at {line_index}", *put_errored_code_line(line, line_index, arr_value_str, -1))
                
            @staticmethod
            def all_values_int(arr_values: list[str], line: str, line_index: int) -> None:
                for val in arr_values:
                    if not val.isdigit():
                        raise SyntaxException(SYNTAX_ERR, f"Invalid declaration for int array: {val}", *put_errored_code_line(line, line_index, val, -1))

        @staticmethod
        def is_valid_string_declaration(string_str: str, line: str, line_index: int) -> None:
            if string_str[0] != '"' or string_str[-1] != '"':
                raise SyntaxException(SYNTAX_ERR, f"Invalid string declaration at {line_index}", *put_errored_code_line(line, line_index, string_str, -1))

class PartialChecks:
    class RsIndent:
        @staticmethod
        def indent_rs_no_colon(chars: list[str], line: str, line_index: int) -> None: 
            if chars[len("_indent")] != ":":
                raise SyntaxException(SYNTAX_ERR, "Expected a colon after _indent", *put_errored_code_line(line, line_index, "t", 0))     
            
        @staticmethod
        def is_value_given(indent_val: str, line: str, line_index: int) -> None:
            if indent_val.strip() == "":
                raise SyntaxException(SYNTAX_ERR, "No value given to _indent. Either remove the line or specify the value", *put_errored_code_line(line, line_index, line[-1], 0))
            
        @staticmethod
        def indent_val_is_int(indent_val: str, line: str, line_index: int) -> None:
            if not indent_val.isdigit():
                raise SyntaxException(SYNTAX_ERR, "The value of _indent must be an integer", *put_errored_code_line(line, line_index, indent_val, -1))
        
        @staticmethod
        def is_allowed_indent(indent: int, line: str, line_index: int) -> None:
            if indent not in ALLOWED_INDENTATIONS:
                raise SyntaxException(SYNTAX_ERR, f"Indentation must be one of {", ".join([str(x) for x in ALLOWED_INDENTATIONS])}", *put_errored_code_line(line, line_index, str(indent), -1))
            
    class ReferenceVar:  
        @staticmethod
        def four_args_in_var_defining(args: list[str], line: str, line_index: int) -> None:
            UtilsChecks.VarValue.Simpletypes.four_args_in_var_defining(args, line, line_index)
            
        @staticmethod
        def reference_is_digit(reference_value_str: str, line: str, line_index: int) -> None:
            if not reference_value_str.isdigit():
                raise SyntaxException(SYNTAX_ERR, f"Referenced value is not an integer: {reference_value_str}", *put_errored_code_line(line, line_index, reference_value_str, -1))
            
        @staticmethod
        def forbidden_chars_in_reference(reference_value_str: str, reference_value_int: int, line: str, line_index: int) -> None:
            if len(reference_value_str) != len(str(reference_value_int)):
                raise SyntaxException(SYNTAX_ERR, f"Forbidden characters during referencing", *put_errored_code_line(line, line_index, reference_value_str, -1))
            
class PartsChecks:
    class RsSpace:
        @staticmethod
        def is_rs(space_name: str, line: str, line_index: int) -> None:
            if space_name not in ALL_RESERVED_SPACES_AS_STR:
                raise SyntaxException(SYNTAX_ERR, f"Not a reserved space: {space_name}", *put_errored_code_line(line, line_index, space_name, 0))
        
        @staticmethod
        def ends_with_colon(space_name: str, chars: list[str], line: str, line_index: int) -> None:
            if chars[-1] != ":" and line[0:len("_indent")] != "_indent":
                raise SyntaxException(SYNTAX_ERR, f"Space {space_name} must end with a colon", *put_errored_code_line(line, line_index, chars[-1], -1))

    class CustomSpace:
        @staticmethod
        def not_a_duplicate(space_name: str, spaces_keys: KeysView[str | ReservedSpace], line: str, line_index: int) -> None:
            if space_name in spaces_keys:
                raise DuplicationException(DUPLICATION_ERR, f"Can not have two similar spaces: {space_name}", *put_errored_code_line(line, line_index, space_name, 0))
        
        @staticmethod
        def not_a_null_owner(owner_name: str | Literal[ReservedSpace.Main], line: str, line_index: int) -> None:
            if owner_name == "": 
                raise OwnershipException(OWNERSHIP_ERR, f"Can not set a null space as owner", *put_errored_code_line(line, line_index, '[]', -1))
            
        @staticmethod
        def ends_with_colon(chars: list[str], line: str, line_index: int) -> None:
            if chars[-1] != ":":
                raise SyntaxException(SYNTAX_ERR, "Expected a colon", *put_errored_code_line(line, line_index, chars[-1], -1))
            
        @staticmethod
        def for_allowed_chars(owner_name: str | Literal[ReservedSpace.Main], line: str, line_index: int) -> None:
            if owner_name != ReservedSpace.Main:
                for char in owner_name[1:-2]:
                    if char not in ALLOWED_CUSTOM_SPACE_CHARS:
                        raise SyntaxException(SYNTAX_ERR, f"Invalid char at {line_index} for owner", *put_errored_code_line(line, line_index, char, 0))
                    
    class VarSubtokens:
        @staticmethod
        def disallowed_args(args: list[str], line: str, line_index: int) -> None:
            if len(args) < 4: 
                raise SyntaxException(SYNTAX_ERR, f"Expected 4 arguments to define a variable, {len(args)} were given", f"{line_index}| {line}", "^"*(len(line) + len(str(line_index)) + 2))
            
        @staticmethod
        def is_int(var_ref_str: str, line: str, line_index: int) -> None:
            if not var_ref_str.isdigit():
                raise SyntaxException(SYNTAX_ERR, f"Expected integer at reference", *put_errored_code_line(line, line_index, var_ref_str, 0))
            
        @staticmethod
        def not_a_null_owner(var_owner: str, space: Literal[ReservedSpace.Pre, ReservedSpace.Consts], line: str, line_index: int) -> None:
            if var_owner[0] != '[' or var_owner[-1] != ']':
                raise SyntaxException(SYNTAX_ERR, f"Expected owner of {"variable" if space == ReservedSpace.Pre else "const"}", f"{line_index}| {line}", "^"*(len(line) + len(str(line_index)) + 2))
            
    class StdinSubtokens:
        @staticmethod
        def disallowed_args(args: list[str], line: str, line_index: int) -> None:
            if len(args) != 3:
                raise SyntaxException(SYNTAX_ERR, f"Expected 3 arguments to define a variable, {len(args)} were given", f"{line_index}| {line}", "^"*(len(line) + len(str(line_index)) + 2))
            
        @staticmethod
        def is_int(var_ref_str: str, line: str, line_index: int) -> None:
            if not var_ref_str.isdigit():
                raise SyntaxException(SYNTAX_ERR, f"Expected integer at reference", *put_errored_code_line(line, line_index, var_ref_str, 0))

        @staticmethod
        def not_a_null_owner(var_owner: str, line: str, line_index: int) -> None:
            if var_owner[0] != '[' or var_owner[-1] != ']':
                raise SyntaxException(SYNTAX_ERR, f"Expected owner of std input var", f"{line_index}| {line}", "^"*(len(line) + len(str(line_index)) + 2))

class TokenizerChecks:
    @staticmethod
    def is_valid_space_indentation(line: str, line_index: int) -> None:
        if line.startswith(" ") and (line.lstrip() in ("$", "_")):
            raise SyntaxException(SYNTAX_ERR, f"Invalid indentation at {line_index}", *put_errored_code_line(line, line_index, " ", 0))
        
    @staticmethod
    def is_valid_instruction_indentation(indentation: int, line: str, line_index: int) -> None:
        if line[indentation] == ' ': 
            raise SyntaxException(SYNTAX_ERR, f"Invalid indentation, expected {indentation}", *put_errored_code_line(line, line_index, ' ', indentation))

    @staticmethod
    def invalid_indentations(indentation: int, line: str, line_index: int) -> None:
        if line[0] == " ": 
            raise SyntaxException(SYNTAX_ERR, f"Invalid indentation. Expected {indentation} indent", *put_errored_code_line(line, line_index, ' ', 0))