package main

import (
	"Event-Scheduler/components/proto"
	"Event-Scheduler/scheduler"
	"fmt"
	"log"
	"strconv"
	"strings"
	"time"
)

func FindStudent(pool []*proto.Student, first, last string) (*proto.Student, bool) {
	first = strings.ToLower(first)
	last = strings.ToLower(last)
	for _, s := range pool {
		if first == strings.ToLower(s.Firstname) && last == strings.ToLower(s.Lastname) {
			return s, false
		}
	}
	return &proto.Student{
		Email:     fmt.Sprintf("%v.%v@warriorlife.net", first, last),
		Firstname: first,
		Lastname:  last,
	}, true
}

func SplitName(combined string) (string, string) {
	without := strings.ReplaceAll(string(
		parenthesis.ReplaceAll([]byte(combined), []byte("")),
	), ",", "")
	parts := strings.Split(without, " ")
	normalized := []string{}
	for _, l := range parts {
		if len(l) > 0 {
			normalized = append(normalized, l)
		}
	}
	if len(normalized) == 0 {
		return "", ""
	}
	if len(normalized) == 1 {
		return normalized[0], ""
	}
	return normalized[0], normalized[1]
}

func Cell(l []string, i int) string {
	if i < len(l) {
		return strings.TrimSpace(l[i])
	}
	return ""
}

func clean(s string) string {
	return strings.Join(strings.Fields(string(
		parenthesis.ReplaceAll([]byte(s), []byte("")),
	)), " ")
}

func SplitLastFirst(combined string) (string, string) {
	if last, first, found := strings.Cut(combined, ","); found {
		return clean(last), clean(first)
	}
	last, first := SplitName(combined)
	return last, first
}

func SplitFirstLast(combined string) (string, string) {
	parts := strings.Fields(clean(combined))
	if len(parts) == 0 {
		return "", ""
	}
	if len(parts) == 1 {
		return parts[0], ""
	}
	return parts[0], strings.Join(parts[1:], " ")
}

func ParseStudents(lines [][]string) ([]*proto.Student, map[string]*proto.Student) {
	students := []*proto.Student{}
	byEmail := map[string]*proto.Student{}

	register := func(email, lastFirst, firstLast string) {
		email = strings.ToLower(email)
		if email == "" {
			return
		}
		if _, ok := byEmail[email]; ok {
			return
		}

		var firstname, lastname string
		if lastFirst != "" {
			lastname, firstname = SplitLastFirst(lastFirst)
		} else {
			firstname, lastname = SplitFirstLast(firstLast)
		}

		s := &proto.Student{
			Email:     email,
			Firstname: firstname,
			Lastname:  lastname,
		}
		byEmail[email] = s
		students = append(students, s)
	}

	for _, l := range lines {
		register(Cell(l, 0), Cell(l, 1), "")
		register(Cell(l, 8), Cell(l, 5), Cell(l, 4))
		register(Cell(l, 9), Cell(l, 7), Cell(l, 6))
	}
	return students, byEmail
}

func ParseRequests(lines [][]string, students *[]*proto.Student, byEmail map[string]*proto.Student) []*proto.StudentRequest {
	requests := []*proto.StudentRequest{}
	for _, l := range lines {
		email := strings.ToLower(Cell(l, 0))
		if email == "" {
			continue
		}

		event := strings.Split(Cell(l, 3), " ")[0]

		group := []string{email}
		for _, i := range []int{8, 9} {
			partner := strings.ToLower(Cell(l, i))
			if partner != "" {
				group = append(group, partner)
			}
		}

		if named := Cell(l, 2); named != "" && len(group) == 1 {
			scheduler.Warn(fmt.Sprintf(
				"%v named partner(s) \"%v\" but gave no partner email, leaving them out of the group",
				email, named,
			))
		}

		if strings.HasSuffix(event, "TDM") && len(group) < 2 {
			scheduler.Warn(fmt.Sprintf(
				"%v is a team event but %v entered it alone, check the partner columns of the student form",
				event, email,
			))
		}

		requests = append(requests, &proto.StudentRequest{
			Event: event,
			Group: group,
		})
	}

	return requests
}

func ParseJudges(rows [][]string) []*proto.Judge {
	judges := []*proto.Judge{}
	for i, row := range rows {
		events := []string{}
		for _, e := range strings.Split(row[2], ",") {
			trimmed := strings.TrimSpace(e)
			if trimmed != "" {
				events = append(events, trimmed)
			}
		}
		if len(events) == 0 {
			scheduler.Warn(fmt.Sprintf(
				"judge %v %v %v lists no events, so they will be treated as able to judge anything",
				i+1, row[0], row[1],
			))
		}
		judges = append(judges, &proto.Judge{
			Number:    int32(i) + 1,
			Firstname: row[0],
			Lastname:  row[1],
			Judgeable: events,
		})
	}
	return judges
}

