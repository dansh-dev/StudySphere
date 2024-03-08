from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from .forms import CourseContentForm, CourseContentSubmissionForm, CourseCreationForm, CourseDeadlineForm, CourseEditForm, StatusUpdateForm, CommentForm, CourseFeedbackForm, UserSearchForm
from .models import Course, NotificationContent, NotificationEnroll, Post, Comment, CourseContent, Submission, CourseDeadline, CourseFeedback, StudySphereUser
from django.contrib import messages
from .tasks import send_emails
from django.contrib.auth.decorators import login_required

# This view is to be called whenever an unauthorized request is made
def not_authorized(request):
    return render(request, 'not_authorized.html')

# This allows the user to view all courses
def view_all_courses(request, mode=""):
    # The MODE is used in one case when the unauthorized index page of the site is called
    # DATA mode simply returns all courses, this is used to give potential students a peek
    # at what courses we offer.
    if mode == "DATA":
        courses = Course.objects.all()
        return courses
    else:
        courses_enrolled = user_subscribed_courses(request)
        courses = Course.objects.all()

        # Excludes all courses currently already enrolled in
        available_courses = courses.exclude(id__in=courses_enrolled.values_list('id', flat=True))
        return render(request, 'courses.html', {'courses': available_courses})

# This view allows for creation of courses
@login_required
def create_course(request):
    auth_level = request.user.auth_level
    # Verifies the auth_level of the user
    if auth_level == "teacher":
        if request.method == 'POST':
            form = CourseCreationForm(request.POST)
            # Checks the forms validity
            if form.is_valid():
                course = form.save(commit=False)
                course.teacher = request.user
                # Saves the course
                course.save()
                return redirect('/courses/courses')
            else:
                # Else it returns errors along with the form again
                errors = form.errors
                form = CourseCreationForm()
                return render(request, 'create_course.html', {'form': form, 'errors': errors})
        else:
            # This returns the page when an initial GET request is sent
            form = CourseCreationForm()
            return render(request, 'create_course.html', {'form': form})
    else:
        # In the case of lacking permissions
        return redirect('/courses/not_authorized')
    
# This view allows for the editing of the course
@login_required
def edit_course(request, course_id):
    # Gets the course from DB with a 404 returned if ID is invalid
    course = get_object_or_404(Course, id=course_id)
    # Verifies that the user attempting to edit the course is the course's creator
    if request.user == course.teacher:
        if request.user.auth_level == 'teacher':
            # In the case of form submission
            if request.method == 'POST':
                form = CourseEditForm(request.POST, instance=course)
                if form.is_valid():
                    # setting field and saving the course
                    course = form.save()
                    banner_image = request.FILES.get('banner_image')
                    if banner_image:
                        course.banner_image = banner_image
                        course.save()
                    # Also displays students that are in the course that the teacher can then remove
                    students_to_remove = request.POST.getlist('students_to_remove')
                    for student_id in students_to_remove:
                        # Removes student from the course
                        course.students.remove(int(student_id))
                    return redirect('/courses/courses', course_id=course_id)
                else:
                    # If invalid data is provided return the errors and the form again
                    errors = form.errors
                    form = CourseEditForm(instance=course)
                    return render(request, 'edit_course.html', {'form': form, 'course': course, 'errors': errors})
            else:
                # This occurs when method is GET
                form = CourseEditForm(instance=course)
                return render(request, 'edit_course.html', {'form': form, 'course': course})
    # These cases occur then the user lacks the necessary permisssions
        else:
            return redirect('/courses/not_authorized')
    else:
        return redirect('/courses/not_authorized')

# This view allows for deletion of course
@login_required
def delete_course(request, course_id):
    # Verifies that a teacher is trying to delete the course
    if request.user.auth_level == 'teacher':
        # Returns 404 if course id is invalid
        course = get_object_or_404(Course, id=course_id)
        course.delete()
        return redirect('/courses/homepage')
    # In case of not being a teacher
    else:
        return redirect('/courses/not_authorized')

