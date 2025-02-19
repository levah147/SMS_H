import json
import math
from datetime import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import (LeaveReportStudentForm, FeedbackStudentForm, StudentEditForm)
from .models import (Student, Attendance, AttendanceReport, Session, NotificationStudent,
                     Result, ResultSummary, Subject, Program, LeaveReportStudent, FeedbackStudent)


def student_home(request):
    student = get_object_or_404(Student, admin=request.user)
    # Count total subjects based on student's course (Program)
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
        attendance = Attendance.objects.filter(subject=subject)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=True, student=student
        ).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=False, student=student
        ).count()
        subject_names.append(subject.name)
        data_present.append(present_count)
        data_absent.append(absent_count)

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
            return JsonResponse(json.dumps(json_data), safe=False)
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
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
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
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)

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




def student_results_list(request):
    """
    List the logged‑in student's result details.
    Since a student should only see their own result,
    we retrieve their Student record and pass it as a one-element queryset.
    """
    # Retrieve the student object for the logged‑in user.
    student = get_object_or_404(Student, admin=request.user)
    
    # Create a queryset containing just this student.
    students = Student.objects.filter(id=student.id)
    
    context = {
        'students': students,
        'page_title': 'Results List',
    }
    return render(request, "student_template/student_results_list.html", context)




from weasyprint import HTML, CSS
from django.template.loader import get_template

def student_result_pdf(request):
    # Retrieve the logged-in student using the related CustomUser (admin)
    student = get_object_or_404(Student, admin=request.user)
    
    # Retrieve all results for the student.
    results = Result.objects.filter(student=student)
    
    # Get or create the ResultSummary for the student.
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
        'page_title': "My Result Detail",
    }
    
    # Load the PDF template (create this template as described below)
    template = get_template("student_template/student_view_result_pdf.html")
    html_string = template.render(context)
    
    # Set base_url so that static files are resolved properly.
    base_url = request.build_absolute_uri('/')
    
    # Define CSS with a watermark (stamp) and to hide any footer if desired.
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
    
    # Generate PDF with WeasyPrint.
    html = HTML(string=html_string, base_url=base_url)
    pdf_file = html.write_pdf(stylesheets=[css])
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="result_{student.id}.pdf"'
    return response
