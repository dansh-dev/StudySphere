from django.shortcuts import render
from courses.views import view_all_courses

# / homepage
def index (request):
    courses = view_all_courses(request, mode="DATA")
    return  render(request, 'index.html', {'courses': courses})
