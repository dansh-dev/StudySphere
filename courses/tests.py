import datetime
from users.models import StudySphereUser

from django.test import Client, TestCase, RequestFactory
from django.http import HttpRequest, HttpResponseNotFound
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from .views import view_all_courses
from .models import Course, NotificationEnroll
from unittest.mock import patch
from django.urls import reverse
from .views import *
from .forms import CourseCreationForm
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages.storage.fallback import FallbackStorage

from django.contrib.messages import get_messages

# This tests the function that is meant to allow the user to view all courses
class TestViewAllCourses(TestCase):
    def setUp(self):
        self.request = HttpRequest()
        self.user = StudySphereUser.objects.create(username="test_user")

    # These two test cases test both modes of the view - This being the "DATA" mode and the Non-Data mode
    @patch('courses.views.Course.objects.all')
    def test_mode_data(self, mock_courses_all):

        # Mocking Course.objects.all() so that it returns the right datatype
        mock_courses_all.return_value = Course.objects.none()

        # Calling my function using the mode set to "DATA"
        courses = view_all_courses(self.request, mode="DATA")

        # Makes sure that it returns an empty data object
        self.assertQuerysetEqual(courses, Course.objects.none(), transform=lambda x: x)

    @patch('courses.views.Course.objects.all')
    @patch('courses.views.user_subscribed_courses')
    @patch('courses.views.render')
    def test_mode_not_data(self, mock_render, mock_user_subscribed_courses, mock_courses_all):
        # Mock user_subscribed_courses to return an empty queryset
        mock_user_subscribed_courses.return_value = Course.objects.none()

        # Mock Course.objects.all() to return an empty queryset
        mock_courses_all.return_value = Course.objects.none()

        # Call the view_all_courses function with mode not equal to "DATA"
        view_all_courses(self.request, mode="")

        # Check that the correct responses are sent
        render_args, _ = mock_render.call_args
        self.assertEqual(render_args[0], self.request)  
        self.assertEqual(render_args[1], 'courses.html')  # Checks the name of the returned template
        self.assertEqual(len(render_args[2]['courses']), 0) 

# This tests the creation of courses
class CreateCourseViewTests(TestCase):
    # Sets up mock users
    def setUp(self):
        self.client = Client()
        self.teacher_user = StudySphereUser.objects.create(username='teacher', auth_level='teacher', email='teacher@test.com')
        self.non_teacher_user = StudySphereUser.objects.create(username='student', auth_level='student', email='student@test.com')

    # This tests the case when a teacher accesses the creation page
    def test_teacher_user_get_form(self):
        # Logs in the teacher
        self.client.force_login(self.teacher_user)
        # Gets the page and verifies the response to ensure correct form passing into template
        response = self.client.get(reverse('create_course'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CourseCreationForm)

    # This case tests the instance where a teacher would input some form of invalid data
    def test_teacher_user_invalid_form_data(self):
        self.client.force_login(self.teacher_user)
        response = self.client.post(reverse('create_course'), {})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)

    # Testing the case where a teacher would input correct data into the form
    def test_teacher_user_post_valid_data(self):
        self.client.force_login(self.teacher_user)
        response = self.client.post(reverse('create_course'), {'name': 'value'})
        self.assertEqual(response.status_code, 200) 

    # Ensures that if a user is not a teacher that it correctly redirects to the not authorized page!
    def test_non_teacher_user_redirected(self):
        self.client.force_login(self.non_teacher_user)
        response = self.client.get(reverse('create_course'))
        self.assertEqual(response.status_code, 302) 

