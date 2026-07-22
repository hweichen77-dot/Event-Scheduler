package output

import (
	"Event-Scheduler/components/proto"
	"Event-Scheduler/scheduler"
	"encoding/csv"
	"fmt"
	"io"
	"sort"
	"strings"
	"time"
)

type sheetRow struct {
	order  int
	slot   int
	kind   string
	start  string
	end    string
	room   string
	judge  string
	event  string
	people string
}

func names(group []*proto.Student) string {
	out := []string{}
	for _, s := range group {
		out = append(out, strings.TrimSpace(fmt.Sprintf("%s %s", s.Firstname, s.Lastname)))
	}
	return strings.Join(out, ", ")
}

func slotStart(o scheduler.Output, slot int) time.Time {
	start := time.Unix(o.Context.Time.Start, 0)
	for i := 0; i < slot && i < len(o.Context.Divisions); i++ {
		start = start.Add(time.Duration(o.Context.Divisions[i]) * time.Minute)
	}
	return start
}

func Sheet(f io.Writer, o scheduler.Output) error {
	rows := []sheetRow{}

	for _, h := range o.Housings {
		room := fmt.Sprintf("%s (%s)", h.Room.Name, h.Room.EventType)
		for _, j := range h.Judges {
			judge := fmt.Sprintf("%d - %s %s", j.Judge.Number, j.Judge.Firstname, j.Judge.Lastname)
			for slot, a := range j.Assignments {
				if a.Event == nil {
					continue
				}
				start := slotStart(o, slot)
				end := start
				if slot < len(o.Context.Divisions) {
					end = start.Add(time.Duration(o.Context.Divisions[slot]) * time.Minute)
				}
				rows = append(rows, sheetRow{
					order:  0,
					slot:   slot,
					kind:   "Event",
					start:  start.Format(time.Kitchen),
					end:    end.Format(time.Kitchen),
					room:   room,
					judge:  judge,
					event:  a.Event.Id,
					people: names(a.Group),
				})
			}
		}
	}

	for _, e := range o.Exams {
		start := slotStart(o, e.Start)
		end := start.Add(time.Duration(o.Context.Constraints.ExamLength) * time.Minute)
		rows = append(rows, sheetRow{
			order:  1,
			slot:   e.Start,
			kind:   "Exam",
			start:  start.Format(time.Kitchen),
			end:    end.Format(time.Kitchen),
			room:   "-",
			judge:  "-",
			people: fmt.Sprintf("%s %s", e.Student.Firstname, e.Student.Lastname),
		})
	}

	for _, a := range o.Leftover {
		event := ""
		if a.Event != nil {
			event = a.Event.Id
		}
		rows = append(rows, sheetRow{
			order:  2,
			kind:   "UNASSIGNED",
			room:   "-",
			judge:  "-",
			event:  event,
			people: names(a.Group),
		})
	}

	sort.SliceStable(rows, func(i, j int) bool {
		if rows[i].order != rows[j].order {
			return rows[i].order < rows[j].order
		}
		if rows[i].slot != rows[j].slot {
			return rows[i].slot < rows[j].slot
		}
		if rows[i].room != rows[j].room {
			return rows[i].room < rows[j].room
		}
		return rows[i].judge < rows[j].judge
	})

	writer := csv.NewWriter(f)
	defer writer.Flush()

	if err := writer.Write([]string{"Start", "End", "Type", "Room", "Judge", "Event", "Participants"}); err != nil {
		return err
	}
	for _, r := range rows {
		if err := writer.Write([]string{
			r.start, r.end, r.kind, r.room, r.judge, r.event, r.people,
		}); err != nil {
			return err
		}
	}
	return nil
}
