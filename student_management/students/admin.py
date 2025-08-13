from django.contrib import admin, messages
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
import pickle
import time
import streamlit as st

import cv2
import numpy as np
import face_recognition
from .models import (
    User, AdminInfo, StaffInfo, TeacherInfo, ParentInfo,
    SchoolYear, Semester, Grade, Classroom, StudentInfo, ClassroomTransfer,
    Subject, Curriculum, Transcript, Score, Attendance, Rule, ConductRecord
)


class SchoolAdminSite(admin.AdminSite):
    site_header = "STUDENT MANAGEMENT"
    site_title = "School Admin"
    index_title = "Bảng điều khiển"


admin_site = SchoolAdminSite(name="admin")



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
    


def enroll(tolerance: float = 0.6, frames_per_pose: int = 5):
    directions = [
        ("NHIN THANG", (0, 0)),
        ("QUAY TRAI", (-30, 0)),
        ("QUAY PHAI", (30, 0)),
        ("NGANG LEN", (0, -20)),
        ("CUI XUONG", (0, 20)),
    ]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Không mở được webcam – bỏ qua lấy gương mặt")
        return None

    encodings = []
    try:
        for label, _ in directions:
            collected = 0
            start = time.time()
            while collected < frames_per_pose:
                ret, frame = cap.read()
                if not ret:
                    continue

                cv2.putText(frame, f"HAY {label}", (30, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow("Enroll", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    cap.release()
                    cv2.destroyAllWindows()
                    return None

                if time.time() - start > 0.5:
                    start = time.time()
                    # # chuyển từ BGR to RGB (dlib cần)
                    # rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    # Dùng verify_image để đảm bảo ảnh RGB chuẩn
                    rgb = verify_image(frame, stage=f"enroll_{label}")
                    if rgb is None:
                        continue

                    locs = face_recognition.face_locations(rgb)
                    if len(locs) != 1:
                        continue
                    enc = face_recognition.face_encodings(rgb, locs)[0]
                    encodings.append(enc)
                    collected += 1
                    print(f"  + Đã lấy {collected}/{frames_per_pose} frame cho tư thế {label}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    if not encodings:
        return None

    # Gộp vector giống nhau
    filtered = []
    for v in encodings:
        if not any(face_recognition.face_distance([u], v)[0] < tolerance for u in filtered):
            filtered.append(v)

    rep = np.mean(filtered, axis=0)
    return rep


class SoftDeleteFilter(admin.SimpleListFilter):

    title = "Trạng thái"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (
            ("active", "Hoạt động"),
            ("inactive", "Ngừng hoạt động"),
        )

    def queryset(self, request, queryset):
        if self.value() == "active":
            return queryset.filter(status=True)
        if self.value() == "inactive":
            return queryset.filter(status=False)
        return queryset


@admin.register(User, site=admin_site)
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "avatar_preview",
        "first_name",
        "last_name",
        "email",
        "role",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" width="40" height="40" style="border-radius:50%;object-fit:cover;"/>', obj.avatar.url)
        return "-"
    
    def save_model(self, request, obj, form, change):
        raw_pwd = form.cleaned_data["password"]
        if change:
            if "password" in form.changed_data:
                obj.set_password(raw_pwd)
        else:
            obj.set_password(raw_pwd)
        super().save_model(request, obj, form, change)

    avatar_preview.short_description = "Avatar"
    avatar_preview.admin_order_field = "avatar"


class PersonalInfoAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "gender",
        "phone",
        "email",
        "birthday",
        "status",
    )
    list_filter = ("gender", SoftDeleteFilter)
    search_fields = ("name", "phone", "email")
    date_hierarchy = "birthday"
    ordering = ("name",)


@admin.register(AdminInfo, site=admin_site)
@admin.register(AdminInfo)
class AdminInfoAdmin(PersonalInfoAdmin):
    pass


@admin.register(StaffInfo, site=admin_site)
@admin.register(StaffInfo)
class StaffInfoAdmin(PersonalInfoAdmin):
    pass


@admin.register(TeacherInfo, site=admin_site)
@admin.register(TeacherInfo)
class TeacherInfoAdmin(PersonalInfoAdmin):
    list_display = PersonalInfoAdmin.list_display + ("user",)


class ParentInline(admin.StackedInline):
    model = ParentInfo
    extra = 0
    verbose_name_plural = "Phụ huynh"


@admin.register(StudentInfo, site=admin_site)
@admin.register(StudentInfo)
class StudentInfoAdmin(PersonalInfoAdmin):
    list_display = PersonalInfoAdmin.list_display + ("current_classroom", "has_encoding")
    inlines = [ParentInline]
    readonly_fields = ("encoding_status",)

    def has_encoding(self, obj):
        return bool(obj.encoding)
    has_encoding.boolean = True
    has_encoding.short_description = "Đã lưu mặt?"

    def current_classroom(self, obj):
        cls = obj.get_current_classroom()
        return cls.classroom_name if cls else "-"

    current_classroom.short_description = "Lớp hiện tại"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/capture-face/",
                self.admin_site.admin_view(self.capture_face),
                name="students_studentinfo_capture_face",
            )
        ]
        return custom + urls

    def encoding_status(self, obj):
        url = reverse("admin:students_studentinfo_capture_face", args=[obj.pk])
        if obj.encoding:
            return mark_safe(f"<a class='button' href='{url}' style='margin-left:10px'>📷Đã lấy! Bạn muốn lấy lại </a>")
        return mark_safe(f"<a class='button' href='{url}' style='margin-left:10px'>📷Lấy gương mặt</a>")

    encoding_status.short_description = "Vector gương mặt"

    def capture_face(self, request, object_id, *args, **kwargs):
        student = get_object_or_404(StudentInfo, pk=object_id)
        rep = enroll()
        if rep is None:
            self.message_user(request, _("Không lấy được gương mặt."), messages.WARNING)
        else:
            student.encoding = pickle.dumps(rep)
            student.save()
            self.message_user(request, _("Đã lưu vector gương mặt."), messages.SUCCESS)
        return redirect(reverse("admin:students_studentinfo_change", args=[object_id]))


@admin.register(SchoolYear, site=admin_site)
@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ("school_year_name",)
    search_fields = ("school_year_name",)


@admin.register(Semester, site=admin_site)
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ("semester_type", "school_year")
    list_filter = ("semester_type", "school_year")
    search_fields = ("school_year__school_year_name",)


@admin.register(Grade, site=admin_site)
@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("grade_type", "school_year")
    list_filter = ("grade_type", "school_year")
    search_fields = ("school_year__school_year_name",)


@admin.register(Classroom, site=admin_site)
@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("classroom_name", "grade", "student_number")
    list_filter = ("grade__grade_type", "grade__school_year")
    search_fields = ("classroom_name",)
    ordering = ("classroom_name",)


@admin.register(ClassroomTransfer, site=admin_site)
@admin.register(ClassroomTransfer)
class ClassroomTransferAdmin(admin.ModelAdmin):
    list_display = ("student_info", "classroom", "transfer_date", "changed_classroom")
    list_filter = ("transfer_date", "changed_classroom")
    date_hierarchy = "transfer_date"
    search_fields = ("student_info__name", "classroom__classroom_name")


@admin.register(Subject, site=admin_site)
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("subject_name",)
    search_fields = ("subject_name",)


@admin.register(Curriculum, site=admin_site)
@admin.register(Curriculum)
class CurriculumAdmin(admin.ModelAdmin):
    list_display = ("grade", "subject")
    list_filter = ("grade", "subject")
    search_fields = ("grade__school_year__school_year_name", "subject__subject_name")


class ScoreInline(admin.TabularInline):
    model = Score
    extra = 0
    fields = ("student_info", "score_type", "score_number")
    autocomplete_fields = ("student_info",)


@admin.register(Transcript, site=admin_site)
@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ("classroom", "curriculum", "semester", "teacher_info", "is_done")
    list_filter = ("semester", "classroom", "curriculum__subject")
    search_fields = (
        "classroom__classroom_name",
        "curriculum__subject__subject_name",
        "teacher_info__name",
    )
    inlines = [ScoreInline]
    list_editable = ("is_done",)


@admin.register(Score, site=admin_site)
@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("student_info", "transcript", "score_type", "score_number")
    list_filter = ("score_type",)
    search_fields = ("student_info__name", "transcript__classroom__classroom_name")
    list_editable = ("score_number",)
    autocomplete_fields = ("student_info", "transcript")


@admin.register(Attendance, site=admin_site)
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "date", "time_checked", "is_late")
    list_filter = ("is_late", "date")
    date_hierarchy = "date"
    search_fields = ("student__name",)


