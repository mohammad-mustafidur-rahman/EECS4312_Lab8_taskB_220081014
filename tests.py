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
    # Validates: C3 (no duplicates in system at a time), C5 (consistent state)
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.cancel("u1")  # u1 removed

    # Re-register should now succeed (not a duplicate anymore)
    s = er.register("u1")
    assert s == UserStatus("registered")
    assert er.snapshot()["registered"] == ["u1"]
    assert er.snapshot()["waitlist"] == []


def test_multiple_cancellations_in_sequence_promote_fifo_each_time():
    # Validates: C1 (registered <= capacity), C2 (FIFO waitlist), C5 (consistent state)
    er = EventRegistration(capacity=2)

    er.register("u1")
    er.register("u2")
    er.register("u3")  # waitlist
    er.register("u4")  # waitlist

    # Cancel u1 -> promote u3
    er.cancel("u1")
    snap1 = er.snapshot()
    assert snap1["registered"] == ["u2", "u3"]
    assert snap1["waitlist"] == ["u4"]

    # Cancel u2 -> promote u4
    er.cancel("u2")
    snap2 = er.snapshot()
    assert snap2["registered"] == ["u3", "u4"]
    assert snap2["waitlist"] == []


def test_cancel_waitlisted_does_not_trigger_promotion():
    # Validates: C2 (FIFO), C5 (consistent state)
    er = EventRegistration(capacity=1)

    er.register("u1")  # registered
    er.register("u2")  # waitlisted
    er.register("u3")  # waitlisted

    # Cancel waitlisted user u2; should NOT change registered list
    er.cancel("u2")

    assert er.snapshot()["registered"] == ["u1"]
    assert er.snapshot()["waitlist"] == ["u3"]
    assert er.status("u3") == UserStatus("waitlisted", 1)


def test_duplicate_after_promotion_is_rejected():
    # Validates: C3 (no duplicates), C4 (not in multiple states)
    er = EventRegistration(capacity=1)

    er.register("u1")
    er.register("u2")  # waitlisted

    er.cancel("u1")    # u2 promoted to registered

    # Now u2 is registered; registering u2 again should raise DuplicateRequest
    with pytest.raises(DuplicateRequest):
        er.register("u2")

    assert er.status("u2") == UserStatus("registered")


def test_status_none_for_unknown_user_does_not_change_state():
    # Validates: C5 (state consistency)
    er = EventRegistration(capacity=2)

    er.register("u1")
    before = er.snapshot()

    assert er.status("missing") == UserStatus("none")
    after = er.snapshot()

    assert after == before  # status query must not mutate state


def test_invalid_user_id_rejected_empty_string():
    # Validates: C5 (consistent state), input validity implied by spec (non-empty user_id)
    er = EventRegistration(capacity=1)

    with pytest.raises(ValueError):
        er.register("")

    with pytest.raises(ValueError):
        er.status("   ")

    with pytest.raises(ValueError):
        er.cancel("")


def test_invalid_capacity_negative_rejected():
    # Validates: C6 (capacity must be non-negative integer)
    with pytest.raises(ValueError):
        EventRegistration(capacity=-1)


def test_cancel_unknown_raises_notfound_if_required_by_tests():
    # Validates: test expectation about NotFound + C5 (consistent behavior)
    er = EventRegistration(capacity=1)

    # No users exist; cancel should raise NotFound per your fixed tests
    with pytest.raises(NotFound):
        er.cancel("missing")
