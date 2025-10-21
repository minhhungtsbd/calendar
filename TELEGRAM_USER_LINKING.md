# 🔗 Liên kết tài khoản Telegram với Web App

## 📖 Tổng quan

Bot Telegram cần liên kết với tài khoản người dùng trên website để:
- Xác thực user và bảo mật dữ liệu
- Hiển thị đúng ghi chú của từng user
- Gửi thông báo đúng người

---

## 🔄 Cơ chế hoạt động

### 1. **User Model** đã có sẵn field `telegram_chat_id`

```python
# app/models/user.py
class User(Base):
    ...
    telegram_chat_id = Column(String(100), nullable=True)  # Lưu Telegram User ID
    telegram_notifications = Column(Boolean, default=False)
```

### 2. **Bot kiểm tra user khi thao tác**

Khi user gửi command `/add` hoặc thao tác khác:

```python
# app/services/telegram_bot_handler.py (line 193-209)
db = SessionLocal()
user = self.get_user_by_telegram_id(db, update.effective_user.id)

if not user:
    # Yêu cầu user liên kết tài khoản
    await message.reply_text(
        "❌ Bạn chưa liên kết tài khoản!\n"
        f"📱 Telegram ID: {update.effective_user.id}\n"
        "Vui lòng đăng nhập website và nhập ID này vào phần Cài đặt."
    )
    return ConversationHandler.END
```

---

## 🛠️ Các bước triển khai

### **Bước 1: Thêm tính năng liên kết trên Web App**

Cần tạo trang **Settings** cho user nhập Telegram ID:

#### File: `app/routes/settings.py` (mới tạo hoặc edit)

```python
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.database import SessionLocal

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

#### Template: `templates/settings/telegram.html`

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
                    <li>Mở Telegram và tìm bot: <code>@YourBotName</code></li>
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
                    <small class="text-muted">
                        Để trống để hủy liên kết
                    </small>
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
    
    <div class="card mt-3">
        <div class="card-body">
            <h5>📖 Hướng dẫn sử dụng Bot</h5>
            <ul>
                <li><code>/start</code> - Khởi động bot</li>
                <li><code>/add</code> - Thêm ghi chú</li>
                <li><code>/list</code> - Xem danh sách ghi chú</li>
                <li><code>/upcoming</code> - Xem ghi chú sắp tới</li>
                <li><code>/help</code> - Xem trợ giúp</li>
            </ul>
        </div>
    </div>
</div>
{% endblock %}
```

---

### **Bước 2: Thêm link vào menu Settings**

Trong navbar/sidebar, thêm:

```html
<a href="{{ url_for('telegram_settings') }}" class="nav-link">
    📱 Telegram Bot
</a>
```

---

### **Bước 3: Migration database (nếu chưa có field)**

Field `telegram_chat_id` đã có trong model, nhưng nếu database chưa có:

```bash
# Tạo migration
alembic revision --autogenerate -m "Add telegram_chat_id to users"

# Chạy migration
alembic upgrade head
```

---

## 🔐 Bảo mật

### 1. **Validate Telegram ID**

```python
def validate_telegram_id(telegram_id: str) -> bool:
    """Kiểm tra Telegram ID hợp lệ (số nguyên dương)"""
    try:
        int(telegram_id)
        return len(telegram_id) >= 5 and len(telegram_id) <= 15
    except ValueError:
        return False
```

### 2. **Unique constraint**

Đảm bảo một Telegram ID chỉ link với 1 tài khoản:

```python
# Check trong database
existing = db.query(User).filter(
    User.telegram_chat_id == telegram_id,
    User.id != current_user.id
).first()
```

---

## 🧪 Test flow

### 1. **User chưa liên kết**
```
User: /start
Bot: ❌ Bạn chưa liên kết tài khoản!
     📱 Telegram ID: 123456789
     Vui lòng đăng nhập website và nhập ID này.
```

### 2. **User liên kết trên web**
- Đăng nhập website
- Vào Settings → Telegram Bot
- Nhập Telegram ID: `123456789`
- Lưu

### 3. **User sử dụng bot**
```
User: /start
Bot: 👋 Xin chào John!
     🗓️ Chào mừng đến với Lịch Âm Dương Bot
     [Menu buttons hiển thị]

User: /add
Bot: 📝 Nhập tiêu đề ghi chú:
User: Họp team
Bot: 💬 Nhập nội dung...
```

---

## 🚀 Tính năng nâng cao (tùy chọn)

### 1. **Auto-register qua OTP/Token**

Thay vì nhập ID thủ công, tạo token từ web:

```python
# User click "Link Telegram" trên web → tạo token
token = secrets.token_urlsafe(16)  # abc123xyz
redis.setex(f"telegram_link:{token}", 300, user_id)  # Expire 5 phút

# User gửi token cho bot
User: /link abc123xyz
Bot: ✅ Đã liên kết thành công với tài khoản john@example.com
```

### 2. **Deep linking**

Tạo link từ web app:

```html
<a href="https://t.me/YourBot?start=link_{{ link_token }}" class="btn btn-primary">
    🔗 Liên kết Telegram
</a>
```

Bot nhận token từ `/start link_abc123`:

```python
async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args  # ['link_abc123']
    
    if args and args[0].startswith('link_'):
        token = args[0].replace('link_', '')
        # Verify token và link account
        ...
```

---

## 📊 Monitoring

Log các sự kiện quan trọng:

```python
logger.info(f"User {user.email} linked Telegram ID: {telegram_id}")
logger.warning(f"Telegram ID {telegram_id} tried to link to multiple accounts")
logger.error(f"Invalid Telegram ID format: {telegram_id}")
```

---

## ❓ FAQ

**Q: User quên Telegram ID của mình?**  
A: Gửi `/start` cho bot, bot sẽ hiển thị ID.

**Q: Một Telegram ID có thể link nhiều tài khoản không?**  
A: Không, để bảo mật mỗi ID chỉ link 1 account.

**Q: User đổi Telegram account thì sao?**  
A: Vào web Settings, xóa ID cũ và nhập ID mới.

**Q: Bot bị hack, lấy được Telegram ID?**  
A: Telegram ID là public, không nhạy cảm. Quan trọng là validate đúng user qua database.

---

## 📝 Checklist triển khai

- [ ] Thêm route `/settings/telegram` vào Flask app
- [ ] Tạo template `settings/telegram.html`
- [ ] Thêm link Settings vào navbar
- [ ] Test flow: web → bot → add note
- [ ] Validate Telegram ID format
- [ ] Check unique constraint
- [ ] Add logging
- [ ] Update TELEGRAM_BOT_GUIDE.md
- [ ] Test edge cases (ID invalid, duplicate, etc.)

---

✅ **Hoàn thành!** User giờ có thể link Telegram và quản lý ghi chú qua bot.
