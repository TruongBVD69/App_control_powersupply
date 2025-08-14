# Power Supply Control GUI

Ứng dụng Python dùng giao diện Tkinter để điều khiển nguồn điện (ví dụ GPP-3323, Keysight E3646A...) qua cổng serial.  
Cho phép:
- Chọn thiết bị từ danh sách (combobox)
- Nhập các thông số điện áp, dòng điện
- Bật/tắt output
- Lưu và tải cấu hình từ file JSON

---

## 1. Yêu cầu hệ thống

- Python 3.8+
- Các thư viện Python:
  ```bash
  pip install pyserial
  ```
  *(Tkinter thường có sẵn trong Python, nếu chưa có thì cài thêm theo hướng dẫn của hệ điều hành)*

---

## 2. Cấu trúc chương trình

- `main.py` — code chính, tạo giao diện và xử lý kết nối thiết bị.
- `config.json` — file lưu cấu hình đã chọn (tự động tạo sau khi bạn lưu).
- Các hàm chính:
  - `save_config()` — lưu cấu hình hiện tại vào `config.json`
  - `load_config()` — đọc cấu hình từ file và áp dụng lên UI
  - `apply_config_to_ui(config)` — cập nhật giao diện từ cấu hình
  - `on_device_change()` — cập nhật loại thiết bị khi chọn từ combobox
  - `connect_device()` — kết nối với thiết bị dựa trên lựa chọn

---

## 3. Cách chạy

1. **Clone hoặc copy code** vào một thư mục.
2. Cài thư viện:
   ```bash
   pip install pyserial
   ```
3. Chạy chương trình:
   ```bash
   python main.py
   ```
4. Chọn **Device** từ combobox (ví dụ: `GPP-3323` hoặc `Keysight`).
5. Chọn **cổng COM** phù hợp với thiết bị.
6. Nhấn **Connect** để kết nối.

---

## 4. Lưu và tải cấu hình

- Để lưu cấu hình:  
  Chọn thiết bị, thông số… rồi nhấn **Save Config**.
- Để tải lại cấu hình:  
  Nhấn **Load Config** — chương trình sẽ tự động set giá trị từ file `config.json`.

---
