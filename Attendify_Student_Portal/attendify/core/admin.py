from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    Department,
    ClassRoom,
    Subject,
    Student,
    Attendance,
    Timetable,
    Announcement,
    Notification,
    SiteSetting,
)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "role", "is_staff"]
    list_filter = ["role", "is_staff", "is_superuser", "is_active"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Attendify Profile", {"fields": ("role", "phone", "photo")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Attendify Profile", {"fields": ("role", "phone", "photo")}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["code", "name"]
    search_fields = ["code", "name"]


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ["name", "department", "class_teacher", "capacity"]
    list_filter = ["department"]
    search_fields = ["name"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "classroom", "teacher"]
    list_filter = ["classroom__department", "classroom"]
    search_fields = ["code", "name"]


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ["student_id", "user", "classroom", "status", "created_at"]
    list_filter = ["status", "classroom"]
    search_fields = ["student_id", "user__username", "user__first_name", "user__last_name", "user__email"]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["date", "student", "subject", "status", "marked_by", "updated_at"]
    list_filter = ["status", "date", "subject__classroom", "subject"]
    search_fields = ["student__student_id", "student__user__first_name", "student__user__last_name", "remarks"]
    date_hierarchy = "date"


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ["classroom", "subject", "teacher", "day_of_week", "start_time", "end_time", "room_number"]
    list_filter = ["day_of_week", "classroom"]


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["title", "target_role", "created_by", "created_at", "expires_at"]
    list_filter = ["target_role", "created_at"]
    search_fields = ["title", "message"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "is_read", "created_at"]
    list_filter = ["is_read", "created_at"]
    search_fields = ["title", "message", "user__username"]


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ["site_name", "threshold"]
