import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from core.models import (
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
    level,
)


class AttendifyModelAndCalculationTests(TestCase):
    def setUp(self):
        self.setting = SiteSetting.get()
        self.setting.threshold = 75
        self.setting.save()

        self.dept = Department.objects.create(name="Computer Science", code="CS")
        self.teacher_user = User.objects.create_user(
            username="teacher_test",
            email="teacher@test.com",
            password="pass",
            role="teacher",
            first_name="Prof",
            last_name="Test",
        )
        self.classroom = ClassRoom.objects.create(
            name="CS-1A", department=self.dept, class_teacher=self.teacher_user
        )
        self.subject = Subject.objects.create(
            name="Programming", code="CS-101", classroom=self.classroom, teacher=self.teacher_user
        )

        self.student_user = User.objects.create_user(
            username="student_test",
            email="student@test.com",
            password="pass",
            role="student",
            first_name="John",
            last_name="Doe",
        )
        self.student = Student.objects.create(
            user=self.student_user, student_id="S1001", classroom=self.classroom
        )

    def test_zero_sessions_division_by_zero_prevention(self):
        """When a student has no attendance records, percentage should be 100.0 without ZeroDivisionError."""
        self.assertEqual(self.student.attendance_set.count(), 0)
        self.assertEqual(self.student.percentage, 100.0)
        self.assertEqual(self.student.level, "safe")

    def test_attendance_calculations_normal(self):
        """Verifies calculation: attended = Present + Late, total sessions = count()."""
        d1 = timezone.localdate()
        d2 = d1 - datetime.timedelta(days=1)
        d3 = d1 - datetime.timedelta(days=2)
        d4 = d1 - datetime.timedelta(days=3)

        Attendance.objects.create(student=self.student, subject=self.subject, date=d1, status="P")
        Attendance.objects.create(student=self.student, subject=self.subject, date=d2, status="L")
        Attendance.objects.create(student=self.student, subject=self.subject, date=d3, status="A")
        Attendance.objects.create(student=self.student, subject=self.subject, date=d4, status="V")

        total, attended, present, absent, late, leave = self.student.stats()
        self.assertEqual(total, 4)
        self.assertEqual(present, 1)
        self.assertEqual(late, 1)
        self.assertEqual(absent, 1)
        self.assertEqual(leave, 1)
        self.assertEqual(attended, 2)  # P + L
        # percentage: 2 / 4 = 50.0%
        self.assertEqual(self.student.percentage, 50.0)
        # Below 75% -> critical
        self.assertEqual(self.student.level, "critical")

    def test_standing_level_logic(self):
        """Test safe, warning, and critical threshold logic."""
        # threshold is 75
        self.assertEqual(level(85), "safe")     # >= 75 + 10
        self.assertEqual(level(75), "warning")  # >= 75 and < 85
        self.assertEqual(level(70), "critical") # < 75

    def test_only_leave_records(self):
        """Student with only leave records should calculate without error."""
        d = timezone.localdate()
        Attendance.objects.create(student=self.student, subject=self.subject, date=d, status="V")
        total, attended, present, absent, late, leave = self.student.stats()
        self.assertEqual(total, 1)
        self.assertEqual(leave, 1)
        self.assertEqual(attended, 0)
        self.assertEqual(self.student.percentage, 0.0)


class AttendanceWorkflowTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Software Engineering", code="SE")
        self.teacher = User.objects.create_user(
            username="teacher1", password="teacher123", role="teacher", first_name="T1"
        )
        self.classroom = ClassRoom.objects.create(
            name="SE-2A", department=self.dept, class_teacher=self.teacher
        )
        self.subject = Subject.objects.create(
            name="Databases", code="SE-201", classroom=self.classroom, teacher=self.teacher
        )

        self.s1_u = User.objects.create_user(username="s1", password="pass", role="student", first_name="A")
        self.s1 = Student.objects.create(user=self.s1_u, student_id="SE01", classroom=self.classroom)

        self.s2_u = User.objects.create_user(username="s2", password="pass", role="student", first_name="B")
        self.s2 = Student.objects.create(user=self.s2_u, student_id="SE02", classroom=self.classroom)

        self.client = Client()
        self.client.login(username="teacher1", password="teacher123")

    def test_mark_attendance_post_and_duplicate_prevention(self):
        """Marking attendance should create records. Re-marking should update records, not duplicate."""
        today = timezone.localdate()
        post_data = {
            "classroom": self.classroom.pk,
            "subject": self.subject.pk,
            "date": today.strftime("%Y-%m-%d"),
            f"s{self.s1.pk}": "P",
            f"r{self.s1.pk}": "Great participation",
            f"s{self.s2.pk}": "A",
            f"r{self.s2.pk}": "Unexcused",
        }

        response = self.client.post(reverse("mark"), post_data)
        self.assertEqual(response.status_code, 302)

        # Verify records created
        self.assertEqual(Attendance.objects.filter(subject=self.subject, date=today).count(), 2)
        att1 = Attendance.objects.get(student=self.s1, subject=self.subject, date=today)
        self.assertEqual(att1.status, "P")
        self.assertEqual(att1.remarks, "Great participation")

        # Now re-submit with updated status for s2 (changed from Absent to Late)
        post_data[f"s{self.s2.pk}"] = "L"
        post_data[f"r{self.s2.pk}"] = "Arrived 15 mins late"
        response2 = self.client.post(reverse("mark"), post_data)
        self.assertEqual(response2.status_code, 302)

        # Still only 2 records, NO duplicates
        self.assertEqual(Attendance.objects.filter(subject=self.subject, date=today).count(), 2)
        att2 = Attendance.objects.get(student=self.s2, subject=self.subject, date=today)
        self.assertEqual(att2.status, "L")
        self.assertEqual(att2.remarks, "Arrived 15 mins late")


