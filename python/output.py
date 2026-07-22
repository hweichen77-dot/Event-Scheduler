"""
CSV output functionality for the Event Scheduler.
Equivalent to the Go output/sheet.go functionality.
"""
import csv
from datetime import datetime, timedelta
from typing import List, Sequence, TextIO, Tuple

from .types import EventType, Output, Student
from .xlsx import column_name, write_workbook

BLOCK = 3


def names(group: List[Student]) -> str:
    return ", ".join(f"{s.firstname} {s.lastname}".strip() for s in group)


def kitchen(moment: datetime) -> str:
    return f"{moment.strftime('%I').lstrip('0')}:{moment.strftime('%M%p')}"


def slot_start(output: Output, slot: int) -> datetime:
    divisions = output.context.time.divisions
    start = datetime.fromtimestamp(output.context.time.start)
    for i in range(min(slot, len(divisions))):
        start += timedelta(minutes=divisions[i])
    return start


def write_csv(file: TextIO, output: Output) -> None:
    """Write scheduling output to CSV file."""
    divisions = output.context.time.divisions
    rows = []

    for housing in output.housings:
        room = f"{housing.room.name} ({housing.room.event_type.name})"
        for judgement in housing.judges:
            judge = (f"{judgement.judge.number} - "
                     f"{judgement.judge.firstname} {judgement.judge.lastname}")
            for slot, assignment in enumerate(judgement.assignments):
                if assignment.event is None:
                    continue
                start = slot_start(output, slot)
                end = start
                if slot < len(divisions):
                    end = start + timedelta(minutes=divisions[slot])
                rows.append((
                    0, slot, room, judge,
                    [kitchen(start), kitchen(end), "Event", room, judge,
                     assignment.event.id, names(assignment.group)],
                ))

    for exam in output.exams:
        start = slot_start(output, exam.start)
        end = start + timedelta(minutes=output.context.constraints.exam_length)
        rows.append((
            1, exam.start, "-", "-",
            [kitchen(start), kitchen(end), "Exam", "-", "-", "",
             f"{exam.student.firstname} {exam.student.lastname}"],
        ))

    for assignment in output.leftover:
        event = assignment.event.id if assignment.event else ""
        rows.append((
            2, 0, "-", "-",
            ["", "", "UNASSIGNED", "-", "-", event, names(assignment.group)],
        ))

    rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))

    writer = csv.writer(file, lineterminator="\n")
    writer.writerow(["Start", "End", "Type", "Room", "Judge", "Event", "Participants"])
    for row in rows:
        writer.writerow(row[4])


def sheets(output: Output) -> List[Tuple[str, Sequence[Sequence[str]]]]:
    divisions = output.context.time.divisions

    sessions = {}
    rooms_by_type = {}
    for housing in output.housings:
        room = f"{housing.room.name} ({housing.room.event_type.name})"
        rooms = rooms_by_type.setdefault(housing.room.event_type, [])
        if room not in rooms:
            rooms.append(room)
        for judgement in housing.judges:
            judge = (f"{judgement.judge.number} - "
                     f"{judgement.judge.firstname} {judgement.judge.lastname}")
            for slot, assignment in enumerate(judgement.assignments):
                if assignment.event is None:
                    continue
                sessions.setdefault(slot, {}).setdefault(room, []).append(
                    (judge, assignment.event.id, names(assignment.group))
                )
    for rooms in rooms_by_type.values():
        rooms.sort()

    def band(rooms: List[str]) -> Tuple[List[List[str]], List[str]]:
        rows: List[List[str]] = []
        merges: List[str] = []
        for slot in sorted(sessions):
            slot_rooms = [r for r in rooms if sessions[slot].get(r)]
            if not slot_rooms:
                continue

            start = slot_start(output, slot)
            end = start
            if slot < len(divisions):
                end = start + timedelta(minutes=divisions[slot])
            window = f"{kitchen(start)} - {kitchen(end)}"

            for room in slot_rooms:
                sessions[slot][room].sort()

            if rows:
                rows.append([])
            rows.append([window])

            room_row = []
            header_row = []
            for index, room in enumerate(slot_rooms):
                room_row.extend([room, "", ""])
                header_row.extend(["Judge", "Event", "Participants"])
                first = column_name(index * BLOCK + 1)
                last = column_name(index * BLOCK + BLOCK)
                merges.append(f"{first}{len(rows) + 1}:{last}{len(rows) + 1}")
            rows.append(room_row)
            rows.append(header_row)

            depth = max(len(sessions[slot][r]) for r in slot_rooms)
            for i in range(depth):
                row = []
                for room in slot_rooms:
                    entries = sessions[slot][room]
                    row.extend(entries[i] if i < len(entries) else ("", "", ""))
                rows.append(row)
        return rows, merges

    roleplay_rows, roleplay_merges = band(rooms_by_type.get(EventType.ROLEPLAY, []))
    written_rows, written_merges = band(rooms_by_type.get(EventType.WRITTEN, []))

    exams = []
    for exam in output.exams:
        start = slot_start(output, exam.start)
        end = start + timedelta(minutes=output.context.constraints.exam_length)
        student = f"{exam.student.firstname} {exam.student.lastname}".strip()
        exams.append((exam.start, student, [kitchen(start), kitchen(end), student]))
    exams.sort(key=lambda r: (r[0], r[1]))

    unassigned = []
    for assignment in output.leftover:
        event = assignment.event.id if assignment.event else ""
        people = names(assignment.group)
        unassigned.append((event, people, [event, people, assignment.reason]))
    unassigned.sort(key=lambda r: (r[0], r[1]))

    reviews = []
    for override in output.overrides:
        judge = (f"{override.judge.number} - "
                 f"{override.judge.firstname} {override.judge.lastname}")
        event = override.event.id if override.event else ""
        people = names(override.group)
        reviews.append((judge, event, [judge, event, people,
                                       ", ".join(override.judge.judgeable)]))
    reviews.sort(key=lambda r: (r[0], r[1]))

    return [
        ("Roleplay", roleplay_rows, roleplay_merges),
        ("Written", written_rows, written_merges),
        ("Exams", [["Start", "End", "Student"]] + [r[2] for r in exams], []),
        ("Unassigned",
         [["Event", "Participants", "Why it could not be scheduled"]]
         + [r[2] for r in unassigned], []),
        ("Review",
         [["Judge", "Event", "Participants", "Events this judge signed up for"]]
         + [r[2] for r in reviews], []),
    ]


def write_xlsx(path: str, output: Output) -> None:
    write_workbook(path, sheets(output))
