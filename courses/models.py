from django.db import models
from users.models import StudySphereUser

# This models each course defined by teachers
class Course(models.Model):
    name = models.CharField(max_length=100) # Name of the course
    description = models.TextField() # A description on what will be learnt / taught
    banner_image = models.FileField(default='default_banner_image.jpg', upload_to='course_banners') # A banner image field
    teacher = models.ForeignKey(StudySphereUser, on_delete=models.CASCADE, related_name='courses_taught') # The teacher of the course
    students = models.ManyToManyField(StudySphereUser, related_name='enrolled_courses') # All students currently enrolled in the course

    def __str__(self):
        return self.name

# This models content for course content
class CourseContent(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='content', null=True) # Course relationship between content
    title = models.CharField(max_length=100) # Title of the content EG. English Essay
    content_text = models.TextField(blank=True, null=True) # Text of the content EG. Write an essay - 2000 words.
    content_image = models.ImageField(blank=True, null=True) # Image that the content will display EG. Diagram
    pdf_files = models.FileField(upload_to='course_pdfs', null=True, blank=True) # PDF file that students can download.

    def __str__(self):
        return self.title

# This models deadlines for each course content
class CourseDeadline(models.Model):
    content = models.ForeignKey(CourseContent, on_delete=models.CASCADE) # Relationship to CourseContent
    deadline = models.DateTimeField() # Deadline for each course content

# Models each post made by the users
class Post(models.Model):
    user = models.ForeignKey(StudySphereUser, on_delete=models.CASCADE) # Relationship to the User that creates the post
    text = models.TextField() # Post text EG. Welcome to the Platform!
    created_at = models.DateTimeField(auto_now_add=True) # Date - Time when post was made.

    def __str__(self):
        return f"Post by {self.user.username} at {self.created_at}"

# Models comments made on posts
class Comment(models.Model):
    user = models.ForeignKey(StudySphereUser, on_delete=models.CASCADE) # Defines the user that makes the comment
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments') # Relationship to the original post
    text = models.TextField() # Text that the comment contains
    created_at = models.DateTimeField(auto_now_add=True) # Date - Time when comment was made created

    def __str__(self):
        return f"Comment by {self.user.username} on post '{self.post}' at {self.created_at}"
    
# Models each Feedback that students leave
class CourseFeedback(models.Model):
    user = models.ForeignKey(StudySphereUser, on_delete=models.CASCADE) # Relationship to the user that created it
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='feedback') # Relationship to the course
    text = models.TextField() # Text that the feedback contains EG. Love this course!
    created_at = models.DateTimeField(auto_now_add=True) # Date - Time created at

    def __str__(self):
        return f"Feedback by {self.user.username} on course '{self.course}' at {self.created_at}"
    
# Models each student submission for each content
class Submission(models.Model):
    student = models.ForeignKey(StudySphereUser, on_delete=models.CASCADE) # Student relationship
    content = models.ForeignKey(CourseContent, on_delete=models.CASCADE) # Relationship to the content that submission was made on
    submission_text = models.TextField(blank=True, null=True) # Text that a student can submit
    submission_image = models.ImageField(blank=True, null=True) # Image that the user could submit EG. Work diagrams
    pdf_files = models.FileField(upload_to='submission_pdfs', null=True, blank=True) # PDF file that a user could submit EG. Work document
    submitted_at = models.DateTimeField(auto_now_add=True) # Date - Time submitted at

# Models a notification when new content is added
class NotificationContent(models.Model):
    student = models.ForeignKey(StudySphereUser, on_delete=models.CASCADE) # Relationship to the student that is to receive the notification
    course_content = models.ForeignKey(CourseContent, on_delete=models.CASCADE) # Relationship to the course content
    created_at = models.DateTimeField(auto_now_add=True) # Date - Time created at

# Models a notification when student is enrolled into course
class NotificationEnroll(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE) # The relationship to the course that the student enrolled to
    student = models.ForeignKey(StudySphereUser, null=True, on_delete=models.CASCADE, related_name='enrolled_student') # relationship to the student that enrolled
    teacher = models.ForeignKey(StudySphereUser, null=True, on_delete=models.CASCADE, related_name='enrolled_teacher') # relationship to the teacher that created the course
    enrolled_at = models.DateTimeField(auto_now_add=True) # Date - Time created at