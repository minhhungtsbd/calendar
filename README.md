# 🗓️ Lịch Âm Dương - Calendar Application

Ứng dụng web quản lý lịch âm dương với tính năng ghi chú và thông báo tự động được xây dựng bằng FastAPI, HTMX, và TailwindCSS.

## ✨ Tính năng chính

### 📅 Lịch Âm Dương
- Hiển thị lịch tháng với cả ngày dương và ngày âm
- Chuyển đổi tự động giữa lịch dương và lịch âm
- Hiển thị các ngày lễ âm lịch quan trọng
- **🇻🇳 Tích hợp Google Calendar API để hiển thị ngày lễ quốc gia Việt Nam**
- Giao diện responsive hỗ trợ desktop và mobile
- Dark/Light mode

### 📝 Quản lý Ghi chú
- Tạo, chỉnh sửa, xóa ghi chú
- Gắn ghi chú với ngày dương hoặc ngày âm
- Hiển thị ghi chú trực tiếp trên lịch
- Tìm kiếm và lọc ghi chú

### 🔔 Thông báo Tự động
- Nhắc nhở trước 1, 2, 3 ngày (có thể tùy chỉnh)
- Gửi thông báo qua Telegram Bot
- Gửi thông báo qua Email (SMTP)
- Quản lý trạng thái thông báo
- Background tasks với Celery + Redis

### 🎨 Giao diện
- HTMX cho tương tác động không cần reload
- TailwindCSS cho giao diện đẹp, hiện đại
- Responsive design
- Dark/Light mode toggle
- Loading indicators và animations

## 🛠️ Công nghệ sử dụng

### Backend
- **FastAPI** - Web framework hiện đại, nhanh
- **SQLAlchemy** - ORM cho Python
- **MySQL** - Cơ sở dữ liệu chính
- **Celery + Redis** - Background tasks và message broker
- **LunarDate** - Thư viện chuyển đổi lịch âm dương
- **Google Calendar API** - Tích hợp ngày lễ quốc gia

### Frontend
- **HTMX** - Tương tác động không cần JavaScript phức tạp
- **TailwindCSS** - CSS framework utility-first
- **Jinja2** - Template engine

### Thông báo
- **python-telegram-bot** - Telegram Bot API
- **SMTP** - Email notifications
- **Mailgun** - Email service (tùy chọn)

## 📦 Cài đặt và Chạy

### Yêu cầu hệ thống
- Python 3.11+
- MySQL 8.0+
- Redis 7+
- Docker & Docker Compose (tùy chọn)

### 1. Clone repository
```bash
git clone <repository-url>
cd Calendar
```

### 2. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 3. Cấu hình môi trường
```bash
cp .env.example .env
```

Chỉnh sửa file `.env` với thông tin của bạn:
```env
# Database
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/calendar_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_API_URL=https://tele-api.cloudmini.net

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com

# Google Calendar API
GOOGLE_API_KEY=your_google_calendar_api_key
GOOGLE_CALENDAR_ID=vi.vietnamese#holiday@group.v.calendar.google.com
```

### 4. Tạo database
```bash
mysql -u root -p
CREATE DATABASE calendar_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Chạy ứng dụng

#### Cách 1: Chạy trực tiếp
```bash
# Chạy web server
python run.py

# Chạy Celery worker (terminal khác)
celery -A app.tasks.notification_tasks worker --loglevel=info

# Chạy Celery beat scheduler (terminal khác)
celery -A app.tasks.notification_tasks beat --loglevel=info
```

#### Cách 2: Sử dụng Docker Compose
```bash
docker-compose up -d
```

### 6. Truy cập ứng dụng
Mở trình duyệt và truy cập: http://localhost:8000

## 🔧 Cấu hình Telegram Bot

### 1. Tạo Telegram Bot
1. Mở Telegram và tìm @BotFather
2. Gửi `/newbot` và làm theo hướng dẫn
3. Lưu Bot Token

### 2. Lấy Chat ID
1. Thêm bot vào group hoặc chat với bot
2. Gửi tin nhắn bất kỳ
3. Truy cập: `https://tele-api.cloudmini.net/bot<BOT_TOKEN>/getUpdates`
4. Tìm `chat.id` trong response

### 3. Cập nhật .env
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_API_URL=https://tele-api.cloudmini.net
```

## 📧 Cấu hình Email

### Gmail SMTP
1. Bật 2-Factor Authentication
2. Tạo App Password
3. Cập nhật .env:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=your_email@gmail.com
```

