from enum import IntEnum, unique

@unique
class OnOffState(IntEnum):
    ON = 1
    OFF = 0
    TOGGLE = 2
