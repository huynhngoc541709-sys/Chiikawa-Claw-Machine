# 🚀 Hướng Dẫn Deploy Game Chiikawa Claw Machine Lên Internet

Dự án đã được cấu hình hoàn chỉnh để chạy Production với **Flask + Flask-SocketIO + Gunicorn (gthread multithreaded worker)** hỗ trợ kết nối realtime WebSocket hai chiều qua Internet.

---

## 🌐 Các Lựa Chọn Nhận PUBLIC URL (Không dùng localhost)

### 🌟 CÁCH 1: Nhận PUBLIC URL Tức Thì Trong 5 Giây (Không cần tạo tài khoản)
Dùng khi bạn muốn bạn bè truy cập và chơi cùng bạn ngay lập tức trên Internet từ máy tính của bạn:

1. Chạy game ở máy của bạn: nhấp đúp file `run.bat` (hoặc chạy `python server.py`).
2. Mở file `start_public_tunnel.bat` (hoặc mở PowerShell gõ lệnh):
   ```powershell
   ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:5000 a.pinggy.io
   ```
3. Màn hình sẽ hiển thị ngay một **PUBLIC HTTPS URL**, ví dụ:
   ```
   https://a9f3-113-161-xx-xx.a.free.pinggy.link
   ```
4. **Copy link này gửi cho bất kỳ ai trên thế giới**: Họ sẽ truy cập trực tiếp vào máy gắp thú Chiikawa của bạn với đầy đủ tính năng Socket.IO realtime, tạo phòng và chơi cùng nhau!

---

### 🌟 CÁCH 2: Deploy Cloud Vĩnh Viễn Trên Render.com (Miễn phí 100%, có URL https://ten-ban.onrender.com)
Render hỗ trợ WebSockets bản quyền cho Socket.IO cực kỳ mượt mà.

#### Bước 1: Đưa code lên GitHub
1. Tạo một repository mới trên [github.com](https://github.com/new) (ví dụ: `chiikawa-claw-machine`).
2. Trong thư mục dự án trên máy tính, chạy:
   ```powershell
   git init
   git add .
   git commit -m "Deploy Chiikawa Claw Machine"
   git branch -M main
   git remote add origin https://github.com/<tai-khoan-cua-ban>/chiikawa-claw-machine.git
   git push -u origin main
   ```

#### Bước 2: Tạo Web Service trên Render
1. Đăng nhập [render.com](https://render.com) (đăng nhập bằng tài khoản GitHub).
2. Bấm nút **New +** -> Chọn **Web Service**.
3. Chọn repository `chiikawa-claw-machine` vừa push.
4. Cấu hình các thông số (Render sẽ tự nhận diện theo file `render.yaml` và `Procfile` đã tạo):
   - **Name**: `chiikawa-claw-machine` (hoặc tên bạn thích)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --worker-class gthread -w 1 --threads 100 --bind 0.0.0.0:$PORT server:app`
   - **Instance Type**: `Free`
5. Bấm **Create Web Service**.

Sau khoảng 1 - 2 phút, Render sẽ cấp cho bạn một **PUBLIC URL vĩnh viễn** có dạng:
```
https://chiikawa-claw-machine.onrender.com
```
👉 Bạn có thể gửi link này cho bất kỳ ai, game sẽ luôn hoạt động 24/7 trên Internet!

---

### 🌟 CÁCH 3: Deploy Bằng Docker (Railway / Fly.io / Koyeb)
Dự án đã có sẵn file `Dockerfile` chuẩn production:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=5000
EXPOSE 5000
CMD ["gunicorn", "--worker-class", "gthread", "-w", "1", "--threads", "100", "--bind", "0.0.0.0:5000", "server:app"]
```

- **Trên Railway**: Chỉ cần kết nối repo GitHub, Railway sẽ tự động build từ `Dockerfile` hoặc `railway.json` và tạo URL:
  `https://chiikawa-claw-machine.up.railway.app`
- **Trên Fly.io**: Gõ `fly launch` -> `fly deploy` để nhận URL:
  `https://chiikawa-claw-machine.fly.dev`

---

## 🔍 Kiểm Tra Kỹ Thuật Trước Khi Deploy

- ✅ **CORS**: Đã cấu hình `cors_allowed_origins="*"` và header `Access-Control-Allow-Origin: *` trên server, tương thích mọi tên miền công khai.
- ✅ **WebSocket Transports**: Frontend tự động kết nối qua `['websocket', 'polling']` dựa trên `window.location.origin`, tự nâng cấp lên `wss://` khi chạy trên giao thức `https://`.
- ✅ **Khả năng chịu tải**: `gunicorn -w 1 --threads 100` đảm bảo tất cả kết nối Socket.IO chia sẻ chung bộ nhớ phòng chơi và xoay lượt ổn định mà không bị phân mảnh process.
