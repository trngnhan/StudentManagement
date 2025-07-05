from django import forms
from django.forms import ModelForm
from .models import StudentInfo, ParentInfo

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
