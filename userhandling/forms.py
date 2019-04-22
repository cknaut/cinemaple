from django import forms
import datetime
from django.forms.utils import ErrorList
from django.contrib.auth.models import User
from .models import Profile
from .utils import  Mailgun

# TODO Think about Validators
class RegistrationForm(forms.Form):
    username = forms.CharField(label="",widget=forms.TextInput(attrs={'placeholder': 'Username','class':'form-control input-perso'}),max_length=30,min_length=3)
    email = forms.EmailField(label="",widget=forms.EmailInput(attrs={'placeholder': 'Email','class':'form-control input-perso'}),max_length=100,error_messages={'invalid': ("Email invalide.")})
    password1 = forms.CharField(label="",max_length=50,min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Password','class':'form-control input-perso'}))
    password2 = forms.CharField(label="",max_length=50,min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password','class':'form-control input-perso'}))

    #recaptcha = ReCaptchaField()

    #Override clean method to check password match
    def clean(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password1 != password2:
            self._errors['password2'] = ErrorList([u"Passwords don't match."])

        return self.cleaned_data

    #Override of save method for saving both User and Profile objects
    def save(self, datas):
        u = User.objects.create_user(datas['username'],
                                     datas['email'],
                                     datas['password1'])
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
        link="http://cinemaple.com/activate/"+datas['activation_key']

        sender_email    = "admin@cinemaple.com"
        sender_name     = "Cinemaple"
        subject         = "Please Verify Email"
        recipients      = [datas['email']]
        content         = "Please activate your email using the following link: " + link

        # Send message and retrieve status and return JSON object.
        status_code, r_json = mg.send_email(sender_email, sender_name, subject, recipients, content)
        assert status_code == 200, "Email Verification Email Failed"