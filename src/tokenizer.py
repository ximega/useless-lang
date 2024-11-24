import pprint, re # type: ignore
from typing import Literal, Self

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
    def __init__(self, action: Action, owner: str | ReservedSpace, keyword: Keyword, arguments: list[tuple[Type, str] | Keyword | ReservedSpace | str | tuple[Keyword, int]], line_index: int, line: str) -> None:
        self.line_index: int = line_index
        self.line: str = line
            
        self.action: Action = action
        self.owner: str | ReservedSpace = owner
        self.keyword: Keyword = keyword
        self.link: str | None = None
        self.arguments: list[tuple[Type, str] | Keyword | ReservedSpace | str | tuple[Keyword, int]] = arguments
        self.subtokens: list[Token] = []

        # tuple[Type, str] -> variable type with its string annotation
        # tuple[Keyword, int] -> when referencing variable with reference key (~)
        # Keyword -> additional operations
        # ReservedSpace -> when defining spaces
        # str -> for other cases

    def __repr__(self) -> str:
        return f"line_index={self.line_index}, line={self.line}\naction={self.action}, owner={self.owner}, keyword={self.keyword}, link={self.link}, arguments={self.arguments}, {len(self.subtokens)} subtokens\n"
    
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
                        try:
                            if args[1][-1] == ":":
                                args[1] = args[1][0:-1]

                            if args[1][0] != "[" or args[1][-1] != "]":
                                raise SyntaxException(SYNTAX_ERR, f"Custom space initialization must follow with an owner: {space_name}", f"{line_index}| {line}", highlight_errored_word(line, line_index, space_name[-1], -1))
                        except IndexError:
                            raise SyntaxError(SYNTAX_ERR, f"Missing owner", f"{line_index}| {line}l", highlight_errored_word(line, line_index, chars[len(space_name)], -1))
                        
                    except IndexError:
                        raise SyntaxException(SYNTAX_ERR, f"Custom space initialization must follow with an owner: {space_name}", f"{line_index}| {line}", highlight_errored_word(line, line_index, space_name[-1], -1))

                    owner_name_str: str = args[1][1:-1]
                    owner_name: str | Literal[ReservedSpace.Main] = f"{owner_name_str}"
                    
                    if owner_name_str == "_main":
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
                    if line[indentation] == ' ': 
                        raise SyntaxException(SYNTAX_ERR, f"Invalid indentation, expected {indentation}", f"{line_index}| {line}", highlight_errored_word(line, line_index, ' ', indentation))

                    # handling _consts rs
                    if cur_space == ReservedSpace.Consts:
                        if len(args) < 4: 
                            raise SyntaxException(SYNTAX_ERR, f"Expected 4 arguments to define a constant, {len(args)} were given", f"{line_index}| {line}", "^"*(len(line) + len(str(line_index)) + 2))

                        const_ref_str: str = args[0]
                        if not const_ref_str.isdigit():
                            raise SyntaxException(SYNTAX_ERR, f"Expected integer inside _const at reference", f"{line_index}| {line}", highlight_errored_word(line, line_index, const_ref_str, 0))
                        
                        const_owner: str | Literal[ReservedSpace.Main] = args[1]
                        if const_owner[0] != '[' or const_owner[-1] != ']':
                            raise SyntaxException(SYNTAX_ERR, f"Expected owner of constant", f"{line_index}| {line}", "^"*(len(line) + len(str(line_index)) + 2))
                        else:
                            const_owner = const_owner[1:-1]
                        # reset to ReservedSpace.Main in case the string given is _main
                        if const_owner == "_main": 
                            const_owner = ReservedSpace.Main
                        
                        const_type_str: str = args[2]
                        const_type: Type | None = None
                        try:
                            const_type = get_type_from_str(const_type_str)
                        except RulesBreak as exc:
                            raise RulesBreak(RULES_BREAK, exc.args[1], f"{line_index}| {line}", highlight_errored_word(line, line_index, const_type_str, 0)) from exc

                        # if the value was referenced with ~
                        # then specific path to add will be executed
                        # so i mean the following
                        if args[3].startswith('~'):
                            reference_value_str: str = args[3][1:]
                            reference_value_int: int = 0

                            if len(args) > 4: 
                                raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {line_index}", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[4], -1))
                            
                            if not reference_value_str.isdigit():
                                raise SyntaxException(SYNTAX_ERR, f"Referenced value is not an integer: {reference_value_str}", f"{line_index}| {line}", highlight_errored_word(line, line_index, reference_value_str, -1))
                            
                            reference_value_int = int(reference_value_str)

                            if len(reference_value_str) != len(str(reference_value_int)):
                                raise SyntaxException(SYNTAX_ERR, f"Unnecessary characters during referencing", f"{line_index}| {line}", highlight_errored_word(line, line_index, reference_value_str, -1))

                            spaces[ReservedSpace.Consts].add_subtokens([Token(
                                Action.Defining,
                                const_owner,
                                Keyword.VarSet,
                                [
                                    (Keyword.Refer, reference_value_int)
                                ],
                                line_index,
                                line
                            )])
                        
                        else:
                            const_value: str = ""

                            if const_type in (Type.Int, Type.Char, Type.Bool):
                                const_value = args[3]

                                if len(args) > 4: 
                                    raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {line_index}", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[4], -1))
                                
                                match const_type:
                                    case Type.Int:
                                        if not args[3].isdigit():
                                            raise SyntaxException(SYNTAX_ERR, "Incorrect value set for int", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[3], -1))
                                    case Type.Bool:
                                        if args[3] not in ('True', 'False', 'Null', 'Vague'):
                                            raise SyntaxException(SYNTAX_ERR, "Unknown bool value", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[3], -1))
                                    case Type.Char:
                                        if args[3][0] != "\'" or args[3][-1] != "\'":
                                            raise SyntaxException(SYNTAX_ERR, "Invalid char declaration", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[3], -1))

                            # int array
                            elif const_type == Type.IntArray:
                                arr_value_list: list[str] = args[3:]
                                arr_value_str: str = "".join(arr_value_list).strip()
                                
                                if arr_value_str[0] != '{' or arr_value_str[-1] != '}':
                                    raise SyntaxException(SYNTAX_ERR, f"Invalid array declaration at {line_index}", f"{line_index}| {line}", highlight_errored_word(line, line_index, arr_value_str, -1))
                                
                                arr_values: list[str] = arr_value_str[1:-1].split(',')

                                for val in arr_values:
                                    if not val.isdigit():
                                        raise SyntaxException(SYNTAX_ERR, f"Invalid declaration for int array: {val}", f"{line_index}| {line}", highlight_errored_word(line, line_index, val, -1))
                                    
                                const_value = arr_value_str

                            # strings
                            else:
                                string_list: list[str] = args[3:]
                                string_str: str = " ".join(string_list).strip()

                                if string_str[0] != '"' or string_str[-1] != '"':
                                    raise SyntaxException(SYNTAX_ERR, f"Invalid string declaration at {line_index}", f"{line_index}| {line}", highlight_errored_word(line, line_index, string_str, -1))
                                
                                string_value: str = string_str[1:-1]

                                const_value = string_value
                            
                            spaces[ReservedSpace.Consts].add_subtokens([Token(
                                Action.Defining,
                                const_owner,
                                Keyword.VarSet,
                                [
                                    (const_type, const_value)
                                ],
                                line_index,
                                line
                            )])

                    elif cur_space == ReservedSpace.Pre:
                        if len(args) < 4: 
                            raise SyntaxException(SYNTAX_ERR, f"Expected 4 arguments to pre-define a variable, {len(args)} were given", f"{line_index}| {line}", "^"*(len(line) + len(str(line_index)) + 2))

                        var_ref_str: str = args[0]
                        if not var_ref_str.isdigit():
                            raise SyntaxException(SYNTAX_ERR, f"Expected integer inside _pre at reference", f"{line_index}| {line}", highlight_errored_word(line, line_index, var_ref_str, 0))
                        
                        var_owner: str | Literal[ReservedSpace.Main] = args[1]
                        if var_owner[0] != '[' or var_owner[-1] != ']':
                            raise SyntaxException(SYNTAX_ERR, f"Expected owner of variable", f"{line_index}| {line}", "^"*(len(line) + len(str(line_index)) + 2))
                        else:
                            var_owner = var_owner[1:-1]
                        # reset to ReservedSpace.Main in case the string given is _main
                        if var_owner == "_main": 
                            var_owner = ReservedSpace.Main
                        
                        var_type_str: str = args[2]
                        var_type: Type | None = None
                        try:
                            var_type = get_type_from_str(var_type_str)
                        except RulesBreak as exc:
                            raise RulesBreak(RULES_BREAK, exc.args[1], f"{line_index}| {line}", highlight_errored_word(line, line_index, var_type_str, 0)) from exc

                        # if the value was referenced with ~
                        # then specific path to add will be executed
                        # so i mean the following
                        if args[3].startswith('~'):
                            reference_value_str: str = args[3][1:]
                            reference_value_int: int = 0

                            if len(args) > 4: 
                                raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {line_index}", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[4], -1))
                            
                            if not reference_value_str.isdigit():
                                raise SyntaxException(SYNTAX_ERR, f"Referenced value is not an integer: {reference_value_str}", f"{line_index}| {line}", highlight_errored_word(line, line_index, reference_value_str, -1))
                            
                            reference_value_int = int(reference_value_str)

                            if len(reference_value_str) != len(str(reference_value_int)):
                                raise SyntaxException(SYNTAX_ERR, f"Unnecessary characters during referencing", f"{line_index}| {line}", highlight_errored_word(line, line_index, reference_value_str, -1))

                            spaces[ReservedSpace.Pre].add_subtokens([Token(
                                Action.Defining,
                                var_owner,
                                Keyword.VarSet,
                                [
                                    (Keyword.Refer, reference_value_int)
                                ],
                                line_index,
                                line
                            )])
                            
                        else:
                            var_value: str = ""
                            if var_type in (Type.Int, Type.Char, Type.Bool):
                                var_value = args[3]

                                if len(args) > 4: 
                                    raise TokenizerException(TOKENIZER_ERR, f"Unexpected token at {line_index}", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[4], -1))
                                
                                match var_type:
                                    case Type.Int:
                                        if not args[3].isdigit():
                                            raise SyntaxException(SYNTAX_ERR, f"Incorrect value set for int", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[3], -1))
                                    case Type.Bool:
                                        if args[3] not in ('True', 'False', 'Null', 'Vague'):
                                            raise SyntaxException(SYNTAX_ERR, f"Unknown bool value", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[3], -1))
                                    case Type.Char:
                                        if args[3][0] != "\'" or args[3][-1] != "\'":
                                            raise SyntaxException(SYNTAX_ERR, f"Invalid char declaration", f"{line_index}| {line}", highlight_errored_word(line, line_index, args[3], -1))

                            # int array
                            elif var_type == Type.IntArray:
                                arr_value_list: list[str] = args[3:]
                                arr_value_str: str = "".join(arr_value_list).strip()
                                
                                if arr_value_str[0] != '{' or arr_value_str[-1] != '}':
                                    raise SyntaxException(SYNTAX_ERR, f"Invalid array declaration at {line_index}", f"{line_index}| {line}", highlight_errored_word(line, line_index, arr_value_str, -1))
                                
                                arr_values: list[str] = arr_value_str[1:-1].split(',')

                                for val in arr_values:
                                    if not val.isdigit():
                                        raise SyntaxException(SYNTAX_ERR, f"Invalid declaration for int array: {val}", f"{line_index}| {line}", highlight_errored_word(line, line_index, val, -1))
                                    
                                var_value = arr_value_str

                            # strings
                            else:
                                string_list: list[str] = args[3:]
                                string_str: str = " ".join(string_list).strip()

                                if string_str[0] != '"' or string_str[-1] != '"':
                                    raise SyntaxException(SYNTAX_ERR, f"Invalid string declaration at {line_index}", f"{line_index}| {line}", highlight_errored_word(line, line_index, string_str, -1))
                                
                                string_value: str = string_str[1:-1]

                                var_value = string_value

                            spaces[ReservedSpace.Pre].add_subtokens([Token(
                                Action.Defining,
                                var_owner,
                                Keyword.VarSet,
                                [
                                    (var_type, var_value)
                                ],
                                line_index,
                                line
                            )])

                    elif cur_space == ReservedSpace.Stdin:
                        pass

                    # the rest of instructions
                    else:
                        pass

                else:
                    if line[0] == " ": 
                        raise SyntaxException(SYNTAX_ERR, f"Invalid indentation. Expected {indentation} indent", f"{line_index}| {line}", highlight_errored_word(line, line_index, ' ', 0))

                    raise SyntaxException(SYNTAX_ERR, f"Unknown token at {line_index}", f"{line_index}| {line}", f"{"^"*(len(line) + len(str(line_index)) + 2)}")

                self.pointer.move()

            except PointerEnd:   
                break

        return list(spaces.values())

