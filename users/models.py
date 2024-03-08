from django.db import models
from django.contrib.auth.models import AbstractUser
from PIL import Image


class StudySphereUser(AbstractUser):
    AUTH_LEVEL = (
        ('student', 'student'),
        ('teacher', 'teacher')
    )
    username = models.TextField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.TextField(max_length=20)
    last_name = models.TextField(max_length=20)
    auth_level = models.CharField(max_length=100, choices=AUTH_LEVEL, default='student')
    bio = models.TextField(max_length=1024)
    profile_picture = models.ImageField(default='default_profile.jpg', upload_to='profile_pictures')

    def __str__(self):
        return(self.username)
