import json
import math
import os
from datetime import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
# IMPORTANT: Import static so we can use it in our view.
from django.templatetags.static import static

from .forms import LeaveReportStudentForm, FeedbackStudentForm, StudentEditForm
from .models import (
    Student, Attendance, AttendanceReport, Session, NotificationStudent,
    Result, ResultSummary, Subject, Program, LeaveReportStudent, FeedbackStudent
)

def student_home(request):
    student = get_object_or_404(Student, admin=request.user)
    total_subject = Subject.objects.filter(program=student.program).count()
    total_attendance = AttendanceReport.objects.filter(student=student).count()
    total_present = AttendanceReport.objects.filter(student=student, status=True).count()
    if total_attendance == 0:
        percent_present = percent_absent = 0
    else:
        percent_present = math.floor((total_present / total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)

    subject_names = []
    data_present = []
    data_absent = []
    subjects = Subject.objects.filter(program=student.program)
    for subject in subjects:
        # attendance = Attendance.objects.filter(subject=subject)
        # present_count = AttendanceReport.objects.filter(
        #     attendance__in=attendance, status=True, student=student
        # ).count()
        # absent_count = AttendanceReport.objects.filter(
        #     attendance__in=attendance, status=False, student=student
        # ).count()
        subject_names.append(subject.name)
        # data_present.append(present_count)
        # data_absent.append(absent_count)

    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'subjects': subjects,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_names,
        'page_title': 'Student Homepage'
    }
    return render(request, 'student_template/home_content.html', context)


@csrf_exempt
def student_view_attendance(request):
    student = get_object_or_404(Student, admin=request.user)
    if request.method != 'POST':
        course = get_object_or_404(Program, id=student.program.id)
        context = {
            'subjects': Subject.objects.filter(program=course),
            'page_title': 'View Attendance'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    else:
        subject_id = request.POST.get('subject')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), subject=subject
            )
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, student=student
            )
            json_data = []
            for report in attendance_reports:
                data = {
                    "date": str(report.attendance.date),
                    "status": report.status
                }
                json_data.append(data)
            return JsonResponse(json_data, safe=False)
        except Exception as e:
            return HttpResponse("Error: " + str(e))


def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit leave application")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_apply_leave.html", context)


