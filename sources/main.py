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

# ======================= BIẾN TOÀN CỤC =======================
GITHUB_API_LATEST_RELEASE = "https://api.github.com/repos/TruongBVD69/App_control_powersupply/releases/latest"
CURRENT_VERSION = "v1.0.3"

ser = None
current_voltage = 0.0
index = 0

voltages = [1.815, 2.479, 3.117, 3.755]

step_options = [0.1, 0.01, 0.001]
step_index = 1
voltage_step = step_options[step_index]

CONFIG_FILE = os.path.join(os.getenv('APPDATA'), 'MyGPPController_config.json')
mode_selected = 1  # 1: list mặc định, 2: tự nhập

NUM_VOLTAGE_BOXES = 4
entry_volt_boxes = []

device_type = "GPP"  # GPP hoặc Keysight

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
        print("Lỗi đọc version.txt:", e)
        return {"AppName": "Unknown", "Version": "Unknown", "BuildTime": "Unknown"}

def refresh_version_info():
    global CURRENT_VERSION, app_info
    app_info = get_app_info()
    CURRENT_VERSION = app_info["Version"]
    root.title(f"{app_info['AppName']} - {CURRENT_VERSION}")
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
    elif device_type == "KEYSIGHT":
        # Keysight
        ser.write((cmd + '\n').encode('ascii'))
    else:
        return "--"  # nếu chưa chọn loại máy
    time.sleep(0.1)
    resp = ser.readline().decode(errors='ignore').strip()
    return resp

def set_voltage(v):
    global current_voltage
    current_voltage = round(v, 3)

    # Gửi lệnh theo đúng loại máy
    if device_type == "GPP":
        # GPP-3323
        send_cmd(f'VOLT {current_voltage}')
        time.sleep(0.01)
        readv = send_cmd('MEAS:VOLT?')
    elif device_type == "KEYSIGHT":
        # Keysight
        send_cmd(f'VOLT {current_voltage}')
        time.sleep(0.01)
        readv = send_cmd('MEAS:VOLT?')
    else:
        readv = "--"  # nếu chưa chọn loại máy

    # Cập nhật label
    lbl_voltage.config(
        text=f"⚡ Điện áp: {current_voltage:.3f} V (máy trả: {readv} V)"
    )

    # highlight ô entry nếu đang ở mode 1
    if mode_selected == 1:
        for i, e in enumerate(entry_volt_boxes):
            try:
                val = float(e.get())
                if abs(val - current_voltage) < 1e-6:
                    e.config(bg="lightgreen")
                else:
                    e.config(bg="white")
            except:
                e.config(bg="white")

def output_on():
    send_cmd('OUTP ON')
    lbl_output.config(text="🟢 Output: ON", fg="green")

def output_off():
    send_cmd('OUTP OFF')
    lbl_output.config(text="🔴 Output: OFF", fg="red")

def set_ovp(enable: bool):
    if not ser or not ser.is_open:
        messagebox.showerror("Lỗi", "Chưa kết nối thiết bị!")
        return
    val = entry_ovp.get().strip()
    if enable:
        if val == "":
            messagebox.showerror("Lỗi", "Nhập giá trị OVP trước!")
            return
        try:
            v = float(val)
            # print(f"Setting OVP to {v}V for {device_type}")
            if device_type == "GPP":
                send_cmd(f'OUTP1:OVP {v}')
                send_cmd('OUTP1:OVP:STAT ON')
            elif device_type == "KEYSIGHT":
                send_cmd(f'VOLT:PROT {v}')
                send_cmd('VOLT:PROT:STAT ON')
            # messagebox.showinfo("Thành công", f"Bật OVP = {v}V")
            btn_ovp_on.config(bg="lightgreen")
            btn_ovp_off.config(bg="SystemButtonFace")
        except:
            messagebox.showerror("Lỗi", "Giá trị OVP không hợp lệ!")
    else:
        # OFF
        if device_type == "GPP":
            send_cmd('OUTP1:OVP:STAT OFF')
        elif device_type == "KEYSIGHT":
            send_cmd('VOLT:PROT:STAT OFF')
        # messagebox.showinfo("Thành công", "Đã tắt OVP")
        btn_ovp_on.config(bg="SystemButtonFace")
        btn_ovp_off.config(bg="red")

