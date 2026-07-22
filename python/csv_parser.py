"""
CSV parsing functionality for the Event Scheduler.
Equivalent to the Go cmd/real/csv.go functionality.
"""
import logging
import re
from datetime import datetime
from typing import List, Tuple, Optional
from .types import Student, StudentRequest, Judge, Room, Event, EventType


PARENTHESIS_PATTERN = re.compile(r'\(.+\)')
TIME_FORMAT = "%I:%M %p"  # 3:00 PM format


def find_student(pool: List[Student], first: str, last: str) -> Tuple[Student, bool]:
    """Find a student in the pool or create a new one."""
    first = first.lower()
    last = last.lower()
    
    for student in pool:
        if (first == student.firstname.lower() and 
            last == student.lastname.lower()):
            return student, False
    
    # Create new student if not found
    email = f"{first}.{last}@warriorlife.net"
    return Student(email=email, firstname=first, lastname=last), True


def split_name(combined: str) -> Tuple[str, str]:
    """Split a combined name into first and last name."""
    # Remove parentheses and commas
    without = PARENTHESIS_PATTERN.sub('', combined).replace(',', '')
    parts = [part for part in without.split() if part]
    
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def cell(line: List[str], index: int) -> str:
    return line[index].strip() if index < len(line) else ""


def clean(text: str) -> str:
    return " ".join(PARENTHESIS_PATTERN.sub('', text).split())


def split_last_first(combined: str) -> Tuple[str, str]:
    if ',' in combined:
        last, _, first = combined.partition(',')
        return clean(last), clean(first)
    return split_name(combined)


def split_first_last(combined: str) -> Tuple[str, str]:
    parts = clean(combined).split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def parse_students(lines: List[List[str]]) -> List[Student]:
    """Parse students from CSV lines."""
    students = []
    seen_emails = set()

    def register(email: str, last_first: str, first_last: str) -> None:
        email = email.lower()
        if not email or email in seen_emails:
            return

        if last_first:
            lastname, firstname = split_last_first(last_first)
        else:
            firstname, lastname = split_first_last(first_last)

        students.append(Student(email=email, firstname=firstname, lastname=lastname))
        seen_emails.add(email)

    for line in lines:
        register(cell(line, 0), cell(line, 1), "")
        register(cell(line, 8), cell(line, 5), cell(line, 4))
        register(cell(line, 9), cell(line, 7), cell(line, 6))

    return students


def parse_requests(lines: List[List[str]], students: List[Student]) -> List[StudentRequest]:
    """Parse student requests from CSV lines."""
    requests = []
    by_email = {s.email for s in students}

    for line in lines:
        email = cell(line, 0).lower()
        if not email:
            continue

        event = cell(line, 3).split()[0]  # Take first word

        # Build group starting with the requesting student
        group = [email]
        for index in (8, 9):
            partner = cell(line, index).lower()
            if partner:
                group.append(partner)

        named = cell(line, 2)
        if named and len(group) == 1:
            logging.warning(
                f"[WARN] {email} named partner(s) \"{named}\" but gave no partner email, "
                f"leaving them out of the group"
            )

        if event.endswith("TDM") and len(group) < 2:
            logging.warning(
                f"[WARN] {event} is a team event but {email} entered it alone, "
                f"check the partner columns of the student form"
            )

        requests.append(StudentRequest(event=event, group=group))

    return requests


def parse_judges(rows: List[List[str]]) -> List[Judge]:
    """Parse judges from CSV rows."""
    judges = []
    
    for i, row in enumerate(rows):
        events = []
        for event in row[2].split(','):
            trimmed = event.strip()
            if trimmed:
                events.append(trimmed)

        if not events:
            logging.warning(
                f"[WARN] judge {i + 1} {row[0]} {row[1]} lists no events, "
                f"so they will be treated as able to judge anything"
            )

        judges.append(Judge(
            number=i + 1,
            firstname=row[0],
            lastname=row[1],
            judgeable=events
        ))
    
    return judges


def parse_time(row: List[str]) -> datetime:
    """Parse start time from CSV row."""
    try:
        return datetime.strptime(row[0], TIME_FORMAT)
    except ValueError as e:
        raise ValueError(
            f"Timestamp parsing error! Please ensure you have written in this exact format "
            f'"{TIME_FORMAT}" with the correct capitals and no spaces'
        ) from e


def parse_divisions(rows: List[List[str]]) -> List[int]:
    """Parse time divisions from CSV rows."""
    divisions = []
    
    for row in rows:
        if row[0] == "NaN":
            continue
        try:
            slot = int(row[0])
            divisions.append(slot)
        except ValueError:
            continue
    
    return divisions


def parse_rooms(rows: List[List[str]]) -> List[Room]:
    """Parse rooms from CSV rows."""
    rooms = []
    
    for row in rows:
        if not row[0]:  # Skip empty room names
            continue
        
        try:
            capacity = int(row[1])
        except (ValueError, IndexError):
            capacity = 0
        
        rooms.append(Room(
            name=row[0],
            judge_capacity=capacity,
            event_type=parse_event_type(row[2])
        ))
    
    return rooms


def parse_event_type(text: str) -> EventType:
    """Parse event type from text."""
    event_types = {
        "roleplay": EventType.ROLEPLAY,
        "written": EventType.WRITTEN,
    }
    
    normalized = text.lower().strip()
    if normalized not in event_types:
        raise ValueError(
            f'Unknown event type, please specify an event type of either "roleplay" or "written", got "{text}"'
        )
    
    return event_types[normalized]


def parse_events(rows: List[List[str]]) -> List[Event]:
    """Parse events from CSV rows."""
    events = []
    
    for row in rows:
        if not row[0]:  # Skip empty event names
            continue
        
        events.append(Event(
            id=row[0],
            event_type=parse_event_type(row[1])
        ))
    
    return events


def parse_number(row: List[str]) -> int:
    """Parse a number from CSV row."""
    return int(row[0])