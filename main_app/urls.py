from django.urls import path
from main_app.EditResultView import EditResultView
from . import hod_views, staff_views, student_views, views



urlpatterns = [
    # General / Authentication Views
    path("", views.login_page, name='login_page'),
    path("get_attendance", views.get_attendance, name='get_attendance'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("staff/mark-attendance/", staff_views.mark_attendance, name="mark_attendance"),  # Ensure this exists
    path("staff/calculate-days-in-term/", staff_views.calculate_days_in_term, name="calculate_days_in_term"),



    # HOD Views
    path("admin/home/", hod_views.admin_home, name='admin_home'),
    path("staff/add", hod_views.add_staff, name='add_staff'),
    path("course/add", hod_views.add_course, name='add_course'),
    path("send_student_notification/", hod_views.send_student_notification, name='send_student_notification'),
    path("send_staff_notification/", hod_views.send_staff_notification, name='send_staff_notification'),
    path("add_session/", hod_views.add_session, name='add_session'),
    path("admin_notify_student", hod_views.admin_notify_student, name='admin_notify_student'),
    path("admin_notify_staff", hod_views.admin_notify_staff, name='admin_notify_staff'),
    path("admin_view_profile", hod_views.admin_view_profile, name='admin_view_profile'),
    path("check_email_availability", hod_views.check_email_availability, name="check_email_availability"),
    path("session/manage/", hod_views.manage_session, name='manage_session'),
    path("session/edit/<int:session_id>", hod_views.edit_session, name='edit_session'),
    path("student/view/feedback/", hod_views.student_feedback_message, name="student_feedback_message"),
    path("staff/view/feedback/", hod_views.staff_feedback_message, name="staff_feedback_message"),
    path("student/view/leave/", hod_views.view_student_leave, name="view_student_leave"),
    path("staff/view/leave/", hod_views.view_staff_leave, name="view_staff_leave"),
    path("attendance/view/", hod_views.admin_view_attendance, name="admin_view_attendance"),
    path("attendance/fetch/", hod_views.get_admin_attendance, name='get_admin_attendance'),
    path("student/add/", hod_views.add_student, name='add_student'),
    path("subject/add/", hod_views.add_subject, name='add_subject'),
    path("staff/manage/", hod_views.manage_staff, name='manage_staff'),
    path("student/manage/", hod_views.manage_student, name='manage_student'),
    path("course/manage/", hod_views.manage_course, name='manage_course'),
    path("subject/manage/", hod_views.manage_subject, name='manage_subject'),
    path("staff/edit/<int:staff_id>", hod_views.edit_staff, name='edit_staff'),
    path("staff/delete/<int:staff_id>", hod_views.delete_staff, name='delete_staff'),
    path("course/delete/<int:course_id>", hod_views.delete_course, name='delete_course'),
    path("subject/delete/<int:subject_id>", hod_views.delete_subject, name='delete_subject'),
    path("session/delete/<int:session_id>", hod_views.delete_session, name='delete_session'),
    path("student/delete/<int:student_id>", hod_views.delete_student, name='delete_student'),
    path("student/edit/<int:student_id>", hod_views.edit_student, name='edit_student'),
    path("course/edit/<int:course_id>", hod_views.edit_course, name='edit_course'),
    path("subject/edit/<int:subject_id>", hod_views.edit_subject, name='edit_subject'),

    # path('api/hod/notifications/', hod_views.api_fetch_hod_notifications, name='api_fetch_hod_notifications'),
    path('hod/staff-leave/', hod_views.view_staff_leave, name='view_staff_leave'),
    path('hod/student-leave/', hod_views.view_student_leave, name='view_student_leave'),
    path('hod/student-feedback/', hod_views.student_feedback_message, name='student_feedback_message'),
    path('hod/staff-feedback/', hod_views.staff_feedback_message, name='staff_feedback_message'),



    # Staff Views
    path("staff/home/", staff_views.staff_home, name='staff_home'),
    path("staff/apply/leave/", staff_views.staff_apply_leave, name='staff_apply_leave'),
    path("staff/feedback/", staff_views.staff_feedback, name='staff_feedback'),
    path("staff/view/profile/", staff_views.staff_view_profile, name='staff_view_profile'),
    path("staff/attendance/take/", staff_views.staff_take_attendance, name='staff_take_attendance'),
    path("staff/attendance/update/", staff_views.staff_update_attendance, name='staff_update_attendance'),
    path("staff/get_students/", staff_views.get_students, name='get_students'),
    path("staff/attendance/fetch/", staff_views.get_student_attendance, name='get_student_attendance'),
    path("staff/attendance/save/", staff_views.save_attendance, name='save_attendance'),
    path("staff/attendance/update/", staff_views.update_attendance, name='update_attendance'),
    path("staff/fcmtoken/", staff_views.staff_fcmtoken, name='staff_fcmtoken'),
    path("staff/view/notification/", staff_views.staff_view_notification, name="staff_view_notification"),
    path("staff/result/add/", staff_views.staff_add_result, name='staff_add_result'),
    path("staff/result/edit/", EditResultView.as_view(), name='edit_student_result'),
    path('staff/result/fetch/', staff_views.fetch_student_result, name='fetch_student_result'),
    # ... existing URL patterns ...
    path("staff/student-list/", staff_views.staff_student_list, name='staff_student_list'),
    path("staff/result-detail/<int:student_id>/", staff_views.staff_result_detail, name='staff_result_detail'),
      # ... other URL patterns ...
    path("staff/result/edit/<int:student_id>/", EditResultView.as_view(), name='edit_student_result'),
     # ... other patterns ...
      # ... other URL patterns ...
    path("staff/result/delete/<int:student_id>/", staff_views.staff_delete_result, name='delete_student_result'),
    # ... other URL patterns ...
    path("staff/result/pdf/<int:student_id>/", staff_views.staff_result_pdf, name='staff_result_pdf'),
    path('staff/result/edit/<int:student_id>/', staff_views.EditResultView.as_view(), name='edit_student_result'),
    path('staff/result/compiled/<int:student_id>/<int:session_id>/', staff_views.compile_session_results, name='staff_view_session_results'),
    # path('staff/result/term/', staff_views.staff_view_term_results, name='staff_view_term_results'),
     path('get_terms/', staff_views.get_terms, name='get_terms'),
     path('get_terms/', staff_views.get_terms, name='get_terms'),
     path('get_terms/', staff_views.get_terms, name='get_terms'),
     path('result/filtered/', staff_views.staff_view_result_filtered, name='staff_view_result_filtered'),
     path("get_attendance/", staff_views.staff_views_get_attendance, name="staff_views_get_attendance"),
    # path('api/notifications/', staff_views.api_fetch_notifications, name='api_fetch_notifications'),
    # path('staff/notifications/ajax/', staff_views.ajax_get_notifications, name='ajax_get_notifications'),
    # path('ajax/get-notifications/', staff_views.ajax_get_notifications, name='ajax_get_notifications'),
    # path('ajax/notifications/', staff_views.ajax_get_notifications, name='ajax_get_notifications'),
    # path('ajax/notifications/mark-read/', staff_views.ajax_mark_notifications_read, name='ajax_mark_notifications_read'),
    # path('ajax/notifications/', student_views.ajax_get_notifications, name='ajax_get_notifications'),
    # path('ajax/notifications/mark-read/', student_views.ajax_mark_notifications_read, name='ajax_mark_notifications_read'),
    # path('ajax/notifications/', hod_views.ajax_get_notifications, name='ajax_get_notifications'),
    # path('ajax/notifications/mark-read/', hod_views.ajax_mark_notifications_read, name='ajax_mark_notifications_read'),

   
    # AJAX notifications for students:///////////////////////////////////////////////////////////////
    # path('ajax/notifications/student/', student_views.ajax_get_notifications_student, name='ajax_get_notifications_student'),
    # path('ajax/notifications/student/mark-read/', student_views.ajax_mark_notifications_read_student, name='ajax_mark_notifications_read_student'),

    # For HOD (currently returns empty list – modify later if you add a NotificationHOD model):
    # path('ajax/notifications/hod/', hod_views.ajax_get_notifications_hod, name='ajax_get_notifications_hod'),
    # path('ajax/notifications/hod/mark-read/', hod_views.ajax_mark_notifications_read_hod, name='ajax_mark_notifications_read_hod'),
    # path('hod/notifications/', hod_views.hod_view_notification, name='hod_view_notification'),
    # path('ajax/get-notifications/', staff_views.ajax_get_notifications, name='ajax_get_notifications'),
    path('ajax/notifications/hod/', hod_views.ajax_get_notifications_hod, name='ajax_get_notifications_hod'),
    path('ajax/notifications/hod/mark-read/', hod_views.ajax_mark_notifications_read_hod, name='ajax_mark_notifications_read_hod'),
    path('api/notifications/hod/', hod_views.api_fetch_hod_notifications, name='api_fetch_hod_notifications'),
    path('hod/view/notification/', hod_views.hod_view_notification, name='hod_view_notification'),
    path('ajax/notifications/hod/', hod_views.ajax_get_notifications_hod, name='ajax_get_notifications_hod'),

     # HOD (Admin) Notifications
    # path('ajax/get-notifications-hod/', hod_views.ajax_get_notifications_hod, name='ajax_get_notifications_hod'),
    # path('ajax/mark-notifications-read-hod/', hod_views.ajax_mark_notifications_read_hod, name='ajax_mark_notifications_read_hod'),

    # Staff Notifications
    path('ajax/get-notifications-staff/', staff_views.ajax_get_notifications_staff, name='ajax_staff_notifications'),
    path('ajax/mark-notifications-read-staff/', staff_views.ajax_mark_notifications_read_staff, name='ajax_mark_notifications_read_staff'),

    # Student Notifications
    path('ajax/get-notifications-student/', student_views.ajax_get_notifications_student, name='ajax_get_notifications_student'),
    path('ajax/mark-notifications-read-student/', student_views.ajax_mark_notifications_read_student, name='ajax_mark_notifications_read_student'),
    path("staff/students/", staff_views.staff_student_attendance, name="staff_student_attendance"),
    path("staff/mark-attendance/", staff_views.mark_attendance, name="mark_attendance"),
    path('staff/mark-attendance/', staff_views.bulk_mark_attendance, name='bulk_mark_attendance'),
    path("staff/students/", staff_views.staff_student_attendance, name="staff_student_attendance"),
    path("staff/mark-attendance/", staff_views.bulk_mark_attendance, name="bulk_mark_attendance"),  # Ensure this exists

   


     
     



    # Student Views
    path("student/home/", student_views.student_home, name='student_home'),
    path("student/view/attendance/", student_views.student_view_attendance, name='student_view_attendance'),
    path("student/apply/leave/", student_views.student_apply_leave, name='student_apply_leave'),
    path("student/feedback/", student_views.student_feedback, name='student_feedback'),
    path("student/view/profile/", student_views.student_view_profile, name='student_view_profile'),
    path("student/fcmtoken/", student_views.student_fcmtoken, name='student_fcmtoken'),
    path("student/view/notification/", student_views.student_view_notification, name="student_view_notification"),
    path('student/view/result/', student_views.student_view_result, name='student_view_result'),
    path("student/view/results/", student_views.student_results_list, name="student_results_list"),
    # ... other URL patterns ...
    path("student/view/result/<int:student_id>/", student_views.student_view_result, name="student_view_result"),
     # ... other URL patterns ...
    path("student/result/pdf/", student_views.student_result_pdf, name="student_result_pdf"),
    path('result/filtered/', student_views.student_result_detail_filtered, name='student_result_detail_filtered'),
    path('results/', student_views.student_results_list, name='student_results_list'),
    path('get_terms_student/', student_views.get_terms_student, name='get_terms_student'),
    
    # ... your other URL patterns ...
    path('student/result/filtered/', student_views.student_result_detail_filtered, name='student_result_detail_filtered'),
    # ... your other url patterns ...
      # ... other URL patterns for student ...
    path('ajax/student/notifications/', student_views.ajax_student_notifications, name='ajax_student_notifications'),
    path('ajax/staff/notifications/', staff_views.ajax_staff_notifications3, name='ajax_staff_notifications3'),
    # path('student/results/', student_views.student_results_list, name="student_results_list"),
    path('student/overall_result/<int:session_id>/', student_views.student_overall_result, name="student_overall_result"),
    path('student/overall-result/pdf/<int:session_id>/', student_views.student_overall_result_pdf, name='student_overall_result_pdf'),
    # path('student/overall-result/pdf/<int:student_id>/<int:session_id>/', student_views.student_overall_result_pdf, name='student_overall_result_pdf'),
    # path('student/overall-result/pdf/<int:student_id>/', student_views.student_overall_result_pdf, name='student_overall_result_pdf'),





]
