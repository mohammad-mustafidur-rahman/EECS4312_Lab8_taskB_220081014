## Student Name: Mohammad Mustafidur Rahman
## Student ID: 220081014

"""
Task B: Event Registration with Waitlist (Stub)
In this lab, you will design and implement an Event Registration with Waitlist system using an LLM assistant as your primary programming collaborator. 
You are asked to implement a Python module that manages registration for a single event with a fixed capacity. 
The system must:
•	Accept a fixed capacity.
•	Register users until capacity is reached.
•	Place additional users into a FIFO waitlist.
•	Automatically promote the earliest waitlisted user when a registered user cancels.
•	Prevent duplicate registrations.
•	Allow users to query their current status.

The system must ensure that:
•	The number of registered users never exceeds capacity.
•	Waitlist ordering preserves FIFO behavior.
•	Promotions occur deterministically under identical operation sequences.

The module must preserve the following invariants:
•	A user may not appear more than once in the system.
•	A user may not simultaneously exist in multiple states.
•	The system state must remain consistent after every operation.

The system must correctly handle non-trivial scenarios such as:
•	Multiple cancellations in sequence.
•	Users attempting to re-register after canceling.
•	Waitlisted users canceling before promotion.
•	Capacity equal to zero.
•	Simultaneous or rapid consecutive operations.
•	Queries during state transitions.

The output consists of the updated registration state and ordered lists of registered and waitlisted users after each operation.
"""

from dataclasses import dataclass
from typing import List, Optional


class DuplicateRequest(Exception):
    """Raised if a user tries to register but is already registered or waitlisted."""
    pass


class NotFound(Exception):
    """Raised if a user cannot be found for cancellation (if required by handout)."""
    pass


@dataclass(frozen=True)
class UserStatus:
    state: str
    position: Optional[int] = None


class EventRegistration:
    def __init__(self, capacity: int) -> None:
        if not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if capacity < 0:
            raise ValueError("capacity must be >= 0")

        self._capacity = capacity
        self._registered: List[str] = []
        self._waitlist: List[str] = []
        self._registered_set = set()
        self._waitlist_set = set()

    def register(self, user_id: str) -> UserStatus:
        self._validate_user_id(user_id)

        if user_id in self._registered_set or user_id in self._waitlist_set:
            raise DuplicateRequest(f"user '{user_id}' already exists")

        if len(self._registered) < self._capacity:
            self._registered.append(user_id)
            self._registered_set.add(user_id)
            self._assert_invariants()
            return UserStatus(state="registered")

        self._waitlist.append(user_id)
        self._waitlist_set.add(user_id)
        self._assert_invariants()
        return UserStatus(state="waitlisted", position=len(self._waitlist))

    def cancel(self, user_id: str) -> None:
        self._validate_user_id(user_id)

        if user_id in self._registered_set:
            self._registered.remove(user_id)
            self._registered_set.remove(user_id)
            self._promote_next()
        elif user_id in self._waitlist_set:
            self._waitlist.remove(user_id)
            self._waitlist_set.remove(user_id)
        else:
            raise NotFound(f"user '{user_id}' not found")

        self._assert_invariants()

    def _promote_next(self) -> None:
        """Move the first waitlisted user into registered if space is available."""
        if self._waitlist and len(self._registered) < self._capacity:
            promoted_user = self._waitlist.pop(0)
            self._waitlist_set.remove(promoted_user)
            self._registered.append(promoted_user)
            self._registered_set.add(promoted_user)

    def status(self, user_id: str) -> UserStatus:
        self._validate_user_id(user_id)

        if user_id in self._registered_set:
            return UserStatus(state="registered")

        if user_id in self._waitlist_set:
            pos = self._waitlist.index(user_id) + 1
            return UserStatus(state="waitlisted", position=pos)

        return UserStatus(state="none")

    def snapshot(self) -> dict:
        return {
            "capacity": self._capacity,
            "registered": list(self._registered),
            "waitlist": list(self._waitlist),
        }

    @staticmethod
    def _validate_user_id(user_id: str) -> None:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string")

    def _assert_invariants(self) -> None:
        assert len(self._registered) <= self._capacity
        assert self._registered_set.isdisjoint(self._waitlist_set)
        assert len(self._registered_set) == len(self._registered)
        assert len(self._waitlist_set) == len(self._waitlist)
