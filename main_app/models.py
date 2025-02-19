from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager, AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.dispatch import receiver
from django.db.models.signals import post_save
from decimal import Decimal

# ---------- Custom User and Related Models ----------

class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


class Session(models.Model):
    start_year = models.DateField()
    end_year = models.DateField()

    def __str__(self):
        return "From " + str(self.start_year) + " to " + str(self.end_year)


class CustomUser(AbstractUser):
    USER_TYPE = ((1, "HOD"), (2, "Staff"), (3, "Student"))
    GENDER = [("M", "Male"), ("F", "Female")]
    
    # Remove username; we'll use email as the unique identifier.
    username = None  
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField()
    address = models.TextField()
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.last_name + ", " + self.first_name


class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)


class Program(models.Model):
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.DO_NOTHING, null=True, blank=False)
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.admin.last_name + ", " + self.admin.first_name


class Staff(models.Model):
    program = models.ForeignKey(Program, on_delete=models.DO_NOTHING, null=True, blank=False)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.admin.last_name + " " + self.admin.first_name


class Subject(models.Model):
    name = models.CharField(max_length=120)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Attendance(models.Model):
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
    subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AttendanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStaff(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# ---------- Updated Result Module ----------

# Replace the previous StudentResult with an updated Result model
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    ca_test1 = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(30)]
    )
    ca_test2 = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    exam_score = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        validators=[MinValueValidator(0), MaxValueValidator(60)]
    )
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'subject']
    
    def calculate_total(self):
        # Total Score = CA Test 1 + CA Test 2 + Exam Score
        return self.ca_test1 + self.ca_test2 + self.exam_score
    
    def save(self, *args, **kwargs):
        self.total_score = self.calculate_total()
        super().save(*args, **kwargs)
    
    @property
    def grade(self):
        total = self.total_score
        if total >= Decimal('90'):
            return 'A+'
        elif total >= Decimal('80'):
            return 'A'
        elif total >= Decimal('70'):
            return 'B'
        elif total >= Decimal('60'):
            return 'C'
        elif total >= Decimal('50'):
            return 'D'
        else:
            return 'F'
    
    def __str__(self):
        return f"{self.student.admin.last_name}, {self.student.admin.first_name} - {self.subject.name}: {self.total_score}"


class ResultSummary(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE)
    total_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    position = models.IntegerField(default=0)
    grade = models.CharField(max_length=2, default='F')
    teacher_remarks = models.TextField(blank=True)
    
    def calculate_grade(self):
        avg = float(self.average_score)
        if avg >= 90:
            return 'A+'
        elif avg >= 80:
            return 'A'
        elif avg >= 70:
            return 'B'
        elif avg >= 60:
            return 'C'
        elif avg >= 50:
            return 'D'
        else:
            return 'F'
    
    def __str__(self):
        return (f"Result Summary for {self.student.admin.last_name}, "
                f"{self.student.admin.first_name}: Avg {self.average_score}, "
                f"Pos {self.position}, Grade {self.grade}")


# ---------- Signals for Profile Creation ----------

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            Admin.objects.create(admin=instance)
        if instance.user_type == 2:
            Staff.objects.create(admin=instance)
        if instance.user_type == 3:
            Student.objects.create(admin=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        instance.admin.save()
    if instance.user_type == 2:
        instance.staff.save()
    if instance.user_type == 3:
        instance.student.save()
