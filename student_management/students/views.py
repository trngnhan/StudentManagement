from io import BytesIO

import openpyxl
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import RestrictedError, Max
from django.views.decorators.http import require_GET
from django_filters.rest_framework import DjangoFilterBackend
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from students.form import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.paginator import Paginator
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
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.conf import settings
from rest_framework import serializers
from collections import defaultdict
from django.db.models import Avg, Count, Q, Max
from django.db.models import Q
from django.db import transaction

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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        user = request.user

        if hasattr(user, "admin_info"):
            role = "admin"
        elif hasattr(user, "teacher_info"):
            role = "teacher"
        elif hasattr(user, "student_info"):
            role = "student"
        else:
            role = "unknown"

        return Response({
            "username": user.username,
            "role": role
        })


class AdminInfoViewSet(viewsets.ModelViewSet):
    queryset = AdminInfo.objects.all()
    serializer_class = AdminInfoSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        data = {
            "total_staff": StaffInfo.objects.count(),
            "total_teacher": TeacherInfo.objects.count(),
            "total_student": StudentInfo.objects.count(),
            "total_classroom": Classroom.objects.count(),
            "total_subject": Subject.objects.count(),
        }
        return Response(data)


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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='with-semesters')
    def with_semesters(self, request):
        queryset = self.get_queryset().prefetch_related('semesters')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["delete"], url_path="", url_name="delete")
    def delete_schoolyear(self, request, pk=None):
        try:
            school_year = self.get_object()
            school_year.delete()
            return Response({"message": "Đã xoá năm học."}, status=status.HTTP_204_NO_CONTENT)
        except RestrictedError:
            return Response(
                {"detail": "Không thể xoá năm học vì còn học kỳ liên kết. Vui lòng xoá học kỳ trước."},
                status=status.HTTP_400_BAD_REQUEST
            )


class SemesterViewSet(viewsets.ModelViewSet):
    queryset = Semester.objects.all()
    serializer_class = SemesterSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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
        serializer = self.get_serializer(semester)
        return Response(serializer.data, status=201)

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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='search', url_name='subject-search')
    def search(self, request):
        q = request.GET.get("q", "").strip()
        subjects = self.queryset.filter(subject_name__icontains=q)[:50] if q else self.queryset[:50]
        data = [{"id": s.id, "subject_name": s.subject_name} for s in subjects]
        return Response({"results": data})

class CurriculumViewSet(viewsets.ModelViewSet):
    queryset = Curriculum.objects.select_related('grade', 'subject').all()
    serializer_class = CurriculumSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

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
    authentication_classes = [JWTAuthentication]
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
    context = {
        "access_token": request.session.get("access"),
    }
    return render(request, 'admin/rules_list.html', context)

def subject_manage_view(request):
    print("access =", request.session.get("access"))
    print("user =", request.user)
    print("authenticated =", request.user.is_authenticated)

    context = {
        "access_token": request.session.get("access"),
    }

    return render(request, 'admin/subject_manage.html', context)

def camera_attendance(request):
    return render(request, "attendance/camera_attendance.html")


def students(request):
    if not request.session.get('access'):
        return redirect('login')
    
    return render(request, "teacher/student.html")

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
            if dist < 0.5:
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
                return redirect('teacher_class_list')
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

    context = {
        "access_token": request.session.get("access"),
    }
    return render(request, "admin/schoolyear_manage.html", context)

def semesters_of_schoolyear_view(request, year_id):
    if not request.session.get("access"):
        return redirect("login")

    school_year = get_object_or_404(SchoolYear, id=year_id)
    semesters = Semester.objects.filter(school_year=school_year)

    return render(request, "admin/schoolyear_semesters.html", {
        "school_year": school_year,
        "semesters": semesters,
        "access_token": request.session.get("access"),
    })


@login_required
def student_create(request):
    if request.method == "POST":
        s_form = StudentForm(request.POST, request.FILES)
        p_form = ParentForm(request.POST)
        if s_form.is_valid() and p_form.is_valid():
            student = s_form.save()           
            parent  = p_form.save(commit=False)
            parent.student = student       
            parent.save()   
            messages.success(request, "Đã tạo Học sinh thành công!")
            return redirect("student_list")
    else:
        s_form = StudentForm()
        p_form = ParentForm()

    return render(request, "students/student_form.html",
                  {"s_form": s_form, "p_form": p_form})


def student_list(request):
    students = StudentInfo.objects.all()
    print(students)
    return render(request, "students/student_list.html", {"students": students})

