import datetime
import json
import os
import requests
from decimal import Decimal  # For compile_session_results calculations
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
from django.templatetags.static import static
from django.views import View
from django.utils import timezone
from datetime import datetime



from .forms import *  # Ensure your forms include TermResultForm (with a 'term' field)
from .models import *  # This imports CustomUser, Staff, Student, Program, Subject, Attendance, AttendanceReport, LeaveReportStaff, FeedbackStaff, NotificationStaff, Result, ResultSummary, Term, etc.

# ------------------------------
# Dashboard and General Views
# ------------------------------

# def staff_home(request):
#     staff = get_object_or_404(Staff, admin=request.user)
#     total_students = Student.objects.filter(program=staff.program).count()
#     total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
#     subjects = Subject.objects.filter(staff=staff)
#     total_subject = subjects.count()
    
#     # Build attendance data for each subject.
#     attendance_list = []
#     subject_list = []
#     for subject in subjects:
#         attendance_count = Attendance.objects.filter(subject=subject).count()
#         subject_list.append(subject.name)
#         attendance_list.append(attendance_count)
    
#     context = {
#         'page_title': f'Staff Panel - {staff.admin.last_name} ({staff.program})',
#         'total_students': total_students,
#         'total_attendance': sum(attendance_list),
#         'total_leave': total_leave,
#         'total_subject': total_subject,
#         'subject_list': subject_list,
#         'attendance_list': attendance_list,
#     }
#     return render(request, 'staff_template/home_content.html', context)
def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    total_students = Student.objects.filter(program=staff.program).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    subjects = Subject.objects.filter(staff=staff)
    total_subject = subjects.count()
    
    # Attendance should now be counted per student, not subject
    attendance_list = []
    subject_list = []
    
    for student in Student.objects.filter(program=staff.program):
        attendance_count = Attendance.objects.filter(student=student).count()
        subject_list.append(f"{student.admin.first_name} {student.admin.last_name}")
        attendance_list.append(attendance_count)
    
    context = {
        'page_title': f'Staff Panel - {staff.admin.last_name} ({staff.program})',
        'total_students': total_students,
        'total_attendance': sum(attendance_list),
        'total_leave': total_leave,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list,
    }
    return render(request, 'staff_template/home_content.html', context)


def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Take Attendance'
    }
    return render(request, 'staff_template/staff_take_attendance.html', context)


@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        # Filter students by the subject's program and the selected session.
        students = Student.objects.filter(program=subject.program, session=session)
        student_data = []
        for student in students:
            data = {
                "id": student.id,
                "name": student.admin.last_name + " " + student.admin.first_name
            }
            student_data.append(data)
        return JsonResponse(student_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    students = json.loads(student_data)
    try:
        session = get_object_or_404(Session, id=session_id)
        subject = get_object_or_404(Subject, id=subject_id)
        attendance, created = Attendance.objects.get_or_create(session=session, subject=subject, date=date)
        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            attendance_report, report_created = AttendanceReport.objects.get_or_create(student=student, attendance=attendance)
            if report_created:
                attendance_report.status = student_dict.get('status')
                attendance_report.save()
    except Exception as e:
        return HttpResponse(str(e), status=400)
    return HttpResponse("OK")


def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Update Attendance'
    }
    return render(request, 'staff_template/staff_update_attendance.html', context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        attendance_obj = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=attendance_obj)
        student_data = []
        for att in attendance_data:
            data = {
                "id": att.student.id,
                "name": att.student.admin.last_name + " " + att.student.admin.first_name,
                "status": att.status
            }
            student_data.append(data)
        return JsonResponse(student_data, safe=False)
    except Exception as e:
        return HttpResponse(str(e), status=400)


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)
        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return HttpResponse(str(e), status=400)
    return HttpResponse("OK")


from django.http import JsonResponse

@csrf_exempt
def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    # Mark them as read if needed; you could add an is_read field
    notifications.update(is_read=True)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)



@csrf_exempt
def ajax_staff_notifications3(request):
    staff = request.user.staff  # Assumes a reverse relation exists.
    # Only fetch notifications that are not read.
    notifications = NotificationStaff.objects.filter(staff=staff, is_read=False)
    data = [{'id': n.id, 'message': n.message} for n in notifications]
    return JsonResponse(data, safe=False)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import NotificationStaff

def ajax_staff_notifications(request):
    if not hasattr(request.user, 'staff'):
        return JsonResponse({'notifications': [], 'unread_count': 0})  # Return empty list if not staff.

    staff = request.user.staff  # Safe to access now
    notifications = NotificationStaff.objects.filter(staff=staff, is_read=False)

    data = {
        'notifications': [{'id': n.id, 'message': n.message, 'type': 'Staff'} for n in notifications],
        'unread_count': notifications.count()
    }
    return JsonResponse(data, safe=False)


@csrf_exempt
def ajax_get_notifications_staff(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff, is_read=False)
    data = {
        'notifications': [{'id': n.id, 'message': n.message, 'type': 'Staff'} for n in notifications],
        'unread_count': notifications.count()
    }
    return JsonResponse(data, safe=False)

@csrf_exempt
def ajax_mark_notifications_read_staff(request):
    staff = get_object_or_404(Staff, admin=request.user)
    NotificationStaff.objects.filter(staff=staff, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)