# This view allows for a student to enroll on a course
@login_required
def enroll_course(request, course_id):
    course = Course.objects.get(id=course_id)
    # if enroll form is submitted
    if request.method == 'POST':
        if request.user.auth_level == 'student':
            # Adds the student to the course
            course.students.add(request.user)
            messages.success(request, f'You have successfully enrolled in {course.name}.')
            student = request.user
            # Creates a notification for the teacher
            NotificationEnroll.objects.create(student=student, teacher_id = course.teacher.id ,course=course)
            recipient = []
            recipient.append(course.teacher.email)
            # Sends an email to the teacher to notify them of enrollment
            send_emails.delay('A New Student enrolled on one of your courses!', f'New student enrolled on course {course.name} \nStudent: {request.user.username}', recipient)
            return redirect('/courses/homepage') # Redirects to course homepage
        else:
            # If a teacher tries to enroll
            messages.error(request, 'Only students can enroll in courses.')
    return render(request, 'enroll_course.html', {'course': course})

# This allows for students to leave a course
@login_required
def course_unenroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    # Remove the current user from the list of students of the course
    if request.user.is_authenticated:
        request.user.enrolled_courses.remove(course)
        return redirect('homepage') # If successful return to homepage
    else:
        # if user is unauthed
        return redirect('/courses/not_authorized')

# Retrieves user enrolled courses
@login_required
def user_subscribed_courses(request):
    subscribed_courses = Course.objects.filter(students=request.user)
    return subscribed_courses

# Retrieves all courses that the user has created
@login_required
def user_created_courses(request):
    created_courses = Course.objects.filter(teacher=request.user)
    return created_courses

# Allows for viewing of course in detail such as course content/feedback and submissions
@login_required
def view_course_details(request, course_id):
    if request.user.is_authenticated:
        if request.method == "POST":
           course = get_object_or_404(Course, id=course_id)
           # Retrieves all content of the course
           course_content = CourseContent.objects.filter(course=course_id)
           # Gets the feedback left by students
           leave_feedback(request, course) 
           feedback = CourseFeedback.objects.filter(course_id=course_id)
           # Sets the form
           form = CourseFeedbackForm
           return render(request, 'view_course.html', {'course': course, 'course_content': course_content, 'form': form, 'feedback': feedback})
        else:    
            # in the case of a get request being sent
            course = get_object_or_404(Course, id=course_id)
            course_content = CourseContent.objects.filter(course=course_id)
            form = CourseFeedbackForm
            feedback = CourseFeedback.objects.filter(course_id=course_id)
            return render(request, 'view_course.html', {'course': course, 'course_content': course_content, 'form': form, 'feedback': feedback})
    else:
        return redirect('/courses/not_authorized')

# View course content details
@login_required
def view_content(request, content_id):
    if request.user.is_authenticated:
        # Gets the content
        content = CourseContent.objects.get(id=content_id)
        # Gets it deadline
        content_deadline = get_course_content_deadline(content_id)
        # gets submissions
        submission = submission_check(request, content.id)
        # Returns data
        return render(request, 'view_content.html', {'content': content, 'content_deadline': content_deadline, 'submission': submission})
    else:
         return redirect('/courses/not_authorized')

# This view allows for addition of course content
@login_required 
def add_course_content(request, course_id):
    course = Course.objects.get(id=course_id)
    if request.method == 'POST':
        content_form = CourseContentForm(request.POST, request.FILES)
        deadline_form = CourseDeadlineForm(request.POST)
        # Retrieves form contents from request
        if content_form.is_valid() and deadline_form.is_valid():
            content = content_form.save(commit=False)
            content.course = course
            content.save()
            deadline = deadline_form.save(commit=False)
            deadline.content = content
            deadline.save()

            # Gets all enrolled students and sends them emails via a Celery Service worker
            enrolled_students = course.students.all()
            recipients = []
            for student in enrolled_students:
                recipients.append(student.email)
                NotificationContent.objects.create(student=student, course_content=content)
            send_emails.delay('New course content added!' ,f'New content added on course {content.course.name} \nContent: {content.title},\nDescription: {content.content_text}\nDeadline:{deadline.deadline}', recipients)
            return redirect('/courses/homepage/') # Redirects to learning homepage
    else:
        # in the case of a get request
        content_form = CourseContentForm()
        deadline_form = CourseDeadlineForm()
    return render(request, 'add_course_content.html', {'content_form': content_form, 'deadline_form': deadline_form})

