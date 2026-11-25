from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Student, ClassRoom, Department, Subject, Timetable, Announcement, SiteSetting

User = get_user_model()


class StudentForm(forms.ModelForm):
    first_name = forms.CharField(max_length=60, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=60, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={"class": "form-control"}))

    class Meta:
        model = Student
        fields = ["student_id", "classroom", "status"]
        widgets = {
            "student_id": forms.TextInput(attrs={"class": "form-control"}),
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            u = self.instance.user
            self.initial.update(
                first_name=u.first_name,
                last_name=u.last_name,
                email=u.email,
                phone=u.phone,
            )

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise ValidationError("This email is already in use by another account.")
        return email

    def clean_student_id(self):
        sid = self.cleaned_data.get("student_id", "").strip().upper()
        qs = Student.objects.filter(student_id__iexact=sid)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This Student ID is already assigned to another student.")
        return sid

    def save(self, commit=True):
        student = super().save(commit=False)
        d = self.cleaned_data
        if not student.user_id:
            username = d["student_id"].lower()
            u = User(username=username, role="student")
            u.set_password("student123")
        else:
            u = student.user

        u.first_name = d["first_name"]
        u.last_name = d["last_name"]
        u.email = d["email"]
        u.phone = d.get("phone", "")
        if "photo" in self.files:
            u.photo = self.files["photo"]

        if commit:
            u.save()
            student.user = u
            student.save()
        return student


class TeacherForm(forms.ModelForm):
    first_name = forms.CharField(max_length=60, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=60, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    photo = forms.ImageField(required=False, widget=forms.FileInput(attrs={"class": "form-control"}))
    password = forms.CharField(
        max_length=128,
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Leave blank to keep default/current password"}),
        help_text="Default is teacher123 if creating a new teacher."
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "phone", "photo"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This email is already in use by another user.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip().lower()
        qs = User.objects.filter(username__iexact=username)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This username is already taken.")
        return username

    def save(self, commit=True):
        teacher = super().save(commit=False)
        teacher.role = "teacher"
        pwd = self.cleaned_data.get("password")
        if not teacher.pk:
            teacher.set_password(pwd if pwd else "teacher123")
        elif pwd:
            teacher.set_password(pwd)
        if "photo" in self.files:
            teacher.photo = self.files["photo"]
        if commit:
            teacher.save()
        return teacher


class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = ["name", "department", "class_teacher", "capacity"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. CS-3A"}),
            "department": forms.Select(attrs={"class": "form-select"}),
            "class_teacher": forms.Select(attrs={"class": "form-select"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 200}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_teacher"].queryset = User.objects.filter(role="teacher")


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "code"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Computer Science"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. CS"}),
        }

    def clean_code(self):
        code = self.cleaned_data.get("code", "").strip().upper()
        qs = Department.objects.filter(code__iexact=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A department with this code already exists.")
        return code


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code", "classroom", "teacher"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Operating Systems"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. CS-301"}),
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "teacher": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["teacher"].queryset = User.objects.filter(role="teacher")

    def clean_code(self):
        code = self.cleaned_data.get("code", "").strip().upper()
        qs = Subject.objects.filter(code__iexact=code)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("A subject with this code already exists.")
        return code


class TimetableForm(forms.ModelForm):
    class Meta:
        model = Timetable
        fields = ["classroom", "subject", "teacher", "day_of_week", "start_time", "end_time", "room_number"]
        widgets = {
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "day_of_week": forms.Select(attrs={"class": "form-select"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "room_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Lab 2 / Room 104"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["teacher"].queryset = User.objects.filter(role="teacher")

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")
        classroom = cleaned_data.get("classroom")
        subject = cleaned_data.get("subject")

        if start and end and start >= end:
            self.add_error("end_time", "End time must be later than start time.")

        if classroom and subject and subject.classroom != classroom:
            self.add_error("subject", "Selected subject does not belong to the selected class.")

        return cleaned_data


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "message", "target_role", "expires_at"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Announcement Title"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Announcement content..."}),
            "target_role": forms.Select(attrs={"class": "form-select"}),
            "expires_at": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "photo"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("This email is already registered to another account.")
        return email


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = ["threshold", "site_name"]
        widgets = {
            "threshold": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 100}),
            "site_name": forms.TextInput(attrs={"class": "form-control"}),
        }