@admin.register(Rule, site=admin_site)
@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("rule_name", "rule_content", "min_value", "max_value")
    search_fields = ("rule_name",)
    list_editable = ("min_value", "max_value")

@admin.register(ConductRecord, site=admin_site)
@admin.register(ConductRecord)
class ConductRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "semester", "conduct")
    list_filter = ("semester__school_year", "semester__semester_type", "conduct")
    search_fields = ("student__name",)
    list_editable = ("conduct",)

@admin.register(Group, site=admin_site)
class CustomGroupAdmin(GroupAdmin):
    pass



# Gán tên tiếng Việt cho mỗi model
User._meta.verbose_name = "Tài khoản người dùng"
User._meta.verbose_name_plural = "Tài khoản người dùng"
AdminInfo._meta.verbose_name = "Quản trị viên"
AdminInfo._meta.verbose_name_plural = "Quản trị viên"
StaffInfo._meta.verbose_name = "Nhân viên"
StaffInfo._meta.verbose_name_plural = "Nhân viên"
TeacherInfo._meta.verbose_name = "Giáo viên"
TeacherInfo._meta.verbose_name_plural = "Giáo viên"
StudentInfo._meta.verbose_name = "Học sinh"
StudentInfo._meta.verbose_name_plural = "Học sinh"
ParentInfo._meta.verbose_name = "Phụ huynh"
ParentInfo._meta.verbose_name_plural = "Phụ huynh"
SchoolYear._meta.verbose_name = "Năm học"
SchoolYear._meta.verbose_name_plural = "Năm học"
Semester._meta.verbose_name = "Học kỳ"
Semester._meta.verbose_name_plural = "Học kỳ"
Grade._meta.verbose_name = "Khối học"
Grade._meta.verbose_name_plural = "Khối học"
Classroom._meta.verbose_name = "Lớp học"
Classroom._meta.verbose_name_plural = "Lớp học"
ClassroomTransfer._meta.verbose_name = "Chuyển lớp"
ClassroomTransfer._meta.verbose_name_plural = "Chuyển lớp"
Subject._meta.verbose_name = "Môn học"
Subject._meta.verbose_name_plural = "Môn học"
Curriculum._meta.verbose_name = "Chương trình học"
Curriculum._meta.verbose_name_plural = "Chương trình học"
Transcript._meta.verbose_name = "Học bạ"
Transcript._meta.verbose_name_plural = "Học bạ"
Score._meta.verbose_name = "Điểm số"
Score._meta.verbose_name_plural = "Điểm số"
Attendance._meta.verbose_name = "Điểm danh"
Attendance._meta.verbose_name_plural = "Điểm danh"
Rule._meta.verbose_name = "Quy định"
Rule._meta.verbose_name_plural = "Quy định"
ConductRecord._meta.verbose_name_plural = "Hạnh kiểm"