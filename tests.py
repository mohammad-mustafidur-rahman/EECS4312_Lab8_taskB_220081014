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

# Covers C6, AC1
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

# Covers C1, C2, AC1
def test_cancel_registered_promotes_earliest_waitlisted_fifo():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist
    er.register("u3")  # waitlist

    # C2 Check: Verify the return string contains the promotion explanation for Mo
    msg = er.cancel("u1")  # should promote u2
    assert "Waitlisted user 'u2' has been automatically promoted" in msg

    assert er.status("u1") == UserStatus("none")
    assert er.status("u2") == UserStatus("registered")
    assert er.status("u3") == UserStatus("waitlisted", 1)

# Covers C3, AC2
def test_duplicate_register_raises_for_registered_and_waitlisted():
    er = EventRegistration(capacity=1)
    er.register("u1")
    # C3 Check: Verify Mo's explicit error message
    with pytest.raises(DuplicateRequest) as excinfo:
        er.register("u1")
    assert "already in the system" in str(excinfo.value)

    er.register("u2")  # waitlisted
    with pytest.raises(DuplicateRequest) as excinfo:
        er.register("u2")
    assert "already in the system" in str(excinfo.value)

# Covers AC6
def test_waitlisted_cancel_removes_and_updates_positions():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")  # waitlist pos1
    er.register("u3")  # waitlist pos2

    er.cancel("u2")    # remove from waitlist

    assert er.status("u2") == UserStatus("none")
    assert er.status("u3") == UserStatus("waitlisted", 1)

# Covers AC4, C4
def test_capacity_zero_all_waitlisted_and_promotion_never_happens():
    er = EventRegistration(capacity=0)
    assert er.register("u1") == UserStatus("waitlisted", 1)
    assert er.register("u2") == UserStatus("waitlisted", 2)

    assert er.status("u1") == UserStatus("waitlisted", 1)
    assert er.status("u2") == UserStatus("waitlisted", 2)

    # C4 Check: Cancellation of unknown user in capacity 0
    with pytest.raises(NotFound) as excinfo:
        er.cancel("missing")
    assert "User 'missing' not found" in str(excinfo.value)

# --- ADDITIONAL MERGED & REFINED TESTS FOR JANE AND MO ---

# Covers C6, AC2
def test_reregister_after_cancel_is_allowed_and_works():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.cancel("u1")
    s = er.register("u1")
    assert s == UserStatus("registered")

# Covers C1, C2, AC1
def test_multiple_cancellations_in_sequence_promote_fifo_each_time():
    er = EventRegistration(capacity=2)
    users = ["u1", "u2", "u3", "u4"]
    for user in users:
        er.register(user)

    msg1 = er.cancel("u1")
    assert "u3" in msg1 # Mo's explanation
    assert er.status("u3") == UserStatus("registered")

    msg2 = er.cancel("u2")
    assert "u4" in msg2 # Mo's explanation
    assert er.status("u4") == UserStatus("registered")

# Covers AC6
def test_cancel_waitlisted_does_not_trigger_promotion():
    er = EventRegistration(capacity=1)
    er.register("u1")
    er.register("u2")
    er.register("u3")

    msg = er.cancel("u2")
    assert "removed from waitlist" in msg
    assert er.status("u1") == UserStatus("registered")
    assert er.snapshot()["waitlist"] == ["u3"]

# Covers C5, AC5
def test_status_none_for_unknown_user_does_not_change_state():
    er = EventRegistration(capacity=2)
    er.register("u1")
    initial_snap = er.snapshot()
    
    # Jane's requirement: Query has no side effects
    assert er.status("ghost") == UserStatus("none")
    assert er.snapshot() == initial_snap

# Covers C6, AC2
def test_invalid_user_id_rejected_empty_string():
    er = EventRegistration(capacity=1)
    for invalid_id in ["", "   "]:
        with pytest.raises(ValueError):
            er.register(invalid_id)

# Covers C4, AC3
def test_cancel_unknown_raises_notfound_with_message():
    er = EventRegistration(capacity=1)
    # C4 Check: Explicit message for Mo
    with pytest.raises(NotFound) as excinfo:
        er.cancel("nobody")
    assert "Cancellation failed: User 'nobody' not found." in str(excinfo.value)