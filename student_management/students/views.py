from django.contrib import messages
from django.views.decorators.http import require_GET
from rest_framework import viewsets
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


class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer


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
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class CurriculumViewSet(viewsets.ModelViewSet):
    queryset = Curriculum.objects.all()
    serializer_class = CurriculumSerializer


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


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

def admin_dashboard(request):
    if request.session.get("role") != "admin":
        return redirect('login')

    return render(request, "admin/admin_dashboard.html", {
        "username": request.session.get("username"),
    })
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

def subject_manage_view(request):
    subjects = Subject.objects.all().order_by("id")
    grades = Grade.objects.select_related('school_year')
    curriculum = Curriculum.objects.select_related('grade', 'subject')

    # --- Thêm môn học mới ---
    if request.method == "POST":
        if 'add_subject' in request.POST:
            subject_name = request.POST.get("subject_name", "").strip()
            if subject_name:
                if Subject.objects.filter(subject_name__iexact=subject_name).exists():
                    messages.error(request, "Môn học đã tồn tại.")
                else:
                    Subject.objects.create(subject_name=subject_name)
                    messages.success(request, "Đã thêm môn học thành công!")
            else:
                messages.error(request, "Tên môn học không được để trống.")
            return redirect("subject_manage")

        # --- Thêm vào chương trình học ---
        elif 'grade' in request.POST and 'subject' in request.POST:
            grade_id = request.POST.get("grade")
            subject_id = request.POST.get("subject")
            try:
                grade = Grade.objects.get(id=grade_id)
                subject = Subject.objects.get(id=subject_id)
                if Curriculum.objects.filter(grade=grade, subject=subject).exists():
                    messages.warning(request, "Môn học này đã có trong chương trình khối này.")
                else:
                    Curriculum.objects.create(grade=grade, subject=subject)
                    messages.success(request, "Đã thêm môn vào chương trình học!")
            except (Grade.DoesNotExist, Subject.DoesNotExist):
                messages.error(request, "Không tìm thấy khối hoặc môn học.")
            return redirect("subject_manage")

    context = {
        "subjects": subjects,
        "grades": grades,
        "curriculum": curriculum,
    }
    return render(request, "admin/subject_manage.html", context)

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

def delete_subject_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Đã xoá môn học.")
    return redirect("subject_manage")

@require_GET
def search_subjects_api(request):
    q = request.GET.get("q", "").strip()
    if q:
        subjects = Subject.objects.filter(subject_name__icontains=q).order_by("id")[:50]
    else:
        subjects = Subject.objects.all().order_by("id")[:50]

    results = [{"id": s.id, "name": s.subject_name} for s in subjects]
    return JsonResponse({"results": results})
