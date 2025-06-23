from django.contrib import admin
from django.urls import path

class MyAdminSite(admin.AdminSite):
    site_header = 'STUDENT MANAGEMENT'

admin_site = MyAdminSite('Student Management')