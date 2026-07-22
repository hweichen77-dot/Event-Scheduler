"""
Core scheduling algorithm for the Event Scheduler.
Equivalent to the Go scheduler/main.go functionality.
"""
import logging
from typing import List, Dict, Optional
from .types import (
    ScheduleContext, Student, StudentRequest, Assignment, Judgement,
    Housing, Exam, Output, EventType, Time, Constraints, Registration,
    Unplaced, Override
)
from .common import unordered_equal, intersects, has_adjacent, keys


def info(message: str):
    """Log info message."""
    logging.info(f"[INFO] {message}")


def warn(message: str):
    """Log warning message."""
    logging.warning(f"[WARN] {message}")


def format_event(event) -> str:
    """Format event for logging."""
    return f'"{event.id}"'


def format_group(group: List[Student]) -> str:
    """Format group for logging."""
    group_text = [f"{s.firstname} {s.lastname}" for s in group]
    return f"[{', '.join(group_text)}]"


def new_context(time: Time, constraints: Constraints, registration: Registration) -> ScheduleContext:
    """Create a new schedule context."""
    students = {s.email: s for s in registration.students}
    judges = {j.number: j for j in registration.judges}
    events = {e.id: e for e in registration.events}
    
    return ScheduleContext(
        time=time,
        constraints=constraints,
        students=students,
        judges=judges,
        events=events,
        rooms=registration.rooms
    )


