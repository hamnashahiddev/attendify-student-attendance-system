from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    ROLES = [
        ("admin", "Administrator"),
        ("teacher", "Teacher"),
        ("student", "Student"),
    ]
    role = models.CharField(max_length=10, choices=ROLES, default="student")
    phone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to="profiles/", blank=True, null=True)

    @property
    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    @property
    def is_teacher(self):
        return self.role == "teacher"

    @property
    def is_student(self):
        return self.role == "student"

    def get_assigned_classes(self):
        if self.is_teacher:
            return ClassRoom.objects.filter(
                models.Q(class_teacher=self) | models.Q(subjects__teacher=self)
            ).distinct()
        return ClassRoom.objects.all()

    def get_assigned_subjects(self):
        if self.is_teacher:
            return Subject.objects.filter(teacher=self)
        return Subject.objects.all()


class SiteSetting(models.Model):
    threshold = models.PositiveIntegerField(default=75)
    site_name = models.CharField(max_length=100, default="Attendify")

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Site Settings (Threshold: {self.threshold}%)"


def level(p):
    t = SiteSetting.get().threshold
    if p >= t + 10:
        return "safe"
    elif p >= t:
        return "warning"
    else:
        return "critical"


class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ClassRoom(models.Model):
    name = models.CharField(max_length=60)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="classes")
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": "teacher"},
        related_name="headed_classes",
    )
    capacity = models.PositiveIntegerField(default=40)

    class Meta:
        ordering = ["department__code", "name"]

    def __str__(self):
        return self.name

    @property
    def student_count(self):
        return self.students.filter(status="active").count()


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=15, unique=True)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="subjects")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": "teacher"},
        related_name="taught_subjects",
    )

    class Meta:
        ordering = ["classroom__name", "code"]

    def __str__(self):
        return f"{self.code} · {self.name}"


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(max_length=20, unique=True)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.PROTECT, related_name="students")
    status = models.CharField(
        max_length=10,
        choices=[("active", "Active"), ("inactive", "Inactive")],
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["student_id"]

    def stats(self):
        qs = self.attendance_set.all()
        total = qs.count()
        present = qs.filter(status="P").count()
        late = qs.filter(status="L").count()
        leave = qs.filter(status="V").count()
        absent = qs.filter(status="A").count()
        attended = present + late
        return total, attended, present, absent, late, leave

    @property
    def percentage(self):
        total, attended, *_ = self.stats()
        return round(attended * 100.0 / total, 1) if total > 0 else 100.0

    @property
    def level(self):
        return level(self.percentage)

    def subject_attendance(self, subject):
        qs = self.attendance_set.filter(subject=subject)
        total = qs.count()
        attended = qs.filter(status__in=["P", "L"]).count()
        pct = round(attended * 100.0 / total, 1) if total > 0 else 100.0
        return {
            "total": total,
            "attended": attended,
            "present": qs.filter(status="P").count(),
            "absent": qs.filter(status="A").count(),
            "late": qs.filter(status="L").count(),
            "leave": qs.filter(status="V").count(),
            "pct": pct,
        }

    def __str__(self):
        return f"{self.student_id} {self.user.get_full_name()}"


class Attendance(models.Model):
    STATUS = [
        ("P", "Present"),
        ("A", "Absent"),
        ("L", "Late"),
        ("V", "Leave"),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=1, choices=STATUS, default="P")
    remarks = models.CharField(max_length=200, blank=True)
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="marked_attendances"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "subject", "date"], name="uniq_att")
        ]
        ordering = ["-date", "student__student_id"]

    def __str__(self):
        return f"{self.date} - {self.student.student_id} ({self.get_status_display()})"


class Timetable(models.Model):
    DAYS = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
    ]
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name="timetables")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="timetables")
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": "teacher"},
        related_name="timetables",
    )
    day_of_week = models.IntegerField(choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.classroom} - {self.subject} ({self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')})"


class Announcement(models.Model):
    TARGETS = [
        ("all", "All Users"),
        ("teacher", "Teachers Only"),
        ("student", "Students Only"),
    ]
    title = models.CharField(max_length=200)
    message = models.TextField()
    target_role = models.CharField(max_length=10, choices=TARGETS, default="all")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"
