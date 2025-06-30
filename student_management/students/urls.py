from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
router = DefaultRouter()


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

urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns = [
    path('', include(router.urls)),
]
