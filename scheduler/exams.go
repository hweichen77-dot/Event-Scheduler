package scheduler

var examByEvent = map[string]string{}

func init() {
	clusters := map[string][]string{
		"Business Administration Core":         {"PBM", "PEN", "PFN", "PHT", "PMK"},
		"Business Management + Administration": {"HRM", "BLTDM"},
		"Entrepreneurship":                     {"ENT", "ETDM"},
		"Finance":                              {"ACT", "BFS", "FTDM"},
		"Hospitality + Tourism":                {"HLM", "QSRM", "RFSM", "HTDM", "TTDM"},
		"Marketing":                            {"AAM", "ASM", "BSM", "FMS", "MCS", "RMS", "SEM", "BTDM", "MTDM", "STDM"},
		"Personal Financial Literacy":          {"PFL"},
	}
	for exam, events := range clusters {
		for _, event := range events {
			examByEvent[event] = exam
		}
	}
}

func ExamFor(eventID string) string {
	return examByEvent[eventID]
}