def schedule(context: ScheduleContext, requests: List[StudentRequest]) -> Output:
    """Main scheduling algorithm."""
    should_take_exam = {}
    
    assignments = []
    
    # Process student requests into assignments
    for request in requests:
        group = []
        for student_email in request.group:
            student = context.students.get(student_email)
            if not student:
                info(f"group's partner ({student_email}) does not exist, skipping...")
                continue
            group.append(student)
        
        event = context.events.get(request.event)
        if not event:
            warn(f"event {request.event} is not offered in the conference form, "
                 f"dropping the request from {format_group(group)}")
            continue
        
        if context.constraints.group_size > 0 and len(group) > context.constraints.group_size:
            warn(f"{format_group(group)} has {len(group)} members, more than the "
                 f"{context.constraints.group_size} allowed, dropping the request for "
                 f"{format_event(event)}")
            continue

        # Mark students for exam if it's a roleplay event
        if event.event_type == EventType.ROLEPLAY:
            for student_email in request.group:
                should_take_exam[student_email] = True
        
        # Check for duplicate requests
        duplicate = False
        for assignment in assignments:
            if (unordered_equal([s.email for s in assignment.group], [s.email for s in group])
                    and assignment.event == event):
                info(f"duplicate student requests ({format_event(event)} - {format_group(assignment.group)}) skipping...")
                duplicate = True
                break
        
        if not duplicate:
            assignments.append(Assignment(event=event, group=group))
    
    # Sort requests from largest group to smallest group
    assignments.sort(key=lambda a: len(a.group), reverse=True)
    
    # Initialize judge structures
    judges = []
    for judge in context.judges.values():
        judgement = Judgement(
            judge=judge,
            assignments=[Assignment() for _ in range(len(context.time.divisions))]
        )
        judges.append(judgement)
    
    # Sort judges from least flexible to most flexible
    judges.sort(key=lambda j: (len(j.judge.judgeable), j.judge.number))
    
    def judge_type(judgement: Judgement) -> EventType:
        if judgement.judge.judgeable:
            event = context.events.get(judgement.judge.judgeable[0])
            if event:
                return event.event_type
        return EventType.ROLEPLAY

    def calculate_occupied(group: List[Student]) -> Dict[int, bool]:
        """Calculate which time slots are occupied for a given group."""
        occupied = {}
        for judge in judges:
            for i in range(len(context.time.divisions)):
                if intersects([s.email for s in judge.assignments[i].group], [s.email for s in group]):
                    occupied[i] = True
        return occupied
    
    def assign_request(occupied: Dict[int, bool], assignment: Assignment, strict: bool,
                       any_event: bool = False) -> Optional[Judgement]:
        """Try to assign a request to a judge."""
        for judge in judges:
            if any_event and judge_type(judge) != assignment.event.event_type:
                continue
            # Check if judge can handle this event
            if (not any_event and
                len(judge.judge.judgeable) > 0 and
                not intersects([assignment.event.id], judge.judge.judgeable)):
                continue
            
            for i in range(len(context.time.divisions)):
                if occupied.get(i, False):
                    continue
                if judge.assignments[i].event is not None:
                    continue
                
                # Check for back-to-back conflicts
                back_to_back = False
                for j in judges:
                    if has_adjacent(j.assignments, i, 
                                  lambda adj, above: intersects([s.email for s in adj.group], 
                                                              [s.email for s in assignment.group])):
                        back_to_back = True
                        break
                
                if back_to_back:
                    continue
                
                if strict:
                    # Check for adjacent assignment with same event
                    if has_adjacent(judge.assignments, i,
                                  lambda adj, above: adj.event is not None and adj.event.id == assignment.event.id):
                        judge.assignments[i] = assignment
                        return judge
                    return None

                judge.assignments[i] = assignment
                return judge
        return None

    def has_legal_slot(occupied: Dict[int, bool], assignment: Assignment) -> bool:
        for i in range(len(context.time.divisions)):
            if occupied.get(i, False):
                continue
            adjacent = False
            for j in judges:
                if has_adjacent(j.assignments, i,
                                lambda adj, above: intersects([s.email for s in adj.group],
                                                              [s.email for s in assignment.group])):
                    adjacent = True
                    break
            if not adjacent:
                return True
        return False

    # Assign requests to judges
    leftover = []
    overrides = []
    for assignment in assignments:
        occupied = calculate_occupied(assignment.group)

        # Try strict assignment first, then relaxed
        if assign_request(occupied, assignment, True) is not None:
            continue
        if assign_request(occupied, assignment, False) is not None:
            continue

        fallback = assign_request(occupied, assignment, False, True)
        if fallback is not None:
            warn(f"no judge for {format_event(assignment.event)} was free, "
                 f"assigning {format_group(assignment.group)} to judge "
                 f"{fallback.judge.firstname} {fallback.judge.lastname} who does not list it")
            overrides.append(Override(
                judge=fallback.judge,
                event=assignment.event,
                group=assignment.group,
            ))
            continue

        reason = "every judge for this event is already booked"
        if not has_legal_slot(occupied, assignment):
            reason = "no legal timeslot: the group's other events block every slot"
        leftover.append(Unplaced(
            event=assignment.event,
            group=assignment.group,
            reason=reason,
        ))
    
    # Handle exam scheduling
    exams = []
    exam_candidates = sorted(context.students.values(), key=lambda s: s.email)
    for student in exam_candidates:
        if not should_take_exam.get(student.email, False):
            continue
        
        occupied = calculate_occupied([student])
        
        start = 0
        sum_duration = 0
        for i in range(len(context.time.divisions)):
            if i not in occupied:
                sum_duration += context.time.divisions[i]
                if sum_duration >= context.constraints.exam_length:
                    exams.append(Exam(start=start, student=student))
                    break
                continue
            else:
                sum_duration = 0
                start = i + 1
        else:
            warn(f"could not find a suitable exam time for student {student.firstname} {student.lastname}")
    
    # Report leftover assignments
    if leftover:
        warn(f"there are {len(leftover)} leftover student requests that could not be assigned without conflicts")
        for assignment in leftover:
            logging.info(f"{format_event(assignment.event)} {format_group(assignment.group)} "
                         f"- {assignment.reason}")
        
        # Calculate percentage due to no available judges
        no_judge_events = set()
        no_judge_count = 0
        for assignment in leftover:
            judgeable = False
            for judge in judges:
                if intersects(judge.judge.judgeable, [assignment.event.id]):
                    judgeable = True
                    break
            if not judgeable:
                no_judge_count += 1
                no_judge_events.add(assignment.event.id)
        
        if leftover:
            percentage = (no_judge_count / len(leftover)) * 100
            warn(f"{percentage:.1f}% of leftover requests are due to having no judges able to judge {list(no_judge_events)}")
    
    # Create housing assignments
    typed_judge_set = {}
    typed_room_set = {}
    
    for judge in judges:
        judge_event_type = EventType.ROLEPLAY
        if judge.judge.judgeable:
            event = context.events.get(judge.judge.judgeable[0])
            if event:
                judge_event_type = event.event_type
        if judge_event_type not in typed_judge_set:
            typed_judge_set[judge_event_type] = []
        typed_judge_set[judge_event_type].append(judge)

    for room in context.rooms:
        if room.event_type not in typed_room_set:
            typed_room_set[room.event_type] = []
        typed_room_set[room.event_type].append(room)
    
    housings = {}
    for event_type, rooms in typed_room_set.items():
        judges_for_type = typed_judge_set.get(event_type, [])
        housings[event_type] = [Housing(room=room) for room in rooms]

        room_index = 0
        judge_index = 0
        filled_explored = 0

        while judge_index < len(judges_for_type):
            housing = housings[event_type][room_index]

            if len(housing.judges) < housing.room.judge_capacity:
                housing.judges.append(judges_for_type[judge_index])
                judge_index += 1
                filled_explored = 0
            else:
                filled_explored += 1
                if filled_explored >= len(rooms):
                    warn(f'there is not enough room to house all the judges for the event type "{event_type.name}" '
                         f'try adjusting "Judge Capacity", {len(judges_for_type) - judge_index} judges will be dropped')
                    break
            
            room_index = (room_index + 1) % len(rooms)
    
    # Flatten housing
    flattened_housing = []
    for housing_list in housings.values():
        flattened_housing.extend(housing_list)
    
    return Output(
        housings=flattened_housing,
        context=context,
        exams=exams,
        leftover=leftover,
        overrides=overrides
    )