def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None, instance=staff)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = staff.admin
                if password:
                    admin.set_password(password)
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(os.path.basename(passport.name), passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = filename  # Save the relative path
                    
                    # admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                staff.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(request, "Error Occurred While Updating Profile " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)
    return render(request, "staff_template/staff_view_profile.html", context)

@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")

# ------------------------------
# Staff Result Views
# ------------------------------

# def staff_add_result(request):
#     """Handles staff adding student results, including attendance & resumption date."""
#     staff = request.user.staff  
#     subjects = Subject.objects.filter(staff=staff)
#     students = Student.objects.filter(program=staff.program)
#     sessions = Session.objects.all()
#     terms = Term.objects.all()

#     if request.method == 'POST':
#         try:
#             student_id = request.POST.get('student')
#             session_id = request.POST.get('session')
#             term_id = request.POST.get('term')
#             resumption_date = request.POST.get('resumption_date')
#             days_in_term = request.POST.get('days_in_term')
#             attendance = request.POST.get('attendance')
#             teacher_remarks = request.POST.get('teacher_remarks', '')

#             # Validate inputs
#             if not student_id or not session_id or not term_id:
#                 messages.error(request, "Please select a student, session, and term.")
#                 return redirect('staff_add_result')

#             student = get_object_or_404(Student, id=student_id)
#             session = get_object_or_404(Session, id=session_id)
#             term = get_object_or_404(Term, id=term_id, session=session)

#             # 🔹 Check if a ResultSummary already exists for this student & term
#             summary, created = ResultSummary.objects.get_or_create(
#                 student=student,
#                 term=term,
#                 defaults={
#                     'resumption_date': resumption_date,
#                     'days_in_term': days_in_term,
#                     'attendance': attendance,
#                     'teacher_remarks': teacher_remarks
#                 }
#             )

#             if not created:  # 🔹 If already exists, update instead of creating duplicate
#                 summary.resumption_date = resumption_date
#                 summary.days_in_term = days_in_term
#                 summary.attendance = attendance
#                 summary.teacher_remarks = teacher_remarks
#                 summary.save()

#             # 🔹 Save results for each subject
#             for subject in subjects:
#                 ca_test1 = float(request.POST.get(f'ca_test1_{subject.id}', 0))
#                 ca_test2 = float(request.POST.get(f'ca_test2_{subject.id}', 0))
#                 exam_score = float(request.POST.get(f'exam_{subject.id}', 0))
#                 total_score = ca_test1 + ca_test2 + exam_score

#                 Result.objects.update_or_create(
#                     student=student,
#                     subject=subject,
#                     term=term,
#                     defaults={
#                         'ca_test1': ca_test1,
#                         'ca_test2': ca_test2,
#                         'exam_score': exam_score,
#                         'total_score': total_score
#                     }
#                 )

#             messages.success(request, "Results saved successfully!")
#             return redirect('staff_add_result')

#         except Exception as e:
#             messages.error(request, f"Error occurred while saving results: {e}")

#     context = {
#         'students': students,
#         'sessions': sessions,
#         'terms': terms,
#         'subjects': subjects,
#         'page_title': 'Add Student Results',
#     }
#     return render(request, "staff_template/staff_add_result.html", context)

@csrf_exempt
def staff_views_get_attendance(request):
    """Returns total attendance count for a student in a session & term."""
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        session_id = request.POST.get("session_id")
        term_id = request.POST.get("term_id")

        # 🔴 If any required field is missing, return an error
        if not student_id or not session_id or not term_id:
            return JsonResponse({"success": False, "error": "Missing required data"}, status=400)

        student = get_object_or_404(Student, id=student_id)
        session = get_object_or_404(Session, id=session_id)
        term = get_object_or_404(Term, id=term_id, session=session)

        attendance_count = Attendance.objects.filter(
            student=student, session=session, term=term, is_present=True
        ).count()

        return JsonResponse({"success": True, "attendance_count": attendance_count})

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)



@csrf_exempt
def calculate_days_in_term(request):
    """Calculates the number of days between the beginning and end of term."""
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        if not start_date or not end_date:
            return JsonResponse({"success": False, "error": "Missing required dates"}, status=400)

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

            if end_date < start_date:
                return JsonResponse({"success": False, "error": "End date cannot be before start date"}, status=400)

            days_in_term = (end_date - start_date).days
            return JsonResponse({"success": True, "days_in_term": days_in_term})

        except ValueError:
            return JsonResponse({"success": False, "error": "Invalid date format"}, status=400)

    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)


# def staff_add_result(request):
#     """Handles staff adding student results, including attendance & term dates."""
#     staff = request.user.staff
#     subjects = Subject.objects.filter(staff=staff)
#     students = Student.objects.filter(program=staff.program)
#     sessions = Session.objects.all()
#     terms = Term.objects.all()

#     if request.method == 'POST':
#         try:
#             student_id = request.POST.get('student')
#             session_id = request.POST.get('session')
#             term_id = request.POST.get('term')
#             beginning_of_term = request.POST.get('beginning_of_term')
#             end_of_term = request.POST.get('end_of_term')
#             resumption_date = request.POST.get('resumption_date')
#             days_in_term = request.POST.get('days_in_term')
#             attendance = request.POST.get('attendance')
#             teacher_remarks = request.POST.get('teacher_remarks', '')

#             # Validate inputs
#             if not student_id or not session_id or not term_id:
#                 messages.error(request, "Please select a student, session, and term.")
#                 return redirect('staff_add_result')

