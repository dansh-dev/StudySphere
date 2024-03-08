from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login_user/', views.login_user, name="login_user"),
    path('logout_user/', views.logout_user, name="logout_user"),
    path('signup_user/', views.register_user, name="signup_user"),
    path('profile/', views.profile, name="profile"),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('view_user_profile/<int:user_id>', views.view_profile, name='view_profile'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/users/login_user'
    ), name='password_reset'),
]