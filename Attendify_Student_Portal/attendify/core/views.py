import csv
import datetime
import json
from functools import wraps

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .forms import (
    AnnouncementForm,
    ClassRoomForm,
    DepartmentForm,
    SiteSettingForm,
    StudentForm,
    SubjectForm,
    TeacherForm,
    TimetableForm,
    UserProfileForm,
)
from .models import (
    Announcement,
    Attendance,
    ClassRoom,
    Department,
    Notification,
    SiteSetting,
    Student,
    Subject,
    Timetable,
    User,
    level,
)


def role_required(*roles):
    """Enforces that the user has at least one of the specified roles."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles and not request.user.is_superuser:
                raise PermissionDenied("You do not have permission to access this page.")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ----------------------------------------------------------------------
# 1. DASHBOARDS & CORE VIEWS
# ----------------------------------------------------------------------

@login_required
def home(request):
    u = request.user
    today = timezone.localdate()
    setting = SiteSetting.get()
    threshold = setting.threshold

    # --- Student Dashboard ---
    if u.role == "student":
        student = get_object_or_404(Student, user=u)
        total, attended, present, absent, late, leave_cnt = student.stats()

        recent_records = student.attendance_set.select_related("subject", "subject__teacher").order_by("-date")[:10]

        # Subject-wise attendance calculation
        subjects_data = []
        for sub in student.classroom.subjects.select_related("teacher"):
            sub_stats = student.subject_attendance(sub)
            subjects_data.append({
                "subject": sub,
                "stats": sub_stats,
            })

        # Today's timetable
        weekday = today.weekday()  # 0=Monday
        today_timetable = Timetable.objects.filter(
            classroom=student.classroom, day_of_week=weekday
        ).select_related("subject", "teacher").order_by("start_time")

        # Active announcements
        announcements = Announcement.objects.filter(
            Q(target_role__in=["all", "student"]),
            Q(expires_at__isnull=True) | Q(expires_at__gte=today)
        ).order_by("-created_at")[:5]

        ctx = {
            "student": student,
            "threshold": threshold,
            "total": total,
            "attended": attended,
            "present": present,
            "absent": absent,
            "late": late,
            "leave": leave_cnt,
            "recent_records": recent_records,
            "subjects_data": subjects_data,
            "today_timetable": today_timetable,
            "announcements": announcements,
        }
        return render(request, "dashboard_student.html", ctx)

    # --- Teacher Dashboard ---
    elif u.role == "teacher":
        assigned_classes = u.get_assigned_classes()
        assigned_subjects = u.get_assigned_subjects()
        students_taught = Student.objects.filter(classroom__in=assigned_classes, status="active").distinct()

        # Teacher's today timetable
        weekday = today.weekday()
        today_timetable = Timetable.objects.filter(
            teacher=u, day_of_week=weekday
        ).select_related("classroom", "subject").order_by("start_time")

        # Attendance marked by this teacher or for their subjects
        base_att = Attendance.objects.filter(subject__in=assigned_subjects)
        today_att = base_att.filter(date=today)

        today_counts = {
            "Present": today_att.filter(status="P").count(),
            "Absent": today_att.filter(status="A").count(),
            "Late": today_att.filter(status="L").count(),
            "Leave": today_att.filter(status="V").count(),
        }

        # 7-day trend for teacher's subjects
        days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
        def calc_pct(d):
            q = base_att.filter(date=d)
            n = q.count()
            return round(q.filter(status__in=["P", "L"]).count() * 100.0 / n, 1) if n else 0

        trend_data = {
            "labels": [d.strftime("%d %b") for d in days],
            "data": [calc_pct(d) for d in days],
        }

        dist_data = [base_att.filter(status=k).count() for k, _ in Attendance.STATUS]

        # Low attendance students among teacher's classes
        low_students = []
        for s in students_taught.select_related("user", "classroom"):
            if s.percentage < threshold:
                low_students.append(s)
        low_students = sorted(low_students, key=lambda s: s.percentage)[:8]

        # Recent attendance marked
        recent_activity = base_att.select_related("student__user", "subject", "student__classroom").order_by("-updated_at")[:10]

        announcements = Announcement.objects.filter(
            Q(target_role__in=["all", "teacher"]),
            Q(expires_at__isnull=True) | Q(expires_at__gte=today)
        ).order_by("-created_at")[:5]

        ctx = {
            "threshold": threshold,
            "assigned_classes": assigned_classes,
            "assigned_subjects": assigned_subjects,
            "total_students": students_taught.count(),
            "today_counts": today_counts,
            "today_timetable": today_timetable,
            "trend_json": json.dumps(trend_data),
            "dist_json": json.dumps(dist_data),
            "low_students": low_students,
            "recent_activity": recent_activity,
            "announcements": announcements,
        }
        return render(request, "dashboard_staff.html", ctx)

    # --- Administrator Dashboard ---
    else:
        students = Student.objects.select_related("user", "classroom")
        teachers_count = User.objects.filter(role="teacher").count()
        classes_count = ClassRoom.objects.count()
        subjects_count = Subject.objects.count()

        base_att = Attendance.objects.all()
        today_att = base_att.filter(date=today)

        today_counts = {
            "Present": today_att.filter(status="P").count(),
            "Absent": today_att.filter(status="A").count(),
            "Late": today_att.filter(status="L").count(),
            "Leave": today_att.filter(status="V").count(),
        }

        days = [today - datetime.timedelta(days=i) for i in range(6, -1, -1)]
        def calc_pct(d):
            q = base_att.filter(date=d)
            n = q.count()
            return round(q.filter(status__in=["P", "L"]).count() * 100.0 / n, 1) if n else 0

        trend_data = {
            "labels": [d.strftime("%d %b") for d in days],
            "data": [calc_pct(d) for d in days],
        }

        dist_data = [base_att.filter(status=k).count() for k, _ in Attendance.STATUS]

        low_students = []
        for s in students:
            if s.percentage < threshold:
                low_students.append(s)
        low_students = sorted(low_students, key=lambda s: s.percentage)[:8]

        recent_activity = base_att.select_related("student__user", "subject", "marked_by").order_by("-updated_at")[:10]

        announcements = Announcement.objects.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gte=today)
        ).order_by("-created_at")[:5]

        ctx = {
            "threshold": threshold,
            "n_students": students.count(),
            "n_teachers": teachers_count,
            "n_classes": classes_count,
            "n_subjects": subjects_count,
            "today_counts": today_counts,
            "trend_json": json.dumps(trend_data),
            "dist_json": json.dumps(dist_data),
            "low_students": low_students,
            "recent_activity": recent_activity,
            "announcements": announcements,
        }
        return render(request, "dashboard_staff.html", ctx)


# ----------------------------------------------------------------------
# 2. PROFILE & USER AUTHENTICATION
# ----------------------------------------------------------------------

@login_required
def profile_view(request):
    u = request.user
    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=u)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=u)

    student_profile = getattr(u, "student_profile", None)
    return render(request, "profile.html", {"form": form, "student_profile": student_profile})


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed successfully.")
            return redirect("profile")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "change_password.html", {"form": form})


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "notifications.html", {"notifications": notifications})


@login_required
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect("notifications")


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("notifications")


# ----------------------------------------------------------------------
# 3. ATTENDANCE SYSTEM (MARKING & HISTORY)
# ----------------------------------------------------------------------

@role_required("admin", "teacher")
def mark(request):
    u = request.user
    today = timezone.localdate()

    # Determine authorized classrooms and subjects
    if u.role == "admin" or u.is_superuser:
        classes = ClassRoom.objects.select_related("department").all()
        subjects_qs = Subject.objects.select_related("classroom", "teacher").all()
    else:
        classes = u.get_assigned_classes()
        subjects_qs = Subject.objects.filter(teacher=u).select_related("classroom", "teacher")

    params = request.POST if request.method == "POST" else request.GET

    selected_class_id = params.get("classroom", "")
    selected_subject_id = params.get("subject", "")
    date_str = params.get("date", "")
    date = parse_date(date_str) if date_str else today

    # Filter subjects if class is selected
    available_subjects = subjects_qs
    if selected_class_id:
        available_subjects = available_subjects.filter(classroom_id=selected_class_id)

    selected_subject = None
    if selected_subject_id:
        selected_subject = subjects_qs.filter(pk=selected_subject_id).first()
        if selected_subject and not selected_class_id:
            selected_class_id = str(selected_subject.classroom_id)

    students = []
    if selected_subject:
        students = Student.objects.filter(
            classroom=selected_subject.classroom, status="active"
        ).select_related("user").order_by("student_id")

    # POST: Save attendance
    if request.method == "POST" and selected_subject:
        with transaction.atomic():
            saved_count = 0
            for s in students:
                st = params.get(f"s{s.pk}", "P")
                remarks = params.get(f"r{s.pk}", "").strip()[:200]
                Attendance.objects.update_or_create(
                    student=s,
                    subject=selected_subject,
                    date=date,
                    defaults={
                        "status": st,
                        "remarks": remarks,
                        "marked_by": u,
                    },
                )
                saved_count += 1

            messages.success(
                request,
                f"Successfully saved attendance for {saved_count} students in {selected_subject.name} on {date}.",
            )
            return redirect(f"/attendance/mark/?classroom={selected_subject.classroom_id}&subject={selected_subject.pk}&date={date}")

    # Fetch existing attendance records if any
    existing_map = {}
    if selected_subject and date:
        existing_att = Attendance.objects.filter(subject=selected_subject, date=date)
        existing_map = {a.student_id: a for a in existing_att}

    rows = [(s, existing_map.get(s.pk)) for s in students]

    ctx = {
        "classes": classes,
        "selected_class_id": str(selected_class_id) if selected_class_id else "",
        "subjects": available_subjects,
        "subject": selected_subject,
        "date": date,
        "rows": rows,
        "existing": bool(existing_map),
        "statuses": Attendance.STATUS,
    }
    return render(request, "mark.html", ctx)


@role_required("admin", "teacher")
def history(request):
    u = request.user
    qs = Attendance.objects.select_related("student__user", "student__classroom", "subject", "marked_by")

    if u.role == "teacher":
        qs = qs.filter(subject__teacher=u)

    # Filters
    class_id = request.GET.get("class", "").strip()
    subject_id = request.GET.get("subject", "").strip()
    status = request.GET.get("status", "").strip()
    from_date_str = request.GET.get("from", "").strip()
    to_date_str = request.GET.get("to", "").strip()
    q = request.GET.get("q", "").strip()

    if class_id:
        qs = qs.filter(student__classroom_id=class_id)
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    if status:
        qs = qs.filter(status=status)
    if from_date_str:
        d = parse_date(from_date_str)
        if d:
            qs = qs.filter(date__gte=d)
    if to_date_str:
        d = parse_date(to_date_str)
        if d:
            qs = qs.filter(date__lte=d)
    if q:
        qs = qs.filter(
            Q(student__student_id__icontains=q)
            | Q(student__user__first_name__icontains=q)
            | Q(student__user__last_name__icontains=q)
        )

    qs = qs.order_by("-date", "student__student_id")

    # Pagination
    paginator = Paginator(qs, 20)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    # Preserve GET parameters for pagination links
    params = request.GET.copy()
    if "page" in params:
        del params["page"]
    querystring = params.urlencode()

    classes = ClassRoom.objects.all() if u.role == "admin" else u.get_assigned_classes()
    subjects = Subject.objects.all() if u.role == "admin" else u.get_assigned_subjects()

    ctx = {
        "page": page,
        "classes": classes,
        "subjects": subjects,
        "statuses": Attendance.STATUS,
        "selected_class": class_id,
        "selected_subject": subject_id,
        "selected_status": status,
        "from_date": from_date_str,
        "to_date": to_date_str,
        "q": q,
        "querystring": querystring,
    }
    return render(request, "history.html", ctx)


@role_required("admin", "teacher")
def export_attendance_csv(request):
    u = request.user
    qs = Attendance.objects.select_related("student__user", "student__classroom", "subject")

    if u.role == "teacher":
        qs = qs.filter(subject__teacher=u)

    # Apply same filters
    class_id = request.GET.get("class", "").strip()
    subject_id = request.GET.get("subject", "").strip()
    status = request.GET.get("status", "").strip()
    from_date_str = request.GET.get("from", "").strip()
    to_date_str = request.GET.get("to", "").strip()
    q = request.GET.get("q", "").strip()

    if class_id:
        qs = qs.filter(student__classroom_id=class_id)
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    if status:
        qs = qs.filter(status=status)
    if from_date_str:
        d = parse_date(from_date_str)
        if d:
            qs = qs.filter(date__gte=d)
    if to_date_str:
        d = parse_date(to_date_str)
        if d:
            qs = qs.filter(date__lte=d)
    if q:
        qs = qs.filter(
            Q(student__student_id__icontains=q)
            | Q(student__user__first_name__icontains=q)
            | Q(student__user__last_name__icontains=q)
        )

    qs = qs.order_by("-date", "student__student_id")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="attendance_export.csv"'

    writer = csv.writer(response)
    writer.writerow(["Date", "Student ID", "Student Name", "Class", "Subject", "Status", "Remarks"])

    for a in qs:
        writer.writerow([
            a.date.strftime("%Y-%m-%d"),
            a.student.student_id,
            a.student.user.get_full_name(),
            a.student.classroom.name,
            a.subject.name,
            a.get_status_display(),
            a.remarks,
        ])

    return response


# ----------------------------------------------------------------------
# 4. REPORTS MODULE
# ----------------------------------------------------------------------

@role_required("admin", "teacher")
def reports_view(request):
    u = request.user
    today = timezone.localdate()
    setting = SiteSetting.get()
    threshold = setting.threshold

    tab = request.GET.get("tab", "daily")
    date_str = request.GET.get("date", "")
    target_date = parse_date(date_str) if date_str else today

    classes = ClassRoom.objects.all() if u.role == "admin" else u.get_assigned_classes()
    subjects = Subject.objects.all() if u.role == "admin" else u.get_assigned_subjects()

    daily_reports = []
    class_reports = []
    student_reports = []
    low_reports = []

    # 1. Daily Attendance Report
    if tab == "daily":
        for c in classes:
            c_att = Attendance.objects.filter(student__classroom=c, date=target_date)
            total = c_att.count()
            present = c_att.filter(status="P").count()
            absent = c_att.filter(status="A").count()
            late = c_att.filter(status="L").count()
            leave_cnt = c_att.filter(status="V").count()
            pct = round((present + late) * 100.0 / total, 1) if total > 0 else 0
            daily_reports.append({
                "classroom": c,
                "total": total,
                "present": present,
                "absent": absent,
                "late": late,
                "leave": leave_cnt,
                "pct": pct,
            })

    # 2. Class Summary Report
    elif tab == "class":
        for c in classes:
            c_att = Attendance.objects.filter(student__classroom=c)
            total = c_att.count()
            present = c_att.filter(status="P").count()
            absent = c_att.filter(status="A").count()
            late = c_att.filter(status="L").count()
            leave_cnt = c_att.filter(status="V").count()
            pct = round((present + late) * 100.0 / total, 1) if total > 0 else 100.0
            class_reports.append({
                "classroom": c,
                "student_count": c.students.filter(status="active").count(),
                "total_records": total,
                "present": present,
                "absent": absent,
                "late": late,
                "leave": leave_cnt,
                "pct": pct,
                "level": level(pct),
            })

    # 3. Student & Low Attendance Reports
    elif tab in ("students", "low"):
        selected_class = request.GET.get("class", "")
        students_qs = Student.objects.filter(status="active").select_related("user", "classroom")
        if u.role == "teacher":
            students_qs = students_qs.filter(classroom__in=classes)
        if selected_class:
            students_qs = students_qs.filter(classroom_id=selected_class)

        for s in students_qs:
            t, att, p, a, l, v = s.stats()
            pct = s.percentage
            data = {
                "student": s,
                "total": t,
                "attended": att,
                "present": p,
                "absent": a,
                "late": l,
                "leave": v,
                "pct": pct,
                "level": s.level,
            }
            if tab == "low" and pct < threshold:
                low_reports.append(data)
            elif tab == "students":
                student_reports.append(data)

        if tab == "low":
            low_reports = sorted(low_reports, key=lambda x: x["pct"])

    ctx = {
        "tab": tab,
        "target_date": target_date,
        "classes": classes,
        "selected_class": request.GET.get("class", ""),
        "daily_reports": daily_reports,
        "class_reports": class_reports,
        "student_reports": student_reports,
        "low_reports": low_reports,
        "threshold": threshold,
    }
    return render(request, "reports.html", ctx)


@role_required("admin", "teacher")
def export_report_csv(request):
    tab = request.GET.get("tab", "daily")
    today = timezone.localdate()
    setting = SiteSetting.get()
    threshold = setting.threshold
    u = request.user

    classes = ClassRoom.objects.all() if u.role == "admin" else u.get_assigned_classes()

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="attendify_report_{tab}.csv"'
    writer = csv.writer(response)

    if tab == "daily":
        date_str = request.GET.get("date", "")
        target_date = parse_date(date_str) if date_str else today
        writer.writerow(["Class", "Date", "Total Sessions", "Present", "Absent", "Late", "Leave", "Attendance %"])
        for c in classes:
            c_att = Attendance.objects.filter(student__classroom=c, date=target_date)
            total = c_att.count()
            present = c_att.filter(status="P").count()
            absent = c_att.filter(status="A").count()
            late = c_att.filter(status="L").count()
            leave_cnt = c_att.filter(status="V").count()
            pct = round((present + late) * 100.0 / total, 1) if total > 0 else 0
            writer.writerow([c.name, target_date.strftime("%Y-%m-%d"), total, present, absent, late, leave_cnt, f"{pct}%"])

    elif tab == "class":
        writer.writerow(["Class", "Department", "Active Students", "Total Records", "Present", "Absent", "Late", "Leave", "Attendance %"])
        for c in classes:
            c_att = Attendance.objects.filter(student__classroom=c)
            total = c_att.count()
            present = c_att.filter(status="P").count()
            absent = c_att.filter(status="A").count()
            late = c_att.filter(status="L").count()
            leave_cnt = c_att.filter(status="V").count()
            pct = round((present + late) * 100.0 / total, 1) if total > 0 else 100.0
            writer.writerow([c.name, c.department.name, c.students.filter(status="active").count(), total, present, absent, late, leave_cnt, f"{pct}%"])

    else:
        writer.writerow(["Student ID", "Name", "Class", "Total Sessions", "Attended", "Present", "Absent", "Late", "Leave", "Attendance %", "Status Level"])
        students_qs = Student.objects.filter(status="active").select_related("user", "classroom")
        if u.role == "teacher":
            students_qs = students_qs.filter(classroom__in=classes)
        for s in students_qs:
            t, att, p, a, l, v = s.stats()
            pct = s.percentage
            if tab == "low" and pct >= threshold:
                continue
            writer.writerow([s.student_id, s.user.get_full_name(), s.classroom.name, t, att, p, a, l, v, f"{pct}%", s.level.upper()])

    return response


# ----------------------------------------------------------------------
# 5. STUDENT MANAGEMENT
# ----------------------------------------------------------------------

@role_required("admin", "teacher")
def student_list(request):
    u = request.user
    qs = Student.objects.select_related("user", "classroom", "classroom__department").order_by("student_id")

    if u.role == "teacher":
        qs = qs.filter(classroom__in=u.get_assigned_classes())

    q = request.GET.get("q", "").strip()
    c = request.GET.get("class", "").strip()
    status = request.GET.get("status", "").strip()

    if q:
        qs = qs.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(student_id__icontains=q)
            | Q(user__email__icontains=q)
        )
    if c:
        qs = qs.filter(classroom_id=c)
    if status:
        qs = qs.filter(status=status)

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    params = request.GET.copy()
    if "page" in params:
        del params["page"]
    querystring = params.urlencode()

    classes = ClassRoom.objects.all() if u.role == "admin" else u.get_assigned_classes()

    return render(
        request,
        "students.html",
        {
            "page": page,
            "q": q,
            "selected_class": c,
            "selected_status": status,
            "classes": classes,
            "querystring": querystring,
        },
    )


@login_required
def student_detail(request, pk):
    u = request.user
    student = get_object_or_404(Student.objects.select_related("user", "classroom", "classroom__department"), pk=pk)

    # Permission check: Student can only view their own profile
    if u.role == "student" and student.user != u:
        raise PermissionDenied("You are not authorized to view another student's profile.")

    # Permission check: Teacher can only view students in their assigned classes
    if u.role == "teacher":
        if student.classroom not in u.get_assigned_classes():
            raise PermissionDenied("You are not authorized to view students outside your assigned classes.")

    total, attended, present, absent, late, leave_cnt = student.stats()
    recent_records = student.attendance_set.select_related("subject", "marked_by").order_by("-date")[:20]

    # Subject-wise attendance
    subjects_data = []
    for sub in student.classroom.subjects.select_related("teacher"):
        stats = student.subject_attendance(sub)
        subjects_data.append({"subject": sub, "stats": stats})

    ctx = {
        "s": student,
        "total": total,
        "attended": attended,
        "present": present,
        "absent": absent,
        "late": late,
        "leave": leave_cnt,
        "recent": recent_records,
        "subjects_data": subjects_data,
    }
    return render(request, "student_detail.html", ctx)


@role_required("admin")
def student_form(request, pk=None):
    inst = get_object_or_404(Student, pk=pk) if pk else None
    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES, instance=inst)
        if form.is_valid():
            student = form.save()
            action = "updated" if pk else "created"
            messages.success(request, f"Student {student.student_id} ({student.user.get_full_name()}) successfully {action}.")
            return redirect("students")
    else:
        form = StudentForm(instance=inst)
    return render(request, "student_form.html", {"form": form, "editing": bool(pk), "student": inst})


@role_required("admin")
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        sid = student.student_id
        # Safe deactivation or deletion:
        # Check if attendance exists
        if student.attendance_set.exists():
            student.status = "inactive"
            student.save()
            messages.warning(
                request,
                f"Student {sid} has existing attendance records, so their status was set to Inactive instead of deleting history.",
            )
        else:
            user = student.user
            student.delete()
            user.delete()
            messages.success(request, f"Student {sid} has been permanently deleted.")
    return redirect("students")


# ----------------------------------------------------------------------
# 6. TEACHER MANAGEMENT
# ----------------------------------------------------------------------

@role_required("admin")
def teacher_list(request):
    teachers = User.objects.filter(role="teacher").prefetch_related("headed_classes", "taught_subjects").order_by("first_name", "last_name")
    q = request.GET.get("q", "").strip()
    if q:
        teachers = teachers.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(username__icontains=q)
            | Q(email__icontains=q)
        )

    paginator = Paginator(teachers, 12)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    return render(request, "teachers.html", {"page": page, "q": q})


@role_required("admin", "teacher")
def teacher_detail(request, pk):
    teacher = get_object_or_404(User, pk=pk, role="teacher")
    if request.user.role == "teacher" and request.user.pk != teacher.pk:
        raise PermissionDenied("You can only view your own teacher profile.")

    assigned_classes = teacher.get_assigned_classes()
    taught_subjects = teacher.get_assigned_subjects()
    timetables = Timetable.objects.filter(teacher=teacher).select_related("classroom", "subject").order_by("day_of_week", "start_time")

    ctx = {
        "teacher": teacher,
        "classes": assigned_classes,
        "subjects": taught_subjects,
        "timetables": timetables,
    }
    return render(request, "teacher_detail.html", ctx)


@role_required("admin")
def teacher_form(request, pk=None):
    inst = get_object_or_404(User, pk=pk, role="teacher") if pk else None
    if request.method == "POST":
        form = TeacherForm(request.POST, request.FILES, instance=inst)
        if form.is_valid():
            teacher = form.save()
            action = "updated" if pk else "created"
            messages.success(request, f"Teacher {teacher.get_full_name()} successfully {action}.")
            return redirect("teachers")
    else:
        form = TeacherForm(instance=inst)
    return render(request, "teacher_form.html", {"form": form, "editing": bool(pk), "teacher": inst})


@role_required("admin")
def teacher_delete(request, pk):
    teacher = get_object_or_404(User, pk=pk, role="teacher")
    if request.method == "POST":
        name = teacher.get_full_name()
        teacher.delete()
        messages.success(request, f"Teacher {name} has been deleted.")
    return redirect("teachers")


# ----------------------------------------------------------------------
# 7. ACADEMIC MANAGEMENT (CLASSES, DEPARTMENTS, SUBJECTS)
# ----------------------------------------------------------------------

@role_required("admin", "teacher")
def classroom_list(request):
    classes = ClassRoom.objects.select_related("department", "class_teacher").prefetch_related("students", "subjects").all()
    q = request.GET.get("q", "").strip()
    if q:
        classes = classes.filter(Q(name__icontains=q) | Q(department__name__icontains=q) | Q(department__code__icontains=q))

    classes_data = []
    for c in classes:
        active_count = c.students.filter(status="active").count()
        att_qs = Attendance.objects.filter(student__classroom=c)
        tot = att_qs.count()
        pct = round(att_qs.filter(status__in=["P", "L"]).count() * 100.0 / tot, 1) if tot > 0 else 100.0
        classes_data.append({
            "classroom": c,
            "student_count": active_count,
            "avg_attendance": pct,
            "level": level(pct),
        })

    return render(request, "classes.html", {"classes_data": classes_data, "q": q})


@role_required("admin", "teacher")
def classroom_detail(request, pk):
    c = get_object_or_404(ClassRoom.objects.select_related("department", "class_teacher"), pk=pk)
    students = c.students.select_related("user").order_by("student_id")
    subjects = c.subjects.select_related("teacher").all()
    timetables = c.timetables.select_related("subject", "teacher").order_by("day_of_week", "start_time")

    ctx = {
        "c": c,
        "students": students,
        "subjects": subjects,
        "timetables": timetables,
    }
    return render(request, "class_detail.html", ctx)


@role_required("admin")
def classroom_form(request, pk=None):
    inst = get_object_or_404(ClassRoom, pk=pk) if pk else None
    if request.method == "POST":
        form = ClassRoomForm(request.POST, instance=inst)
        if form.is_valid():
            c = form.save()
            action = "updated" if pk else "created"
            messages.success(request, f"Class {c.name} successfully {action}.")
            return redirect("classes")
    else:
        form = ClassRoomForm(instance=inst)
    return render(request, "class_form.html", {"form": form, "editing": bool(pk), "classroom": inst})


@role_required("admin")
def classroom_delete(request, pk):
    c = get_object_or_404(ClassRoom, pk=pk)
    if request.method == "POST":
        name = c.name
        if c.students.exists():
            messages.error(request, f"Cannot delete class {name} because it has enrolled students. Reassign students first.")
        else:
            c.delete()
            messages.success(request, f"Class {name} has been deleted.")
    return redirect("classes")


# Departments
@role_required("admin")
def department_list(request):
    departments = Department.objects.prefetch_related("classes").all()
    return render(request, "departments.html", {"departments": departments})


@role_required("admin")
def department_form(request, pk=None):
    inst = get_object_or_404(Department, pk=pk) if pk else None
    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=inst)
        if form.is_valid():
            d = form.save()
            action = "updated" if pk else "created"
            messages.success(request, f"Department {d.name} successfully {action}.")
            return redirect("departments")
    else:
        form = DepartmentForm(instance=inst)
    return render(request, "department_form.html", {"form": form, "editing": bool(pk), "department": inst})


@role_required("admin")
def department_delete(request, pk):
    d = get_object_or_404(Department, pk=pk)
    if request.method == "POST":
        name = d.name
        if d.classes.exists():
            messages.error(request, f"Cannot delete department {name} because classes belong to it.")
        else:
            d.delete()
            messages.success(request, f"Department {name} deleted.")
    return redirect("departments")


# Subjects
@role_required("admin", "teacher")
def subject_list(request):
    subjects = Subject.objects.select_related("classroom", "teacher", "classroom__department").all()
    q = request.GET.get("q", "").strip()
    c = request.GET.get("class", "").strip()

    if q:
        subjects = subjects.filter(Q(name__icontains=q) | Q(code__icontains=q))
    if c:
        subjects = subjects.filter(classroom_id=c)

    classes = ClassRoom.objects.all()
    return render(request, "subjects.html", {"subjects": subjects, "classes": classes, "q": q, "selected_class": c})


@role_required("admin")
def subject_form(request, pk=None):
    inst = get_object_or_404(Subject, pk=pk) if pk else None
    if request.method == "POST":
        form = SubjectForm(request.POST, instance=inst)
        if form.is_valid():
            s = form.save()
            action = "updated" if pk else "created"
            messages.success(request, f"Subject {s.name} successfully {action}.")
            return redirect("subjects")
    else:
        form = SubjectForm(instance=inst)
    return render(request, "subject_form.html", {"form": form, "editing": bool(pk), "subject": inst})


@role_required("admin")
def subject_delete(request, pk):
    s = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        name = s.name
        s.delete()
        messages.success(request, f"Subject {name} deleted.")
    return redirect("subjects")


# ----------------------------------------------------------------------
# 8. TIMETABLE
# ----------------------------------------------------------------------

@login_required
def timetable_view(request):
    u = request.user
    selected_class_id = request.GET.get("class", "")
    selected_teacher_id = request.GET.get("teacher", "")

    timetables = Timetable.objects.select_related("classroom", "subject", "teacher").all()

    if u.role == "student":
        student = getattr(u, "student_profile", None)
        if student:
            timetables = timetables.filter(classroom=student.classroom)
            selected_class_id = str(student.classroom.pk)
    else:
        if selected_class_id:
            timetables = timetables.filter(classroom_id=selected_class_id)
        if selected_teacher_id:
            timetables = timetables.filter(teacher_id=selected_teacher_id)
        elif u.role == "teacher" and not selected_class_id and not selected_teacher_id:
            timetables = timetables.filter(teacher=u)
            selected_teacher_id = str(u.pk)

    # Group timetables by day of week (0 to 5)
    days_map = {i: [] for i in range(6)}
    for entry in timetables:
        days_map[entry.day_of_week].append(entry)

    days_display = [
        {"day": 0, "name": "Monday", "entries": days_map[0]},
        {"day": 1, "name": "Tuesday", "entries": days_map[1]},
        {"day": 2, "name": "Wednesday", "entries": days_map[2]},
        {"day": 3, "name": "Thursday", "entries": days_map[3]},
        {"day": 4, "name": "Friday", "entries": days_map[4]},
        {"day": 5, "name": "Saturday", "entries": days_map[5]},
    ]

    classes = ClassRoom.objects.all()
    teachers = User.objects.filter(role="teacher")

    ctx = {
        "days_display": days_display,
        "classes": classes,
        "teachers": teachers,
        "selected_class": selected_class_id,
        "selected_teacher": selected_teacher_id,
    }
    return render(request, "timetable.html", ctx)


@role_required("admin")
def timetable_form(request, pk=None):
    inst = get_object_or_404(Timetable, pk=pk) if pk else None
    if request.method == "POST":
        form = TimetableForm(request.POST, instance=inst)
        if form.is_valid():
            t = form.save()
            action = "updated" if pk else "created"
            messages.success(request, f"Timetable slot successfully {action}.")
            return redirect("timetable")
    else:
        form = TimetableForm(instance=inst)
    return render(request, "timetable_form.html", {"form": form, "editing": bool(pk), "timetable": inst})


@role_required("admin")
def timetable_delete(request, pk):
    t = get_object_or_404(Timetable, pk=pk)
    if request.method == "POST":
        t.delete()
        messages.success(request, "Timetable slot deleted.")
    return redirect("timetable")


# ----------------------------------------------------------------------
# 9. ANNOUNCEMENTS
# ----------------------------------------------------------------------

@login_required
def announcement_list(request):
    u = request.user
    today = timezone.localdate()

    if u.role == "admin" or u.is_superuser:
        announcements = Announcement.objects.all()
    else:
        announcements = Announcement.objects.filter(
            Q(target_role__in=["all", u.role]),
            Q(expires_at__isnull=True) | Q(expires_at__gte=today)
        )

    return render(request, "announcements.html", {"announcements": announcements})


@role_required("admin", "teacher")
def announcement_form(request, pk=None):
    inst = get_object_or_404(Announcement, pk=pk) if pk else None
    if pk and request.user.role == "teacher" and inst.created_by != request.user:
        raise PermissionDenied("You can only edit announcements created by you.")

    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=inst)
        if form.is_valid():
            ann = form.save(commit=False)
            if not pk:
                ann.created_by = request.user
            ann.save()
            action = "updated" if pk else "published"
            messages.success(request, f"Announcement successfully {action}.")
            return redirect("announcements")
    else:
        form = AnnouncementForm(instance=inst)
    return render(request, "announcement_form.html", {"form": form, "editing": bool(pk)})


@role_required("admin", "teacher")
def announcement_delete(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.user.role == "teacher" and ann.created_by != request.user:
        raise PermissionDenied("You can only delete announcements created by you.")
    if request.method == "POST":
        ann.delete()
        messages.success(request, "Announcement deleted.")
    return redirect("announcements")


# ----------------------------------------------------------------------
# 10. SETTINGS
# ----------------------------------------------------------------------

@role_required("admin")
def settings_page(request):
    s = SiteSetting.get()
    if request.method == "POST":
        form = SiteSettingForm(request.POST, instance=s)
        if form.is_valid():
            form.save()
            messages.success(request, "System settings updated successfully.")
            return redirect("settings")
    else:
        form = SiteSettingForm(instance=s)
    return render(request, "settings.html", {"form": form, "s": s})


# ----------------------------------------------------------------------
# 11. ERROR HANDLERS
# ----------------------------------------------------------------------

def handler404(request, exception=None):
    return render(request, "404.html", status=404)

def handler403(request, exception=None):
    return render(request, "403.html", {"exception": str(exception)}, status=403)

def handler500(request):
    return render(request, "500.html", status=500)