class SecurityAndRolePermissionsTests(TestCase):
    def setUp(self):
        self.dept = Department.objects.create(name="Data Science", code="DS")
        self.teacher1 = User.objects.create_user(
            username="prof1", password="pwd", role="teacher", first_name="Prof1"
        )
        self.teacher2 = User.objects.create_user(
            username="prof2", password="pwd", role="teacher", first_name="Prof2"
        )
        self.admin = User.objects.create_superuser(
            username="admin_user", password="pwd", email="admin@ds.com", role="admin"
        )

        self.class1 = ClassRoom.objects.create(name="DS-1", department=self.dept, class_teacher=self.teacher1)
        self.class2 = ClassRoom.objects.create(name="DS-2", department=self.dept, class_teacher=self.teacher2)

        self.s1_u = User.objects.create_user(username="ds_student1", password="pwd", role="student")
        self.s1 = Student.objects.create(user=self.s1_u, student_id="DS001", classroom=self.class1)

        self.s2_u = User.objects.create_user(username="ds_student2", password="pwd", role="student")
        self.s2 = Student.objects.create(user=self.s2_u, student_id="DS002", classroom=self.class2)

        self.client = Client()

    def test_anonymous_user_redirected_to_login(self):
        """Unauthenticated requests to protected pages must redirect to login."""
        urls = [reverse("home"), reverse("students"), reverse("mark"), reverse("settings")]
        for u in urls:
            resp = self.client.get(u)
            self.assertEqual(resp.status_code, 302)
            self.assertIn(reverse("login"), resp.url)

    def test_student_cannot_view_other_student_profile(self):
        """A student cannot view another student's detail page."""
        self.client.login(username="ds_student1", password="pwd")
        # Allowed to view own detail
        resp_own = self.client.get(reverse("student_detail", kwargs={"pk": self.s1.pk}))
        self.assertEqual(resp_own.status_code, 200)

        # Forbidden from viewing another student's detail
        resp_other = self.client.get(reverse("student_detail", kwargs={"pk": self.s2.pk}))
        self.assertEqual(resp_other.status_code, 403)

    def test_teacher_cannot_view_student_outside_their_classes(self):
        """A teacher can only view students in their assigned classes."""
        self.client.login(username="prof1", password="pwd")
        # Student in their class
        resp = self.client.get(reverse("student_detail", kwargs={"pk": self.s1.pk}))
        self.assertEqual(resp.status_code, 200)

        # Student in different class
        resp_unauth = self.client.get(reverse("student_detail", kwargs={"pk": self.s2.pk}))
        self.assertEqual(resp_unauth.status_code, 403)

    def test_student_cannot_access_mark_or_settings(self):
        """Students cannot access attendance marking or administrative settings."""
        self.client.login(username="ds_student1", password="pwd")
        resp_mark = self.client.get(reverse("mark"))
        self.assertEqual(resp_mark.status_code, 403)

        resp_set = self.client.get(reverse("settings"))
        self.assertEqual(resp_set.status_code, 403)


class SearchReportsAndExportTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_test", password="pwd", email="a@test.com", role="admin"
        )
        self.dept = Department.objects.create(name="CS", code="CS")
        self.classroom = ClassRoom.objects.create(name="CS-A", department=self.dept)
        self.teacher = User.objects.create_user(username="t_test", password="pwd", role="teacher")
        self.sub = Subject.objects.create(name="Networks", code="CS-301", classroom=self.classroom, teacher=self.teacher)

        self.u1 = User.objects.create_user(username="alice", password="pwd", role="student", first_name="Alice", last_name="Wonder")
        self.s1 = Student.objects.create(user=self.u1, student_id="A101", classroom=self.classroom)

        self.u2 = User.objects.create_user(username="bob", password="pwd", role="student", first_name="Bob", last_name="Builder")
        self.s2 = Student.objects.create(user=self.u2, student_id="B102", classroom=self.classroom)

        Attendance.objects.create(student=self.s1, subject=self.sub, date=timezone.localdate(), status="P")
        Attendance.objects.create(student=self.s2, subject=self.sub, date=timezone.localdate(), status="A")

        self.client = Client()
        self.client.login(username="admin_test", password="pwd")

    def test_student_search(self):
        """Test searching students by first name and student ID."""
        resp = self.client.get(reverse("students"), {"q": "Alice"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Alice")
        self.assertNotContains(resp, "Bob")

        resp2 = self.client.get(reverse("students"), {"q": "B102"})
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, "Bob")
        self.assertNotContains(resp2, "Alice")

    def test_attendance_csv_export(self):
        """Attendance export returns CSV with correct Content-Type and data."""
        resp = self.client.get(reverse("attendance_export"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/csv")
        content = resp.content.decode("utf-8")
        self.assertIn("Student ID", content)
        self.assertIn("A101", content)
        self.assertIn("B102", content)

    def test_reports_tabs(self):
        """Reports view renders daily, class, and low attendance reports."""
        for tab in ["daily", "class", "students", "low"]:
            resp = self.client.get(reverse("reports"), {"tab": tab})
            self.assertEqual(resp.status_code, 200)
