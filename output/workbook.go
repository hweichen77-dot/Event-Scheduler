package output

import (
	"Event-Scheduler/components/proto"
	"Event-Scheduler/scheduler"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/xuri/excelize/v2"
)

const block = 3

const (
	widthPadding = 3
	minWidth     = 8
	maxWidth     = 60
)

type sheet struct {
	name   string
	rows   [][]string
	merges []string
}

type session struct {
	judge string
	event string
	group string
}

type examRow struct {
	slot    int
	student string
	cells   []string
}

type leftoverRow struct {
	event  string
	people string
	cells  []string
}

func sheets(o scheduler.Output) []sheet {
	sessions := map[int]map[string][]session{}
	roomsByType := map[proto.EventType][]string{}
	seenRoom := map[string]bool{}
	for _, h := range o.Housings {
		room := fmt.Sprintf("%s (%s)", h.Room.Name, h.Room.EventType)
		if !seenRoom[room] {
			seenRoom[room] = true
			roomsByType[h.Room.EventType] = append(roomsByType[h.Room.EventType], room)
		}
		for _, j := range h.Judges {
			judge := fmt.Sprintf("%d - %s %s", j.Judge.Number, j.Judge.Firstname, j.Judge.Lastname)
			for slot, a := range j.Assignments {
				if a.Event == nil {
					continue
				}
				if sessions[slot] == nil {
					sessions[slot] = map[string][]session{}
				}
				sessions[slot][room] = append(sessions[slot][room], session{
					judge: judge, event: a.Event.Id, group: names(a.Group),
				})
			}
		}
	}
	for _, rooms := range roomsByType {
		sort.Strings(rooms)
	}

	slots := []int{}
	for slot := range sessions {
		slots = append(slots, slot)
	}
	sort.Ints(slots)

	band := func(rooms []string) ([][]string, []string) {
		rows := [][]string{}
		merges := []string{}
		for _, slot := range slots {
			slotRooms := []string{}
			for _, room := range rooms {
				if len(sessions[slot][room]) > 0 {
					slotRooms = append(slotRooms, room)
				}
			}
			if len(slotRooms) == 0 {
				continue
			}

			start := slotStart(o, slot)
			end := start
			if slot < len(o.Context.Divisions) {
				end = start.Add(time.Duration(o.Context.Divisions[slot]) * time.Minute)
			}
			window := fmt.Sprintf("%s - %s", start.Format(time.Kitchen), end.Format(time.Kitchen))

			for _, room := range slotRooms {
				entries := sessions[slot][room]
				sort.SliceStable(entries, func(i, j int) bool {
					if entries[i].judge != entries[j].judge {
						return entries[i].judge < entries[j].judge
					}
					if entries[i].event != entries[j].event {
						return entries[i].event < entries[j].event
					}
					return entries[i].group < entries[j].group
				})
			}

			if len(rows) > 0 {
				rows = append(rows, []string{})
			}
			rows = append(rows, []string{window})

			roomRow := []string{}
			headerRow := []string{}
			for index, room := range slotRooms {
				roomRow = append(roomRow, room, "", "")
				headerRow = append(headerRow, "Judge", "Event", "Participants")
				first, _ := excelize.ColumnNumberToName(index*block + 1)
				last, _ := excelize.ColumnNumberToName(index*block + block)
				merges = append(merges, fmt.Sprintf("%s%d:%s%d",
					first, len(rows)+1, last, len(rows)+1))
			}
			rows = append(rows, roomRow)
			rows = append(rows, headerRow)

			depth := 0
			for _, room := range slotRooms {
				if len(sessions[slot][room]) > depth {
					depth = len(sessions[slot][room])
				}
			}
			for i := 0; i < depth; i++ {
				row := []string{}
				for _, room := range slotRooms {
					entries := sessions[slot][room]
					if i < len(entries) {
						row = append(row, entries[i].judge, entries[i].event, entries[i].group)
					} else {
						row = append(row, "", "", "")
					}
				}
				rows = append(rows, row)
			}
		}
		return rows, merges
	}

	roleplayRows, roleplayMerges := band(roomsByType[proto.EventType_ROLEPLAY])
	writtenRows, writtenMerges := band(roomsByType[proto.EventType_WRITTEN])

	exams := []examRow{}
	for _, e := range o.Exams {
		start := slotStart(o, e.Start)
		end := start.Add(time.Duration(o.Context.Constraints.ExamLength) * time.Minute)
		student := fmt.Sprintf("%s %s", e.Student.Firstname, e.Student.Lastname)
		exams = append(exams, examRow{
			slot: e.Start, student: student,
			cells: []string{start.Format(time.Kitchen), end.Format(time.Kitchen), student},
		})
	}
	sort.SliceStable(exams, func(i, j int) bool {
		if exams[i].slot != exams[j].slot {
			return exams[i].slot < exams[j].slot
		}
		return exams[i].student < exams[j].student
	})

	leftovers := []leftoverRow{}
	for _, a := range o.Leftover {
		event := ""
		if a.Event != nil {
			event = a.Event.Id
		}
		people := names(a.Group)
		leftovers = append(leftovers, leftoverRow{
			event: event, people: people,
			cells: []string{event, people, a.Reason},
		})
	}
	sort.SliceStable(leftovers, func(i, j int) bool {
		if leftovers[i].event != leftovers[j].event {
			return leftovers[i].event < leftovers[j].event
		}
		return leftovers[i].people < leftovers[j].people
	})

	reviews := []leftoverRow{}
	for _, ov := range o.Overrides {
		judge := fmt.Sprintf("%d - %s %s", ov.Judge.Number, ov.Judge.Firstname, ov.Judge.Lastname)
		event := ""
		if ov.Event != nil {
			event = ov.Event.Id
		}
		people := names(ov.Group)
		reviews = append(reviews, leftoverRow{
			event: judge, people: event,
			cells: []string{judge, event, people, strings.Join(ov.Judge.Judgeable, ", ")},
		})
	}
	sort.SliceStable(reviews, func(i, j int) bool {
		if reviews[i].event != reviews[j].event {
			return reviews[i].event < reviews[j].event
		}
		return reviews[i].people < reviews[j].people
	})

	examRows := [][]string{{"Start", "End", "Student"}}
	for _, r := range exams {
		examRows = append(examRows, r.cells)
	}
	leftoverRows := [][]string{{"Event", "Participants", "Why it could not be scheduled"}}
	for _, r := range leftovers {
		leftoverRows = append(leftoverRows, r.cells)
	}
	reviewRows := [][]string{{"Judge", "Event", "Participants", "Events this judge signed up for"}}
	for _, r := range reviews {
		reviewRows = append(reviewRows, r.cells)
	}

	return []sheet{
		{name: "Roleplay", rows: roleplayRows, merges: roleplayMerges},
		{name: "Written", rows: writtenRows, merges: writtenMerges},
		{name: "Exams", rows: examRows},
		{name: "Unassigned", rows: leftoverRows},
		{name: "Review", rows: reviewRows},
	}
}

