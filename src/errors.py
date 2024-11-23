class PointerEnd(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class TokenizerException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

TOKENIZER_ERR = "Tokenizer issue"

class SyntaxException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

SYNTAX_ERR = "Invalid syntax"

class RulesBreak(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

RULES_BREAK = "Infringement"

class DuplicationException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

DUPLICATION_ERR = "Duplication flaw"

class OwnershipException(Exception): 
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

OWNERSHIP_ERR = "Ownership error"