#             student = get_object_or_404(Student, id=student_id)
#             session = get_object_or_404(Session, id=session_id)
#             term = get_object_or_404(Term, id=term_id, session=session)

#             # Update Term with the new dates
#             term.beginning_of_term = beginning_of_term
#             term.end_of_term = end_of_term
#             term.days_in_term = days_in_term
#             term.save()

#             # 🔹 Check if a ResultSummary already exists for this student & term
#             summary, created = ResultSummary.objects.get_or_create(
#                 student=student,
#                 term=term,
#                 defaults={
#                     'resumption_date': resumption_date,
#                     'days_in_term': days_in_term,
#                     'attendance': attendance,
#                     'teacher_remarks': teacher_remarks
#                 }
#             )

#             if not created:  # 🔹 If already exists, update instead of creating duplicate
#                 summary.resumption_date = resumption_date
#                 summary.days_in_term = days_in_term
#                 summary.attendance = attendance
#                 summary.teacher_remarks = teacher_remarks
#                 summary.save()

#             # 🔹 Save results for each subject
#             for subject in subjects:
#                 ca_test1 = float(request.POST.get(f'ca_test1_{subject.id}', 0))
#                 ca_test2 = float(request.POST.get(f'ca_test2_{subject.id}', 0))
#                 exam_score = float(request.POST.get(f'exam_{subject.id}', 0))
#                 total_score = ca_test1 + ca_test2 + exam_score

#                 Result.objects.update_or_create(
#                     student=student,
#                     subject=subject,
#                     term=term,
#                     defaults={
#                         'ca_test1': ca_test1,
#                         'ca_test2': ca_test2,
#                         'exam_score': exam_score,
#                         'total_score': total_score
#                     }
#                 )

#             messages.success(request, "Results saved successfully!")
#             return redirect('staff_add_result')

#         except Exception as e:
#             messages.error(request, f"Error occurred while saving results: {e}")

#     context = {
#         'students': students,
#         'sessions': sessions,
#         'terms': terms,
#         'subjects': subjects,
#         'page_title': 'Add Student Results',
#     }
#     return render(request, "staff_template/staff_add_result.html", context)
from datetime import datetime

def staff_add_result(request):
    """Handles staff adding student results, including attendance & term dates."""
    staff = request.user.staff
    subjects = Subject.objects.filter(staff=staff)
    students = Student.objects.filter(program=staff.program)
    sessions = Session.objects.all()
    terms = Term.objects.all()

    if request.method == 'POST':
        try:
            # Fetching data from the form
            student_id = request.POST.get('student')
            session_id = request.POST.get('session')
            term_id = request.POST.get('term')
            beginning_of_term = request.POST.get('beginning_of_term')
            end_of_term = request.POST.get('end_of_term')
            resumption_date = request.POST.get('resumption_date')
            days_in_term = request.POST.get('days_in_term')
            attendance = request.POST.get('attendance')
            teacher_remarks = request.POST.get('teacher_remarks', '').strip()

            # ✅ Validate mandatory fields
            if not student_id or not session_id or not term_id:
                messages.error(request, "Please select a student, session, and term.")
                return redirect('staff_add_result')
            
            # ✅ Validate dates
            if not beginning_of_term or not end_of_term or not resumption_date:
                messages.error(request, "Please provide all required dates.")
                return redirect('staff_add_result')

            # ✅ Validate days and attendance (Convert to integer)
            try:
                days_in_term = int(days_in_term)
                attendance = int(attendance)
            except ValueError:
                messages.error(request, "Days in term and attendance must be valid numbers.")
                return redirect('staff_add_result')

            # ✅ Get the required objects
            student = get_object_or_404(Student, id=student_id)
            session = get_object_or_404(Session, id=session_id)
            term = get_object_or_404(Term, id=term_id, session=session)

            # ✅ Update Term with the new dates
            term.beginning_of_term = beginning_of_term
            term.end_of_term = end_of_term
            term.days_in_term = days_in_term
            term.save()

            # ✅ Check if a ResultSummary already exists
            summary, created = ResultSummary.objects.get_or_create(
                student=student,
                term=term,
                defaults={
                    'resumption_date': resumption_date,
                    'days_in_term': days_in_term,
                    'attendance': attendance,
                    'teacher_remarks': teacher_remarks
                }
            )

            # ✅ If already exists, update instead of creating duplicate
            if not created:
                summary.resumption_date = resumption_date
                summary.days_in_term = days_in_term
                summary.attendance = attendance
                summary.teacher_remarks = teacher_remarks
                summary.save()

            # ✅ Save results for each subject
            for subject in subjects:
                # Fetch scores, default to 0 if empty
                ca_test1 = float(request.POST.get(f'ca_test1_{subject.id}', 0) or 0)
                ca_test2 = float(request.POST.get(f'ca_test2_{subject.id}', 0) or 0)
                exam_score = float(request.POST.get(f'exam_{subject.id}', 0) or 0)
                total_score = ca_test1 + ca_test2 + exam_score

                # Validate that total is within acceptable limits
                if total_score > 100:
                    messages.warning(request, f"Total score for {subject.name} cannot exceed 100.")
                    continue

                Result.objects.update_or_create(
                    student=student,
                    subject=subject,
                    term=term,
                    defaults={
                        'ca_test1': ca_test1,
                        'ca_test2': ca_test2,
                        'exam_score': exam_score,
                        'total_score': total_score
                    }
                )

            messages.success(request, "Results saved successfully!")
            return redirect('staff_add_result')

        except Exception as e:
            # ✅ Log the error (for debugging)
            print(f"Error: {e}")
            messages.error(request, f"An unexpected error occurred: {e}")

    # ✅ Prepare context for template
    context = {
        'students': students,
        'sessions': sessions,
        'terms': terms,
        'subjects': subjects,
        'page_title': 'Add Student Results',
    }
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
            'grade': result.grade
        }
        return HttpResponse(json.dumps(result_data), content_type='application/json')
    except Exception as e:
        return HttpResponse('False')

