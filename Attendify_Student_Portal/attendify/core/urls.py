from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Dashboard & Auth
    path("", views.home, name="home"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/password/", views.change_password_view, name="change_password"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/<int:pk>/read/", views.mark_notification_read, name="notification_read"),
    path("notifications/read-all/", views.mark_all_notifications_read, name="notifications_mark_all_read"),

    # Attendance
    path("attendance/mark/", views.mark, name="mark"),
    path("attendance/history/", views.history, name="history"),
    path("attendance/export/", views.export_attendance_csv, name="attendance_export"),

    # Reports
    path("reports/", views.reports_view, name="reports"),
    path("reports/export/", views.export_report_csv, name="reports_export"),

    # Students
    path("students/", views.student_list, name="students"),
    path("students/add/", views.student_form, name="student_add"),
    path("students/<int:pk>/", views.student_detail, name="student_detail"),
    path("students/<int:pk>/edit/", views.student_form, name="student_edit"),
    path("students/<int:pk>/delete/", views.student_delete, name="student_delete"),

    # Teachers
    path("teachers/", views.teacher_list, name="teachers"),
    path("teachers/add/", views.teacher_form, name="teacher_add"),
    path("teachers/<int:pk>/", views.teacher_detail, name="teacher_detail"),
    path("teachers/<int:pk>/edit/", views.teacher_form, name="teacher_edit"),
    path("teachers/<int:pk>/delete/", views.teacher_delete, name="teacher_delete"),

    # Academic: Classes
    path("classes/", views.classroom_list, name="classes"),
    path("classes/add/", views.classroom_form, name="class_add"),
    path("classes/<int:pk>/", views.classroom_detail, name="class_detail"),
    path("classes/<int:pk>/edit/", views.classroom_form, name="class_edit"),
    path("classes/<int:pk>/delete/", views.classroom_delete, name="class_delete"),

    # Academic: Departments
    path("departments/", views.department_list, name="departments"),
    path("departments/add/", views.department_form, name="department_add"),
    path("departments/<int:pk>/edit/", views.department_form, name="department_edit"),
    path("departments/<int:pk>/delete/", views.department_delete, name="department_delete"),

    # Academic: Subjects
    path("subjects/", views.subject_list, name="subjects"),
    path("subjects/add/", views.subject_form, name="subject_add"),
    path("subjects/<int:pk>/edit/", views.subject_form, name="subject_edit"),
    path("subjects/<int:pk>/delete/", views.subject_delete, name="subject_delete"),

    # Timetable
    path("timetable/", views.timetable_view, name="timetable"),
    path("timetable/add/", views.timetable_form, name="timetable_add"),
    path("timetable/<int:pk>/edit/", views.timetable_form, name="timetable_edit"),
    path("timetable/<int:pk>/delete/", views.timetable_delete, name="timetable_delete"),

    # Announcements
    path("announcements/", views.announcement_list, name="announcements"),
    path("announcements/add/", views.announcement_form, name="announcement_add"),
    path("announcements/<int:pk>/edit/", views.announcement_form, name="announcement_edit"),
    path("announcements/<int:pk>/delete/", views.announcement_delete, name="announcement_delete"),

    # Settings
    path("settings/", views.settings_page, name="settings"),
]
