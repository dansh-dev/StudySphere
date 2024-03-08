from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .models import StudySphereUser

from users.forms import UserRegistrationForm, ProfileForm

# This is the function that logs in the user
def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        # Authenticates the user
        user = authenticate(request, username=username, password=password)
        # Verifies the user object
        if user is not None:
            login(request, user)
            # Redirects to homepage for further input from the user
            return redirect('/')
        else:
            messages.success(request, ("There was an error logging you in please try again"))
            return redirect('/users/login_user/')  
    else:
        return render(request, 'authentication/login.html', {})

# Logs out the current user
def logout_user(request):
    if request.method == "GET":
        logout(request)
        return redirect('/')
    
# This view allows for registration of users
def register_user(request):
    # In the case that the user POSTS the form
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        # Verifies validity of form
        if form.is_valid():
            profile_picture = request.FILES.get('profile-picture')
            # Sets the user object
            user = form.save()
            if profile_picture:
                user.profile_picture = profile_picture
                # Saves the user if all is verified
                user.save()
            # Logs in the user
            login(request, user)

            return redirect('/')  
        else:
            # In the case invalid data is entered
            errors = form.errors
            form = UserRegistrationForm()
            return render(request, "authentication/signup.html", {'errors': errors})

    else:
        return render(request, "authentication/signup.html")

# This is the profile function that returns the correct view
def profile(request):
    if request.method == "POST":
        pass
    else:
        return render(request, "authentication/profile.html")
    
# This function facilitates the view_profile view that is used whenever a searched user is accessed
def view_profile(request, user_id):
    if request.method == "POST":
        pass
    else:
        requested_user = StudySphereUser.objects.filter(id = user_id)
        return render(request, "authentication/view_user_profile.html", {'req_user': requested_user})
    
# This function facilitates the editing of a users profile
def edit_profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        # Verifies that new information is valid
        if form.is_valid():
            profile_picture = request.FILES.get('profile_picture')
            # If valid save the form
            user = form.save()
            if profile_picture:
                user.profile_picture = profile_picture
                # Sets necessary fields and saves the object
                user.save()     
            return redirect('profile')

        else:
            # If invalid data is sent return form including all errors
            errors = form.errors
            form = ProfileForm(instance=request.user)
            return render(request, 'authentication/edit_profile.html', {'form': form, 'errors':errors})
    else:
        # Returns edit profile page if method is GET
        form = ProfileForm(instance=request.user)
        return render(request, 'authentication/edit_profile.html', {'form': form})

