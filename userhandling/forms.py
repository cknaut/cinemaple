from django import forms
import datetime
from django.utils import timezone
from django.forms.utils import ErrorList
from django.contrib.auth.models import User
from .models import Profile, PasswordReset, MovieNightEvent
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.conf import settings
from django.core.mail import EmailMessage
from .utils import VerificationHash
from django.forms import ModelForm
from bootstrap_datepicker_plus import DateTimePickerInput
from django.utils.translation import gettext_lazy as _



# Code taken from https://stackoverflow.com/questions/24935271/django-custom-user-email-account-verification
class RegistrationForm(forms.Form):
    ''' Testing Flag used for calling form in testing setup in order to avoid recaptcha'''
    username =  forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder': 'Username','class':'form-control input-perso'}),max_length=100)
    email = forms.EmailField(label="",widget=forms.EmailInput(attrs={'placeholder': 'Email','class':'form-control input-perso'}),max_length=100,error_messages={'invalid': ("Invalid Email.")})
    first_name =  forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder': 'Your first name','class':'form-control input-perso'}),max_length=100)
    last_name =  forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder': 'Your last name','class':'form-control input-perso'}),max_length=100)
    password1 = forms.CharField(label="",max_length=50,min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Password','class':'form-control input-perso'}))
    password2 = forms.CharField(label="",max_length=50,min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password','class':'form-control input-perso'}))

    if not settings.DEBUG:
        captcha = ReCaptchaField(label="", widget=ReCaptchaV2Checkbox(attrs={'data-theme': 'light', 'data-size': 'normal'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(u'A user with username "%s" is already registered.' % username)

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(u'A user with email "%s" is already registered.' % email)

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
        u = User.objects.create_user(username = datas['username'],
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

        link="http://www.cinemaple.com/activate/"+datas['activation_key']

        sender_email    = "admin@cinemaple.com"
        sender_name     = "Cinemaple"
        subject         = "Please Verify Email"
        recipients      = [datas['email']]
        content         = "Hi " + datas["first_name"] + ", please activate your email using the following link: " + link

        email = EmailMessage(subject,content, sender_name + " <" + sender_email + ">", recipients)
        email.send()

class LoginForm(forms.Form):
   username =  forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder': 'Username','class':'form-control input-perso'}),max_length=100)
   password = forms.CharField(label="",max_length=50,min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Password','class':'form-control input-perso'}))
   def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        # Check if user exists.
        try:
            user = User.objects.get(username=username)
        except:
            raise forms.ValidationError(u'Invalid login data.')

        # Check if password mathes.
        # NOoe that we return the same error message for every login error. This way, it is not possible to poll the site for existing usernames.
        if not user.check_password(password):
            raise forms.ValidationError(u'Invalid login data.')

        # Check if user is valid
        if not user.is_active:
            raise forms.ValidationError(u'User account is not activated, please verify email adress.')

        # if all checks passed, user should be valid:
        return cleaned_data

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="",widget=forms.EmailInput(attrs={'placeholder': 'Email','class':'form-control input-perso'}),max_length=100,error_messages={'invalid': ("Invalid Email.")})

    def populate_PasswordReset_send_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            userexists = True
        except User.DoesNotExist:
            userexists = False

        if userexists:
            # initiate password reste model
            username = user.username

            # generate reset hash
            vh = VerificationHash()
            reset_key = vh.gen_pw_hash(username)

            # save model
            pr = PasswordReset(username=username, reset_key=reset_key)
            pr.save()

            link="http://www.cinemaple.com/reset/"+reset_key

            sender_email    = "admin@cinemaple.com"
            sender_name     = "Cinemaple"
            subject         = "Password Reset Link"
            recipients      = [email]
            content         = "Hi " + user.first_name + ", please reset your password using the following link: " + link

            email_send = EmailMessage(subject,content, sender_name + " <" + sender_email + ">", recipients)
            email_send.send()
        return email

class PasswordResetForm(forms.Form):
    password1 = forms.CharField(label="",max_length=50,min_length=6,
                            widget=forms.PasswordInput(attrs={'placeholder': 'New Password','class':'form-control input-perso'}))
    password2 = forms.CharField(label="",max_length=50,min_length=6,
                            widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new Password','class':'form-control input-perso'}))

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")

        return cleaned_data

class MoveNightForm(ModelForm):
    class Meta:
        model = MovieNightEvent
        fields = ['motto', 'description', 'date']
        labels = {
            'motto': _('Movie Night Motto'),
            'description': _('Description:'),
            'date': _('Date:'),
        }
        widgets = {
             'date': DateTimePickerInput(), # default date-format %m/%d/%Y will be used
             'description': forms.TextInput(attrs={"id": "tinymice"}),
             'motto' : forms.TextInput(attrs={'placeholder': '','class':'form-control input-perso'})

         }

class MovieAddForm(forms.Form):

    movieID1    = forms.CharField(required=False, widget = forms.HiddenInput())
    movieID2    = forms.CharField(required=False, widget = forms.HiddenInput())
    movieID3    = forms.CharField(required=False, widget = forms.HiddenInput())
    movieID4    = forms.CharField(required=False, widget = forms.HiddenInput())
    movieID5    = forms.CharField(required=False, widget = forms.HiddenInput())
    movieID6    = forms.CharField(required=False, widget = forms.HiddenInput())
    movieID7    = forms.CharField(required=False, widget = forms.HiddenInput())
    movieID8    = forms.CharField(required=False, widget = forms.HiddenInput())
    movieID9    = forms.CharField(required=False, widget = forms.HiddenInput())
    movieID10   = forms.CharField(required=False, widget = forms.HiddenInput())

class SneakymovienightIDForm(forms.Form):
    movienightid    = forms.CharField(required=False, widget = forms.HiddenInput())


# forms.HiddenInput()