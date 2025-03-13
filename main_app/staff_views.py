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

from .forms import *  # Ensure your forms include TermResultForm (with a 'term' field)
from .models import *  # This imports CustomUser, Staff, Student, Program, Subject, Attendance, AttendanceReport, LeaveReportStaff, FeedbackStaff, NotificationStaff, Result, ResultSummary, Term, etc.

# ------------------------------
# Dashboard and General Views
# ------------------------------

def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    total_students = Student.objects.filter(program=staff.program).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    subjects = Subject.objects.filter(staff=staff)
    total_subject = subjects.count()
    
    # Build attendance data for each subject.
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name)
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


# @csrf_exempt
# def ajax_get_notifications(request):
#     # Example for staff notifications; adjust for student if needed.
#     staff = get_object_or_404(Staff, admin=request.user)
#     notifications = NotificationStaff.objects.filter(staff=staff, is_read=False)
#     data = [{'id': n.id, 'message': n.message} for n in notifications]
#     return JsonResponse(data, safe=False)

# @csrf_exempt
# def ajax_mark_notifications_read(request):
#     staff = get_object_or_404(Staff, admin=request.user)
#     NotificationStaff.objects.filter(staff=staff, is_read=False).update(is_read=True)
#     return JsonResponse({'status': 'success'})
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
                    admin.profile_pic = passport_url
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

# @csrf_exempt
# def staff_add_result(request):
#     staff = get_object_or_404(Staff, admin=request.user)
#     subjects = Subject.objects.filter(staff=staff)
#     # Filter students by the staff's program.
#     students = Student.objects.filter(program=staff.program)
#     # Get all academic sessions and terms.
#     sessions = Session.objects.all()
#     terms = Term.objects.all()
#     page_title = "Add Results"
    
#     context = {
#         'students': students,
#         'subjects': subjects,
#         'sessions': sessions,
#         'terms': terms,
#         'page_title': page_title,
#     }
    
#     if request.method == 'POST':
#         try:
#             student_id = request.POST.get('student')
#             session_id = request.POST.get('session')
#             term_id = request.POST.get('term')
#             if not student_id:
#                 messages.error(request, "Please select a student.")
#                 return render(request, "staff_template/staff_add_result.html", context)
#             if not session_id:
#                 messages.error(request, "Please select an academic session.")
#                 return render(request, "staff_template/staff_add_result.html", context)
#             if not term_id:
#                 messages.error(request, "Please select a term.")
#                 return render(request, "staff_template/staff_add_result.html", context)
            
#             student = get_object_or_404(Student, id=student_id)
#             session = get_object_or_404(Session, id=session_id)
#             term = get_object_or_404(Term, id=term_id)
#             # Validate that the term belongs to the selected session.
#             if term.session.id != session.id:
#                 messages.error(request, "Selected term does not belong to the chosen session.")
#                 return render(request, "staff_template/staff_add_result.html", context)
            
#             # Loop through each subject and update or create the result.
#             for subject in subjects:
#                 ca_test1 = float(request.POST.get(f'ca_test1_{subject.id}', 0))
#                 ca_test2 = float(request.POST.get(f'ca_test2_{subject.id}', 0))
#                 exam_score = float(request.POST.get(f'exam_{subject.id}', 0))
#                 Result.objects.update_or_create(
#                     student=student,
#                     subject=subject,
#                     term=term,
#                     defaults={
#                         'ca_test1': ca_test1,
#                         'ca_test2': ca_test2,
#                         'exam_score': exam_score,
#                     }
#                 )
#             teacher_remarks = request.POST.get('teacher_remarks', '')
#             summary, created = ResultSummary.objects.get_or_create(
#                 student=student,
#                 defaults={
#                     'total_score': 0,
#                     'average_score': 0,
#                     'position': 0,
#                     'grade': 'F',
#                     'teacher_remarks': teacher_remarks
#                 }
#             )
#             if not created:
#                 summary.teacher_remarks = teacher_remarks
#                 summary.save()
#             messages.success(request, "Scores saved successfully!")
#             return redirect(reverse('staff_result_detail', kwargs={'student_id': student.id}))
#         except Exception as e:
#             messages.error(request, "Error Occurred While Processing Form: " + str(e))
    
