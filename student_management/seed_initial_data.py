# seed_initial_data.py
import os
import django

# --- Thiết lập Django ---
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "student_management.settings")
django.setup()

from students.models import (
    Subject, SchoolYear, Semester, Grade, Classroom, Curriculum,
    GradeType, SemesterType
)

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