// used instead of time.Kitchen because google sheets adds a space
// between the time and meridiem specifier
var timeFormat = "3:00 PM"

func ParseTime(row []string) time.Time {
	startTime, err := time.ParseInLocation(timeFormat, row[0], time.Local)
	if err != nil {
		log.Fatalf(
			"[ERROR] timestamp parsing error! "+
				"please ensure you have written in this exact format \"%s\" "+
				"with the correct capitals and no spaces\n", timeFormat,
		)
	}
	return startTime
}

func ParseDivisions(rows [][]string) []int32 {
	divisions := []int32{}
	for _, row := range rows {
		if row[0] == "NaN" {
			continue
		}
		slot, err := strconv.ParseInt(row[0], 10, 64)
		if err != nil {
			panic(err)
		}
		divisions = append(divisions, int32(slot))
	}
	return divisions
}

func ParseRooms(rows [][]string) []*proto.Room {
	rooms := []*proto.Room{}
	for _, row := range rows {
		if row[0] == "" {
			continue
		}
		capacity, err := strconv.ParseInt(row[1], 10, 32)
		if err != nil {
			capacity = 0
		}
		rooms = append(rooms, &proto.Room{
			Name:          row[0],
			JudgeCapacity: int32(capacity),
			EventType:     ParseEventType(row[2]),
		})
	}
	return rooms
}

var eventTypes = map[string]proto.EventType{
	"roleplay": proto.EventType_ROLEPLAY,
	"written":  proto.EventType_WRITTEN,
}

func ParseEventType(text string) proto.EventType {
	eventType, ok := eventTypes[strings.ToLower(strings.Trim(text, " "))]
	if !ok {
		log.Fatalf(
			"[ERROR] unknown event type, please specify an event type of either \"roleplay\" or \"written\" got \"%s\"",
			text,
		)
	}
	return eventType
}

func ParseEvents(rows [][]string) []*proto.Event {
	events := []*proto.Event{}
	for _, row := range rows {
		if row[0] == "" {
			continue
		}
		events = append(events, &proto.Event{
			Id:        row[0],
			EventType: ParseEventType(row[1]),
		})
	}
	return events
}

func ParseNumber(row []string) int32 {
	groupSize, err := strconv.ParseInt(row[0], 10, 32)
	if err != nil {
		panic(err)
	}
	return int32(groupSize)
}

type Participation int

const (
	WrittenAndRoleplay Participation = iota
	OnlyWritten
	OnlyRoleplay
)

func ParseParticipationValue(text string) Participation {
	normalized := strings.Join(strings.Fields(strings.ToLower(text)), " ")
	switch normalized {
	case "only written", "written only":
		return OnlyWritten
	case "only roleplay", "roleplay only":
		return OnlyRoleplay
	}
	return WrittenAndRoleplay
}

func ParseParticipation(lines [][]string) map[string]Participation {
	participation := map[string]Participation{}
	for _, l := range lines {
		email := strings.ToLower(Cell(l, 0))
		if email == "" {
			continue
		}
		if value := ParseParticipationValue(Cell(l, 10)); value != WrittenAndRoleplay {
			participation[email] = value
		}
	}
	return participation
}

func SkipsEventType(p Participation, eventType proto.EventType) bool {
	return (p == OnlyWritten && eventType == proto.EventType_ROLEPLAY) ||
		(p == OnlyRoleplay && eventType == proto.EventType_WRITTEN)
}

func ApplyParticipation(
	requests []*proto.StudentRequest,
	events []*proto.Event,
	participation map[string]Participation,
) []*proto.StudentRequest {
	types := map[string]proto.EventType{}
	for _, e := range events {
		types[e.Id] = e.EventType
	}

	kept := []*proto.StudentRequest{}
	for _, r := range requests {
		eventType, ok := types[r.Event]
		if !ok {
			kept = append(kept, r)
			continue
		}

		group := []string{}
		for _, email := range r.Group {
			if SkipsEventType(participation[email], eventType) {
				scheduler.Info(fmt.Sprintf(
					"%v is only doing one event type at this conference, leaving them out of %v",
					email, r.Event,
				))
				continue
			}
			group = append(group, email)
		}

		if len(group) == 0 {
			continue
		}
		if strings.HasSuffix(r.Event, "TDM") && len(group) < 2 && len(r.Group) >= 2 {
			scheduler.Warn(fmt.Sprintf(
				"%v is a team event but only %v is left after removing teammates who skip roleplays",
				r.Event, group[0],
			))
		}

		kept = append(kept, &proto.StudentRequest{
			Event: r.Event,
			Group: group,
		})
	}
	return kept
}
