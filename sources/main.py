import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time
import json
import os
import requests
import sys
import webbrowser   # 👈 để mở link tải trên trình duyệt
import getpass
import subprocess
import tempfile
from tkinter import simpledialog
from tkinter import filedialog
from PIL import Image, ImageTk
import threading
from urllib.parse import urlparse
import shutil
import math

# ======================= BIẾN TOÀN CỤC =======================
GITHUB_API_LATEST_RELEASE = "https://api.github.com/repos/TruongBVD69/App_control_powersupply/releases/latest"
CURRENT_VERSION = "1.9.1"

ser = None
current_voltage = 0.0
index = 0
is_reverse = False

voltages = [1.815, 2.479, 3.117, 3.755]

step_options = [0.1, 0.01, 0.001]
step_index = 1
voltage_step = step_options[step_index]

appdata_dir = os.getenv('APPDATA')
config_dir = os.path.join(appdata_dir, 'PowerSupply Controller', 'config')
os.makedirs(config_dir, exist_ok=True)
download_folder = os.path.join(appdata_dir, 'PowerSupply Controller', 'download')
os.makedirs(download_folder, exist_ok=True)  # tạo nếu chưa có
temp_dir = os.path.join(appdata_dir, 'PowerSupply Controller', 'temp')
os.makedirs(temp_dir, exist_ok=True)  # tạo nếu chưa có

# Đường dẫn uninstall mặc định (chỉnh theo nơi bạn cài)
DEFAULT_UNINSTALL_PATH = r"C:\Program Files (x86)\PowerSupply Controller\unins000.exe"
# Nếu uninstaller hỗ trợ silent, đặt args ở đây (tuỳ uninstaller của bạn)
DEFAULT_UNINSTALL_ARGS = ["/VERYSILENT"]   # hoặc ["/S"] tùy từng uninstaller
DEFAULT_UNINSTALL_TIMEOUT = 90  # giây

mode_selected = 1  # 1: list mặc định, 2: tự nhập

NUM_VOLTAGE_BOXES = 4
entry_volt_boxes = []

auto_running = False

device_type = "GPP"  # GPP hoặc Keysight

read_response_enabled = False  # mặc định tắt đọc phản hồi

# Range mode globals
range_running = False
range_after_id = None
range_current = None   # <-- None khi chưa khởi chạy lần nào
range_start = 0.0
range_end = 0.0
range_delay_ms = 200  # default

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)  # exe đã bundle sẵn
    else:
        # lấy thư mục gốc project (ra ngoài khỏi sources)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)

