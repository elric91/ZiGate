from enum import IntEnum, unique


@unique
class OnOffState(IntEnum):
    ON = 1
    OFF = 0
    TOGGLE = 2


@unique
class DeviceType(IntEnum):
    COORDINATOR = 0
    ROUTER = 1
    LEGACY_ROUTER = 2
