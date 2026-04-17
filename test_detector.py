"""Tests for SquatDetector state machine."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from detector import SquatDetector

STAND = 2.05
SQUAT = 2.50
CAL = 30


def _calibrated(target=3, min_hold=3):
    d = SquatDetector(target=target, min_hold_frames=min_hold)
    for _ in range(CAL):
        d.process(STAND)
    assert d.state == "standing"
    return d


def test_calibration():
    d = SquatDetector(target=3)
    assert d.state == "calibrating"
    for _ in range(CAL):
        d.process(STAND)
    assert d.state == "standing"


def test_standing_no_count():
    d = _calibrated()
    for _ in range(20):
        d.process(STAND)
    assert d.count == 0


def test_squat_by_y_position():
    d = _calibrated(min_hold=3)
    for _ in range(5):
        d.process(SQUAT)
    assert d.state == "down"
    for _ in range(5):
        d.process(STAND)
    assert d.count == 1


def test_squat_by_disappear():
    """Hips disappearing should trigger squat."""
    d = _calibrated(min_hold=3)
    for _ in range(5):
        d.process(None)
    assert d.state == "down"
    for _ in range(5):
        d.process(STAND)
    assert d.count == 1


def test_incomplete_no_count():
    d = _calibrated(min_hold=10)
    for _ in range(3):
        d.process(SQUAT)
    for _ in range(5):
        d.process(STAND)
    assert d.count == 0


def test_three_squats():
    d = _calibrated(target=3, min_hold=3)
    for _ in range(3):
        for _ in range(5):
            d.process(SQUAT)
        for _ in range(5):
            d.process(STAND)
    assert d.count == 3
    assert d.is_complete()


def test_mixed_squats():
    """Mix of Y-position and disappearance triggers."""
    d = _calibrated(target=2, min_hold=3)
    # Squat by Y position
    for _ in range(5):
        d.process(SQUAT)
    for _ in range(5):
        d.process(STAND)
    assert d.count == 1
    # Squat by disappearing
    for _ in range(5):
        d.process(None)
    for _ in range(5):
        d.process(STAND)
    assert d.count == 2
    assert d.is_complete()


def test_none_ignored_during_calibration():
    """None values during calibration should be skipped."""
    d = SquatDetector(target=3, min_hold_frames=3)
    d.process(None)  # Should be ignored
    d.process(STAND)
    assert d.state == "calibrating"
    assert len(d._calibration) == 1


def test_reset():
    d = _calibrated(target=2, min_hold=3)
    for _ in range(2):
        for _ in range(5):
            d.process(SQUAT)
        for _ in range(5):
            d.process(STAND)
    assert d.count == 2
    d.reset()
    assert d.count == 0
    assert d.state == "standing"


if __name__ == "__main__":
    test_calibration()
    test_standing_no_count()
    test_squat_by_y_position()
    test_squat_by_disappear()
    test_incomplete_no_count()
    test_three_squats()
    test_mixed_squats()
    test_none_ignored_during_calibration()
    test_reset()
    print("All tests passed!")
