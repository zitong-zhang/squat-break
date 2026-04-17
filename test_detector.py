"""Tests for SquatDetector state machine."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from detector import SquatDetector

# Simulated coordinates: standing hip_y=2.05, squatting hip_y=2.50
STAND = 2.05
SQUAT = 2.50
CALIBRATION_FRAMES = 30


def _calibrated(target=3, min_hold=3):
    d = SquatDetector(target=target, min_hold_frames=min_hold)
    for _ in range(CALIBRATION_FRAMES):
        d.process(STAND)
    assert d.state == "standing", f"Expected standing, got {d.state}"
    return d


def test_calibration():
    d = SquatDetector(target=3)
    assert d.state == "calibrating"
    for i in range(CALIBRATION_FRAMES - 1):
        d.process(STAND)
        assert d.state == "calibrating"
    d.process(STAND)
    assert d.state == "standing"


def test_standing_no_count():
    d = _calibrated()
    for _ in range(20):
        d.process(STAND)
    assert d.count == 0


def test_one_squat():
    d = _calibrated(min_hold=3)
    for _ in range(5):
        d.process(SQUAT)
    assert d.state == "down"
    for _ in range(5):
        d.process(STAND)
    assert d.count == 1
    assert d.state == "standing"


def test_incomplete_squat_no_count():
    d = _calibrated(min_hold=10)
    for _ in range(3):
        d.process(SQUAT)
    for _ in range(5):
        d.process(STAND)
    assert d.count == 0


def test_three_squats_complete():
    d = _calibrated(target=3, min_hold=3)
    for _ in range(3):
        for _ in range(5):
            d.process(SQUAT)
        for _ in range(5):
            d.process(STAND)
    assert d.count == 3
    assert d.is_complete()


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
    test_one_squat()
    test_incomplete_squat_no_count()
    test_three_squats_complete()
    test_reset()
    print("All tests passed!")
