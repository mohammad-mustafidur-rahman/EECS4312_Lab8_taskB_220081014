import pytest

from solution import EventRegistration, UserStatus, DuplicateRequest, NotFound


def test_register_until_capacity_then_waitlist_fifo_positions():
    er = EventRegistration(capacity=2)

    s1 = er.register("u1")
    s2 = er.register("u2")
    s3 = er.register("u3")
    s4 = er.register("u4")

    assert s1 == UserStatus("registered")
    assert s2 == UserStatus("registered")
    assert s3 == UserStatus("waitlisted", 1)
    assert s4 == UserStatus("waitlisted", 2)

    snap = er.snapshot()
    assert snap["registered"] == ["u1", "u2"]
    assert snap["waitlist"] == ["u3", "u4"]


def test_cancel_registered_promotes_earliest_waitlisted_fifo():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist
    er.register("u3")  # waitlist

    er.cancel("u1")  # should promote u2

    assert er.status("u1") == UserStatus("none")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u2"]
    assert snap["waitlist"] == ["u3"]


def test_duplicate_register_raises_for_registered_and_waitlisted():
    er = EventRegistration(capacity=1)
    er.register("u1")
    with pytest.raises(DuplicateRequest):
        er.register("u1")

    er.register("u2")  # waitlisted
    with pytest.raises(DuplicateRequest):
        er.register("u2")


def test_waitlisted_cancel_removes_and_updates_positions():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos1
    er.register("u3")  # waitlist pos2

    er.cancel("u2")    # remove from waitlist

    assert er.status("u2") == UserStatus("none")
    assert er.status("u3") == UserStatus("waitlisted", 1)

    snap = er.snapshot()
    assert snap["registered"] == ["u1"]
    assert snap["waitlist"] == ["u3"]


def test_capacity_zero_all_waitlisted_and_promotion_never_happens():
    er = EventRegistration(capacity=0)
    assert er.register("u1") == UserStatus("waitlisted", 1)
    assert er.register("u2") == UserStatus("waitlisted", 2)

    # No one can ever be registered when capacity=0
    assert er.status("u1") == UserStatus("waitlisted", 1)
    assert er.status("u2") == UserStatus("waitlisted", 2)
    assert er.snapshot()["registered"] == []

    # Cancel unknown should raise NotFound
    with pytest.raises(NotFound):
        er.cancel("missing")



#################################################################################
# Add your own additional tests here to cover more cases and edge cases as needed.
#################################################################################

def test_reregister_after_cancel_is_allowed_and_works():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.cancel("u1") 
    # Logic check: The sets must be empty for this to pass
    s = er.register("u1")
    assert s.state == "registered"
    assert er.status("u1").state == "registered"

def test_multiple_cancellations_in_sequence_promote_fifo_each_time():
    er = EventRegistration(capacity=2)
    users = ["u1", "u2", "u3", "u4"]
    for u in users: er.register(u)

    er.cancel("u1")
    # Verify u3 took the spot and u4 is now #1
    assert er.status("u3").state == "registered"
    assert er.status("u4").position == 1

    er.cancel("u2")
    # Verify u4 took the last spot and waitlist is empty
    assert er.status("u4").state == "registered"
    assert len(er.snapshot()["waitlist"]) == 0

def test_cancel_waitlisted_does_not_trigger_promotion():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")
    er.register("u3")

    # u2 is between u1 and u3. Removing u2 should just slide u3 up.
    er.cancel("u2")
    assert er.status("u1").state == "registered"
    assert er.status("u3").position == 1

def test_duplicate_after_promotion_is_rejected():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2") # waitlisted
    er.cancel("u1") # u2 promoted

    with pytest.raises(DuplicateRequest):
        er.register("u2")

def test_status_none_for_unknown_user_does_not_change_state():
    er = EventRegistration(capacity=2)
    er.register("u1")
    initial_snap = er.snapshot()
    
    assert er.status("ghost").state == "none"
    assert er.snapshot() == initial_snap

def test_invalid_user_id_rejected_empty_string():
    er = EventRegistration(capacity=1)
    # Testing both empty and whitespace strings
    for invalid_id in ["", "   "]:
        with pytest.raises(ValueError):
            er.register(invalid_id)

def test_invalid_capacity_negative_rejected():
    # Enforces Requirement C6
    with pytest.raises(ValueError):
        EventRegistration(capacity=-5)

def test_cancel_unknown_raises_notfound_if_required_by_tests():
    er = EventRegistration(capacity=1)
    with pytest.raises(NotFound):
        er.cancel("nobody")
