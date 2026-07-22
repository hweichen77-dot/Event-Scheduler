"""
Common utility functions for the Event Scheduler.
Equivalent to the Go components/common/general.go functionality.
"""
from typing import List, TypeVar, Callable, Any

T = TypeVar('T')


def unordered_equal(list1: List[T], list2: List[T]) -> bool:
    """Check if two lists contain the same elements regardless of order."""
    if len(list1) != len(list2):
        return False
    return set(list1) == set(list2)


def intersects(list1: List[T], list2: List[T]) -> bool:
    """Check if two lists have any common elements."""
    return bool(set(list1) & set(list2))


def has_adjacent(assignments: List[Any], index: int, predicate: Callable[[Any, bool], bool]) -> bool:
    """
    Check if there's an adjacent assignment that satisfies the predicate.
    
    Args:
        assignments: List of assignments
        index: Current index
        predicate: Function that takes (assignment, above) and returns bool
                  above=True means the adjacent is above current index
    """
    # Check above (index - 1)
    if index > 0:
        if predicate(assignments[index - 1], True):
            return True
    
    # Check below (index + 1)
    if index < len(assignments) - 1:
        if predicate(assignments[index + 1], False):
            return True
    
    return False


def keys(dictionary: dict) -> List[Any]:
    """Get keys from dictionary as a list."""
    return list(dictionary.keys())