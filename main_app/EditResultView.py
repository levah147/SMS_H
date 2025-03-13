import logging
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.views import View
from django.contrib import messages

from .models import Subject, Staff, Student, Result
from .forms import EditResultForm

# Set up logging (ensure your logging configuration is set in settings.py)
logger = logging.getLogger(__name__)

class EditResultView(View):
    def get(self, request, student_id, *args, **kwargs):
        # Retrieve the student using student_id from the URL.
        student = get_object_or_404(Student, id=student_id)
        # Initialize the form with the student field pre-set.
        form = EditResultForm(initial={'student': student})
        # Retrieve the logged-in staff.
        staff = get_object_or_404(Staff, admin=request.user)
        # Limit subject choices to those assigned to this staff.
        subjects = Subject.objects.filter(staff=staff)
        form.fields['subject'].queryset = subjects

        # Build results_dict for each subject.
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
        form = EditResultForm(request.POST)
        if form.is_valid():
            try:
                # Log the cleaned data for debugging.
                logger.debug("Cleaned Data: %s", form.cleaned_data)
                
                student = form.cleaned_data.get('student')
                subject = form.cleaned_data.get('subject')
                ca_test1 = form.cleaned_data.get('ca_test1')
                ca_test2 = form.cleaned_data.get('ca_test2')
                exam_score = form.cleaned_data.get('exam_score')
                
                # Use get_or_create so that if a Result record does not exist, it is created.
                result, created = Result.objects.get_or_create(
                    student=student,
                    subject=subject,
                    defaults={
                        'ca_test1': ca_test1,
                        'ca_test2': ca_test2,
                        'exam_score': exam_score
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
                logger.exception("Error updating result")
                messages.warning(request, "Result Could Not Be Updated: " + str(e))
        else:
            # Log form errors for debugging.
            logger.debug("EditResultForm errors: %s", form.errors)
            messages.warning(request, "Result Could Not Be Updated (Form invalid)")
        
        # Rebuild context in case of error.
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
