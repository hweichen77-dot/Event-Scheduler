# Event Scheduler

*Scheduling system for mock DECA conferences*

A comprehensive event scheduling system with both Go and Python implementations. This tool automatically assigns students to events, schedules judges, manages room capacity, and handles exam scheduling for competitive events.

## Features

- **Smart Scheduling Algorithm**: Automatically resolves conflicts and optimizes assignments
- **Dual Implementation**: Choose between Go (performance) or Python (simplicity)
- **Judge Management**: Intelligent assignment based on expertise and availability
- **Room Optimization**: Efficient distribution of judges across available rooms
- **Exam Scheduling**: Automatic scheduling for roleplay events
- **CSV Integration**: Easy import/export with spreadsheet applications
- **Comprehensive Logging**: Detailed execution logs for debugging and analysis

## Repository Structure

```
Event-Scheduler/
├── cmd/                 # Go application commands
│   └── real/           # Main Go application
├── components/         # Go components and protobuf definitions
├── scheduler/          # Go core scheduling logic
├── output/            # Go output generation
├── proto/             # Protocol buffer definitions
├── python/            # Python implementation
│   ├── main.py        # Python entry point
│   ├── scheduler.py   # Core algorithm
│   ├── types.py       # Data structures
│   └── ...           # Other Python modules
├── docs/              # Documentation
├── tests/             # Go tests
├── go.mod            # Go module definition
└── README.md         # This file
```

## Quick Start

### Go Implementation

```bash
# Build and run
cd cmd/real
go build && ./real

# Or use make
make build && make run
```

### Python Implementation

```bash
# Run directly
cd python
python main.py

# Or use make
cd python
make run
```

Both implementations will generate:
- `output.csv` - Detailed schedule
- `output.log` - Execution logs

## Input Requirements

### Student Registration (`new_students_form.csv`)
```csv
Email,Name,Partners,Event
student@school.edu,"Last, First","Partner1, Partner2",EventName
```

### Judge Registration (`judges_event_form.csv`)
```csv
First Name,Last Name,Judgeable Events
John,Doe,"Event1, Event2, Event3"
```

### Conference Details (`conference_form.csv`)
```csv
Room,Judge Capacity,Room Event Type,Event,Event Type,Start Time,Time Slot,Group Size,Exam Length
Room A,2,roleplay,Event1,roleplay,9:00 AM,60,4,60
```

## Configuration

### Time Settings
- **Start Time**: Conference start time (e.g., "9:00 AM")
- **Time Slots**: Duration of each scheduling block in minutes
- **Exam Length**: Duration for written exams in minutes

### Constraints
- **Group Size**: Maximum students per group
- **Room Capacity**: Maximum judges per room
- **Event Types**: `roleplay` or `written`

## Algorithm Overview

The scheduling system uses a sophisticated bottom-up approach:

1. **Request Processing**: Parse student requests into group assignments
2. **Judge Prioritization**: Handle less flexible judges first
3. **Group Size Optimization**: Schedule larger groups first to minimize conflicts
4. **Conflict Resolution**: 
   - Prevent overlapping assignments for shared students
   - Avoid back-to-back events for same participants
   - Optimize adjacent time slots for same events
5. **Exam Scheduling**: Automatic exam slots for roleplay participants
6. **Room Distribution**: Even distribution of judges across available rooms

For detailed algorithm documentation, see [`docs/scheduling.md`](docs/scheduling.md).

## Testing

### Go Tests
```bash
go test ./tests/...
```

### Python Tests
```bash
cd python
python -m unittest test_scheduler.py -v
```

## Output Format

The generated `output.csv` contains:

1. **Room Layout**: Visual representation of room assignments
2. **Judge Schedule**: Time-based judge assignments with student groups
3. **Event Details**: Complete event and participant information
4. **Exam Schedule**: Separate section for exam times and participants

## Troubleshooting

Common issues and solutions:

- **Missing Students**: The system automatically creates missing students from partner lists
- **Judge Conflicts**: Check judge availability and event expertise in logs
- **Room Capacity**: Verify room judge capacity settings
- **Time Conflicts**: Review time slot durations and exam lengths

Check `output.log` for detailed warnings and suggestions.

## Deployment

### Go Binary
```bash
# Build for current platform
go build -o scheduler ./cmd/real

# Cross-compile for different platforms
GOOS=windows GOARCH=amd64 go build -o scheduler.exe ./cmd/real
GOOS=linux GOARCH=amd64 go build -o scheduler-linux ./cmd/real
```

### Python Standalone
```bash
# Create distributable package
cd python
python -m py_compile *.py
```

