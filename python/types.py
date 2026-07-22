"""
Data types and structures for the Event Scheduler.
Equivalent to the Go protobuf definitions and scheduler types.
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict
import time


class EventType(Enum):
    ROLEPLAY = 0
    WRITTEN = 1


@dataclass
class Room:
    name: str
    judge_capacity: int
    event_type: EventType


@dataclass
class Event:
    id: str
    event_type: EventType


@dataclass
class Judge:
    number: int
    firstname: str
    lastname: str
    judgeable: List[str]


@dataclass
class Student:
    email: str
    firstname: str
    lastname: str


@dataclass
class StudentRequest:
    event: str
    group: List[str]


@dataclass
class Time:
    start: int  # Unix timestamp
    divisions: List[int]  # Duration of each time slot in minutes


@dataclass
class Constraints:
    group_size: int
    exam_length: int


@dataclass
class Registration:
    students: List[Student]
    judges: List[Judge]
    rooms: List[Room]
    events: List[Event]


@dataclass
class Assignment:
    event: Optional[Event]
    group: List[Student]

    def __init__(self, event: Optional[Event] = None, group: Optional[List[Student]] = None):
        self.event = event
        self.group = group if group is not None else []


@dataclass
class Judgement:
    judge: Judge
    assignments: List[Assignment]


@dataclass
class Housing:
    room: Optional[Room]
    judges: List[Judgement]

    def __init__(self, room: Optional[Room] = None, judges: Optional[List[Judgement]] = None):
        self.room = room
        self.judges = judges if judges is not None else []


@dataclass
class Exam:
    start: int
    student: Student


@dataclass
class ScheduleContext:
    time: Time
    constraints: Constraints
    students: Dict[str, Student]
    judges: Dict[int, Judge]
    events: Dict[str, Event]
    rooms: List[Room]


@dataclass
class Unplaced:
    event: Optional[Event]
    group: List[Student]
    reason: str


@dataclass
class Override:
    judge: Judge
    event: Optional[Event]
    group: List[Student]


@dataclass
class Output:
    housings: List[Housing]
    context: ScheduleContext
    exams: List[Exam]
    leftover: List[Unplaced]
    overrides: List[Override]