#     return render(request, "staff_template/staff_add_result.html", context)
@csrf_exempt
def staff_add_result(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff=staff)
    students = Student.objects.filter(program=staff.program)
    sessions = Session.objects.all()
    terms = Term.objects.all()
    page_title = "Add Results"

    if request.method == 'POST':
        student_id = request.POST.get('student')
        session_id = request.POST.get('session')
        term_id = request.POST.get('term')
        teacher_remarks = request.POST.get('teacher_remarks', '')

        if not student_id or not session_id or not term_id:
            messages.error(request, "Please select a student, session, and term.")
            return redirect('staff_add_result')

        student = get_object_or_404(Student, id=student_id)
        session = get_object_or_404(Session, id=session_id)
        term = get_object_or_404(Term, id=term_id, session=session)

        for subject in subjects:
            ca_test1 = float(request.POST.get(f'ca_test1_{subject.id}', 0))
            ca_test2 = float(request.POST.get(f'ca_test2_{subject.id}', 0))
            exam_score = float(request.POST.get(f'exam_{subject.id}', 0))

            Result.objects.update_or_create(
                student=student,
                subject=subject,
                term=term,
                defaults={
                    'ca_test1': ca_test1,
                    'ca_test2': ca_test2,
                    'exam_score': exam_score,
                }
            )

        summary, created = ResultSummary.objects.get_or_create(
            student=student,
            term=term,
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

        messages.success(request, "Results saved successfully!")
        return redirect(reverse('staff_result_detail', kwargs={'student_id': student.id}))

    context = {
        'students': students,
        'subjects': subjects,
        'sessions': sessions,
        'terms': terms,
        'page_title': page_title,
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

# def staff_view_result_filtered(request):
#     student_id = request.GET.get('student')
#     session_id = request.GET.get('session')
#     term_id = request.GET.get('term')
#     if not (student_id and session_id and term_id):
#         messages.error(request, "Please select a student, session, and term.")
#         return redirect('staff_student_list')
    
#     student = get_object_or_404(Student, id=student_id)
#     session = get_object_or_404(Session, id=session_id)
#     # Ensure the term belongs to the selected session.
#     term = get_object_or_404(Term, id=term_id, session=session)
    
#     # Retrieve results for this student and term.
#     results = Result.objects.filter(student=student, term=term)
#     # Compute summary for this term.
#     total_score = sum(result.total_score or 0 for result in results)
#     num_subjects = results.count()
#     average_score = total_score / num_subjects if num_subjects > 0 else 0
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
    
#     # Prepare a summary dictionary.
#     summary = {
#         'total_score': total_score,
#         'average_score': round(average_score, 2),
#         'grade': grade,
#         'teacher_remarks': '',  # You can later modify this to fetch remarks if stored.
#     }
    
#     context = {
#         'student': student,
#         'session': session,
#         'term': term,
#         'results': results,
#         'summary': summary,
#         'page_title': "Filtered Student Result",
#     }
#     return render(request, 'staff_template/staff_result_detail_filtered.html', context)
from django.db.models import Count

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

    # Fetch the student's results
    results = Result.objects.filter(student=student, term=term)

    # **No of Days in Term**: Count unique attendance records for this session & term
    total_days_in_term = Attendance.objects.filter(session=session, term=term).count()

    # **Attendance**: Count how many times the student was marked **present**
    total_attendance = AttendanceReport.objects.filter(
        student=student,
        attendance__session=session,
        attendance__term=term,
        status=True  # Only count when present
    ).count()

    # **No in Class**: Total students in the same program
    total_students_in_class = Student.objects.filter(program=student.program).count()

    # **Resumption Date**: Assuming session has a `start_date`
    resumption_date = session.start_date if hasattr(session, 'start_date') else "N/A"

    # **Compute Total Score, Average Score, and Grade**
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

    # **Position**: Rank the student based on average score
    rankings = ResultSummary.objects.filter(student__program=student.program, term=term).order_by('-average_score')
    ranked_students = list(rankings.values_list('student_id', flat=True))
    position = ranked_students.index(student.id) + 1 if student.id in ranked_students else "N/A"

    # **Ensure Teacher's Remarks is Set**
    summary, created = ResultSummary.objects.get_or_create(
        student=student,
        term=term,
        defaults={
            'total_score': total_score,
            'average_score': average_score,
            'position': position,
            'grade': grade,
            'teacher_remarks': 'No remarks yet'
        }
    )

    if not created:
        summary.total_score = total_score
        summary.average_score = average_score
        summary.position = position
        summary.grade = grade
        summary.save()

    # **Pass everything to the template**
    context = {
        'student': student,
        'session': session,
        'term': term,
        'results': results,
        'summary': summary,
        'total_days_in_term': total_days_in_term,
        'total_attendance': total_attendance,
        'total_students_in_class': total_students_in_class,
        'resumption_date': resumption_date,
        'position': position,
        'page_title': "Filtered Student Result",
    }
    return render(request, 'staff_template/staff_result_detail_filtered.html', context)


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


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def get_terms(request):
    session_id = request.POST.get('session')
    try:
        session = get_object_or_404(Session, id=session_id)
        # Retrieve terms related to the session
        terms = session.terms.all()  # Assumes you set related_name='terms' in the Term model's session field.
        terms_data = [{
            'id': term.id,
            'name': term.name  # e.g., "1st", "2nd", "3rd"
        } for term in terms]
        return JsonResponse(terms_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
