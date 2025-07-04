import os
import django

# --- Thiết lập Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "student_management.settings")
django.setup()

from students.models import (
    Subject, SchoolYear, Semester, Grade, Classroom, Curriculum,
    GradeType, SemesterType,
    User, AdminInfo, TeacherInfo, StudentInfo, StaffInfo,
    Gender, Role
)
from django.utils import timezone

# --- Môn học ---
subjects = ['Toán', 'Ngữ văn', 'Vật lý', 'Hóa học', 'Sinh học',
            'Lịch sử', 'Địa lý', 'Tiếng Anh', 'Tin học', 'GDCD']

subject_objs = []
for name in subjects:
    subject, _ = Subject.objects.get_or_create(subject_name=name)
    subject_objs.append(subject)
print("✅ Subjects created")

# --- Năm học ---
years = ['2023-2024', '2024-2025']
school_year_objs = []
for y in years:
    sy, _ = SchoolYear.objects.get_or_create(school_year_name=y)
    school_year_objs.append(sy)
print("✅ School years created")

# --- Học kỳ ---
for sy in school_year_objs:
    Semester.objects.get_or_create(school_year=sy, semester_type=SemesterType.FIRST_TERM)
    Semester.objects.get_or_create(school_year=sy, semester_type=SemesterType.SECOND_TERM)
print("✅ Semesters created")

# --- Khối ---
grades_by_year = {}
grade_objs = []
for sy in school_year_objs:
    for gt in [GradeType.GRADE_10, GradeType.GRADE_11, GradeType.GRADE_12]:
        grade, _ = Grade.objects.get_or_create(grade_type=gt, school_year=sy)
        grades_by_year[(sy.school_year_name, gt)] = grade
        grade_objs.append(grade)
print("✅ Grades created")

# --- Lớp ---
sample_classes = ['A', 'B', 'C']
for sy in years:
    for g in [10, 11, 12]:
        grade_obj = grades_by_year[(sy, g)]
        for label in sample_classes:
            name = f"{g}{label}"
            Classroom.objects.get_or_create(classroom_name=name, student_number=0, grade=grade_obj)
print("✅ Classrooms created")

# --- Curriculum ---
count = 0
for grade in grade_objs:
    for subject in subject_objs:
        _, created = Curriculum.objects.get_or_create(grade=grade, subject=subject)
        if created:
            count += 1
print(f"✅ Curriculum created ({count} môn học được gán vào khối)")

# ==========================
# TẠO USER MẪU CHO CÁC ROLE
# ==========================

# --- Admin ---
admin_user, _ = User.objects.get_or_create(username='admin01', defaults={'role': Role.ADMIN})
admin_user.set_password('admin123')
admin_user.save()
AdminInfo.objects.get_or_create(
    user=admin_user,
    defaults={
        'name': 'Admin Nguyễn',
        'gender': Gender.MALE,
        'birthday': timezone.datetime(1990, 1, 1),
        'email': 'admin@example.com',
        'phone': '0900000001',
        'address': 'Hà Nội',
        'status': True
    }
)

# --- Giáo viên ---
teacher_user, _ = User.objects.get_or_create(username='teacher01', defaults={'role': Role.TEACHER})
teacher_user.set_password('teacher123')
teacher_user.save()
TeacherInfo.objects.get_or_create(
    user=teacher_user,
    defaults={
        'name': 'Cô Mai Hoa',
        'gender': Gender.FEMALE,
        'birthday': timezone.datetime(1985, 3, 10),
        'email': 'teacher@example.com',
        'phone': '0900000002',
        'address': 'TP.HCM',
        'status': True
    }
)

# --- Học sinh ---
student_user, _ = User.objects.get_or_create(username='student01', defaults={'role': Role.STUDENT})
student_user.set_password('student123')
student_user.save()
StudentInfo.objects.get_or_create(
    user=student_user,
    defaults={
        'name': 'Trần Văn B',
        'gender': Gender.MALE,
        'birthday': timezone.datetime(2006, 9, 9),
        'email': 'student@example.com',
        'phone': '0900000003',
        'address': 'Đồng Nai',
        'status': True
    }
)

# --- Nhân viên ---
staff_user, _ = User.objects.get_or_create(username='staff01', defaults={'role': Role.STAFF})
staff_user.set_password('staff123')
staff_user.save()
StaffInfo.objects.get_or_create(
    user=staff_user,
    defaults={
        'name': 'Nguyễn Thị Lan',
        'gender': Gender.FEMALE,
        'birthday': timezone.datetime(1992, 5, 20),
        'email': 'staff@example.com',
        'phone': '0900000004',
        'address': 'Cần Thơ',
        'status': True
    }
)

print("✅ Sample users created (Admin, Teacher, Student, Staff)")