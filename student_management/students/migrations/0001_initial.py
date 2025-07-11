# Generated by Django 5.2.2 on 2025-06-23 04:18

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade_type', models.IntegerField(choices=[(10, 'Khối 10'), (11, 'Khối 11'), (12, 'Khối 12')])),
            ],
        ),
        migrations.CreateModel(
            name='Rule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_name', models.CharField(max_length=50, unique=True)),
                ('min_value', models.IntegerField(blank=True, null=True)),
                ('max_value', models.IntegerField(blank=True, null=True)),
                ('rule_content', models.TextField(max_length=191)),
            ],
        ),
        migrations.CreateModel(
            name='SchoolYear',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('school_year_name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject_name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('avatar', models.URLField(default='https://res.cloudinary.com/dqw4mc8dg/image/upload/w_1000,c_fill,ar_1:1,g_auto,r_max/v1733391370/aj6sc6isvelwkotlo1vw.png')),
                ('role', models.IntegerField(choices=[(1, 'Admin'), (2, 'Staff'), (3, 'Teacher'), (4, 'Student')], default=3)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='AdminInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('gender', models.IntegerField(choices=[(0, 'Nữ'), (1, 'Nam')])),
                ('phone', models.CharField(max_length=10, unique=True)),
                ('address', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('birthday', models.DateField()),
                ('status', models.BooleanField(default=True)),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin_info', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('classroom_name', models.CharField(max_length=50)),
                ('student_number', models.PositiveIntegerField(default=0)),
                ('grade', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='classrooms', to='students.grade')),
            ],
            options={
                'unique_together': {('classroom_name', 'grade')},
            },
        ),
        migrations.AddField(
            model_name='grade',
            name='school_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='grades', to='students.schoolyear'),
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester_type', models.IntegerField(choices=[(1, 'Học kỳ I'), (2, 'Học kỳ II')])),
                ('school_year', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='semesters', to='students.schoolyear')),
            ],
            options={
                'unique_together': {('semester_type', 'school_year')},
            },
        ),
        migrations.CreateModel(
            name='StaffInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('gender', models.IntegerField(choices=[(0, 'Nữ'), (1, 'Nam')])),
                ('phone', models.CharField(max_length=10, unique=True)),
                ('address', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('birthday', models.DateField()),
                ('status', models.BooleanField(default=True)),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='staff_info', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StudentInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('gender', models.IntegerField(choices=[(0, 'Nữ'), (1, 'Nam')])),
                ('phone', models.CharField(max_length=10, unique=True)),
                ('address', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('birthday', models.DateField()),
                ('status', models.BooleanField(default=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='student_info', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ParentInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('phone', models.CharField(max_length=10)),
                ('email', models.EmailField(max_length=254)),
                ('student', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='parent', to='students.studentinfo')),
            ],
        ),
        migrations.CreateModel(
            name='Curriculum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('grade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curriculums', to='students.grade')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='curriculums', to='students.subject')),
            ],
            options={
                'unique_together': {('grade', 'subject')},
            },
        ),
        migrations.CreateModel(
            name='TeacherInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('gender', models.IntegerField(choices=[(0, 'Nữ'), (1, 'Nam')])),
                ('phone', models.CharField(max_length=10, unique=True)),
                ('address', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('birthday', models.DateField()),
                ('status', models.BooleanField(default=True)),
                ('user', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='teacher_info', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Transcript',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_done', models.BooleanField(default=False)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transcripts', to='students.classroom')),
                ('curriculum', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='students.curriculum')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='transcripts', to='students.semester')),
                ('teacher_info', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='transcripts', to='students.teacherinfo')),
            ],
            options={
                'unique_together': {('classroom', 'curriculum', 'semester')},
            },
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score_number', models.FloatField(null=True)),
                ('score_type', models.IntegerField(choices=[(1, '15 phút'), (2, '1 tiết'), (3, 'Thi')])),
                ('student_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scores', to='students.studentinfo')),
                ('transcript', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='scores', to='students.transcript')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='grade',
            unique_together={('grade_type', 'school_year')},
        ),
        migrations.CreateModel(
            name='ClassroomTransfer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changed_classroom', models.BooleanField(default=False)),
                ('transfer_date', models.DateField(default=django.utils.timezone.now)),
                ('classroom', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='classroom_transfers', to='students.classroom')),
                ('student_info', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classroom_transfers', to='students.studentinfo')),
            ],
            options={
                'unique_together': {('student_info', 'classroom', 'transfer_date')},
            },
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('time_checked', models.TimeField(blank=True, null=True)),
                ('is_late', models.BooleanField(default=False)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='students.studentinfo')),
            ],
            options={
                'unique_together': {('student', 'date')},
            },
        ),
    ]