# ======================= HÀM ĐỌC VERSION TỪ FILE =======================
def get_app_info():
    try:
        base_dir = os.path.dirname(sys.argv[0])
        version_file = os.path.join(base_dir, "version.txt")
        info = {"AppName": "", "Version": "", "BuildTime": ""}
        with open(version_file, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    if key in info:
                        info[key] = value
        return info
    except Exception as e:
        print("Error đọc version.txt:", e)
        return {"AppName": "Unknown", "Version": "Unknown", "BuildTime": "Unknown"}

def refresh_version_info():
    global CURRENT_VERSION, app_info
    app_info = get_app_info()
    CURRENT_VERSION = app_info["Version"]
    root.title(f"{app_info['AppName']}")
    # Nếu bạn có label version thì cập nhật ở đây luôn
    # ví dụ: lbl_version.config(text=f"Version: {CURRENT_VERSION}")

# ======================= HÀM GỬI LỆNH =======================
def send_cmd(cmd):
    if not ser or not ser.is_open:
        return ""
    # Gửi lệnh đến thiết bị
    if device_type == "GPP":
        # GPP-3323
        ser.write((cmd + '\r\n').encode('ascii'))
    elif device_type == "Keysight":
        # Keysight
        ser.write((cmd + '\n').encode('ascii'))
    else:
        return "--"  # nếu chưa chọn loại máy
    if read_response_enabled:
        time.sleep(0.1)
        resp = ser.readline().decode(errors='ignore').strip()
        return resp
    else:
        return ""  # nếu tắt thì không đọc

def toggle_read_response():
    global read_response_enabled
    read_response_enabled = not read_response_enabled
    btn_toggle_resp.config(
        text=f"Read Resp: {'ON' if read_response_enabled else 'OFF'}",
        bg="lightgreen" if read_response_enabled else "lightcoral"
    )

def update_toggle_button():
    btn_toggle_resp.config(
        text=f"Read Resp: {'ON' if read_response_enabled else 'OFF'}",
        bg="lightgreen" if read_response_enabled else "lightcoral"
    )

def set_voltage(v):
    global current_voltage
    current_voltage = round(v, 3)

    # Gửi lệnh theo đúng loại máy
    if device_type == "GPP":
        # GPP-3323
        send_cmd(f'VOLT {current_voltage}')
    elif device_type == "Keysight":
        # Keysight
        send_cmd(f'VOLT {current_voltage}')
    else:
        readv = "--"  # nếu chưa chọn loại máy

    if read_response_enabled:  # chỉ đọc khi được bật
        readv = send_cmd('MEAS:VOLT?')
    else:
        readv = "--"

    # Cập nhật label
    lbl_voltage.config(
        text=f"⚡ Voltage: {current_voltage:.3f} V (Device return: {readv} V)"
    )

    # highlight ô entry nếu đang ở mode 1
    if mode_selected == 1:
        for i, e in enumerate(entry_volt_boxes):
            if i == index:
                e.config(bg="lightgreen")
            else:
                e.config(bg="white")

def output_on():
    if device_type == "Keysight":
        send_cmd('INST:SEL OUT1')  # Chọn OUT1 cho Keysight
    send_cmd('OUTP ON')
    lbl_output.config(text="🟢 Output: ON", fg="green")

def output_off():
    send_cmd('OUTP OFF')
    lbl_output.config(text="🔴 Output: OFF", fg="red")

def set_ovp(enable: bool):
    if not ser or not ser.is_open:
        messagebox.showerror("Error", "Device not connected!")
        return
    val = entry_ovp.get().strip()
    if enable:
        if val == "":
            messagebox.showerror("Error", "Please enter OVP value first!")
            return
        try:
            v = float(val)
            # print(f"Setting OVP to {v}V for {device_type}")
            if device_type == "GPP":
                send_cmd(f'OUTP1:OVP {v}')
                send_cmd('OUTP1:OVP:STAT ON')
            elif device_type == "Keysight":
                send_cmd(f'VOLT:PROT {v}')
                send_cmd('VOLT:PROT:STAT ON')
            # messagebox.showinfo("Thành công", f"Bật OVP = {v}V")
            btn_ovp_on.config(bg="lightgreen")
            btn_ovp_off.config(bg="SystemButtonFace")
        except:
            messagebox.showerror("Error", "Invalid OVP value!")
    else:
        # OFF
        if device_type == "GPP":
            send_cmd('OUTP1:OVP:STAT OFF')
        elif device_type == "Keysight":
            send_cmd('VOLT:PROT:STAT OFF')
        # messagebox.showinfo("Thành công", "Đã tắt OVP")
        btn_ovp_on.config(bg="SystemButtonFace")
        btn_ovp_off.config(bg="red")

def set_ocp(enable: bool):
    if not ser or not ser.is_open:
        messagebox.showerror("Error", "Device not connected!")
        return
    val = entry_ocp.get().strip()
    if enable:
        if val == "":
            messagebox.showerror("Error", "Please enter OCP value first!")
            return
        try:
            c = float(val)
            if device_type == "GPP":
                send_cmd(f'OUTP1:OCP {c}')
                send_cmd('OUTP1:OCP:STAT ON')
            # messagebox.showinfo("Thành công", f"Bật OCP = {c}A")
            btn_ocp_on.config(bg="lightgreen")
            btn_ocp_off.config(bg="SystemButtonFace")
        except:
            messagebox.showerror("Error", "Invalid OCP value!")
    else:
        # OFF
        if device_type == "GPP":
            send_cmd('OUTP1:OCP:STAT OFF')
        # messagebox.showinfo("Thành công", "Đã tắt OCP")
        btn_ocp_on.config(bg="SystemButtonFace")
        btn_ocp_off.config(bg="red")


def next_voltage():
    global index
    list_volt = get_entry_voltages()
    if not list_volt:
        return

    # Cập nhật hướng từ checkbox
    is_reverse = reverse_var.get()

    if is_reverse:
        index = (index - 1) % len(list_volt)
    else:
        index = (index + 1) % len(list_volt)

    set_voltage(list_volt[index])

def step_next():
    global step_index, voltage_step
    if step_index < len(step_options) - 1:
        step_index += 1
        voltage_step = step_options[step_index]
        lbl_step.config(text=f"Bước: {voltage_step}")
    else:
        messagebox.showinfo("Info", "Already at the smallest step.")

def step_prev():
    global step_index, voltage_step
    if step_index > 0:
        step_index -= 1
        voltage_step = step_options[step_index]
        lbl_step.config(text=f"Bước: {voltage_step}")
    else:
        messagebox.showinfo("Info", "Already at the largest step.")

def increase_voltage():
    global current_voltage
    new_voltage = current_voltage + voltage_step
    set_voltage(new_voltage)
    
    # cập nhật vào ô đang highlight
    if mode_selected == 1 and 0 <= index < len(entry_volt_boxes):
        entry_volt_boxes[index].delete(0, tk.END)
        entry_volt_boxes[index].insert(0, f"{new_voltage:.3f}")

def decrease_voltage():
    global current_voltage
    new_voltage = current_voltage - voltage_step
    set_voltage(new_voltage)
    
    # cập nhật vào ô đang highlight
    if mode_selected == 1 and 0 <= index < len(entry_volt_boxes):
        entry_volt_boxes[index].delete(0, tk.END)
        entry_volt_boxes[index].insert(0, f"{new_voltage:.3f}")

def choose_mode_1():
    global mode_selected
    mode_selected = 1
    # highlight_mode()
    apply_mode()

def choose_mode_2():
    global mode_selected
    mode_selected = 2
    # highlight_mode()
    apply_mode()

def build_voltage_entries(n):
    global entry_volt_boxes, NUM_VOLTAGE_BOXES
    for w in entry_volt_boxes:
        w.destroy()
    entry_volt_boxes.clear()
    NUM_VOLTAGE_BOXES = n

    max_per_col = 8  # số ô tối đa mỗi cột
    for i in range(NUM_VOLTAGE_BOXES):
        col = i // max_per_col      # cột hiện tại
        row = i % max_per_col       # hàng trong cột

        e = tk.Entry(frame_mode1_boxes, width=10, justify="center")
        if i < len(voltages):
            e.insert(0, str(voltages[i]))
        else:
            e.insert(0, "")

        e.grid(row=row, column=col, padx=5, pady=2)  # dùng grid thay cho pack
        e.bind("<Return>", on_voltage_entry_return)  # bắt sự kiện Enter
        entry_volt_boxes.append(e)

    # Cập nhật GUI
    root.update()

def get_entry_voltages():
    lst = []
    for e in entry_volt_boxes:
        try:
            val = float(e.get())
            lst.append(val)
        except:
            pass
    return lst

def apply_mode():
    global current_voltage, index
    if mode_selected == 1:
        index = 0
        lst = get_entry_voltages()
        if lst:
            set_voltage(lst[index])
        else:
            messagebox.showerror("Error", "Please enter voltages in Mode 1 boxes!")
    else:
        try:
            val = float(entry_custom_voltage.get().strip())
            set_voltage(val)
        except:
            messagebox.showerror("Error", "Invalid custom voltage value!")

def auto_run():
    global auto_running
    if not auto_running:
        return  # Dừng thì thoát

    try:
        delay_sec = float(delay_entry.get()) or 5.0  # Lấy từ ô nhập, mặc định 5s nếu trống
        delay_ms = int(delay_entry.get())
        delay_ms = int(delay_sec * 1000)      # Chuyển sang ms
    except ValueError:
        messagebox.showwarning("Cảnh báo", "Vui lòng nhập thời gian delay (ms) hợp lệ!")
        auto_running = False
        btn_auto_run.config(text="▶ Auto Run", bg="#ffcccc")  # Màu đỏ khi dừng
        return

    next_voltage()  # Gọi hàm có sẵn
    root.after(delay_ms, auto_run)  # Lặp lại

def toggle_auto_run():
    global auto_running
    if not auto_running:
        try:
            delay_sec = float(delay_entry.get())
        except ValueError:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập thời gian delay (giây) hợp lệ!")
            return
        auto_running = True
        btn_auto_run.config(text="⏹ Stop", bg="#ccffcc")  # Màu xanh khi chạy
        auto_run()
    else:
        auto_running = False
        btn_auto_run.config(text="▶ Auto Run", bg="#ffcccc")  # Màu đỏ khi dừng

def save_config():
    # Mở cửa sổ chọn nơi lưu file + đặt tên
    file_path = filedialog.asksaveasfilename(
        initialdir=config_dir,
        title="Save Config As",
        defaultextension=".json",
        filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
    )
    if not file_path:
        return  # Người dùng hủy

    config = {
        "num_voltage_boxes": int(combo_num_boxes.get()),
        "voltages": get_entry_voltages(),
        "com_port": combo_com.get(),
        "device": combo_device.get(),
        "baudrate": combo_baud.get(),
        "mode": mode_var.get(),
        "ovp": entry_ovp.get(),
        "ocp": entry_ocp.get(),
        "reverse_order": reverse_var.get() if 'reverse_var' in globals() else False
    }

    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=4)
        messagebox.showinfo("Info", f"Configuration saved as '{os.path.basename(file_path)}'")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save config:\n{e}")

