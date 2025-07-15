from django.core.mail import send_mail

send_mail(
    subject='Test email',
    message='Hello from Django',
    from_email='trinhquocdat041004@gmail.com',
    recipient_list=['2251050016dat@ou.edu.vn'],
    fail_silently=False
)