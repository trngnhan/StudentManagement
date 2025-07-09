from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from students.admin import admin_site
from .views import *

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'admins', AdminInfoViewSet)
router.register(r'staffs', StaffInfoViewSet)
router.register(r'teachers', TeacherInfoViewSet)
router.register(r'students', StudentInfoViewSet)
router.register(r'parents', ParentInfoViewSet)
router.register(r'school-years', SchoolYearViewSet)
router.register(r'semesters', SemesterViewSet)
router.register(r'grades', GradeViewSet)
router.register(r'classrooms', ClassroomViewSet)
router.register(r'classroom-transfers', ClassroomTransferViewSet)
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'curriculums', CurriculumViewSet)
router.register(r'transcripts', TranscriptViewSet)
router.register(r'scores', ScoreViewSet)
router.register(r'attendances', AttendanceViewSet)
router.register(r'rules', RuleViewSet)
router.register(r'admin-info', AdminInfoViewSet, basename='admin-info')

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin_site.urls),
    #path('api/', include(router.urls)),
    path('rules_list/', rules_list_view, name='rules_list'),
    # url profile
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # url QLHB
    path("subject_manage/", subject_manage_view, name="subject_manage"),
    path("subject_manage/edit/<int:subject_id>/", edit_subject_view, name="edit_subject"),
    path("schoolyear_manage/", schoolyear_semester_manage_view, name="schoolyear_manage"),
    path("schoolyear/<int:year_id>/semesters/", semesters_of_schoolyear_view, name="schoolyear_semesters"),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    # url QLDD
    path("attendance/camera/", camera_attendance, name="camera_attendance"),
    path("attendance/mark/",  mark_attendance,  name="mark_attendance"),
    path("attendance/management", attendance_management, name="attendance_management"),
    # url QLHS
    path("home/", student_list, name="home"),
    path("student_list/", student_list, name="student_list"),
    path("student/create/", student_create, name="student_create"),
    path("student/<int:pk>/edit/", student_update, name="student_update"),
    path("student/<int:pk>/delete/", student_delete, name="student_delete"),
    path("search_student", search_student_list, name="search_student"),
    # url QLLH
    path("classroom/class_management/", class_management, name="classroom_management"),
    path("classroom/create/", classroom_create, name="classroom_create"),
    path("classroom/<int:pk>/add-student/", add_student_to_classroom, name="add_student_to_classroom"),
    path("classroom/transfer/", transfer_student, name="transfer_student"),
    path("classroom/add-students-bulk/", classroom_add_students_bulk, name="classroom_add_students_bulk"),
    path("classroom/<int:pk>/update/", classroom_update, name="classroom_update"),
    path("classroom/<int:pk>/delete/", classroom_delete, name="classroom_delete"),
    path("classroom/classroom_transfer_students_bulk", classroom_transfer_students_bulk, name="classroom_transfer_students_bulk")
]
