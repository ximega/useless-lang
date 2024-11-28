from typing import NoReturn
from src.errors import (
    TokenizerException, TOKENIZER_ERR,
    SyntaxException, SYNTAX_ERR,
    DuplicationException, DUPLICATION_ERR,
    RulesBreak, RULES_BREAK,
    OwnershipException, OWNERSHIP_ERR,
)
from src.errorutils import put_errored_code_line
from src.rules import ALLOWED_INDENTATIONS


__all__ = [
    'UtilsChecks',
    'PartialChecks',
    'PartsChecks',
    'TokenizerChecks',
]


class PartialChecks:
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
        
    @staticmethod
    def four_args_in_var_defining(args: list[str], line: str, line_index: int) -> None:
        if len(args) > 4: 
            raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {line_index}", *put_errored_code_line(line, line_index, args[4], -1))
        
    @staticmethod
    def reference_is_digit(reference_value_str: str, line: str, line_index: int) -> None:
        if not reference_value_str.isdigit():
            raise SyntaxException(SYNTAX_ERR, f"Referenced value is not an integer: {reference_value_str}", *put_errored_code_line(line, line_index, reference_value_str, -1))
        
    @staticmethod
    def forbidden_chars_in_reference(reference_value_str: str, reference_value_int: int, line: str, line_index: int) -> None:
        if len(reference_value_str) != len(str(reference_value_int)):
            raise SyntaxException(SYNTAX_ERR, f"Forbidden characters during referencing", *put_errored_code_line(line, line_index, reference_value_str, -1))