def staff_student_list(request):
    staff = get_object_or_404(Staff, admin=request.user)
    students = Student.objects.filter(program=staff.program)
    for student in students:
        student.has_result = ResultSummary.objects.filter(student=student).exists()
    sessions = Session.objects.all()
    terms = Term.objects.all()
    context = {
        'students': students,
        'sessions': sessions,
        'terms': terms,
        'page_title': 'Student List',
    }
    return render(request, 'staff_template/staff_student_list.html', context)

def staff_view_result_filtered(request):
    student_id = request.GET.get('student')
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')

    if not (student_id and session_id and term_id):
        messages.error(request, "Please select a student, session, and term.")
        return redirect('staff_student_list')

    student = get_object_or_404(Student, id=student_id)
    session = get_object_or_404(Session, id=session_id)
    term = get_object_or_404(Term, id=term_id, session=session)

    # Get number of students in the same program
    no_in_class = Student.objects.filter(program=student.program).count()

    # Get term details
    resumption_date = term.resumption_date if hasattr(term, 'resumption_date') else "N/A"
    days_in_term = term.days_in_term if hasattr(term, 'days_in_term') else 0

    # Get student's attendance in this session & term
    attendance = Attendance.objects.filter(student=student, session=session, term=term, is_present=True).count()

    # Get all results for this student in this term
    results = Result.objects.filter(student=student, term=term)

    # Calculate Grand Total Score
    total_score = sum(result.total_score for result in results)

    # Calculate Final Average Score
    num_subjects = results.count()
    average_score = total_score / num_subjects if num_subjects > 0 else 0

    # Assign Grade Based on Average
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

    # Get the student's position in the class for the term
    position = (
        ResultSummary.objects.filter(term=term, average_score__gt=average_score)
        .count() + 1
    )

    # Update or Create the Result Summary
    summary, created = ResultSummary.objects.get_or_create(
        student=student,
        term=term,
        defaults={
            'total_score': total_score,
            'average_score': average_score,
            'grade': grade,
            'position': position,
            'attendance': attendance, 
            'days_in_term': days_in_term if days_in_term else 0,
            'resumption_date': resumption_date
        }
    )

    if not created:
        summary.total_score = total_score
        summary.average_score = average_score
        summary.grade = grade
        summary.position = position
        summary.attendance = attendance
        summary.save()

    context = {
        'student': student,
        'session': session,
        'term': term,
        'results': results,
        'summary': summary,
        'no_in_class': no_in_class,
        'attendance': summary.attendance if summary.attendance is not None else 0,  # ✅ Default to 0
        'days_in_term': summary.days_in_term if summary.days_in_term is not None else 0,  # ✅ Default to 0
        'resumption_date': summary.resumption_date if summary.resumption_date else "N/A",
        'page_title': "Filtered Student Result",
    }

    return render(request, 'staff_template/staff_result_detail_filtered.html', context)

# def staff_view_result_filtered(request):
#     # Get parameters from request
#     student_id = request.GET.get('student')
#     session_id = request.GET.get('session')
#     term_id = request.GET.get('term')

#     if not (student_id and session_id and term_id):
#         messages.error(request, "Please select a student, session, and term.")
#         return redirect('staff_student_list')

#     # Get relevant objects
#     student = get_object_or_404(Student, id=student_id)
#     session = get_object_or_404(Session, id=session_id)
#     term = get_object_or_404(Term, id=term_id, session=session)

#     # Get number of students in the same class/program
#     no_in_class = Student.objects.filter(program=student.program).count()

#     # Get term details with safe defaults
#     resumption_date = getattr(term, 'resumption_date', "N/A")
#     days_in_term = getattr(term, 'days_in_term', 0)

#     # ✅ Get student's attendance in this session & term
#     attendance = Attendance.objects.filter(
#         student=student, session=session, term=term, is_present=True
#     ).count()

#     # ✅ Get all results for this student in this term
#     results = Result.objects.filter(student=student, term=term)
    
#     # ✅ Defensive check to avoid sum() errors
#     total_score = sum(result.total_score or 0 for result in results)
    
#     # ✅ Calculate Final Average Score
#     num_subjects = results.count()
#     average_score = total_score / num_subjects if num_subjects > 0 else 0

#     # ✅ Assign Grade Based on Average
#     if average_score >= 90:
#         grade = 'A+'
#     elif average_score >= 80:
#         grade = 'A'
#     elif average_score >= 70:
#         grade = 'B'
#     elif average_score >= 60:
#         grade = 'C'
#     elif average_score >= 50:
#         grade = 'D'
#     else:
#         grade = 'F'

#     # ✅ Get the student's position based on average score
#     position = (
#         ResultSummary.objects.filter(term=term, average_score__gt=average_score)
#         .count() + 1
#     )

