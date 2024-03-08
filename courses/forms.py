from django import forms
from .models import Course, Post, Comment, CourseContent, Submission, CourseDeadline, CourseFeedback

#  These forms are defined to set the rules for user input and provide validation and errors.

# This form facilitates the creation of Courses
class CourseCreationForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'banner_image']

# This form facilitates the editing of a Course
class CourseEditForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'banner_image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

# Submission form that facilitates students submitting their work
class CourseContentSubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['submission_text', 'submission_image', 'pdf_files']

#  This form creates Content on a course
class CourseContentForm(forms.ModelForm):
    class Meta:
        model = CourseContent
        fields = ['title', 'content_text', 'content_image', 'pdf_files']

# This form used in conjunction with the CourseContent form allows for deadlines to be set for content
class CourseDeadlineForm(forms.ModelForm):
    class Meta:
        model = CourseDeadline
        fields = ['deadline']

# Form where students and teachers post status updates
class StatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 1, 'placeholder': 'What\'s on your mind?'}),
        }

# Creation of a comment on a status update
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter your comment'}),
        }

# creation of feedback on a course
class CourseFeedbackForm(forms.ModelForm):
    class Meta:
        model = CourseFeedback
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 1, 'placeholder': 'Do you have any feedback for this course?'}),
        }

#  Search for users
class UserSearchForm(forms.Form):
    query = forms.CharField(label='Search Users', max_length=100)