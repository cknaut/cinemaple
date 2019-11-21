from django.contrib.auth.forms import PasswordChangeForm
from django import forms
import datetime
from django.utils import timezone
from django.forms.utils import ErrorList
from django.contrib.auth.models import User
from .models import Profile, Location,  PasswordReset, MovieNightEvent, VotePreference, Topping, LocationPermission
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.conf import settings
from django.core.mail import EmailMessage
from .utils import VerificationHash
from django.forms import ModelForm, formset_factory
from bootstrap_datepicker_plus import DateTimePickerInput
from django.utils.translation import gettext_lazy as _


# Code taken from https://stackoverflow.com/questions/24935271/django-custom-user-email-account-verification
class RegistrationForm(forms.Form):
    ''' Testing Flag used for calling form in testing setup in order to avoid recaptcha'''
    username = forms.CharField(label="", widget=forms.TextInput(
        attrs={'placeholder': 'Username', 'class': 'form-control input-perso'}), max_length=100)
    email = forms.EmailField(label="", widget=forms.EmailInput(attrs={
                             'placeholder': 'Email', 'class': 'form-control input-perso'}), max_length=100, error_messages={'invalid': ("Invalid Email.")})
    first_name = forms.CharField(label="", widget=forms.TextInput(
        attrs={'placeholder': 'Your first name', 'class': 'form-control input-perso'}), max_length=100)
    last_name = forms.CharField(label="", widget=forms.TextInput(
        attrs={'placeholder': 'Your last name', 'class': 'form-control input-perso'}), max_length=100)
    password1 = forms.CharField(label="", max_length=50, min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control input-perso'}))
    password2 = forms.CharField(label="", max_length=50, min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control input-perso'}))
    i_agree = forms.BooleanField()

    invitation_code = forms.CharField(label="", widget=forms.TextInput(
        attrs={'placeholder': 'Invitation Code', 'class': 'form-control input-perso'}), max_length=100)

    if not settings.DEBUG:
        captcha = ReCaptchaField(label="", widget=ReCaptchaV2Checkbox(
            attrs={'data-theme': 'light', 'data-size': 'normal'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            u'A user with username "%s" is already registered.' % username)

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(
            u'A user with email "%s" is already registered.' % email)

    def clean_i_agree(self):
        i_agree = self.cleaned_data.get('i_agree')
        if i_agree == False:
            raise forms.ValidationError("You must read and agree to Cinemaple's Privacy Policy.")

    def clean_invitation_code(self):
        invitation_code = self.cleaned_data.get('invitation_code')
        
        #Look for Location Permission Object
        try:
            loc_p = LocationPermission.objects.get(invitation_code=invitation_code)
            if loc_p.can_invite():
                return invitation_code
            else:
                raise forms.ValidationError("Invalid Invitation Code")

        except:
            raise forms.ValidationError("Invalid Invitation Code")

    # Override clean method to check password match
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
    
        if password1 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")

        return cleaned_data

    # Override of save method for saving both User and Profile objects
    def save(self, datas):
        u = User.objects.create_user(username=datas['username'],
                                     email=datas['email'],
                                     password=datas['password1'],
                                     first_name=datas['first_name'],
                                     last_name=datas['last_name'])
        u.is_active = False

        # Saving auto-creates profile
        u.save()

        u.profile.activation_key = datas['activation_key']
        u.profile.key_expires = datetime.datetime.strftime(
            datetime.datetime.now() + datetime.timedelta(days=2), "%Y-%m-%d %H:%M:%S")
        u.profile.save()


        location = LocationPermission.objects.get(invitation_code=datas["invitation_code"]).location
        invitor = LocationPermission.objects.get(invitation_code=datas["invitation_code"]).user

        lp = LocationPermission.objects.create(
            location = location,
            user = u, 
            invitor = invitor,
        )

        lp.save()

        #Notify Invitor about signup
        sender_email = "info@cinemaple.com"
        sender_name = "Cinemaple"
        subject = "Cinemaple User Signup with Your Link"
        recipients = [invitor.email]
        content = "Hi " + invitor.first_name + \
            ", {} {} has signed up on Cinemaple.com using your invitation link. If you know this person, no action is requried. If not, please let us know by responding to this email.".format(u.first_name, u.last_name)

        email = EmailMessage(subject, content, sender_name +
                             " <" + sender_email + ">", recipients)
        email.send()

        return u

    # Sending activation email
    def send_activation_email(self, datas):

        link = "http://www.cinemaple.com/activate/"+datas['activation_key']

        sender_email = "info@cinemaple.com"
        sender_name = "Cinemaple"
        subject = "Please Verify Email"
        recipients = [datas['email']]
        content = "Hi " + datas["first_name"] + \
            ", please activate your email using the following link: " + link

        email = EmailMessage(subject, content, sender_name +
                             " <" + sender_email + ">", recipients)
        email.send()


class LoginForm(forms.Form):
    username = forms.CharField(label="", widget=forms.TextInput(
        attrs={'placeholder': 'Username', 'class': 'form-control input-perso'}), max_length=100)
    password = forms.CharField(label="", max_length=50, min_length=6,
                               widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control input-perso'}))

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
            raise forms.ValidationError(
                u'User account is not activated, please verify email adress.')

        # if all checks passed, user should be valid:
        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="", widget=forms.EmailInput(attrs={
                             'placeholder': 'Email', 'class': 'form-control input-perso'}), max_length=100, error_messages={'invalid': ("Invalid Email.")})

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

            link = "http://www.cinemaple.com/reset/"+reset_key

            sender_email = "info@cinemaple.com"
            sender_name = "Cinemaple"
            subject = "Password Reset Link"
            recipients = [email]
            content = "Hi " + user.first_name + \
                ", please reset your password using the following link: " + link

            email_send = EmailMessage(
                subject, content, sender_name + " <" + sender_email + ">", recipients)
            email_send.send()
        return email


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(label="", max_length=50, min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'New Password', 'class': 'form-control input-perso'}))
    password2 = forms.CharField(label="", max_length=50, min_length=6,
                                widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new Password', 'class': 'form-control input-perso'}))

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
        fields = ['motto', 'description', 'date', 'location', 'MaxAttendence']
        labels = {
            'motto': _('Movie Night Motto'),
            'location': _('Location'),
            'description': _('Description:'),
            'date': _('Date:'),
        }

        location_choices = [location.name for location in Location.objects.all()]
        widgets = {
            'date': DateTimePickerInput(),  # default date-format %m/%d/%Y will be used
            'description': forms.TextInput(attrs={"id": "tinymice"}),
            'motto': forms.TextInput(attrs={'placeholder': '', 'class': 'form-control input-perso'}),
            'MaxAttendence': forms.NumberInput(attrs={'placeholder': '', 'class': 'form-control input-perso'}),
            'location': forms.Select(choices = location_choices, attrs={'placeholder': '', 'class': 'form-control input-perso'}),

        }

class MovieAddForm(forms.Form):

    movieID1 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieID2 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieID3 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieID4 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieID5 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieID6 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieID7 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieID8 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieID9 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieID10 = forms.CharField(required=False, widget=forms.HiddenInput())


class SneakymovienightIDForm(forms.Form):
    movienightid = forms.CharField(required=False, widget=forms.HiddenInput())


# forms.HiddenInput

class VotePreferenceForm(forms.Form):
    movieID = forms.IntegerField(widget=forms.HiddenInput())
    rating = forms.IntegerField(widget=forms.HiddenInput())


class ToppingForm(forms.Form):
    def __init__(self, movienight, *args, **kwargs):

        # retrieve available topping
        _, available_topings = movienight.get_topping_list()

        super(ToppingForm, self).__init__(*args, **kwargs)
        self.fields['toppings'] = forms.MultipleChoiceField(
            choices=[(o.id, str(o.topping)) for o in available_topings],
            widget=(forms.CheckboxSelectMultiple(
                attrs={"style": "list-style: none;"})),
            label='Select topping to bring:'
        )


class AlreadyBroughtToppingForm(forms.Form):
    def __init__(self, movienight, *args, **kwargs):

        # retrieve available topping
        un_available_toppings, _ = movienight.get_topping_list()

        super(AlreadyBroughtToppingForm, self).__init__(*args, **kwargs)
        self.fields['toppings'] = forms.MultipleChoiceField(
            choices=[(o.id, str(o.topping)) for o in un_available_toppings],
            widget=(forms.CheckboxSelectMultiple(
                attrs={"checked": "", "class": "listnobullets"},)),
            label='Toppings already brought along:',
            disabled=True,
        )


class ToppingAddForm(ModelForm):
    class Meta:
        model = Topping
        fields = ['topping']
        widgets = {
            'topping': forms.TextInput(attrs={'placeholder': '', 'class': 'form-control input-perso'})
        }


class MyPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={'placeholder': 'Old password', 'class': 'form-control input-perso'})
        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={'placeholder': 'New password', 'class': 'form-control input-perso'})
        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={'placeholder': 'Confirm new password', 'class': 'form-control input-perso'})


