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
    interval_seconds = interval * 60
    accumulated = 0.0
    poll_interval = 5
    squat_sessions = 0
    start_time = time.time()
    active_seconds = 0.0

    print(f"Hi! 每 {interval} 分钟提醒你做蹲起。", flush=True)
    print("输入 end 结束。屏幕活跃时计时，锁屏时暂停。", flush=True)

    # Check camera availability at startup
    try:
        import cv2
        cam_idx = 0
        try:
            from AVFoundation import AVCaptureDevice, AVCaptureDeviceDiscoverySession
            session = AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
                ['AVCaptureDeviceTypeBuiltInWideAngleCamera'], 'vide', 0,
            )
            builtin = session.devices()
            if builtin:
                target_uid = builtin[0].uniqueID()
                all_devices = AVCaptureDevice.devicesWithMediaType_('vide')
                for i, d in enumerate(all_devices):
                    if d.uniqueID() == target_uid:
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
                active_seconds += poll_interval
                remaining = interval_seconds - accumulated
                if remaining <= 0:
                    print("\n时间到！起来做蹲起！")
                    global _ui_process
                    ui_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ui_window.py")
                    _ui_process = subprocess.Popen(
                        [sys.executable, ui_script, "10"],
                    )
                    _ui_process.wait()
                    _ui_process = None
                    squat_sessions += 1
                    accumulated = 0.0
                    print("计时器已重置，继续工作吧！")

            # Check for "end" command on stdin
            if select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline().strip().lower()
                if line == "end":
                    break

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        pass

    total_wall = time.time() - start_time
    print(f"\n工作结束！")
    print(f"总时长: {fmt_duration(total_wall)}，活跃时长: {fmt_duration(active_seconds)}")
    print(f"完成了 {squat_sessions} 次蹲起提醒。再见！", flush=True)


if __name__ == "__main__":
    main()
