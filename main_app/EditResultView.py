from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from django.urls import reverse

from .models import Subject, Staff, Student, Result
from .forms import EditResultForm

class EditResultView(View):
    def get(self, request, *args, **kwargs):
        form = EditResultForm()
        student = get_object_or_404(Student, id=self.kwargs['student_id'])
        form = EditResultForm(initial={'student': student})
        staff = get_object_or_404(Staff, admin=request.user)
        staff = get_object_or_404(Staff, admin=request.user)
        # Limit subjects to those assigned to this staff member.
        form.fields['subject'].queryset = Subject.objects.filter(staff=staff)
        context = {
            'form': form,
            'page_title': "Edit Student's Result",
            'student': student,  # Ensure this is passed!
        }
        return render(request, "staff_template/edit_student_result.html", context)





    def post(self, request, *args, **kwargs):
        form = EditResultForm(request.POST)
        context = {'form': form, 'page_title': "Edit Student's Result"}
        if form.is_valid():
            try:
                # Retrieve the student and subject from the form.
                student = form.cleaned_data.get('student')
                subject = form.cleaned_data.get('subject')
                ca_test1 = form.cleaned_data.get('ca_test1')
                ca_test2 = form.cleaned_data.get('ca_test2')
                exam_score = form.cleaned_data.get('exam_score')
                
                # Retrieve the existing Result for the given student and subject.
                result = Result.objects.get(student=student, subject=subject)
                result.ca_test1 = ca_test1
                result.ca_test2 = ca_test2
                result.exam_score = exam_score
                result.save()  # The save() method will recalculate total_score.
                messages.success(request, "Result Updated")
                # Redirect using a URL name (ensure your URL configuration defines 'edit_student_result').
                return redirect(reverse('edit_student_result'))
            except Exception as e:
                messages.warning(request, "Result Could Not Be Updated: " + str(e))
        else:
            messages.warning(request, "Result Could Not Be Updated")
        return render(request, "staff_template/edit_student_result.html", context)
