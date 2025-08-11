import tkinter as tk
import win32com.client
import speech_recognition as sr
from tkinter import messagebox

# Kết nối tới Excel
try:
    excel = win32com.client.GetActiveObject("Excel.Application")
    excel.Visible = True
    wb = excel.ActiveWorkbook
    ws = excel.ActiveSheet
except Exception as e:
    messagebox.showerror("Lỗi", f"Không tìm thấy Excel hoặc file chưa mở:\n{e}")
    exit()

r = sr.Recognizer()

# Từ điển số tiếng Việt cơ bản
num_dict = {
    "không": "0", "một": "1", "mốt": "1", "hai": "2", "ba": "3", "bốn": "4",
    "tư": "4", "năm": "5", "lăm": "5", "sáu": "6", "bảy": "7", "bẩy": "7",
    "tám": "8", "chín": "9",
}

def text_to_number(text):
    text = text.lower().strip()

    # Thay các từ và dấu phẩy thật thành dấu chấm
    for word in ["chấm", "phẩy", "phay", "phảy", "dấu chấm", "dấu phẩy", "dấu phay"]:
        text = text.replace(word, ".")
    text = text.replace(",", ".")

    tokens = text.split()
    result_tokens = []
    for tok in tokens:
        if tok in num_dict:
            result_tokens.append(num_dict[tok])
        elif tok == ".":
            result_tokens.append(".")
        else:
            filtered = "".join(c for c in tok if c.isdigit() or c in [".", "-"])
            if filtered:
                result_tokens.append(filtered)

    # Nếu có nhiều hơn 1 nhóm số mà không có dấu chấm → bỏ qua
    num_groups = [t for t in result_tokens if t != "."]
    if "." not in result_tokens and len(num_groups) > 1:
        print(f"⚠ Bỏ qua vì nhiều nhóm số không có dấu chấm: {result_tokens}")
        return None

    result = "".join(result_tokens)

    try:
        if result.count(".") <= 1 and result not in ["", ".", "-", "-.", ".-"]:
            if "." in result:
                final_value = float(result)
            else:
                final_value = int(result)
            return final_value
        else:
            return None
    except:
        return None



def listen_and_write():
    try:
        with sr.Microphone() as source:
            lbl_status.config(text="🎤 Đang nghe...")
            root.update_idletasks()
            audio = r.listen(source)

        text = r.recognize_google(audio, language="vi-VN").strip()
        lbl_status.config(text=f"Bạn nói: {text}")
        print(f"Bạn nói: {text}")  # Log ra console

        number = text_to_number(text)
        if number is not None:
            print(f"➡ Sẽ điền vào Excel: {number}")  # Log ra console
            ws.Application.ActiveCell.Value = number
            ws.Application.ActiveCell.Offset(0, 2).Select()
        else:
            lbl_status.config(text="Không nhận dạng được số hợp lệ!")

    except Exception as e:
        lbl_status.config(text=f"Lỗi: {e}")



# Tạo GUI
root = tk.Tk()
# Cố định kích thước cửa sổ, ví dụ 800x600
root.geometry("310x100")

# Không cho thay đổi kích thước (cố định cả chiều ngang và dọc)
root.resizable(True, True)
root.title("Điền Excel bằng giọng nói")

lbl_status = tk.Label(root, text="Nhấn nút để bắt đầu nói")
lbl_status.pack(padx=10, pady=10)

btn_listen = tk.Button(root, text="🎤 Nói", command=listen_and_write)
btn_listen.pack(padx=10, pady=10)

root.mainloop()

