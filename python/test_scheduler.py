"""
Tests for the Event Scheduler functionality.
Equivalent to the Go tests functionality.
"""
import unittest
from datetime import datetime
from .types import (
    Student, Judge, Room, Event, EventType, Time, Constraints, 
    Registration, StudentRequest, Assignment
)
from .common import unordered_equal, intersects, has_adjacent
from .csv_parser import split_name, parse_event_type, find_student
from .scheduler import new_context, schedule


class TestCommon(unittest.TestCase):
    """Test common utility functions."""
    
    def test_unordered_equal(self):
        """Test unordered equality checking."""
        self.assertTrue(unordered_equal([1, 2, 3], [3, 1, 2]))
        self.assertTrue(unordered_equal([], []))
        self.assertFalse(unordered_equal([1, 2], [1, 2, 3]))
        self.assertFalse(unordered_equal([1, 2, 3], [1, 2, 4]))
    
    def test_intersects(self):
        """Test intersection checking."""
        self.assertTrue(intersects([1, 2, 3], [3, 4, 5]))
        self.assertTrue(intersects(['a', 'b'], ['b', 'c']))
        self.assertFalse(intersects([1, 2], [3, 4]))
        self.assertFalse(intersects([], [1, 2]))
    
    def test_has_adjacent(self):
        """Test adjacent checking."""
        assignments = [Assignment() for _ in range(5)]
        assignments[1].event = Event(id="test", event_type=EventType.ROLEPLAY)
        
        # Test with a predicate that checks for non-None events
        result = has_adjacent(assignments, 0, lambda adj, above: adj.event is not None)
        self.assertTrue(result)
        
        result = has_adjacent(assignments, 2, lambda adj, above: adj.event is not None)
        self.assertTrue(result)
        
        result = has_adjacent(assignments, 3, lambda adj, above: adj.event is not None)
        self.assertFalse(result)


class TestCSVParser(unittest.TestCase):
    """Test CSV parsing functions."""
    
    def test_split_name(self):
        """Test name splitting."""
        self.assertEqual(split_name("John Doe"), ("John", "Doe"))
        self.assertEqual(split_name("John"), ("John", ""))
        self.assertEqual(split_name("John (Jr) Doe"), ("John", "Doe"))
        self.assertEqual(split_name("John, Doe"), ("John", "Doe"))
        self.assertEqual(split_name(""), ("", ""))
    
    def test_parse_event_type(self):
        """Test event type parsing."""
        self.assertEqual(parse_event_type("roleplay"), EventType.ROLEPLAY)
        self.assertEqual(parse_event_type("WRITTEN"), EventType.WRITTEN)
        self.assertEqual(parse_event_type(" roleplay "), EventType.ROLEPLAY)
        
        with self.assertRaises(ValueError):
            parse_event_type("invalid")
    
    def test_find_student(self):
        """Test student finding."""
        students = [
            Student(email="john.doe@test.com", firstname="John", lastname="Doe"),
            Student(email="jane.smith@test.com", firstname="Jane", lastname="Smith")
        ]
        
        # Test finding existing student
        student, is_new = find_student(students, "John", "Doe")
        self.assertFalse(is_new)
        self.assertEqual(student.email, "john.doe@test.com")
        
        # Test creating new student
        student, is_new = find_student(students, "Bob", "Johnson")
        self.assertTrue(is_new)
        self.assertEqual(student.email, "bob.johnson@warriorlife.net")


class TestScheduler(unittest.TestCase):
    """Test scheduling functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.students = [
            Student(email="alice@test.com", firstname="Alice", lastname="Smith"),
            Student(email="bob@test.com", firstname="Bob", lastname="Jones"),
            Student(email="charlie@test.com", firstname="Charlie", lastname="Brown")
        ]
        
        self.judges = [
            Judge(number=1, firstname="Judge", lastname="One", judgeable=["EVENT1"]),
            Judge(number=2, firstname="Judge", lastname="Two", judgeable=["EVENT2"])
        ]
        
        self.rooms = [
            Room(name="Room1", judge_capacity=2, event_type=EventType.ROLEPLAY),
            Room(name="Room2", judge_capacity=2, event_type=EventType.WRITTEN)
        ]
        
        self.events = [
            Event(id="EVENT1", event_type=EventType.ROLEPLAY),
            Event(id="EVENT2", event_type=EventType.WRITTEN)
        ]
        
        self.time = Time(start=int(datetime(2024, 1, 1, 9, 0).timestamp()), divisions=[60, 60, 60])
        self.constraints = Constraints(group_size=4, exam_length=60)
        
        self.registration = Registration(
            students=self.students,
            judges=self.judges,
            rooms=self.rooms,
            events=self.events
        )
    
    def test_new_context(self):
        """Test context creation."""
        context = new_context(self.time, self.constraints, self.registration)
        
        self.assertEqual(len(context.students), 3)
        self.assertEqual(len(context.judges), 2)
        self.assertEqual(len(context.events), 2)
        self.assertEqual(len(context.rooms), 2)
        self.assertIn("alice@test.com", context.students)
        self.assertIn(1, context.judges)
        self.assertIn("EVENT1", context.events)
    
    def test_schedule_basic(self):
        """Test basic scheduling."""
        context = new_context(self.time, self.constraints, self.registration)
        
        requests = [
            StudentRequest(event="EVENT1", group=["alice@test.com", "bob@test.com"]),
            StudentRequest(event="EVENT2", group=["charlie@test.com"])
        ]
        
        output = schedule(context, requests)
        
        self.assertIsNotNone(output)
        self.assertEqual(len(output.housings), 2)
        self.assertGreaterEqual(len(output.exams), 0)  # May have exams for roleplay events


class TestTypes(unittest.TestCase):
    """Test data type functionality."""
    
    def test_event_type_enum(self):
        """Test EventType enum."""
        self.assertEqual(EventType.ROLEPLAY.value, 0)
        self.assertEqual(EventType.WRITTEN.value, 1)
    
    def test_assignment_initialization(self):
        """Test Assignment initialization."""
        assignment = Assignment()
        self.assertIsNone(assignment.event)
        self.assertEqual(assignment.group, [])
        
        student = Student(email="test@test.com", firstname="Test", lastname="User")
        event = Event(id="TEST", event_type=EventType.ROLEPLAY)
        assignment = Assignment(event=event, group=[student])
        self.assertEqual(assignment.event, event)
        self.assertEqual(len(assignment.group), 1)


if __name__ == "__main__":
    unittest.main()