#     # ✅ Update or Create the Result Summary
#     summary, created = ResultSummary.objects.update_or_create(
#         student=student,
#         term=term,
#         defaults={
#             'total_score': total_score,
#             'average_score': average_score,
#             'grade': grade,
#             'position': position,
#             'attendance': attendance,
#             'days_in_term': days_in_term,
#             'resumption_date': resumption_date,
#         }
#     )

#     # ✅ Prepare Context for Template
#     context = {
#         'student': student,
#         'session': session,
#         'term': term,
#         'results': results,
#         'summary': summary,
#         'no_in_class': no_in_class,
#         'attendance': summary.attendance or 0,
#         'days_in_term': summary.days_in_term or 0,
#         'resumption_date': summary.resumption_date or "N/A",
#         'page_title': "Filtered Student Result",
#     }

#     return render(request, 'staff_template/staff_result_detail_filtered.html', context)
# def staff_view_result_filtered(request):
#     # Get parameters from request
#     student_id = request.GET.get('student')
#     session_id = request.GET.get('session')
#     term_id = request.GET.get('term')

#     if not (student_id and session_id and term_id):
#         messages.error(request, "Please select a student, session, and term.")
#         return redirect('staff_student_list')

#     # Get relevant objects
#     student = get_object_or_404(Student, id=student_id)
#     session = get_object_or_404(Session, id=session_id)
#     term = get_object_or_404(Term, id=term_id, session=session)

#     # Get number of students in the same class/program
#     no_in_class = Student.objects.filter(program=student.program).count()

#     # Get term details with None as fallback
#     resumption_date = getattr(term, 'resumption_date', None)
#     days_in_term = getattr(term, 'days_in_term', 0)

#     # ✅ Get student's attendance in this session & term
#     attendance = Attendance.objects.filter(
#         student=student, session=session, term=term, is_present=True
#     ).count()

#     # ✅ Get all results for this student in this term
#     results = Result.objects.filter(student=student, term=term)
    
#     # ✅ Defensive check to avoid sum() errors
#     total_score = sum(result.total_score or 0 for result in results)
    
#     # ✅ Calculate Final Average Score
#     num_subjects = results.count()
#     average_score = total_score / num_subjects if num_subjects > 0 else 0

#     # ✅ Assign Grade Based on Average
#     if average_score >= 90:
#         grade = 'A+'
#     elif average_score >= 80:
#         grade = 'A'
#     elif average_score >= 70:
#         grade = 'B'
#     elif average_score >= 60:
#         grade = 'C'
#     elif average_score >= 50:
#         grade = 'D'
#     else:
#         grade = 'F'

#     # ✅ Get the student's position based on average score
#     position = (
#         ResultSummary.objects.filter(term=term, average_score__gt=average_score)
#         .count() + 1
#     )

#     # ✅ Update or Create the Result Summary
#     summary, created = ResultSummary.objects.update_or_create(
#         student=student,
#         term=term,
#         defaults={
#             'total_score': total_score,
#             'average_score': average_score,
#             'grade': grade,
#             'position': position,
#             'attendance': attendance,
#             'days_in_term': days_in_term,
#             'resumption_date': resumption_date,
#         }
#     )

#     # ✅ Prepare Context for Template
#     context = {
#         'student': student,
#         'session': session,
#         'term': term,
#         'results': results,
#         'summary': summary,
#         'no_in_class': no_in_class,
#         'attendance': summary.attendance or 0,
#         'days_in_term': summary.days_in_term or 0,
#         'resumption_date': summary.resumption_date,
#         'page_title': "Filtered Student Result",
#     }

#     return render(request, 'staff_template/staff_result_detail_filtered.html', context)






