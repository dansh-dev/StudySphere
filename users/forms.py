# forms.py

from django import forms
from .models import StudySphereUser

class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = StudySphereUser
        fields = ['username', 'email', 'first_name', 'last_name', 'bio', 'profile_picture']

    def clean_password2(self):
        # Check if the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = StudySphereUser
        fields = ['username', 'first_name', 'last_name', 'email', 'bio', 'profile_picture', 'auth_level']
        
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        # Make username unchangeable
        self.fields['username'].disabled = True
        self.fields['username'].widget.attrs['readonly'] = True
        # Make auth_level unchangeable
        self.fields['auth_level'].disabled = True