# 🤖 Hướng dẫn sử dụng Telegram Bot

## Tổng quan

Telegram Bot cho phép bạn quản lý ghi chú trực tiếp từ Telegram với các tính năng:
- ➕ **Thêm ghi chú** với conversation flow
- 📋 **Xem tất cả ghi chú** với pagination
- ⏰ **Xem ghi chú sắp tới** (7 ngày tới)
- 🗑️ **Xóa ghi chú** với confirmation
- 📱 **Menu inline keyboard** dễ thao tác

## Cài đặt

### 1. Chuẩn bị Bot Token

Bot đã được tạo sẵn, chỉ cần có token trong file `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_API_URL=https://tele-api.cloudmini.net
```

### 2. Liên kết tài khoản

Để sử dụng bot, bạn cần liên kết Telegram ID với tài khoản:

1. Mở bot và gửi `/start`
2. Copy **Telegram ID** hiển thị trong tin nhắn chào mừng
3. Đăng nhập vào website
4. Vào **Cài đặt → Thông báo**
5. Nhập **Telegram ID** vào ô "Telegram Chat ID"
6. Nhấn **Lưu cài đặt**
7. Quay lại bot và thử các chức năng

**Cơ chế hoạt động:**
- Bot lưu `telegram_chat_id` vào database (bảng `users`)
- Khi user chat với bot → bot kiểm tra `telegram_chat_id` trong database
- Nếu chưa link → bot yêu cầu user vào website để nhập ID
- Sau khi link → mọi thao tác trên bot đều dùng account đã link

## Chạy Bot

### Development (Local)

```bash
# Kích hoạt virtual environment
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows

# Chạy bot
python run_telegram_bot.py
```

Bot sẽ chạy ở chế độ polling và nhận message từ Telegram.

### Production (Server)

#### Option 1: Chạy với systemd service

Tạo file `/etc/systemd/system/calendar-telegram-bot.service`:

```ini
[Unit]
Description=Calendar Telegram Bot
After=network.target mysql.service redis.service
Wants=mysql.service redis.service

[Service]
Type=simple
User=calendar
Group=calendar
WorkingDirectory=/var/www/calendar
Environment=PATH=/var/www/calendar/venv/bin
Environment=PYTHONPATH=/var/www/calendar
EnvironmentFile=/var/www/calendar/.env
ExecStart=/var/www/calendar/venv/bin/python /var/www/calendar/run_telegram_bot.py
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
TimeoutStartSec=30
TimeoutStopSec=10

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/var/www/calendar/logs /tmp

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=calendar-telegram-bot

[Install]
WantedBy=multi-user.target
```

**Quản lý service:**

```bash
# Enable và start
sudo systemctl enable calendar-telegram-bot
sudo systemctl start calendar-telegram-bot

# Kiểm tra trạng thái
sudo systemctl status calendar-telegram-bot

# Xem logs
sudo journalctl -u calendar-telegram-bot -f

# Restart
sudo systemctl restart calendar-telegram-bot

# Stop
sudo systemctl stop calendar-telegram-bot
```

#### Option 2: Chạy với screen/tmux

```bash
# Sử dụng screen
screen -S telegram-bot
python run_telegram_bot.py
# Nhấn Ctrl+A, D để detach

# Quay lại screen
screen -r telegram-bot

# Hoặc sử dụng tmux
tmux new -s telegram-bot
python run_telegram_bot.py
# Nhấn Ctrl+B, D để detach

# Quay lại tmux
tmux attach -t telegram-bot
```

## Sử dụng Bot

### Commands

> 💡 **Tip:** Các commands này cũng xuất hiện trong menu bot khi bạn gõ `/` trong ô chat.

| Command | Mô tả |
|---------|-------|
| `/start` | 🚀 Khởi động bot và xem menu |
| `/help` | ❓ Xem hướng dẫn sử dụng |
| `/add` | ➕ Thêm ghi chú mới |
| `/list` | 📋 Xem danh sách ghi chú |
| `/upcoming` | ⏰ Xem ghi chú sắp tới (7 ngày) |
| `/cancel` | ❌ Hủy thao tác hiện tại |

### Menu Chính

Sau khi gửi `/start`, bạn sẽ thấy menu với các nút:

```
➕ Thêm ghi chú    📋 Xem tất cả
⏰ Sắp tới         🔍 Tìm kiếm
       ℹ️ Trợ giúp
```

### Thêm Ghi Chú