def load_config():
    file_path = filedialog.askopenfilename(
        initialdir=config_dir,
        title="Select config file",
        filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
    )
    if not file_path:
        return

    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        apply_config_to_ui(config)
        messagebox.showinfo("Info", f"Configuration '{os.path.basename(file_path)}' loaded successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load config:\n{e}")

def apply_config_to_ui(config):
    global voltages
    if "voltages" in config:
        voltages = config["voltages"]

    if "num_voltage_boxes" in config:
        try:
            n = int(config["num_voltage_boxes"])
            combo_num_boxes.set(str(n))
            build_voltage_entries(n)  # build lúc này sẽ lấy giá trị từ voltages mới
        except Exception:
            pass

    if "com_port" in config:
        combo_com.set(config["com_port"])

    if "device" in config:
        combo_device.set(config["device"])
        on_device_change(None)  # Gọi thủ công hàm xử lý khi device thay đổi

    if "baudrate" in config:
        combo_baud.set(config["baudrate"])

    if "mode" in config:
        mode_var.set(config["mode"])
        on_mode_change()

    if "ovp" in config:
        entry_ovp.delete(0, tk.END)
        entry_ovp.insert(0, config["ovp"])

    if "ocp" in config:
        entry_ocp.delete(0, tk.END)
        entry_ocp.insert(0, config["ocp"])

    if "reverse_order" in config and 'reverse_var' in globals():
        reverse_var.set(config["reverse_order"])


def on_load_config():
    config = load_config()
    apply_config_to_ui(config)
    messagebox.showinfo("Info", "Configuration loaded successfully.")

def reset_mode():
    output_off()
    output_on()
    apply_mode()

def quit_app():
    if ser and ser.is_open:
        output_off()
        ser.close()
    root.destroy()

# ======================= Hàm thực thi cho range mode =======================
def _range_reached(a, b, step):
    """Trả True nếu a đã tiến đến (hoặc vượt) b theo hướng step (cân nhắc làm tròn)."""
    if step > 0:
        return a >= b - 1e-9
    else:
        return a <= b + 1e-9

def range_stepper():
    """Hàm nội bộ chạy 1 bước, sau đó schedule bước tiếp theo bằng root.after."""
    global range_running, range_after_id, range_current, range_end, range_delay_ms, voltage_step, range_start

    if not range_running:
        return

    # Gửi điện áp hiện tại
    set_voltage(range_current)

    # Xác định điểm đích thực tế và hướng step tùy reverse_var
    if reverse_var.get():
        effective_end = range_start      # chạy ngược: đích là start
    else:
        effective_end = range_end        # bình thường: đích là end

    # Tính bước actual (+ hoặc -)
    if effective_end < range_current:
        step_val = -abs(voltage_step)
    else:
        step_val = abs(voltage_step)

    # Nếu user bật reverse_var, hướng đã được tính bằng effective_end so với range_current,
    # nên không cần đảo thêm ở đây.

    # Kiểm tra đã đạt end chưa
    if _range_reached(range_current, effective_end, step_val):
        # đặt đúng end cuối cùng (effective_end)
        set_voltage(effective_end)
        range_running = False
        range_after_id = None
        lbl_status.config(text=f"Range done ({range_start} → {range_end})", fg="green")
        btn_range_start.config(text="▶ Start Range", bg="#ccffcc")
        return

    # Tính giá trị tiếp theo
    next_v = range_current + step_val

    # Prevent overshoot: nếu next vượt quá effective_end theo chiều step thì gán effective_end
    if (step_val > 0 and next_v > effective_end) or (step_val < 0 and next_v < effective_end):
        next_v = effective_end

    range_current = round(next_v, 6)  # giữ chút precision
    # schedule next
    range_after_id = root.after(range_delay_ms, range_stepper)


def start_range_mode():
    """Bắt đầu chạy range mode (tôn trọng resume_var và reverse_var)."""
    global range_running, range_current, range_start, range_end, range_delay_ms, range_after_id

    if range_running:
        return

    # Lấy input từ entry_range_start/entry_range_end/entry_range_delay
    try:
        s = float(entry_range_start.get().strip())
        e = float(entry_range_end.get().strip())
        d = int(entry_range_delay.get().strip())  # ms
    except Exception:
        messagebox.showerror("Error", "Please enter valid numeric values for start, end and delay (ms).")
        return

    if d <= 0:
        messagebox.showerror("Error", "Delay must be positive (ms).")
        return

    if math.isclose(s, e, rel_tol=1e-9, abs_tol=1e-9):
        messagebox.showinfo("Info", "Start and end are equal — nothing to run.")
        return

    # Cập nhật tham số range (nhưng KHÔNG ép range_current về start ở đây)
    range_start = s
    range_end = e
    range_delay_ms = d

    # Xác định effective_end và effective_start_point theo reverse_var
    if reverse_var.get():
        effective_end = range_start
        effective_start_point = range_end   # nếu không resume thì bắt đầu từ range_end
    else:
        effective_end = range_end
        effective_start_point = range_start # nếu không resume thì bắt đầu từ range_start

    # Kiểm tra range_current hợp lệ (nằm trong khoảng min..max của [range_start, range_end])
    eps = 1e-9
    in_range = False
    if range_current is not None:
        lo, hi = min(range_start, range_end) - eps, max(range_start, range_end) + eps
        if lo <= range_current <= hi:
            in_range = True

    # Tính step_dir dùng để kiểm tra đã tới đích chưa
    step_dir = voltage_step if effective_end >= (range_current if range_current is not None else effective_start_point) else -voltage_step

    if resume_var.get() and in_range and not _range_reached(range_current, effective_end, step_dir):
        # resume từ range_current (không thay đổi range_current)
        start_from = range_current
    else:
        # start lại từ effective_start_point (phụ thuộc reverse)
        start_from = effective_start_point
        range_current = start_from

    range_running = True
    btn_range_start.config(text="⏸ Stop Range", bg="#ffcc99")
    lbl_status.config(text=f"Range running: {start_from} → {effective_end}, step {voltage_step}", fg="blue")

    # call first step immediately
    range_after_id = root.after(0, range_stepper)


