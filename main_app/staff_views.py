import json

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template


from .forms import *
from .models import *

def staff_home(request):
    staff = get_object_or_404(Staff, admin=request.user)
    # Changed 'course' to 'program'
    total_students = Student.objects.filter(program=staff.program).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    subjects = Subject.objects.filter(staff=staff)
    total_subject = subjects.count()
    
    # Build attendance data for each subject
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
    subjects = Subject.objects.filter(staff_id=staff)
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
        students = Student.objects.filter(
            course_id=subject.course.id, session=session)
        student_data = []
        for student in students:
            data = {
                    "id": student.id,
                    "name": student.admin.last_name + " " + student.admin.first_name
                    }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e



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

        # Check if an attendance object already exists for the given date and session
        attendance, created = Attendance.objects.get_or_create(session=session, subject=subject, date=date)

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))

            # Check if an attendance report already exists for the student and the attendance object
            attendance_report, report_created = AttendanceReport.objects.get_or_create(student=student, attendance=attendance)

            # Update the status only if the attendance report was newly created
            if report_created:
                attendance_report.status = student_dict.get('status')
                attendance_report.save()

    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
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
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.admin.id,
                    "name": attendance.student.admin.last_name + " " + attendance.student.admin.first_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(
                Student, admin_id=student_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


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
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None,instance=staff)
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
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
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
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
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


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


from django.views import View


# --------------------------------
# staff_add_result view
# --------------------------------

@csrf_exempt
def staff_add_result(request):
    # Get the logged-in staff member.
    staff = get_object_or_404(Staff, admin=request.user)
    # Get subjects assigned to this staff.
    subjects = Subject.objects.filter(staff=staff)
    # Get all students in the staff's assigned program.
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
            
            # Process scores for each subject.
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
            
            # Process teacher remarks.
            teacher_remarks = request.POST.get('teacher_remarks', '')
            
            # Get or create a ResultSummary for this student.
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
                # Update the teacher_remarks if they are provided.
                summary.teacher_remarks = teacher_remarks
                summary.save()
            
            messages.success(request, "Scores saved successfully!")
            return redirect(reverse('staff_result_detail', kwargs={'student_id': student.id}))
        except Exception as e:
            messages.error(request, "Error Occurred While Processing Form: " + str(e))
    
    return render(request, "staff_template/staff_add_result.html", context)

# --------------------------------
# fetch_student_result view
# --------------------------------
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

# --------------------------------
# staff_student_list view
# --------------------------------
def staff_student_list(request):
    """
    Display a list of students assigned to the staff’s program,
    along with an indication whether results have been added.
    """
    staff = get_object_or_404(Staff, admin=request.user)
    # Filter students by the staff's program.
    students = Student.objects.filter(program=staff.program)
    
    # Annotate each student with a 'has_result' attribute.
    for student in students:
        student.has_result = ResultSummary.objects.filter(student=student).exists()
    
    context = {
        'students': students,
        'page_title': 'Student List',
    }
    return render(request, 'staff_template/staff_student_list.html', context)

# --------------------------------

# --------------------------------
# EditResultView class-based view
# --------------------------------
class EditResultView(View):
    def get(self, request, student_id, *args, **kwargs):
        student = get_object_or_404(Student, id=student_id)
        # Prepopulate the form with the selected student.
        form = EditResultForm(initial={'student': student})
        staff = get_object_or_404(Staff, admin=request.user)
        # Limit subjects to those assigned to the staff.
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
                # Retrieve the existing Result record.
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
    """
    Delete all Result records and the associated ResultSummary for the specified student.
    """
    student = get_object_or_404(Student, id=student_id)
    try:
        # Delete all Result entries for the student.
        Result.objects.filter(student=student).delete()
        # Delete the student's ResultSummary, if it exists.
        ResultSummary.objects.filter(student=student).delete()
        messages.success(request, "Results deleted successfully!")
    except Exception as e:
        messages.error(request, "Could not delete results: " + str(e))
    # Redirect back to the student list page.
    return redirect('staff_student_list')

# /////////////////////////////////////////////////////////////////////////////////////////////////////////

def compute_result_summary(student):
    """
    Compute the total score, average score, position, and grade for the given student
    based on the Result objects.
    """
    results = Result.objects.filter(student=student)
    if results.exists():
        # Sum up the total score from all subjects.
        total_score = sum(result.total_score or 0 for result in results)
        num_subjects = results.count()
        average_score = total_score / num_subjects if num_subjects > 0 else 0

        # Compute the grade based on the average score.
        # (You can adjust these thresholds as needed.)
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
        
        # For simplicity, we set the position to 1.
        # For a more complete implementation, you might calculate the position
        # relative to other students in the same program.
        position = 1
        return total_score, average_score, position, grade
    else:
        # No results found; return zeros/defaults.
        return 0, 0, 0, 'F'



def staff_result_detail(request, student_id):
    # Retrieve the student.
    student = get_object_or_404(Student, id=student_id)
    # Get all results for the student.
    results = Result.objects.filter(student=student)
    
    # Calculate the total and average scores.
    total_score = sum(result.total_score or 0 for result in results)
    num_subjects = results.count()
    average_score = total_score / num_subjects if num_subjects > 0 else 0

    # Compute the student's position based on average score.
    # Get all result summaries for students in the same program, ordered by average score descending.
    summaries = ResultSummary.objects.filter(student__program=student.program).order_by('-average_score')
    ranked_ids = list(summaries.values_list('student__id', flat=True))
    if student.id in ranked_ids:
        position = ranked_ids.index(student.id) + 1
    else:
        # If the student's summary is not in the list, default to 1 (or 0, depending on your logic)
        position = 1

    # Compute grade based on average score.
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
    
    # Get or create the ResultSummary object for the student.
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
        # Update summary if it already exists.
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
    
    # Load the PDF-specific template.
    template = get_template("staff_template/staff_result_detail_pdf.html")
    html_string = template.render(context)
    
    # Use an absolute base URL. Here, we're using the root URL of your site.
    # Ensure that your STATIC_URL is configured (e.g., '/static/').
    base_url = request.build_absolute_uri('/')  # This should point to the root of your site
    
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
