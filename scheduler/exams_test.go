package scheduler

import "testing"

func TestExamFor(t *testing.T) {
	cases := map[string]string{
		"PEN":  "Business Administration Core",
		"HRM":  "Business Management + Administration",
		"TTDM": "Hospitality + Tourism",
		"SEM":  "Marketing",
		"PFL":  "Personal Financial Literacy",
		"ESB":  "",
	}
	for event, want := range cases {
		if got := ExamFor(event); got != want {
			t.Errorf("ExamFor(%q) = %q, want %q", event, got, want)
		}
	}
}
