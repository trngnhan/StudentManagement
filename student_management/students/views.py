from io import BytesIO
import json
from datetime import datetime
from django.db.models import Exists, OuterRef
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import RestrictedError, Max
from django.views.decorators.http import require_GET, require_POST
from django_filters.rest_framework import DjangoFilterBackend
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from students.form import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.paginator import Paginator
from students.models import *
from students.serializers import *
from students.permissions import *
from datetime import date, datetime
import pickle
from datetime import time
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
from django.db import transaction
from functools import wraps
import streamlit as st
from django.db.models import Avg
from django.utils.text import slugify
from django.http import HttpResponseForbidden

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
    

# ==================== Phân Quyền =====================
def is_admin(user):
    return user.groups.filter(name="admin").exists()


def is_staff(user):
    return user.groups.filter(name="staff").exists()


def is_teacher(user):
    return user.groups.filter(name="teacher").exists()

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            role = request.session.get("role")
            print("ROLE == ",role)
            if role in allowed_roles:
                return view_func(request, *args, **kwargs)
            return redirect("login")
        return wrapper
    return decorator

#======================School Year======================
@login_required
@role_required("admin")
def schoolyear_manage_view(request):
    if request.method == "POST":
        name = request.POST.get("school_year_name")
        if not name:
            messages.error(request, "Tên năm học không được để trống.")
        elif SchoolYear.objects.filter(school_year_name=name).exists():
            messages.warning(request, "Năm học đã tồn tại.")
        else:
            SchoolYear.objects.create(school_year_name=name)
            messages.success(request, "Đã thêm năm học mới.")
        return redirect("schoolyear_manage_view")
    schoolyears = SchoolYear.objects.all()
    return render(request, "admin/schoolyear_manage.html", {"schoolyears": schoolyears})

@login_required
@require_GET
@role_required("admin")
def schoolyear_with_semesters_view(request):
    schoolyears = SchoolYear.objects.prefetch_related('semesters').all()
    data = []
    for sy in schoolyears:
        semesters = list(sy.semesters.values())
        sy_data = {
            "id": sy.id,
            "school_year_name": sy.school_year_name,
            "semesters": semesters
        }
        data.append(sy_data)
    return JsonResponse(data, safe=False)

@csrf_exempt
@role_required("admin")
def schoolyears_api_view(request):
    if request.method == "GET":
        schoolyears = SchoolYear.objects.all()
        data = [{"id": sy.id, "school_year_name": sy.school_year_name} for sy in schoolyears]
        return JsonResponse(data, safe=False)
    elif request.method == "POST":
        import json
        body = json.loads(request.body)
        name = body.get("school_year_name")
        if not name:
            return JsonResponse({"detail": "Thiếu tên năm học."}, status=400)
        sy = SchoolYear.objects.create(school_year_name=name)
        return JsonResponse({"id": sy.id, "school_year_name": sy.school_year_name}, status=201)

@login_required
@require_POST
@role_required("admin")
def schoolyear_delete_view(request, pk):
    try:
        school_year = SchoolYear.objects.get(pk=pk)
        school_year.delete()
        return JsonResponse({"message": "Đã xoá năm học."}, status=204)
    except RestrictedError:
        return JsonResponse(
            {"detail": "Không thể xoá năm học vì còn học kỳ liên kết. Vui lòng xoá học kỳ trước."},
            status=400
        )
    except SchoolYear.DoesNotExist:
        return JsonResponse({"detail": "Không tìm thấy năm học."}, status=404)
    
#======================Semester======================
@login_required
@role_required("admin")
def semesters_of_schoolyear_view(request, year_id):
    school_year = get_object_or_404(SchoolYear, id=year_id)
    semesters = Semester.objects.filter(school_year=school_year)
    return render(request, "admin/schoolyear_semesters.html", {
        "school_year": school_year,
        "semesters": semesters,
    })

@login_required
@role_required("admin")
def semester_edit_form_view(request, semester_id):
    semester = get_object_or_404(Semester, pk=semester_id)
    if request.method == "POST":
        semester_type = request.POST.get("semester_type")
        if semester_type is not None:
            if Semester.objects.filter(school_year=semester.school_year, semester_type=semester_type).exclude(id=semester.id).exists():
                messages.warning(request, "Học kỳ đã tồn tại.")
                return redirect("semesters_of_schoolyear_view", year_id=semester.school_year.id)
            semester.semester_type = semester_type
            semester.save()
            messages.success(request, "Đã cập nhật học kỳ.")
            return redirect("semesters_of_schoolyear_view", year_id=semester.school_year.id)
        else:
            messages.error(request, "Thiếu loại học kỳ.")
    return render(request, "admin/semester_edit.html", {"semester": semester})

