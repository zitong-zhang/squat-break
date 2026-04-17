"""Squat Break - 久坐蹲起提醒工具 - 主入口"""
import argparse
import sys
import time

from Quartz import CGSessionCopyCurrentDictionary


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

    try:
        while True:
            if is_screen_active():
                accumulated += poll_interval
                remaining = interval_seconds - accumulated
                if remaining <= 0:
                    print("\n时间到！起来做蹲起！")
                    from ui import show_break_ui

                    show_break_ui()
                    accumulated = 0.0
                    print("计时器已重置，继续工作吧！")
            else:
                pass

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\nSquat Break 已停止。")
        sys.exit(0)


if __name__ == "__main__":
    main()