# ------------------------------
# EditResultView class-based view
# ------------------------------
class EditResultView(View):
    def get(self, request, student_id, *args, **kwargs):
        student = get_object_or_404(Student, id=student_id)
        # Initialize the form with the student pre-populated.
        form = TermResultForm(initial={'student': student})
        staff = get_object_or_404(Staff, admin=request.user)
        subjects = Subject.objects.filter(staff=staff)
        form.fields['subject'].queryset = subjects
        # Build a dictionary (results_dict) for pre-populating result fields.
        results_dict = {}
        for subject in subjects:
            try:
                result = Result.objects.get(student=student, subject=subject)
                results_dict[subject.id] = {
                    'ca_test1': result.ca_test1,
                    'ca_test2': result.ca_test2,
                    'exam_score': result.exam_score,
                    'total_score': result.total_score,
                }
            except Result.DoesNotExist:
                results_dict[subject.id] = {
                    'ca_test1': 0,
                    'ca_test2': 0,
                    'exam_score': 0,
                    'total_score': 0,
                }
        context = {
            'form': form,
            'page_title': "Edit Student's Result",
            'student': student,
            'results_dict': results_dict,
            'subjects': subjects,
        }
        return render(request, "staff_template/edit_student_result.html", context)

    def post(self, request, student_id, *args, **kwargs):
        form = TermResultForm(request.POST)
        if form.is_valid():
            try:
                student = form.cleaned_data.get('student')
                subject = form.cleaned_data.get('subject')
                term = form.cleaned_data.get('term')
                ca_test1 = form.cleaned_data.get('ca_test1')
                ca_test2 = form.cleaned_data.get('ca_test2')
                exam_score = form.cleaned_data.get('exam_score')
                result, created = Result.objects.get_or_create(
                    student=student,
                    subject=subject,
                    term=term,
                    defaults={
                        'ca_test1': ca_test1,
                        'ca_test2': ca_test2,
                        'exam_score': exam_score,
                    }
                )
                if not created:
                    result.ca_test1 = ca_test1
                    result.ca_test2 = ca_test2
                    result.exam_score = exam_score
                    result.save()
                messages.success(request, "Result Updated")
                return redirect(reverse('edit_student_result', kwargs={'student_id': student.id}))
            except Exception as e:
                messages.warning(request, "Result Could Not Be Updated: " + str(e))
        else:
            messages.warning(request, "Result Could Not Be Updated (Form invalid)")
        # Rebuild context for re-rendering the form.
        student = get_object_or_404(Student, id=student_id)
        staff = get_object_or_404(Staff, admin=request.user)
        subjects = Subject.objects.filter(staff=staff)
        results_dict = {}
        for subject in subjects:
            try:
                result = Result.objects.get(student=student, subject=subject)
                results_dict[subject.id] = {
                    'ca_test1': result.ca_test1,
                    'ca_test2': result.ca_test2,
                    'exam_score': result.exam_score,
                    'total_score': result.total_score,
                }
            except Result.DoesNotExist:
                results_dict[subject.id] = {
                    'ca_test1': 0,
                    'ca_test2': 0,
                    'exam_score': 0,
                    'total_score': 0,
                }
        context = {
            'form': form,
            'page_title': "Edit Student's Result",
            'student': student,
            'results_dict': results_dict,
            'subjects': subjects,
        }
        return render(request, "staff_template/edit_student_result.html", context)

def compile_session_results(request, student_id, session_id):
    student = get_object_or_404(Student, id=student_id)
    session = get_object_or_404(Session, id=session_id)
    # Get all terms for this session.
    terms = session.terms.all()
    subjects = Subject.objects.filter(program=student.program)
    compiled = {}
    for subject in subjects:
        subject_total = Decimal('0.00')
        for term in terms:
            try:
                result = Result.objects.get(student=student, subject=subject, term=term)
                subject_total += result.total_score
            except Result.DoesNotExist:
                pass
        compiled[subject.name] = subject_total
    context = {
        'student': student,
        'session': session,
        'compiled_results': compiled,
        'page_title': "Compiled Session Results",
    }
    return render(request, "staff_template/compiled_session_results.html", context)

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
        position = 1  # For now, position is set to 1; adjust logic as needed.
        return total_score, average_score, position, grade
    else:
        return 0, 0, 0, 'F'

# ////////////////////////////////////////////////////////////
def staff_result_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    results = Result.objects.filter(student=student)

    # Calculate total and average score
    total_score = sum(result.total_score or 0 for result in results)
    num_subjects = results.count()
    average_score = total_score / num_subjects if num_subjects > 0 else 0
 
    # Get the latest term
    latest_term = Term.objects.filter(
        session__student=student
    ).order_by('-session__start_year').first()

    if not latest_term:
        messages.error(request, "No term found for this student!")
        return redirect('staff_student_list')

    # Only get summaries for the same session and term
    summaries = ResultSummary.objects.filter(
        student__program=student.program,
        term=latest_term
    ).order_by('-average_score', 'student__admin__first_name')  # Sort by score, then by name

    # Determine Position Based on Average Score
    ranked_students = list(summaries)
    position = 1  # Default position if no other students

    for index, summary in enumerate(ranked_students):
        if summary.student == student:
            position = index + 1  # Positions start from 1
            break

    # Determine Grade
    grade = 'F'
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

    # ✅ Create or Update the ResultSummary
    summary, created = ResultSummary.objects.get_or_create(
        student=student,
        term=latest_term,
        defaults={
            'total_score': total_score,
            'average_score': average_score,
            'position': position,
            'grade': grade,
            'teacher_remarks': ''
        }
    )

    # Update summary if already exists
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
        bottom: 50mm;
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

@csrf_exempt
def get_terms(request):
    """Fetch terms only for the selected session."""
    session_id = request.POST.get('session')  # Get session ID from AJAX request
    if session_id:
        terms = Term.objects.filter(session_id=session_id)  # Filter terms by session
        data = [{'id': term.id, 'name': term.name} for term in terms]
        return JsonResponse(data, safe=False)
    
    return JsonResponse([], safe=False)  # Return empty list if no session selected




# def staff_student_attendance(request):
#     """
#     Display the student attendance page with session and term selection.
#     Only students in the staff's program are shown.
#     """
#     # Get the current staff user
#     staff = get_object_or_404(Staff, admin=request.user)
#     # Filter students by the staff's program
#     students = Student.objects.filter(program=staff.program)
    
#     sessions = Session.objects.all()
#     terms = Term.objects.all()
    
#     # Get the selected session and term from the GET parameters
#     selected_session_id = request.GET.get("session")
#     selected_term_id = request.GET.get("term")
    
#     if selected_session_id and selected_term_id:
#         selected_session = get_object_or_404(Session, id=selected_session_id)
#         selected_term = get_object_or_404(Term, id=selected_term_id, session=selected_session)
#         # Get attendance records for the selected session and term.
#         attendance_data = Attendance.objects.filter(session=selected_session, term=selected_term)
#     else:
#         attendance_data = None

