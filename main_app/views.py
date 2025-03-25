import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt

from .EmailBackend import EmailBackend
from .models import Attendance, Session, Subject

# ------------------------------
# User Authentication Views
# ------------------------------

def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html')


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        # (Optional) Google reCAPTCHA code is commented out below.
        # captcha_token = request.POST.get('g-recaptcha-response')
        # captcha_url = "https://www.google.com/recaptcha/api/siteverify"
        # captcha_key = "your-captcha-key"
        # data = {'secret': captcha_key, 'response': captcha_token}
        # try:
        #     captcha_server = requests.post(url=captcha_url, data=data)
        #     response = json.loads(captcha_server.text)
        #     if not response.get('success', False):
        #         messages.error(request, 'Invalid Captcha. Try Again')
        #         return redirect('/')
        # except Exception:
        #     messages.error(request, 'Captcha could not be verified. Try Again')
        #     return redirect('/')

        # Authenticate using the custom EmailBackend.
        user = EmailBackend.authenticate(
            request,
            username=request.POST.get('email'),
            password=request.POST.get('password')
        )
        if user is not None:
            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")


def logout_user(request):
    if request.user:
        logout(request)
    return redirect("/")


# ------------------------------
# Attendance View
# ------------------------------

@csrf_exempt
def get_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                "id": attd.id,
                "attendance_date": str(attd.date),
                "session": attd.session.id
            }
            attendance_list.append(data)
        # Directly pass Python object to JsonResponse (no need for json.dumps)
        return JsonResponse(attendance_list, safe=False)
    except Exception as e:
        # Return a JSON error message with status 400
        return JsonResponse({'error': str(e)}, status=400)


# ------------------------------
# Firebase Service Worker JS
# ------------------------------

def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
    // Note: Only Firebase Messaging is available here.
    importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
    importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

    // Initialize the Firebase app in the service worker with your Firebase config.
    firebase.initializeApp({
        apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
        authDomain: "sms-with-django.firebaseapp.com",
        databaseURL: "https://sms-with-django.firebaseio.com",
        projectId: "sms-with-django",
        storageBucket: "sms-with-django.appspot.com",
        messagingSenderId: "945324593139",
        appId: "1:945324593139:web:03fa99a8854bbd38420c86",
        measurementId: "G-2F2RXTL9GT"
    });

    // Retrieve an instance of Firebase Messaging.
    const messaging = firebase.messaging();
    messaging.setBackgroundMessageHandler(function (payload) {
        const notification = JSON.parse(payload);
        const notificationOption = {
            body: notification.body,
            icon: notification.icon
        };
        return self.registration.showNotification(payload.notification.title, notificationOption);
    });
    """
    return HttpResponse(data, content_type='application/javascript')


# from django.shortcuts import render, redirect
# from django.contrib import messages
# from django.core.mail import send_mail
# from django.contrib.auth.models import User
# from django.contrib.auth.tokens import default_token_generator
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from django.utils.encoding import force_bytes, force_str
# import uuid

# def password_reset_request(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         try:
#             # Find user by email
#             user = User.objects.get(email=email)
            
#             # Generate unique token
#             token = str(uuid.uuid4())
            
#             # Store token with user (you might want to create a separate model for this)
#             user.profile.reset_token = token
#             user.profile.save()
            
#             # Construct reset link
#             reset_link = f"http://{request.get_host()}/password-reset-confirm/{urlsafe_base64_encode(force_bytes(user.pk))}/{token}/"
            
#             # Send email
#             send_mail(
#                 'Password Reset Request',
#                 f'Click the following link to reset your password: {reset_link}',
#                 'noreply@hibiscusacademy.com',
#                 [email],
#                 fail_silently=False,
#             )
            
#             messages.success(request, 'Password reset link has been sent to your email.')
#             return redirect('login_page')
        
#         except User.DoesNotExist:
#             messages.error(request, 'No account found with this email address.')
    
#     return render(request, 'main_apppassword_reset_request.html')

# def password_reset_confirm(request, uidb64, token):
    try:
        # Decode user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        
        # Check if token matches
        if user.profile.reset_token != token:
            messages.error(request, 'Invalid or expired reset link.')
            return redirect('login_page')
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'password_reset_confirm.html', {'uidb64': uidb64, 'token': token})
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Clear reset token
            user.profile.reset_token = None
            user.profile.save()
            
            messages.success(request, 'Password reset successful. You can now log in.')
            return redirect('login_page')
        
        return render(request, 'password_reset_confirm.html', {'uidb64': uidb64, 'token': token})
    
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid reset link.')
        return redirect('login_page')