# This tests the Edit course functionality
class EditCourseViewTests(TestCase):
    def setUp(self):
        # Setup the clients, including creating a course bound to the teacher user
        self.client = Client()
        self.teacher_user = get_user_model().objects.create(username="teacher", auth_level="teacher", email="teacher@test.com")
        self.student_user = get_user_model().objects.create(username="student", auth_level="student", email="student@test.com")
        self.course = Course.objects.create(name="Test Course", teacher=self.teacher_user)

    # Tests the case where a teacher would edit their course
    def test_access_edit_course_page_teacher(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('edit', args=[self.course.id]))
        self.assertEqual(response.status_code, 200)

    # This tests if a student tries to edit a course
    def test_access_edit_course_page_non_teacher(self):
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('edit', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)  # Expecting a not authorized page

    # Tests if a teacher user edits a course and inputs valid data
    def test_edit_course_valid_data(self):
        self.client.force_login(self.teacher_user)
        response = self.client.post(reverse('edit', args=[self.course.id]), {'name': 'New Course Title'})
        self.assertEqual(response.status_code, 200)  # Expecting to be redirected

    # This tests the case where a user would input invalid data to the form
    def test_edit_course_invalid_data(self):
        self.client.force_login(self.teacher_user)
        response = self.client.post(reverse('edit', args=[self.course.id]), {})
        self.assertEqual(response.status_code, 200) # This ensures correct back to homepage and non-submission of form

    # This tests the file upload functionality
    def test_edit_course_file_upload(self):
        self.client.force_login(self.teacher_user)
        with open('courses/test_images/test_image.jpg', 'rb') as file:
            response = self.client.post(reverse('edit', args=[self.course.id]), {'banner_image': file})
        self.assertEqual(response.status_code, 200)

