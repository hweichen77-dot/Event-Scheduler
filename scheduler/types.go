package scheduler

import (
	"Event-Scheduler/components/proto"
)

// decisions
type Output struct {
	Housings  []Housing
	Context   ScheduleContext
	Exams     []Exam
	Leftover  []Unplaced
	Overrides []Override
}

type Unplaced struct {
	Event  *proto.Event
	Group  []*proto.Student
	Reason string
}

type Override struct {
	Judge *proto.Judge
	Event *proto.Event
	Group []*proto.Student
}

type Exam struct {
	Start   int
	Student *proto.Student
}

type Housing struct {
	Room   *proto.Room
	Judges []*Judgement
}

type Judgement struct {
	Judge       *proto.Judge
	Assignments []Assignment
}

type Assignment struct {
	Event *proto.Event
	Group []*proto.Student
}
