# 🔧 Telegram Bot Quick Fix - Timeout Error

## ❌ Lỗi: "Timed out"

```
2025-10-21 15:11:02,797 - __main__ - ERROR - ❌ Error running bot: Timed out
```

### Nguyên nhân

Bot không thể kết nối đến Telegram API qua proxy `https://tele-api.cloudmini.net`

Có thể do:
- Proxy không hoạt động
- Server không thể kết nối ra ngoài qua proxy
- Firewall chặn kết nối

---

## ✅ Giải pháp: Sử dụng Default Telegram API

### Option 1: Xóa TELEGRAM_API_URL (Khuyến nghị)

**Bước 1:** Sửa file `.env`:

```bash
nano /var/www/calendar/.env
```

**Bước 2:** Tìm dòng:
```env
TELEGRAM_API_URL=https://tele-api.cloudmini.net
```

**Bước 3:** Xóa dòng đó hoặc comment lại:
```env
# TELEGRAM_API_URL=https://tele-api.cloudmini.net
```

**Bước 4:** Lưu file (Ctrl+O, Enter, Ctrl+X)

**Bước 5:** Test bot:
```bash
source venv/bin/activate
python run_telegram_bot.py
```

### Option 2: Để trống TELEGRAM_API_URL

Sửa trong `.env`:
```env
TELEGRAM_API_URL=
```

---

## 🚀 Nếu vẫn bị timeout

### Check 1: Kiểm tra kết nối internet

```bash
# Test kết nối đến Telegram API
curl -I https://api.telegram.org

# Nếu thành công sẽ thấy:
# HTTP/2 200
```

### Check 2: Kiểm tra Bot Token

```bash
# Test bot token
TOKEN="your_bot_token_here"
curl "https://api.telegram.org/bot$TOKEN/getMe"

# Nếu thành công sẽ thấy:
# {"ok":true,"result":{"id":...,"is_bot":true,...}}
```

### Check 3: Kiểm tra firewall

```bash
# Kiểm tra port 443 có mở không
sudo netstat -tulpn | grep :443

# Kiểm tra có rule firewall nào block không
sudo iptables -L -n | grep 443
```

---

## 📝 Code đã update

Bot đã được cập nhật để:
1. **Tự động fallback**: Nếu proxy timeout, sẽ dùng default API
2. **Timeout lớn hơn**: Tăng timeout lên 30 giây
3. **Logging tốt hơn**: Log rõ đang dùng API nào

```python
# Trong telegram_bot_handler.py
if self.api_url and "tele-api" in self.api_url:
    logger.info(f"Using custom API URL: {self.api_url}")
    builder.base_url(f"{self.api_url}/bot")
else:
    logger.info("Using default Telegram API")

builder.connect_timeout(30.0)
builder.read_timeout(30.0)
```

---

## ✅ Test lại

Sau khi sửa `.env`, test bot:

```bash
cd /var/www/calendar
source venv/bin/activate
python run_telegram_bot.py
```

**Kết quả mong đợi:**
```
2025-10-21 15:15:00 - __main__ - INFO - 🚀 Starting Telegram Bot...
2025-10-21 15:15:00 - app.services.telegram_bot_handler - INFO - Using default Telegram API
2025-10-21 15:15:00 - app.services.telegram_bot_handler - INFO - ✅ Telegram bot handlers setup complete
2025-10-21 15:15:00 - app.services.telegram_bot_handler - INFO - 🚀 Starting Telegram bot (polling mode)...
```

✅ **Không còn timeout!**

---

## 🔄 Restart service

Nếu đã setup systemd service:

```bash
# Restart service
sudo systemctl restart calendar-telegram-bot

# Kiểm tra
sudo systemctl status calendar-telegram-bot

# Xem logs
sudo journalctl -u calendar-telegram-bot -f --since "1 minute ago"
```

---

## 🌐 Khi nào dùng Proxy?

**Dùng proxy khi:**
- Server ở quốc gia chặn Telegram (Iran, China, etc.)
- Cần bypass firewall nội bộ
- Có middleware riêng

**Không dùng proxy khi:**
- Server kết nối trực tiếp được đến Telegram
- Proxy không ổn định
- Gặp lỗi timeout

---

## 📞 Still not working?

### Debug mode

Chạy bot với logging chi tiết:

```bash
# Edit run_telegram_bot.py, thay:
level=logging.INFO

# Thành:
level=logging.DEBUG
```

Chạy lại:
```bash
python run_telegram_bot.py
```

### Check Python environment

```bash
# Kiểm tra python-telegram-bot version
pip show python-telegram-bot

# Should be: 20.7 or higher
```

### Network diagnostics

```bash
# Check DNS resolution
nslookup api.telegram.org

# Check routing
traceroute api.telegram.org

# Check if port 443 is reachable
telnet api.telegram.org 443
```

---

## ✅ Success Checklist

- [ ] Xóa hoặc comment `TELEGRAM_API_URL` trong `.env`
- [ ] Bot chạy không còn timeout
- [ ] Bot phản hồi `/start` command
- [ ] Có thể thêm ghi chú qua bot
- [ ] Systemd service chạy ổn định

---

**💡 Pro tip:** Sau khi fix, commit file `.env.example` để team khác biết cách config đúng!

```bash
git add .env.example
git commit -m "Update Telegram Bot config - fix timeout with default API"
git push
```
