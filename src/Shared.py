from enum import Enum


class Review_Type(Enum):
    ONE_STAR = 1,
    TWO_STAR = 2,
    THREE_STAR = 3,
    FOUR_STAR = 4,
    FIVE_STAR = 5


class Status(Enum):
    PROCESSING = 1
    COMPLETED = 2
    FAILED = 3
    NOT_FOUND = 4
