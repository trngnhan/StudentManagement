from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from students.admin import admin_site
from .views import *

router = DefaultRouter()

urlpatterns = [
    path('', admin_dashboard, name='admin_dashboard'),
    path('admin/', admin_site.urls),
    path('rules_list/', rules_list_get_view, name='rules_list_get_view'),
    path('rules_list/update/', rules_list_post_view, name='rules_list_post_view'),
    # url profile
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # url QLHB
    path('subject_manage/', subject_manage_view, name='subject_manage_view'),
    path('subject_manage/add/', subject_add_view, name='subject_add_view'),
    path('subject_manage/search/', subject_search_view, name='subject_search_view'),
    path('subject_manage/edit/<int:subject_id>/', edit_subject_view, name='subject_edit_view'),
    path('subject_manage/delete/<int:subject_id>/', subject_delete_view, name='subject_delete_view'),

    path('schoolyear_manage/', schoolyear_manage_view, name='schoolyear_manage_view'),
    path('schoolyear/with-semesters/', schoolyear_with_semesters_view, name='schoolyear_with_semesters_view'),
    path('school-years/', schoolyears_api_view, name='schoolyears_api_view'),
    path('schoolyear/delete/<int:pk>/', schoolyear_delete_view, name='schoolyear_delete_view'),
    path('schoolyear/<int:year_id>/semesters/', semesters_of_schoolyear_view, name='semesters_of_schoolyear_view'),
    path('semester/create/', semester_create_view, name='semester_create_view'),
    path('semester/update/<int:semester_id>/', semester_update_view, name='semester_update_view'),
    path('semester/delete/<int:semester_id>/', semester_delete_view, name='semester_delete_view'),
    path('semester/edit/<int:semester_id>/', semester_edit_form_view, name='semester_edit_form_view'),

    path('class-score-report/', class_score_report_view, name='class_score_report'),
    path("teacher/classes/", teacher_class_list_view, name="teacher_class_list"),
    path("teacher/class/<int:classroom_id>/scores/", teacher_subject_scores_view, name="teacher_subject_scores_view"),
    path("teacher/scores/<int:transcript_id>/", teacher_score_detail_view, name="teacher_score_detail_view"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # url QLDD
    path("attendance/camera/", camera_attendance, name="camera_attendance"),
    path("attendance/mark/",  mark_attendance,  name="mark_attendance"),
    path("attendance/management", attendance_management, name="attendance_management"),
    path("attendance/students", save_attendance, name="save_attendance"),
    # url QLHS
    path("home/", student_list, name="home"),
    path("student_list/", student_list, name="student_list"),
    path("student/create/", student_create, name="student_create"),
    path("student/<int:pk>/edit/", student_update, name="student_update"),
    path("student/<int:pk>/delete/", student_delete, name="student_delete"),
    path("search_student", search_student_list, name="search_student"),
    path("student/dashboard/", student_dashboard_view, name="student_dashboard"),
    path("student/scores/", student_view_scores, name="student_view_scores"),
    # url QLLH
    path('curriculums/', curriculum_list_view, name='curriculum_list_view'),
    path('curriculums/add/', curriculum_add_form_view, name='curriculum_add_form_view'),
    path('curriculums/add/submit/', curriculum_add_view, name='curriculum_add_view'),

    path("classroom/", class_management, name="classroom_management"),
    path("classroom/create/", classroom_create, name="classroom_create"),
    path("classroom/<int:pk>/add-student/", add_student_to_classroom, name="add_student_to_classroom"),
    path("classroom/transfer/", transfer_student, name="transfer_student"),
    path("classroom/add-students-bulk/", classroom_add_students_bulk, name="classroom_add_students_bulk"),
    path("classroom/<int:pk>/update/", classroom_update, name="classroom_update"),
    path("classroom/<int:pk>/delete/", classroom_delete, name="classroom_delete"),
    path("classroom/classroom_transfer_students_bulk", classroom_transfer_students_bulk, name="classroom_transfer_students_bulk"),
    path("classroom/assign-teacher/", assign_teacher, name="assign_teacher"),

]
