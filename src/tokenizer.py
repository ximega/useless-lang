from typing import Literal, Self
import pprint # type: ignore

from rules import *
from errors import (
    PointerEnd,
    SyntaxException, 
    TokenizerException, 
    DuplicationException,
    OwnershipException,
)
from errors import (
    SYNTAX_ERR,
    OWNERSHIP_ERR,
    TOKENIZER_ERR,
    DUPLICATION_ERR,
)

def highlight_errored_word(line: str, line_index: int, match_word: str, occur_index: int) -> str:
    matched: list[int] = [] # indexes of matched
    chars: list[str] = list(line)
    mchars: list[str] = list(match_word)
    for index, char in enumerate(chars):
        if char == match_word[0]:
            all_equal = True
            for jndex, mchar in enumerate(mchars):
                try:
                    if mchar != chars[index+jndex]:
                        all_equal = False
                except IndexError:
                    pass
            if all_equal:
                matched.append(index)

    if len(matched) == 0: 
        raise TokenizerException(TOKENIZER_ERR, f"There is no word to match, to be highlighted", f"{line=}, {match_word=}", "^"*(len(line) + len(str(line_index)) + 2))
    
    return " "*(matched[occur_index] + 2 + len(str(line_index))) + "^"*len(match_word)    

class Pointer:
    __instanced = False

    def __new__(cls, lines: list[str]) -> Self:
        if cls.__instanced:
            raise TypeError("Cannot create a second pointer")
        cls.__instanced = True
        return super().__new__(cls)

    def __init__(self, lines: list[str]) -> None:
        formatted_lines: list[str] = []

        for index, line in enumerate(lines, start=1):
            if line.strip() == "":
                continue

            is_with_comment = False
            chars: list[str] = list(line)
            for index, char in enumerate(chars):
                if not is_with_comment:
                    if char == "/" and chars[index+1] == "/":
                        is_with_comment = True
                        formatted_line: str = line[0:index].rstrip()
                        formatted_lines.append(formatted_line)

                        for char in list(formatted_line):
                            if char not in ALLOWED_CHARS:
                                raise TokenizerException(TOKENIZER_ERR, f"Unexpected char: {char}", f"{index}| {line}", {highlight_errored_word(line, index, char, 0)})
           
            if not is_with_comment:
                formatted_line: str = line.rstrip()
                formatted_lines.append(line.rstrip())

                for char in list(formatted_line):
                    if char not in ALLOWED_CHARS:
                        raise TokenizerException(TOKENIZER_ERR, f"Unexpected char: {char}", f"{index}| {line}", {highlight_errored_word(line, index, char, 0)})
    


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
            raise TokenizerException(TOKENIZER_ERR, "Cannot set link to non-instruction", f"{self.line_index}| {self.line}", "^"*(len(self.line) + len(str(self.line_index)) + 2))
        self.link = link
        return self

    def set_subtokens(self, subtokens: list["Token"]) -> Self:
        if self.action not in (Action.Instruction, Action.Spacing):
            raise TokenizerException(TOKENIZER_ERR, "Cannot set subtokens for non-instruction or non-spacing", f"{self.line_index}| {self.line}", "^"*(len(self.line) + len(str(self.line_index)) + 2))
        if (self.action == Action.Instruction) and (self.keyword not in ALLOWED_SUBTOKEN_INSTRUCTION):
            raise TokenizerException(TOKENIZER_ERR, f"Cannot include subtokens under {get_str_from_keyword(self.keyword)}", f"{self.line_index}| {self.line}", highlight_errored_word(self.line, self.line_index, get_str_from_keyword(self.keyword), 0))
                    
        self.subtokens = subtokens
        return self
    
    def add_subtokens(self, subtokens: list["Token"]) -> Self:
        if self.action not in (Action.Instruction, Action.Spacing):
            raise TokenizerException(TOKENIZER_ERR, "Cannot add subtokens for non-instruction or non-spacing", f"{self.line_index}| {self.line}", "^"*(len(self.line) + len(str(self.line_index)) + 2))
        if (self.action == Action.Instruction) and (self.keyword not in ALLOWED_SUBTOKEN_INSTRUCTION):
            raise TokenizerException(TOKENIZER_ERR, f"Cannot include subtokens under {get_str_from_keyword(self.keyword)}", f"{self.line_index}| {self.line}", highlight_errored_word(self.line, self.line_index, get_str_from_keyword(self.keyword), 0))
                    
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

        while True:
            try:
                line, line_index = self.pointer.current()
                args: list[str] = line.strip().split(' ')
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
                        raise SyntaxException(SYNTAX_ERR, f"Not a reserved space: {space_name}", f"{line_index}| {line}", highlight_errored_word(line, line_index, space_name, 0))
                    # if the line has anything after : in a reserved space
                    # causes an exception
                    # _indent does not cause anything, as the value is given straight after :
                    if chars[-1] != ":" and line[0:len("_indent")] != "_indent":
                        occur_index: int = line.count(chars[-1]) - 1
                        raise SyntaxException(SYNTAX_ERR, f"Space {space_name} must end with a colon", f"{line_index}| {line}", highlight_errored_word(line, line_index, chars[-1], occur_index))

                    # if it is _indent rs
                    if line.startswith("_indent"):
                        if chars[len("_indent")] != ":":
                            raise SyntaxException(SYNTAX_ERR, "Expected a colon after _indent", f"{line_index}| {line}", highlight_errored_word(line, line_index, "t", 0))                     
                        
                        indent_val_: list[str] = chars[len("_indent")+1:]
                        indent_val: str = "".join(indent_val_)

                        if indent_val.strip() == "":
                            raise SyntaxException(SYNTAX_ERR, "No value given to _indent. Either remove the line or specify the value", f"{line_index}| {line}", highlight_errored_word(line, line_index, line[-1], 0))

                        if not indent_val.isdigit():
                            occur_index: int = line.count(indent_val) - 1
                            raise SyntaxException(SYNTAX_ERR, "The value of _indent must be an integer", f"{line_index}| {line}", highlight_errored_word(line, line_index, indent_val, occur_index))
                        
                        indent: int = int(indent_val)
                        if indent not in ALLOWED_INDENTATIONS:
                            occur_index: int = line.count(indent_val) - 1
                            raise SyntaxException(SYNTAX_ERR, f"Indentation must be one of {", ".join([str(x) for x in ALLOWED_INDENTATIONS])}", f"{line_index}| {line}", highlight_errored_word(line, line_index, indent_val, occur_index))

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

                    # _links rs
                    elif line.startswith("_links"):
                        links: list[str] = []
                        index: int = 1
                        next_line, next_line_index = self.pointer.get_next(index)[index-1]

                        while next_line.startswith(' '*indentation): # type: ignore
                            line_args: list[str] = [x.strip() for x in next_line.split(',')]
                            for arg in line_args:
                                if arg in THREE_LETTER_KEYWORDS:
                                    raise SyntaxException(SYNTAX_ERR, f"Cannot override a keyword: {arg}", f"{next_line_index}| {next_line}", highlight_errored_word(next_line, next_line_index, arg, 0))

                                if len(arg) != 3:
                                    raise SyntaxException(SYNTAX_ERR, f"The length of {arg} must be strongly 3 chars", f"{next_line_index}| {next_line}", highlight_errored_word(next_line, next_line_index, arg, 0))
                                for char in list(arg):
                                    if char not in ALLOWED_LINK_CHARS:
                                        raise SyntaxException(SYNTAX_ERR, f"The link can not include {char} char", f"{next_line_index}| {next_line}", highlight_errored_word(next_line, next_line_index, char, 0))
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
                                raise SyntaxException(SYNTAX_ERR, f"Two similar links were instantiated: {dupe}", f"{next_line_index}| {next_line}", highlight_errored_word(next_line, next_line_index, dupe, 1))
                        
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

                        cur_space = ReservedSpace.Links

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
                        cur_space = get_reserved_space_from_str(space_name)

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

                # handling custom spaces
                elif line.startswith('$_'):
                    space_name: str = ""
                    for char in chars:
                        if char == "[": break
                        if char not in ALLOWED_CUSTOM_SPACE_CHARS:
                            raise SyntaxException(SYNTAX_ERR, f"Invalid char at {line_index}", f"{line_index}| {line}", highlight_errored_word(line, line_index, char, 0))
                        space_name += char

                    if space_name in spaces.keys():
                        raise DuplicationException(DUPLICATION_ERR, f"Can not have two similar spaces: {space_name}", f"{line_index}| {line}", highlight_errored_word(line, line_index, space_name, 0))
                    
                    try:
                        # removing from args[1] (which is supposed to be just owner)
                        if args[1][-1] == ":":
                            args[1] = args[1][0:-1]

                        if args[1][0] != "[" or args[1][-1] != "]":
                            raise SyntaxException(SYNTAX_ERR, f"Custom space initialization must follow with an owner: {space_name}", f"{line_index}| {line}", highlight_errored_word(line, line_index, space_name[-1], -1))
                    except IndexError:
                        raise SyntaxException(SYNTAX_ERR, f"Custom space initialization must follow with an owner: {space_name}", f"{line_index}| {line}", highlight_errored_word(line, line_index, space_name[-1], -1))

                    owner_name_str: str = args[1][1:-1]
                    owner_name: str | Literal[ReservedSpace.Main] = f"{owner_name_str}"
                    
                    if owner_name_str.startswith("_"):
                        if owner_name != "_main":
                            raise OwnershipException(OWNERSHIP_ERR, f"Can not set reserved space {owner_name_str} as owner", f"{line_index}| {line}", highlight_errored_word(line, line_index, owner_name_str, -1))
                        
                        owner_name = ReservedSpace.Main
                    else:
                        owner_name = owner_name_str

                    if owner_name == "": 
                        raise OwnershipException(OWNERSHIP_ERR, f"Can not set a null space as owner", f"{line_index}| {line}", highlight_errored_word(line, line_index, '[]', -1))
                    
                    if chars[-1] != ":":
                        raise SyntaxException(SYNTAX_ERR, "Expected a colon", f"{line_index}| {line}", highlight_errored_word(line, line_index, chars[-1], -1))
                    
                    for char in owner_name_str:
                        if char not in ALLOWED_CUSTOM_SPACE_CHARS:
                            raise SyntaxException(SYNTAX_ERR, f"Invalid char at {line_index} for owner", f"{line_index}| {line}", highlight_errored_word(line, line_index, char, 0))
                    
                    cur_space = space_name

                    spaces[space_name] = Token(
                        Action.Spacing,
                        owner_name,
                        Keyword.SpaceDefine,
                        [
                            space_name
                        ],
                        line_index,
                        line
                    )

                # handling definitions and instructions
                elif line.startswith(' '*indentation):
                    pass

                else:
                    if line[0] == " ": 
                        raise SyntaxException(SYNTAX_ERR, f"Invalid indentation. Expected {indentation} indent", f"{line_index}| {line}", highlight_errored_word(line, line_index, ' ', 0))

                    raise SyntaxException(SYNTAX_ERR, f"Unknown token at {line_index}", f"{line_index}| {line}", f"{"^"*(len(line) + len(str(line_index)) + 2)}")

                self.pointer.move()

            except PointerEnd:   
                break

        return list(spaces.values())

