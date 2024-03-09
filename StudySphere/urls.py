from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core_study.urls')),
    path('chat/', include('chat.urls')),
    path('users/', include('django.contrib.auth.urls')),
    path('users/', include('users.urls')),
    path('courses/', include('courses.urls')),

] 
if settings.DEBUG == False:
    urlpatterns += static(settings.STATIC_URL ,document_root=settings.MEDIA_ROOT)


if settings.DEBUG == True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)