"""Tests for SquatDetector state machine."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from detector import SquatDetector


def test_initial_state():
    d = SquatDetector(target=3)
    assert d.count == 0
    assert d.state == "standing"
    assert not d.is_complete()


def test_standing_no_count():
    d = SquatDetector(target=3)
    for _ in range(20):
        d.process(0.5, 0.7)
    assert d.count == 0


def test_one_squat():
    d = SquatDetector(target=3, min_hold_frames=3)
    for _ in range(5):
        d.process(0.5, 0.7)
    for _ in range(5):
        d.process(0.68, 0.72)
    for _ in range(5):
        d.process(0.5, 0.7)
    assert d.count == 1


def test_incomplete_squat_no_count():
    d = SquatDetector(target=3, min_hold_frames=10)
    for _ in range(5):
        d.process(0.5, 0.7)
    for _ in range(3):
        d.process(0.68, 0.72)
    for _ in range(5):
        d.process(0.5, 0.7)
    assert d.count == 0


def test_three_squats_complete():
    d = SquatDetector(target=3, min_hold_frames=3)
    for _ in range(3):
        for _ in range(5):
            d.process(0.5, 0.7)
        for _ in range(5):
            d.process(0.68, 0.72)
        for _ in range(5):
            d.process(0.5, 0.7)
    assert d.count == 3
    assert d.is_complete()


def test_partial_squats_then_full():
    d = SquatDetector(target=2, min_hold_frames=3)
    for _ in range(5):
        d.process(0.5, 0.7)
    for _ in range(5):
        d.process(0.68, 0.72)
    for _ in range(5):
        d.process(0.5, 0.7)
    for _ in range(2):
        d.process(0.68, 0.72)
    for _ in range(5):
        d.process(0.5, 0.7)
    assert d.count == 1
    for _ in range(5):
        d.process(0.5, 0.7)
    for _ in range(5):
        d.process(0.68, 0.72)
    for _ in range(5):
        d.process(0.5, 0.7)
    assert d.count == 2
    assert d.is_complete()


def test_reset():
    d = SquatDetector(target=2, min_hold_frames=3)
    for _ in range(2):
        for _ in range(5):
            d.process(0.5, 0.7)
        for _ in range(5):
            d.process(0.68, 0.72)
        for _ in range(5):
            d.process(0.5, 0.7)
    assert d.count == 2
    d.reset()
    assert d.count == 0
    assert d.state == "standing"


if __name__ == "__main__":
    test_initial_state()
    test_standing_no_count()
    test_one_squat()
    test_incomplete_squat_no_count()
    test_three_squats_complete()
    test_partial_squats_then_full()
    test_reset()
    print("All tests passed!")