def set_ocp(enable: bool):
    if not ser or not ser.is_open:
        messagebox.showerror("Lỗi", "Chưa kết nối thiết bị!")
        return
    val = entry_ocp.get().strip()
    if enable:
        if val == "":
            messagebox.showerror("Lỗi", "Nhập giá trị OCP trước!")
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
            messagebox.showerror("Lỗi", "Giá trị OCP không hợp lệ!")
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
    index = (index + 1) % len(list_volt)
    set_voltage(list_volt[index])
    time.sleep(0.02)

def step_next():
    global step_index, voltage_step
    if step_index < len(step_options) - 1:
        step_index += 1
        voltage_step = step_options[step_index]
        lbl_step.config(text=f"Bước: {voltage_step}")
    else:
        messagebox.showinfo("Thông báo", "Đang ở bước nhỏ nhất.")

def step_prev():
    global step_index, voltage_step
    if step_index > 0:
        step_index -= 1
        voltage_step = step_options[step_index]
        lbl_step.config(text=f"Bước: {voltage_step}")
    else:
        messagebox.showinfo("Thông báo", "Đang ở bước lớn nhất.")

def increase_voltage():
    set_voltage(current_voltage + voltage_step)

def decrease_voltage():
    set_voltage(current_voltage - voltage_step)

# def highlight_mode():
#     if mode_selected == 1:
#         btn_mode1.config(bg="lightgreen", activebackground="lightgreen")
#         btn_mode2.config(bg="SystemButtonFace", activebackground="SystemButtonFace")
#     elif mode_selected == 2:
#         btn_mode2.config(bg="lightgreen", activebackground="lightgreen")
#         btn_mode1.config(bg="SystemButtonFace", activebackground="SystemButtonFace")

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
            messagebox.showerror("Lỗi", "Chưa nhập điện áp nào trong list!")
    else:
        try:
            val = float(entry_custom_voltage.get().strip())
            set_voltage(val)
        except:
            messagebox.showerror("Lỗi", "Điện áp nhập không hợp lệ!")

def reset_mode():
    output_off()
    output_on()
    apply_mode()

def quit_app():
    if ser and ser.is_open:
        output_off()
        ser.close()
    root.destroy()

# ======================= KẾT NỐI COM =======================
def refresh_com_list():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    combo_com['values'] = ports
    if ports:
        combo_com.current(0)

def save_config(port):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"com_port": port}, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

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
        messagebox.showerror("Lỗi", "Vui lòng nhập dòng điện trước khi kết nối!")
        return

    # Chuyển giá trị dòng điện sang float
    try:
        curr_val = float(entry_current.get().strip())
    except ValueError:
        messagebox.showerror("Lỗi", "Giá trị dòng điện không hợp lệ!")
        return

    if not port:
        messagebox.showerror("Lỗi", "Chưa chọn cổng COM.")
        return
    try:
        baud = int(baud)
    except:
        messagebox.showerror("Lỗi", "Baudrate không hợp lệ.")
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
            messagebox.showerror("Lỗi", f"Không phải GPP-3323.\nTrả về: {resp}")
            return
        if device_type == "Agilent Technologies" and "E3646A" not in resp:
            s.close()
            messagebox.showerror("Lỗi", f"Không phải Keysight.\nTrả về: {resp}")
            return

        ser = s
        lbl_status.config(text=f"✅ Kết nối: {resp} @ {baud}bps", fg="green")
        save_config(port)
        send_cmd('*CLS')

        # ✅ Gửi dòng điện ngay khi kết nối
        send_cmd(f'CURR {curr_val}')

        output_on()
        apply_mode()
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể mở {port}\n{e}")

def disconnect_com():
    global ser
    if ser and ser.is_open:
        try:
            output_off()  # tắt output trước khi ngắt (nếu muốn)
            ser.close()
            ser = None
            lbl_status.config(text="🔌 Đã ngắt kết nối", fg="orange")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi ngắt kết nối:\n{e}")
    else:
        lbl_status.config(text="⚠ Chưa có kết nối để ngắt", fg="red")

# --- Xử lý sự kiện khi nhấn Enter trong ô nhập điện áp ---
def on_voltage_entry_return(event):
    # chỉ xử lý khi đang ở mode 1 và đã kết nối
    if mode_selected == 1 and ser and ser.is_open:
        try:
            new_val = float(event.widget.get())
            set_voltage(new_val)
        except ValueError:
            messagebox.showerror("Lỗi", "Giá trị điện áp không hợp lệ!")

