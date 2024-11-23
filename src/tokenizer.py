from typing import Self


from rules import *
from errors import SyntaxException, TokenizerException, PointerEnd

def highlight_errored_word(line: str, line_index: int, match_word: str, occur_index: int) -> str:
    matched: list[int] = [] # indexes of matched
    chars: list[str] = list(line)
    mchars: list[str] = list(match_word)
    for index, char in enumerate(chars):
        if char == match_word[0]:
            all_equal = True
            for jndex, mchar in enumerate(mchars):
                if mchar != chars[index+jndex]:
                    all_equal = False
            if all_equal:
                matched.append(index)

    if len(matched) == 0: 
        raise TokenizerException(f"There is no word to match, to be highlighted\n\n{line=}, {match_word=}")
    
    return " "*(matched[occur_index] + 2 + len(str(line_index))) + "^"*len(match_word)    

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

    def get_next(self, times: int) -> list[tuple[str, int]]:
        items: list[tuple[str, int]] = []
        for i in range(1, times+1):
            try:
                items.append((self.lines[self.index + i], self.index + i))
            except KeyError:
                pass
        return items
    
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
            raise TokenizerException(f"Cannot include subtokens under {get_str_from_keyword(self.keyword)}\n\n{self.line_index}| {self.line}\n{highlight_errored_word(self.line, self.line_index, get_str_from_keyword(self.keyword), 0)}")
                    
        self.subtokens = subtokens
        return self
    
    def add_subtokens(self, subtokens: list["Token"]) -> Self:
        if self.action not in (Action.Instruction, Action.Spacing):
            raise TokenizerException(f"Cannot add subtokens for non-instruction or non-spacing\n\n{self.line_index}| {self.line}")
        if (self.action == Action.Instruction) and (self.keyword not in ALLOWED_SUBTOKEN_INSTRUCTION):
            raise TokenizerException(f"Cannot include subtokens under {get_str_from_keyword(self.keyword)}\n\n{self.line_index}| {self.line}\n{highlight_errored_word(self.line, self.line_index, get_str_from_keyword(self.keyword), 0)}")
                    
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
        spaces: dict[str | ReservedSpace, Token] = {}
        cur_space: str | ReservedSpace | None = None
        instructions: list[Token] = []
        defining: list[Token] = []

        while True:
            try:
                line, line_index = self.pointer.current()
                args: list[str] = line.split(' ')
                chars: list[str] = [x for x in list(line) if x != " "]

                # reserved spaces
                # all of them are specified in src/rules.py
                # also, they are stored in ALL_RESERVED_SPACES_AS_STR and in ReservedSpace enum
                if line.startswith("_"):
                    # the current space name is defined 
                    space_name_listed: list[str] = []
                    for char in chars:
                        if char in (":", "%"): break
                        space_name_listed.append(char)
                    space_name: str = "".join(space_name_listed)

                    # if rs does not exist
                    if space_name not in ALL_RESERVED_SPACES_AS_STR:
                        raise SyntaxException(f"Not a reserved space: {space_name}\n\n{line_index}| {line}\n{highlight_errored_word(line, line_index, space_name, 0)}")
                    # if the line has anything after : in a reserved space
                    # causes an exception
                    # _indent does not cause anything, as the value is given straight after :
                    if chars[-1] != ":" and line[0:len("_indent")] != "_indent":
                        occur_index: int = line.count(chars[-1]) - 1
                        raise SyntaxException(f"Space {space_name} must end with a colon\n\n{line_index}| {line}\n{highlight_errored_word(line, line_index, chars[-1], occur_index)}")

                    # if it is _indent rs
                    if line.startswith("_indent"):
                        if chars[len("_indent")] != ":":
                            raise SyntaxException(f"Expected a colon after _indent\n\n{line_index}| {line}\n{highlight_errored_word(line, line_index, "t", 0)}")                     
                        
                        indent_val_: list[str] = chars[len("_indent")+1:]
                        indent_val: str = "".join(indent_val_)

                        if indent_val.strip() == "":
                            raise SyntaxException(f"No value given to _indent. Either remove the line or specify the value\n\n{line_index}| {line}\n{highlight_errored_word(line, line_index, line[-1], 0)}")

                        if not indent_val.isdigit():
                            occur_index: int = line.count(indent_val) - 1
                            raise SyntaxException(f"The value of _indent must be an integer\n\n{line_index}| {line}\n{highlight_errored_word(line, line_index, indent_val, occur_index)}")
                        
                        indent: int = int(indent_val)
                        if indent not in ALLOWED_INDENTATIONS:
                            occur_index: int = line.count(indent_val) - 1
                            raise SyntaxException(f"Indentation must be one of {", ".join([str(x) for x in ALLOWED_INDENTATIONS])}\n\n{line_index}| {line}\n{highlight_errored_word(line, line_index, indent_val, occur_index)}")

                        indentation = indent

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

                    # _links rs
                    elif line.startswith("_links"):
                        links: list[str] = []
                        index: int = 1
                        next_line, next_line_index = self.pointer.get_next(index)[index-1]
                        while next_line.startswith(' '*indentation): # type: ignore
                            line_args: list[str] = [x.strip() for x in next_line.split(',')]
                            for arg in line_args:
                                if arg in THREE_LETTER_KEYWORDS:
                                    raise SyntaxException(f"Cannot override a keyword: {arg}\n\n{next_line_index}| {next_line}\n{highlight_errored_word(next_line, next_line_index, arg, 0)}")

                                if len(arg) != 3:
                                    raise SyntaxException(f"The length of {arg} must be strongly 3 chars\n\n{next_line_index}| {next_line}\n{highlight_errored_word(next_line, next_line_index, arg, 0)}")
                                for char in list(arg):
                                    if char not in ALLOWED_LINK_CHARS:
                                        raise SyntaxException(f"The link can not include {char} char\n\n{next_line_index}| {next_line}\n{highlight_errored_word(next_line, next_line_index, char, 0)}")
                            links.extend(line_args)
                            index += 1
                            next_line, next_line_index = self.pointer.get_next(index)[index-1]
                        if len(set(links)) < len(links):
                            seen: set[str] = set()
                            dupe: str | None = None
                            for link in links:
                                if link in seen:
                                    dupe = link
                                else:
                                    seen.add(link)

                            if isinstance(dupe, str):
                                raise SyntaxException(f"Two similar links were instantiated: {dupe}\n\n{next_line_index}| {next_line}\n{highlight_errored_word(next_line, next_line_index, dupe, 1)}")
                        
                        subtokens: list[Token] = []
                        for link in links:
                            subtokens.append(Token(
                                Action.Defining,
                                ReservedSpace.Links,
                                Keyword.LinkDef,
                                [
                                    link
                                ],
                                line_index,
                                line
                            ))

                        spaces[ReservedSpace.Links] = Token(
                            Action.Spacing,
                            GLOBAL_OWNER,
                            Keyword.SpaceDefine,
                            [
                                get_reserved_space_from_str(space_name)
                            ],
                            line_index,
                            line
                        ).set_subtokens(subtokens)
                            
                    # the rest of rs 'es
                    else:
                        spaces[get_reserved_space_from_str(space_name)] = Token(
                            Action.Spacing,
                            GLOBAL_OWNER,
                            Keyword.SpaceDefine,
                            [
                                get_reserved_space_from_str(space_name)
                            ],
                            line_index,
                            line
                        )

                # handling definitions and instructions
                else:
                    ...

                self.pointer.move()

            except PointerEnd:   
                break

        return list(spaces.values())

