from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Admin, Staff, Student, Program, Subject, Session,
    Attendance, AttendanceReport, LeaveReportStudent, LeaveReportStaff,
    FeedbackStudent, FeedbackStaff, NotificationStaff, NotificationStudent,
    Result, ResultSummary,Term
)
from django.contrib.auth.models import Group

# Optionally unregister the default Group model if not used
admin.site.unregister(Group)

# ================================
# Proxy Models for Grouping (Verbose Names Only)
# ================================

# User Management
class CustomUserProxy(CustomUser):
    class Meta:
        proxy = True
        verbose_name = "Custom User"
        verbose_name_plural = "Custom Users"

class StaffProxy(Staff):
    class Meta:
        proxy = True
        verbose_name = "Staff"
        verbose_name_plural = "Staff"

class StudentProxy(Student):
    class Meta:
        proxy = True
        verbose_name = "Student"
        verbose_name_plural = "Students"

# Academic Management
class ProgramProxy(Program):
    class Meta:
        proxy = True
        verbose_name = "Program"
        verbose_name_plural = "Programs"

class SubjectProxy(Subject):
    class Meta:
        proxy = True
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

class SessionProxy(Session):
    class Meta:
        proxy = True
        verbose_name = "Session"
        verbose_name_plural = "Sessions"
        # Term
class TermProxy(Term):
    class Meta:
        proxy = True
        verbose_name = "Term"
        verbose_name_plural = "Terms"

class ResultProxy(Result):
    class Meta:
        proxy = True
        verbose_name = "Result"
        verbose_name_plural = "Results"

class ResultSummaryProxy(ResultSummary):
    class Meta:
        proxy = True
        verbose_name = "Result Summary"
        verbose_name_plural = "Result Summaries"

# Attendance & Leaves
class AttendanceProxy(Attendance):
    class Meta:
        proxy = True
        verbose_name = "Attendance"
        verbose_name_plural = "Attendances"

class AttendanceReportProxy(AttendanceReport):
    class Meta:
        proxy = True
        verbose_name = "Attendance Report"
        verbose_name_plural = "Attendance Reports"

class LeaveReportStudentProxy(LeaveReportStudent):
    class Meta:
        proxy = True
        verbose_name = "Leave Report (Student)"
        verbose_name_plural = "Leave Reports (Student)"

class LeaveReportStaffProxy(LeaveReportStaff):
    class Meta:
        proxy = True
        verbose_name = "Leave Report (Staff)"
        verbose_name_plural = "Leave Reports (Staff)"

# Feedback & Notifications
class FeedbackStudentProxy(FeedbackStudent):
    class Meta:
        proxy = True
        verbose_name = "Feedback (Student)"
        verbose_name_plural = "Feedback (Student)"

class FeedbackStaffProxy(FeedbackStaff):
    class Meta:
        proxy = True
        verbose_name = "Feedback (Staff)"
        verbose_name_plural = "Feedback (Staff)"

class NotificationStaffProxy(NotificationStaff):
    class Meta:
        proxy = True
        verbose_name = "Notification (Staff)"
        verbose_name_plural = "Notifications (Staff)"

class NotificationStudentProxy(NotificationStudent):
    class Meta:
        proxy = True
        verbose_name = "Notification (Student)"
        verbose_name_plural = "Notifications (Student)"


# ================================
# Custom Admin Classes
# ================================

class CustomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'gender', 'profile_pic', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
        ('Extra Info', {'fields': ('user_type', 'fcm_token')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'gender', 'profile_pic', 'address', 'user_type'),
        }),
    )

# ================================
# Admin Site Registrations
# ================================
admin.site.register(CustomUserProxy, CustomUserAdmin)
admin.site.register(StaffProxy)
admin.site.register(StudentProxy)
admin.site.register(ProgramProxy)
admin.site.register(SubjectProxy)
admin.site.register(SessionProxy)
admin.site.register(TermProxy)
# Term
admin.site.register(AttendanceProxy)
admin.site.register(AttendanceReportProxy)
admin.site.register(LeaveReportStudentProxy)
admin.site.register(LeaveReportStaffProxy)
admin.site.register(FeedbackStudentProxy)
admin.site.register(FeedbackStaffProxy)
admin.site.register(NotificationStaffProxy)
admin.site.register(NotificationStudentProxy)
admin.site.register(ResultProxy)
admin.site.register(ResultSummaryProxy)
