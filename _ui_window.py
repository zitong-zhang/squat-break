"""Squat Break UI window - runs as a subprocess."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import subprocess
import tkinter as tk
from PIL import Image, ImageTk

from detector import SquatDetector

BG = "#0d1117"
BG_LIGHT = "#161b22"
ACCENT = "#58a6ff"
SUCCESS = "#3fb950"
DANGER = "#f85149"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
TEXT_MUTED = "#484f58"


def _activate_and_notify():
    """Send notification and steal focus using osascript."""
    try:
        subprocess.run([
            'osascript', '-e',
            'display notification "起来做蹲起！" with title "Squat Break" sound name "default"'
        ], timeout=3)
    except Exception:
        pass
    try:
        subprocess.run([
            'osascript', '-e',
            'tell application "System Events" to set frontmost of every process whose name contains "Python" to true'
        ], timeout=3)
    except Exception:
        pass


def _suppress_stderr():
    """Redirect fd 2 to /dev/null to suppress macOS AVFoundation deprecation warnings."""
    devnull = os.open(os.devnull, os.O_WRONLY)
    old = os.dup(2)
    sys.stderr.flush()
    os.dup2(devnull, 2)
    os.close(devnull)
    return old


def _restore_stderr(old_fd):
    sys.stderr.flush()
    os.dup2(old_fd, 2)
    os.close(old_fd)


def _find_built_in_camera():
    """Find the built-in camera. Returns (index, name)."""
    try:
        from AVFoundation import AVCaptureDevice, AVCaptureDeviceDiscoverySession
        session = AVCaptureDeviceDiscoverySession.discoverySessionWithDeviceTypes_mediaType_position_(
            ['AVCaptureDeviceTypeBuiltInWideAngleCamera'], 'vide', 0,
        )
        builtin = session.devices()
        if builtin:
            target_uid = builtin[0].uniqueID()
            target_name = builtin[0].localizedName()
            saved = _suppress_stderr()
            try:
                all_devices = AVCaptureDevice.devicesWithMediaType_('vide')
            finally:
                _restore_stderr(saved)
            for i, d in enumerate(all_devices):
                if d.uniqueID() == target_uid:
                    return i, target_name
            return 0, target_name
        # No built-in camera found, pick first non-iPhone/iPad device
        saved = _suppress_stderr()
        try:
            all_devices = AVCaptureDevice.devicesWithMediaType_('vide')
        finally:
            _restore_stderr(saved)
        for i, d in enumerate(all_devices):
            name = d.localizedName()
            if 'iPhone' not in name and 'iPad' not in name:
                return i, name
    except Exception:
        pass
    return 0, "unknown"


def main():
    target_squats = int(sys.argv[1]) if len(sys.argv) > 1 else 5

    result = {"completed": False, "_done": False}

    root = tk.Tk()
    root.title("Squat Break")
    root.configure(bg=BG)
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"{screen_w}x{screen_h}+0+0")

    root.bind("<Escape>", lambda e: _on_escape(root, result))
    root.after(0, _activate_and_notify)

    _show_reminder(root, result, target_squats)

    pid = os.getpid()
    def steal_focus():
        if not root.winfo_exists():
            return
        try:
            subprocess.run([
                'osascript',
                '-e', f'tell application "System Events" to set frontmost of first process whose unix id is {pid} to true',
                '-e', 'tell application "System Events" to set frontmost of every process whose name contains "Python" to true',
            ], timeout=3)
        except Exception:
            pass
        root.lift()
        root.focus_force()

    root.update_idletasks()
    steal_focus()
    for ms in [500, 2000]:
        root.after(ms, steal_focus)

    root.mainloop()

    sys.exit(0 if result["completed"] else 1)


def _on_escape(root, result):
    if result.get("_done"):
        return
    result["_done"] = True
    result["completed"] = False
    root.destroy()


def _show_reminder(root, result, target_squats):
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg=BG)

    frame = tk.Frame(root, bg=BG)
    frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(frame, text="起来活动一下！", font=("Helvetica", 48, "bold"),
             fg=ACCENT, bg=BG).pack(pady=20)
    tk.Label(frame, text=f"你需要完成 {target_squats} 个蹲起才能继续工作",
             font=("Helvetica", 24), fg=TEXT, bg=BG).pack(pady=10)
    tk.Label(frame, text="按 Esc 跳过（计时器会重置）",
             font=("Helvetica", 14), fg=TEXT_DIM, bg=BG).pack(pady=5)
    tk.Button(frame, text="开  始", font=("Helvetica", 28, "bold"),
              fg="white", bg=ACCENT, activebackground="#79c0ff",
              activeforeground="white", bd=0, padx=60, pady=15,
              command=lambda: _show_squat_phase(root, result, target_squats)).pack(pady=40)


def _show_squat_phase(root, result, target_squats):
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg=BG)

    cam_idx, cam_name = _find_built_in_camera()
    saved = _suppress_stderr()
    try:
        cap = cv2.VideoCapture(cam_idx, cv2.CAP_AVFOUNDATION)
    finally:
        _restore_stderr(saved)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        tk.Label(root, text="无法访问摄像头\n按 Esc 退出",
                 font=("Helvetica", 32), fg=DANGER, bg=BG
                 ).place(relx=0.5, rely=0.5, anchor="center")
        return

    detector = SquatDetector(target=target_squats, min_hold_frames=5)

    container = tk.Frame(root, bg=BG)
    container.place(relx=0.5, rely=0.5, anchor="center")

    cam_label = tk.Label(container, bg=BG)
    cam_label.pack(side="left", padx=30, pady=30)

    info_frame = tk.Frame(container, bg=BG)
    info_frame.pack(side="left", padx=30, pady=30)

    count_label = tk.Label(info_frame, text=f"0 / {target_squats}",
                           font=("Helvetica", 64, "bold"), fg=ACCENT, bg=BG)
    count_label.pack(pady=20)

    progress_canvas = tk.Canvas(info_frame, width=300, height=30, bg=BG_LIGHT, highlightthickness=0)
    progress_canvas.pack(pady=10)

    status_label = tk.Label(info_frame, text="准备开始...", font=("Helvetica", 24),
                            fg=TEXT, bg=BG)
    status_label.pack(pady=20)

    debug_label = tk.Label(info_frame, text="", font=("Helvetica", 12),
                           fg=TEXT_MUTED, bg=BG)
    debug_label.pack(pady=5)

    esc_hint = tk.Label(info_frame, text="按 Esc 跳过", font=("Helvetica", 14),
                        fg=TEXT_MUTED, bg=BG)
    esc_hint.pack(pady=10)

    read_failures = [0]
    prev = {"count": -1, "label": ""}

    def update_frame():
        if result.get("_done") or not root.winfo_exists():
            return

        ret, frame = cap.read()
        if not ret:
            read_failures[0] += 1
            if read_failures[0] > 30:
                status_label.configure(text="摄像头读取失败，请按 Esc 退出", fg=DANGER)
                return
            root.after(100, update_frame)
            return
        read_failures[0] = 0

        frame = cv2.flip(frame, 1)
        rgb, count, label, person_visible, hip_y = detector.process_frame(frame)

        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        cam_label.imgtk = imgtk
        cam_label.configure(image=imgtk)

        if count != prev["count"]:
            prev["count"] = count
            count_label.configure(text=f"{count} / {target_squats}")
            progress_canvas.delete("all")
            bar_width = int(300 * count / target_squats)
            color = SUCCESS if count >= target_squats else ACCENT
            progress_canvas.create_rectangle(0, 0, bar_width, 30, fill=color, outline="")

        if label != prev["label"]:
            prev["label"] = label
            status_label.configure(text=label)

        debug_label.configure(text=f"hip: {hip_y:.3f}  state: {detector.state}")

        if detector.is_complete():
            result["_done"] = True
            result["completed"] = True
            status_label.configure(text="太棒了！", fg=SUCCESS)
            count_label.configure(fg=SUCCESS)
            cap.release()
            detector.release()
            root.after(2000, root.destroy)
            return

        root.after(100, update_frame)

    root.after(1000, update_frame)


if __name__ == "__main__":
    main()