# Functionality for deletion of course content
def delete_content(request, content_id):
    content = get_object_or_404(CourseContent, id=content_id)
    if request.user.is_authenticated:
        if request.user.auth_level == "teacher":
            # If content exists -> Delete
            if content:
                content.delete()
                return redirect('/courses/homepage/')
    else:
        return redirect('/courses/not_authorized')

# Home page function that displays all data to users
@login_required
def homepage(request):
    if request.user.is_authenticated:
        if request.user.auth_level == 'student':
            # Gets courses that they have enrolled in, posts, deadlines and the forms
            enrolled_courses = user_subscribed_courses(request)
            posts = show_status_updates(request)
            form = StatusUpdateForm
            deadlines = get_course_content_with_deadline(request)
            sorted_deadlines = sorted(deadlines, key=lambda x: x[0].deadline)
            return render(request, 'homepage.html', {'enrolled_courses': enrolled_courses, 'posts': posts, 'form': form, 'deadlines': sorted_deadlines})
        else:
            # In the case that a teacher accesses their homepage get the relevant details
            active_students = get_active_students(request)
            created_courses = user_created_courses(request)
            posts = show_status_updates(request)
            form = StatusUpdateForm
            searchform = UserSearchForm
            return render(request, 'homepage.html', {'created_courses': created_courses, 'posts': posts, 'form': form, 'searchform': searchform, 'active_students': active_students})
    else:
        return redirect('/courses/not_authorized')

# This function posts a status update
@login_required
def post_status_update(request):
    if request.method == 'POST':
        form = StatusUpdateForm(request.POST)
        # Checks if form is valid and saves it
        if form.is_valid():
            status_update = form.save(commit=False)
            status_update.user = request.user
            status_update.save()
            messages.success(request, 'Status update posted successfully.')
            return redirect('homepage')
    else:
        form = StatusUpdateForm()
    return render(request, 'homepage.html', {'form': form})

# Facilitates deletion of a post
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        # Ensures that user requesting to delete post is the creator of a post
        if request.user == post.user:
            post.delete()
            messages.success(request, 'Post deleted successfully.')
        else:
            messages.error(request, 'You do not have permission to delete this post.')
    return redirect('homepage')

# This function shows status updates and sorts them accordingly
@login_required
def show_status_updates(request):
    if request.method == 'GET':
        posts = Post.objects.all()
        # Sorts by date created at
        sorted_posts = sorted(posts, key=lambda x: x.created_at)
        return sorted_posts

# Used to display comments on a post
@login_required 
def show_comments(request, post_id):
    comments = Comment.objects.filter(post_id=post_id)
    return render(request, 'comment_view.html', {'comments': comments})

# Facilitates posting of comments 
@login_required
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        # Checks if form is valid and saves
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            return redirect('homepage')
    else:
        form = CommentForm()
    return redirect('homepage')

# Retrieves content deadline for a specified content
def get_course_content_deadline(content_id):
    return CourseDeadline.objects.filter(content = content_id)

