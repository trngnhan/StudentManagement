from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from datetime import time as dt_time

from students.models import StudentInfo, Attendance

def get_students_absent_today():
    today = timezone.localdate()

    absent_students = StudentInfo.objects.filter(
        parent__isnull=False
    ).exclude(
        attendances__date=today
    ).select_related('parent')

    return absent_students

@shared_task
def notify_absent_students():
    print("Celery is working.")

    now = timezone.localtime().time()
    if now < dt_time(7, 30):
        return

    print("2")
    today = timezone.localdate()
    absent_students = get_students_absent_today()
    print(absent_students)

    for student in absent_students:
        parent = student.parent
        if parent.email:
            send_mail(
                subject="Thông báo học sinh vắng mặt",
                message=f"Kính gửi phụ huynh,\n\n"
                        f"Hôm nay ({today:%d/%m/%Y}), học sinh {student.name} chưa được điểm danh.\n"
                        f"Vui lòng liên hệ giáo viên chủ nhiệm để biết thêm chi tiết.",
                from_email="trinhquocdat041004@gmail.com",
                recipient_list=[parent.email],
                fail_silently=True,
            )
            print("3")
