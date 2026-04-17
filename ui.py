"""Squat Break - 久坐蹲起提醒工具 - 全屏 UI"""
import os
import subprocess
import sys

import cv2
import tkinter as tk
from PIL import Image, ImageTk

from detector import SquatDetector


def show_break_ui(target_squats=10):
    """Show break UI in a subprocess. Returns True if squats completed."""
    ui_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ui_window.py")
    result = subprocess.run(
        [sys.executable, ui_script, str(target_squats)],
        capture_output=False,
    )
    return result.returncode == 0