def stop_range_mode():
    """Dừng range mode nếu đang chạy."""
    global range_running, range_after_id
    if not range_running:
        return
    range_running = False
    if range_after_id:
        try:
            root.after_cancel(range_after_id)
        except Exception:
            pass
    range_after_id = None
    btn_range_start.config(text="▶ Start Range", bg="#ccffcc")
    lbl_status.config(text="Range stopped", fg="red")

# toggle handler for the button created earlier
def toggle_range():
    if range_running:
        stop_range_mode()
    else:
        start_range_mode()

# ======================= KẾT NỐI COM =======================
def refresh_com_list():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    combo_com['values'] = ports
    if ports:
        combo_com.current(0)

# def save_config(port):
#     with open(CONFIG_FILE, 'w') as f:
#         json.dump({"com_port": port}, f)

# def load_config():
#     if os.path.exists(CONFIG_FILE):
#         try:
#             with open(CONFIG_FILE, 'r') as f:
#                 return json.load(f)
#         except:
#             return {}
#     return {}

def on_device_change(event=None):
    global device_type
    val = combo_device.get()
    if val == "GPP-3323":
        device_type = "GPP"
    elif val == "Keysight":
        device_type = "Keysight"
    # debug in ra để kiểm tra
    print("Thiết bị đang chọn:", device_type)

def connect_com():
    global ser, device_type
    port = combo_com.get().strip()
    baud = combo_baud.get().strip()

    # 🔹 Kiểm tra dòng điện trước
    if entry_current.get().strip() == "":
        messagebox.showerror("Error", "Please enter current value first!")
        return

    # Chuyển giá trị dòng điện sang float
    try:
        curr_val = float(entry_current.get().strip())
    except ValueError:
        messagebox.showerror("Error", "Invalid current value!")
        return

    if not port:
        messagebox.showerror("Error", "Please select a COM port!")
        return
    try:
        baud = int(baud)
    except:
        messagebox.showerror("Error", "Invalid baudrate value!")
        return
    try:
        s = serial.Serial(port=port, baudrate=baud, bytesize=8, parity='N', stopbits=1, timeout=1)
        # test nhận dạng
        s.write(b'*IDN?\r\n')
        time.sleep(0.05)
        resp = s.readline().decode(errors='ignore').strip()
        # kiểm tra xem chuỗi trả về có hợp với loại máy không
        if device_type == "GPP" and "GW Instek" not in resp:
            s.close()
            messagebox.showerror("Error", f"Invalid device.\nResponse: {resp}")
            return
        if device_type == "Keysight" and "E3646A" not in resp and "Agilent" not in resp:
            s.close()
            messagebox.showerror("Error", f"Invalid device.\nResponse: {resp}")
            return

        ser = s
        lbl_status.config(text=f"✅ Connected to: {resp} @ {baud}bps", fg="green")

        send_cmd('*CLS')

        # ✅ Gửi dòng điện ngay khi kết nối
        send_cmd(f'CURR {curr_val}')

        output_on()
        apply_mode()
    except Exception as e:
        messagebox.showerror("Error", f"Can not open {port}\n{e}")

def disconnect_com():
    global ser
    if ser and ser.is_open:
        try:
            output_off()  # tắt output trước khi ngắt (nếu muốn)
            ser.close()
            ser = None
            lbl_status.config(text="🔌Disconnected", fg="red")
        except Exception as e:
            messagebox.showerror("Error", f"Can not disconnect {combo_com.get()}\n{e}")
    else:
        lbl_status.config(text="⚠ Not connected", fg="orange")

# --- Xử lý sự kiện khi nhấn Enter trong ô nhập điện áp ---
def on_voltage_entry_return(event):
    global index
    widget = event.widget
    # chỉ xử lý khi đang ở mode 1 và đã kết nối
    if mode_selected == 1 and ser and ser.is_open:
        if widget in entry_volt_boxes:
            i = entry_volt_boxes.index(widget)  # xác định ô nào được Enter
            try:
                val = float(widget.get())
                index = i  # cập nhật index
                set_voltage(val)
            except:
                messagebox.showerror("Error", f"Invalid voltage at box {i+1}!")

def on_num_boxes_change(event=None):
    try:
        n = int(combo_num_boxes.get())
        build_voltage_entries(n)
    except:
        pass

def on_mode_change(event=None):
    global mode_selected
    mode_selected = mode_var.get()

    # ẩn cả 2 trước
    try: frame_numboxs.pack_forget()
    except: pass
    try: frame_mode3.pack_forget()
    except: pass

    if mode_selected == 1:
        frame_numboxs.pack(fill="both", expand=True, padx=5, pady=5)
        lbl_status.config(text="Mode 1: Default list", fg="black")
        apply_mode()
    elif mode_selected == 2:
        # không show left-holder nội dung (manual input)
        lbl_status.config(text="Mode 2: Manual input", fg="black")
        apply_mode()
    elif mode_selected == 3:
        frame_mode3.pack(fill="both", expand=True, padx=5, pady=5)
        lbl_status.config(text="Mode 3: Range mode", fg="black")
    else:
        lbl_status.config(text="Unknown mode", fg="orange")

def on_custom_voltage_enter(event=None):
    if mode_selected == 2 and ser and ser.is_open:
        try:
            val = float(entry_custom_voltage.get().strip())
            set_voltage(val)
        except:
            messagebox.showerror("Error", "Invalid custom voltage value!")
            
def on_current_enter(event=None):
    if ser and ser.is_open:
        try:
            val_cur = float(entry_current.get().strip())
            send_cmd(f'CURR {val_cur}')
            # messagebox.showinfo("Thông báo", f"Đã đặt dòng điện: {curr_val} A")
        except ValueError:
            messagebox.showerror("Error", "Current value is invalid!")
    else:
        messagebox.showerror("Error", "Device not connected!")

def on_ovp_enter(event=None):
    if ser and ser.is_open:
        try:
            val_ovp = float(entry_ovp.get().strip())
            set_ovp(True)  # bật OVP với giá trị đã nhập
        except ValueError:
            messagebox.showerror("Error", "OVP value is invalid!")
    else:
        messagebox.showerror("Error", "Device not connected!")

def on_ocp_enter(event=None):
    if ser and ser.is_open:
        try:
            val_ocp = float(entry_ocp.get().strip())
            set_ocp(True)  # bật OCP với giá trị đã nhập
        except ValueError:
            messagebox.showerror("Error", "OCP value is invalid!")
    else:
        messagebox.showerror("Error", "Device not connected!")

# ==== CHECK UPDATE ====
def parse_version(v):
    return tuple(int(x) for x in v.strip().lstrip("v").split('.') if x.isdigit())

def is_newer_version(latest, current):
    return parse_version(latest) > parse_version(current)