## 🇻🇳 Cấu hình Google Calendar API

### 1. Lấy Google Calendar API Key
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project có sẵn
3. Bật Google Calendar API:
   - Vào "APIs & Services" > "Library"
   - Tìm "Google Calendar API" và click "Enable"
4. Tạo API Key:
   - Vào "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy API Key vừa tạo

### 2. Bảo mật API Key (Khuyến nghị)
1. Click vào API Key vừa tạo để chỉnh sửa
2. Trong "API restrictions", chọn "Restrict key"
3. Chọn "Google Calendar API" để giới hạn quyền truy cập

### 3. Cập nhật file cấu hình
```env
# Google Calendar API
GOOGLE_API_KEY=your_google_calendar_api_key_here
GOOGLE_CALENDAR_ID=vi.vietnamese#holiday@group.v.calendar.google.com
```

### 4. Calendar ID có sẵn
- **Việt Nam**: `vi.vietnamese#holiday@group.v.calendar.google.com`
- **Quốc tế**: `en.usa#holiday@group.v.calendar.google.com` 
- Hoặc sử dụng Calendar ID riêng của bạn

### 5. Kiểm tra tích hợp
- Sau khi cấu hình, restart ứng dụng
- Ngày lễ quốc gia sẽ hiển thị với icon 🇻🇳
- Nếu chưa cấu hình, sẽ có thông báo hướng dẫn

## 🗂️ Cấu trúc thư mục

```
Calendar/
├── app/
│   ├── models/          # Database models
│   ├── routes/          # API routes
│   ├── services/        # Business logic
│   ├── tasks/           # Celery tasks
│   ├── templates/       # HTML templates
│   ├── static/          # CSS, JS files
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   └── main.py          # FastAPI app
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker setup
├── Dockerfile          # Docker image
├── .env.example        # Environment template
└── README.md           # Documentation
```

## 🚀 Deployment

### Docker Production
```bash
# Build và chạy
docker-compose -f docker-compose.prod.yml up -d

# Hoặc build riêng
docker build -t calendar-app .
docker run -d -p 8000:8000 calendar-app
```

### Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 🔧 Systemd Services (Production)

#### 1. Tạo systemd service files

Tạo user và thư mục:
```bash
sudo useradd -m -s /bin/bash calendar
sudo mkdir -p /var/www/calendar
sudo chown calendar:calendar /var/www/calendar
```

**Web Service** (`/etc/systemd/system/calendar-web.service`):
```ini
[Unit]
Description=Calendar FastAPI Web Application
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
ExecStart=/var/www/calendar/venv/bin/python /var/www/calendar/run.py
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
SyslogIdentifier=calendar-web

[Install]
WantedBy=multi-user.target
```

**Celery Worker Service** (`/etc/systemd/system/calendar-worker.service`):
```ini
[Unit]
Description=Calendar Celery Worker
After=network.target mysql.service redis.service
Wants=mysql.service redis.service

[Service]
Type=simple
User=calendar
Group=calendar
WorkingDirectory=/var/www/calendar
Environment=PATH=/var/www/calendar/venv/bin
Environment=PYTHONPATH=/var/www/calendar
Environment=C_FORCE_ROOT=1
EnvironmentFile=/var/www/calendar/.env
ExecStart=/var/www/calendar/venv/bin/celery -A app.tasks.notification_tasks worker --loglevel=info --concurrency=2
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
TimeoutStartSec=30
TimeoutStopSec=30
KillMode=mixed
KillSignal=SIGTERM

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/var/www/calendar/logs /tmp

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=calendar-worker

[Install]
WantedBy=multi-user.target
```

**Celery Beat Service** (`/etc/systemd/system/calendar-beat.service`):
```ini
[Unit]
Description=Calendar Celery Beat Scheduler
After=network.target mysql.service redis.service
Wants=mysql.service redis.service

[Service]
Type=simple
User=calendar
Group=calendar
WorkingDirectory=/var/www/calendar
Environment=PATH=/var/www/calendar/venv/bin
Environment=PYTHONPATH=/var/www/calendar
Environment=C_FORCE_ROOT=1
EnvironmentFile=/var/www/calendar/.env
ExecStart=/var/www/calendar/venv/bin/celery -A app.tasks.notification_tasks beat --loglevel=info --pidfile=/var/www/calendar/celerybeat.pid
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5
TimeoutStartSec=30
TimeoutStopSec=10

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/var/www/calendar/logs /var/www/calendar /tmp

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=calendar-beat

[Install]
WantedBy=multi-user.target
```

