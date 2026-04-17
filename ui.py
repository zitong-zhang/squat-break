"""Squat Break - 久坐蹲起提醒工具 - 全屏 UI"""
import cv2
import tkinter as tk
from PIL import Image, ImageTk

from detector import SquatDetector


def show_break_ui(target_squats=10):
    """Show fullscreen break UI. Returns when user completes squats or presses Esc."""
    result = {"completed": False}

    root = tk.Tk()
    root.title("Squat Break")
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.configure(bg="#1a1a2e")
    root.bind("<Escape>", lambda e: _on_escape(root, result))

    # Try to steal focus on macOS
    try:
        from AppKit import NSApp, NSApplication, NSApplicationActivationPolicyAccessory
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        NSApp.activateIgnoringOtherApps_(True)
    except Exception:
        pass

    # Phase 1: Reminder
    _show_reminder(root, result, target_squats)

    root.mainloop()
    return result["completed"]


def _on_escape(root, result):
    if "_cap" in result and result["_cap"] is not None:
        result["_cap"].release()
        result["_cap"] = None
    if "_detector" in result and result["_detector"] is not None:
        result["_detector"].release()
        result["_detector"] = None
    result["completed"] = False
    root.destroy()


def _show_reminder(root, result, target_squats):
    for widget in root.winfo_children():
        widget.destroy()

    root.configure(bg="#1a1a2e")

    frame = tk.Frame(root, bg="#1a1a2e")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(
        frame,
        text="起来活动一下！",
        font=("Helvetica", 48, "bold"),
        fg="#e94560",
        bg="#1a1a2e",
    ).pack(pady=20)

    tk.Label(
        frame,
        text=f"你需要完成 {target_squats} 个蹲起才能继续工作",
        font=("Helvetica", 24),
        fg="#eee",
        bg="#1a1a2e",
    ).pack(pady=10)

    tk.Label(
        frame,
        text="按 Esc 跳过（计时器会重置）",
        font=("Helvetica", 14),
        fg="#888",
        bg="#1a1a2e",
    ).pack(pady=5)

    btn = tk.Button(
        frame,
        text="开  始",
        font=("Helvetica", 28, "bold"),
        fg="white",
        bg="#e94560",
        activebackground="#c73e54",
        activeforeground="white",
        bd=0,
        padx=60,
        pady=15,
        command=lambda: _show_squat_phase(root, result, target_squats),
    )
    btn.pack(pady=40)


def _show_squat_phase(root, result, target_squats):
    for widget in root.winfo_children():
        widget.destroy()

    root.configure(bg="#0f0f1a")

    # Open camera with explicit AVFoundation backend (required on macOS)
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        error_frame = tk.Frame(root, bg="#0f0f1a")
        error_frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(
            error_frame,
            text="无法访问摄像头",
            font=("Helvetica", 36, "bold"),
            fg="#e94560",
            bg="#0f0f1a",
        ).pack(pady=10)
        tk.Label(
            error_frame,
            text="请检查：",
            font=("Helvetica", 20),
            fg="#eee",
            bg="#0f0f1a",
        ).pack(pady=5)
        tk.Label(
            error_frame,
            text="1. 系统设置 → 隐私与安全性 → 摄像头\n   开启你的终端应用的摄像头权限\n2. 重启终端后重试",
            font=("Helvetica", 18),
            fg="#aaa",
            bg="#0f0f1a",
            justify="left",
        ).pack(pady=10)
        tk.Label(
            error_frame,
            text="按 Esc 退出",
            font=("Helvetica", 14),
            fg="#555",
            bg="#0f0f1a",
        ).pack(pady=20)
        return

    detector = SquatDetector(target=target_squats, min_hold_frames=5)

    # Store references so _on_escape can release them
    result["_cap"] = cap
    result["_detector"] = detector

    # Layout: camera left, info right
    container = tk.Frame(root, bg="#0f0f1a")
    container.place(relx=0.5, rely=0.5, anchor="center")

    cam_label = tk.Label(container, bg="#0f0f1a")
    cam_label.pack(side="left", padx=30, pady=30)

    info_frame = tk.Frame(container, bg="#0f0f1a")
    info_frame.pack(side="left", padx=30, pady=30)

    count_label = tk.Label(
        info_frame,
        text=f"0 / {target_squats}",
        font=("Helvetica", 64, "bold"),
        fg="#e94560",
        bg="#0f0f1a",
    )
    count_label.pack(pady=20)

    # Progress bar
    progress_canvas = tk.Canvas(
        info_frame, width=300, height=30, bg="#222", highlightthickness=0
    )
    progress_canvas.pack(pady=10)

    status_label = tk.Label(
        info_frame,
        text="准备开始...",
        font=("Helvetica", 24),
        fg="#eee",
        bg="#0f0f1a",
    )
    status_label.pack(pady=20)

    esc_hint = tk.Label(
        info_frame,
        text="按 Esc 跳过",
        font=("Helvetica", 14),
        fg="#555",
        bg="#0f0f1a",
    )
    esc_hint.pack(pady=10)

    read_failures = [0]  # Using list for closure mutability

    def update_frame():
        if not root.winfo_exists():
            cap.release()
            detector.release()
            result["_cap"] = None
            result["_detector"] = None
            return

        ret, frame = cap.read()
        if not ret:
            read_failures[0] += 1
            if read_failures[0] > 30:
                status_label.configure(text="摄像头读取失败，请按 Esc 退出", fg="#e94560")
                cam_label.configure(text="摄像头无法读取画面", font=("Helvetica", 24), fg="#888")
                return
            root.after(100, update_frame)
            return
        read_failures[0] = 0

        frame = cv2.flip(frame, 1)  # Mirror
        frame, count, label, person_visible = detector.process_frame(frame)

        # Convert to Tkinter image
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        cam_label.imgtk = imgtk
        cam_label.configure(image=imgtk)

        count_label.configure(text=f"{count} / {target_squats}")
        status_label.configure(text=label)

        # Update progress bar
        progress_canvas.delete("all")
        bar_width = int(300 * count / target_squats)
        progress_canvas.create_rectangle(
            0, 0, bar_width, 30, fill="#e94560", outline=""
        )

        if detector.is_complete():
            status_label.configure(text="太棒了！", fg="#4ecca3")
            count_label.configure(fg="#4ecca3")
            cap.release()
            detector.release()
            result["_cap"] = None
            result["_detector"] = None
            result["completed"] = True

            def _safe_destroy():
                if root.winfo_exists():
                    root.destroy()

            root.after(2000, _safe_destroy)
            return

        root.after(100, update_frame)

    root.after(1000, update_frame)
