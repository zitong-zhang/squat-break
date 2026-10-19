"""Squat Break - 久坐蹲起提醒工具 - 主入口"""
import os
import select
import signal
import subprocess
import sys
import time

# Ensure squat-break directory is in path for sibling imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Quartz import CGSessionCopyCurrentDictionary

_ui_process = None


def _cleanup(signum, frame):
    global _ui_process
    if _ui_process and _ui_process.poll() is None:
        _ui_process.terminate()
        try:
            _ui_process.wait(timeout=3)
        except Exception:
            _ui_process.kill()
    sys.exit(0)


signal.signal(signal.SIGHUP, _cleanup)
signal.signal(signal.SIGTERM, _cleanup)


def is_screen_active():
    """Check if screen is unlocked and active on macOS."""
    d = CGSessionCopyCurrentDictionary()
    if d is None:
        return False
    if d.get("CGSSessionScreenIsLocked", False):
        return False
    return True


def fmt_duration(seconds):
    h = int(seconds) // 3600
    m = (int(seconds) % 3600) // 60
    s = int(seconds) % 60
    if h > 0:
        return f"{h}小时{m}分钟{ s}秒"
    if m > 0:
        return f"{m}分钟{ s}秒"
    return f"{s}秒"


def main():
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    squat_count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    interval_seconds = interval * 60
    accumulated = 0.0
    paused = False
    poll_interval = 5
    squat_sessions = 0
    start_time = time.time()
    active_seconds = 0.0

    print(f"Hi! 每 {interval} 分钟提醒你做 {squat_count} 个蹲起。", flush=True)
    print("输入 end 结束，输入 time 查看时间，输入 pause 暂停，输入 resume 恢复。", flush=True)

    try:
        from AVFoundation import AVCaptureDeviceDiscoverySession
        session = AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
            ['AVCaptureDeviceTypeBuiltInWideAngleCamera'], 'vide', 0,
        )
        if not session.devices():
            print("警告：未检测到摄像头，蹲起检测将无法工作。")
    except Exception:
        pass

    def check_stdin():
        """Check stdin for commands. Returns True if should exit."""
        if not select.select([sys.stdin], [], [], 0)[0]:
            return False
        line = sys.stdin.readline().strip().lower()
        nonlocal paused
        if line == "end":
            return True
        elif line == "time":
            total_wall = time.time() - start_time
            remaining = max(0, interval_seconds - accumulated)
            print(f"已工作: {fmt_duration(total_wall)}（活跃 {fmt_duration(active_seconds)}），下次蹲起: {fmt_duration(remaining)}", flush=True)
        elif line == "pause":
            paused = True
            print("计时已暂停。输入 resume 恢复。", flush=True)
        elif line == "resume":
            paused = False
            print("计时已恢复。", flush=True)
        return False

    def wait_ui(process):
        """Wait for the squat UI while still accepting stdin commands.
        Returns True if the user requested exit (UI is terminated)."""
        while process.poll() is None:
            if check_stdin():
                process.terminate()
                try:
                    process.wait(timeout=3)
                except Exception:
                    process.kill()
                return True
            time.sleep(0.5)
        return False

    stop = False
    try:
        while not stop:
            if not paused and is_screen_active():
                accumulated += poll_interval
                active_seconds += poll_interval
                if accumulated >= interval_seconds:
                    print("\n时间到！起来做蹲起！")
                    global _ui_process
                    ui_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ui_window.py")
                    _ui_process = subprocess.Popen(
                        [sys.executable, ui_script, str(squat_count)],
                    )
                    if wait_ui(_ui_process):
                        stop = True
                    _ui_process = None
                    if stop:
                        break
                    squat_sessions += 1
                    accumulated = 0.0
                    print("计时器已重置，继续工作吧！")

            if check_stdin():
                break

            # Sleep in 1-second increments for responsive command input
            for _ in range(poll_interval):
                time.sleep(1)
                if check_stdin():
                    stop = True
                    break
    except KeyboardInterrupt:
        pass

    total_wall = time.time() - start_time
    print(f"\n工作结束！")
    print(f"总时长: {fmt_duration(total_wall)}，活跃时长: {fmt_duration(active_seconds)}")
    print(f"完成了 {squat_sessions} 次蹲起提醒。再见！", flush=True)


if __name__ == "__main__":
    main()
