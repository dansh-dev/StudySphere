from django.test import TestCase, Client
from django.urls import reverse
from .models import StudySphereUser
from .forms import UserRegistrationForm

# Tests the login functionality of the application
class LoginUserViewTest(TestCase):
    # Sets up a user
    def setUp(self):
        self.client = Client()
        self.user = StudySphereUser.objects.create(username='testuser', email='testuser@example.com', password='password')

    # Tests the login functionality
    def test_login_successful(self):
        response = self.client.post(reverse('login_user'), {'username': 'testuser', 'password': 'password'})
        self.assertEqual(response.status_code, 302) 

    # Test the case login is unsuccessful
    def test_login_unsuccessful(self):
        response = self.client.post(reverse('login_user'), {'username': 'testuser', 'password': 'wrong_password'})
        # Expects the redirect
        self.assertEqual(response.status_code, 302) 

    # Test the case where login page is requested
    def test_get_login_page(self):
        response = self.client.get(reverse('login_user'))
        self.assertTemplateUsed(response, 'authentication/login.html')
        self.assertEqual(response.status_code, 200)  

# Tests the logout functionality
class LogoutUserViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = StudySphereUser.objects.create(username='testuser', email='testuser@example.com', password='password')
        self.client.login(username='testuser', password='password')

    # Testing the case where a user successfully logs out
    def test_logout_successful(self):
        response = self.client.get(reverse('logout_user'))
        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertRedirects(response, '/')

    # Tests the case where the user isn't authenticated, should just redirect
    def test_user_not_authenticated(self):
        self.client.logout()  # Log out the user
        response = self.client.get(reverse('logout_user'))
        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertRedirects(response, '/')

# Testing the registration of a user
class RegisterUserViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    # Testing successful user registration
    def test_register_user_successful(self):
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
        }
        response = self.client.post(reverse('signup_user'), data)
        self.assertEqual(response.status_code, 200)  # Redirect status code

    # Testing the case where a user registers using invalid data
    def test_register_user_invalid_form(self):
        invalid_data = {
            'username': 'testuser',
            'email': 'invalid_email', 
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
        }
        response = self.client.post(reverse('signup_user'), invalid_data)
        self.assertEqual(response.status_code, 200)  # Remains on same page as errors need to be displayed
        self.assertTemplateUsed(response, 'authentication/signup.html')

    # Testing the GET method on the register form - should just return the page with the form
    def test_register_user_get_request(self):
        response = self.client.get(reverse('signup_user'))
        self.assertEqual(response.status_code, 200)  # Successful GET request
        self.assertTemplateUsed(response, 'authentication/signup.html')
