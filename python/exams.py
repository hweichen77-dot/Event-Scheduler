EXAM_CLUSTERS = {
    "Business Administration Core": ["PBM", "PEN", "PFN", "PHT", "PMK"],
    "Business Management + Administration": ["HRM", "BLTDM"],
    "Entrepreneurship": ["ENT", "ETDM"],
    "Finance": ["ACT", "BFS", "FTDM"],
    "Hospitality + Tourism": ["HLM", "QSRM", "RFSM", "HTDM", "TTDM"],
    "Marketing": ["AAM", "ASM", "BSM", "FMS", "MCS", "RMS", "SEM", "BTDM", "MTDM", "STDM"],
    "Personal Financial Literacy": ["PFL"],
}

EXAM_BY_EVENT = {event: exam for exam, events in EXAM_CLUSTERS.items() for event in events}


def exam_for(event_id: str) -> str:
    return EXAM_BY_EVENT.get(event_id, "")
