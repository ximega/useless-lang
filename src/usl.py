#!/usr/bin/python3.13


import sys, pprint

from tokenizer import Tokenizer, Pointer


def main() -> None:
    lines: list[str] = []

    file_name: str = sys.argv[1]

    with open(file_name, "r+") as file:
        lines = file.read().split('\n')

    tokenizer: Tokenizer = Tokenizer(Pointer(lines))

    pprint.pprint(tokenizer.parse_to_tokens())


if __name__ == "__main__":
    main()