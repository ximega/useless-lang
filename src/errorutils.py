"""So far only contains utilities to highlight part of the code, where the mistake occurred"""

from src.errors import (
    TokenizerException, TOKENIZER_ERR
)


__all__ = [
    'put_errored_code_line',
    'format_code_line',
]


def format_code_line(line: str, line_index: int) -> str:
    """
    Returns a formatted code line\n
    Puts code line num, then | and the code itself\n
    E.g.: 2| _indent: 4
    """
    return f"{line_index}| {line}"

def highlight_errored_word(line: str, line_index: int, match_word: str, occur_index: int) -> str:
    """Highlights code line with a line of ^'s, \n
    where the mistake/flaw/error occurred

    Raises
        `TOKENIZER_ERR`
        * If no matched words found
    """
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

def put_errored_code_line(line: str, line_index: int, match_word: str, occur_index: int = 0) -> tuple[str, str]:
    """Combines `format_code_line` and `highlight_errored_word`
    """
    return (
        format_code_line(line, line_index),
        highlight_errored_word(line, line_index, match_word, occur_index)
    )