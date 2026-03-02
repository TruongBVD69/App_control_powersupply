from __future__ import annotations

import math
import os
import subprocess
import sys
import threading
import time
import webbrowser
from types import SimpleNamespace
from urllib.parse import urlparse

import requests
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox, ttk

from app_core.config_store import load_json_config, save_json_config
from app_core.logging_utils import setup_logging
from app_core.paths import build_app_paths, resource_path as core_resource_path
from app_core.range_utils import clamp_next_value, compute_step, next_index, range_reached
from app_core.serial_service import DEVICE_GPP, DEVICE_KEYSIGHT, SerialService
from app_core.update_service import fetch_latest_release, first_download_url
from app_core.versioning import is_newer_version, read_version_info


class AppController:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.ui = SimpleNamespace()

        self.current_version = "1.9.1"
        self.app_name = "PowerSupply Controller"
        self.app_info = {"AppName": self.app_name, "Version": self.current_version, "BuildTime": "Unknown"}

        self.current_voltage = 0.0
        self.index = 0
        self.voltages = [1.815, 2.479, 3.117, 3.755]

        self.step_options = [0.1, 0.01, 0.001]
        self.step_index = 1
        self.voltage_step = self.step_options[self.step_index]

        self.mode_selected = 1
        self.num_voltage_boxes = 4
        self.entry_volt_boxes: list[tk.Entry] = []
        self.auto_running = False
        self.read_response_enabled = False

        self.range_running = False
        self.range_after_id: str | None = None
        self.range_current: float | None = None
        self.range_start = 0.0
        self.range_end = 0.0
        self.range_delay_ms = 200

        self.paths = build_app_paths(self.app_name)
        self.config_dir = str(self.paths.config_dir)
        self.download_folder = str(self.paths.download_dir)

        self.logger = setup_logging(self.paths.appdata_root)
        self.serial_service = SerialService()
        self.device_type = DEVICE_GPP
        self.serial_service.set_device_type(self.device_type)

        self.default_uninstall_path = r"C:\Program Files (x86)\PowerSupply Controller\unins000.exe"
        self.default_uninstall_args = ["/VERYSILENT"]
        self.default_uninstall_timeout = 90

    def attach_widgets(self, **widgets: object) -> None:
        for name, widget in widgets.items():
            setattr(self.ui, name, widget)

    def resource_path(self, relative_path: str) -> str:
        return core_resource_path(relative_path)

    def refresh_version_info(self) -> None:
        self.app_info = read_version_info(os.path.dirname(sys.argv[0]))
        self.current_version = self.app_info["Version"]
        self.root.title(self.app_info["AppName"])
        if hasattr(self.ui, "lbl_version"):
            self.ui.lbl_version.config(text=f"Version: {self.current_version}")

    def send_cmd(self, cmd: str) -> str:
        if not self.serial_service.is_connected():
            return ""
        if self.device_type not in (DEVICE_GPP, DEVICE_KEYSIGHT):
            return "--"
        return self.serial_service.send(cmd, read_response=self.read_response_enabled)

    def toggle_read_response(self) -> None:
        self.read_response_enabled = not self.read_response_enabled
        self.update_toggle_button()

    def update_toggle_button(self) -> None:
        self.ui.btn_toggle_resp.config(
            text=f"Read Resp: {'ON' if self.read_response_enabled else 'OFF'}",
            bg="lightgreen" if self.read_response_enabled else "lightcoral",
        )

    def set_voltage(self, value: float) -> None:
        self.current_voltage = round(value, 3)
        if self.device_type in (DEVICE_GPP, DEVICE_KEYSIGHT):
            self.send_cmd(f"VOLT {self.current_voltage}")

        readv = self.send_cmd("MEAS:VOLT?") if self.read_response_enabled else "--"
        self.ui.lbl_voltage.config(
            text=f"⚡ Voltage: {self.current_voltage:.3f} V (Device return: {readv} V)"
        )

        if self.mode_selected == 1:
            for i, entry in enumerate(self.entry_volt_boxes):
                entry.config(bg="lightgreen" if i == self.index else "white")

    def output_on(self) -> None:
        if self.device_type == DEVICE_KEYSIGHT:
            self.send_cmd("INST:SEL OUT1")
        self.send_cmd("OUTP ON")
        self.ui.lbl_output.config(text="🟢 Output: ON", fg="green")

    def output_off(self) -> None:
        self.send_cmd("OUTP OFF")
        self.ui.lbl_output.config(text="🔴 Output: OFF", fg="red")

    def set_ovp(self, enable: bool) -> None:
        if not self.serial_service.is_connected():
            messagebox.showerror("Error", "Device not connected!")
            return
        val = self.ui.entry_ovp.get().strip()
        if enable:
            if not val:
                messagebox.showerror("Error", "Please enter OVP value first!")
                return
            try:
                v = float(val)
                if self.device_type == DEVICE_GPP:
                    self.send_cmd(f"OUTP1:OVP {v}")
                    self.send_cmd("OUTP1:OVP:STAT ON")
                elif self.device_type == DEVICE_KEYSIGHT:
                    self.send_cmd(f"VOLT:PROT {v}")
                    self.send_cmd("VOLT:PROT:STAT ON")
                self.ui.btn_ovp_on.config(bg="lightgreen")
                self.ui.btn_ovp_off.config(bg="SystemButtonFace")
            except ValueError:
                messagebox.showerror("Error", "Invalid OVP value!")
        else:
            if self.device_type == DEVICE_GPP:
                self.send_cmd("OUTP1:OVP:STAT OFF")
            elif self.device_type == DEVICE_KEYSIGHT:
                self.send_cmd("VOLT:PROT:STAT OFF")
            self.ui.btn_ovp_on.config(bg="SystemButtonFace")
            self.ui.btn_ovp_off.config(bg="red")

    def set_ocp(self, enable: bool) -> None:
        if not self.serial_service.is_connected():
            messagebox.showerror("Error", "Device not connected!")
            return
        val = self.ui.entry_ocp.get().strip()
        if enable:
            if not val:
                messagebox.showerror("Error", "Please enter OCP value first!")
                return
            try:
                c = float(val)
                if self.device_type == DEVICE_GPP:
                    self.send_cmd(f"OUTP1:OCP {c}")
                    self.send_cmd("OUTP1:OCP:STAT ON")
                self.ui.btn_ocp_on.config(bg="lightgreen")
                self.ui.btn_ocp_off.config(bg="SystemButtonFace")
            except ValueError:
                messagebox.showerror("Error", "Invalid OCP value!")
        else:
            if self.device_type == DEVICE_GPP:
                self.send_cmd("OUTP1:OCP:STAT OFF")
            self.ui.btn_ocp_on.config(bg="SystemButtonFace")
            self.ui.btn_ocp_off.config(bg="red")

    def get_entry_voltages(self) -> list[float]:
        result: list[float] = []
        for entry in self.entry_volt_boxes:
            try:
                result.append(float(entry.get()))
            except ValueError:
                pass
        return result

    def next_voltage(self) -> None:
        values = self.get_entry_voltages()
        if not values:
            return
        self.index = next_index(self.index, len(values), self.ui.reverse_var.get())
        self.set_voltage(values[self.index])

    def step_next(self) -> None:
        if self.step_index < len(self.step_options) - 1:
            self.step_index += 1
            self.voltage_step = self.step_options[self.step_index]
            self.ui.lbl_step.config(text=f"Step: {self.voltage_step}")
        else:
            messagebox.showinfo("Info", "Already at the smallest step.")

    def step_prev(self) -> None:
        if self.step_index > 0:
            self.step_index -= 1
            self.voltage_step = self.step_options[self.step_index]
            self.ui.lbl_step.config(text=f"Step: {self.voltage_step}")
        else:
            messagebox.showinfo("Info", "Already at the largest step.")

    def increase_voltage(self) -> None:
        new_voltage = self.current_voltage + self.voltage_step
        self.set_voltage(new_voltage)
        if self.mode_selected == 1 and 0 <= self.index < len(self.entry_volt_boxes):
            self.entry_volt_boxes[self.index].delete(0, tk.END)
            self.entry_volt_boxes[self.index].insert(0, f"{new_voltage:.3f}")

    def decrease_voltage(self) -> None:
        new_voltage = self.current_voltage - self.voltage_step
        self.set_voltage(new_voltage)
        if self.mode_selected == 1 and 0 <= self.index < len(self.entry_volt_boxes):
            self.entry_volt_boxes[self.index].delete(0, tk.END)
            self.entry_volt_boxes[self.index].insert(0, f"{new_voltage:.3f}")

    def build_voltage_entries(self, n: int) -> None:
        for widget in self.entry_volt_boxes:
            widget.destroy()
        self.entry_volt_boxes.clear()
        self.num_voltage_boxes = n

        max_per_col = 8
        for i in range(self.num_voltage_boxes):
            col = i // max_per_col
            row = i % max_per_col
            entry = tk.Entry(self.ui.frame_mode1_boxes, width=10, justify="center")
            entry.insert(0, str(self.voltages[i]) if i < len(self.voltages) else "")
            entry.grid(row=row, column=col, padx=5, pady=2)
            entry.bind("<Return>", self.on_voltage_entry_return)
            self.entry_volt_boxes.append(entry)

    def apply_mode(self) -> None:
        if self.mode_selected == 1:
            self.index = 0
            values = self.get_entry_voltages()
            if values:
                self.set_voltage(values[self.index])
            else:
                messagebox.showerror("Error", "Please enter voltages in Mode 1 boxes!")
        else:
            try:
                self.set_voltage(float(self.ui.entry_custom_voltage.get().strip()))
            except ValueError:
                messagebox.showerror("Error", "Invalid custom voltage value!")

    def auto_run(self) -> None:
        if not self.auto_running:
            return
        try:
            delay_ms = int(float(self.ui.delay_entry.get()) * 1000)
        except ValueError:
            messagebox.showwarning("Warning", "Please enter a valid delay (seconds)!")
            self.auto_running = False
            self.ui.btn_auto_run.config(text="▶ Auto Run", bg="#ffcccc")
            return
        self.next_voltage()
        self.root.after(delay_ms, self.auto_run)

    def toggle_auto_run(self) -> None:
        if not self.auto_running:
            try:
                float(self.ui.delay_entry.get())
            except ValueError:
                messagebox.showwarning("Warning", "Please enter a valid delay (seconds)!")
                return
            self.auto_running = True
            self.ui.btn_auto_run.config(text="⏹ Stop", bg="#ccffcc")
            self.auto_run()
        else:
            self.auto_running = False
            self.ui.btn_auto_run.config(text="▶ Auto Run", bg="#ffcccc")

    def save_config(self) -> None:
        file_path = filedialog.asksaveasfilename(
            initialdir=self.config_dir,
            title="Save Config As",
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )
        if not file_path:
            return
        config = {
            "num_voltage_boxes": int(self.ui.combo_num_boxes.get()),
            "voltages": self.get_entry_voltages(),
            "com_port": self.ui.combo_com.get(),
            "device": self.ui.combo_device.get(),
            "baudrate": self.ui.combo_baud.get(),
            "mode": self.ui.mode_var.get(),
            "ovp": self.ui.entry_ovp.get(),
            "ocp": self.ui.entry_ocp.get(),
            "reverse_order": self.ui.reverse_var.get(),
        }
        try:
            save_json_config(file_path, config)
            messagebox.showinfo("Info", f"Configuration saved as '{os.path.basename(file_path)}'")
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to save config:\n{ex}")

    def load_config(self) -> None:
        file_path = filedialog.askopenfilename(
            initialdir=self.config_dir,
            title="Select config file",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*")),
        )
        if not file_path:
            return
        try:
            config = load_json_config(file_path)
            self.apply_config_to_ui(config)
            messagebox.showinfo("Info", f"Configuration '{os.path.basename(file_path)}' loaded successfully.")
        except Exception as ex:
            messagebox.showerror("Error", f"Failed to load config:\n{ex}")

    def apply_config_to_ui(self, config: dict[str, object]) -> None:
        if "voltages" in config:
            self.voltages = list(config["voltages"])  # type: ignore[arg-type]
        if "num_voltage_boxes" in config:
            n = int(config["num_voltage_boxes"])  # type: ignore[arg-type]
            self.ui.combo_num_boxes.set(str(n))
            self.build_voltage_entries(n)
        if "com_port" in config:
            self.ui.combo_com.set(config["com_port"])
        if "device" in config:
            self.ui.combo_device.set(config["device"])
            self.on_device_change()
        if "baudrate" in config:
            self.ui.combo_baud.set(config["baudrate"])
        if "mode" in config:
            self.ui.mode_var.set(config["mode"])
            self.on_mode_change()
        if "ovp" in config:
            self.ui.entry_ovp.delete(0, tk.END)
            self.ui.entry_ovp.insert(0, str(config["ovp"]))
        if "ocp" in config:
            self.ui.entry_ocp.delete(0, tk.END)
            self.ui.entry_ocp.insert(0, str(config["ocp"]))
        if "reverse_order" in config:
            self.ui.reverse_var.set(bool(config["reverse_order"]))

    def reset_mode(self) -> None:
        self.output_off()
        self.output_on()
        self.apply_mode()

    def quit_app(self) -> None:
        if self.serial_service.is_connected():
            self.output_off()
            self.serial_service.disconnect()
        self.root.destroy()

    def range_stepper(self) -> None:
        if not self.range_running:
            return
        self.set_voltage(self.range_current or 0.0)
        effective_end = self.range_start if self.ui.reverse_var.get() else self.range_end
        step_val = compute_step(self.range_current or 0.0, effective_end, self.voltage_step)
        if range_reached(self.range_current or 0.0, effective_end, step_val):
            self.set_voltage(effective_end)
            self.range_running = False
            self.range_after_id = None
            self.ui.lbl_status.config(text=f"Range done ({self.range_start} → {self.range_end})", fg="green")
            self.ui.btn_range_start.config(text="▶ Start Range", bg="#ccffcc")
            return
        self.range_current = clamp_next_value(self.range_current or 0.0, step_val, effective_end)
        self.range_after_id = self.root.after(self.range_delay_ms, self.range_stepper)

    def start_range_mode(self) -> None:
        if self.range_running:
            return
        try:
            s = float(self.ui.entry_range_start.get().strip())
            e = float(self.ui.entry_range_end.get().strip())
            d = int(self.ui.entry_range_delay.get().strip())
        except Exception:
            messagebox.showerror("Error", "Please enter valid numeric values for start/end/delay.")
            return
        if d <= 0:
            messagebox.showerror("Error", "Delay must be positive (ms).")
            return
        if math.isclose(s, e, rel_tol=1e-9, abs_tol=1e-9):
            messagebox.showinfo("Info", "Start and end are equal.")
            return

        self.range_start = s
        self.range_end = e
        self.range_delay_ms = d
        effective_end = self.range_start if self.ui.reverse_var.get() else self.range_end
        effective_start = self.range_end if self.ui.reverse_var.get() else self.range_start

        in_range = False
        if self.range_current is not None:
            lo, hi = min(self.range_start, self.range_end) - 1e-9, max(self.range_start, self.range_end) + 1e-9
            in_range = lo <= self.range_current <= hi

        current_for_dir = self.range_current if self.range_current is not None else effective_start
        step_dir = self.voltage_step if effective_end >= current_for_dir else -self.voltage_step

        if self.ui.resume_var.get() and in_range and not range_reached(current_for_dir, effective_end, step_dir):
            start_from = current_for_dir
        else:
            start_from = effective_start
            self.range_current = start_from

        self.range_running = True
        self.ui.btn_range_start.config(text="⏸ Stop Range", bg="#ffcc99")
        self.ui.lbl_status.config(
            text=f"Range running: {start_from} → {effective_end}, step {self.voltage_step}",
            fg="blue",
        )
        self.range_after_id = self.root.after(0, self.range_stepper)

    def stop_range_mode(self) -> None:
        if not self.range_running:
            return
        self.range_running = False
        if self.range_after_id:
            try:
                self.root.after_cancel(self.range_after_id)
            except Exception:
                pass
        self.range_after_id = None
        self.ui.btn_range_start.config(text="▶ Start Range", bg="#ccffcc")
        self.ui.lbl_status.config(text="Range stopped", fg="red")

    def toggle_range(self) -> None:
        if self.range_running:
            self.stop_range_mode()
        else:
            self.start_range_mode()

    def refresh_com_list(self) -> None:
        ports = self.serial_service.list_ports()
        self.ui.combo_com["values"] = ports
        if ports:
            self.ui.combo_com.current(0)

    def on_device_change(self, _event: object | None = None) -> None:
        val = self.ui.combo_device.get()
        if val == "GPP-3323":
            self.device_type = DEVICE_GPP
        elif val == "Keysight":
            self.device_type = DEVICE_KEYSIGHT
        self.serial_service.set_device_type(self.device_type)
        self.logger.info("Selected device type: %s", self.device_type)

    def connect_com(self) -> None:
        port = self.ui.combo_com.get().strip()
        baud = self.ui.combo_baud.get().strip()
        if self.ui.entry_current.get().strip() == "":
            messagebox.showerror("Error", "Please enter current value first!")
            return
        try:
            curr_val = float(self.ui.entry_current.get().strip())
            baud_int = int(baud)
        except ValueError:
            messagebox.showerror("Error", "Invalid current or baudrate value!")
            return
        if not port:
            messagebox.showerror("Error", "Please select a COM port!")
            return
        try:
            self.serial_service.set_device_type(self.device_type)
            resp = self.serial_service.connect(port=port, baudrate=baud_int)
            self.ui.lbl_status.config(text=f"✅ Connected to: {resp} @ {baud_int}bps", fg="green")
            self.send_cmd("*CLS")
            self.send_cmd(f"CURR {curr_val}")
            self.output_on()
            self.apply_mode()
            self.logger.info("Connected to %s on %s @ %s", resp, port, baud_int)
        except Exception as ex:
            self.logger.exception("Failed connecting COM port %s", port)
            messagebox.showerror("Error", f"Can not open {port}\n{ex}")

    def disconnect_com(self) -> None:
        if self.serial_service.is_connected():
            try:
                self.output_off()
                self.serial_service.disconnect()
                self.ui.lbl_status.config(text="🔌Disconnected", fg="red")
            except Exception as ex:
                self.logger.exception("Failed disconnecting COM")
                messagebox.showerror("Error", f"Can not disconnect {self.ui.combo_com.get()}\n{ex}")
        else:
            self.ui.lbl_status.config(text="⚠ Not connected", fg="orange")

    def on_voltage_entry_return(self, event: tk.Event) -> None:
        if self.mode_selected == 1 and self.serial_service.is_connected() and event.widget in self.entry_volt_boxes:
            i = self.entry_volt_boxes.index(event.widget)
            try:
                self.index = i
                self.set_voltage(float(event.widget.get()))
            except ValueError:
                messagebox.showerror("Error", f"Invalid voltage at box {i + 1}!")

    def on_num_boxes_change(self, _event: object | None = None) -> None:
        try:
            self.build_voltage_entries(int(self.ui.combo_num_boxes.get()))
        except ValueError:
            pass

    def on_mode_change(self, _event: object | None = None) -> None:
        self.mode_selected = self.ui.mode_var.get()
        self.ui.frame_numboxs.pack_forget()
        self.ui.frame_mode3.pack_forget()
        if self.mode_selected == 1:
            self.ui.frame_numboxs.pack(fill="both", expand=True, padx=5, pady=5)
            self.ui.lbl_status.config(text="Mode 1: Default list", fg="black")
            self.apply_mode()
        elif self.mode_selected == 2:
            self.ui.lbl_status.config(text="Mode 2: Manual input", fg="black")
            self.apply_mode()
        elif self.mode_selected == 3:
            self.ui.frame_mode3.pack(fill="both", expand=True, padx=5, pady=5)
            self.ui.lbl_status.config(text="Mode 3: Range mode", fg="black")
        else:
            self.ui.lbl_status.config(text="Unknown mode", fg="orange")

    def on_custom_voltage_enter(self, _event: object | None = None) -> None:
        if self.mode_selected == 2 and self.serial_service.is_connected():
            try:
                self.set_voltage(float(self.ui.entry_custom_voltage.get().strip()))
            except ValueError:
                messagebox.showerror("Error", "Invalid custom voltage value!")

    def on_current_enter(self, _event: object | None = None) -> None:
        if self.serial_service.is_connected():
            try:
                self.send_cmd(f"CURR {float(self.ui.entry_current.get().strip())}")
            except ValueError:
                messagebox.showerror("Error", "Current value is invalid!")
        else:
            messagebox.showerror("Error", "Device not connected!")

    def on_ovp_enter(self, _event: object | None = None) -> None:
        if self.serial_service.is_connected():
            try:
                float(self.ui.entry_ovp.get().strip())
                self.set_ovp(True)
            except ValueError:
                messagebox.showerror("Error", "OVP value is invalid!")
        else:
            messagebox.showerror("Error", "Device not connected!")

    def on_ocp_enter(self, _event: object | None = None) -> None:
        if self.serial_service.is_connected():
            try:
                float(self.ui.entry_ocp.get().strip())
                self.set_ocp(True)
            except ValueError:
                messagebox.showerror("Error", "OCP value is invalid!")
        else:
            messagebox.showerror("Error", "Device not connected!")

    def check_update(self) -> None:
        try:
            release = fetch_latest_release(timeout=5)
            latest_version = release.tag_name
            if is_newer_version(latest_version, self.current_version):
                download_url = first_download_url(release)
                if not download_url:
                    messagebox.showinfo("New Update Available", f"No attached file found for {latest_version}.")
                    return
                if messagebox.askyesno(
                    "New Update Available",
                    f"A new version is available: {latest_version}\nYou are using: {self.current_version}\n\nDo you want to update now?",
                ):
                    self.download_and_replace(download_url, latest_version)
            else:
                messagebox.showinfo("Information", f"You are already using the latest version ({self.current_version})")
        except Exception as ex:
            messagebox.showerror("Error", f"Could not check for updates:\n{ex}")

    def download_and_replace(self, download_url: str, latest_version: str) -> None:
        def worker() -> None:
            prog_win = None
            prog_label = None
            prog_bar = None
            tmp_path = None
            try:
                filename = "".join(
                    c for c in (os.path.basename(urlparse(download_url).path) or f"update_{latest_version}.bin")
                    if c.isalnum() or c in "._-"
                )
                save_path = os.path.join(self.download_folder, filename)
                if os.path.exists(save_path):
                    base, ext = os.path.splitext(save_path)
                    save_path = f"{base}_v{latest_version}{ext}"

                def create_progress() -> None:
                    nonlocal prog_win, prog_label, prog_bar
                    prog_win = tk.Toplevel(self.root)
                    prog_win.title("Downloading update...")
                    prog_win.resizable(False, False)
                    prog_label = tk.Label(prog_win, text=f"Downloading {filename}")
                    prog_label.pack(padx=12, pady=(10, 6))
                    prog_bar = ttk.Progressbar(prog_win, length=300, mode="determinate")
                    prog_bar.pack(padx=12, pady=(0, 10))
                    prog_win.transient(self.root)
                    prog_win.grab_set()

                self.root.after(0, create_progress)
                with requests.get(download_url, stream=True, timeout=30) as resp:
                    resp.raise_for_status()
                    total = int(resp.headers.get("Content-Length", 0))
                    if total and prog_bar is not None:
                        self.root.after(0, lambda: prog_bar.config(maximum=total))
                    written = 0
                    tmp_path = save_path + ".part"
                    with open(tmp_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if not chunk:
                                continue
                            f.write(chunk)
                            written += len(chunk)
                            if prog_label is not None:
                                if total:
                                    self.root.after(0, lambda w=written: prog_label.config(text=f"Downloading {filename} — {w / total * 100:.1f}%"))
                                else:
                                    self.root.after(0, lambda w=written: prog_label.config(text=f"Downloading {filename} — {w // 1024} KB"))
                    os.replace(tmp_path, save_path)
                    tmp_path = None

                if prog_win is not None:
                    self.root.after(0, prog_win.destroy)

                ext = os.path.splitext(save_path)[1].lower()
                if ext in (".exe", ".msi"):
                    os.startfile(save_path)  # type: ignore[attr-defined]
                else:
                    os.startfile(os.path.dirname(save_path))  # type: ignore[attr-defined]

                self.root.after(0, lambda: messagebox.showinfo("Installer started", "Installer has been launched."))
            except Exception as ex:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
                self.root.after(0, lambda: messagebox.showerror("Download error", f"Could not download update:\n{ex}"))
            finally:
                try:
                    if prog_win is not None:
                        self.root.after(0, prog_win.destroy)
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def open_installed_voice_app(self) -> None:
        app_path = r"C:\Program Files (x86)\MyGPPController\voice_app.exe"
        try:
            os.startfile(app_path)  # type: ignore[attr-defined]
        except Exception:
            self.logger.exception("Cannot open voice app: %s", app_path)

    def open_url(self, url: str) -> None:
        webbrowser.open_new(url)

    def load_icon(self, path: str, size: tuple[int, int] | None = None) -> ImageTk.PhotoImage:
        abs_path = self.resource_path(path)
        try:
            img = Image.open(abs_path)
        except Exception as ex:
            self.logger.warning("Icon load failed: %s (%s)", abs_path, ex)
            img = Image.new("RGBA", (size or (20, 20)), (200, 200, 200, 0))
        if size:
            img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)

