import json
import os
import requests
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (get_object_or_404, redirect, render, reverse)
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.template.loader import get_template

from .forms import *
from .models import *

# ------------------------------
# Admin (HOD) Views
# ------------------------------

def admin_home(request):
    """
    Display dashboard statistics for the HOD.
    """
    total_staff = Staff.objects.all().count()
    total_students = Student.objects.all().count()
    subjects = Subject.objects.all()
    total_subject = subjects.count()
    total_course = Program.objects.all().count()  # 'Program' replaces 'course'
    
    # Build attendance data per subject.
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name[:7])
        attendance_list.append(attendance_count)
    
    context = {
        'page_title': "Administrative Dashboard",
        'total_students': total_students,
        'total_staff': total_staff,
        'total_course': total_course,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list,
    }
    return render(request, 'hod_template/home_content.html', context)


def add_staff(request):
    """
    View for adding a new staff member.
    """
    form = StaffForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Staff'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            # Use 'program' field (instead of course)
            program = form.cleaned_data.get('program')
            passport = request.FILES.get('profile_pic')
            if passport:
                fs = FileSystemStorage()
                filename = fs.save(os.path.basename(passport.name), passport)
                passport_url = fs.url(filename)
            else:
                passport_url = ""
            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    user_type="2",
                    first_name=first_name,
                    last_name=last_name,
                    profile_pic=passport_url
                )
                user.gender = gender
                user.address = address
                # Assign staff's program.
                user.staff.program = program
                user.save()
                messages.success(request, "Staff successfully added!")
                return redirect(reverse('add_staff'))
            except Exception as e:
                messages.error(request, "Could not add staff: " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements.")
    return render(request, 'hod_template/add_staff_template.html', context)


def add_student(request):
    """
    View for adding a new student.
    """
    student_form = StudentForm(request.POST or None, request.FILES or None)
    context = {'form': student_form, 'page_title': 'Add Student'}
    if request.method == 'POST':
        if student_form.is_valid():
            first_name = student_form.cleaned_data.get('first_name')
            last_name = student_form.cleaned_data.get('last_name')
            address = student_form.cleaned_data.get('address')
            email = student_form.cleaned_data.get('email')
            gender = student_form.cleaned_data.get('gender')
            password = student_form.cleaned_data.get('password')
            program = student_form.cleaned_data.get('program')
            session = student_form.cleaned_data.get('session')
            passport = request.FILES.get('profile_pic')
            if passport:
                fs = FileSystemStorage()
                clean_name = os.path.basename(passport.name)
                filename = fs.save(clean_name, passport)
                passport_url = fs.url(filename)
            else:
                passport_url = ""
            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    user_type="3",
                    first_name=first_name,
                    last_name=last_name,
                    profile_pic=passport_url
                )
                user.gender = gender
                user.address = address
                user.student.session = session
                user.student.program = program
                user.save()
                messages.success(request, "Student successfully added!")
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could not add student: " + str(e))
        else:
            messages.error(request, "Could not add student: Please check the form errors.")
    return render(request, 'hod_template/add_student_template.html', context)


def add_course(request):
    """
    View for adding a new academic program.
    """
    form = CourseForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Program'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                program_obj = Program(name=name)
                program_obj.save()
                messages.success(request, "Program successfully added!")
                return redirect(reverse('add_course'))
            except Exception as e:
                messages.error(request, "Could not add program: " + str(e))
        else:
            messages.error(request, "Could not add program: Please check the form errors.")
    return render(request, 'hod_template/add_course_template.html', context)


def add_subject(request):
    """
    View for adding a new subject.
    """
    form = SubjectForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            program = form.cleaned_data.get('program')  # Updated field
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject(name=name, staff=staff, program=program)
                subject.save()
                messages.success(request, "Subject successfully added!")
                return redirect(reverse('add_subject'))
            except Exception as e:
                messages.error(request, "Could not add subject: " + str(e))
        else:
            messages.error(request, "Fill the form properly.")
    return render(request, 'hod_template/add_subject_template.html', context)


