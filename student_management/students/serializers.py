from rest_framework import serializers
from .models import (
    User, AdminInfo, StaffInfo, TeacherInfo, StudentInfo, ParentInfo,
    SchoolYear, Semester, Grade, Classroom, ClassroomTransfer,
    Subject, Curriculum, Transcript, Score, Attendance, Rule
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class PersonalInfoBaseSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        abstract = True


class AdminInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminInfo
        fields = '__all__'


class StaffInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffInfo
        fields = '__all__'


class TeacherInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherInfo
        fields = '__all__'


class StudentInfoSerializer(serializers.ModelSerializer):
    current_classroom = serializers.SerializerMethodField()

    class Meta:
        model = StudentInfo
        fields = '__all__'

    def get_current_classroom(self, obj):
        classroom = obj.get_current_classroom()
        return str(classroom) if classroom else None


class ParentInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParentInfo
        fields = '__all__'


class SchoolYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolYear
        fields = '__all__'


class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = '__all__'


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = '__all__'


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = '__all__'


class ClassroomTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomTransfer
        fields = '__all__'


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class CurriculumSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curriculum
        fields = '__all__'


class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = '__all__'


class ScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Score
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = '__all__'