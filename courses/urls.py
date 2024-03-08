from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_course, name='create_course'),
    path('courses/', views.view_all_courses, name='courses'),
    path('not_authorized/', views.not_authorized, name='not_authorized'),
    path('<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('subscribed/', views.user_subscribed_courses, name='subscribed_courses'),
    path('homepage/', views.homepage, name='homepage'),
    path('post_status_update', views.post_status_update, name='post_status_update'),
    path('posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('posts/<int:post_id>/comment/', views.post_comment, name='post_comment'),
    path('posts/<int:post_id>/view_comments/', views.show_comments, name='view_comments'),
    path('edit/<int:course_id>/', views.edit_course, name='edit'),
    path('delete_course/<int:course_id>/', views.delete_course, name='delete_course'),
    path('view/<int:course_id>', views.view_course_details, name='view'),
    path('unenroll_course/<int:course_id>/', views.course_unenroll, name='unenroll_course'),
    path('add_content/<int:course_id>/', views.add_course_content, name='add_course_content'),
    path('submit/<int:content_id>/', views.create_submission, name='submit'),
    path('view_submissions/<int:content_id>/', views.view_submissions, name='view_submissions'),
    path('submission/<int:submission_id>/', views.view_submission, name='submission'),
    path('view_content/<int:content_id>/', views.view_content, name='view_content'),
    path('download_pdf/<int:content_id>/', views.download_pdf, name='download_pdf'),
    path('download_pdf_submission/<int:submission_id>/', views.download_pdf_submission, name='download_pdf_submission'),
    path('delete_content/<int:content_id>/', views.delete_content, name='delete_content'),
    path('notifications/', views.show_notifications, name='notifications'),
    path('notifications/', views.show_notifications, name='notifications'),
    path('user_search/', views.user_search, name='user_search')
]