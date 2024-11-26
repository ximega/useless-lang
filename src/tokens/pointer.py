"""Contains a pointer, which simply talking contains a line, where the code is right now to be tokenized

"""

from typing import Self

from src.errors import PointerEnd, TokenizerException, TOKENIZER_ERR
from src.rules import ALLOWED_CHARS
from src.errorutils import put_errored_code_line

__all__ = [
    'Pointer'
]

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
                                raise TokenizerException(TOKENIZER_ERR, f"Unexpected char: {char}", *put_errored_code_line(line, index, char, 0))
           
            if not is_with_comment:
                formatted_line: str = line.rstrip()
                formatted_lines.append(line.rstrip())

                for char in list(formatted_line):
                    if char not in ALLOWED_CHARS:
                        raise TokenizerException(TOKENIZER_ERR, f"Unexpected char: {char}", *put_errored_code_line(line, index, char, 0))
    


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