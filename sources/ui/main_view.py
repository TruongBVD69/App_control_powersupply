from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

from controllers.app_controller import AppController


def build_main_view(root: tk.Tk, controller: AppController) -> None:
    root.geometry("760x860")
    root.minsize(760, 300)
    root.configure(bg="#f0f7ff")
    root.resizable(False, True)
    controller.refresh_version_info()

    main_container = tk.Frame(root, bg="#f0f7ff")
    main_container.pack(side="top", fill="both", expand=True, pady=0, padx=0)
    canvas = tk.Canvas(main_container, bg="#f0f7ff", highlightthickness=0)
    v_scroll = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)
    scrollable_frame = tk.Frame(canvas, bg="#f0f7ff")
    canvas_window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.pack(side="left", fill="both", expand=True)
    v_scroll.pack(side="right", fill="y")

    scrollable_frame.bind("<Configure>", lambda _: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window_id, width=e.width))

    def on_mousewheel(event: tk.Event) -> None:
        delta = int(-1 * (event.delta if sys.platform == "darwin" else event.delta / 120))
        canvas.yview_scroll(delta, "units")

    canvas.bind("<Enter>", lambda _: canvas.bind_all("<MouseWheel>", on_mousewheel))
    canvas.bind("<Leave>", lambda _: canvas.unbind_all("<MouseWheel>"))

    frame_device = tk.LabelFrame(scrollable_frame, text="Device", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
    frame_device.pack(pady=5, padx=10, fill="x")
    tk.Label(frame_device, text="🔧 Select device:", bg="#ffffff", fg="#003366", font=("Arial", 10, "bold")).pack(side="left", padx=5)
    combo_device = ttk.Combobox(frame_device, width=20, values=["GPP-3323", "Keysight"])
    combo_device.set("GPP-3323")
    combo_device.pack(side="left", padx=5)
    combo_device.bind("<<ComboboxSelected>>", controller.on_device_change)
    tk.Button(frame_device, text="💾 Save Config", bg="#ccffcc", command=controller.save_config).pack(side="left", padx=10)
    tk.Button(frame_device, text="📂 Load Config", bg="#cce6ff", command=controller.load_config).pack(side="left", padx=5)
    tk.Button(frame_device, text="🔊 Voice", bg="#cce6ff", command=controller.open_installed_voice_app).pack(side="left", padx=5)

    frame_com = tk.LabelFrame(scrollable_frame, text="COM Connection", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
    frame_com.pack(pady=5, padx=10, fill="x")
    combo_com = ttk.Combobox(frame_com, width=15)
    combo_com.pack(side="left", padx=5)
    tk.Label(frame_com, text="Baudrate:", bg="#ffffff", fg="#003366").pack(side="left", padx=5)
    combo_baud = ttk.Combobox(frame_com, width=10, values=[4800, 9600, 19200, 38400, 57600, 115200])
    combo_baud.set(115200)
    combo_baud.pack(side="left", padx=5)
    tk.Button(frame_com, text="🔄 Refresh", bg="#cce6ff", command=controller.refresh_com_list).pack(side="left", padx=5)
    tk.Button(frame_com, text="🔌 Connect", bg="#ccffcc", command=controller.connect_com).pack(side="left", padx=5)
    tk.Button(frame_com, text="❌ Disconnect", bg="#ffcccc", command=controller.disconnect_com).pack(side="left", padx=5)

    frame_current = tk.LabelFrame(scrollable_frame, text="Current Setting", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
    frame_current.pack(pady=5, padx=10, fill="x")
    tk.Label(frame_current, text="Current (A):", bg="#ffffff", fg="#003366").pack(side="left", padx=5)
    entry_current = tk.Entry(frame_current, width=10, justify="center", bg="#f0fff0")
    entry_current.pack(side="left", padx=5)
    entry_current.insert(0, "0.3")
    entry_current.bind("<Return>", controller.on_current_enter)

    frame_status = tk.LabelFrame(scrollable_frame, text="📌 Status", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=10, pady=10)
    frame_status.pack(pady=10, fill="x", padx=20)
    lbl_status = tk.Label(frame_status, text="Not connected", fg="red", bg="#ffffff", font=("Arial", 11, "bold"))
    lbl_status.grid(row=0, column=0, sticky="w", pady=3)
    lbl_output = tk.Label(frame_status, text="⚡ Output unknown", fg="blue", bg="#ffffff", font=("Arial", 12, "bold"))
    lbl_output.grid(row=1, column=0, sticky="w", pady=3)
    lbl_voltage = tk.Label(frame_status, text="⚡ Voltage: --", fg="#000000", bg="#ffffff", font=("Arial", 14, "bold"))
    lbl_voltage.grid(row=2, column=0, sticky="w", pady=3)

    frame_top = tk.Frame(scrollable_frame, bg="#f0f7ff")
    frame_top.pack(side="top", fill="x", padx=10, pady=2)
    frame_mode = tk.LabelFrame(frame_top, text="Select Mode", bg="#ffffff", fg="#003366", bd=2, relief="groove", width=300, height=150)
    frame_mode.pack_propagate(False)
    frame_mode.pack(side="left", padx=(5, 2), pady=0)
    mode_var = tk.IntVar(value=1)
    tk.Radiobutton(frame_mode, text="Mode 1: Default list", variable=mode_var, value=1, bg="#ffffff", command=controller.on_mode_change).pack(pady=5)
    tk.Radiobutton(frame_mode, text="Mode 2: Manual input", variable=mode_var, value=2, bg="#ffffff", command=controller.on_mode_change).pack(pady=5)
    tk.Radiobutton(frame_mode, text="Mode 3: Range Mode", variable=mode_var, value=3, bg="#ffffff", command=controller.on_mode_change).pack(pady=5)
    entry_custom_voltage = tk.Entry(frame_mode, bg="#f0fff0")
    entry_custom_voltage.pack(pady=3)
    entry_custom_voltage.bind("<Return>", controller.on_custom_voltage_enter)

    frame_protection = tk.LabelFrame(frame_top, text="OVP/OCP Protection", bg="#ffffff", fg="#003366", bd=2, relief="groove", width=300, height=150)
    frame_protection.pack_propagate(False)
    frame_protection.pack(side="left", padx=(2, 5))
    btn_toggle_resp = tk.Button(frame_protection, text="Read Resp: ON", bg="lightgreen", font=("Arial", 10, "bold"), command=controller.toggle_read_response)
    btn_toggle_resp.grid(row=0, column=0, padx=10, pady=3)
    tk.Label(frame_protection, text="OVP (V):", bg="#ffffff").grid(row=1, column=0, padx=5, pady=2)
    entry_ovp = tk.Entry(frame_protection, width=8, justify="center")
    entry_ovp.grid(row=1, column=1, padx=5, pady=2)
    entry_ovp.insert(0, "5.0")
    entry_ovp.bind("<Return>", controller.on_ovp_enter)
    btn_ovp_on = tk.Button(frame_protection, text="OVP ON", width=8, command=lambda: controller.set_ovp(True))
    btn_ovp_on.grid(row=1, column=2, padx=5, pady=2)
    btn_ovp_off = tk.Button(frame_protection, text="OVP OFF", width=8, command=lambda: controller.set_ovp(False))
    btn_ovp_off.grid(row=1, column=3, padx=5, pady=2)
    tk.Label(frame_protection, text="OCP (A):", bg="#ffffff").grid(row=2, column=0, padx=5, pady=2)
    entry_ocp = tk.Entry(frame_protection, width=8, justify="center")
    entry_ocp.grid(row=2, column=1, padx=5, pady=2)
    entry_ocp.insert(0, "0.3")
    entry_ocp.bind("<Return>", controller.on_ocp_enter)
    btn_ocp_on = tk.Button(frame_protection, text="OCP ON", width=8, command=lambda: controller.set_ocp(True))
    btn_ocp_on.grid(row=2, column=2, padx=5, pady=2)
    btn_ocp_off = tk.Button(frame_protection, text="OCP OFF", width=8, command=lambda: controller.set_ocp(False))
    btn_ocp_off.grid(row=2, column=3, padx=5, pady=2)

    frame_bottom = tk.Frame(scrollable_frame, bg="#f0f7ff", height=335)
    frame_bottom.pack(side="top", fill="x", padx=10, pady=2)
    frame_bottom.pack_propagate(False)
    left_holder = tk.Frame(frame_bottom, bg="#f0f7ff")
    left_holder.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    frame_numboxs = tk.LabelFrame(left_holder, text="Voltage for Mode 1", bg="#ffffff", fg="#003366", bd=2, relief="groove")
    frame_numboxs.pack(fill="both", expand=True, padx=5, pady=5)

    frame_mode3 = tk.LabelFrame(left_holder, text="Range Mode (Mode 3)", bg="#ffffff", fg="#003366", bd=2, relief="groove")
    tk.Label(frame_mode3, text="Start (V):", bg="#ffffff").grid(row=0, column=0, padx=5, pady=4, sticky="e")
    entry_range_start = tk.Entry(frame_mode3, width=10, justify="center")
    entry_range_start.grid(row=0, column=1, padx=5, pady=4)
    entry_range_start.insert(0, "1.000")
    tk.Label(frame_mode3, text="End (V):", bg="#ffffff").grid(row=1, column=0, padx=5, pady=4, sticky="e")
    entry_range_end = tk.Entry(frame_mode3, width=10, justify="center")
    entry_range_end.grid(row=1, column=1, padx=5, pady=4)
    entry_range_end.insert(0, "3.000")
    tk.Label(frame_mode3, text="Delay (ms):", bg="#ffffff").grid(row=2, column=0, padx=5, pady=4, sticky="e")
    entry_range_delay = tk.Entry(frame_mode3, width=10, justify="center")
    entry_range_delay.grid(row=2, column=1, padx=5, pady=4)
    entry_range_delay.insert(0, "200")
    tk.Label(frame_mode3, text="Step (uses current Step):", bg="#ffffff").grid(row=3, column=0, columnspan=2, padx=5, pady=(2, 6))
    resume_var = tk.BooleanVar(value=True)
    tk.Checkbutton(frame_mode3, text="Resume from current (if stopped)", variable=resume_var, bg="#ffffff", anchor="w").grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(0, 6))
    btn_range_start = tk.Button(frame_mode3, text="▶ Start Range", bg="#ccffcc", width=20, command=controller.toggle_range)
    btn_range_start.grid(row=5, column=0, columnspan=2, padx=5, pady=6)

    frame_num_boxes = tk.Frame(frame_numboxs, bg="#ffffff")
    frame_num_boxes.pack(pady=(5, 0))
    frame_auto_run = tk.Frame(frame_numboxs, bg="#ffffff")
    frame_auto_run.pack(pady=5)
    tk.Label(frame_auto_run, text="Delay (s):").grid(row=7, column=0, pady=5)
    delay_entry = tk.Entry(frame_auto_run, width=8, justify="center")
    delay_entry.insert(0, "5")
    delay_entry.grid(row=7, column=1, pady=5)
    btn_auto_run = tk.Button(frame_auto_run, text="▶ Auto Run", width=15, bg="#ffcccc", command=controller.toggle_auto_run)
    btn_auto_run.grid(row=8, column=0, columnspan=3, pady=5)
    tk.Label(frame_num_boxes, text="🔢 Number of boxes:", bg="#ffffff", fg="#003366").pack(side="left", padx=5)
    combo_num_boxes = ttk.Combobox(frame_num_boxes, width=5, values=[2, 3, 4, 5, 6, 7, 8, 9, 10, 18], state="normal")
    combo_num_boxes.set(controller.num_voltage_boxes)
    combo_num_boxes.pack(side="left", padx=5)
    combo_num_boxes.bind("<<ComboboxSelected>>", controller.on_num_boxes_change)
    combo_num_boxes.bind("<Return>", controller.on_num_boxes_change)

    frame_mode1_canvas = tk.Canvas(frame_numboxs, bg="#ffffff", highlightthickness=0)
    scroll_y = tk.Scrollbar(frame_numboxs, orient="vertical", command=frame_mode1_canvas.yview)
    scroll_x = tk.Scrollbar(frame_numboxs, orient="horizontal", command=frame_mode1_canvas.xview)
    frame_mode1_canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")
    frame_mode1_canvas.pack(side="left", fill="both", expand=True)
    frame_mode1_boxes = tk.Frame(frame_mode1_canvas, bg="#ffffff")
    frame_mode1_canvas.create_window((0, 0), window=frame_mode1_boxes, anchor="nw")
    frame_mode1_boxes.bind("<Configure>", lambda _: frame_mode1_canvas.configure(scrollregion=frame_mode1_canvas.bbox("all")))

    frame_btn = tk.LabelFrame(frame_bottom, text="Voltage Adjustment", bg="#ffffff", fg="#003366", bd=2, relief="groove", width=250, height=300)
    frame_btn.pack_propagate(False)
    frame_btn.pack(side="left", fill="y", padx=5, pady=5)
    tk.Button(frame_btn, text="⬆ Increase", width=10, bg="#cce6ff", command=controller.increase_voltage).grid(row=0, column=1, padx=5, pady=5)
    tk.Button(frame_btn, text="⬇ Decrease", width=10, bg="#cce6ff", command=controller.decrease_voltage).grid(row=2, column=1, padx=5, pady=5)
    tk.Button(frame_btn, text="◀ Step-", width=10, bg="#cce6ff", command=controller.step_prev).grid(row=1, column=0, padx=5, pady=5)
    lbl_step = tk.Label(frame_btn, text=f"Step: {controller.voltage_step}", width=12, bg="#ffffcc", relief="solid", bd=1.2, font=("Arial", 12))
    lbl_step.grid(row=1, column=1, padx=5, pady=5)
    tk.Button(frame_btn, text="▶ Step+", width=10, bg="#cce6ff", command=controller.step_next).grid(row=1, column=2, padx=5, pady=5)
    reverse_var = tk.BooleanVar(value=False)
    tk.Checkbutton(frame_btn, text="🔁 Reverse direction", variable=reverse_var).grid(row=3, column=0, columnspan=3)
    tk.Button(frame_btn, text="⏩ Next voltage", width=20, bg="#e6e6fa", command=controller.next_voltage).grid(row=4, column=0, columnspan=3, pady=5)
    tk.Button(frame_btn, text="🔄 Reset mode", width=20, bg="#e6e6fa", command=controller.reset_mode).grid(row=5, column=0, columnspan=3, pady=5)
    tk.Button(frame_btn, text="🔄 Check for update", width=20, bg="#e6ffe6", command=controller.check_update).grid(row=6, column=0, columnspan=3, pady=5)
    tk.Button(frame_btn, text="❌ Exit", width=20, bg="#ffcccc", command=controller.quit_app).grid(row=7, column=0, columnspan=3, pady=5)

    footer_frame = tk.Frame(root, bg="#f0f7ff", height=25)
    footer_frame.pack_propagate(False)
    footer_frame.pack(side="bottom", fill="x")
    tk.Label(footer_frame, text="© 2025 BuiVuDuyTruong-Embedded. All rights reserved.", bg="#f0f7ff", fg="#555555", font=("Arial", 8)).pack(side="left", padx=5)
    link_frame = tk.Frame(footer_frame, bg="#f0f7ff")
    link_frame.pack(side="right", pady=2)

    def make_icon_link(icon_path: str, url: str, size: tuple[int, int]) -> None:
        icon = controller.load_icon(icon_path, size)
        lbl = tk.Label(link_frame, image=icon, bg="#f0f7ff", cursor="hand2")
        lbl.image = icon
        lbl.pack(side="left", padx=8)
        lbl.bind("<Button-1>", lambda _: controller.open_url(url))

    make_icon_link("assets/icons8-facebook-48.png", "https://www.facebook.com/bui.truong.902266", (20, 20))
    make_icon_link("assets/icons8-linkedin-48.png", "https://www.linkedin.com/in/b%C3%B9i-tr%C6%B0%E1%BB%9Dng-embedded/", (20, 20))
    make_icon_link("assets/icons8-github-32.png", "https://github.com/TruongBVD69", (20, 20))

    lbl_version = tk.Label(footer_frame, text=f"Version: {controller.current_version}", bg="#f0f7ff", fg="#555555", font=("Arial", 8))
    lbl_version.pack(side="right", padx=5)

    controller.attach_widgets(
        combo_device=combo_device,
        combo_com=combo_com,
        combo_baud=combo_baud,
        entry_current=entry_current,
        lbl_status=lbl_status,
        lbl_output=lbl_output,
        lbl_voltage=lbl_voltage,
        mode_var=mode_var,
        entry_custom_voltage=entry_custom_voltage,
        btn_toggle_resp=btn_toggle_resp,
        entry_ovp=entry_ovp,
        btn_ovp_on=btn_ovp_on,
        btn_ovp_off=btn_ovp_off,
        entry_ocp=entry_ocp,
        btn_ocp_on=btn_ocp_on,
        btn_ocp_off=btn_ocp_off,
        frame_mode1_boxes=frame_mode1_boxes,
        frame_numboxs=frame_numboxs,
        frame_mode3=frame_mode3,
        combo_num_boxes=combo_num_boxes,
        delay_entry=delay_entry,
        btn_auto_run=btn_auto_run,
        lbl_step=lbl_step,
        reverse_var=reverse_var,
        entry_range_start=entry_range_start,
        entry_range_end=entry_range_end,
        entry_range_delay=entry_range_delay,
        resume_var=resume_var,
        btn_range_start=btn_range_start,
        lbl_version=lbl_version,
    )
    controller.update_toggle_button()
    controller.build_voltage_entries(controller.num_voltage_boxes)
    controller.refresh_com_list()
    controller.on_mode_change()