#### 2. Kích hoạt và khởi động services
```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable services (tự động chạy khi khởi động)
sudo systemctl enable calendar-web calendar-worker calendar-beat

# Start services
sudo systemctl start calendar-web calendar-worker calendar-beat
```

#### 3. Quản lý Services

**Khởi động services:**
```bash
sudo systemctl start calendar-web
sudo systemctl start calendar-worker
sudo systemctl start calendar-beat

# Hoặc khởi động tất cả cùng lúc
sudo systemctl start calendar-web calendar-worker calendar-beat
```

**Dừng services:**
```bash
sudo systemctl stop calendar-web
sudo systemctl stop calendar-worker
sudo systemctl stop calendar-beat

# Hoặc dừng tất cả cùng lúc
sudo systemctl stop calendar-web calendar-worker calendar-beat
```

**Khởi động lại services:**
```bash
sudo systemctl restart calendar-web
sudo systemctl restart calendar-worker
sudo systemctl restart calendar-beat

# Hoặc restart tất cả cùng lúc
sudo systemctl restart calendar-web calendar-worker calendar-beat
```

**Reload services (không gián đoạn):**
```bash
sudo systemctl reload calendar-web
sudo systemctl reload calendar-worker
sudo systemctl reload calendar-beat
```

**Kiểm tra trạng thái:**
```bash
# Kiểm tra từng service
sudo systemctl status calendar-web
sudo systemctl status calendar-worker
sudo systemctl status calendar-beat

# Kiểm tra tất cả services
sudo systemctl status calendar-*
```

#### 4. Xem Logs

**Xem log real-time:**
```bash
# Xem log của web service
sudo journalctl -u calendar-web -f

# Xem log của worker
sudo journalctl -u calendar-worker -f

# Xem log của beat scheduler
sudo journalctl -u calendar-beat -f

# Xem log của tất cả services
sudo journalctl -u calendar-* -f
```

**Xem log từ thời điểm cụ thể:**
```bash
# Log 100 dòng cuối
sudo journalctl -u calendar-web -n 100

# Log từ hôm nay
sudo journalctl -u calendar-web --since today

# Log từ 1 giờ trước
sudo journalctl -u calendar-web --since "1 hour ago"

# Log trong khoảng thời gian
sudo journalctl -u calendar-web --since "2024-01-01" --until "2024-01-31"
```

**Xem log với định dạng chi tiết:**
```bash
# Hiển thị log với timestamp chi tiết
sudo journalctl -u calendar-web -o verbose

# Hiển thị log dạng JSON
sudo journalctl -u calendar-web -o json-pretty

# Reverse order (mới nhất ở trên)
sudo journalctl -u calendar-web -r
```

**Xem log lỗi:**
```bash
# Chỉ xem log lỗi
sudo journalctl -u calendar-web -p err

# Xem log với priority (0=emerg, 1=alert, 2=crit, 3=err, 4=warning)
sudo journalctl -u calendar-web -p 3
```

#### 5. Troubleshooting

**Kiểm tra service có chạy không:**
```bash
sudo systemctl is-active calendar-web
sudo systemctl is-enabled calendar-web
```

**Xem thông tin chi tiết service:**
```bash
sudo systemctl show calendar-web
```

**Kiểm tra file cấu hình service:**
```bash
systemctl cat calendar-web
```

**Reload sau khi sửa file service:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart calendar-web
```

## 🧪 Testing

```bash
# Chạy tests
pytest

# Test với coverage
pytest --cov=app

# Test Telegram bot
curl -X POST http://localhost:8000/notifications/test-telegram

# Test notifications
curl -X POST http://localhost:8000/notifications/process-pending
```

## 📝 API Documentation

Sau khi chạy ứng dụng, truy cập:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Tạo Pull Request

## 📄 License

Dự án này được phân phối dưới MIT License. Xem file `LICENSE` để biết thêm chi tiết.

## 🆘 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra [Issues](../../issues) hiện có
2. Tạo issue mới với mô tả chi tiết
3. Cung cấp logs và thông tin môi trường

## 🎯 Roadmap

- [ ] Tích hợp Google Calendar
- [ ] Push notifications cho mobile
- [ ] API cho mobile app
- [ ] Xuất/nhập dữ liệu
- [ ] Chia sẻ lịch công khai
- [ ] Tích hợp AI cho gợi ý

---

**Phát triển bởi:** [Tên của bạn]  
**Email:** your-email@example.com  
**Version:** 1.0.0
