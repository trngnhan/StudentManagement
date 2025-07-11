from cloudinary.models import CloudinaryField
from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


# -------- ENUMS --------
class Role(models.IntegerChoices):
    ADMIN = 1, 'Admin'
    STAFF = 2, 'Staff'
    TEACHER = 3, 'Teacher'
    STUDENT = 4, 'Student'


class Gender(models.IntegerChoices):
    FEMALE = 0, 'Nữ'
    MALE = 1, 'Nam'


class SemesterType(models.IntegerChoices):
    FIRST_TERM = 1, 'Học kỳ I'
    SECOND_TERM = 2, 'Học kỳ II'


class GradeType(models.IntegerChoices):
    GRADE_10 = 10, 'Khối 10'
    GRADE_11 = 11, 'Khối 11'
    GRADE_12 = 12, 'Khối 12'


class ScoreType(models.IntegerChoices):
    SCORE_15_MIN = 1, "Điểm 15 phút"
    SCORE_1_PERIOD = 2, "Điểm 1 tiết"
    FINAL_EXAM = 3, "Điểm thi cuối kỳ"


# -------- USER --------
class User(AbstractUser):
    avatar = CloudinaryField('image', blank=True, null=True)
    role = models.IntegerField(choices=Role.choices, default=Role.TEACHER)


# -------- BASE INFO --------
class PersonalInfo(models.Model):
    name = models.CharField(max_length=50)
    gender = models.IntegerField(choices=Gender.choices)
    phone = models.CharField(max_length=10, unique=True)
    address = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    birthday = models.DateField()
    status = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class AdminInfo(PersonalInfo):
    user = models.OneToOneField(User, null=True, on_delete=models.SET_NULL, related_name='admin_info')


class StaffInfo(PersonalInfo):
    user = models.OneToOneField(User, null=True, on_delete=models.SET_NULL, related_name='staff_info')


class TeacherInfo(PersonalInfo):
    user = models.OneToOneField(User, null=True, on_delete=models.SET_NULL, related_name='teacher_info')


# -------- PHỤ HUYNH --------
class ParentInfo(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=10)
    email = models.EmailField()
    student = models.OneToOneField('StudentInfo', on_delete=models.CASCADE, related_name='parent')

    def __str__(self):
        return f'Phụ huynh của {self.student.name}'


# -------- CẤU TRÚC TRƯỜNG --------
class SchoolYear(models.Model):
    school_year_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.school_year_name


class Semester(models.Model):
    semester_type = models.IntegerField(choices=SemesterType.choices)
    school_year = models.ForeignKey(SchoolYear, on_delete=models.RESTRICT, related_name='semesters')

    class Meta:
        unique_together = ('semester_type', 'school_year')

    def __str__(self):
        return f'{self.get_semester_type_display()} - {self.school_year}'


class Grade(models.Model):
    grade_type = models.IntegerField(choices=GradeType.choices)
    school_year = models.ForeignKey(SchoolYear, on_delete=models.RESTRICT, related_name='grades')

    class Meta:
        unique_together = ('grade_type', 'school_year')

    def __str__(self):
        return f'{self.get_grade_type_display()} - {self.school_year}'


class Classroom(models.Model):
    classroom_name = models.CharField(max_length=50)
    student_number = models.PositiveIntegerField(default=0)
    grade = models.ForeignKey(Grade, on_delete=models.RESTRICT, related_name='classrooms')

    class Meta:
        unique_together = ('classroom_name', 'grade')

    def __str__(self):
        return self.classroom_name


# -------- HỌC SINH --------
class StudentInfo(PersonalInfo):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='student_info')
    encoding = models.BinaryField(null=True)

    def get_current_classroom(self):
        latest = self.classroom_transfers.order_by('-transfer_date').first()
        return latest.classroom if latest else None


# -------- CHUYỂN LỚP --------
class ClassroomTransfer(models.Model):
    changed_classroom = models.BooleanField(default=False)
    transfer_date = models.DateField(default=timezone.now)
    classroom = models.ForeignKey(Classroom, on_delete=models.RESTRICT, related_name='classroom_transfers')
    student_info = models.ForeignKey(StudentInfo, on_delete=models.CASCADE, related_name='classroom_transfers')

    class Meta:
        unique_together = ('student_info', 'classroom', 'transfer_date')

    def __str__(self):
        return f'{self.classroom} - {self.student_info}'


# -------- MÔN HỌC & CHƯƠNG TRÌNH --------
class Subject(models.Model):
    subject_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.subject_name


class Curriculum(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='curriculums')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='curriculums')

    class Meta:
        unique_together = ('grade', 'subject')

    def __str__(self):
        return f'{self.subject} - {self.grade}'


# -------- HỌC BẠ & ĐIỂM --------
class Transcript(models.Model):
    is_done = models.BooleanField(default=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='transcripts')
    curriculum = models.ForeignKey(Curriculum, on_delete=models.RESTRICT)
    semester = models.ForeignKey(Semester, on_delete=models.RESTRICT, related_name='transcripts')
    teacher_info = models.ForeignKey(TeacherInfo, on_delete=models.RESTRICT, related_name='transcripts')

    class Meta:
        unique_together = ('classroom', 'curriculum', 'semester')

    def __str__(self):
        return f'{self.classroom} - {self.curriculum} - {self.semester}'


class Score(models.Model):
    score_number = models.FloatField(null=True)
    score_type = models.IntegerField(choices=ScoreType.choices)
    student_info = models.ForeignKey(StudentInfo, on_delete=models.CASCADE, related_name='scores')
    transcript = models.ForeignKey(Transcript, on_delete=models.RESTRICT, related_name='scores')

    def __str__(self):
        return f'{self.student_info} - {self.get_score_type_display()}'


# -------- ĐIỂM DANH --------
class Attendance(models.Model):
    student = models.ForeignKey(StudentInfo, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    time_checked = models.TimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f'{self.student.name} - {self.date}'


# -------- QUY ĐỊNH --------
class Rule(models.Model):
    rule_name = models.CharField(max_length=50, unique=True)
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)
    rule_content = models.CharField(max_length=191)

    def __str__(self):
        return self.rule_name
    
