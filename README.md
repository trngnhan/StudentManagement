# StudentManagement
Bài tập lớn Lập trình cơ sở dữ liệu
# 📚 Hệ thống Quản lý học sinh tích hợp điểm danh bằng nhận dạng gương mặt

## 🧠 Giới thiệu

Đây là hệ thống quản lý học sinh dành cho các trường trung học, được xây dựng bằng **Django**. Hệ thống hỗ trợ:

- Quản lý tài khoản giáo viên, học sinh, phụ huynh
- Theo dõi lớp học, khối học, năm học, học kỳ
- Nhập điểm, học bạ, môn học, chương trình học
- **Điểm danh học sinh thông qua nhận dạng gương mặt**
- Tích hợp quản trị viên (admin) với giao diện trực quan

---

## 🎯 Tính năng chính

### ✅ Quản lý thông tin

- **Người dùng:** Tài khoản phân quyền (Admin, Giáo viên, Học sinh, Nhân viên)
- **Thông tin cá nhân:** Họ tên, giới tính, ngày sinh, số điện thoại, email
- **Cấu trúc trường:** Khối lớp, lớp học, môn học, chương trình học
- **Phụ huynh:** Gắn với mỗi học sinh
Liên hệ Email: 
trinhquocdat041004@gmail.com


### 🧑‍🏫 Học tập & Điểm số

- **Transcript:** Học bạ cho mỗi môn học – học kỳ – lớp học
- **Score:** Ghi nhận các loại điểm (15 phút, 1 tiết, thi)
- **Chương trình học:** Xác định môn nào học trong khối nào

### 🎥 Điểm danh bằng nhận diện gương mặt

- **Lưu vector gương mặt** bằng webcam (từ giao diện admin)
- **Mở camera điểm danh** tại `/attendance/camera/`
- Hệ thống nhận diện khuôn mặt và lưu thời gian điểm danh

---

## 🔧 Công nghệ sử dụng

- Backend: [Django](https://www.djangoproject.com/) + Admin
- Frontend: HTML, JavaScript (WebRTC, Fetch API)
- AI: [face_recognition](https://github.com/ageitgey/face_recognition) (dựa trên dlib)
- Camera: Webcam tích hợp trình duyệt (getUserMedia API)
- Lưu vector: `numpy` + `pickle`
- CSDL: MySQL

---

## 🚀 Cách sử dụng

### 1. Cài đặt

```bash
git clone [https://github.com/trngnhan/StudentManagement.git]
cd student_management
python -m venv venv
source venv/bin/activate  # hoặc venv\\Scripts\\activate trên Windows
pip install -r requirements.txt
python manage.py migrate
python magage.py runserver


### 1. Liên Hệ
```bash
Trần Trọng Nhân: kingtrngnhan@gmail.com
Trịnh Quốc Đạt: trinhquocdat041004@gmail.com