# This tests the functionality that allows a user to delete a course
class DeleteCourseViewTests(TestCase):
    def setUp(self):
        # Sets up two users with different permissions and a course to test the functionality on
        self.teacher_user = get_user_model().objects.create_user(
            username='teacher',
            password='teacherpassword',
            auth_level='teacher',
            email="teacher@test.com"
        )
        self.non_teacher_user = get_user_model().objects.create_user(
            username='student',
            password='studentpassword',
            auth_level='student',
            email="student@test.com"
        )
        self.course = Course.objects.create(
            name='Test Course',
            teacher=self.teacher_user
        )

    # This tests when a teacher deletes a course
    def test_delete_course_by_teacher(self):
        self.client.force_login(self.teacher_user)
        response = self.client.post(reverse('delete_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)  # Expecting to be redirected
        self.assertFalse(Course.objects.filter(pk=self.course.id).exists())

    def test_delete_course_by_non_teacher(self):
        self.client.force_login(self.non_teacher_user)
        response = self.client.post(reverse('delete_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)  # Expecting to be redirected and no course deletion to occur

    def test_delete_course_with_invalid_id(self):
        self.client.force_login(self.teacher_user)
        invalid_course_id = 9999  # Course ID that doesn't exist
        response = self.client.post(reverse('delete_course', args=[invalid_course_id]))
        self.assertEqual(response.status_code, 404)  # Expecting Not Found
        self.assertIsInstance(response, HttpResponseNotFound)

# Testing the enrollment view
class EnrollCourseViewTests(TestCase):
    def setUp(self):
        self.student_user = get_user_model().objects.create_user(
            username='student',
            password='studentpassword',
            auth_level='student',
            email="student@test.com"
        )
        self.non_student_user = get_user_model().objects.create_user(
            username='teacher',
            password='teacherpassword',
            auth_level='teacher',
            email="teacher@test.com"
        )
        self.course = Course.objects.create(
            name='Test Course',
            teacher=self.non_student_user
        )

    # Testing the case where a student would enroll into a course
    def test_successful_enrollment_by_student(self):
        self.client.force_login(self.student_user)
        response = self.client.post(reverse('enroll_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 302)  # Expecting to be redirected to homepage
        self.assertTrue(self.course.students.filter(pk=self.student_user.id).exists())
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn(f'You have successfully enrolled in {self.course.name}.', messages) # Ensures that student has been enrolled
        self.assertTrue(NotificationEnroll.objects.filter(student=self.student_user, course=self.course).exists()) # Confirms through query
        self.assertEqual(response.status_code, 302) 

    # Ensures that when a teacher attempts to enroll that it is successfully prevented
    def test_enrollment_by_non_student_user(self):
        self.client.force_login(self.non_student_user)
        response = self.client.post(reverse('enroll_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 200) 
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('Only students can enroll in courses.', messages) # Ensures that enrollment doesn't happen

    # Testing the rendering of the page including form use
    def test_render_enrollment_page(self):
        response = self.client.get(reverse('enroll_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 302) 

# Tests the unenrollment function
class CourseUnenrollViewTests(TestCase):
    def setUp(self):
        self.student_user = get_user_model().objects.create_user(
            username='student',
            password='studentpassword',
            auth_level='student',
            email="student@test.com"
        )
        self.teacher_user = get_user_model().objects.create_user(
            username='teacher',
            password='teacherpassword',
            auth_level='teacher',
            email="teacher@test.com"
        )
        self.course = Course.objects.create(
            name='Test Course',
            teacher = self.teacher_user
        )
        self.student_user.enrolled_courses.add(self.course)

    # This tests if unenrollment happens successfully
    def test_successful_unenrollment(self):
        self.client.force_login(self.student_user)
        response = course_unenroll(self.get_request_with_user(), self.course.id)
        self.assertEqual(response.url, reverse('homepage')) # Ensures that user is redirected appropriately
        self.assertFalse(self.student_user.enrolled_courses.filter(pk=self.course.id).exists()) # Confirms unenrollment through query

    # Tests the get request
    def get_request_with_user(self, user=None):
        request = self.client.request().wsgi_request
        request.user = user if user else self.student_user
        return request

# This tests the view where the user can view the course and send feedback whist viewing course content 
class ViewCourseDetailsTestCase(TestCase):
    def setUp(self):
        # Sets up two users and a course including a course content object with a feedback object to test all facets of the view
        self.client = Client()
        self.student_user = StudySphereUser.objects.create_user(username='testuser', password='testpassword', auth_level='student', email="student@test.com")
        self.teacher_user = StudySphereUser.objects.create_user(username='testuser2', password='testpassword', auth_level='student',email="teavhrt@test.com")
        self.course = Course.objects.create(name='Test Course', teacher=self.teacher_user)
        self.course_content = CourseContent.objects.create(course=self.course, title='Test Content', content_text='Test Content')
        self.feedback_text = 'Test feedback'
        self.feedback = CourseFeedback.objects.create(course=self.course, user=self.student_user, text=self.feedback_text)

    # Testing the case where an authenticated user accesses the view
    def test_view_course_details_authenticated_user_get(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('view', args=[self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Ensures that course & content are returned 
        self.assertContains(response, self.course.name)
        self.assertContains(response, self.course_content.title)

    # Testing the posting of Feedback
    def test_view_course_details_authenticated_user_post(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('view', args=[self.course.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200) # Ensures correct redirect

    # Tests the case where an unauthenticated user tries to use the view
    def test_view_course_details_unauthenticated_user(self):
        url = reverse('view', args=[self.course.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) 

# This tests the functionality of viewing course content
class ViewContentTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.student_user = StudySphereUser.objects.create_user(username='testuser', password='testpassword', auth_level='student', email="student@test.com")
        self.teacher_user = StudySphereUser.objects.create_user(username='testuser2', password='testpassword', auth_level='student',email="teavhrt@test.com")
        self.course = Course.objects.create(name='Test Course', teacher=self.teacher_user)
        self.content = CourseContent.objects.create(title='Test Content', content_text='Test Content', course=self.course)

    # Testing the case where a user tries to access course content
    def test_view_content_authenticated_user(self):
        self.client.login(username='testuser', password='testpassword')
        url = reverse('view_content', args=[self.content.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Verifies that content details are returned appropriately
        self.assertContains(response, self.content.title)
        self.assertContains(response, self.content.content_text)

    # Ensures that if a unauthenticated user tries to access the view that they are appropriately redirected
    def test_view_content_unauthenticated_user(self):
        url = reverse('view_content', args=[self.content.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302) 

# Tests the addition of course content
class AddCourseContentTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.student_user = StudySphereUser.objects.create_user(username='testuser', password='testpassword', auth_level='student', email="student@test.com")
        self.teacher_user = StudySphereUser.objects.create_user(username='testuser2', password='testpassword', auth_level='student',email="teavhrt@test.com")
        self.course = Course.objects.create(name='Test Course', teacher=self.teacher_user)
        self.content = CourseContent.objects.create(title='Test Content', content_text='Test Content', course=self.course)
        self.course.students.add(self.student_user)

    # This tests the form return when the GET method is used
    def test_add_course_content_get(self):
        self.client.force_login(self.teacher_user)
        url = reverse('add_course_content', args=[self.course.id])
        response = self.client.get(url)
        # Ensures that correct forms are returned in template
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['content_form'], CourseContentForm)
        self.assertIsInstance(response.context['deadline_form'], CourseDeadlineForm)

    # This tests the POST functionality of the view
    def test_add_course_content_post(self):
        self.client.force_login(self.teacher_user)
        url = reverse('add_course_content', args=[self.course.id])
        content_data = {
            'title': 'Test Content',
            'content': SimpleUploadedFile('test.txt', b'Test file content'),
        }
        deadline_data = {
            'deadline': '2024-03-31',
        }
        response = self.client.post(url, {**content_data, **deadline_data}, follow=True)
        # Ensures and verifies the addition of course content
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/courses/homepage/')
        self.assertTrue(CourseContent.objects.filter(title='Test Content').exists())
        self.assertTrue(CourseDeadline.objects.filter(deadline='2024-03-31').exists())

# This tests the posting of user status updates
class PostStatusUpdateTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.student_user = StudySphereUser.objects.create_user(username='testuser', password='testpassword', auth_level='student', email="student@test.com")

    # This tests the posting of status updates with valid data
    def test_post_status_update(self):
        form_data = {'status': 'Test status update'}
        request = self.factory.post(reverse('homepage'), data=form_data)
        request.user = self.student_user
        response = post_status_update(request)

    # This tests the posting of status updates with invalid data
    def test_post_status_update_invalid_form(self):
        form_data = {'status': ''}  # Invalid form data
        request = self.factory.post(reverse('homepage'), data=form_data)
        request.user = self.student_user
        response = post_status_update(request)
        self.assertEqual(response.status_code, 200)  # Expecting the same page to be rendered
    
    # This tests the return of all status updates
    def test_post_status_update_get_request(self):
        request = self.factory.get(reverse('homepage'))
        request.user = self.student_user
        response = post_status_update(request)
        self.assertEqual(response.status_code, 200)  # Expecting the same page to be rendered

# This tests the deletion of posts
class DeletePostTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = StudySphereUser.objects.create_user(username='testuser', password='testpassword', email='tester1@test.com')
        self.other_user = StudySphereUser.objects.create_user(username='otheruser', password='testpassword', email='tester2@test.com')
        self.post = Post.objects.create(user=self.user, text='Test post content')

    # This tests the deletion of a post as the creator of it
    def test_delete_post_as_owner(self):
        request = self.factory.post(reverse('delete_post', args=[self.post.id]))
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = delete_post(request, self.post.id)
        self.assertEqual(response.url, reverse('homepage'))

        # Ensures that post was successfully deleted
        self.assertEqual(messages._queued_messages[0].message, 'Post deleted successfully.')
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    # This tests if the post can be deleted by a non owner of the post
    def test_delete_post_as_non_owner(self):
        request = self.factory.post(reverse('delete_post', args=[self.post.id]))
        request.user = self.other_user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

        response = delete_post(request, self.post.id)
        self.assertEqual(response.url, reverse('homepage'))
        # Ensures that correct state is returned and that the post isn't in fact deleted
        self.assertEqual(messages._queued_messages[0].message, 'You do not have permission to delete this post.')
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    # This tests the case if the method used isn't valid
    def test_delete_post_invalid_method(self):
        request = self.factory.get(reverse('delete_post', args=[self.post.id]))
        request.user = self.user
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        # Ensures that the post isnt deleted
        response = delete_post(request, self.post.id)
        self.assertEqual(response.url, reverse('homepage'))
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

# Tests the posting of comments
class PostCommentTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = StudySphereUser.objects.create_user(username='testuser', password='testpassword', email='tester1@test.com')
        self.post = Post.objects.create(user=self.user, text='Test post content')

    # Tests the posting of a comment with and authenticated user
    def test_post_comment_authenticated_user(self):
        form_data = {'text': 'Test comment'}
        request = self.factory.post(reverse('post_comment', args=[self.post.id]), data=form_data)
        request.user = self.user
        response = post_comment(request, self.post.id)
        self.assertEqual(response.url, reverse('homepage'))
        # Ensures that comment is successfully posted on correct post
        self.assertTrue(Comment.objects.filter(user=self.user, post=self.post, text='Test comment').exists())

    # Tests the case when the comment form is filled with invalid data
    def test_post_comment_invalid_form(self):
        form_data = {'text': ''}  # Invalid form data
        request = self.factory.post(reverse('post_comment', args=[self.post.id]), data=form_data)
        request.user = self.user
        response = post_comment(request, self.post.id)
        self.assertEqual(response.url, reverse('homepage'))
        # Ensures that no entry is posted as a comment as data is invalid
        self.assertFalse(Comment.objects.filter(user=self.user, post=self.post).exists())

    # Tests the get method on the view
    def test_post_comment_get_request(self):
        request = self.factory.get(reverse('post_comment', args=[self.post.id]))
        request.user = self.user
        response = post_comment(request, self.post.id)
        self.assertEqual(response.url, reverse('homepage'))  # Ensures that homepage is returned with no error

        self.assertFalse(Comment.objects.filter(user=self.user, post=self.post).exists())

# Testing the leave feedback functionality
class LeaveFeedbackTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = StudySphereUser.objects.create_user(username='testuser', password='testpassword', email='tester1@test.com')
        self.course = Course.objects.create(name='Test Course', teacher=self.user)

    # Ensures that when a valid form is submitted that feedback is created
    def test_leave_feedback_valid_form(self):
        form_data = {'text': 'Test feedback'}
        request = self.factory.post(reverse('view', args=[self.course.id]), data=form_data)
        request.user = self.user
        response = leave_feedback(request, self.course)
        self.assertIsNone(response)
        # Verifies that Feedback is posted
        self.assertTrue(CourseFeedback.objects.filter(user=self.user, course=self.course, text='Test feedback').exists())

    # Ensures that if an invalid form is submitted that no feedback is left
    def test_leave_feedback_invalid_form(self):
        form_data = {'text': ''}  
        request = self.factory.post(reverse('view', args=[self.course.id]), data=form_data)
        request.user = self.user
        response = leave_feedback(request, self.course)
        self.assertIsInstance(response, dict)  # Expects form errors
        # Verifies that no feedback is created
        self.assertFalse(CourseFeedback.objects.filter(user=self.user, course=self.course).exists())  # No feedback should be saved with invalid form data

# This tests the submission functionality that all students will use when submitting their work
class CreateSubmissionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = StudySphereUser.objects.create_user(username='testuser', password='testpassword', email='tester1@test.com')
        self.content = CourseContent.objects.create(title='Test Content', content_text='Test Description')

    # Tests an authenticated user accessing the page
    def test_authenticated_user_accessing_page(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('submit', args=[self.content.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'create_submission.html')

    # Tests the case when an authenticated user submits their work in a valid format
    def test_authenticated_user_submit_valid_form(self):
        self.client.force_login(self.user)
        form_data = {'submission_text': 'Submission Title'} 
        response = self.client.post(reverse('submit', args=[self.content.id]), data=form_data)
        self.assertEqual(response.status_code, 302)  
        # Ensures that Submission is created
        self.assertTrue(Submission.objects.filter(submission_text='Submission Title').exists())
    
    # Tests the case when a user submits and invalid form
    def test_authenticated_user_submit_invalid_form(self):
        self.client.force_login(self.user)
        invalid_form_data = {'submission_text': '', 'file': ''}  # Test invalid form data
        response = self.client.post(reverse('submit', args=[self.content.id]), data=invalid_form_data)
        # Expects to be redirected
        self.assertEqual(response.status_code, 302)

    # Ensures that when an unauthenticated user accesses the page that they are redirected to the not authorized page
    def test_unauthenticated_user_accessing_page(self):
        response = self.client.get(reverse('submit', args=[self.content.id]))
        self.assertEqual(response.status_code, 302)

# This tests the view submissions page that is to be accessed by the teacher.
class ViewSubmissionsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher_user = StudySphereUser.objects.create_user(username='teacher', email='teacher@example.com', password='password', auth_level='teacher')
        self.student_user = StudySphereUser.objects.create_user(username='student', email='student@example.com', password='password', auth_level='student')
        self.content1 = CourseContent.objects.create(title='Test Content', content_text='Test Description')
        self.content2 = CourseContent.objects.create(title='Test Content', content_text='Test Description')
        self.submission1 = Submission.objects.create(submission_text='Submission 1', content=self.content1, student=self.student_user)
        self.submission2 = Submission.objects.create(submission_text='Submission 2', content=self.content2, student=self.student_user)

    # Tests the case when a teacher accesses the page
    def test_authenticated_teacher_accessing_page(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('view_submissions', args=[self.submission1.content.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_submissions.html')
        self.assertIn('submissions', response.context)
        # Ensures that the returned submissions are equal to the database
        self.assertQuerysetEqual(response.context['submissions'], Submission.objects.filter(content=self.submission1.content))

    # This tests the case when a student accesses the page
    def test_authenticated_student_accessing_page(self):
        self.client.force_login(self.student_user)
        # this ensures that the student isn't permitted to view all submissions
        response = self.client.get(reverse('view_submissions', args=[self.submission1.content.id]))
        self.assertEqual(response.status_code, 302)
        
    # This tests the case when an unauthenticated user accesses the page
    def test_unauthenticated_user_accessing_page(self):
        response = self.client.get(reverse('view_submissions', args=[self.submission1.content.id]))
        self.assertEqual(response.status_code, 302)  # Expects to be redirected

# This tests the view individual submission function
class ViewSubmissionViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher_user = StudySphereUser.objects.create_user(username='teacher', email='teacher@example.com', password='password', auth_level='teacher')
        self.student_user = StudySphereUser.objects.create_user(username='student', email='student@example.com', password='password', auth_level='student')
        self.content1 = CourseContent.objects.create(title='Test Content', content_text='Test Description')
        self.other_content = CourseContent.objects.create(title='Test Content2', content_text='Test Description')
        self.submission = Submission.objects.create(submission_text='Submission 1', content=self.content1, student=self.student_user)

    # tests the case where an authenticated teacher accesses the view submission page
    def test_authenticated_teacher_accessing_submission(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse('submission', args=[self.submission.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submission.html')
        # Ensures that correct submission is returned
        self.assertIn('submission', response.context)
        self.assertEqual(response.context['submission'], self.submission)

    # this tests the variation of this function where a student would access their own submission
    def test_authenticated_student_accessing_own_submission(self):
        self.client.force_login(self.student_user)
        response = self.client.get(reverse('submission', args=[self.submission.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submission.html')
        # This checks that the correct submission is returned
        self.assertIn('submission', response.context)
        self.assertEqual(response.context['submission'], self.submission)

    # This test case ensures that other students can access each others submissions
    def test_authenticated_student_accessing_other_student_submission(self):
        other_student = StudySphereUser.objects.create_user(username='other_student', email='other_student@example.com', password='password', auth_level='student')
        submission = Submission.objects.create(submission_text='Other Submission', content=self.other_content, student=other_student)
        self.client.force_login(self.student_user)
        # Ensures that submission isn't returned and that user is redirected
        response = self.client.get(reverse('submission', args=[submission.id]))
        self.assertEqual(response.status_code, 302)  
        
    # Ensures that unauthenticated users can't access user submissions
    def test_unauthenticated_user_accessing_submission(self):
        response = self.client.get(reverse('submission', args=[self.submission.id]))
        self.assertEqual(response.status_code, 302)  