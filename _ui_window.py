"""Squat Break UI window - runs as a subprocess."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import subprocess
import tkinter as tk
from PIL import Image, ImageTk

from detector import SquatDetector


def _activate_app():
    """Register as a regular macOS app and steal focus."""
    try:
        from AppKit import NSApplication
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(0)  # Regular app - shows in dock
        app.activateIgnoringOtherApps_(True)
    except Exception:
        pass
    try:
        subprocess.run([
            'osascript', '-e',
            'display notification "起来做蹲起！" with title "Squat Break" sound name "default"'
        ], timeout=3)
    except Exception:
        pass


def main():
    target_squats = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    # Register as macOS app BEFORE creating window
    _activate_app()

    result = {"completed": False, "_done": False}

    root = tk.Tk()
    root.title("Squat Break")
    root.configure(bg="#1a1a2e")
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    root.geometry(f"{screen_w}x{screen_h}+0+0")

    root.bind("<Escape>", lambda e: _on_escape(root, result))

    _show_reminder(root, result, target_squats)

    # Force foreground
    root.update_idletasks()
    root.lift()
    root.focus_force()

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
    root.configure(bg="#1a1a2e")

    frame = tk.Frame(root, bg="#1a1a2e")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(frame, text="起来活动一下！", font=("Helvetica", 48, "bold"),
             fg="#e94560", bg="#1a1a2e").pack(pady=20)
    tk.Label(frame, text=f"你需要完成 {target_squats} 个蹲起才能继续工作",
             font=("Helvetica", 24), fg="#eee", bg="#1a1a2e").pack(pady=10)
    tk.Label(frame, text="按 Esc 跳过（计时器会重置）",
             font=("Helvetica", 14), fg="#888", bg="#1a1a2e").pack(pady=5)
    tk.Button(frame, text="开  始", font=("Helvetica", 28, "bold"),
              fg="white", bg="#e94560", activebackground="#c73e54",
              activeforeground="white", bd=0, padx=60, pady=15,
              command=lambda: _show_squat_phase(root, result, target_squats)).pack(pady=40)


def _find_macbook_camera_index():
    """Find the MacBook built-in camera index, not iPhone Continuity Camera."""
    try:
        from AVFoundation import AVCaptureDevice
        devices = AVCaptureDevice.devicesWithMediaType_('vide')
        for i, d in enumerate(devices):
            name = d.localizedName()
            if 'MacBook' in name or 'FaceTime' in name:
                return i
    except Exception:
        pass
    return 0


def _show_squat_phase(root, result, target_squats):
    for widget in root.winfo_children():
        widget.destroy()
    root.configure(bg="#0f0f1a")

    cam_idx = _find_macbook_camera_index()
    cap = cv2.VideoCapture(cam_idx, cv2.CAP_AVFOUNDATION)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        tk.Label(root, text="无法访问摄像头\n按 Esc 退出",
                 font=("Helvetica", 32), fg="#e94560", bg="#0f0f1a"
                 ).place(relx=0.5, rely=0.5, anchor="center")
        return

    detector = SquatDetector(target=target_squats, min_hold_frames=5)

    container = tk.Frame(root, bg="#0f0f1a")
    container.place(relx=0.5, rely=0.5, anchor="center")

    cam_label = tk.Label(container, bg="#0f0f1a")
    cam_label.pack(side="left", padx=30, pady=30)

    info_frame = tk.Frame(container, bg="#0f0f1a")
    info_frame.pack(side="left", padx=30, pady=30)

    count_label = tk.Label(info_frame, text=f"0 / {target_squats}",
                           font=("Helvetica", 64, "bold"), fg="#e94560", bg="#0f0f1a")
    count_label.pack(pady=20)

    progress_canvas = tk.Canvas(info_frame, width=300, height=30, bg="#222", highlightthickness=0)
    progress_canvas.pack(pady=10)

    status_label = tk.Label(info_frame, text="准备开始...", font=("Helvetica", 24),
                            fg="#eee", bg="#0f0f1a")
    status_label.pack(pady=20)

    debug_label = tk.Label(info_frame, text="", font=("Helvetica", 12),
                           fg="#555", bg="#0f0f1a")
    debug_label.pack(pady=5)

    esc_hint = tk.Label(info_frame, text="按 Esc 跳过", font=("Helvetica", 14),
                        fg="#555", bg="#0f0f1a")
    esc_hint.pack(pady=10)

    read_failures = [0]

    def update_frame():
        if result.get("_done") or not root.winfo_exists():
            return

        ret, frame = cap.read()
        if not ret:
            read_failures[0] += 1
            if read_failures[0] > 30:
                status_label.configure(text="摄像头读取失败，请按 Esc 退出", fg="#e94560")
                return
            root.after(100, update_frame)
            return
        read_failures[0] = 0

        frame = cv2.flip(frame, 1)
        frame, count, label, person_visible, angle = detector.process_frame(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        cam_label.imgtk = imgtk
        cam_label.configure(image=imgtk)

        count_label.configure(text=f"{count} / {target_squats}")
        status_label.configure(text=label)
        debug_label.configure(text=f"angle: {angle:.0f}°  state: {detector.state}")

        progress_canvas.delete("all")
        bar_width = int(300 * count / target_squats)
        progress_canvas.create_rectangle(0, 0, bar_width, 30, fill="#e94560", outline="")

        if detector.is_complete():
            result["_done"] = True
            result["completed"] = True
            status_label.configure(text="太棒了！", fg="#4ecca3")
            count_label.configure(fg="#4ecca3")
            cap.release()
            detector.release()
            root.after(2000, root.destroy)
            return

        root.after(100, update_frame)

    root.after(1000, update_frame)


if __name__ == "__main__":
    main()