1. Nhấn **"➕ Thêm ghi chú"** hoặc gửi `/add`
2. **Bước 1:** Nhập tiêu đề ghi chú
   ```
   Ví dụ: Đóng tiền nhà
   ```
3. **Bước 2:** Nhập nội dung (hoặc gửi `skip` để bỏ qua)
   ```
   Ví dụ: Đóng tiền nhà tháng 11, số tiền 5 triệu
   ```
4. **Bước 3:** Nhập ngày
   ```
   Định dạng: DD/MM/YYYY hoặc YYYY-MM-DD
   Ví dụ: 05/11/2025 hoặc 2025-11-05
   ```
5. **Bước 4:** Chọn có muốn thông báo không
   ```
   ✅ Có    ❌ Không
   ```
6. **Bước 5:** (Nếu chọn Có) Chọn kiểu lặp lại
   ```
   📅 Hàng tháng
   🔄 Hàng năm
   ❌ Không lặp
   ```
7. **Bước 6:** Chọn số ngày nhắc trước
   ```
   1 ngày
   3 ngày
   5 ngày
   7 ngày
   ```
8. **Hoàn tất!** Bot sẽ hiển thị thông tin ghi chú vừa tạo

### Xem Ghi Chú

**Xem tất cả:**
- Nhấn **"📋 Xem tất cả"** hoặc gửi `/list`
- Chọn ghi chú từ danh sách để xem chi tiết

**Xem sắp tới:**
- Nhấn **"⏰ Sắp tới"** hoặc gửi `/upcoming`
- Xem các ghi chú trong 7 ngày tới
- Hiển thị "Hôm nay", "Ngày mai", hoặc "Còn X ngày"

**Chi tiết ghi chú:**
- Chọn ghi chú từ danh sách
- Xem đầy đủ thông tin:
  - Tiêu đề & nội dung
  - Ngày dương & âm
  - Còn bao nhiêu ngày
  - Cài đặt thông báo

### Xóa Ghi Chú

1. Chọn ghi chú từ danh sách
2. Nhấn **"🗑️ Xóa"**
3. Xác nhận xóa
4. Ghi chú sẽ bị xóa vĩnh viễn (soft delete)

### Hủy Thao Tác

Trong quá trình thêm ghi chú, gửi `/cancel` để hủy và quay lại menu.

## Icon Meanings

| Icon | Ý nghĩa |
|------|---------|
| 📝 | Ghi chú thường (không có thông báo) |
| 🔔 | Ghi chú có thông báo |
| 📅 | Ghi chú lặp hàng tháng |
| 🔄 | Ghi chú lặp hàng năm |
| ⏰ | Ghi chú sắp tới |
| ✅ | Xác nhận/Thành công |
| ❌ | Hủy/Lỗi |
| ⚠️ | Cảnh báo |

## Troubleshooting

### Bot không phản hồi

**Nguyên nhân:** Bot chưa chạy hoặc token sai

**Giải pháp:**
```bash
# Kiểm tra bot có chạy không
ps aux | grep run_telegram_bot

# Kiểm tra logs
sudo journalctl -u calendar-telegram-bot -n 50

# Restart bot
sudo systemctl restart calendar-telegram-bot
```

### "Bạn chưa liên kết tài khoản"

**Nguyên nhân:** Telegram ID chưa được thêm vào tài khoản

**Giải pháp:**
1. Copy Telegram ID từ bot (`/start`)
2. Đăng nhập website → Cài đặt → Thông báo
3. Nhập Telegram ID và lưu

### Bot bị crash

**Kiểm tra logs:**
```bash
# Xem 100 dòng log cuối
sudo journalctl -u calendar-telegram-bot -n 100

# Xem log real-time
sudo journalctl -u calendar-telegram-bot -f

# Xem log lỗi
sudo journalctl -u calendar-telegram-bot -p err
```

**Restart bot:**
```bash
sudo systemctl restart calendar-telegram-bot
```

### Database connection error

**Kiểm tra:**
```bash
# Kiểm tra MySQL có chạy không
sudo systemctl status mysql

# Kiểm tra connection string trong .env
cat /var/www/calendar/.env | grep DATABASE_URL
```

## Best Practices

### 1. **Đặt tên ghi chú rõ ràng**
   ```
   ✅ Đóng tiền nhà tháng 11
   ❌ Nhà
   ```

### 2. **Sử dụng thông báo hợp lý**
   - Sự kiện quan trọng: 5-7 ngày trước
   - Sự kiện thường: 3 ngày trước
   - Nhắc nhở nhanh: 1 ngày trước

