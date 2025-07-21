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

# ======================= BIẾN TOÀN CỤC =======================
GITHUB_API_LATEST_RELEASE = "https://api.github.com/repos/TruongBVD69/App_control_powersupply/releases/latest"
CURRENT_VERSION = "v1.0.0"

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
    highlight_mode()
    apply_mode()

def choose_mode_2():
    global mode_selected
    mode_selected = 2
    highlight_mode()
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
        send_cmd('CURR 0.5')
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

# ==== CHECK UPDATE ====
def check_update():
    try:
        resp = requests.get(GITHUB_API_LATEST_RELEASE, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            latest_version = data['tag_name']
            if latest_version > CURRENT_VERSION:
                # Lấy link file đầu tiên trong release
                assets = data.get('assets', [])
                if assets:
                    download_url = assets[0]['browser_download_url']
                    answer = messagebox.askyesno(
                        "Cập nhật mới",
                        f"Đã có bản mới: {latest_version}\n"
                        f"Bạn đang dùng: {CURRENT_VERSION}\n\n"
                        "Bạn có muốn mở link tải không?"
                    )
                    if answer:
                        download_and_replace(download_url)
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
# ==== END CHECK UPDATE ====

def download_and_replace(download_url):
    try:
        filename = download_url.split('/')[-1]
        # Tải file mới
        r = requests.get(download_url, stream=True)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        messagebox.showinfo("Tải xong", f"Đã tải file {filename}.\nHãy đóng app và chạy file mới.")
        # Nếu muốn tự mở file mới:
        # os.startfile(filename)
        # root.quit()
    except Exception as e:
        messagebox.showerror("Lỗi tải", f"Không tải được file mới:\n{e}")

# ======================= GIAO DIỆN =======================
root = tk.Tk()
root.title("Điều khiển GPP-3323")

# root.geometry("650x750")
root.resizable(False, True)

# --- Khối chọn thiết bị ---
frame_device = tk.Frame(root)
frame_device.pack(pady=5)
tk.Label(frame_device, text="🔧 Chọn thiết bị:").pack(side="left", padx=5)
combo_device = ttk.Combobox(frame_device, width=20, values=["GPP-3323", "Keysight"])
combo_device.set("GPP-3323")
combo_device.pack(side="left", padx=5)
combo_device.bind("<<ComboboxSelected>>", on_device_change)

# --- Khối chọn COM & Baud ---
frame_com = tk.Frame(root)
frame_com.pack(pady=5)
combo_com = ttk.Combobox(frame_com, width=15)
combo_com.pack(side="left", padx=5)

tk.Label(frame_com, text="Baudrate:").pack(side="left", padx=5)
combo_baud = ttk.Combobox(frame_com, width=10, values=[4800,9600,19200,38400,57600,115200])
combo_baud.set(115200)
combo_baud.pack(side="left", padx=5)

btn_refresh = tk.Button(frame_com, text="🔄 Refresh", command=refresh_com_list)
btn_refresh.pack(side="left", padx=5)
btn_connect = tk.Button(frame_com, text="🔌 Kết nối", command=connect_com)
btn_connect.pack(side="left", padx=5)
btn_disconnect = tk.Button(frame_com, text="❌ Ngắt kết nối", command=disconnect_com)
btn_disconnect.pack(side="left", padx=5)

lbl_status = tk.Label(root, text="Chưa kết nối", fg="red")
lbl_status.pack(pady=5)

lbl_output = tk.Label(root, text="⚡ Output chưa xác định", fg="blue", font=("Arial", 12))
lbl_output.pack(pady=5)

lbl_voltage = tk.Label(root, text=f"⚡ Điện áp: --", font=("Arial", 14))
lbl_voltage.pack(pady=10)

# --- Chọn mode ---
frame_mode = tk.LabelFrame(root, text="Chọn Mode")
frame_mode.pack(pady=5)

mode_var = tk.IntVar(value=1)  # mặc định Mode 1

def on_mode_change():
    global mode_selected
    mode_selected = mode_var.get()
    apply_mode()  # áp dụng ngay
    # highlight không cần vì radiobutton đã tự thể hiện, nhưng nếu muốn đổi màu có thể chỉnh thủ công

# Radio button cho Mode 1
rb_mode1 = tk.Radiobutton(frame_mode, text="Mode 1: List mặc định",
                          variable=mode_var, value=1,
                          indicatoron=True, width=25,
                          command=on_mode_change)
rb_mode1.pack(pady=5)

# Radio button cho Mode 2
rb_mode2 = tk.Radiobutton(frame_mode, text="Mode 2: Nhập thủ công",
                          variable=mode_var, value=2,
                          indicatoron=True, width=25,
                          command=on_mode_change)
rb_mode2.pack(pady=5)

entry_custom_voltage = tk.Entry(frame_mode)
entry_custom_voltage.pack(pady=3)

# Áp dụng ngay khi nhấn Enter trong ô nhập điện áp
def on_custom_voltage_enter(event=None):
    if mode_selected == 2 and ser and ser.is_open:
        try:
            val = float(entry_custom_voltage.get().strip())
            set_voltage(val)
        except:
            messagebox.showerror("Lỗi", "Điện áp nhập không hợp lệ!")

entry_custom_voltage.bind("<Return>", on_custom_voltage_enter)

# --- Khối chọn số ô và ô nhập điện áp ---
frame_num_boxes = tk.Frame(root)
frame_num_boxes.pack(pady=5)
tk.Label(frame_num_boxes, text="🔢 Số ô điện áp:").pack(side="left", padx=5)
combo_num_boxes = ttk.Combobox(frame_num_boxes, width=5, values=[2,3,4,5,6,7,8,9,10])
combo_num_boxes.set(NUM_VOLTAGE_BOXES)
combo_num_boxes.pack(side="left", padx=5)

frame_mode1_boxes = tk.LabelFrame(root, text="Danh sách điện áp (Mode 1)")
frame_mode1_boxes.pack(pady=5)

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

combo_num_boxes.bind("<<ComboboxSelected>>", on_num_boxes_change)
build_voltage_entries(NUM_VOLTAGE_BOXES)

# highlight_mode()

# --- Nút điều chỉnh ---
frame_btn = tk.Frame(root)
frame_btn.pack(pady=10)

tk.Button(frame_btn, text="⬆ Tăng", width=10, command=increase_voltage).grid(row=0, column=1, padx=5, pady=5)
tk.Button(frame_btn, text="⬇ Giảm", width=10, command=decrease_voltage).grid(row=2, column=1, padx=5, pady=5)
tk.Button(frame_btn, text="◀ Bước-", width=10, command=step_prev).grid(row=1, column=0, padx=5, pady=5)
lbl_step = tk.Label(
    frame_btn,
    text=f"Bước: {voltage_step}",
    width=12,
    bg="#ffffcc",        # màu nền vàng nhạt để highlight
    relief="solid",      # kiểu viền: solid
    bd=1.2,                # độ dày viền
    font=("Arial", 12)
)
lbl_step.grid(row=1, column=1, padx=5, pady=5)
tk.Button(frame_btn, text="▶ Bước+", width=10, command=step_next).grid(row=1, column=2, padx=5, pady=5)

tk.Button(root, text="⏩ Điện áp kế tiếp", width=20, command=next_voltage).pack(pady=5)
tk.Button(root, text="🔄 Reset Mode", width=20, command=reset_mode).pack(pady=5)
# ==== NÚT CHECK UPDATE ====
tk.Button(root, text="🔄 Check for update", width=20, command=check_update).pack(pady=5)
# ==== END NÚT CHECK UPDATE ====
tk.Button(root, text="❌ Thoát", width=20, command=quit_app).pack(pady=5)

cfg = load_config()
if "com_port" in cfg:
    refresh_com_list()
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if cfg["com_port"] in ports:
        combo_com.set(cfg["com_port"])

root.mainloop()