def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Student Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not submit feedback!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    form = StudentEditForm(request.POST or None, request.FILES or None, instance=student)
    context = {'form': form, 'page_title': 'View/Edit Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = student.admin
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
                student.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occurred While Updating Profile: " + str(e))
    return render(request, "student_template/student_view_profile.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_obj = get_object_or_404(Student, admin=request.user)
    try:
        student_obj.admin.fcm_token = token
        student_obj.admin.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    # Mark all notifications as read:
    notifications.update(is_read=True)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


from django.contrib.auth.decorators import login_required

@login_required
def ajax_student_notifications(request):
    student = request.user.student  # Assumes a reverse relation exists.
    # Only fetch notifications that are not read.
    notifications = NotificationStudent.objects.filter(student=student, is_read=False)
    data = [{'id': n.id, 'message': n.message} for n in notifications]
    return JsonResponse(data, safe=False)

# @csrf_exempt
# def ajax_get_notifications_student(request):
#     student = get_object_or_404(Student, admin=request.user)
#     # (Optionally, filter by unread notifications if you add an "is_read" field.)
#     notifications = NotificationStudent.objects.filter(student=student)
#     data = [{'id': n.id, 'message': n.message} for n in notifications]
#     return JsonResponse(data, safe=False)

# @csrf_exempt
# def ajax_mark_notifications_read_student(request):
#     student = get_object_or_404(Student, admin=request.user)
#     # If you add an "is_read" field to NotificationStudent:
#     notifications = NotificationStudent.objects.filter(student=student, is_read=False)
#     notifications.update(is_read=True)
#     return JsonResponse({'status': 'success'})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import NotificationStudent

@csrf_exempt
def ajax_get_notifications_student(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student, is_read=False)
    data = {
        'notifications': [{'id': n.id, 'message': n.message, 'type': 'Student'} for n in notifications],
        'unread_count': notifications.count()
    }
    return JsonResponse(data, safe=False)

@csrf_exempt
def ajax_mark_notifications_read_student(request):
    student = get_object_or_404(Student, admin=request.user)
    NotificationStudent.objects.filter(student=student, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})



def student_view_result(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    results = Result.objects.filter(student=student)
    try:
        summary = ResultSummary.objects.get(student=student)
    except ResultSummary.DoesNotExist:
        summary = None
    context = {
        'student': student,
        'results': results,
        'summary': summary,
        'page_title': "Student Result Detail",
    }
    return render(request, "student_template/student_view_result.html", context)




from weasyprint import HTML, CSS
from django.template.loader import get_template

def student_result_pdf(request):
    student = get_object_or_404(Student, admin=request.user)
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
    
    # Compute absolute URL for the profile image.
    if student.admin.profile_pic:
        profile_pic_absolute = request.build_absolute_uri(student.admin.profile_pic.url)
    else:
        profile_pic_absolute = request.build_absolute_uri(static('dist/img/avatar5.png'))
    
    context = {
        'student': student,
        'results': results,
        'summary': summary,
        'page_title': "My Result Detail",
        'profile_pic_absolute': profile_pic_absolute,
        'request': request,  # ensure static tag resolves correctly
    }
    
    template = get_template("student_template/student_view_result_pdf.html")
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



from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.contrib import messages
from .models import Student, Result, Session, Term
from decimal import Decimal

def student_result_detail_filtered(request):
    # Retrieve the logged‑in student.
    student = get_object_or_404(Student, admin=request.user)
    
    # Get session and term IDs from GET parameters.
    session_id = request.GET.get('session')
    term_id = request.GET.get('term')
    
    if not (session_id and term_id):
        messages.error(request, "Please select both an academic session and a term.")
        return redirect(reverse('student_results_list'))
    
    # Retrieve the session and term objects.
    session = get_object_or_404(Session, id=session_id)
    term = get_object_or_404(Term, id=term_id, session=session)
    
    # Retrieve results for the student filtered by the selected term.
    results = Result.objects.filter(student=student, term=term)
    
    # Compute summary: total score, average score, and grade.
    total_score = sum(result.total_score for result in results)
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
    
    # Build a summary dictionary.
    summary = {
        'total_score': total_score,
        'average_score': round(average_score, 2),
        'grade': grade,
        'teacher_remarks': '',  # Adjust if you store remarks elsewhere.
    }
    
    context = {
        'student': student,
        'results': results,
        'summary': summary,
        'session': session,
        'term': term,
        'page_title': "Filtered Result Detail",
    }
    return render(request, "student_template/student_result_detail_filtered.html", context)

# def student_results_list(request):
#     student = get_object_or_404(Student, admin=request.user)
#     sessions = Session.objects.all()
#     terms = Term.objects.all()
    
#     # Read selected session and term from GET parameters.
#     selected_session_id = request.GET.get('session', '')
#     selected_term_id = request.GET.get('term', '')
    
#     results = None
#     if selected_session_id and selected_term_id:
#         session = get_object_or_404(Session, id=selected_session_id)
#         term = get_object_or_404(Term, id=selected_term_id, session=session)
#         results = Result.objects.filter(student=student, term=term)
    
#     context = {
#         'student': student,
#         'sessions': sessions,
#         'terms': terms,
#         'selected_session_id': selected_session_id,
#         'selected_term_id': selected_term_id,
#         'results': results,
#         'page_title': 'My Results',
#     }
#     return render(request, "student_template/student_results_list.html", context)
def student_results_list(request):
    student = get_object_or_404(Student, admin=request.user)
    sessions = Session.objects.all()
    terms = Term.objects.all()
    
    # Read selected session and term from GET parameters.
    selected_session_id = request.GET.get('session', '')
    selected_term_id = request.GET.get('term', '')
    
    results = None
    if selected_session_id and selected_term_id:
        session = get_object_or_404(Session, id=selected_session_id)
        term = get_object_or_404(Term, id=selected_term_id, session=session)
        results = Result.objects.filter(student=student, term=term)
    
    context = {
        'student': student,
        'sessions': sessions,
        'terms': terms,
        'selected_session_id': selected_session_id,  # ✅ Retain selected session
        'selected_term_id': selected_term_id,  # ✅ Retain selected term
        'results': results,
        'page_title': 'My Results',
    }
    return render(request, "student_template/student_results_list.html", context)


@csrf_exempt  # Disable CSRF for testing (REMOVE in production)
def get_terms_student(request):
    """Fetch terms only for the selected session."""
    if request.method == "POST":
        session_id = request.POST.get("session")
        if session_id:
            terms = Term.objects.filter(session_id=session_id).values("id", "name")
            return JsonResponse(list(terms), safe=False)
    
    return JsonResponse([], safe=False)  # Return empty list if no session is selected




# def student_overall_result(request, session_id):
#     student = get_object_or_404(Student, admin=request.user)
#     session = get_object_or_404(Session, id=session_id)
#     terms = Term.objects.filter(session=session)
    
#     term_results = {}
#     total_score = 0
#     total_subjects = 0

#     for term in terms:
#         results = Result.objects.filter(student=student, term=term)
#         term_results[term] = results
#         for result in results:
#             total_score += result.total_score
#             total_subjects += 1

#     # Calculate average score
#     average_score = total_score / total_subjects if total_subjects > 0 else 0

#     # Determine final grade
#     if average_score >= 90:
#         final_grade = 'A+'
#     elif average_score >= 80:
#         final_grade = 'A'
#     elif average_score >= 70:
#         final_grade = 'B'
#     elif average_score >= 60:
#         final_grade = 'C'
#     elif average_score >= 50:
#         final_grade = 'D'
#     else:
#         final_grade = 'F'

#     context = {
#         'student': student,
#         'session': session,
#         'term_results': term_results,
#         'total_score': total_score,
#         'average_score': round(average_score, 2),
#         'final_grade': final_grade,
#         'page_title': f"Overall Results for {session.start_year} - {session.end_year}"
#     }

#     return render(request, 'student_template/student_overall_result.html', context)
def student_overall_result(request, session_id):
    student = get_object_or_404(Student, admin=request.user)
    session = get_object_or_404(Session, id=session_id)
    terms = Term.objects.filter(session=session)

    term_results = {}
    total_score = 0
    total_subjects = 0

    for term in terms:
        results = Result.objects.filter(student=student, term=term)
        term_summary = ResultSummary.objects.filter(student=student, term=term).first()

        # Get student's position if summary exists
        position = term_summary.position if term_summary else "N/A"

        term_results[term] = {
            "results": results,
            "total_score": sum(result.total_score for result in results),
            "average_score": round(sum(result.total_score for result in results) / results.count(), 2) if results.exists() else "N/A",
            "grade": term_summary.grade if term_summary else "N/A",
            "position": position
        }

        for result in results:
            total_score += result.total_score
            total_subjects += 1

    # Calculate overall average score
    average_score = total_score / total_subjects if total_subjects > 0 else 0

    # Determine final grade
    if average_score >= 90:
        final_grade = 'A+'
    elif average_score >= 80:
        final_grade = 'A'
    elif average_score >= 70:
        final_grade = 'B'
    elif average_score >= 60:
        final_grade = 'C'
    elif average_score >= 50:
        final_grade = 'D'
    else:
        final_grade = 'F'

    context = {
        'student': student,
        'session': session,
        'term_results': term_results,
        'total_score': total_score,
        'average_score': round(average_score, 2),
        'final_grade': final_grade,
        'page_title': f"Overall Results for {session.start_year} - {session.end_year}"
    }

    return render(request, 'student_template/student_overall_result.html', context)










# def student_overall_result_pdf(request, session_id):
#     student = get_object_or_404(Student, admin=request.user)
#     session = get_object_or_404(Session, id=session_id)
#     terms = Term.objects.filter(session=session)
    
#     term_results = {}
#     total_score = 0
#     total_subjects = 0

#     for term in terms:
#         results = Result.objects.filter(student=student, term=term)
#         term_results[term] = results
#         for result in results:
#             total_score += result.total_score
#             total_subjects += 1

#     average_score = total_score / total_subjects if total_subjects > 0 else 0

#     # Determine final grade
#     if average_score >= 90:
#         final_grade = 'A+'
#     elif average_score >= 80:
#         final_grade = 'A'
#     elif average_score >= 70:
#         final_grade = 'B'
#     elif average_score >= 60:
#         final_grade = 'C'
#     elif average_score >= 50:
#         final_grade = 'D'
#     else:
#         final_grade = 'F'

#     if student.admin.profile_pic:
#         profile_pic_absolute = request.build_absolute_uri(student.admin.profile_pic.url)
#     else:
#         profile_pic_absolute = request.build_absolute_uri(static('dist/img/avatar5.png'))

#     context = {
#         'student': student,
#         'session': session,
#         'term_results': term_results,
#         'total_score': total_score,
#         'average_score': round(average_score, 2),
#         'final_grade': final_grade,
#         'profile_pic_absolute': profile_pic_absolute,
#         'request': request
#     }

#     template = get_template("student_template/student_overall_result_pdf.html")
#     html_string = template.render(context)
#     base_url = request.build_absolute_uri('/')
#     css_string = """
#     @page { size: A4; margin: 10mm; }
#     body footer { display: none; }
#     body::after {
#         content: "Hibiscus Royal Academy";
#         position: fixed;
#         bottom: 10mm;
#         right: 10mm;
#         font-size: 40px;
#         color: rgba(0, 0, 0, 0.15);
#         transform: rotate(-45deg);
#         z-index: 9999;
#     }
#     """
#     css = CSS(string=css_string)
#     html = HTML(string=html_string, base_url=base_url)
#     pdf_file = html.write_pdf(stylesheets=[css])

#     response = HttpResponse(pdf_file, content_type='application/pdf')
#     response['Content-Disposition'] = f'inline; filename="overall_result_{session.id}.pdf"'
#     return response
# def student_overall_result_pdf(request, session_id):
#     student = get_object_or_404(Student, admin=request.user)
#     session = get_object_or_404(Session, id=session_id)

#     # Get all term summaries for this student in the session
#     overall_results = ResultSummary.objects.filter(student=student, term__session=session)

#     # Calculate final average and overall grade
#     total_score = sum(result.total_score for result in overall_results)
#     num_terms = overall_results.count()
#     final_average = total_score / num_terms if num_terms > 0 else 0

#     if final_average >= 90:
#         final_grade = 'A+'
#     elif final_average >= 80:
#         final_grade = 'A'
#     elif final_average >= 70:
#         final_grade = 'B'
#     elif final_average >= 60:
#         final_grade = 'C'
#     elif final_average >= 50:
#         final_grade = 'D'
#     else:
#         final_grade = 'F'

#     context = {
#         'student': student,
#         'session': session,
#         'overall_results': overall_results,
#         'final_average': final_average,
#         'final_grade': final_grade
#     }

#     # Render template to HTML
#     template = get_template("student_template/student_overall_result_pdf.html")
#     html_string = template.render(context)
#     base_url = request.build_absolute_uri('/')

#     # Generate PDF
#     pdf_file = HTML(string=html_string, base_url=base_url).write_pdf()

#     # Return PDF response
#     response = HttpResponse(pdf_file, content_type="application/pdf")
#     response["Content-Disposition"] = f'inline; filename="Overall_Result_{student.id}.pdf"'
#     return response



def student_overall_result_pdf(request, session_id):
    student = get_object_or_404(Student, admin=request.user)
    session = get_object_or_404(Session, id=session_id)

    # Ensure all terms (1st, 2nd, 3rd) for the session are retrieved
    terms = Term.objects.filter(session=session).order_by('name')
    overall_results = ResultSummary.objects.filter(student=student, term__in=terms).order_by('term__name')

    # Ensure we display all terms even if a result summary is missing
    term_results = {term.name: None for term in terms}  # Create a dictionary for all terms
    for summary in overall_results:
        term_results[summary.term.name] = summary  # Assign results to respective terms

    # Calculate final average and overall grade
    total_score = sum(result.total_score for result in overall_results if result)
    num_terms = sum(1 for result in overall_results if result)  # Count terms with results
    final_average = total_score / num_terms if num_terms > 0 else 0

    # Determine final grade
    if final_average >= 90:
        final_grade = 'A+'
    elif final_average >= 80:
        final_grade = 'A'
    elif final_average >= 70:
        final_grade = 'B'
    elif final_average >= 60:
        final_grade = 'C'
    elif final_average >= 50:
        final_grade = 'D'
    else:
        final_grade = 'F'

    context = {
        'student': student,
        'session': session,
        'terms': terms,
        'term_results': term_results,
        'final_average': final_average,
        'final_grade': final_grade,
    }

    # Render template to HTML
    template = get_template("student_template/student_overall_result_pdf.html")
    html_string = template.render(context)
    base_url = request.build_absolute_uri('/')

    # Generate PDF
    pdf_file = HTML(string=html_string, base_url=base_url).write_pdf()

    # Return PDF response
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="Overall_Result_{student.id}.pdf"'
    return response

# from django.shortcuts import get_object_or_404, render
# from .models import Student, Term, ResultSummary, Session

# def student_overall_result_pdf(request, student_id):
#     student = get_object_or_404(Student, id=student_id)
#     sessions = Session.objects.all()
    
#     # Get all terms of this student’s session
#     terms = Term.objects.filter(session__in=sessions)
    
#     # Fetch ResultSummary for each term
#     term_results = {
#         term.name: ResultSummary.objects.filter(student=student, term=term).first()
#         for term in terms
#     }

#     print("DEBUG: Term Results:", term_results)  # Debugging step

#     context = {
#         'student': student,
#         'sessions': sessions,
#         'terms': terms,
#         'term_results': term_results,
#         'page_title': "Student Overall Result PDF"
#     }
    
#     return render(request, "student_template/student_overall_result_pdf.html", context)


# from django.shortcuts import get_object_or_404, render
# from .models import Student, Term, ResultSummary, Session

# def student_overall_result_pdf(request, student_id, session_id):
#     student = get_object_or_404(Student, id=student_id)
#     session = get_object_or_404(Session, id=session_id)
    
#     # Get all terms within the session
#     terms = Term.objects.filter(session=session)

#     # Fetch ResultSummary for each term
#     term_results = {
#         term.name: ResultSummary.objects.filter(student=student, term=term).first()
#         for term in terms
#     }

#     print("DEBUG: Term Results:", term_results)  # Debugging step

#     context = {
#         'student': student,
#         'session': session,
#         'terms': terms,
#         'term_results': term_results,
#         'page_title': "Student Overall Result PDF"
#     }
    
#     return render(request, "student_template/student_overall_result_pdf.html", context)