# Thêm mới học sinh
def student_create(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã thêm học sinh thành công.")
            return redirect("student_list")
    else:
        form = StudentForm()
    return render(request, "students/student_form.html", {"form": form})

# Sửa học sinh
def student_update(request, pk):
    student = get_object_or_404(StudentInfo, pk=pk)
    if request.method == "POST":
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật học sinh.")
            return redirect("student_list")
    else:
        form = StudentForm(instance=student)
    return render(request, "students/student_form.html", {"form": form})

# Xoá học sinh
def student_delete(request, pk):
    student = get_object_or_404(StudentInfo, pk=pk)
    if request.method == "POST":
        student.delete()
        messages.success(request, "Đã xoá học sinh.")
        return redirect("student_list")
    return render(request, "students/student_confirm_delete.html", {"student": student})

def teacher_class_list_view(request):
    if request.session.get("role") != "teacher":
        return redirect("login")

    teacher = get_object_or_404(TeacherInfo, user__username=request.session.get("username"))

    class_ids = Transcript.objects.filter(teacher_info=teacher).values_list("classroom_id", flat=True).distinct()
    classes = Classroom.objects.filter(id__in=class_ids).order_by("classroom_name")

    return render(request, "teacher/teacher_class_list.html", {
        "classes": classes,
    })


def teacher_subject_scores_view(request, classroom_id):
    if request.session.get("role") != "teacher":
        return redirect("login")

    teacher = get_object_or_404(TeacherInfo, user__username=request.session.get("username"))
    classroom = get_object_or_404(Classroom, id=classroom_id)

    transcripts = Transcript.objects.filter(teacher_info=teacher, classroom=classroom)

    subjects = [{
        'subject_id': tr.curriculum.subject.id,
        'subject_name': tr.curriculum.subject.subject_name,
        'transcript_id': tr.id,
    } for tr in transcripts]

    return render(request, "teacher/teacher_subjects.html", {
        "classroom": classroom,
        "subjects": subjects,
    })

def teacher_score_detail_view(request, transcript_id):
    if request.session.get("role") != "teacher":
        return redirect("login")

    transcript = get_object_or_404(Transcript, id=transcript_id)

    # === POST xử lý lưu hoặc thêm điểm ===
    if request.method == "POST":
        # === Xuất Excel ===
        if "export_excel" in request.POST:
            wb = Workbook()
            ws = wb.active
            ws.title = "Scores"

            ws.append(["Học sinh", "Loại điểm", "Điểm"])

            for score in Score.objects.filter(transcript=transcript).select_related("student_info"):
                ws.append([score.student_info.name, score.get_score_type_display(), score.score_number])

            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            response = HttpResponse(buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename=bang_diem_{transcript.classroom.classroom_name}.xlsx'
            return response

        # === Lưu điểm đã chỉnh sửa ===
        for key, value in request.POST.items():
            if key.startswith("score_"):
                try:
                    score_id = int(key.replace("score_", ""))
                    score = Score.objects.get(id=score_id)
                    score.score_number = float(value)
                    score.save()
                except:
                    continue

        # === Thêm điểm mới ===
        rules = {r.rule_name: r for r in Rule.objects.all()}

        for key in request.POST:
            if key.startswith("add_score_for_"):
                student_id = key.replace("add_score_for_", "")
                try:
                    student = StudentInfo.objects.get(id=student_id)
                    score_type = int(request.POST.get(f"new_score_type_{student_id}"))
                    score_value = float(request.POST.get(f"new_score_value_{student_id}"))
                except:
                    continue

                # Kiểm tra giới hạn theo quy định
                current_count = Score.objects.filter(
                    transcript=transcript,
                    student_info=student,
                    score_type=score_type
                ).count()

                score_type_map = {
                    ScoreType.SCORE_15_MIN: "15 phút",
                    ScoreType.SCORE_1_PERIOD: "1 tiết",
                    ScoreType.FINAL_EXAM: "thi cuối kỳ",
                }

                rule = None
                if score_type == ScoreType.SCORE_15_MIN:
                    rule = rules.get("score_15_min_max")
                elif score_type == ScoreType.SCORE_1_PERIOD:
                    rule = rules.get("test_1_min_max")
                elif score_type == ScoreType.FINAL_EXAM:
                    rule = rules.get("final_exam_required")

                if rule and rule.max_value is not None and current_count >= rule.max_value:
                    messages.error(
                        request,
                        f"Học sinh {student.name} đã đủ số điểm {score_type_map.get(score_type, 'khác')} theo quy định."
                    )
                else:
                    Score.objects.create(
                        student_info=student,
                        transcript=transcript,
                        score_type=score_type,
                        score_number=score_value
                    )
                    messages.success(request, f"Đã thêm điểm cho học sinh {student.name}.")

        return redirect("teacher_score_detail_view", transcript_id=transcript.id)

    # === GET: Hiển thị dữ liệu ===
    scores = Score.objects.filter(transcript=transcript).select_related("student_info").order_by("score_type")
    grouped_scores = {}
    for score in scores:
        sid = score.student_info.id
        if sid not in grouped_scores:
            grouped_scores[sid] = {
                "student": score.student_info,
                "scores": []
            }
        grouped_scores[sid]["scores"].append(score)

    return render(request, "teacher/teacher_score_detail.html", {
        "transcript": transcript,
        "grouped_scores": list(grouped_scores.values()),
    })

def class_score_report_view(request):
    if request.session.get("role") != "admin":
        return redirect("login")

    classes = Classroom.objects.all().order_by("classroom_name")
    report = []

    for classroom in classes:
        # Lấy học sinh đang thuộc lớp này (giả sử transfer mới nhất là lớp hiện tại)
        latest_transfers = ClassroomTransfer.objects.filter(classroom=classroom).values('student_info').annotate(
            latest_id=Max('id')
        )
        latest_transfer_ids = [item['latest_id'] for item in latest_transfers]
        students = StudentInfo.objects.filter(classroom_transfers__id__in=latest_transfer_ids).distinct()
        student_count = students.count()

        # Tính điểm trung bình từng học sinh
        student_scores = []
        for student in students:
            avg_score = Score.objects.filter(student_info=student).aggregate(avg=Avg("score_number"))["avg"]
            student_scores.append(avg_score if avg_score is not None else 0)
        class_avg = sum(student_scores) / student_count if student_count > 0 else 0

        report.append({
            "classroom": classroom,
            "student_count": student_count,
            "class_avg": round(class_avg, 2),
        })

    return render(request, "admin/class_score_report.html", {
        "report": report,
    })

def search_student_list(request):
    q = request.GET.get('q', '').strip()
    students = StudentInfo.objects.all()
    if q:
        if q.isdigit():
            students = students.filter(id=int(q))
        else:
            students = students.filter(
                Q(user__username__icontains=q) | Q(name__icontains=q)
            )

    # --- Phân trang ---
    page_number = request.GET.get('page', 1)
    paginator = Paginator(students, 10)
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "q": q,
    }

    context = {"students": students, "q": q}
    return render(request, "students\student_list.html", context)


def classroom_create(request):
    if request.method == "POST":
        form = ClassroomForm(request.POST)
        if form.is_valid():
            classroom = form.save(commit=False)
            classroom.student_number = 0
            classroom.save()
            messages.success(request, "Đã tạo lớp thành công.")
            return redirect("classroom_create")
    else:
        form = ClassroomForm()
    return render(request, "classroom\create.html", {"form": form})


def add_student_to_classroom(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        form = AddStudentForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data["student"]
            if student.get_current_classroom():
                messages.warning(request, "Học sinh đã có lớp.")
            else:
                ClassroomTransfer.objects.create(
                    student_info=student,
                    classroom=classroom,
                    transfer_date=form.cleaned_data.get("transfer_date"),
                )
                classroom.student_number += 1
                classroom.save(update_fields=["student_number"])
                messages.success(request, f"Đã thêm {student.name} vào lớp {classroom}.")
                return redirect("add_student_to_classroom", pk=pk)
    else:
        form = AddStudentForm()
    return render(request, "classroom/add_student.html", {"form": form, "classroom": classroom})


@transaction.atomic
def transfer_student(request):
    if request.method == "POST":
        form = TransferStudentForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data["student"]
            new_classroom = form.cleaned_data["new_classroom"]
            old_classroom = student.get_current_classroom()
            if old_classroom == new_classroom:
                messages.warning(request, "Học sinh đã ở lớp này.")
            else:
                ClassroomTransfer.objects.create(
                    student_info=student,
                    classroom=new_classroom,
                    transfer_date=form.cleaned_data.get("transfer_date"),
                )
                if old_classroom:
                    old_classroom.student_number = max(0, old_classroom.student_number - 1)
                    old_classroom.save()
                new_classroom.student_number += 1
                new_classroom.save()
                messages.success(request, f"Đã chuyển {student.name} sang lớp {new_classroom}.")
                return redirect("transfer_student")
    else:
        form = TransferStudentForm()
    return render(request, "classroom/transfer.html", {"form": form})


def class_management(request):
    classes = Classroom.objects.select_related("grade").order_by("grade__grade_type", "classroom_name")

    students = (
        StudentInfo.objects
        .annotate(last_date=Max("classroom_transfers__transfer_date"))
        .select_related()
    )

    students_by_class = {}
    for s in students:
        cur = s.get_current_classroom()
        if cur:
            lst = students_by_class.setdefault(cur.id, [])
            lst.append({"id": s.id, "name": s.name})

    students_json_by_class = {
        k: json.dumps(v, ensure_ascii=False) for k, v in students_by_class.items()
    }

    context = {
        "classes": classes,
        "studentsByClass": students_json_by_class,
        "students": students.filter(last_date__isnull=True),
    }
    print(context)
    return render(request, "classroom/class_management.html", context)


def classroom_add_students_bulk(request):
    if request.method == "POST":
        class_id = request.POST.get("class_id")
        student_ids = request.POST.getlist("student_ids")
        classroom = get_object_or_404(Classroom, id=class_id)
        added = 0
        for student_id in student_ids:
            student = StudentInfo.objects.get(id=student_id)
            # kiểm tra đã có lớp chưa
            if student.get_current_classroom() != classroom:
                ClassroomTransfer.objects.create(
                    student_info=student,
                    classroom=classroom,
                    transfer_date=timezone.now()
                )
                added += 1
        
        if added:
            classroom.student_number += added
            classroom.save(update_fields=["student_number"])
            messages.success(request, f"Đã thêm {added} học sinh vào lớp {classroom.classroom_name}.")
        else:
            messages.warning(request, "Không có học sinh nào được thêm.")
    return redirect("classroom_management")

def classroom_update(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        form = ClassroomForm(request.POST, instance=classroom)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật lớp học.")
            return redirect("classroom_management")
    else:
        form = ClassroomForm(instance=classroom)

    return render(request, "classroom/classroom_update.html",
                  {"form": form, "classroom": classroom})


def classroom_delete(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        classroom.delete()
        messages.success(request, f"Đã xóa lớp {classroom.classroom_name}.")
        return redirect("classroom_management")

    return render(request, "classroom/classroom_confirm_delete.html",
                  {"classroom": classroom})


def classroom_transfer_students_bulk(request):
    if request.method == "POST":
        # Lớp nguồn & lớp đích
        src_class_id  = request.POST.get("class_id")
        dest_class_id = request.POST.get("new_class_id")
        src_class     = get_object_or_404(Classroom, pk=src_class_id)
        dest_class    = get_object_or_404(Classroom, pk=dest_class_id)

        student_ids   = request.POST.getlist("student_ids")
        transfer_date = request.POST.get("transfer_date") or timezone.now().date()

        if not student_ids:
            messages.warning(request, "Bạn chưa chọn học sinh nào.")
            return redirect("classroom_management")

        moved = 0
        for sid in student_ids:
            try:
                student = StudentInfo.objects.get(pk=sid)
            except StudentInfo.DoesNotExist:
                continue

            # Bỏ qua nếu đã ở lớp đích
            if student.get_current_classroom() == dest_class:
                continue

            # Tạo bản ghi chuyển lớp
            ClassroomTransfer.objects.create(
                student_info  = student,
                classroom     = dest_class,
                transfer_date = transfer_date,
                changed_classroom = True,
            )
            moved += 1

        # Cập nhật sĩ số hai lớp (nếu thực sự có HS được chuyển)
        if moved:
            src_class.student_number = max(0, src_class.student_number - moved)
            dest_class.student_number += moved
            src_class.save(update_fields=["student_number"])
            dest_class.save(update_fields=["student_number"])
            messages.success(
                request,
                f"Đã chuyển {moved} học sinh sang lớp {dest_class.classroom_name}."
            )
        else:
            messages.info(request, "Không có học sinh nào được chuyển.")

    # Quay về trang quản lý lớp
    return redirect("classroom_management")


# views.py
import json
from datetime import datetime
from django.db.models import Exists, OuterRef
from django.shortcuts import render
from django.utils import timezone

from .models import Classroom, StudentInfo, Attendance


def attendance_management(request):
    # 1. Ngày cần kiểm tra
    date_param = request.GET.get("date")         
    if date_param:                                
        try:
            selected_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            selected_date = timezone.localdate() 
    else:
        selected_date = timezone.localdate()
    # 2. Danh sách lớp
    classes = (
        Classroom.objects
        .select_related("grade")
        .order_by("grade__grade_type", "classroom_name")
    )

    # 3. Subquery kiểm tra đã điểm danh?
    attended_qs = Attendance.objects.filter(student=OuterRef("pk"), date=selected_date)
    students_not_checked = (
        StudentInfo.objects
        .annotate(has_checked=Exists(attended_qs))
        .filter(has_checked=False)
    )

    # 4. Gom vào dict theo lớp hiện tại
    students_by_class = {}
    for stu in students_not_checked:
        cur_cls = stu.get_current_classroom()
        if cur_cls:
            students_by_class.setdefault(cur_cls.id, []).append({
                "id": stu.id,
                "name": stu.name,
                "gender_display": stu.get_gender_display(),
                "birthday": stu.birthday.strftime("%d/%m/%Y") if stu.birthday else ""
            })

    students_json_by_class = {
        cid: json.dumps(lst, ensure_ascii=False) for cid, lst in students_by_class.items()
    }

    context = {
        "date": selected_date,
        "classes": classes,
        "students_by_class": students_json_by_class
    }
    return render(request, "attendance/attendance_management.html", context)