#     context = {
#         "students": students,
#         "sessions": sessions,
#         "terms": terms,
#         "attendance_data": attendance_data,
#         "selected_session_id": selected_session_id,
#         "selected_term_id": selected_term_id
#     }
#     return render(request, "staff_template/staff_student_attendance.html", context)

# @csrf_exempt
# def bulk_mark_attendance(request):
#     """
#     AJAX view to mark attendance for a given student, session, and term.
#     """
#     from django.utils import timezone
#     if request.method == "POST":
#         student_id = request.POST.get("student_id")
#         session_id = request.POST.get("session_id")
#         term_id = request.POST.get("term_id")
#         is_present = request.POST.get("is_present") == "true"  # convert string to boolean

#         student = get_object_or_404(Student, id=student_id)
#         session = get_object_or_404(Session, id=session_id)
#         term = get_object_or_404(Term, id=term_id, session=session)

#         # Create or update the attendance record for today
#         attendance, created = Attendance.objects.get_or_create(
#             student=student,
#             session=session,
#             term=term,
#             date=timezone.now().date()
#         )
#         attendance.is_present = is_present
#         attendance.save()

#         # Count total days the student was present in this session & term
#         total_attendance = Attendance.objects.filter(
#             student=student, session=session, term=term, is_present=True
#         ).count()

#         return JsonResponse({"success": True, "attendance_count": total_attendance})
    
#     return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

# staff_views.py
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Student, Session, Term, Attendance, Staff

def staff_student_attendance(request):
    """
    Display the student attendance page.
    Staff can select a session and term to load students in their program.
    """
    # Get current staff profile
    staff = get_object_or_404(Staff, admin=request.user)
    # Only students in the staff’s program
    students = Student.objects.filter(program=staff.program)
    sessions = Session.objects.all()
    terms = Term.objects.all()

    selected_session_id = request.GET.get("session")
    selected_term_id = request.GET.get("term")

    if selected_session_id and selected_term_id:
        selected_session = get_object_or_404(Session, id=selected_session_id)
        selected_term = get_object_or_404(Term, id=selected_term_id, session=selected_session)
        # Filter attendance records for the selected session and term
        attendance_data = Attendance.objects.filter(
            session=selected_session,
            term=selected_term
        )
    else:
        attendance_data = None

    context = {
        "students": students,
        "sessions": sessions,
        "terms": terms,
        "attendance_data": attendance_data,
        "selected_session_id": selected_session_id,
        "selected_term_id": selected_term_id,
        "page_title": "Student Attendance"
    }
    return render(request, "staff_template/staff_student_attendance.html", context)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Student, Session, Term, Attendance

@csrf_exempt
def bulk_mark_attendance(request):
    """
    Mark attendance for multiple students via AJAX.
    """
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        session_id = request.POST.get("session_id")
        term_id = request.POST.get("term_id")
        is_present = request.POST.get("is_present") == "true"

        print("Received Data:", student_id, session_id, term_id, is_present)  # Debugging

        if not (student_id and session_id and term_id):
            return JsonResponse({"success": False, "error": "Missing required data"}, status=400)

        student = get_object_or_404(Student, id=student_id)
        session = get_object_or_404(Session, id=session_id)
        term = get_object_or_404(Term, id=term_id, session=session)

        attendance, created = Attendance.objects.get_or_create(
            student=student,
            session=session,
            term=term,
            date=timezone.now().date()
        )
        attendance.is_present = is_present
        attendance.save()

        total_attendance = Attendance.objects.filter(
            student=student, session=session, term=term, is_present=True
        ).count()

        return JsonResponse({"success": True, "attendance_count": total_attendance})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

# @csrf_exempt
# def bulk_mark_attendance(request):
#     """
#     Mark attendance for a single student via AJAX.
#     Expects POST data: student_id, session_id, term_id, and is_present.
#     """
#     if request.method == "POST":
#         student_id = request.POST.get("student_id")
#         session_id = request.POST.get("session_id")
#         term_id = request.POST.get("term_id")
#         # Convert "true"/"false" string to boolean:
#         is_present = request.POST.get("is_present") == "true"

#         student = get_object_or_404(Student, id=student_id)
#         session = get_object_or_404(Session, id=session_id)
#         term = get_object_or_404(Term, id=term_id, session=session)

#         # Create or update today's attendance record for this student, session and term.
#         attendance, created = Attendance.objects.get_or_create(
#             student=student,
#             session=session,
#             term=term,
#             date=timezone.now().date()
#         )
#         attendance.is_present = is_present
#         attendance.save()

#         # Count the total number of days this student was present in this session and term.
#         total_attendance = Attendance.objects.filter(
#             student=student, session=session, term=term, is_present=True
#         ).count()

#         return JsonResponse({"success": True, "attendance_count": total_attendance})

#     return JsonResponse({"success": False, "error": "Invalid request"}, status=400)



# @csrf_exempt
# def mark_attendance(request):
#     """Mark student attendance for the selected session and term."""
#     if request.method == "POST":
#         student_id = request.POST.get("student_id")
#         session_id = request.POST.get("session_id")
#         term_id = request.POST.get("term_id")
#         is_present = request.POST.get("is_present") == "true"

#         student = get_object_or_404(Student, id=student_id)
#         session = get_object_or_404(Session, id=session_id)
#         term = get_object_or_404(Term, id=term_id, session=session)

