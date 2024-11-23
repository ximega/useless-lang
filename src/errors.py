class PointerEnd(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class TokenizerException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SyntaxException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class RulesBreak(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)