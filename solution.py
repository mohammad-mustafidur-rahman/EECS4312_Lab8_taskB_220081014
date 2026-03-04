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
    """
    state:
      - "registered"
      - "waitlisted"
      - "none"
    position: 1-based waitlist position if waitlisted; otherwise None
    """
    state: str
    position: Optional[int] = None


class EventRegistration:
    """
    Students must implement this class per the lab handout.
    Deterministic ordering is required (e.g., FIFO waitlist, predictable registration order).
    """

    def __init__(self, capacity: int) -> None:
        """
        Args:
            capacity: maximum number of registered users (>= 0)
        """
        if not isinstance(capacity, int):
            raise TypeError("capacity must be an int")
        if capacity < 0:
            raise ValueError("capacity must be >= 0")

        self._capacity: int = capacity
        self._registered: List[str] = []
        self._waitlist: List[str] = []

        # Fast membership checks for duplicate prevention / invariants.
        self._registered_set = set()
        self._waitlist_set = set()
        #raise NotImplementedError("EventRegistration.__init__ not implemented yet")

    def register(self, user_id: str) -> UserStatus:
        """
        Register a user:
          - if capacity available -> registered
          - else -> waitlisted (FIFO)

        Raises:
            DuplicateRequest if user already exists (registered or waitlisted)
        """
        self._validate_user_id(user_id)

        if user_id in self._registered_set or user_id in self._waitlist_set:
            raise DuplicateRequest(f"user '{user_id}' is already registered or waitlisted")

        if len(self._registered) < self._capacity:
            self._registered.append(user_id)
            self._registered_set.add(user_id)
            self._assert_invariants()
            return UserStatus(state="registered", position=None)

        # capacity full (including when capacity == 0)
        self._waitlist.append(user_id)
        self._waitlist_set.add(user_id)
        self._assert_invariants()
        return UserStatus(state="waitlisted", position=len(self._waitlist))

        #raise NotImplementedError("register not implemented yet")

    def cancel(self, user_id: str) -> None:
        """
        Cancel a user:
          - if registered -> remove and promote earliest waitlisted user (if any)
          - if waitlisted -> remove from waitlist
          - behavior when user not found depends on handout (raise NotFound or ignore)

        Raises:
            NotFound (if required by handout)
        """
        self._validate_user_id(user_id)

        if user_id in self._registered_set:
            self._registered_set.remove(user_id)
            self._registered.remove(user_id)

            if len(self._registered) < self._capacity and self._waitlist:
                 promoted = self._waitlist.pop(0)
                 self._waitlist_set.remove(promoted)
                 self._registered.append(promoted)
                 self._registered_set.add(promoted)

            self._assert_invariants()
            return

        if user_id in self._waitlist_set:
             self._waitlist_set.remove(user_id)
             self._waitlist.remove(user_id)
             self._assert_invariants()
             return

        # Not found -> raise
        self._assert_invariants()
        raise NotFound(f"user '{user_id}' not found")
        #raise NotImplementedError("cancel not implemented yet")

    def status(self, user_id: str) -> UserStatus:
        """
        Return status of a user:
          - registered
          - waitlisted with position (1-based)
          - none
        """
        self._validate_user_id(user_id)

        if user_id in self._registered_set:
            return UserStatus(state="registered", position=None)

        if user_id in self._waitlist_set:
            # 1-based position
            pos = self._waitlist.index(user_id) + 1
            return UserStatus(state="waitlisted", position=pos)

        return UserStatus(state="none", position=None)
        #raise NotImplementedError("status not implemented yet")

    def snapshot(self) -> dict[str, object]:
        """
        (Optional helper for debugging/tests)
        Return a deterministic snapshot of internal state.
        """
        return {
            "capacity": self._capacity,
            "registered": list(self._registered),
            "waitlist": list(self._waitlist),
        }

    @staticmethod
    def _validate_user_id(user_id: str) -> None:
        if not isinstance(user_id, str):
            raise TypeError("user_id must be a str")
        if user_id.strip() == "":
            raise ValueError("user_id must be a non-empty string")

    def _assert_invariants(self) -> None:
        # 1. Registered size <= capacity
        assert len(self._registered) <= self._capacity, "Invariant violated: registered exceeds capacity"

        # 2. No user appears in both lists
        assert self._registered_set.isdisjoint(self._waitlist_set), "Invariant violated: user in both registered and waitlist"

        # 3. Each user appears at most once overall
        assert len(self._registered_set) == len(self._registered), "Invariant violated: duplicate in registered list"
        assert len(self._waitlist_set) == len(self._waitlist), "Invariant violated: duplicate in waitlist"
        #raise NotImplementedError("snapshot not implemented yet")
