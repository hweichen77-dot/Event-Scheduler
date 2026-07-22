### scheduling

*this scheduling algorithm was written by someone who has never done a lick of scheduling, if you have a better implementation, feel free to step right up*

#### inputs

- time
    - `time start` - the starting time
    - `time divisions` - a list of durations specifying "slots of time"
- constraints
    - `group size` - the max size of a group
    - `exam length` - the length of an exam
- `students` - a list of students
- `judges` - a list of judges
- `events` - a list of events
- `rooms` - a list of occupiable rooms
- `student requests` - a list of "requests" by a student to join an event

#### outputs

- `assignment` - a student + the event they wish to attend
- `judgement` - a judge + the `assignments` they will judge throughout the divisions of time
- `housing` - a room + the `judgements` that will be happening in the room
- `exams` - exam times and the students that will take them

#### algorithm

the algorithm of the scheduler works bottom to top (from the most granular decisions to the larger ones)

1. parse the `student requests` into `assignments`.
1. leave the judges with the most flexibility for last
    1. this is done to ensure that a request that could be handled by a judge with less flexibility does not get delegated to one of more flexibility, as the one with more flexibility is able to handle more requests
    1. implementation: sort judges least to greatest based on the length of their event restriction
1. prioritize requests with the most members in their group
    1. this is done to minimize conflicts due to people being in different places at the same time
    1. implementation: sort requests greatest to least based on the size of their group
1. assign requests to judges based on a few rules
    1. get the divisions of time that are "occupied" by an existing request
        - here, "occupied" means another request in the same time division that shares some students with the current request's group
    1. search all time divisions of all judges, if a time division is empty (not taken by an existing assignment) and not part of the "occupied". assign the request to it.
        - to minimize students rushing around to get to all their events, we chose to disallow "back to back" events. that means, events whose group members intersect with the group members of directly adjacent events in the timeslot above or below
1. if there are leftovers, warn the user
1. assign students to exam times based on a few rules
    1. get the divisions of time that are "occupied" by an existing assignment
    1. check if there is a block of consecutive free timeslots whose duration is enough to house the given exam length
        - back to back exams/judged events are okay
    1. if so add the student and start time to the exam list
    1. if not, warn the user
1. attempt to spread the judges evenly across the rooms, match judge event types to room event types
