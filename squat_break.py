"""Squat Break - 久坐蹲起提醒工具 - 主入口"""
import argparse
import os
import sys
import time

# Ensure squat-break directory is in path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Quartz import CGSessionCopyCurrentDictionary

try:
    from ui import show_break_ui
except Exception as e:
    print(f"Warning: could not import ui module: {e}")
    show_break_ui = None


def is_screen_active():
    """Check if screen is unlocked and active on macOS."""
    d = CGSessionCopyCurrentDictionary()
    if d is None:
        return False
    if d.get("CGSSessionScreenIsLocked", False):
        return False
    return True


def parse_args():
    parser = argparse.ArgumentParser(description="久坐蹲起提醒工具")
    parser.add_argument(
        "--interval",
        type=int,
        default=40,
        help="提醒间隔（分钟），默认 40",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    interval_seconds = args.interval * 60
    accumulated = 0.0
    poll_interval = 5

    print(f"Squat Break 已启动！每 {args.interval} 分钟提醒你做蹲起。")
    print("屏幕活跃时计时，锁屏时暂停。按 Ctrl+C 退出。")

    # Check camera availability at startup
    try:
        import cv2
        cam_idx = 0
        try:
            from AVFoundation import AVCaptureDevice
            devices = AVCaptureDevice.devicesWithMediaType_('vide')
            for i, d in enumerate(devices):
                if 'MacBook' in d.localizedName() or 'FaceTime' in d.localizedName():
                    cam_idx = i
                    break
        except Exception:
            pass
        cap = cv2.VideoCapture(cam_idx, cv2.CAP_AVFOUNDATION)
        if not cap.isOpened():
            print("警告：摄像头不可用，蹲起检测将无法工作。")
            print("请检查摄像头连接和权限设置。")
        else:
            cap.release()
    except Exception as e:
        print(f"警告：摄像头检查失败: {e}")

    try:
        while True:
            if is_screen_active():
                accumulated += poll_interval
                remaining = interval_seconds - accumulated
                if remaining <= 0:
                    print("\n时间到！起来做蹲起！")
                    if show_break_ui is not None:
                        show_break_ui()
                    else:
                        print("UI 模块不可用，跳过蹲起提醒。")
                    accumulated = 0.0
                    print("计时器已重置，继续工作吧！")

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nSquat Break 已停止。")
        sys.exit(0)


if __name__ == "__main__":
    main()