# Facilitates downloading of PDF files directly from a template
def download_pdf(request, content_id):
    content = get_object_or_404(CourseContent, id=content_id)
    pdf_file = content.pdf_files
    if pdf_file:
        # Open the PDF file and serve it as a FileResponse
        response = FileResponse(open(pdf_file.path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_file.name}"'
        return response
    else:
        # Handle case where PDF file does not exist
        return HttpResponse("PDF file not found", status=404)
    
# Facilitates downloading of a student submission
def download_pdf_submission(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    pdf_file = submission.pdf_files
    if pdf_file:
        # Open the PDF file and serve it as a FileResponse
        response = FileResponse(open(pdf_file.path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{pdf_file.name}"'
        return response
    else:
        # Handle case where PDF file does not exist
        return HttpResponse("PDF file not found", status=404)

# Facilitates leaving of feedback on courses
@login_required
def leave_feedback(request, course):
    form = CourseFeedbackForm(request.POST)
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.user = request.user
        feedback.course = course
        feedback.save()
        pass
    else:
        return(form.errors)
    
# Gets all deadlines of a user on courses that they are enrolled to
def get_deadlines(request):
    if request.user.is_authenticated:
        deadlines = []
        courses = user_subscribed_courses(request)
        
        if courses:
            for course in courses:
                content = CourseContent.objects.filter(course = course.id)
                for content_item in content:
                    deadline = get_course_content_deadline(content_id=content_item.id)
                    for date in deadline:
                        deadlines.append(date.deadline)           
        return deadlines

    else:
        return redirect('homepage')

# Gets a specified course content and its deadline
@login_required
def get_course_content_with_deadline(request):
    courses = user_subscribed_courses(request)
    deadlines = []
    for course in courses:
        course_contents = CourseContent.objects.filter(course=course.id)
        for content in course_contents:
            content_deadline = CourseDeadline.objects.filter(content = content.id)
            deadlines.append(content_deadline)

    return deadlines

# Gets all active students through a simple query
@login_required
def get_active_students(request):
    if request.user.is_authenticated:
        if request.user.auth_level == "teacher":
            active_users = StudySphereUser.objects.filter(is_active = 1, auth_level='student')
            return active_users
        else: 
            return "Not authorized!"    
    else: 
        return "Not authorized!"
    
# Retrieves notifications based on auth_level
@login_required
def show_notifications(request):
    if request.user.is_authenticated:

        if request.user.auth_level == 'teacher':
            # Get enrollment notifications
            notifications = NotificationEnroll.objects.filter(teacher_id = request.user)
            return render(request, 'notifications.html', {'notifications': notifications})
        else:
            # Get new content notifications
            notifications = NotificationContent.objects.filter(student_id=request.user)    
            return render(request, 'notifications.html', {'notifications': notifications})
    else:
        return redirect('/courses/not_authorized')

# Facilitates searching of a user
@login_required
def user_search(request):
    if request.method == 'GET':
        form = UserSearchForm(request.GET)
        # Verifies that form is valid before querying
        if form.is_valid():
            query = form.cleaned_data['query']
            users = StudySphereUser.objects.filter(username__icontains=query)
            return render(request, 'user_search_results.html', {'form': form, 'users': users})
    else:
        form = UserSearchForm()
    return redirect('homepage')

# Facilitates creation of a submission on a course content
@login_required
def create_submission(request, content_id):
    if request.user.is_authenticated:
        content = get_object_or_404(CourseContent, pk=content_id)
        if request.method == 'GET':
            # In the case of a GET request users ae returned the creation form
            form = CourseContentSubmissionForm()
            return render(request, 'create_submission.html', {'form': form})
        else:
            # Else validate the form and save it
            form = CourseContentSubmissionForm(request.POST, request.FILES)
            if form.is_valid():
                submission = form.save(commit=False)
                submission.content = content  # Set the content object directly
                submission.student = request.user  # Set the student
                submission.save()
                return redirect('homepage')
    else:
        return redirect('/courses/not_authorized')

# Allows for a teacher to view all submissions on a course content
@login_required
def view_submissions(request, content_id):
    if request.user.is_authenticated:
        if request.user.auth_level == 'teacher':
            submissions = Submission.objects.filter(content=content_id)
            if request.method == 'GET':
                return render(request, 'view_submissions.html', {'submissions': submissions})
        else:
          return redirect('/courses/not_authorized')  
    else:
        return redirect('/courses/not_authorized')

# Allows for viewing of a specific submission of a single student
@login_required
def view_submission(request, submission_id):
    if request.user.is_authenticated:
        submission = get_object_or_404(Submission, pk=submission_id)
        if request.user.auth_level == 'teacher' or request.user == submission.student:
            if request.method == 'GET':
                return render(request, 'submission.html', {'submission': submission})
        else:
          return redirect('/courses/not_authorized')  
    else:
        return redirect('/courses/not_authorized')

# Checks if a submission on the course content has been made
@login_required
def submission_check(request, content_id):
    submission = Submission.objects.filter(student=request.user, content=content_id)
    if submission:
        return submission
    