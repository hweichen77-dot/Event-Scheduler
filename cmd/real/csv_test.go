package main

import (
	"Event-Scheduler/components/proto"
	"reflect"
	"testing"
)

func TestParseParticipationValue(t *testing.T) {
	cases := map[string]Participation{
		"ONLY Written":         OnlyWritten,
		" only  written ":      OnlyWritten,
		"ONLY Roleplay":        OnlyRoleplay,
		"Written and Roleplay": WrittenAndRoleplay,
		"":                     WrittenAndRoleplay,
	}
	for text, want := range cases {
		if got := ParseParticipationValue(text); got != want {
			t.Errorf("ParseParticipationValue(%q) = %v, want %v", text, got, want)
		}
	}
}

func TestApplyParticipation(t *testing.T) {
	events := []*proto.Event{
		{Id: "PEN", EventType: proto.EventType_ROLEPLAY},
		{Id: "STDM", EventType: proto.EventType_ROLEPLAY},
		{Id: "ESB", EventType: proto.EventType_WRITTEN},
	}
	lines := [][]string{
		{"w@x.net", "", "", "ESB", "", "", "", "", "", "", "ONLY Written"},
		{"w@x.net", "", "", "PEN", "", "", "", "", "", "", "ONLY Written"},
		{"r@x.net", "", "", "STDM", "", "", "", "", "w@x.net", "", "ONLY Roleplay"},
		{"r@x.net", "", "", "ESB", "", "", "", "", "w@x.net", "", "ONLY Roleplay"},
		{"b@x.net", "", "", "PEN", "", "", "", "", "", ""},
	}
	participation := ParseParticipation(lines)
	requests := []*proto.StudentRequest{
		{Event: "ESB", Group: []string{"w@x.net"}},
		{Event: "PEN", Group: []string{"w@x.net"}},
		{Event: "STDM", Group: []string{"r@x.net", "w@x.net"}},
		{Event: "ESB", Group: []string{"r@x.net", "w@x.net"}},
		{Event: "PEN", Group: []string{"b@x.net"}},
	}
	got := ApplyParticipation(requests, events, participation)
	want := []*proto.StudentRequest{
		{Event: "ESB", Group: []string{"w@x.net"}},
		{Event: "STDM", Group: []string{"r@x.net"}},
		{Event: "ESB", Group: []string{"w@x.net"}},
		{Event: "PEN", Group: []string{"b@x.net"}},
	}
	if len(got) != len(want) {
		t.Fatalf("got %v requests, want %v", len(got), len(want))
	}
	for i := range want {
		if got[i].Event != want[i].Event || !reflect.DeepEqual(got[i].Group, want[i].Group) {
			t.Errorf("request %v = %v %v, want %v %v", i, got[i].Event, got[i].Group, want[i].Event, want[i].Group)
		}
	}
}