@login_required
@require_POST
@role_required("admin")
def semester_create_view(request):
    school_year_id = request.POST.get("school_year")
    semester_type = request.POST.get("semester_type")

    if not school_year_id or semester_type is None:
        messages.error(request, "Thiếu trường năm học hoặc loại học kỳ.")
        return redirect("semesters_of_schoolyear_view", year_id=school_year_id)

    if Semester.objects.filter(school_year_id=school_year_id, semester_type=semester_type).exists():
        messages.warning(request, "Học kỳ này đã tồn tại trong năm học.")
        return redirect("semesters_of_schoolyear_view", year_id=school_year_id)

    Semester.objects.create(
        school_year_id=school_year_id,
        semester_type=semester_type
    )
    messages.success(request, "Đã thêm học kỳ mới.")
    return redirect("semesters_of_schoolyear_view", year_id=school_year_id)

@login_required
@require_POST
@role_required("admin")
def semester_update_view(request, semester_id):
    semester = get_object_or_404(Semester, pk=semester_id)
    semester_type = request.POST.get("semester_type")
    if semester_type is not None:
        if Semester.objects.filter(school_year=semester.school_year, semester_type=semester_type).exclude(id=semester.id).exists():
            messages.warning(request, "Học kỳ đã tồn tại.")
            return redirect("semesters_of_schoolyear_view", year_id=semester.school_year.id)
        semester.semester_type = semester_type
        semester.save()
        messages.success(request, "Đã cập nhật học kỳ.")
    else:
        messages.error(request, "Thiếu loại học kỳ.")
    return redirect("semesters_of_schoolyear_view", year_id=semester.school_year.id)

@login_required
@require_POST
@role_required("admin")
def semester_delete_view(request, semester_id):
    semester = get_object_or_404(Semester, pk=semester_id)
    year_id = semester.school_year.id
    semester.delete()
    messages.success(request, "Đã xoá học kỳ.")
    return redirect("semesters_of_schoolyear_view", year_id=year_id)
    
#======================Subject======================
@login_required
@require_GET
@role_required("admin")
def subject_manage_view(request):
    subjects = Subject.objects.all().order_by("id")
    grades = Grade.objects.all()
    #Thực hiện kết bảng related
    curriculums = Curriculum.objects.select_related('grade', 'subject').all()
    return render(request, "admin/subject_manage.html", {
        "subjects": subjects,
        "grades": grades,
        "curriculums": curriculums,
    })

@login_required
@require_POST
@role_required("admin")
def subject_delete_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Đã xoá môn học.")
    return redirect("subject_manage_view")

@login_required
@role_required("admin")
def edit_subject_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)

    if request.method == "POST":
        subject_name = request.POST.get("subject_name")
        if subject_name:
            subject.subject_name = subject_name
            subject.save()
            messages.success(request, "Đã cập nhật môn học.")
            return redirect("subject_manage_view")
        else:
            messages.error(request, "Tên môn học không được để trống.")

    return render(request, "admin/subject_edit.html", {"subject": subject})

@login_required
@require_POST
@role_required("admin")
def subject_add_view(request):
    subject_name = request.POST.get("subject_name")
    if not subject_name:
        messages.error(request, "Tên môn học không được để trống.")
        return redirect("subject_manage_view")
    if Subject.objects.filter(subject_name=subject_name).exists():
        messages.warning(request, "Tên môn học đã tồn tại.")
        return redirect("subject_manage_view")
    Subject.objects.create(subject_name=subject_name)
    messages.success(request, "Đã thêm môn học mới.")
    return redirect("subject_manage_view")

@login_required
@require_GET
@role_required("admin")
#Tìm theo từng kí tự khi tìm kiếm
def subject_search_view(request):
    q = request.GET.get("q", "").strip()
    subjects = Subject.objects.filter(subject_name__icontains=q) if q else Subject.objects.all()
    return render(request, "admin/subject_search.html", {"subjects": subjects, "q": q})

