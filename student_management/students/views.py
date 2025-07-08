from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import *
from .serializers import *
from .permissions import *
from datetime import date, datetime
import pickle
import time
import cv2
import numpy as np
import face_recognition
import json, base64
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import requests
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from rest_framework import serializers

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data["username"] = user.username

        if hasattr(user, 'admin_info'):
            data["role"] = "admin"
        elif hasattr(user, 'teacher_info'):
            data["role"] = "teacher"
        elif hasattr(user, 'student_info'):
            data["role"] = "student"
        else:
            data["role"] = "unknown"

        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class AdminInfoViewSet(viewsets.ModelViewSet):
    queryset = AdminInfo.objects.all()
    serializer_class = AdminInfoSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        if not hasattr(request.user, 'admin_info'):
            return Response({"detail": "Không có quyền truy cập"}, status=403)

        return Response({
            "total_staff": StaffInfo.objects.count(),
            "total_teacher": TeacherInfo.objects.count(),
            "total_student": StudentInfo.objects.count(),
            "total_classroom": Classroom.objects.count(),
            "total_subject": Subject.objects.count(),
        })


class StaffInfoViewSet(viewsets.ModelViewSet):
    queryset = StaffInfo.objects.all()
    serializer_class = StaffInfoSerializer


class TeacherInfoViewSet(viewsets.ModelViewSet):
    queryset = TeacherInfo.objects.all()
    serializer_class = TeacherInfoSerializer


class StudentInfoViewSet(viewsets.ModelViewSet):
    queryset = StudentInfo.objects.all()
    serializer_class = StudentInfoSerializer
    permission_classes = [IsAuthenticated, IsStudent]


class ParentInfoViewSet(viewsets.ModelViewSet):
    queryset = ParentInfo.objects.all()
    serializer_class = ParentInfoSerializer


class SchoolYearViewSet(viewsets.ModelViewSet):
    queryset = SchoolYear.objects.all()
    serializer_class = SchoolYearSerializer

    @action(detail=False, methods=['get'], url_path='with-semesters')
    def with_semesters(self, request):
        queryset = self.get_queryset().prefetch_related('semesters')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["delete"], url_path="delete")
    def delete_schoolyear(self, request, pk=None):
        try:
            school_year = self.get_object()
            school_year.delete()
            return Response({"message": "Đã xoá năm học."}, status=status.HTTP_204_NO_CONTENT)
        except models.ProtectedError:
            return Response(
                {"detail": "Không thể xoá năm học vì có học kỳ liên kết."},
                status=status.HTTP_400_BAD_REQUEST
            )


