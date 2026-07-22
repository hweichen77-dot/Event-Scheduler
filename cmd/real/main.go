package main

import (
	"Event-Scheduler/components/proto"
	"Event-Scheduler/output"
	"Event-Scheduler/scheduler"
	"encoding/csv"
	"flag"
	"log"
	"os"
	"regexp"
	"strings"

	"github.com/go-gota/gota/dataframe"
)

var parenthesis = regexp.MustCompile(`\(.+\)`)

func main() {
	//* setup
	f, err := os.Create("output.log")
	if err != nil {
		panic(err)
	}
	defer f.Close()
	log.SetOutput(f)

	studentRegistrationFilePtr := flag.String("student", "new_students_form.csv", "student registration file")
	judgeRegistrationFilePtr := flag.String("judge", "judges_event_form.csv", "judge registration file")
	conferenceFilePtr := flag.String("conference", "conference_form.csv", "conference details file")

	flag.Parse()

	//* parse students and student requests
	f, err = os.Open(*studentRegistrationFilePtr)
	if err != nil {
		panic(err)
	}
	reader := csv.NewReader(f)
	lines, err := reader.ReadAll()
	if err != nil {
		panic(err)
	}

	lines = lines[1:]
	parsedStudents, byEmail := ParseStudents(lines)
	students := &parsedStudents
	requests := ParseRequests(lines, students, byEmail)

	log.Println("================================== Registered students")
	for _, s := range *students {
		log.Println(s.Firstname, s.Lastname, s.Email)
	}
	log.Println("================================== Registered requests")
	for _, r := range requests {
		log.Println(r.Event, r.Group)
	}

	//* parse judges and conference data
	judgeFile, err := os.Open(*judgeRegistrationFilePtr)
	if err != nil {
		panic(err)
	}
	conferenceFile, err := os.Open(*conferenceFilePtr)
	if err != nil {
		panic(err)
	}
	judgeDf := dataframe.ReadCSV(judgeFile)
	conferenceDf := dataframe.ReadCSV(conferenceFile)

	judges := ParseJudges(judgeDf.Records()[1:])
	rooms := ParseRooms(conferenceDf.Select([]string{"Room", "Judge Capacity", "Room Event Type"}).Records()[1:])
	events := ParseEvents(conferenceDf.Select([]string{"Event", "Event Type"}).Records()[1:])

	startTime := ParseTime(conferenceDf.Select([]string{"Start Time"}).Records()[1])
	divisions := ParseDivisions(conferenceDf.Select([]string{"Time Slot"}).Records()[1:])

	groupSize := ParseNumber(conferenceDf.Select([]string{"Group Size"}).Records()[1])
	examLength := ParseNumber(conferenceDf.Select([]string{"Exam Length"}).Records()[1])

	log.Println("================================== Registered judges")
	for _, j := range judges {
		log.Println(j.Firstname, j.Lastname, j.Judgeable)
	}
	log.Println("================================== Registered rooms")
	for _, r := range rooms {
		log.Println(r.Name, r.JudgeCapacity)
	}
	log.Println("================================== Registered events")
	eventStr := []string{}
	for _, e := range events {
		eventStr = append(eventStr, e.Id)
	}
	log.Println(strings.Join(eventStr, ", "))

	//* schedule
	c := scheduler.NewContext(
		&proto.Time{
			Start:     startTime.Unix(),
			Divisions: divisions,
		},
		&proto.Constraints{
			GroupSize:  groupSize,
			ExamLength: examLength,
		},
		&proto.Registration{
			Students: *students,
			Judges:   judges,
			Rooms:    rooms,
			Events:   events,
		},
	)

	log.Println("==================================")
	log.Printf(
		"[INFO] scheduling with %v students, %v requests, and %v judges\n",
		len(*students), len(requests), len(judges),
	)

	o := scheduler.Schedule(c, requests)

	//* write to output
	f, err = os.Create("output.csv")
	if err != nil {
		panic(err)
	}

	err = output.Sheet(f, o)
	if err != nil {
		panic(err)
	}

	err = output.Workbook("schedule.xlsx", o)
	if err != nil {
		panic(err)
	}
}