## What I contributed

This repository is a copy of [isabella354/Event-Scheduler](https://github.com/isabella354/Event-Scheduler), where the scheduler was originally written by Grace Xu and Isabella Yu for our DECA chapter's mock conference. My work on it was four commits in July 2026, described below. Each one links to the commit in the original repository.

### Excel output, reproducible runs, and a working Python port ([69eff1c](https://github.com/isabella354/Event-Scheduler/commit/69eff1c))

The scheduler only produced a CSV that was hard to read on the day of the conference, so I added a `schedule.xlsx` workbook with separate tabs for roleplay sessions, written events, exams, and unassigned requests. Sessions are grouped by time slot, each room gets one merged block, and column widths are sized to their contents so no room number or student name is cut off. The Go version writes the workbook with excelize and the Python version writes it with the standard library.

While testing it I noticed the schedule came out different on every run with the same inputs. Go randomizes map iteration order, and the judge sort had ties that the iteration order was silently breaking. I made the sort break ties by judge number and iterate students by email, so a given set of forms now always produces the same schedule.

The Python implementation was also building request groups from a positional index into the deduplicated student list. Because deduplication changed the list length, requests were attached to the wrong students and the loop eventually ran past the end of the list. I keyed the groups on the row's email instead, resolved conference columns by header name rather than fixed position, and matched the Go behavior for strict assignment, judge housing, and duplicate detection. After this the two implementations produce byte-identical output for the same inputs, which is how I checked the later fixes.

### Fallback judge assignment ([15fa1bf](https://github.com/isabella354/Event-Scheduler/commit/15fa1bf))

Requests were only ever matched to judges who listed that event, so 26 requests were left unscheduled while judges sat with open slots. I added a second pass: once no specialty-matched judge is free, the request goes to any judge with an open slot. Student conflicts and the back to back rule still apply, and every fallback placement is logged with the judge's name and the event they did not sign up for, so an adviser can review them before the conference.

Unassigned requests dropped from 26 to 5 and all 43 judges are now used. The remaining 5 cannot be placed at all: there were 216 student requests and only 215 judge slots, so at least one request is impossible regardless of the algorithm.

### Identifying students by email instead of by name ([86881b2](https://github.com/isabella354/Event-Scheduler/commit/86881b2))

The registration form collects an email for each partner, but the parser read only the captain's email and matched partners by name. It split names on the first two words, so a partner with a multi-word name never matched their roster entry. The parser then created a second record for that person with an invented email.

One competitor was scheduled into two rooms at the same time, once under his real record and once under the invented one. The conflict checks could not see the clash because the two records looked like two different people. Ten other partners who never filled out their own row were invented the same way and scheduled into events and exams.

I changed the parser to register students from the captain email column and both partner email columns, and to build request groups from those emails. Names are now used only for display, so name parsing can no longer affect who gets scheduled. The result is 149 real students with no invented records and no one double booked. I also added a missing event to the conference form and made the scheduler warn, rather than log quietly, when a request names an event the conference does not offer.

### Room matching, group size limits, and reviewable output ([1b0ec98](https://github.com/isabella354/Event-Scheduler/commit/1b0ec98))

The fallback pass from the earlier commit was too permissive: it could place a roleplay into a room set up for written events. I restricted it to judges whose room type matches the event. I also made the scheduler enforce the group size from the conference form, dropping oversized groups with a warning instead of scheduling them.

Name parsing now splits on the comma the form already uses, so a surname like "Ka Yu, Chun" is no longer truncated. Two new warnings cover data problems that used to pass silently: a team event entered by a single competitor, which can only come from a parsing or data error, and a judge who lists no events at all, which quietly made them eligible to judge anything.

For the output, the unassigned tab now records why each request could not be scheduled, and a new review tab lists every judge who was given an event they did not sign up for. Both exist so the schedule can be checked by hand before the conference rather than debugged during it.

### A note on the data in this repository

The input forms here are generated sample data. The real conference ran on forms containing student names and school email addresses, which are not published here. The synthetic roster keeps the same shape as the real one, including the same number of rows, the same event mix, and the same pattern of solo and team entries, so the scheduler exercises the same paths.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

## Related Documentation

- [Scheduling Algorithm Details](docs/scheduling.md)
- [Coding Conventions](docs/conventions.md)
- [Python Implementation](python/README.md)

## Use Cases

- **DECA Conferences**: Mock competitive business events
- **Academic Competitions**: Judge and room management
- **Workshop Scheduling**: Multi-track event coordination
- **General Event Management**: Any scenario requiring judge assignment and room allocation