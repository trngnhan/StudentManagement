from django import forms
from django.forms import ModelForm
from .models import StudentInfo, ParentInfo, Classroom

class StudentForm(ModelForm):
    class Meta:
        model  = StudentInfo
        exclude = ("user", "encoding")  
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
        }

class ParentForm(ModelForm):
    class Meta:
        model  = ParentInfo
        fields = ("name", "phone", "email")



class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["classroom_name", "grade"]


class AddStudentForm(forms.Form):
    student = forms.ModelChoiceField(queryset=StudentInfo.objects.filter(status=True))
    transfer_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


class TransferStudentForm(forms.Form):
    student = forms.ModelChoiceField(queryset=StudentInfo.objects.filter(status=True))
    new_classroom = forms.ModelChoiceField(queryset=Classroom.objects.all())
    transfer_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