def build_voltage_entries(n):
    global entry_volt_boxes, NUM_VOLTAGE_BOXES
    for w in entry_volt_boxes:
        w.destroy()
    entry_volt_boxes.clear()
    NUM_VOLTAGE_BOXES = n
    for i in range(NUM_VOLTAGE_BOXES):
        e = tk.Entry(frame_mode1_boxes, width=10, justify="center")
        if i < len(voltages):
            e.insert(0, str(voltages[i]))
        else:
            e.insert(0, "")
        e.pack(pady=2)
        e.bind("<Return>", on_voltage_entry_return)  # 👈 Bắt sự kiện Enter
        entry_volt_boxes.append(e)
    
    # Sau khi thêm xong các entry mới, cập nhật lại cửa sổ:
    root.update()        # cập nhật GUI
    root.geometry("")    # reset geometry, để Tkinter tự tính lại kích thước window

def on_num_boxes_change(event=None):
    try:
        n = int(combo_num_boxes.get())
        build_voltage_entries(n)
    except:
        pass

def on_mode_change():
    global mode_selected
    mode_selected = mode_var.get()
    apply_mode()

def on_custom_voltage_enter(event=None):
    if mode_selected == 2 and ser and ser.is_open:
        try:
            val = float(entry_custom_voltage.get().strip())
            set_voltage(val)
        except:
            messagebox.showerror("Lỗi", "Điện áp nhập không hợp lệ!")

def on_current_enter(event=None):
    if ser and ser.is_open:
        try:
            val_cur = float(entry_current.get().strip())
            send_cmd(f'CURR {val_cur}')
            # messagebox.showinfo("Thông báo", f"Đã đặt dòng điện: {curr_val} A")
        except ValueError:
            messagebox.showerror("Lỗi", "Giá trị dòng điện không hợp lệ!")
    else:
        messagebox.showerror("Lỗi", "Chưa kết nối thiết bị!")

