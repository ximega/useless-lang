"""Simply contains Token class
"""

from typing import Self, Literal

from src.errors import TOKENIZER_ERR, TokenizerException
from src.rules import Action, Keyword, ReservedSpace, Type, ALLOWED_SUBTOKEN_INSTRUCTIONS, get_str_from_keyword
from src.errorutils import put_errored_code_line, format_code_line


__all__ = [
    'Token',
]


type ReferenceValue = int
type VarValue = str
type OtherArg = str

type StdinArg = tuple[ReferenceValue, Type]
type VarArg = tuple[ReferenceValue, Type, VarValue]
type ReferencedValue = tuple[Literal[Keyword.Refer], ReferenceValue]
type ReferencedValueArg = tuple[ReferenceValue, Type, ReferencedValue]

type TokenArguments = list[StdinArg | VarArg | OtherArg | Keyword | ReservedSpace | ReferencedValueArg]


class Token:
    def __init__(self, action: Action, owner: str | ReservedSpace, keyword: Keyword, arguments: TokenArguments, line_index: int, line: str) -> None:
        self.line_index: int = line_index
        self.line: str = line
            
        self.action: Action = action
        self.owner: str | ReservedSpace = owner
        self.keyword: Keyword = keyword
        self.link: str | None = None
        self.arguments: TokenArguments = arguments
        self.subtokens: list[Self] = []

        # for self.arguments:
        # tuple[Type, str] -> variable type with its string annotation
        # tuple[Keyword, int] -> when referencing variable with reference key (~)
        # Keyword -> additional operations
        # ReservedSpace -> when defining spaces
        # str -> for other cases

    def __repr__(self) -> str:
        return f"line_index={self.line_index}, line={self.line}\naction={self.action}, owner={self.owner}, keyword={self.keyword}, link={self.link}, arguments={self.arguments}, {len(self.subtokens)} subtokens\n"
    
    def set_link(self, link: str) -> Self:
        if self.action != Action.Instruction:
            raise TokenizerException(TOKENIZER_ERR, "Cannot set link to non-instruction", format_code_line(self.line, self.line_index), "^"*(len(self.line) + len(str(self.line_index)) + 2))
        self.link = link
        return self
    
    def __check_for_addition_errors(self) -> None:
        if self.action not in (Action.Instruction, Action.Spacing):
            raise TokenizerException(TOKENIZER_ERR, "Cannot add subtokens for non-instruction or non-spacing", f"{self.line_index}| {self.line}", "^"*(len(self.line) + len(str(self.line_index)) + 2))
        if (self.action == Action.Instruction) and (self.keyword not in ALLOWED_SUBTOKEN_INSTRUCTIONS):
            raise TokenizerException(TOKENIZER_ERR, f"Cannot include subtokens under {get_str_from_keyword(self.keyword)}", *put_errored_code_line(self.line, self.line_index, get_str_from_keyword(self.keyword), 0))

    def set_subtokens(self, subtokens: list[Self]) -> Self:
        self.__check_for_addition_errors()
        
        self.subtokens = subtokens
        return self
    
    def add_subtokens(self, subtokens: list[Self]) -> Self:
        self.__check_for_addition_errors()
                    
        self.subtokens.extend(subtokens)
        return self 