#======================Curiculum======================
@login_required
@require_GET
@role_required("admin")
def curriculum_list_view(request):
    curriculums = Curriculum.objects.select_related('grade', 'subject').all()
    return render(request, "admin/curriculum_list.html", {"curriculums": curriculums})

@login_required
@require_POST
@role_required("admin")
def curriculum_add_view(request):
    grade_id = request.POST.get("grade_id")
    subject_id = request.POST.get("subject_id")

    if not grade_id or not subject_id:
        messages.error(request, "Thiếu khối lớp hoặc môn học.")
        return redirect("subject_manage_view")

    try:
        grade = Grade.objects.get(id=grade_id)
        subject = Subject.objects.get(id=subject_id)
    except Grade.DoesNotExist:
        messages.error(request, "Không tìm thấy khối lớp.")
        return redirect("subject_manage_view")
    except Subject.DoesNotExist:
        messages.error(request, "Không tìm thấy môn học.")
        return redirect("subject_manage_view")

    if Curriculum.objects.filter(grade=grade, subject=subject).exists():
        messages.warning(request, "Môn học này đã tồn tại trong chương trình khối này.")
        return redirect("subject_manage_view")

    Curriculum.objects.create(grade=grade, subject=subject)
    messages.success(request, "Đã thêm môn học vào chương trình.")
    return redirect("subject_manage_view")

@login_required
@require_GET
@role_required("admin")
def curriculum_add_form_view(request):
    grades = Grade.objects.all()
    subjects = Subject.objects.all()
    return render(request, "admin/curriculum_add.html", {"grades": grades, "subjects": subjects})

@login_required
@require_GET
@role_required("admin")
def curriculum_list_view(request):
    curriculums = Curriculum.objects.select_related('grade', 'subject').all()
    return render(request, "admin/curriculum_list.html", {"curriculums": curriculums})

#======================Rule======================
@login_required
@require_GET
@role_required("admin")
def rules_list_get_view(request):
    role = request.session.get("role")
    if not role:
        return redirect("login")
    is_admin = role == "admin"
    is_teacher = role == "teacher"
    is_student = role == "student"
    rules = Rule.objects.all()
    context = {
        "rules": rules,
        "role": role,
        "is_admin": is_admin,
        "is_teacher": is_teacher,
        "is_student": is_student,
    }
    return render(request, "admin/rules_list.html", context)

@login_required
@require_POST
@role_required("admin")
def rules_list_post_view(request):
    for rule in Rule.objects.all():
        min_value = request.POST.get(f"min_value_{rule.id}")
        max_value = request.POST.get(f"max_value_{rule.id}")
        rule_content = request.POST.get(f"rule_content_{rule.id}")

        # Xử lý giá trị rỗng
        rule.min_value = float(min_value) if min_value not in [None, ''] else None
        rule.max_value = float(max_value) if max_value not in [None, ''] else None
        if rule_content is not None:
            rule.rule_content = rule_content
        rule.save()
    messages.success(request, "Đã cập nhật quy định.")
    return redirect("rules_list_get_view")

@login_required
@role_required("admin")
def admin_dashboard(request):
    if request.session.get("role") != "admin":
        return redirect('login')

    data = {
        "total_staff": StaffInfo.objects.count(),
        "total_teacher": TeacherInfo.objects.count(),
        "total_student": StudentInfo.objects.count(),
        "total_classroom": Classroom.objects.count(),
        "total_subject": Subject.objects.count(),
    }
    return render(request, "admin/admin_dashboard.html", {
        "username": request.session.get("username"),
        **data
    })

@role_required("staff", "admin")
@login_required
def camera_attendance(request):
    return render(request, "attendance/camera_attendance.html")


def verify_image(image, stage):
    try:
        st.write(f"{stage} image shape: {image.shape}, dtype: {image.dtype}")
        if len(image.shape) == 2 or image.shape[2] == 1:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        elif image.shape[2] != 3:
            raise ValueError(f"Unsupported image shape at {stage}: {image.shape}")
        if image.dtype != 'uint8':
            image = image.astype('uint8')
        return image
    except Exception as e:
        st.error(f"Error verifying image at {stage}: {e}")
        return None