def check_update():
    try:
        resp = requests.get(GITHUB_API_LATEST_RELEASE, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            latest_version = data['tag_name']
            if is_newer_version(latest_version, CURRENT_VERSION):
                assets = data.get('assets', [])
                if assets:
                    download_url = assets[0]['browser_download_url']
                    answer = messagebox.askyesno(
                        "New Update Available",
                        f"A new version is available: {latest_version}\n"
                        f"You are using: {CURRENT_VERSION}\n\n"
                        "Do you want to update now?"
                    )
                    if answer:
                        download_and_replace(
                            download_url,
                            latest_version,
                            default_uninstall_path=DEFAULT_UNINSTALL_PATH,
                            uninstall_args=DEFAULT_UNINSTALL_ARGS,
                            uninstall_timeout=DEFAULT_UNINSTALL_TIMEOUT
                        )
                else:
                    messagebox.showinfo(
                        "New Update Available",
                        f"A new version {latest_version} is available, but no attached file was found!"
                    )
            else:
                messagebox.showinfo(
                    "Information",
                    f"You are already using the latest version ({CURRENT_VERSION})"
                )
        else:
            messagebox.showerror("Error", f"Failed to connect to GitHub: {resp.status_code}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not check for updates:\n{e}")

def download_and_replace(download_url, latest_version, default_uninstall_path=None, uninstall_args=None, uninstall_timeout=60):
    def worker():
        prog_win = prog_label = prog_bar = None
        tmp_path = None
        try:
            # Chuẩn bị tên file an toàn
            parsed = urlparse(download_url)
            filename = os.path.basename(parsed.path) or f"update_{latest_version}.bin"
            filename = "".join(c for c in filename if c.isalnum() or c in "._-")
            save_path = os.path.join(download_folder, filename)
            if os.path.exists(save_path):
                base, ext = os.path.splitext(save_path)
                save_path = f"{base}_v{latest_version}{ext}"

            # tạo progress dialog trong main thread
            def create_progress():
                nonlocal prog_win, prog_label, prog_bar
                prog_win = tk.Toplevel(root)
                prog_win.title("Downloading update...")
                prog_win.resizable(False, False)
                prog_label = tk.Label(prog_win, text=f"Downloading {filename}")
                prog_label.pack(padx=12, pady=(10,6))
                prog_bar = ttk.Progressbar(prog_win, length=300, mode='determinate')
                prog_bar.pack(padx=12, pady=(0,10))
                prog_win.transient(root)
                prog_win.grab_set()
                prog_win.update_idletasks()
            root.after(0, create_progress)

            # Download with timeout and progress
            with requests.get(download_url, stream=True, timeout=30) as r:
                r.raise_for_status()
                total = r.headers.get('Content-Length')
                if total is not None:
                    total = int(total)
                    root.after(0, lambda: prog_bar.config(maximum=total))
                bytes_written = 0
                tmp_path = save_path + ".part"
                with open(tmp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
                        bytes_written += len(chunk)
                        def _upd():
                            if prog_bar and total:
                                prog_bar['value'] = bytes_written
                            if prog_label:
                                if total:
                                    percent = bytes_written / total * 100
                                    prog_label.config(text=f"Downloading {filename} — {percent:.1f}%")
                                else:
                                    prog_label.config(text=f"Downloading {filename} — {bytes_written//1024} KB")
                        root.after(0, _upd)
                os.replace(tmp_path, save_path)
                tmp_path = None  # đã move thành công

            # Close progress dialog
            root.after(0, lambda: prog_win.destroy() if prog_win else None)

            # Nếu user muốn uninstall trước, hỏi đường dẫn uninstaller
            uninstall_path = None
            if default_uninstall_path:
                # hỏi user có muốn dùng đường dẫn mặc định không
                use_default = messagebox.askyesno(
                    "Uninstall existing app?",
                    f"Bạn muốn chạy uninstaller tại:\n{default_uninstall_path}\nTrước khi cài bản mới?"
                )
                if use_default:
                    uninstall_path = default_uninstall_path

            if not uninstall_path:
                # hỏi user nhập đường dẫn uninstall (user có thể Cancel)
                ans = messagebox.askyesno("Uninstall existing app?", "Bạn muốn chọn đường dẫn uninstaller thủ công trước khi cài (Recommended)?")
                if ans:
                    # opens file dialog để chọn exe
                    upath = filedialog.askopenfilename(title="Select uninstall executable (unins000.exe)", filetypes=[("Executable","*.exe"),("All files","*.*")])
                    if upath:
                        uninstall_path = upath

            # Nếu có uninstall_path -> thực thi uninstaller (với args nếu cung cấp)
            if uninstall_path:
                if not os.path.exists(uninstall_path):
                    root.after(0, lambda: messagebox.showwarning("Uninstall not found", f"Không tìm thấy file uninstaller:\n{uninstall_path}\nBỏ qua bước uninstall."))
                else:
                    # hỏi xác nhận cuối cùng
                    confirm = messagebox.askyesno("Confirm uninstall", f"Ứng dụng sẽ chạy uninstaller:\n{uninstall_path}\nBạn có chắc muốn tiếp tục?")
                    if confirm:
                        try:
                            # build command
                            cmd = [uninstall_path]
                            if uninstall_args:
                                # nếu uninstall_args là string -> split, nếu list -> extend
                                if isinstance(uninstall_args, str):
                                    cmd.extend(uninstall_args.split())
                                else:
                                    cmd.extend(uninstall_args)
                            # run and wait (có timeout)
                            # note: uninstaller thường spawn child process and exit 0 even khi uninstall tiếp tục.
                            proc = subprocess.run(cmd, shell=False, timeout=uninstall_timeout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            if proc.returncode != 0:
                                # hiển thị cảnh báo nhưng cho phép tiếp tục
                                msg = proc.stderr.decode(errors='ignore')[:200] if proc.stderr else f"Exit code: {proc.returncode}"
                                root.after(0, lambda: messagebox.showwarning("Uninstall warning", f"Uninstaller returned non-zero: {msg}\nBạn có muốn tiếp tục cài đặt bản mới?"))
                                # hỏi tiếp tục hay dừng
                                cont = messagebox.askyesno("Continue install?", "Uninstall không trả về trạng thái thành công. Bạn có muốn tiếp tục cài bản mới không?")
                                if not cont:
                                    root.after(0, lambda: messagebox.showinfo("Cancelled", "Cập nhật đã bị huỷ."))
                                    return
                            else:
                                root.after(0, lambda: messagebox.showinfo("Uninstall", "Uninstall hoàn tất (hoặc đã được khởi chạy)."))
                        except subprocess.TimeoutExpired:
                            cont = messagebox.askyesno("Timeout", f"Uninstaller mất quá {uninstall_timeout} giây và chưa kết thúc.\nBạn muốn tiếp tục (bỏ qua) hay hủy cập nhật?")
                            if not cont:
                                root.after(0, lambda: messagebox.showinfo("Cancelled", "Cập nhật đã bị huỷ do uninstaller timeout."))
                                return
                        except Exception as ex:
                            cont = messagebox.askyesno("Error running uninstaller", f"Lỗi khi chạy uninstaller:\n{ex}\nBạn có muốn tiếp tục cài đặt bản mới không?")
                            if not cont:
                                root.after(0, lambda: messagebox.showinfo("Cancelled", "Cập nhật đã bị huỷ."))
                                return

            # Sau bước uninstall (hoặc bỏ qua) -> chạy installer đã tải
            ext = os.path.splitext(save_path)[1].lower()
            try:
                if ext in ('.exe', '.msi'):
                    if sys.platform.startswith("win"):
                        os.startfile(save_path)
                    else:
                        subprocess.Popen([save_path], shell=False)
                else:
                    # không phải installer -> mở thư mục chứa file
                    folder = os.path.dirname(save_path)
                    if sys.platform.startswith("win"):
                        os.startfile(folder)
                    elif sys.platform.startswith("linux"):
                        subprocess.Popen(["xdg-open", folder])
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", folder])

                root.after(0, lambda: messagebox.showinfo("Installer started", "Installer đã được mở. Ứng dụng sẽ đóng lại."))
                root.after(200, lambda: root.destroy())
            except Exception as e:
                root.after(0, lambda: messagebox.showerror("Launch error", f"Không thể khởi chạy installer:\n{e}\nFile đã lưu ở:\n{save_path}"))

        except Exception as e:
            # cleanup partial file nếu có
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except:
                pass
            root.after(0, lambda: messagebox.showerror("Download error", f"Không tải được file mới:\n{e}"))
        finally:
            # đảm bảo dialog progress được đóng
            try:
                if prog_win:
                    root.after(0, prog_win.destroy)
            except:
                pass

    threading.Thread(target=worker, daemon=True).start()
# ==== END CHECK UPDATE ====

def open_installed_voice_app():
    app_path = r"C:\Program Files (x86)\MyGPPController\voice_app.exe"
    try:
        os.startfile(app_path)
    except Exception as e:
        print(f"Không thể mở ứng dụng: {e}")

# ======================= GIAO DIỆN (scrollable content + fixed footer) =======================
root = tk.Tk()
MIN_WIDTH = 760
MIN_HEIGHT = 300
root.geometry("760x860")
root.minsize(MIN_WIDTH, MIN_HEIGHT)
root.configure(bg="#f0f7ff")
root.resizable(False, True)
refresh_version_info()

# ----------------- Main container + scrollable canvas -----------------
main_container = tk.Frame(root, bg="#f0f7ff")
main_container.pack(side="top", fill="both", expand=True, pady=0, padx=0)

canvas = tk.Canvas(main_container, bg="#f0f7ff", highlightthickness=0)
v_scroll = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=v_scroll.set)

scrollable_frame = tk.Frame(canvas, bg="#f0f7ff")
canvas_window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

canvas.pack(side="left", fill="both", expand=True)
v_scroll.pack(side="right", fill="y")

def _on_scrollable_config(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
scrollable_frame.bind("<Configure>", _on_scrollable_config)

def _on_canvas_config(event):
    canvas.itemconfig(canvas_window_id, width=event.width)
canvas.bind("<Configure>", _on_canvas_config)

# Mouse wheel support
def _on_mousewheel(event):
    if sys.platform == 'darwin':
        canvas.yview_scroll(int(-1 * (event.delta)), "units")
    else:
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

# Bind mousewheel to canvas (works across platforms)
canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

# ----------------- Now create the UI widgets inside `scrollable_frame` -----------------

# Style for LabelFrames
frame_device = tk.LabelFrame(scrollable_frame, text="Device", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
frame_device.pack(pady=5, padx=10, fill="x")
tk.Label(frame_device, text="🔧 Select device:", bg="#ffffff", fg="#003366", font=("Arial", 10, "bold")).pack(side="left", padx=5)
combo_device = ttk.Combobox(frame_device, width=20, values=["GPP-3323", "Keysight"])
combo_device.set("GPP-3323")
combo_device.pack(side="left", padx=5)
combo_device.bind("<<ComboboxSelected>>", on_device_change)
btn_save_config = tk.Button(frame_device, text="💾 Save Config", bg="#ccffcc", command=save_config)
btn_save_config.pack(side="left", padx=10)
btn_load_config = tk.Button(frame_device, text="📂 Load Config", bg="#cce6ff", command=load_config)
btn_load_config.pack(side="left", padx=5)
btn_voice = tk.Button(frame_device, text="🔊 Voice", bg="#cce6ff", command=open_installed_voice_app)
btn_voice.pack(side="left", padx=5)

frame_com = tk.LabelFrame(scrollable_frame, text="COM Connection", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
frame_com.pack(pady=5, padx=10, fill="x")
combo_com = ttk.Combobox(frame_com, width=15)
combo_com.pack(side="left", padx=5)
tk.Label(frame_com, text="Baudrate:", bg="#ffffff", fg="#003366").pack(side="left", padx=5)
combo_baud = ttk.Combobox(frame_com, width=10, values=[4800,9600,19200,38400,57600,115200])
combo_baud.set(115200)
combo_baud.pack(side="left", padx=5)
btn_refresh = tk.Button(frame_com, text="🔄 Refresh", bg="#cce6ff", activebackground="#99ccff", command=refresh_com_list)
btn_refresh.pack(side="left", padx=5)
btn_connect = tk.Button(frame_com, text="🔌 Connect", bg="#ccffcc", activebackground="#99ff99", command=connect_com)
btn_connect.pack(side="left", padx=5)
btn_disconnect = tk.Button(frame_com, text="❌ Disconnect", bg="#ffcccc", activebackground="#ff9999", command=disconnect_com)
btn_disconnect.pack(side="left", padx=5)

frame_current = tk.LabelFrame(scrollable_frame, text="Current Setting", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
frame_current.pack(pady=5, padx=10, fill="x")
tk.Label(frame_current, text="Current (A):", bg="#ffffff", fg="#003366").pack(side="left", padx=5)
entry_current = tk.Entry(frame_current, width=10, justify="center", bg="#f0fff0")
entry_current.pack(side="left", padx=5)
entry_current.bind("<Return>", on_current_enter)
entry_current.insert(0, "0.3")

frame_status = tk.LabelFrame(scrollable_frame, text="📌 Status", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=10, pady=10)
frame_status.pack(pady=10, fill="x", padx=20)
lbl_status = tk.Label(frame_status, text="Not connected", fg="red", bg="#ffffff", font=("Arial", 11, "bold"))
lbl_status.grid(row=0, column=0, sticky="w", pady=3)
lbl_output = tk.Label(frame_status, text="⚡ Output unknown", fg="blue", bg="#ffffff", font=("Arial", 12, "bold"))
lbl_output.grid(row=1, column=0, sticky="w", pady=3)
lbl_voltage = tk.Label(frame_status, text="⚡ Voltage: --", fg="#000000", bg="#ffffff", font=("Arial", 14, "bold"))
lbl_voltage.grid(row=2, column=0, sticky="w", pady=3)

# ================== TOP FRAMES ==================
frame_top = tk.Frame(scrollable_frame, bg="#f0f7ff")
frame_top.pack(side="top", fill="x", padx=10, pady=2)

# Frame Mode
frame_mode = tk.LabelFrame(frame_top, text="Select Mode",
                           bg="#ffffff", fg="#003366",
                           bd=2, relief="groove", width=300, height=150)
frame_mode.pack_propagate(False)
frame_mode.pack(side="left", padx=(5,2), pady=0)

mode_var = tk.IntVar(value=1)
rb_mode1 = tk.Radiobutton(frame_mode, text="Mode 1: Default list",
                          variable=mode_var, value=1,
                          bg="#ffffff", activebackground="#e6f2ff",
                          command=on_mode_change)
rb_mode1.pack(pady=5)

rb_mode2 = tk.Radiobutton(frame_mode, text="Mode 2: Manual input",
                          variable=mode_var, value=2,
                          bg="#ffffff", activebackground="#e6f2ff",
                          command=on_mode_change)
rb_mode2.pack(pady=5)

# NEW: Mode 3
rb_mode3 = tk.Radiobutton(frame_mode, text="Mode 3: Range Mode",
                          variable=mode_var, value=3,
                          bg="#ffffff", activebackground="#e6f2ff",
                          command=on_mode_change)
rb_mode3.pack(pady=5)

entry_custom_voltage = tk.Entry(frame_mode, bg="#f0fff0")
entry_custom_voltage.pack(pady=3)
entry_custom_voltage.bind("<Return>", on_custom_voltage_enter)

# Frame Protection
frame_protection = tk.LabelFrame(frame_top, text="OVP/OCP Protection",
                                 bg="#ffffff", fg="#003366",
                                 bd=2, relief="groove", width=300, height=150)
frame_protection.pack_propagate(False)
frame_protection.pack(side="left", padx=(2,5))

# Nút bật/tắt đọc phản hồi
btn_toggle_resp = tk.Button(
    frame_protection,
    text="Read Resp: ON",
    bg="lightgreen",
    font=("Arial", 10, "bold"),
    command=toggle_read_response
)
btn_toggle_resp.grid(row=0, column=0, padx=10, pady=3)
update_toggle_button()

# OVP
tk.Label(frame_protection, text="OVP (V):", bg="#ffffff").grid(row=1, column=0, padx=5, pady=2)
entry_ovp = tk.Entry(frame_protection, width=8, justify="center")
entry_ovp.grid(row=1, column=1, padx=5, pady=2)
entry_ovp.bind("<Return>", on_ovp_enter)
entry_ovp.insert(0, "5.0")
btn_ovp_on = tk.Button(frame_protection, text="OVP ON", width=8, command=lambda: set_ovp(True))
btn_ovp_on.grid(row=1, column=2, padx=5, pady=2)
btn_ovp_off = tk.Button(frame_protection, text="OVP OFF", width=8, command=lambda: set_ovp(False))
btn_ovp_off.grid(row=1, column=3, padx=5, pady=2)

# OCP
tk.Label(frame_protection, text="OCP (A):", bg="#ffffff").grid(row=2, column=0, padx=5, pady=2)
entry_ocp = tk.Entry(frame_protection, width=8, justify="center")
entry_ocp.grid(row=2, column=1, padx=5, pady=2)
entry_ocp.bind("<Return>", on_ocp_enter)
entry_ocp.insert(0, "0.3")
btn_ocp_on = tk.Button(frame_protection, text="OCP ON", width=8, command=lambda: set_ocp(True))
btn_ocp_on.grid(row=2, column=2, padx=5, pady=2)
btn_ocp_off = tk.Button(frame_protection, text="OCP OFF", width=8, command=lambda: set_ocp(False))
btn_ocp_off.grid(row=2, column=3, padx=5, pady=2)

# ================== BOTTOM FRAMES ==================
frame_bottom = tk.Frame(scrollable_frame, bg="#f0f7ff", height=335)
frame_bottom.pack(side="top", fill="x", padx=10, pady=2)
# nếu muốn cố định chiều cao thì giữ pack_propagate(False)
frame_bottom.pack_propagate(False)

# --- NEW: left holder (cố định bên trái) ---
left_holder = tk.Frame(frame_bottom, bg="#f0f7ff")
left_holder.pack(side="left", fill="both", expand=True, padx=5, pady=5)

# Left: Voltage list Mode 1
frame_numboxs = tk.LabelFrame(left_holder, text="Voltage for Mode 1",
                              bg="#ffffff", fg="#003366",
                              bd=2, relief="groove")
frame_numboxs.pack(fill="both", expand=True, padx=5, pady=5)   # shown by default

# Mode3 is also child of left_holder but NOT packed at start
frame_mode3 = tk.LabelFrame(left_holder, text="Range Mode (Mode 3)",
                            bg="#ffffff", fg="#003366",
                            bd=2, relief="groove")
# do not pack frame_mode3 now, we'll pack it when mode 3 selected

# inside frame_mode3: controls for start, end, delay and a start/stop button
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

# Use existing voltage_step variable. If you want separate step for mode3,
# add entry or reuse lbl_step / step_index controls. For now we'll use voltage_step.
tk.Label(frame_mode3, text="Step (uses current Step):", bg="#ffffff").grid(row=3, column=0, columnspan=2, padx=5, pady=(2,6))

# biến resume
resume_var = tk.BooleanVar(value=True)
chk_resume = tk.Checkbutton(frame_mode3, text="Resume from current (if stopped)", variable=resume_var,
                            bg="#ffffff", anchor="w")
chk_resume.grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=(0,6))

# Start/Stop button for range mode; _toggle_range must exist (we'll add functions later)
btn_range_start = tk.Button(frame_mode3, text="▶ Start Range", bg="#ccffcc", width=20, command=toggle_range)
btn_range_start.grid(row=5, column=0, columnspan=2, padx=5, pady=6)

frame_num_boxes = tk.Frame(frame_numboxs, bg="#ffffff")
frame_num_boxes.pack(pady=(5, 0))

frame_auto_run = tk.Frame(frame_numboxs, bg="#ffffff")
frame_auto_run.pack(pady=5)

tk.Label(frame_auto_run, text="Delay (s):").grid(row=7, column=0, pady=5)
delay_entry = tk.Entry(frame_auto_run, width=8, justify="center")
delay_entry.insert(0, "5")
delay_entry.grid(row=7, column=1, pady=5)

btn_auto_run = tk.Button(frame_auto_run, text="▶ Auto Run", width=15, bg="#ffcccc", command=toggle_auto_run)
btn_auto_run.grid(row=8, column=0, columnspan=3, pady=5)

tk.Label(frame_num_boxes, text="🔢 Number of boxes:", bg="#ffffff", fg="#003366").pack(side="left", padx=5)
combo_num_boxes = ttk.Combobox(frame_num_boxes, width=5, values=[2,3,4,5,6,7,8,9,10,18], state="normal")
combo_num_boxes.set(NUM_VOLTAGE_BOXES)
combo_num_boxes.pack(side="left", padx=5)

# Tạo canvas và scrollbar cho các ô voltage (nếu cần)
frame_mode1_canvas = tk.Canvas(frame_numboxs, bg="#ffffff", highlightthickness=0)
scroll_y = tk.Scrollbar(frame_numboxs, orient="vertical", command=frame_mode1_canvas.yview)
scroll_x = tk.Scrollbar(frame_numboxs, orient="horizontal", command=frame_mode1_canvas.xview)

frame_mode1_canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")
frame_mode1_canvas.pack(side="left", fill="both", expand=True)

frame_mode1_boxes = tk.Frame(frame_mode1_canvas, bg="#ffffff")
frame_mode1_canvas.create_window((0,0), window=frame_mode1_boxes, anchor="nw")

frame_mode1_boxes.bind("<Configure>", lambda e: frame_mode1_canvas.configure(
    scrollregion=frame_mode1_canvas.bbox("all")
))

combo_num_boxes.bind("<<ComboboxSelected>>", on_num_boxes_change)
combo_num_boxes.bind("<Return>", lambda event: on_num_boxes_change(event))
build_voltage_entries(NUM_VOLTAGE_BOXES)

# ---------- Frame Voltage Adjustment ----------
frame_btn = tk.LabelFrame(frame_bottom, text="Voltage Adjustment",
                          bg="#ffffff", fg="#003366",
                          bd=2, relief="groove", width=250, height=300)
frame_btn.pack_propagate(False)
frame_btn.pack(side="left", fill="y", padx=5, pady=5)

tk.Button(frame_btn, text="⬆ Increase", width=10, bg="#cce6ff", command=increase_voltage).grid(row=0, column=1, padx=5, pady=5)
tk.Button(frame_btn, text="⬇ Decrease", width=10, bg="#cce6ff", command=decrease_voltage).grid(row=2, column=1, padx=5, pady=5)
tk.Button(frame_btn, text="◀ Step-", width=10, bg="#cce6ff", command=step_prev).grid(row=1, column=0, padx=5, pady=5)

lbl_step = tk.Label(frame_btn, text=f"Step: {voltage_step}", width=12,
                    bg="#ffffcc", relief="solid", bd=1.2, font=("Arial", 12))
lbl_step.grid(row=1, column=1, padx=5, pady=5)

tk.Button(frame_btn, text="▶ Step+", width=10, bg="#cce6ff", command=step_next).grid(row=1, column=2, padx=5, pady=5)

reverse_var = tk.BooleanVar(value=False)
tk.Checkbutton(frame_btn, text="🔁 Reverse direction", variable=reverse_var).grid(row=3, column=0, columnspan=3)

tk.Button(frame_btn, text="⏩ Next voltage", width=20, bg="#e6e6fa", command=next_voltage).grid(row=4, column=0, columnspan=3, pady=5)
tk.Button(frame_btn, text="🔄 Reset mode", width=20, bg="#e6e6fa", command=reset_mode).grid(row=5, column=0, columnspan=3, pady=5)
tk.Button(frame_btn, text="🔄 Check for update", width=20, bg="#e6ffe6", command=check_update).grid(row=6, column=0, columnspan=3, pady=5)
tk.Button(frame_btn, text="❌ Exit", width=20, bg="#ffcccc", command=quit_app).grid(row=7, column=0, columnspan=3, pady=5)

# ----------------- Footer (fixed at bottom) -----------------
footer_frame = tk.Frame(root, bg="#f0f7ff", height=25)
footer_frame.pack_propagate(False)
footer_frame.pack(side="bottom", fill="x")

# Dòng bản quyền
copyright_text = "© 2025 BuiVuDuyTruong-Embedded. All rights reserved."
lbl_copyright = tk.Label(
    footer_frame,
    text=copyright_text,
    bg="#f0f7ff",
    fg="#555555",
    font=("Arial", 8)
)
lbl_copyright.pack(side="left", padx=5)

# ==== LINK AREA ====
def callback(url):
    webbrowser.open_new(url)

link_frame = tk.Frame(footer_frame, bg="#f0f7ff")
link_frame.pack(side="right", pady=2)

def load_icon(path, size=None):
    abs_path = resource_path(path)
    try:
        img = Image.open(abs_path)
    except Exception as e:
        print("Icon load failed:", abs_path, e)
        img = Image.new("RGBA", (size or (20,20)), (200,200,200,0))
    if size:
        img = img.resize(size, Image.LANCZOS)
    return ImageTk.PhotoImage(img)

fb_icon = load_icon("assets/icons8-facebook-48.png", (20, 20))
linkedin_icon = load_icon("assets/icons8-linkedin-48.png", (20, 20))
github_icon = load_icon("assets/icons8-github-32.png", (20, 20))

def make_icon_link(parent, icon, url, tooltip=""):
    lbl = tk.Label(parent, image=icon, bg="#f0f7ff", cursor="hand2")
    lbl.image = icon
    lbl.pack(side="left", padx=8)
    lbl.bind("<Button-1>", lambda e: callback(url))
    return lbl

make_icon_link(link_frame, fb_icon, "https://www.facebook.com/bui.truong.902266")
make_icon_link(link_frame, linkedin_icon, "https://www.linkedin.com/in/b%C3%B9i-tr%C6%B0%E1%BB%9Dng-embedded/")
make_icon_link(link_frame, github_icon, "https://github.com/TruongBVD69")

# Phiên bản app
app_version_text = f"Version: {CURRENT_VERSION}"
lbl_version = tk.Label(
    footer_frame,
    text=app_version_text,
    bg="#f0f7ff",
    fg="#555555",
    font=("Arial", 8)
)
lbl_version.pack(side="right", padx=5)

root.mainloop()