func columnWidths(rows [][]string) []float64 {
	widths := []float64{}
	for _, row := range rows {
		for i, value := range row {
			width := float64(len(value) + widthPadding)
			if width < minWidth {
				width = minWidth
			}
			if width > maxWidth {
				width = maxWidth
			}
			for i >= len(widths) {
				widths = append(widths, 0)
			}
			if width > widths[i] {
				widths[i] = width
			}
		}
	}
	return widths
}

func Workbook(path string, o scheduler.Output) error {
	f := excelize.NewFile()
	defer f.Close()

	for i, s := range sheets(o) {
		if i == 0 {
			if err := f.SetSheetName(f.GetSheetName(0), s.name); err != nil {
				return err
			}
		} else if _, err := f.NewSheet(s.name); err != nil {
			return err
		}

		for rowIndex, row := range s.rows {
			if len(row) == 0 {
				continue
			}
			cell, err := excelize.CoordinatesToCellName(1, rowIndex+1)
			if err != nil {
				return err
			}
			values := make([]interface{}, len(row))
			for i, v := range row {
				values[i] = v
			}
			if err := f.SetSheetRow(s.name, cell, &values); err != nil {
				return err
			}
		}

		for _, ref := range s.merges {
			parts := strings.Split(ref, ":")
			if err := f.MergeCell(s.name, parts[0], parts[1]); err != nil {
				return err
			}
		}

		for i, width := range columnWidths(s.rows) {
			name, err := excelize.ColumnNumberToName(i + 1)
			if err != nil {
				return err
			}
			if err := f.SetColWidth(s.name, name, name, width); err != nil {
				return err
			}
		}
	}

	return f.SaveAs(path)
}
