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
router.register(r'subjects', SubjectViewSet)
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
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
    path("subject_manage/", subject_manage_view, name="subject_manage"),
    path("subject_manage/edit/<int:subject_id>/", edit_subject_view, name="edit_subject"),
    path("subject_manage/delete/<int:subject_id>/", delete_subject_view, name="delete_subject"),
    path("subject_manage/search/", search_subjects_api, name="search_subjects_api"),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path("attendance/camera/", camera_attendance, name="camera_attendance"),
    path("attendance/mark/",  mark_attendance,  name="mark_attendance"),
    path("student_list/", student_list, name="student_list"),
    path("home/", student_list, name="home"),
    path("student/create/", student_create, name="student_create"),
    path("student/<int:pk>/edit/", student_update, name="student_update"),
    path("student/<int:pk>/delete/", student_delete, name="student_delete"),
    path("search_student", search_student_list, name="search_student")
]
