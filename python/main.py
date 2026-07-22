"""
Main application for the Event Scheduler.
Equivalent to the Go cmd/real/main.go functionality.
"""
import argparse
import csv
import logging
import os
from datetime import datetime

from .types import Time, Constraints, Registration
from .csv_parser import (
    parse_students, parse_requests, parse_judges, parse_rooms, parse_events,
    parse_time, parse_divisions, parse_number
)
from .scheduler import schedule, new_context
from .output import write_csv, write_xlsx


def setup_logging():
    """Setup logging to file."""
    logging.basicConfig(
        filename='output.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filemode='w'
    )


def read_csv_file(filename: str) -> list:
    """Read CSV file and return rows."""
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        return list(reader)


def main():
    """Main application entry point."""
    setup_logging()
    
    # Command line arguments
    parser = argparse.ArgumentParser(description='Event Scheduler')
    parser.add_argument('--student', default='new_students_form.csv',
                       help='Student registration file')
    parser.add_argument('--judge', default='judges_event_form.csv',
                       help='Judge registration file')
    parser.add_argument('--conference', default='conference_form.csv',
                       help='Conference details file')
    
    args = parser.parse_args()
    
    # Parse students and student requests
    student_lines = read_csv_file(args.student)
    student_data = student_lines[1:]  # Skip header
    
    students = parse_students(student_data)
    requests = parse_requests(student_data, students)
    
    logging.info("================================== Registered students")
    for student in students:
        logging.info(f"{student.firstname} {student.lastname} {student.email}")
    
    logging.info("================================== Registered requests")
    for request in requests:
        logging.info(f"{request.event} {request.group}")
    
    # Parse judges and conference data
    judge_lines = read_csv_file(args.judge)
    conference_lines = read_csv_file(args.conference)
    
    judges = parse_judges(judge_lines[1:])  # Skip header
    
    header = [name.strip() for name in conference_lines[0]]
    col = {name: i for i, name in enumerate(header)}
    conference_data = conference_lines[1:]

    def column(row, name):
        i = col[name]
        return row[i] if i < len(row) else ""

    room_data = [
        [column(row, "Room"), column(row, "Judge Capacity"), column(row, "Room Event Type")]
        for row in conference_data if column(row, "Room")
    ]
    rooms = parse_rooms(room_data)

    event_data = [
        [column(row, "Event"), column(row, "Event Type")]
        for row in conference_data if column(row, "Event")
    ]
    events = parse_events(event_data)

    start_time = parse_time([column(conference_data[0], "Start Time")])

    division_data = [
        [column(row, "Time Slot")] for row in conference_data if column(row, "Time Slot")
    ]
    divisions = parse_divisions(division_data)

    group_size = parse_number([column(conference_data[0], "Group Size")])
    exam_length = parse_number([column(conference_data[0], "Exam Length")])
    
    logging.info("================================== Registered judges")
    for judge in judges:
        logging.info(f"{judge.firstname} {judge.lastname} {judge.judgeable}")
    
    logging.info("================================== Registered rooms")
    for room in rooms:
        logging.info(f"{room.name} {room.judge_capacity}")
    
    logging.info("================================== Registered events")
    event_names = [event.id for event in events]
    logging.info(", ".join(event_names))
    
    # Create schedule context
    context = new_context(
        Time(
            start=int(start_time.timestamp()),
            divisions=divisions
        ),
        Constraints(
            group_size=group_size,
            exam_length=exam_length
        ),
        Registration(
            students=students,
            judges=judges,
            rooms=rooms,
            events=events
        )
    )
    
    logging.info("==================================")
    logging.info(f"[INFO] scheduling with {len(students)} students, {len(requests)} requests, and {len(judges)} judges")
    
    # Run scheduler
    output = schedule(context, requests)
    
    # Write output
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        write_csv(file, output)

    write_xlsx('schedule.xlsx', output)

    print("Scheduling complete! Check schedule.xlsx, output.csv and output.log for results.")


if __name__ == "__main__":
    main()