def manage_staff(request):
    """
    View for managing all staff members.
    """
    allStaff = CustomUser.objects.filter(user_type="2", staff__isnull=False)
    context = {
        'allStaff': allStaff,
        'page_title': 'Manage Staff'
    }
    return render(request, "hod_template/manage_staff.html", context)


def manage_student(request):
    """
    View for managing all students.
    """
    students = CustomUser.objects.filter(user_type="3", student__isnull=False)
    for student in students:
        student.has_result = ResultSummary.objects.filter(student=student.student).exists()
    context = {
        'students': students,
        'page_title': 'Manage Students'
    }
    return render(request, "hod_template/manage_student.html", context)


def manage_course(request):
    """
    View for managing academic programs.
    """
    courses = Program.objects.all()
    context = {
        'courses': courses,
        'page_title': 'Manage Program'
    }
    return render(request, "hod_template/manage_course.html", context)


def manage_subject(request):
    """
    View for managing subjects.
    """
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects,
        'page_title': 'Manage Subjects'
    }
    return render(request, "hod_template/manage_subject.html", context)


def edit_staff(request, staff_id):
    """
    Edit an existing staff profile.
    """
    staff = get_object_or_404(Staff, id=staff_id)
    form = StaffForm(request.POST or None, instance=staff)
    context = {
        'form': form,
        'staff_id': staff_id,
        'page_title': 'Edit Staff'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            program = form.cleaned_data.get('program')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=staff.admin.id)
                user.username = username
                user.email = email
                if password:
                    user.set_password(password)
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(os.path.basename(passport.name), passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                staff.program = program
                user.save()
                staff.save()
                messages.success(request, "Staff successfully updated!")
                return redirect(reverse('edit_staff', args=[staff_id]))
            except Exception as e:
                messages.error(request, "Could not update staff: " + str(e))
        else:
            messages.error(request, "Please fill the form properly.")
    return render(request, "hod_template/edit_staff_template.html", context)


def edit_student(request, student_id):
    """
    Edit an existing student profile.
    """
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    context = {
        'form': form,
        'student_id': student_id,
        'page_title': 'Edit Student'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            program = form.cleaned_data.get('program')
            session = form.cleaned_data.get('session')
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=student.admin.id)
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(os.path.basename(passport.name), passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.username = username
                user.email = email
                if password:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                student.session = session
                user.gender = gender
                user.address = address
                student.program = program
                user.save()
                student.save()
                messages.success(request, "Student successfully updated!")
                return redirect(reverse('edit_student', args=[student_id]))
            except Exception as e:
                messages.error(request, "Could not update student: " + str(e))
        else:
            messages.error(request, "Please fill the form properly!")
    return render(request, "hod_template/edit_student_template.html", context)


def edit_course(request, course_id):
    """
    Edit an existing academic program.
    """
    instance = get_object_or_404(Program, id=course_id)
    form = CourseForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': 'Edit Program'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course_obj = Program.objects.get(id=course_id)
                course_obj.name = name
                course_obj.save()
                messages.success(request, "Program successfully updated!")
            except Exception as e:
                messages.error(request, "Could not update program: " + str(e))
        else:
            messages.error(request, "Could not update program.")
    return render(request, 'hod_template/edit_course_template.html', context)


def edit_subject(request, subject_id):
    """
    Edit an existing subject.
    """
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'subject_id': subject_id,
        'page_title': 'Edit Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            program = form.cleaned_data.get('program')
            staff = form.cleaned_data.get('staff')
            try:
                subject_obj = Subject.objects.get(id=subject_id)
                subject_obj.name = name
                subject_obj.staff = staff
                subject_obj.program = program
                subject_obj.save()
                messages.success(request, "Subject successfully updated!")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could not update subject: " + str(e))
        else:
            messages.error(request, "Fill the form properly.")
    return render(request, 'hod_template/edit_subject_template.html', context)


def add_session(request):
    """
    Add a new academic session.
    """
    form = SessionForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session created successfully!")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, "Could not add session: " + str(e))
        else:
            messages.error(request, "Please fill the form properly.")
    return render(request, "hod_template/add_session_template.html", context)


def manage_session(request):
    """
    Manage academic sessions.
    """
    sessions = Session.objects.all()
    context = {'sessions': sessions, 'page_title': 'Manage Sessions'}
    return render(request, "hod_template/manage_session.html", context)


def edit_session(request, session_id):
    """
    Edit an existing academic session.
    """
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {'form': form, 'session_id': session_id, 'page_title': 'Edit Session'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session updated successfully!")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(request, "Session could not be updated: " + str(e))
                return render(request, "hod_template/edit_session_template.html", context)
        else:
            messages.error(request, "Invalid form submitted.")
            return render(request, "hod_template/edit_session_template.html", context)
    else:
        return render(request, "hod_template/edit_session_template.html", context)


@csrf_exempt
def check_email_availability(request):
    """
    Check if an email is already registered.
    """
    email = request.POST.get("email")
    try:
        user_exists = CustomUser.objects.filter(email=email).exists()
        return HttpResponse(user_exists)
    except Exception:
        return HttpResponse(False)


from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt


# ------------------------------
# HOD Leave and Feedback Views
# ------------------------------

@csrf_exempt
def view_staff_leave(request):
    """View and approve/reject staff leave applications."""
    if request.method == 'POST':  # AJAX request
        leave_id = request.POST.get('id')
        status = request.POST.get('status')
        try:
            leave = get_object_or_404(LeaveReportStaff, id=leave_id)
            leave.status = int(status)  # 1 for approved, -1 for rejected
            leave.save()
            return JsonResponse({"message": "Staff leave updated successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    # Render leave management page
    allLeave = LeaveReportStaff.objects.all()
    context = {'allLeave': allLeave, 'page_title': 'Staff Leave Requests'}
    return render(request, "hod_template/staff_leave_view.html", context)


@csrf_exempt
def view_student_leave(request):
    """View and approve/reject student leave applications."""
    if request.method == 'POST':  # AJAX request
        leave_id = request.POST.get('id')
        status = request.POST.get('status')
        try:
            leave = get_object_or_404(LeaveReportStudent, id=leave_id)
            leave.status = int(status)
            leave.save()
            return JsonResponse({"message": "Student leave updated successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    # Render leave management page
    allLeave = LeaveReportStudent.objects.all()
    context = {'allLeave': allLeave, 'page_title': 'Student Leave Requests'}
    return render(request, "hod_template/student_leave_view.html", context)


@csrf_exempt
def student_feedback_message(request):
    """View and respond to student feedback messages."""
    if request.method == 'POST':  # AJAX request
        feedback_id = request.POST.get('id')
        reply = request.POST.get('reply')
        try:
            feedback = get_object_or_404(FeedbackStudent, id=feedback_id)
            feedback.reply = reply
            feedback.save()
            return JsonResponse({"message": "Reply sent successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    feedbacks = FeedbackStudent.objects.all()
    context = {'feedbacks': feedbacks, 'page_title': 'Student Feedback Messages'}
    return render(request, 'hod_template/student_feedback_template.html', context)


@csrf_exempt
def staff_feedback_message(request):
    """View and respond to staff feedback messages."""
    if request.method == 'POST':  # AJAX request
        feedback_id = request.POST.get('id')
        reply = request.POST.get('reply')
        try:
            feedback = get_object_or_404(FeedbackStaff, id=feedback_id)
            feedback.reply = reply
            feedback.save()
            return JsonResponse({"message": "Reply sent successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    feedbacks = FeedbackStaff.objects.all()
    context = {'feedbacks': feedbacks, 'page_title': 'Staff Feedback Messages'}
    return render(request, 'hod_template/staff_feedback_template.html', context)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def api_fetch_hod_notifications(request):
    """Fetch new staff/student leave requests and feedback messages for the HOD."""
    if request.user.is_authenticated and request.user.user_type == "1":  # HOD (Admin)
        staff_leaves = LeaveReportStaff.objects.filter(status=0).count()
        student_leaves = LeaveReportStudent.objects.filter(status=0).count()
        student_feedbacks = FeedbackStudent.objects.filter(reply="").count()
        staff_feedbacks = FeedbackStaff.objects.filter(reply="").count()

        notifications = {
            "staff_leaves": staff_leaves,
            "student_leaves": student_leaves,
            "student_feedbacks": student_feedbacks,
            "staff_feedbacks": staff_feedbacks,
        }
        return JsonResponse(notifications)
    
    return JsonResponse({'error': 'Not authenticated'}, status=403)

from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import (
    LeaveReportStaff,
    LeaveReportStudent,
    FeedbackStudent,
    FeedbackStaff
)
import datetime

def aggregate_hod_notifications():
    """Aggregate notifications from various sources for the HOD."""
    notifications = []
    
    # Staff leave requests (status 0 means pending)
    staff_leaves = LeaveReportStaff.objects.filter(status=0)
    for leave in staff_leaves:
        notifications.append({
            "type": "Staff Leave",
            "message": f"Staff {leave.staff.admin.first_name} {leave.staff.admin.last_name} applied for leave on {leave.date}.",
            "date": leave.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "id": leave.id
        })
    
    # Student leave requests
    student_leaves = LeaveReportStudent.objects.filter(status=0)
    for leave in student_leaves:
        notifications.append({
            "type": "Student Leave",
            "message": f"Student {leave.student.admin.first_name} {leave.student.admin.last_name} applied for leave on {leave.date}.",
            "date": leave.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "id": leave.id
        })
    
    # Student feedbacks without a reply
    student_feedbacks = FeedbackStudent.objects.filter(reply="")
    for fb in student_feedbacks:
        notifications.append({
            "type": "Student Feedback",
            "message": f"Student {fb.student.admin.first_name} {fb.student.admin.last_name} submitted feedback: {fb.feedback[:50]}...",
            "date": fb.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "id": fb.id
        })
    
    # Staff feedbacks without a reply
    staff_feedbacks = FeedbackStaff.objects.filter(reply="")
    for fb in staff_feedbacks:
        notifications.append({
            "type": "Staff Feedback",
            "message": f"Staff {fb.staff.admin.first_name} {fb.staff.admin.last_name} submitted feedback: {fb.feedback[:50]}...",
            "date": fb.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "id": fb.id
        })
    
    # Optionally sort notifications by date (most recent first)
    notifications.sort(key=lambda x: x["date"], reverse=True)
    return notifications

@csrf_exempt
def ajax_get_notifications_hod(request):
    """
    Return a JSON response with aggregated notifications for the HOD.
    This view can be called via AJAX to update the notification badge and dropdown.
    """
    if request.user.is_authenticated and request.user.user_type == "1":
        notifications = aggregate_hod_notifications()
        data = {
            "notifications": notifications,
            "unread_count": len(notifications)
        }
        return JsonResponse(data, safe=False)
    return JsonResponse({'error': 'Not authenticated'}, status=403)

@csrf_exempt
def ajax_mark_notifications_read_hod(request):
    """
    In this example, we don't have a per-notification "is_read" field.
    If you add one, you could mark all notifications as read here.
    For now, simply return success.
    """
    return JsonResponse({'status': 'success'})

def hod_view_notification(request):
    """
    Render a page that shows all aggregated notifications for the HOD.
    """
    if request.user.is_authenticated and request.user.user_type == "1":
        notifications = aggregate_hod_notifications()
        context = {
            "notifications": notifications,
            "page_title": "View Notifications"
        }
        return render(request, "hod_template/hod_view_notification.html", context)
    messages.error(request, "Not authorized.")
    return redirect(reverse("login_page"))


def admin_view_attendance(request):
    """
    View attendance records.
    """
    subjects = Subject.objects.all()
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'View Attendance'
    }
    return render(request, "hod_template/admin_view_attendance.html", context)


@csrf_exempt
def get_admin_attendance(request):
    """
    Fetch attendance reports for a specific attendance record.
    """
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = get_object_or_404(Attendance, id=attendance_date_id, session=session)
        attendance_reports = AttendanceReport.objects.filter(attendance=attendance)
        json_data = []
        for report in attendance_reports:
            data = {
                "status": str(report.status),
                "name": str(report.student)
            }
            json_data.append(data)
        return JsonResponse(json_data, safe=False)
    except Exception as e:
        return HttpResponse(str(e), status=400)


def admin_view_profile(request):
    """
    View and edit admin profile.
    """
    admin_obj = get_object_or_404(Admin, admin=request.user)
    form = AdminForm(request.POST or None, request.FILES or None, instance=admin_obj)
    context = {'form': form, 'page_title': 'View/Edit Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin_obj.admin
                if password:
                    custom_user.set_password(password)
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(os.path.basename(passport.name), passport)
                    passport_url = fs.url(filename)
                    custom_user.profile_pic = passport_url
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occurred While Updating Profile " + str(e))
    return render(request, "hod_template/admin_view_profile.html", context)


def admin_notify_staff(request):
    """
    Display notification form for staff.
    """
    staff_users = CustomUser.objects.filter(user_type="2")
    context = {
        'page_title': "Send Notifications To Staff",
        'allStaff': staff_users
    }
    return render(request, "hod_template/staff_notification.html", context)


def admin_notify_student(request):
    """
    Display notification form for students.
    """
    student_users = CustomUser.objects.filter(user_type="3")
    context = {
        'page_title': "Send Notifications To Students",
        'students': student_users
    }
    return render(request, "hod_template/student_notification.html", context)


@csrf_exempt
def send_student_notification(request):
    """
    Send notification to a specific student.
    """
    id = request.POST.get('id')
    message_text = request.POST.get('message')
    student = get_object_or_404(Student, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message_text,
                'click_action': reverse('student_view_notification'),
                'icon': static('dist/img/1.png')
            },
            'to': student.admin.fcm_token
        }
        headers = {
            'Authorization': 'key=YOUR_KEY_HERE',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStudent(student=student, message=message_text)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@csrf_exempt
def send_staff_notification(request):
    """
    Send notification to a specific staff member.
    """
    id = request.POST.get('id')
    message_text = request.POST.get('message')
    staff_obj = get_object_or_404(Staff, admin_id=id)
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message_text,
                'click_action': reverse('staff_view_notification'),
                'icon': static('dist/img/1.png')
            },
            'to': staff_obj.admin.fcm_token
        }
        headers = {
            'Authorization': 'key=YOUR_KEY_HERE',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStaff(staff=staff_obj, message=message_text)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def delete_staff(request, staff_id):
    """
    Delete a staff member.
    """
    staff_user = get_object_or_404(CustomUser, staff__id=staff_id)
    staff_user.delete()
    messages.success(request, "Staff deleted successfully!")
    return redirect(reverse('manage_staff'))


def delete_student(request, student_id):
    """
    Delete a student.
    """
    student_user = get_object_or_404(CustomUser, student__id=student_id)
    student_user.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect(reverse('manage_student'))


def delete_course(request, course_id):
    """
    Delete an academic program.
    """
    course_obj = get_object_or_404(Program, id=course_id)
    try:
        course_obj.delete()
        messages.success(request, "Program deleted successfully!")
    except Exception:
        messages.error(request, "Sorry, some students are assigned to this program already. Kindly change the affected student program and try again")
    return redirect(reverse('manage_course'))


def delete_subject(request, subject_id):
    """
    Delete a subject.
    """
    subject_obj = get_object_or_404(Subject, id=subject_id)
    subject_obj.delete()
    messages.success(request, "Subject deleted successfully!")
    return redirect(reverse('manage_subject'))


def delete_session(request, session_id):
    """
    Delete an academic session.
    """
    session_obj = get_object_or_404(Session, id=session_id)
    try:
        session_obj.delete()
        messages.success(request, "Session deleted successfully!")
    except Exception:
        messages.error(request, "There are students assigned to this session. Please move them to another session.")
    return redirect(reverse('manage_session'))



# ------------------------------
# Staff Result Views
# ------------------------------

@csrf_exempt
def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    students = Student.objects.filter(program=staff.program)
    page_title = "Add Results"
    
    context = {
        'students': students,
        'subjects': subjects,
        'page_title': page_title,
    }
    
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student')
            if not student_id:
                messages.error(request, "Please select a student.")
                return render(request, "staff_template/staff_add_result.html", context)
            student = get_object_or_404(Student, id=student_id)
            
            for subject in subjects:
                ca_test1 = float(request.POST.get(f'ca_test1_{subject.id}', 0))
                ca_test2 = float(request.POST.get(f'ca_test2_{subject.id}', 0))
                exam_score = float(request.POST.get(f'exam_{subject.id}', 0))
                
                Result.objects.update_or_create(
                    student=student,
                    subject=subject,
                    defaults={
                        'ca_test1': ca_test1,
                        'ca_test2': ca_test2,
                        'exam_score': exam_score,
                    }
                )
            
            teacher_remarks = request.POST.get('teacher_remarks', '')
            
            summary, created = ResultSummary.objects.get_or_create(
                student=student,
                defaults={
                    'total_score': 0,
                    'average_score': 0,
                    'position': 0,
                    'grade': 'F',
                    'teacher_remarks': teacher_remarks
                }
            )
            if not created:
                summary.teacher_remarks = teacher_remarks
                summary.save()
            
            messages.success(request, "Scores saved successfully!")
            return redirect(reverse('staff_result_detail', kwargs={'student_id': student.id}))
        except Exception as e:
            messages.error(request, "Error Occurred While Processing Form: " + str(e))
    
    return render(request, "staff_template/staff_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        result = get_object_or_404(Result, student=student, subject=subject)
        
        result_data = {
            'ca_test1': float(result.ca_test1),
            'ca_test2': float(result.ca_test2),
            'exam_score': float(result.exam_score),
            'total_score': float(result.total_score),
            'grade': result.grade  # Assuming your Result model has a @property "grade"
        }
        return HttpResponse(json.dumps(result_data), content_type='application/json')
    except Exception as e:
        return HttpResponse('False')


def staff_student_list(request):
    staff = get_object_or_404(Staff, admin=request.user)
    students = Student.objects.filter(program=staff.program)
    for student in students:
        student.has_result = ResultSummary.objects.filter(student=student).exists()
    
    context = {
        'students': students,
        'page_title': 'Student List',
    }
    return render(request, 'staff_template/staff_student_list.html', context)


# --------------------------------
# EditResultView class-based view
# --------------------------------
from django.views import View

class EditResultView(View):
    def get(self, request, student_id, *args, **kwargs):
        student = get_object_or_404(Student, id=student_id)
        form = EditResultForm(initial={'student': student})
        staff = get_object_or_404(Staff, admin=request.user)
        form.fields['subject'].queryset = Subject.objects.filter(staff=staff)
        context = {
            'form': form,
            'page_title': "Edit Student's Result",
            'student': student,
        }
        return render(request, "staff_template/edit_student_result.html", context)

    def post(self, request, student_id, *args, **kwargs):
        form = EditResultForm(request.POST)
        context = {'form': form, 'page_title': "Edit Student's Result"}
        if form.is_valid():
            try:
                student = form.cleaned_data.get('student')
                subject = form.cleaned_data.get('subject')
                ca_test1 = form.cleaned_data.get('ca_test1')
                ca_test2 = form.cleaned_data.get('ca_test2')
                exam_score = form.cleaned_data.get('exam_score')
                result = Result.objects.get(student=student, subject=subject)
                result.ca_test1 = ca_test1
                result.ca_test2 = ca_test2
                result.exam_score = exam_score
                result.save()  # This will recalculate total_score.
                messages.success(request, "Result Updated")
                return redirect(reverse('edit_student_result', kwargs={'student_id': student.id}))
            except Exception as e:
                messages.warning(request, "Result Could Not Be Updated: " + str(e))
        else:
            messages.warning(request, "Result Could Not Be Updated")
        return render(request, "staff_template/edit_student_result.html", context)


def staff_delete_result(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    try:
        Result.objects.filter(student=student).delete()
        ResultSummary.objects.filter(student=student).delete()
        messages.success(request, "Results deleted successfully!")
    except Exception as e:
        messages.error(request, "Could not delete results: " + str(e))
    return redirect('staff_student_list')


def compute_result_summary(student):
    results = Result.objects.filter(student=student)
    if results.exists():
        total_score = sum(result.total_score or 0 for result in results)
        num_subjects = results.count()
        average_score = total_score / num_subjects if num_subjects > 0 else 0
        if average_score >= 90:
            grade = 'A+'
        elif average_score >= 80:
            grade = 'A'
        elif average_score >= 70:
            grade = 'B'
        elif average_score >= 60:
            grade = 'C'
        elif average_score >= 50:
            grade = 'D'
        else:
            grade = 'F'
        position = 1
        return total_score, average_score, position, grade
    else:
        return 0, 0, 0, 'F'


def staff_result_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    results = Result.objects.filter(student=student)
    total_score = sum(result.total_score or 0 for result in results)
    num_subjects = results.count()
    average_score = total_score / num_subjects if num_subjects > 0 else 0
    summaries = ResultSummary.objects.filter(student__program=student.program).order_by('-average_score')
    ranked_ids = list(summaries.values_list('student__id', flat=True))
    if student.id in ranked_ids:
        position = ranked_ids.index(student.id) + 1
    else:
        position = 1
    if average_score >= 90:
        grade = 'A+'
    elif average_score >= 80:
        grade = 'A'
    elif average_score >= 70:
        grade = 'B'
    elif average_score >= 60:
        grade = 'C'
    elif average_score >= 50:
        grade = 'D'
    else:
        grade = 'F'
    summary, created = ResultSummary.objects.get_or_create(
        student=student,
        defaults={
            'total_score': total_score,
            'average_score': average_score,
            'position': position,
            'grade': grade,
            'teacher_remarks': ''
        }
    )
    if not created:
        summary.total_score = total_score
        summary.average_score = average_score
        summary.position = position
        summary.grade = grade
        summary.save()
    context = {
        'student': student,
        'results': results,
        'summary': summary,
        'page_title': "Student Result Detail",
    }
    return render(request, 'staff_template/staff_result_detail.html', context)


from weasyprint import HTML, CSS

def staff_result_pdf(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    results = Result.objects.filter(student=student)
    summary, created = ResultSummary.objects.get_or_create(
        student=student,
        defaults={
            'total_score': 0,
            'average_score': 0,
            'position': 0,
            'grade': 'F',
            'teacher_remarks': ''
        }
    )
    context = {
        'student': student,
        'results': results,
        'summary': summary,
        'page_title': "Student Result Detail",
    }
    template = get_template("staff_template/staff_result_detail_pdf.html")
    html_string = template.render(context)
    base_url = request.build_absolute_uri('/')
    css_string = """
    @page { size: A4; margin: 10mm; }
    body footer { display: none; }
    body::after {
        content: "Hibiscus Royal Academy";
        position: fixed;
        bottom: 10mm;
        right: 10mm;
        font-size: 40px;
        color: rgba(0, 0, 0, 0.15);
        transform: rotate(-45deg);
        z-index: 9999;
    }
    """
    css = CSS(string=css_string)
    html = HTML(string=html_string, base_url=base_url)
    pdf_file = html.write_pdf(stylesheets=[css])
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="result_{student.id}.pdf"'
    return response
