from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager, AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.dispatch import receiver
from django.db.models.signals import post_save
from decimal import Decimal
from django.utils import timezone
from django.utils.timezone import now  # Import this


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
        assert extra_fields["is_staff"], "Superuser must have is_staff=True."
        assert extra_fields["is_superuser"], "Superuser must have is_superuser=True."
        return self._create_user(email, password, **extra_fields)


class Session(models.Model):
    """
    Represents an academic session.
    """
    start_year = models.DateField()
    end_year = models.DateField()
    # is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"From {self.start_year} to {self.end_year}"


class CustomUser(AbstractUser):
    """
    Custom user model that uses email as the unique identifier and supports different user types.
    """
    # Using string keys for choices
    USER_TYPE = (("1", "HOD"), ("2", "Staff"), ("3", "Student"))
    GENDER = [("M", "Male"), ("F", "Female")]
    
    # Remove username; use email as the unique identifier.
    username = None  
    email = models.EmailField(unique=True)
    user_type = models.CharField(default="1", choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)  # Allow blank if no image provided.
    address = models.TextField()
    fcm_token = models.TextField(default="")  # For Firebase notifications.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Admin(models.Model):
    """
    Administrator profile linked to CustomUser.
    """
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.admin)


class Program(models.Model):
    """
    Academic program (e.g., a course of study).
    """
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    """
    Student profile linked to a CustomUser.
    """
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.DO_NOTHING, null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return f"{self.admin.last_name}, {self.admin.first_name}"


class Staff(models.Model):
    """
    Staff profile linked to a CustomUser.
    """
    program = models.ForeignKey(Program, on_delete=models.DO_NOTHING, null=True)
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.admin.last_name} {self.admin.first_name}"


class Subject(models.Model):
    """
    Subject offered in a Program.
    """
    name = models.CharField(max_length=120)
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Term(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="terms")
    name = models.CharField(max_length=10, choices=[('1st', '1st Term'), ('2nd', '2nd Term'), ('3rd', '3rd Term')])
    beginning_of_term = models.DateField(null=True, blank=True)  # New Field
    end_of_term = models.DateField(null=True, blank=True)  # New Field
    days_in_term = models.PositiveIntegerField(default=0)
    # resumption_date = models.DateField(null=True, blank=True)
    resumption_date = models.DateField(null=True, blank=True)  # ✅ Add this line!

    class Meta:
        unique_together = ('session', 'name')  # Ensures no duplicate terms in the same session

    def __str__(self):
        return f"{self.name} ({self.session.start_year} - {self.session.end_year})"
# class Attendance(models.Model):
#     subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
#     session = models.ForeignKey(Session, on_delete=models.CASCADE)
#     date = models.DateField()


# class AttendanceReport(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE)
#     attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
#     status = models.BooleanField(default=False)  # Whether student attended or not



class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    is_present = models.BooleanField(default=False)  # If checked, student is Present
    is_absent = models.BooleanField(default=False)  # New field for Absent checkbox

    class Meta:
        unique_together = ('student', 'session', 'term', 'date')  # Avoid duplicate attendance

    def __str__(self):
        return f"{self.student.admin.first_name} - {self.session} - {'Present' if self.is_present else 'Absent' if self.is_absent else 'Not Marked'}"
    
# class Attendance(models.Model):
#     """
#     Represents a specific attendance record for a subject on a given date.
#     """
#     session = models.ForeignKey(Session, on_delete=models.DO_NOTHING)
#     subject = models.ForeignKey(Subject, on_delete=models.DO_NOTHING)
#     date = models.DateField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)


class AttendanceReport(models.Model):
    """
    Individual student's attendance status for a specific attendance record.
    """
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True) 


class LeaveReportStudent(models.Model):
    """
    Student leave report.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStaff(models.Model):
    """
    Staff leave report.
    """
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStudent(models.Model):
    """
    Student feedback.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStaff(models.Model):
    """
    Staff feedback.
    """
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStaff(models.Model):
    """
    Notifications for staff.
    """
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)  # Add this field  # New field to track if notification is read.
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Notification for {self.staff}"
    
    

class NotificationStudent(models.Model):
    """
    Notifications for students.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # New field to track if notification is read.
    
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"Notification for {self.student}"

# ---------- Term and Result Models ----------

# class Term(models.Model):
#     """
#     Represents a term within an academic session.
#     Each Session is divided into three terms: 1st Term, 2nd Term, and 3rd Term.
#     """
#     session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='terms')
#     name = models.CharField(max_length=10, choices=[('1st', '1st Term'), ('2nd', '2nd Term'), ('3rd', '3rd Term')])

#     def __str__(self):
#         return f"{self.name} Term, {self.session}"






class Result(models.Model):
    """
    Stores results for a student in a subject for a particular term.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    # Allow term to be nullable temporarily for migration; later you may enforce non-null.
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
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
        unique_together = ['student', 'subject', 'term']
    
    def calculate_total(self):
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
    """
    Aggregated result summary for a student.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    # term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)  # Allow NULL temporarily
    
    attendance = models.PositiveIntegerField(default=0, null=True, blank=True)  # Stores days attended
    days_in_term = models.PositiveIntegerField(default=0, null=True, blank=True)
    resumption_date = models.DateField(null=True, blank=True)
    
    total_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    position = models.IntegerField(default=0)
    grade = models.CharField(max_length=2, default='F')
    teacher_remarks = models.TextField(blank=True, null=True)
     # ✅ Add these fields for tracking
    created_at = models.DateTimeField(auto_now_add=True)
    # created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'term')  # Ensure uniqueness per student and term

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
                f"Pos {self.position}, Grade {self.grade}"
                f"{self.student.admin.first_name} {self.student.admin.last_name} - {self.term}")


class SessionResultSummary(models.Model):
    """
    Compiled session result summary that aggregates results from all terms of a session.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    total_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=2, default='F')
    teacher_remarks = models.TextField(blank=True)
    
    def __str__(self):
        return f"Session Result for {self.student.admin.last_name}, {self.student.admin.first_name} in {self.session}"


# ---------- Signals for Profile Creation ----------

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == "1":
            Admin.objects.create(admin=instance)
        elif instance.user_type == "2":
            Staff.objects.create(admin=instance)
        elif instance.user_type == "3":
            Student.objects.create(admin=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == "1" and hasattr(instance, 'admin'):
        instance.admin.save()
    elif instance.user_type == "2" and hasattr(instance, 'staff'):
        instance.staff.save()
    elif instance.user_type == "3" and hasattr(instance, 'student'):
        instance.student.save()


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Session)
def create_terms_for_session(sender, instance, created, **kwargs):
    if created:
        # Create three terms automatically for the new session.
        term_choices = ['1st', '2nd', '3rd']
        for term_name in term_choices:
            Term.objects.create(session=instance, name=term_name)

# from django.db.models.signals import post_save
# from django.dispatch import receiver

# @receiver(post_save, sender=Session)
# def create_default_terms(sender, instance, created, **kwargs):
#     if created:
#         Term.objects.create(session=instance, name="1st")
#         Term.objects.create(session=instance, name="2nd")
#         Term.objects.create(session=instance, name="3rd")
