# ✨ Chiikawa Claw Machine - Máy Gắp Thú Online ♡

Hệ thống game Máy Gắp Thú Chiikawa hỗ trợ chơi Đơn (Solo) & Chơi Nhiều Người (Multiplayer) qua Socket.IO với đầy đủ các tính năng theo đặc tả kỹ thuật:

---

### 17. 🪙 COINS (Hệ thống Xu)
- Mỗi người chơi bắt đầu với **10 xu**.
- Mỗi lượt gắp: **-1 xu**.
- Khi hết xu (`coins <= 0`), nếu người chơi cố bấm gắp, modal xuất hiện:
  > **"Hết xu rồi! 🥺"**  
  > `[ NHẬN 5 XU ]`
- Tặng ngay **+5 xu** miễn phí, không yêu cầu thanh toán thật.

---

### 18. 📖 COLLECTION (Bộ Sưu Tập ♡)
- Màn hình: **BỘ SƯU TẬP ♡**
- Tiến độ: `X / 20` có progress bar trực quan (ví dụ: `3 / 20 (15%)`).
- Thẻ nhân vật:
  - Nếu đã bắt: Hiển thị hình ảnh gấu bông SVG dễ thương, tên nhân vật, độ hiếm (`THƯỜNG`, `HIẾM`, `HUYỀN THOẠI`), và số lần bắt (`Đã bắt ×N`).
  - Nếu chưa bắt: Hiển thị thẻ bóng mờ bí ẩn `???` và nhãn `CHƯA MỞ KHÓA`.
- Bộ lọc: *Tất cả (20)*, *Đã mở khóa*, *Chưa mở khóa*, *🌟 Huyền Thoại*.

---

### 19. 🎁 DAILY REWARD (Quà Hằng Ngày)
- Chuỗi quà đăng nhập hằng ngày:
  - **Ngày 1**: +3 xu
  - **Ngày 2**: +5 xu
  - **Ngày 3**: +7 xu
  - **Ngày 4+**: +10 xu
- Lưu trữ qua `localStorage` (`streak`, `lastClaimDate`).
- Nhận biết streak liên tục, nếu bỏ lỡ sẽ tính lại từ đầu chu kỳ. Có huy hiệu thông báo `MỚI!` khi có quà.

---

### 20. ✨ SUCCESS ANIMATION (Hiệu Ứng Bắt Thành Công)
- Khi bắt thành công:
  - Header: `✨ ✨ ✨`
  - Tiêu đề: **GẮP ĐƯỢC RỒI!**
  - Tên gấu: `🧸 MOMONGA 🧸` (hoặc tên nhân vật tương ứng)
  - Phụ đề: *"Đã thêm vào bộ sưu tập!"*
  - Hiệu ứng: **Confetti canvas**, **Sparkle (lấp lánh)**, **Heart (trái tim bay)**, **Plushie bounce** (nảy tưng tưng dễ thương).
- Nếu bắt được bé **HUYỀN THOẠI**:
  - Header: `🌟 🌟 🌟 🌟 🌟`
  - Tiêu đề: **GẮP ĐƯỢC BÉ HUYỀN THOẠI!**
  - Hiệu ứng đặc biệt: Hào quang xoay nhiều màu (Rainbow Halo Aura), pháo hoa giấy đa tầng và nhạc chuông rạng rỡ đặc biệt.

---

### 21. 🔊 SOUND (Hệ Thống Âm Thanh Web Audio API)
- Tổng hợp âm thanh đa tần số chân thực không phụ thuộc vào file MP3 ngoài:
  - `click sound`: Âm click/pop UI
  - `claw movement`: Tiếng mô-tơ/bánh răng di chuyển
  - `drop`: Tiếng rít hạ càng gắp
  - `grab`: Tiếng kẹp càng gắp cơ khí
  - `success`: Điệp khúc chiến thắng vui tươi (Arpeggio C5-E5-G5-C6)
  - `failure`: Tiếng lò xo tưng trượt ngộ nghĩnh
  - `coin`: Tiếng leng keng đồng xu
  - `legendary`: Hợp âm thiên thần lấp lánh (Celestial Arpeggio)
- Nút chuyển đổi trạng thái:
  - `🔊 ÂM THANH BẬT`
  - `🔇 ÂM THANH TẮT`
- Không autoplay nhạc nền lớn, hoàn toàn tôn trọng người dùng.

---

### 22. 💾 LOCAL STORAGE (Lưu Trữ Bền Vững)
- Tự động lưu và đồng bộ:
  - `chiikawa_coins`
  - `chiikawa_collection`
  - `chiikawa_daily_reward`
  - `chiikawa_sound_enabled`
  - `chiikawa_player_name`
  - `chiikawa_last_room`
- Refresh trang web **không mất dữ liệu**!

---

### 23. 🔄 RECONNECT (Khôi Phục Kết Nối Socket.IO)
- Socket.IO tự động thử kết nối lại (`reconnection: true`, `reconnectionDelay: 1000`).
- Nếu người chơi mất mạng:
  - Giữ vị trí người chơi trong phòng trong thời gian ân hạn (`DISCONNECT_GRACE_PERIOD = 50s`).
  - Các người chơi khác thấy thông báo: `[Mất mạng ⏳]`.
- Khi người chơi kết nối lại:
  - Gửi event `reconnect_player`, khôi phục trọn vẹn:
    - `room`
    - `player`
    - `gameState`
    - `currentTurn`
    - `claw` (tọa độ hiện tại)
    - `players`
  - **Không reset phòng**.
- Nếu mất kết nối quá thời gian chờ:
  - Loại người chơi khỏi phòng.
- Nếu người chơi bị mất kết nối đang trong lượt của mình:
  - Chuyển lượt tự động sang người kế tiếp sau thời gian chờ (tránh kẹt phòng).

---

## Hướng dẫn Chạy Game

1. Mở PowerShell hoặc Command Prompt tại thư mục dự án:
   ```powershell
   cd "C:\Users\HUYNH BAO NGOC\.gemini\antigravity\scratch\chiikawa_claw_machine"
   ```
2. Cài đặt thư viện (nếu cần):
   ```powershell
   pip install -r requirements.txt
   ```
3. Chạy server:
   ```powershell
   python server.py
   # hoặc nhấp đúp file run.bat
   ```
4. Mở trình duyệt và truy cập:
   ```
   http://127.0.0.1:5000
   ```