@csrf_exempt
def mark_attendance(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")

    try:
        data_url = json.loads(request.body)["image"]
        if not data_url:
            return JsonResponse({"status": "error", "detail": "No image"}, status=400)
        # # tách base64
        # header, b64 = data_url.split(",", 1)
        # img_bytes = base64.b64decode(b64)
        # img_array = np.frombuffer(img_bytes, np.uint8)
        # frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        # #  chuyển về dạng -> RGB
        # rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # tách base64
        header, b64 = data_url.split(",", 1)
        img_bytes = base64.b64decode(b64)
        img_array = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)  # dùng UNCHANGED để giữ nguyên kênh

        # dùng verify_image để đảm bảo ảnh ở dạng RGB
        rgb = verify_image(frame, stage="mark_attendance")
        if rgb is None:
            return JsonResponse({"status": "error", "detail": "Invalid image format"}, status=400)


        # detect & encode
        locs = face_recognition.face_locations(rgb)
        if len(locs) == 0:
            return JsonResponse({"status": "no_face"})
        if len(locs) > 1:
            return JsonResponse({"status": "multi_face", "faces": len(locs)})

        # enc luôn là numpy array 128‑d
        enc = face_recognition.face_encodings(rgb, locs)[0]

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
        now = datetime.now()
        late_time = time(7, 15)

        att, _ = Attendance.objects.get_or_create(
            student=student,
            date=datetime.today(),
            defaults={
                "time_checked": now.time(),
                "is_late": now.time() > late_time,
            },
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

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Lấy tên role từ enum
            role_name = Role(user.role).label.lower()  # Ví dụ: "Admin" → "admin"

            # Lưu vào session
            request.session['username'] = user.username
            request.session['role'] = role_name

            # Chuyển hướng theo role
            if role_name == 'admin':
                return redirect('admin_dashboard')
            elif role_name == 'teacher':
                return redirect('teacher_class_list')
            elif role_name == 'student':
                return redirect('student_dashboard')
            elif role_name == 'staff':
                return redirect('student_list')
            else:
                return redirect('/')

        return render(request, "login.html", {"error": "Sai tên đăng nhập hoặc mật khẩu."})

    return render(request, "login.html")

def logout_view(request):
    request.session.flush()
    return redirect('login')

#======================Profile======================
@login_required
def profile_view(request):
    user = request.user
    role = None
    profile = None

    if hasattr(user, 'admin_info'):
        role = 'admin'
        profile = user.admin_info
    elif hasattr(user, 'teacher_info'):
        role = 'teacher'
        profile = user.teacher_info
    elif hasattr(user, 'staff_info'):
        role = 'staff'
        profile = user.staff_info
    elif hasattr(user, 'student_info'):
        role = 'student'
        profile = user.student_info

    # Nếu không xác định được role hoặc profile, chuyển về login
    if not profile or not role:
        return redirect('login')

    return render(request, 'profile.html', {
        'profile': profile,
        'role': role,
        'username': user.username,
    })


#======================Student======================
@login_required
@role_required("admin", "staff")
def student_list(request):
    students = StudentInfo.objects.all()
    return render(request, "students/student_list.html", {"students": students})

# Thêm mới học sinh
@login_required
@role_required("admin", "staff")
def student_create(request):
    if request.session.get("role") in ["staff", "admin"]:
        if request.method == "POST":    
            form = StudentForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Đã thêm học sinh thành công.")
                return redirect("student_list")
        else:
            form = StudentForm()
        return render(request, "students/student_form.html", {"form": form})

    return HttpResponseForbidden("Bạn không có quyền truy cập.")
# Sửa học sinh
@login_required
@role_required("admin", "staff")
def student_update(request, pk):
    if request.session.get("role") in ["staff", "admin"]:
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
@login_required
@role_required("admin", "staff")
def student_delete(request, pk):
    if request.session.get("role") in ["staff", "admin"]:
        student = get_object_or_404(StudentInfo, pk=pk)
        if request.method == "POST":
            student.delete()
            messages.success(request, "Đã xoá học sinh.")
            return redirect("student_list")
        return render(request, "students/student_confirm_delete.html", {"student": student})

#======================Teacher======================
@login_required
@role_required("teacher")
def teacher_class_list_view(request):
    teacher = get_object_or_404(TeacherInfo, user=request.user)

    selected_year = request.GET.get("school_year")
    selected_semester = request.GET.get("semester")

    transcripts = Transcript.objects.filter(teacher_info=teacher).select_related(
        "classroom",
        "classroom__grade",
        "semester",
        "semester__school_year"
    )

    if selected_year:
        transcripts = transcripts.filter(semester__school_year_id=selected_year)
    if selected_semester:
        transcripts = transcripts.filter(semester__semester_type=selected_semester)

    transcripts = transcripts.order_by(
        "semester__school_year__school_year_name",
        "semester__semester_type",
        "classroom__classroom_name"
    )

    class_list = []
    seen = set()
    for t in transcripts:
        key = (t.classroom.id, t.semester.id)
        if key not in seen:
            seen.add(key)
            class_list.append({
                "id": t.classroom.id,
                "name": t.classroom.classroom_name,
                "year": t.semester.school_year.school_year_name,
                "semester": t.semester.get_semester_type_display()
            })

    school_years = SchoolYear.objects.all()
    semesters = Semester.objects.all()

    return render(request, "teacher/teacher_class_list.html", {
        "classes": class_list,
        "school_years": school_years,
        "semesters": semesters,
        "selected_year": int(selected_year) if selected_year else None,
        "selected_semester": int(selected_semester) if selected_semester else None,
    })

@login_required
@role_required("teacher", "admin")
def teacher_subject_scores_view(request, classroom_id):
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

@login_required
@role_required("teacher", "admin")
def teacher_score_detail_view(request, transcript_id):
    transcript = get_object_or_404(Transcript, id=transcript_id)

    # === POST xử lý ===
    if request.method == "POST":
        # 1. Xuất Excel
        if "export_excel" in request.POST:
            wb = Workbook()
            ws = wb.active
            ws.title = "Scores"
            ws.append(["Học sinh", "Loại điểm", "Điểm"])

            for score in Score.objects.filter(transcript=transcript).select_related("student_info"):
                ws.append([
                    score.student_info.name,
                    score.get_score_type_display(),
                    score.score_number
                ])

            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)
            filename = f"bang_diem_{slugify(transcript.curriculum.subject.subject_name)}_{slugify(transcript.classroom.classroom_name)}.xlsx"

            response = HttpResponse(
                buffer.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename={filename}'
            return response

        # 2. Lưu điểm đã chỉnh sửa
        for key, value in request.POST.items():
            if key.startswith("score_") and value != "":
                try:
                    score_id = int(key.replace("score_", ""))
                    score = Score.objects.get(id=score_id)
                    score.score_number = float(value)
                    score.save()
                except Exception as e:
                    continue

        # 3. Thêm điểm mới
        rules = {r.rule_name: r for r in Rule.objects.all()}

        for key in request.POST:
            if key.startswith("add_score_for_"):
                student_id = key.replace("add_score_for_", "")
                try:
                    student = StudentInfo.objects.get(id=student_id)
                    score_type = int(request.POST.get(f"new_score_type_{student_id}", 0))
                    score_value = request.POST.get(f"new_score_value_{student_id}", None)
                    if score_value is None or score_value == "":
                        continue
                    score_value = float(score_value)
                except:
                    continue

                # Kiểm tra giới hạn theo quy định
                current_count = Score.objects.filter(
                    transcript=transcript,
                    student_info=student,
                    score_type=score_type
                ).count()

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
                        f"Học sinh {student.name} đã đủ số điểm {ScoreType(score_type).label}."
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
    students = (
        StudentInfo.objects.filter(
            classroom_transfers__classroom=transcript.classroom
        ).distinct().order_by("name")
    )

    grouped_scores = []
    for student in students:
        scores = Score.objects.filter(transcript=transcript, student_info=student).order_by("score_type")
        grouped_scores.append({
            "student": student,
            "scores": scores
        })

    return render(request, "teacher/teacher_score_detail.html", {
        "transcript": transcript,
        "grouped_scores": grouped_scores,
    })
#======================Classroom======================
@login_required
@role_required("admin")
def class_score_report_view(request):
    school_years = SchoolYear.objects.all()
    subjects = Subject.objects.all()

    # Lấy dữ liệu filter từ query params
    selected_subject = request.GET.get("subject")
    selected_year = request.GET.get("school_year")
    selected_semester = request.GET.get("semester")

    classrooms = Classroom.objects.all()
    if selected_year:
        classrooms = classrooms.filter(grade__school_year__school_year_name=selected_year)

    report_data = {
        'classes': [],
        'student_counts': [],
        'class_averages': [],
        'subjects_data': {}
    }

    #Tổng hợp điểm trung bình và số học sinh
    print(f"Processing {classrooms.count()} classrooms")
    
    for classroom in classrooms:
        transcripts = Transcript.objects.filter(classroom=classroom)
        if selected_semester:
            transcripts = transcripts.filter(semester__semester_type=selected_semester)

        scores = Score.objects.filter(
            transcript__in=transcripts,
            score_number__isnull=False
        )

        student_count = ClassroomTransfer.objects.filter(
            classroom=classroom
        ).values("student_info").distinct().count()

        avg_score = scores.aggregate(avg=Avg("score_number"))["avg"] or 0

        # Thêm năm học vào tên lớp để phân biệt
        school_year = classroom.grade.school_year.school_year_name
        label = f"{classroom.classroom_name} ({school_year})"
        print(f"Classroom: {label}, Students: {student_count}, Avg: {avg_score}")
        
        report_data["classes"].append(label)
        report_data["student_counts"].append(student_count)
        report_data["class_averages"].append(round(avg_score, 2))

    #Điểm từng môn học
    for subject in subjects:
        subject_scores = {}
        for classroom in classrooms:
            scores = Score.objects.filter(
                transcript__classroom=classroom,
                transcript__curriculum__subject=subject,
                score_number__isnull=False
            )
            if selected_semester:
                scores = scores.filter(transcript__semester__semester_type=selected_semester)
            if selected_year:
                scores = scores.filter(transcript__classroom__grade__school_year__school_year_name=selected_year)

            school_year = classroom.grade.school_year.school_year_name
            label = f"{classroom.classroom_name} ({school_year})"
            avg = scores.aggregate(avg=Avg("score_number"))["avg"]
            subject_scores[label] = round(avg or 0, 2)
        report_data["subjects_data"][subject.subject_name] = subject_scores

    context = {
        "report_data": report_data,
        "school_years": school_years,
        "subjects": subjects,
    }
    return render(request, "admin/class_score_report.html", context)

# =========== Nhân Viên ==============
@login_required
@role_required("staff", "admin")
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

@login_required
@role_required("staff", "admin")
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

@login_required
@role_required("staff", "admin")
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


@login_required
@role_required("staff", "admin")
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

@login_required
@role_required("staff", "admin")
def class_management(request):
    classes =classes = Classroom.objects.select_related("grade", "grade__school_year").order_by("grade__grade_type", "classroom_name")

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
    return render(request, "classroom/class_management.html", context)


@login_required
@role_required("staff", "admin")
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


@login_required
@role_required("staff", "admin")
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


@login_required
@role_required("staff", "admin")
def classroom_delete(request, pk):
    classroom = get_object_or_404(Classroom, pk=pk)
    if request.method == "POST":
        classroom.delete()
        messages.success(request, f"Đã xóa lớp {classroom.classroom_name}.")
        return redirect("classroom_management")

    return render(request, "classroom/classroom_confirm_delete.html",
                  {"classroom": classroom})



@login_required
@role_required("staff", "admin")
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


@login_required
@role_required("staff", "admin")
def attendance_management(request):
    date_param = request.GET.get("date")
    if date_param:
        try:
            selected_date = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            selected_date = timezone.localdate()
    else:
        selected_date = timezone.localdate()

    # Lấy lớp kèm thông tin năm học
    classes = (
        Classroom.objects
        .select_related("grade", "grade__school_year")
        .order_by("grade__grade_type", "classroom_name")
    )

    attended_qs = Attendance.objects.filter(student=OuterRef("pk"), date=selected_date)
    students_not_checked = (
        StudentInfo.objects
        .annotate(has_checked=Exists(attended_qs))
        .filter(has_checked=False)
    )

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
    print(context)
    return render(request, "attendance/attendance_management.html", context)



@login_required
@role_required("staff", "admin")
@require_POST
@transaction.atomic
def save_attendance(request):
    class_id   = request.POST.get('class_id')
    date_str   = request.POST.get('date')
    attended   = request.POST.getlist('attended')

    classroom  = get_object_or_404(Classroom, pk=class_id)
    try:
        date_obj = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        messages.error(request, "Ngày không hợp lệ.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    students_in_class = [ s for s in StudentInfo.objects.all() if s.get_current_classroom() == classroom]
    now_time = timezone.localtime().time()

    for student in students_in_class:
        if str(student.id) in attended:
            is_late = now_time > time(7, 30)
            Attendance.objects.update_or_create(
                student=student,
                date=date_obj,
                defaults={"time_checked": now_time, "is_late": is_late},
            )

    messages.success(request, "Lưu điểm danh thành công.")
    return redirect("attendance_management")

@login_required
@role_required("student")
def student_dashboard_view(request):
    student = get_object_or_404(StudentInfo, user=request.user)

    # --- Lấy danh sách năm học ---
    school_years = SchoolYear.objects.all().order_by("-school_year_name")
    selected_school_year_id = request.GET.get("school_year")
    selected_semester_type = request.GET.get("semester", "all")

    # Nếu chưa chọn, mặc định chọn năm học mới nhất
    if not selected_school_year_id and school_years.exists():
        selected_school_year_id = school_years.first().id

    selected_school_year = None
    if selected_school_year_id:
        selected_school_year = get_object_or_404(SchoolYear, id=selected_school_year_id)

    summary = {
        "HK1": {"avg": None, "grade": None},
        "HK2": {"avg": None, "grade": None},
        "overall": {"avg": None, "grade": None}
    }
    conduct = {"HK1": None, "HK2": None, "overall": None}

    if selected_school_year:
        semesters = Semester.objects.filter(school_year=selected_school_year)

        # Tính điểm TB và học lực cho từng học kỳ
        for sem in semesters:
            avg_scores = []
            transcripts = Transcript.objects.filter(semester=sem, scores__student_info=student).distinct()
            for tr in transcripts:
                avg = Score.objects.filter(transcript=tr, student_info=student).aggregate(avg=Avg("score_number"))["avg"]
                if avg is not None:
                    avg_scores.append(avg)

            if avg_scores:
                semester_avg = round(sum(avg_scores) / len(avg_scores), 2)
                summary[f"HK{sem.semester_type}"]["avg"] = semester_avg
                # Xếp loại học lực
                if semester_avg >= 8:
                    summary[f"HK{sem.semester_type}"]["grade"] = "Giỏi"
                elif semester_avg >= 6.5:
                    summary[f"HK{sem.semester_type}"]["grade"] = "Khá"
                elif semester_avg >= 5:
                    summary[f"HK{sem.semester_type}"]["grade"] = "Trung bình"
                else:
                    summary[f"HK{sem.semester_type}"]["grade"] = "Yếu"

            # Lấy hạnh kiểm
            cr = ConductRecord.objects.filter(student=student, semester=sem).first()
            if cr:
                conduct[f"HK{sem.semester_type}"] = cr.conduct

        # Tính cả năm nếu đủ 2 học kỳ có điểm
        if summary["HK1"]["avg"] is not None and summary["HK2"]["avg"] is not None:
            overall_avg = round((summary["HK1"]["avg"] + summary["HK2"]["avg"]) / 2, 2)
            summary["overall"]["avg"] = overall_avg
            if overall_avg >= 8:
                summary["overall"]["grade"] = "Giỏi"
            elif overall_avg >= 6.5:
                summary["overall"]["grade"] = "Khá"
            elif overall_avg >= 5:
                summary["overall"]["grade"] = "Trung bình"
            else:
                summary["overall"]["grade"] = "Yếu"

            # Xét hạnh kiểm cả năm (ưu tiên học kỳ 2, nếu trống thì lấy HK1)
            conduct["overall"] = conduct["HK2"] or conduct["HK1"]

    overall_avg = summary["overall"]["avg"]
    overall_grade = summary["overall"]["grade"]
    overall_conduct = conduct["overall"]

    return render(request, "students/student_dashboard.html", {
        "student": student,
        "school_years": school_years,
        "selected_school_year_id": int(selected_school_year_id) if selected_school_year_id else None,
        "selected_semester_type": selected_semester_type,
        "summary": summary,
        "conduct": conduct,
        "overall_avg": overall_avg,
        "overall_grade": overall_grade,
        "overall_conduct": overall_conduct,
    })

def get_grade_label(avg):
    if avg >= 8:
        return "Giỏi"
    elif avg >= 6.5:
        return "Khá"
    elif avg >= 5:
        return "Trung bình"
    else:
        return "Yếu"

@login_required
@role_required("student")
def student_view_scores(request):
    student = get_object_or_404(StudentInfo, user=request.user)

    school_years = SchoolYear.objects.all()
    semesters = Semester.objects.select_related('school_year')

    selected_school_year_id = request.GET.get("school_year")
    selected_semester_id = request.GET.get("semester")

    scores_by_transcript = []
    semester_avg = None  # Thêm biến lưu điểm TB học kỳ

    if selected_school_year_id and selected_semester_id:
        transcripts = Transcript.objects.filter(
            scores__student_info=student,
            semester_id=selected_semester_id,
            semester__school_year_id=selected_school_year_id
        ).select_related(
            'curriculum__subject',
            'semester__school_year',
            'classroom',
            'teacher_info'
        ).distinct()

        total_avg = 0
        count_subjects = 0

        for tr in transcripts:
            scores = Score.objects.filter(transcript=tr, student_info=student).order_by("score_type")
            average = scores.aggregate(avg=Avg("score_number"))["avg"]

            scores_by_transcript.append({
                "subject": tr.curriculum.subject.subject_name,
                "teacher": tr.teacher_info.name if tr.teacher_info else "N/A",
                "semester": tr.semester.get_semester_type_display(),
                "classroom": tr.classroom.classroom_name,
                "scores": scores,
                "average": round(average, 2) if average is not None else None,
            })

            # Chỉ cộng những môn có điểm
            if average is not None:
                total_avg += average
                count_subjects += 1

        if count_subjects > 0:
            semester_avg = round(total_avg / count_subjects, 2)

    return render(request, "students/student_scores.html", {
        "student": student,
        "school_years": school_years,
        "semesters": semesters,
        "score_groups": scores_by_transcript,
        "selected_school_year_id": int(selected_school_year_id) if selected_school_year_id else None,
        "selected_semester_id": int(selected_semester_id) if selected_semester_id else None,
        "semester_avg": semester_avg,
    })


def assign_teacher(request):
    if request.method == "POST":
        classroom_id = request.POST.get("classroom")
        curriculum_id = request.POST.get("curriculum")
        teacher_id = request.POST.get("teacher_info")
        semester_id = request.POST.get("semester")
        transcript_id = request.POST.get("transcript_id")

        try:
            classroom = Classroom.objects.get(id=classroom_id)
            curriculum = Curriculum.objects.get(id=curriculum_id)
            teacher = TeacherInfo.objects.get(id=teacher_id)
            semester = Semester.objects.get(id=semester_id)

            # Update
            if transcript_id:
                transcript = Transcript.objects.get(id=transcript_id)
                transcript.classroom = classroom
                transcript.curriculum = curriculum
                transcript.teacher_info = teacher
                transcript.semester = semester
                transcript.save()
                messages.success(request, "Cập nhật phân công thành công!")
            else:
                # Kiểm tra trùng lặp
                exists = Transcript.objects.filter(
                    classroom=classroom,
                    curriculum=curriculum,
                    semester=semester
                ).exists()

                if exists:
                    messages.error(request, "Phân công này đã tồn tại.")
                else:
                    Transcript.objects.create(
                        classroom=classroom,
                        curriculum=curriculum,
                        teacher_info=teacher,
                        semester=semester
                    )
                    messages.success(request, "Phân công giảng viên thành công!")

        except (Classroom.DoesNotExist, Curriculum.DoesNotExist, TeacherInfo.DoesNotExist, Semester.DoesNotExist):
            messages.error(request, "Dữ liệu không hợp lệ.")

        return redirect("assign_teacher")

   # Lấy danh sách transcripts
    transcripts = Transcript.objects.all().select_related("classroom", "curriculum__subject", "teacher_info", "semester__school_year")

    year = request.GET.get('year')
    teacher_name = request.GET.get('teacher')
    semester = request.GET.get('semester')
    class_name = request.GET.get('class_name')

    if year:
        transcripts = transcripts.filter(
            semester__school_year__school_year_name__icontains=year
        )

    if teacher_name:
        transcripts = transcripts.filter(
            teacher_info__name__icontains=teacher_name
        )

    if semester:
        transcripts = transcripts.filter(
            semester__semester_type=semester
        )

    if class_name:
        transcripts = transcripts.filter(
            classroom__classroom_name__icontains=class_name)

    paginator = Paginator(transcripts, 10)
    page_number = request.GET.get("page")
    transcripts = paginator.get_page(page_number)

    context = {
        "classrooms": Classroom.objects.all(),
        "curriculums": Curriculum.objects.all(),
        "teachers": TeacherInfo.objects.all(),
        "semesters": Semester.objects.all(),
        "transcripts": transcripts
    }
    return render(request, "classroom/assign_teacher.html", context)
