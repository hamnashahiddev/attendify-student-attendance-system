import random
import datetime
from django.core.management.base import BaseCommand
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
)


class Command(BaseCommand):
    help = "Populate demo data"

    def handle(self, *args, **kwargs):
        random.seed(7)
        SiteSetting.get()

        admin_user = User.objects.filter(username="admin").first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                "admin", "admin@attendify.edu", "admin123", role="admin", first_name="Ayesha", last_name="Khan"
            )
            self.stdout.write("Created superuser admin.")

        depts = []
        for name, code in [("Computer Science", "CS"), ("Software Engineering", "SE"), ("Data Science", "DS")]:
            dept, _ = Department.objects.get_or_create(code=code, defaults={"name": name})
            depts.append(dept)

        fn = ["Ali", "Sara", "Hamza", "Fatima", "Usman", "Zainab", "Bilal", "Hira", "Omar", "Maryam", "Danish", "Noor", "Talha", "Iqra", "Faizan", "Amna", "Saad", "Laiba", "Hassan", "Mehwish"]
        ln = ["Ahmed", "Malik", "Raza", "Sheikh", "Qureshi", "Chaudhry", "Iqbal", "Butt"]

        teachers = []
        for i, name in enumerate(["Dr. Imran", "Prof. Nadia", "Dr. Kamran"], 1):
            t = User.objects.filter(username=f"teacher{i}").first()
            if not t:
                t = User.objects.create_user(
                    f"teacher{i}",
                    f"teacher{i}@attendify.edu",
                    "teacher123",
                    role="teacher",
                    first_name=name,
                    last_name=random.choice(ln),
                    phone=f"+92 300 123450{i}",
                )
            teachers.append(t)

        classes = []
        for i, d in enumerate(depts):
            c, _ = ClassRoom.objects.get_or_create(
                name=f"{d.code}-A",
                department=d,
                defaults={"class_teacher": teachers[i % len(teachers)], "capacity": 40},
            )
            classes.append(c)

        subs = []
        for ci, c in enumerate(classes):
            for j, sname in enumerate(["Programming", "Databases"]):
                code = f"{c.name}-{j+1}"
                sub, _ = Subject.objects.get_or_create(
                    code=code,
                    defaults={
                        "name": sname,
                        "classroom": c,
                        "teacher": teachers[ci % len(teachers)],
                    },
                )
                subs.append(sub)

        studs = []
        for i in range(20):
            sid = f"S{2026000 + i + 1}"
            u = User.objects.filter(username=f"student{i+1}").first()
            if not u:
                u = User.objects.create_user(
                    f"student{i+1}",
                    f"student{i+1}@attendify.edu",
                    "student123",
                    role="student",
                    first_name=fn[i],
                    last_name=random.choice(ln),
                    phone=f"+92 321 98765{i:02d}",
                )
            s, _ = Student.objects.get_or_create(
                student_id=sid,
                defaults={"user": u, "classroom": classes[i % len(classes)], "status": "active"},
            )
            studs.append(s)

        # Seed attendance records for past 30 days if sparse
        if Attendance.objects.count() < 50:
            today = timezone.localdate()
            bias = {s.pk: random.uniform(0.65, 0.98) for s in studs}
            for d in range(30):
                day = today - datetime.timedelta(days=d)
                if day.weekday() > 4:
                    continue
                for sub in subs:
                    for s in [x for x in studs if x.classroom_id == sub.classroom_id]:
                        r = random.random()
                        b = bias[s.pk]
                        st = "P" if r < b else "L" if r < b + 0.04 else "V" if r < b + 0.06 else "A"
                        Attendance.objects.get_or_create(
                            student=s,
                            subject=sub,
                            date=day,
                            defaults={"status": st, "marked_by": sub.teacher},
                        )

        # Seed Timetable entries if none exist
        if not Timetable.objects.exists():
            time_slots = [
                (datetime.time(9, 0), datetime.time(10, 30)),
                (datetime.time(11, 0), datetime.time(12, 30)),
                (datetime.time(14, 0), datetime.time(15, 30)),
            ]
            for c in classes:
                c_subs = [s for s in subs if s.classroom_id == c.pk]
                for day_idx in range(5):  # Mon - Fri
                    slot = time_slots[day_idx % len(time_slots)]
                    sub = c_subs[day_idx % len(c_subs)]
                    Timetable.objects.create(
                        classroom=c,
                        subject=sub,
                        teacher=sub.teacher,
                        day_of_week=day_idx,
                        start_time=slot[0],
                        end_time=slot[1],
                        room_number=f"Room {101 + day_idx}",
                    )
            self.stdout.write("Created timetable slots.")

        # Seed Announcements
        if not Announcement.objects.exists():
            Announcement.objects.create(
                title="Mid-Term Examination Schedule Announced",
                message="Mid-term examinations will commence from next Monday. Please review the updated timetable and ensure your attendance is above the 75% threshold to be eligible.",
                target_role="all",
                created_by=admin_user,
                expires_at=timezone.localdate() + datetime.timedelta(days=30),
            )
            Announcement.objects.create(
                title="Faculty Meeting regarding Attendance Compliance",
                message="All teachers are requested to ensure daily attendance is finalized before 4:00 PM every weekday.",
                target_role="teacher",
                created_by=admin_user,
                expires_at=timezone.localdate() + datetime.timedelta(days=14),
            )
            Announcement.objects.create(
                title="Attendance Shortage Advisory",
                message="Students with attendance below 75% must contact their respective department coordinators immediately.",
                target_role="student",
                created_by=admin_user,
                expires_at=timezone.localdate() + datetime.timedelta(days=20),
            )
            self.stdout.write("Created announcements.")

        # Seed Sample Notifications
        if not Notification.objects.exists():
            for u in User.objects.all()[:5]:
                Notification.objects.create(
                    user=u,
                    title="Welcome to Attendify Portal",
                    message="Your account is active. You can now track your attendance and schedule in real-time.",
                    link="/",
                )
            self.stdout.write("Created notifications.")

        self.stdout.write(self.style.SUCCESS("Demo seeding completed! Ready: admin/admin123, teacher1/teacher123, student1/student123"))
