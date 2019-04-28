from django import forms
import datetime
from django.forms.utils import ErrorList
from django.contrib.auth.models import User
from .models import Profile
from .utils import  Mailgun
from captcha.fields import ReCaptchaField
from django.conf import settings

# TODO Think about Validators
# Code taken from https://stackoverflow.com/questions/24935271/django-custom-user-email-account-verification
class RegistrationForm(forms.Form):
    email = forms.EmailField(label="",widget=forms.EmailInput(attrs={'placeholder': 'Email','class':'form-control input-perso'}),max_length=100,error_messages={'invalid': ("Invalid Email.")})
    first_name =  forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder': 'Your first name','class':'form-control input-perso'}),max_length=100)
    last_name =  forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder': 'Your last name','class':'form-control input-perso'}),max_length=100)
    password1 = forms.CharField(label="",max_length=50,min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Password','class':'form-control input-perso'}))
    password2 = forms.CharField(label="",max_length=50,min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password','class':'form-control input-perso'}))

    if not settings.DEBUG:
        captcha = ReCaptchaField()

    def clean_email(self):
        username = self.cleaned_data['email']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(u'A user with email "%s" is already registered.' % username)

    #Override clean method to check password match
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")

        return cleaned_data

    #Override of save method for saving both User and Profile objects
    def save(self, datas):
        u = User.objects.create_user(username = datas['email'],
                                     email = datas['email'],
                                     password = datas['password1'],
                                     first_name = datas['first_name'],
                                     last_name = datas['last_name'])
        u.is_active = False

        # Saving auto-creates profile
        u.save()

        u.profile.activation_key=datas['activation_key']
        u.profile.key_expires=datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=2), "%Y-%m-%d %H:%M:%S")
        u.profile.save()
        return u

    #Sending activation email
    def send_activation_email(self, datas):
        mg = Mailgun()
        link="http://www.cinemaple.com/activate/"+datas['activation_key']

        sender_email    = "admin@cinemaple.com"
        sender_name     = "Cinemaple"
        subject         = "Please Verify Email"
        recipients      = [datas['email']]
        content         = "Please activate your email using the following link: " + link

        # Send message and retrieve status and return JSON object.
        status_code, r_json = mg.send_email(sender_email, sender_name, subject, recipients, content)
        assert status_code == 200, "Email Verification Email Failed"