### 3. **Lặp lại thông minh**
   - **Hàng tháng:** Đóng tiền, họp định kỳ
   - **Hàng năm:** Sinh nhật, kỷ niệm
   - **Không lặp:** Sự kiện một lần

### 4. **Xem ghi chú thường xuyên**
   - Dùng `/upcoming` để xem việc cần làm
   - Xóa ghi chú đã hoàn thành

## Security

- ⚠️ **Không chia sẻ Bot Token**
- 🔒 Bot chỉ xử lý tin nhắn từ user đã liên kết
- 🛡️ Dữ liệu được mã hóa trong database
- 🚫 Bot không lưu trữ tin nhắn

## 🔧 Triển khai Settings Page (cho Dev)

### Thêm route `/settings/telegram`

```python
# app/routes/settings.py
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.database import SessionLocal
from app.models.user import User

@app.route('/settings/telegram', methods=['GET', 'POST'])
@login_required
def telegram_settings():
    if request.method == 'POST':
        telegram_id = request.form.get('telegram_chat_id', '').strip()
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == current_user.id).first()
            
            if telegram_id:
                # Kiểm tra ID đã được dùng chưa
                existing = db.query(User).filter(
                    User.telegram_chat_id == telegram_id,
                    User.id != current_user.id
                ).first()
                
                if existing:
                    flash('❌ Telegram ID này đã được liên kết với tài khoản khác!', 'danger')
                else:
                    user.telegram_chat_id = telegram_id
                    user.telegram_notifications = True
                    db.commit()
                    flash('✅ Đã liên kết Telegram thành công!', 'success')
            else:
                # Xóa liên kết
                user.telegram_chat_id = None
                user.telegram_notifications = False
                db.commit()
                flash('ℹ️ Đã hủy liên kết Telegram', 'info')
        
        except Exception as e:
            db.rollback()
            flash(f'❌ Lỗi: {str(e)}', 'danger')
        finally:
            db.close()
        
        return redirect(url_for('telegram_settings'))
    
    return render_template('settings/telegram.html')
```

### Template `templates/settings/telegram.html`

```html
{% extends "base.html" %}
{% block content %}
<div class="container mt-5">
    <h2>⚙️ Cài đặt Telegram Bot</h2>
    
    <div class="card mt-3">
        <div class="card-body">
            <h5>🔗 Liên kết tài khoản Telegram</h5>
            
            <div class="alert alert-info">
                <strong>📱 Cách lấy Telegram ID:</strong>
                <ol>
                    <li>Mở Telegram và tìm bot</li>
                    <li>Gửi lệnh <code>/start</code></li>
                    <li>Bot sẽ hiển thị Telegram ID của bạn</li>
                    <li>Copy ID và dán vào ô bên dưới</li>
                </ol>
            </div>
            
            <form method="POST">
                <div class="mb-3">
                    <label for="telegram_chat_id" class="form-label">Telegram ID</label>
                    <input 
                        type="text" 
                        class="form-control" 
                        id="telegram_chat_id"
                        name="telegram_chat_id"
                        value="{{ current_user.telegram_chat_id or '' }}"
                        placeholder="Ví dụ: 123456789"
                    >
                </div>
                
                {% if current_user.telegram_chat_id %}
                <div class="alert alert-success">
                    ✅ Đã liên kết với Telegram ID: <code>{{ current_user.telegram_chat_id }}</code>
                </div>
                {% endif %}
                
                <button type="submit" class="btn btn-primary">💾 Lưu cài đặt</button>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

## ❓ FAQ

**Q: Một Telegram ID có thể link nhiều tài khoản không?**  
A: Không, để bảo mật mỗi ID chỉ link 1 account.

**Q: User quên Telegram ID của mình?**  
A: Gửi `/start` cho bot, bot sẽ hiển thị ID.

**Q: User đổi Telegram account thì sao?**  
A: Vào web Settings, xóa ID cũ và nhập ID mới.

## Tính năng sắp có

- [ ] ✏️ Sửa ghi chú qua bot
- [ ] 🔍 Tìm kiếm ghi chú
- [ ] 📊 Thống kê ghi chú
- [ ] 🖼️ Đính kèm hình ảnh
- [ ] 🔗 Liên kết với Google Calendar

## Support

Gặp vấn đề? Liên hệ:
- 📧 Email: support@minhhungtsbd.me
- 🌐 Website: https://calendar.minhhungtsbd.me

---

**Made with ❤️ by Calendar Team**