#         # We assume one attendance record per student per day per session/term.
#         today = timezone.now().date()
#         attendance, created = Attendance.objects.get_or_create(
#             student=student,
#             session=session,
#             term=term,
#             date=today,
#             defaults={'is_present': is_present}
#         )
#         if not created:
#             attendance.is_present = is_present
#             attendance.save()

#         # Count total present for the student for today
#         attendance_count = Attendance.objects.filter(
#             student=student,
#             session=session,
#             term=term,
#             date=today,
#             is_present=True
#         ).count()

#         return JsonResponse({"success": True, "attendance_count": attendance_count})

#     return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

# @csrf_exempt
# def mark_attendance(request):
#     """Mark student attendance for a selected session and term."""
#     if request.method == "POST":
#         student_id = request.POST.get("student_id")
#         session_id = request.POST.get("session_id")
#         term_id = request.POST.get("term_id")
#         is_present = request.POST.get("is_present") == "true"

#         # Debugging: Log received data
#         print(f"📌 Received: Student ID: {student_id}, Session ID: {session_id}, Term ID: {term_id}, Present: {is_present}")

#         # Check for missing data
#         if not student_id or not session_id or not term_id:
#             return JsonResponse({"success": False, "error": "Missing required data"}, status=400)

#         # Fetch student and check if they exist
#         try:
#             student = Student.objects.get(id=student_id)
#         except Student.DoesNotExist:
#             return JsonResponse({"success": False, "error": "Student not found"}, status=404)

#         session = get_object_or_404(Session, id=session_id)
#         term = get_object_or_404(Term, id=term_id, session=session)

#         # Create or update attendance
#         attendance, created = Attendance.objects.get_or_create(
#             student=student,
#             session=session,
#             term=term,
#             date=timezone.now()
#         )
#         attendance.is_present = is_present
#         attendance.save()

#         # Count total attendance records for the student in this session and term
#         total_attendance = Attendance.objects.filter(
#             student=student, session=session, term=term, is_present=True
#         ).count()

#         return JsonResponse({"success": True, "attendance_count": total_attendance})

#     return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

# @csrf_exempt
# def mark_attendance(request):
#     """Mark student attendance for a selected session and term."""
#     if request.method == "POST":
#         student_id = request.POST.get("student_id")
#         session_id = request.POST.get("session_id")
#         term_id = request.POST.get("term_id")
#         is_present = request.POST.get("is_present") == "true"

#         # 🚨 Debugging: Log received data
#         print(f"📌 Received Data - Student ID: {student_id}, Session ID: {session_id}, Term ID: {term_id}, Present: {is_present}")

#         # Check if required data is missing
#         if not student_id or not session_id or not term_id:
#             print("❌ Error: Missing required data")
#             return JsonResponse({"success": False, "error": "Missing required data"}, status=400)

#         try:
#             student = Student.objects.get(id=student_id)
#         except Student.DoesNotExist:
#             print("❌ Error: Student not found")
#             return JsonResponse({"success": False, "error": "Student not found"}, status=404)

#         session = get_object_or_404(Session, id=session_id)
#         term = get_object_or_404(Term, id=term_id, session=session)

#         # Create or update attendance
#         attendance, created = Attendance.objects.get_or_create(
#             student=student,
#             session=session,
#             term=term,
#             date=timezone.now()
#         )
#         attendance.is_present = is_present
#         attendance.save()

#         # Count total attendance records for the student in this session and term
#         total_attendance = Attendance.objects.filter(
#             student=student, session=session, term=term, is_present=True
#         ).count()

#         print(f"✅ Attendance marked successfully for {student.admin.first_name}. Total Days Present: {total_attendance}")
#         return JsonResponse({"success": True, "attendance_count": total_attendance})

#     print("❌ Error: Invalid request method")
#     return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@csrf_exempt
def mark_attendance(request):
    """Mark student attendance as Present or Absent."""
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        session_id = request.POST.get("session_id")
        term_id = request.POST.get("term_id")
        status = request.POST.get("status")  # "present" or "absent"

        # 🚨 Debugging: Log received data
        print(f"📌 Received Data - Student ID: {student_id}, Session ID: {session_id}, Term ID: {term_id}, Status: {status}")

        # Check if required data is missing
        if not student_id or not session_id or not term_id or not status:
            return JsonResponse({"success": False, "error": "Missing required data"}, status=400)

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return JsonResponse({"success": False, "error": "Student not found"}, status=404)

        session = get_object_or_404(Session, id=session_id)
        term = get_object_or_404(Term, id=term_id, session=session)

        # Retrieve or create attendance record
        attendance, created = Attendance.objects.get_or_create(
            student=student,
            session=session,
            term=term,
            date=timezone.now()
        )

        # Update attendance based on the checkbox clicked
        if status == "present":
            attendance.is_present = True
            attendance.is_absent = False  # Reset Absent if Present is checked
        elif status == "absent":
            attendance.is_absent = True
            attendance.is_present = False  # Reset Present if Absent is checked

        attendance.save()

        # Count total Present and Absent records
        total_present = Attendance.objects.filter(
            student=student, session=session, term=term, is_present=True
        ).count()

        total_absent = Attendance.objects.filter(
            student=student, session=session, term=term, is_absent=True
        ).count()

        return JsonResponse({"success": True, "present_count": total_present, "absent_count": total_absent})

    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