class ProfileUpdateForm(ModelForm):

    def clean_email(self):
        email = self.cleaned_data['email']
        username = self.cleaned_data['username']

        # if new email entered: Make sure no user already has it
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email

        # if instanticated form is called, don't raise error if email is current email
        user = User.objects.get(email=email)
        thisuser = User.objects.get(username=username)

        if user == thisuser:
            return email

        raise forms.ValidationError(
            u'A user with email "%s" is already registered.' % email)

    #remove helper text (thanks https://stackoverflow.com/questions/13202845/removing-help-text-from-django-usercreateform )
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)

        for fieldname in ['username', 'first_name', 'last_name', 'email']:
            self.fields[fieldname].help_text = None



    # Sending activation email
    def send_activation_new_email(self, datas):

        link = "http://www.cinemaple.com/activate/update_email/"+datas['activation_key']

        sender_email = "info@cinemaple.com"
        sender_name = "Cinemaple"
        subject = "Please Verify Email"
        recipients = [datas['email']]
        content = "Hi " + datas["first_name"] + \
            ", please activate your email using the following link: " + link

        email = EmailMessage(subject, content, sender_name +
                             " <" + sender_email + ">", recipients)
        email.send()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': '', 'class': 'form-control input-perso', 'readonly':'readonly'}),
            'first_name': forms.TextInput(attrs={'placeholder': '', 'class': 'form-control input-perso'}),
            'last_name': forms.TextInput(attrs={'placeholder': '', 'class': 'form-control input-perso'}),
            'email': forms.TextInput(attrs={'placeholder': '', 'class': 'form-control input-perso'})
        }

ROLE_CHOICES = [
('HO', 'Host'),
('AM', 'Ambassador'),
('GU', 'Guest'),
('RW', 'Revoked Access'),
]
class PermissionsChangeForm(ModelForm):
    class Meta:
        model = LocationPermission
        fields = ['role']
        widgets = {
            'role':  forms.Select(choices = ROLE_CHOICES, attrs={'placeholder': '', 'class': 'form-control input-perso'}),
        }
