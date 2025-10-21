# Cập nhật: Thêm tính năng lặp lại hàng tháng

## Tổng quan
Cập nhật này thêm tính năng lặp lại hàng tháng cho ghi chú, bên cạnh tính năng lặp lại hàng năm đã có.

## Các thay đổi

### 1. Database Changes
- **Table `notes`**: Thêm column `monthly_repeat` (BOOLEAN)
- **Table `notification_schedules`**: Thêm column `current_month` (INTEGER)

### 2. Model Changes
- `app/models/note.py`: Thêm field `monthly_repeat`
- `app/models/notification_schedule.py`: Thêm field `current_month`

### 3. UI Changes
- `app/templates/components/note_form.html`: Thêm radio buttons cho lựa chọn:
  - 📅 Lặp lại hàng tháng
  - 🔄 Lặp lại hàng năm
  - ❌ Không lặp lại

### 4. Backend Changes
- `app/routes/notes.py`: 
  - Thêm parameter `repeat_type` thay vì `yearly_repeat`
  - Xử lý `monthly_repeat` và `yearly_repeat` dựa trên `repeat_type`
  
- `app/services/notification_service.py`:
  - Cập nhật logic tính toán ngày sự kiện theo tháng/năm
  - Xử lý reset schedule khi hoàn thành:
    - Monthly repeat: chuyển sang tháng tiếp theo
    - Yearly repeat: chuyển sang năm tiếp theo
  - Xử lý các trường hợp ngày không hợp lệ (vd: 31 tháng 2)

## Cách cập nhật

### Trên máy Development (Windows)

```powershell
# 1. Pull code mới
git pull origin main

# 2. Chạy migration (nếu đang chạy local database)
py migration_add_monthly_repeat.py
```

### Trên Production Server (Linux)

```bash
# 1. SSH vào server
ssh calendar@your-server-ip

# 2. Chuyển sang thư mục project
cd /var/www/calendar

# 3. Pull code mới
git pull origin main

# 4. Kích hoạt virtual environment
source venv/bin/activate

# 5. Chạy migration script
python migration_add_monthly_repeat.py

# 6. Restart các services
sudo systemctl restart calendar-web calendar-worker calendar-beat

# 7. Kiểm tra trạng thái
sudo systemctl status calendar-*

# 8. Xem logs
sudo journalctl -u calendar-* -f
```

## Cách sử dụng

### Tạo ghi chú lặp lại hàng tháng

1. Vào trang tạo ghi chú
2. Điền thông tin ghi chú
3. Chọn ngày (ví dụ: 15/01/2025)
4. Bật "Thông báo nhắc nhở"
5. Chọn số ngày nhắc trước (ví dụ: 3 ngày)
6. **Chọn "📅 Lặp lại hàng tháng"**
7. Lưu ghi chú

### Kết quả

Hệ thống sẽ:
- Gửi thông báo 3 ngày trước (12/01/2025)
- Gửi thông báo 2 ngày trước (13/01/2025)
- Gửi thông báo 1 ngày trước (14/01/2025)
- Gửi thông báo đúng ngày (15/01/2025)

Sau khi hoàn thành, tự động chuyển sang tháng sau:
- Lặp lại vào ngày 15/02/2025
- Tiếp tục lặp mỗi tháng vào ngày 15

### Xử lý trường hợp đặc biệt

**Trường hợp: Ngày 31 tháng 1**
- Tháng 2 không có ngày 31 → Hệ thống tự động chuyển thành ngày 28/2 (hoặc 29/2 năm nhuận)

**Trường hợp: Ngày 30 tháng 1**
- Tháng 2 không có ngày 30 → Hệ thống tự động chuyển thành ngày 28/2 (hoặc 29/2)

## Kiểm tra

### 1. Kiểm tra database

```sql
-- Kiểm tra column mới trong notes
DESCRIBE notes;

-- Kiểm tra column mới trong notification_schedules
DESCRIBE notification_schedules;

-- Kiểm tra ghi chú có lặp hàng tháng
SELECT id, title, solar_date, monthly_repeat, yearly_repeat 
FROM notes 
WHERE monthly_repeat = TRUE;

-- Kiểm tra schedule với current_month
SELECT ns.id, ns.current_year, ns.current_month, n.title 
FROM notification_schedules ns 
JOIN notes n ON ns.note_id = n.id;
```

### 2. Kiểm tra logs

```bash
# Xem log của worker
sudo journalctl -u calendar-worker -n 100

# Xem log của beat scheduler
sudo journalctl -u calendar-beat -n 100

# Tìm log liên quan đến monthly repeat
sudo journalctl -u calendar-* | grep -i "monthly\|reset\|🔄"
```

### 3. Test thủ công

1. Tạo một ghi chú lặp hàng tháng với ngày gần nhất
2. Đợi thông báo được gửi
3. Kiểm tra database để xác nhận schedule đã reset sang tháng sau

## Rollback (nếu cần)

```bash
# 1. Quay lại commit trước
cd /var/www/calendar
git reset --hard <previous-commit-hash>

# 2. Xóa columns trong database
mysql -u username -p calendar_db

# Trong MySQL:
ALTER TABLE notes DROP COLUMN monthly_repeat;
ALTER TABLE notification_schedules DROP COLUMN current_month;

# 3. Restart services
sudo systemctl restart calendar-web calendar-worker calendar-beat
```

## Lưu ý

1. **Backup trước khi migrate**: Luôn backup database trước khi chạy migration
2. **Testing**: Test trên môi trường development trước khi deploy production
3. **Monitoring**: Theo dõi logs sau khi deploy để phát hiện lỗi sớm
4. **User notification**: Thông báo cho người dùng về tính năng mới

## Hỗ trợ

Nếu gặp vấn đề, hãy kiểm tra:
1. Logs: `sudo journalctl -u calendar-* -f`
2. Database: Xác nhận các column đã được tạo
3. Service status: `sudo systemctl status calendar-*`
