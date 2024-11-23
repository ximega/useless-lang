#!/usr/bin/python3.13


import sys, pprint

from rules import RulesBreak
from tokenizer import Tokenizer, Pointer, Token, SyntaxException, TokenizerException


def main() -> None:
    lines: list[str] = []

    file_name: str = sys.argv[1]

    if not file_name.endswith(".usl"):
        print("Not a .usl file")
        return

    try:
        with open(file_name, "r+") as file:
            lines = file.read().split('\n')

        tokenizer: Tokenizer = Tokenizer(Pointer(lines))

        tokens: list[Token] = []

        try:
            tokens = tokenizer.parse_to_tokens()
        except (SyntaxException, RulesBreak, TokenizerException) as exc:
            print("\n" + exc.args[0] + "\n")
            return
        
        pprint.pprint(tokens)

    except FileNotFoundError as exc:
        print(exc.args[1] + ": " + file_name)
        return


if __name__ == "__main__":
    main()