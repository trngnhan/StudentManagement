import os
import random

import django

# --- Thiết lập Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "student_management.settings")
django.setup()

from students.models import (
    Subject, SchoolYear, Semester, Grade, Classroom, Curriculum,
    GradeType, SemesterType,
    User, AdminInfo, TeacherInfo, StudentInfo, StaffInfo,
    Gender, Role, Rule, Score, ScoreType, Transcript, ClassroomTransfer
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

# --- Quy định hệ thống ---
rule_data = [
    {
        'rule_name': 'age_range',
        'min_value': 15,
        'max_value': 20,
        'rule_content': 'Độ tuổi học sinh từ 15 đến 20'
    },
    {
        'rule_name': 'max_class_size',
        'min_value': None,
        'max_value': 40,
        'rule_content': 'Sĩ số tối đa mỗi lớp là 40 học sinh'
    },
    {
        'rule_name': 'score_15_min_max',
        'min_value': 1,
        'max_value': 5,
        'rule_content': 'Mỗi môn có từ 1 đến 5 cột điểm 15 phút'
    },
    {
        'rule_name': 'test_1_min_max',
        'min_value': 1,
        'max_value': 3,
        'rule_content': 'Mỗi môn có từ 1 đến 3 bài kiểm tra 1 tiết'
    },
    {
        'rule_name': 'final_exam_required',
        'min_value': 1,
        'max_value': 1,
        'rule_content': 'Mỗi môn có 1 bài thi cuối kỳ'
    },
    {
        'rule_name': 'min_average_to_pass',
        'min_value': 5,
        'max_value': 10,
        'rule_content': 'Đạt môn nếu điểm trung bình môn ≥ 5'
    }
]

for rule in rule_data:
    Rule.objects.get_or_create(
        rule_name=rule['rule_name'],
        defaults={
            'min_value': rule['min_value'],
            'max_value': rule['max_value'],
            'rule_content': rule['rule_content']
        }
    )

print("✅ Rules created")

# Lấy lớp đầu tiên
classroom = Classroom.objects.first()
semester = classroom.grade.school_year.semesters.first()
curriculums = classroom.grade.curriculums.all()[:3]  # chọn 3 môn đầu

# Lấy giáo viên đầu tiên
from students.models import TeacherInfo
teacher = TeacherInfo.objects.first()

# Tạo 5 học sinh mới
for i in range(1, 6):
    username = f"student_extra_{i}"
    user, _ = User.objects.get_or_create(username=username, defaults={"role": Role.STUDENT})
    user.set_password("student123")
    user.save()

    student, _ = StudentInfo.objects.get_or_create(
        user=user,
        defaults={
            "name": f"Học sinh phụ {i}",
            "gender": Gender.MALE if i % 2 == 0 else Gender.FEMALE,
            "phone": f"09000000{i+10}",
            "email": f"extra{i}@example.com",
            "address": "TP. Hồ Chí Minh",
            "birthday": timezone.datetime(2007, 1, i+1),
            "status": True
        }
    )

    # Gán vào lớp
    ClassroomTransfer.objects.get_or_create(
        student_info=student,
        classroom=classroom
    )

    # Tạo điểm cho từng môn
    for curriculum in curriculums:
        transcript, _ = Transcript.objects.get_or_create(
            classroom=classroom,
            semester=semester,
            curriculum=curriculum,
            defaults={"teacher_info": teacher}
        )

        # Tạo 3 điểm 15 phút
        for _ in range(3):
            Score.objects.create(
                student_info=student,
                transcript=transcript,
                score_type=ScoreType.SCORE_15_MIN,
                score_number=round(random.uniform(5, 10), 1)
            )

        # Tạo 2 điểm 1 tiết
        for _ in range(2):
            Score.objects.create(
                student_info=student,
                transcript=transcript,
                score_type=ScoreType.SCORE_1_PERIOD,
                score_number=round(random.uniform(5, 10), 1)
            )

        # Tạo 1 điểm thi cuối kỳ
        Score.objects.create(
            student_info=student,
            transcript=transcript,
            score_type=ScoreType.FINAL_EXAM,
            score_number=round(random.uniform(5, 10), 1)
        )

print("✅ Đã tạo 5 học sinh và điểm cho mỗi môn theo đúng quy định.")
