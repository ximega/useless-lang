from typing import Self


from rules import *


class PointerEnd(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class TokenizerException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SyntaxException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

def highlight_errored_word(line: str, match_word: str, occur_index: int) -> str:
    matched: list[int] = []
    for x in line.split(' '):
        if x == match_word:
            matched.append(list(line).index(match_word))

    if len(matched) == 0: 
        raise TokenizerException(f"There is no word to match, to be highlighted\n\n{line}")
    
    return " "*(matched[occur_index]) + "^"*len(match_word)    

class Pointer:
    __instanced = False

    def __new__(cls, lines: list[str]) -> Self:
        if cls.__instanced:
            raise ValueError("Cannot create a second pointer")
        cls.__instanced = True
        return super().__new__(cls)

    def __init__(self, lines: list[str]) -> None:
        formatted_lines: list[str] = []

        for line in lines:
            is_with_comment = False
            chars: list[str] = list(line)
            for index, char in enumerate(chars):
                if not is_with_comment:
                    if char == "/" and chars[index+1] == "/":
                        is_with_comment = True
                        formatted_lines.append(line[index:])
            if not is_with_comment:
                formatted_lines.append(line)
        
        self.lines: list[str] = formatted_lines
        self.index = 0
        self.cur_line: str = self.lines[self.index]

    def current(self) -> tuple[str, int]:
        return (
            self.cur_line,
            self.index+1
        )

    def move(self) -> None:
        if self.index == len(self.lines) - 1: 
            raise PointerEnd()
        self.index += 1
        self.cur_line = self.lines[self.index]
    
    def back(self, times: int) -> None:
        if self.index - times <= 0: 
            self.index = 0
        self.index -= times
        self.cur_line = self.lines[self.index]
    
class Token:
    def __init__(self, action: Action, owner: str | ReservedSpace, keyword: Keyword, arguments: list[tuple[Type, str] | Keyword | ReservedSpace | str], line_index: int, line: str) -> None:
        self.line_index: int = line_index
        self.line: str = line
            
        self.action: Action = action
        self.owner: str | ReservedSpace = owner
        self.keyword: Keyword = keyword
        self.link: str | None = None
        self.arguments: list[tuple[Type, str] | Keyword | ReservedSpace | str] = arguments
        self.subtokens: list[Token] = []

    def __repr__(self) -> str:
        return f"{self.line_index=}, {self.line=}\n{self.action=}, {self.owner=}, {self.keyword=}, {self.link=}, {self.arguments=}, {len(self.subtokens)} subtokens"
    
    def set_link(self, link: str) -> Self:
        if self.action != Action.Instruction:
            raise TokenizerException(f"Cannot set link to non-instruction\n\n{self.line_index}| {self.line}")
        self.link = link
        return self

    def set_subtokens(self, subtokens: list["Token"]) -> Self:
        if self.action not in (Action.Instruction, Action.Spacing):
            raise TokenizerException(f"Cannot set subtokens for non-instruction or non-spacing\n\n{self.line_index}| {self.line}")
        if (self.action == Action.Instruction) and (self.keyword not in ALLOWED_SUBTOKEN_INSTRUCTION):
            raise TokenizerException(f"Cannot include subtokens under {get_str_from_keyword(self.keyword)}\n\n{self.line_index}| {self.line}\n{highlight_errored_word(self.line, get_str_from_keyword(self.keyword), 0)}")
                    
        self.subtokens = subtokens
        return self
    
    def add_subtokens(self, subtokens: list["Token"]) -> Self:
        if self.action not in (Action.Instruction, Action.Spacing):
            raise TokenizerException(f"Cannot add subtokens for non-instruction or non-spacing\n\n{self.line_index}| {self.line}")
        if (self.action == Action.Instruction) and (self.keyword not in ALLOWED_SUBTOKEN_INSTRUCTION):
            raise TokenizerException(f"Cannot include subtokens under {get_str_from_keyword(self.keyword)}\n\n{self.line_index}| {self.line}\n{highlight_errored_word(self.line, get_str_from_keyword(self.keyword), 0)}")
                    
        self.subtokens.extend(subtokens)
        return self 
        

class Tokenizer:
    __instanced = False         

    def __new__(cls, pointer: Pointer) -> Self:
        if cls.__instanced:
            raise TypeError("Cannot create a second lexer")
        cls.__instanced = True
        return super().__new__(cls)
    
    def __init__(self, pointer: Pointer) -> None:
        self.pointer: Pointer = pointer

    def parse_to_tokens(self) -> list[Token]:
        indentation: int = DEFAULT_INDENTATION
        spaces: list[Token] = []
        instructions: list[Token] = []
        defining: list[Token] = []

        while True:
            try:
                line, line_index = self.pointer.current()
                args: list[str] = line.split(' ')
                chars: list[str] = [x for x in list(line) if x != " "]

                if line.startswith("_"): # reserved spaces
                    if chars[-1] != ":" and line[0:len("_indent")] != "_indent":
                        occur_index: int = line.count(chars[-1]) - 1
                        raise SyntaxException(f"A initialized space must end with a colon\n\n{line_index}| {line}\n{highlight_errored_word(line, chars[-1], occur_index)}")

                    # if it is _indent rs
                    if line.startswith("_indent"):
                        if chars[len("_indent")] != ":":
                            raise SyntaxException(f"After _indent must come a colon\n\n{line_index}| {line}\n{highlight_errored_word(line, "t", 0)}")                     
                        
                        indent_val_: list[str] = chars[len("_indent")+1:]
                        indent_val: str = "".join(indent_val_)
                        if not indent_val.isdigit():
                            occur_index: int = line.count(indent_val) - 1
                            raise SyntaxException(f"The value of _indent must be an integer\n\n{line_index}| {line}\n{highlight_errored_word(line, indent_val, occur_index)}")
                        
                        indent: int = int(indent_val)
                        if indent not in ALLOWED_INDENTATIONS:
                            occur_index: int = line.count(indent_val) - 1
                            raise SyntaxException(f"Indentation must be one of {", ".join([str(x) for x in ALLOWED_INDENTATIONS])}\n\n{line_index}| {line}\n{highlight_errored_word(line, indent_val, occur_index)}")

                        indentation = indent

                        spaces.append(Token(
                            Action.Spacing,
                            GLOBAL_OWNER,
                            Keyword.SpaceDefine,
                            [
                                ReservedSpace.Indent
                            ],
                            line_index,
                            line
                        ))
                    else:
                        space_name_listed: list[str] = []
                        for char in chars:
                            if char in (":", "%"): break
                            space_name_listed.append(char)
                        space_name: str = "".join(space_name_listed)

                        if space_name not in ALL_RESERVED_SPACES_AS_STR:
                            raise SyntaxException(f"Not a reserved space: {space_name}\n\n{line_index}| {line}\n{highlight_errored_word(line, space_name, 0)}")
                        
                        spaces.append(Token(
                            Action.Spacing,
                            GLOBAL_OWNER,
                            Keyword.SpaceDefine,
                            [
                                get_reserved_space_from_str(space_name)
                            ],
                            line_index,
                            line
                        ))

                self.pointer.move()

            except PointerEnd:   
                break

        return spaces

