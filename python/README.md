# Event Scheduler - Python Implementation

*Mock DECA conferences*

This is a Python reimplementation of the Go-based Event Scheduler found in the parent directory.

## Features

- **Student Registration**: Parse student data from CSV files
- **Judge Assignment**: Automatically assign judges to events based on their preferences
- **Event Scheduling**: Smart scheduling algorithm that avoids conflicts and optimizes assignments
- **Room Management**: Distribute judges across available rooms
- **Exam Scheduling**: Schedule exams for roleplay events
- **CSV Output**: Generate detailed scheduling reports

## Files

- `main.py` - Main application entry point
- `types.py` - Data structures and type definitions
- `scheduler.py` - Core scheduling algorithm
- `csv_parser.py` - CSV file parsing utilities
- `output.py` - CSV output generation
- `common.py` - Common utility functions
- `test_scheduler.py` - Unit tests

## Installation

This implementation requires Python 3.7+ with only standard library dependencies.

```bash
# No additional dependencies required - uses only Python standard library
```

## Usage

### Quick Start

To test the scheduler:

```bash
python main.py
```

Then open `output.csv` in LibreOffice Calc, Excel, or any CSV viewer.

### Command Line Options

```bash
python main.py --student students.csv --judge judges.csv --conference conference.csv
```

- `--student`: Student registration file (default: `new_students_form.csv`)
- `--judge`: Judge registration file (default: `judges_event_form.csv`) 
- `--conference`: Conference details file (default: `conference_form.csv`)

### Input File Formats

#### Student Registration File
CSV with columns:
- Email
- Name (Last, First format)
- Partners (comma-separated names)
- Event (event name)

#### Judge Registration File  
CSV with columns:
- First Name
- Last Name
- Judgeable Events (comma-separated)

#### Conference Details File
CSV with columns:
- Room Name
- Judge Capacity
- Room Event Type (roleplay/written)
- Event Name
- Event Type (roleplay/written)
- Start Time (e.g., "9:00 AM")
- Time Slot Duration (minutes)
- Group Size
- Exam Length (minutes)

## Algorithm

The scheduling algorithm works bottom-up (from granular to larger decisions):

1. **Parse Requests**: Convert student requests into assignments
2. **Judge Flexibility**: Prioritize judges with fewer event restrictions  
3. **Group Size Priority**: Handle larger groups first to minimize conflicts
4. **Assignment Rules**:
   - Check for time slot conflicts with overlapping students
   - Prevent back-to-back events for same students
   - Prefer adjacent time slots for same events
5. **Exam Scheduling**: Schedule exams for roleplay participants
6. **Room Distribution**: Spread judges evenly across available rooms

## Output

The scheduler generates:

- `output.csv` - Detailed schedule with time slots, room assignments, and exam times
- `output.log` - Execution log with warnings and debug information

## Testing

Run the test suite:

```bash
python -m unittest test_scheduler.py -v
```

## Differences from Go Version

This Python implementation maintains the same core algorithm and functionality as the original Go version with these adaptations:

- Uses Python data classes instead of Protocol Buffers
- Leverages Python's standard library (csv, datetime, logging)
- Follows Python naming conventions (snake_case)
- Includes comprehensive unit tests
- More readable error messages and logging

## Documentation

For detailed algorithm documentation, see the original `docs/scheduling.md` in the parent directory.