# ==== CHECK UPDATE ====
def check_update():
    try:
        resp = requests.get(GITHUB_API_LATEST_RELEASE, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            latest_version = data['tag_name']
            if latest_version > CURRENT_VERSION:
                assets = data.get('assets', [])
                if assets:
                    download_url = assets[0]['browser_download_url']
                    answer = messagebox.askyesno(
                        "Cập nhật mới",
                        f"Đã có bản mới: {latest_version}\n"
                        f"Bạn đang dùng: {CURRENT_VERSION}\n\n"
                        "Bạn có muốn cập nhật ngay không?"
                    )
                    if answer:
                        download_and_replace(download_url, latest_version)
                else:
                    messagebox.showinfo(
                        "Cập nhật mới",
                        f"Đã có bản mới {latest_version}, nhưng không tìm thấy file đính kèm!"
                    )
            else:
                messagebox.showinfo(
                    "Thông báo",
                    f"Bạn đang dùng bản mới nhất ({CURRENT_VERSION})"
                )
        else:
            messagebox.showerror("Lỗi", f"Lỗi kết nối GitHub: {resp.status_code}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không kiểm tra được update:\n{e}")

def download_and_replace(download_url, latest_version):
    try:
        filename = download_url.split('/')[-1]

        # Thư mục Downloads
        download_folder = tempfile.gettempdir()
        if not os.path.exists(download_folder):
            download_folder = os.getcwd()  # fallback

        save_path = os.path.join(download_folder, filename)
        if os.path.exists(save_path):
            base, ext = os.path.splitext(save_path)
            save_path = f"{base}_{latest_version}{ext}" # dùng version mới từ GitHub

        # Tải file
        r = requests.get(download_url, stream=True)
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Tạo file batch cập nhật
        temp_dir = tempfile.gettempdir()
        batch_path = os.path.join(temp_dir, "update_script.bat")

        # 👉 Sửa đường dẫn này theo đường dẫn cài đặt hiện tại của bạn
        uninstall_exe = r'"C:\Program Files (x86)\MyGPPController\unins000.exe"'

        with open(batch_path, 'w', encoding='utf-8') as bat:
            bat.write("@echo off\n")
            bat.write("echo [Updater] Đang cập nhật...\n")
            bat.write("timeout /t 2 /nobreak >nul\n")
            bat.write(f"{uninstall_exe}\n")
            bat.write("timeout /t 2 /nobreak >nul\n")
            bat.write(f'start "" "{save_path}"\n')
            bat.write('(goto) 2>nul & del "%~f0"\n')

        # Chạy batch và đóng app
        subprocess.Popen(batch_path, shell=True)
        messagebox.showinfo("Đang cập nhật", "Ứng dụng sẽ đóng và bản mới sẽ được cài đặt.")
        root.destroy()

    except Exception as e:
        messagebox.showerror("Lỗi tải", f"Không tải được file mới:\n{e}")
# ==== END CHECK UPDATE ====

# ======================= GIAO DIỆN =======================
root = tk.Tk()
root.configure(bg="#f0f7ff")  # màu nền tổng thể
refresh_version_info()

root.resizable(False, True)

# Style cho các LabelFrame
frame_device = tk.LabelFrame(root, text="Thiết bị", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
frame_device.pack(pady=5, padx=10, fill="x")
tk.Label(frame_device, text="🔧 Chọn thiết bị:", bg="#ffffff", fg="#003366", font=("Arial", 10, "bold")).pack(side="left", padx=5)
combo_device = ttk.Combobox(frame_device, width=20, values=["GPP-3323", "Keysight"])
combo_device.set("GPP-3323")
combo_device.pack(side="left", padx=5)
combo_device.bind("<<ComboboxSelected>>", on_device_change)

frame_com = tk.LabelFrame(root, text="Kết nối COM", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
frame_com.pack(pady=5, padx=10, fill="x")
combo_com = ttk.Combobox(frame_com, width=15)
combo_com.pack(side="left", padx=5)

tk.Label(frame_com, text="Baudrate:", bg="#ffffff", fg="#003366").pack(side="left", padx=5)
combo_baud = ttk.Combobox(frame_com, width=10, values=[4800,9600,19200,38400,57600,115200])
combo_baud.set(115200)
combo_baud.pack(side="left", padx=5)

btn_refresh = tk.Button(frame_com, text="🔄 Refresh", bg="#cce6ff", activebackground="#99ccff", command=refresh_com_list)
btn_refresh.pack(side="left", padx=5)
btn_connect = tk.Button(frame_com, text="🔌 Kết nối", bg="#ccffcc", activebackground="#99ff99", command=connect_com)
btn_connect.pack(side="left", padx=5)
btn_disconnect = tk.Button(frame_com, text="❌ Ngắt kết nối", bg="#ffcccc", activebackground="#ff9999", command=disconnect_com)
btn_disconnect.pack(side="left", padx=5)

frame_current = tk.LabelFrame(root, text="Thiết lập dòng điện", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
frame_current.pack(pady=5, padx=10, fill="x")
tk.Label(frame_current, text="Dòng điện (A):", bg="#ffffff", fg="#003366").pack(side="left", padx=5)
entry_current = tk.Entry(frame_current, width=10, justify="center", bg="#f0fff0")
entry_current.pack(side="left", padx=5)
entry_current.bind("<Return>", on_current_enter)  # Bắt sự kiện Enter
entry_current.insert(0, "0.3")  # giá trị mặc định

frame_status = tk.LabelFrame(root, text="📌 Trạng thái", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=10, pady=10)
frame_status.pack(pady=10, fill="x", padx=20)

lbl_status = tk.Label(frame_status, text="Chưa kết nối", fg="red", bg="#ffffff", font=("Arial", 11, "bold"))
lbl_status.grid(row=0, column=0, sticky="w", pady=3)
lbl_output = tk.Label(frame_status, text="⚡ Output chưa xác định", fg="blue", bg="#ffffff", font=("Arial", 12, "bold"))
lbl_output.grid(row=1, column=0, sticky="w", pady=3)
lbl_voltage = tk.Label(frame_status, text="⚡ Điện áp: --", fg="#000000", bg="#ffffff", font=("Arial", 14, "bold"))
lbl_voltage.grid(row=2, column=0, sticky="w", pady=3)

# Horizontal frame chứa mode và bảo vệ
frame_horiz = tk.Frame(root, bg="#f0f7ff")
frame_horiz.pack(pady=5)

frame_mode = tk.LabelFrame(frame_horiz, text="Chọn Mode", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
frame_mode.pack(side="left", padx=10)
mode_var = tk.IntVar(value=1)

rb_mode1 = tk.Radiobutton(frame_mode, text="Mode 1: List mặc định", variable=mode_var, value=1,
                          bg="#ffffff", activebackground="#e6f2ff", command=on_mode_change)
rb_mode1.pack(pady=5)
rb_mode2 = tk.Radiobutton(frame_mode, text="Mode 2: Nhập thủ công", variable=mode_var, value=2,
                          bg="#ffffff", activebackground="#e6f2ff", command=on_mode_change)
rb_mode2.pack(pady=5)
entry_custom_voltage = tk.Entry(frame_mode, bg="#f0fff0")
entry_custom_voltage.pack(pady=3)
entry_custom_voltage.bind("<Return>", on_custom_voltage_enter)

# --- OVP/OCP ngang với Mode ---
frame_protection = tk.LabelFrame(frame_horiz, text="Bảo vệ OVP / OCP")
frame_protection.pack(side="left", padx=10)   # đặt bên phải, cùng hàng

# OVP
tk.Label(frame_protection, text="OVP (V):").grid(row=0, column=0, padx=5, pady=2)
entry_ovp = tk.Entry(frame_protection, width=8, justify="center")
entry_ovp.grid(row=0, column=1, padx=5, pady=2)
btn_ovp_on = tk.Button(frame_protection, text="OVP ON", width=8, command=lambda: set_ovp(True))
btn_ovp_on.grid(row=0, column=2, padx=5, pady=2)

btn_ovp_off = tk.Button(frame_protection, text="OVP OFF", width=8, command=lambda: set_ovp(False))
btn_ovp_off.grid(row=0, column=3, padx=5, pady=2)

# OCP
tk.Label(frame_protection, text="OCP (A):").grid(row=1, column=0, padx=5, pady=2)
entry_ocp = tk.Entry(frame_protection, width=8, justify="center")
entry_ocp.grid(row=1, column=1, padx=5, pady=2)
btn_ocp_on = tk.Button(frame_protection, text="OCP ON", width=8, command=lambda: set_ocp(True))
btn_ocp_on.grid(row=1, column=2, padx=5, pady=2)

btn_ocp_off = tk.Button(frame_protection, text="OCP OFF", width=8, command=lambda: set_ocp(False))
btn_ocp_off.grid(row=1, column=3, padx=5, pady=2)


# --- Khối chọn số ô và ô nhập điện áp ---
frame_num_boxes = tk.Frame(root, bg="#f0f7ff")
frame_num_boxes.pack(pady=5)
tk.Label(frame_num_boxes, text="🔢 Số ô điện áp:", bg="#f0f7ff", fg="#003366").pack(side="left", padx=5)
combo_num_boxes = ttk.Combobox(frame_num_boxes, width=5, values=[2,3,4,5,6,7,8,9,10])
combo_num_boxes.set(NUM_VOLTAGE_BOXES)
combo_num_boxes.pack(side="left", padx=5)

frame_mode1_boxes = tk.LabelFrame(root, text="Danh sách điện áp (Mode 1)", bg="#ffffff", fg="#003366", bd=2, relief="groove", padx=5, pady=5)
frame_mode1_boxes.pack(pady=5)

combo_num_boxes.bind("<<ComboboxSelected>>", on_num_boxes_change)
build_voltage_entries(NUM_VOLTAGE_BOXES)

# highlight_mode()

# --- Nút điều chỉnh ---
frame_btn = tk.Frame(root, bg="#f0f7ff")
frame_btn.pack(pady=10)
tk.Button(frame_btn, text="⬆ Tăng", width=10, bg="#cce6ff", command=increase_voltage).grid(row=0, column=1, padx=5, pady=5)
tk.Button(frame_btn, text="⬇ Giảm", width=10, bg="#cce6ff", command=decrease_voltage).grid(row=2, column=1, padx=5, pady=5)
tk.Button(frame_btn, text="◀ Bước-", width=10, bg="#cce6ff", command=step_prev).grid(row=1, column=0, padx=5, pady=5)
lbl_step = tk.Label(frame_btn, text=f"Bước: {voltage_step}", width=12, bg="#ffffcc", relief="solid",
                    bd=1.2, font=("Arial", 12))
lbl_step.grid(row=1, column=1, padx=5, pady=5)
tk.Button(frame_btn, text="▶ Bước+", width=10, bg="#cce6ff", command=step_next).grid(row=1, column=2, padx=5, pady=5)

tk.Button(root, text="⏩ Điện áp kế tiếp", width=20, bg="#e6e6fa", command=next_voltage).pack(pady=5)
tk.Button(root, text="🔄 Reset Mode", width=20, bg="#e6e6fa", command=reset_mode).pack(pady=5)
tk.Button(root, text="🔄 Check for update", width=20, bg="#e6ffe6", command=check_update).pack(pady=5)
tk.Button(root, text="❌ Thoát", width=20, bg="#ffcccc", command=quit_app).pack(pady=5)

cfg = load_config()
if "com_port" in cfg:
    refresh_com_list()
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if cfg["com_port"] in ports:
        combo_com.set(cfg["com_port"])

root.mainloop()