class SemesterViewSet(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    filter_backends = [DjangoFilterBackend]
    search_fields = ['school_year__id']

    def get_queryset(self):
        queryset = super().get_queryset()
        school_year_id = self.request.query_params.get("school_year")
        if school_year_id:
            queryset = queryset.filter(school_year_id=school_year_id)
        return queryset

    @action(detail=False, methods=['post'], url_path='create')
    def create_semester(self, request):
        school_year_id = request.data.get("school_year")
        semester_type = request.data.get("semester_type")

        if not school_year_id or semester_type is None:
            return Response({"detail": "Thiếu trường school_year hoặc semester_type."}, status=400)

        if Semester.objects.filter(school_year_id=school_year_id, semester_type=semester_type).exists():
            return Response({"detail": "Học kỳ này đã tồn tại trong năm học."}, status=409)

        semester = Semester.objects.create(
            school_year_id=school_year_id,
            semester_type=semester_type
        )
        return Response(SemesterSerializer(semester).data, status=201)

    @action(detail=True, methods=['put'], url_path='update')
    def update_semester(self, request, pk=None):
        try:
            semester = Semester.objects.get(pk=pk)
        except Semester.DoesNotExist:
            return Response({"detail": "Không tìm thấy học kỳ."}, status=404)

        semester_type = request.data.get("semester_type")
        if semester_type is not None:
            if Semester.objects.filter(school_year=semester.school_year, semester_type=semester_type).exclude(
                    id=semester.id).exists():
                return Response({"detail": "Học kỳ đã tồn tại."}, status=409)

            semester.semester_type = semester_type
            semester.save()

        return Response(SemesterSerializer(semester).data)

    @action(detail=True, methods=['delete'], url_path='delete')
    def delete_semester(self, request, pk=None):
        try:
            semester = Semester.objects.get(pk=pk)
        except Semester.DoesNotExist:
            return Response({"detail": "Không tìm thấy học kỳ."}, status=404)

        semester.delete()
        return Response({"detail": "Đã xoá học kỳ."}, status=204)


class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = Classroom.objects.all()
    serializer_class = ClassroomSerializer


class ClassroomTransferViewSet(viewsets.ModelViewSet):
    queryset = ClassroomTransfer.objects.all()
    serializer_class = ClassroomTransferSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().order_by("id")
    serializer_class = SubjectSerializer

    @action(detail=False, methods=['get'], url_path='search', url_name='subject-search')
    def search(self, request):
        q = request.GET.get("q", "").strip()
        subjects = self.queryset.filter(subject_name__icontains=q)[:50] if q else self.queryset[:50]
        data = [{"id": s.id, "subject_name": s.subject_name} for s in subjects]
        return Response({"results": data})

class CurriculumViewSet(viewsets.ModelViewSet):
    queryset = Curriculum.objects.select_related('grade', 'subject').all()
    serializer_class = CurriculumSerializer

    @action(detail=False, methods=['post'], url_path='add')
    def add_to_curriculum(self, request):
        grade_id = request.data.get("grade_id")
        subject_id = request.data.get("subject_id")

        if not grade_id or not subject_id:
            return Response({"detail": "Thiếu grade_id hoặc subject_id."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            grade = Grade.objects.get(id=grade_id)
            subject = Subject.objects.get(id=subject_id)
        except Grade.DoesNotExist:
            return Response({"detail": "Không tìm thấy khối lớp."}, status=status.HTTP_404_NOT_FOUND)
        except Subject.DoesNotExist:
            return Response({"detail": "Không tìm thấy môn học."}, status=status.HTTP_404_NOT_FOUND)

        if Curriculum.objects.filter(grade=grade, subject=subject).exists():
            return Response({"detail": "Môn học này đã có trong chương trình khối này."}, status=status.HTTP_409_CONFLICT)

        curriculum = Curriculum.objects.create(grade=grade, subject=subject)
        serializer = self.get_serializer(curriculum)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TranscriptViewSet(viewsets.ModelViewSet):
    queryset = Transcript.objects.all()
    serializer_class = TranscriptSerializer


class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer
    permission_classes = [IsAuthenticated, IsTeacher | ReadOnly]


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsTeacher | ReadOnly]


class RuleViewSet(viewsets.GenericViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @action(detail=False, methods=['get'], url_path='all_rules')
    def all_rules(self, request):
        rules = self.get_queryset()
        serializer = self.get_serializer(rules, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['put'], url_path='update_rules')
    def update_rules(self, request):
        data = request.data
        updated = []

        for item in data:
            rule_name = item.get('rule_name')
            if not rule_name:
                continue
            try:
                rule = Rule.objects.get(rule_name=rule_name)
                serializer = self.get_serializer(rule, data=item, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated.append(serializer.data)
            except Rule.DoesNotExist:
                continue

        return Response(updated, status=200)

def admin_dashboard(request):
    if request.session.get("role") != "admin":
        return redirect('login')

    return render(request, "admin/admin_dashboard.html", {
        "username": request.session.get("username"),
    })


#------Khai báo các trang web---------
def rules_list_view(request):
    if not request.session.get("access"):
        return redirect('login')
    return render(request, 'admin/rules_list.html')



def subject_manage_view(request):
    if not request.session.get("access"):
        return redirect('login')
    return render(request, 'admin/subject_manage.html')

def camera_attendance(request):
    return render(request, "attendance/camera_attendance.html")

@csrf_exempt
def mark_attendance(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        data_url = json.loads(request.body)["image"]
        # tách base64
        header, b64 = data_url.split(",", 1)
        img_bytes = base64.b64decode(b64)
        img_array = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        # detect & encode
        locs = face_recognition.face_locations(frame)
        encs = face_recognition.face_encodings(frame, locs)

        if not encs:
            return JsonResponse({"status": "no_face"})

        enc = encs[0]

        # tìm học sinh gần nhất trong DB
        students = StudentInfo.objects.exclude(encoding__isnull=True)
        candidates = []
        for s in students:
            known = pickle.loads(s.encoding)
            dist = face_recognition.face_distance([known], enc)[0]
            if dist < 0.5:                        # ngưỡng so khớp
                candidates.append((dist, s))
        if not candidates:
            return JsonResponse({"status": "unknown"})

        # chọn khoảng cách nhỏ nhất
        _, student = sorted(candidates, key=lambda x: x[0])[0]

        # ghi bảng điểm danh
        att, _ = Attendance.objects.get_or_create(
            student=student, date=datetime.today(),
            defaults={"time_checked": datetime.now().time(), "is_late": False},
        )

        return JsonResponse({
            "status": "ok",
            "student": student.name,
            "already": not att._state.adding,
        })
    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=500)

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        url = request.build_absolute_uri('/token/')
        response = requests.post(url, data={
            "username": username,
            "password": password,
        })

        if response.status_code == 200:
            data = response.json()
            request.session['access'] = data['access']
            request.session['refresh'] = data['refresh']
            request.session['username'] = data['username']
            request.session['role'] = data['role']

            print("DEBUG LOGIN:", data)

            role = data['role']
            if role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'teacher':
                return redirect('teacher_dashboard')
            elif role == 'student':
                return redirect('student_dashboard')
            else:
                return redirect('/')

        return render(request, "login.html", {"error": "Sai tên đăng nhập hoặc mật khẩu."})

    return render(request, "login.html")

def logout_view(request):
    request.session.flush()
    return redirect('login')

from students.models import User

def profile_view(request):
    if not request.session.get('access'):
        return redirect('login')

    username = request.session.get('username')
    role = request.session.get('role')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return redirect('login')

    profile = None

    if role == 'admin' and hasattr(user, 'admin_info'):
        profile = user.admin_info
    elif role == 'teacher' and hasattr(user, 'teacher_info'):
        profile = user.teacher_info
    elif role == 'staff' and hasattr(user, 'staff_info'):
        profile = user.staff_info
    elif role == 'student' and hasattr(user, 'student_info'):
        profile = user.student_info

    print("USERNAME:", username)
    print("ROLE:", role)
    print("HAS PROFILE:", bool(profile))

    return render(request, 'profile.html', {
        'profile': profile,
        'role': role,
    })

def edit_subject_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    if request.method == "POST":
        subject_name = request.POST.get("subject_name")
        if subject_name:
            subject.subject_name = subject_name
            subject.save()
            messages.success(request, "Đã cập nhật môn học.")
            return redirect("subject_manage")
        else:
            messages.error(request, "Tên môn học không được để trống.")

    return render(request, "admin/subject_edit.html", {"subject": subject})

def schoolyear_semester_manage_view(request):
    if not request.session.get("access"):
        return redirect('login')
    return render(request, "admin/schoolyear_manage.html")


def semesters_of_schoolyear_view(request, year_id):
    if not request.session.get("access"):
        return redirect("login")

    school_year = get_object_or_404(SchoolYear, id=year_id)
    semesters = Semester.objects.filter(school_year=school_year)

    return render(request, "admin/schoolyear_semesters.html", {
        "school_year": school_year,
        "semesters": semesters,
    })
