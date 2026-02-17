import datetime

from bootstrap_datepicker_plus import DateTimePickerInput
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox
from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.mail import EmailMultiAlternatives
from django.db.utils import OperationalError
from django.forms import ModelForm
from django.forms.utils import ErrorList
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from .models import (Location, LocationPermission, MovieNightEvent,
                     PasswordReset, Topping)
from .utils import VerificationHash


class DivErrorList(ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''
        return ''.join(['<div class="errorlist">%s</div>' % e for e in self])


# Code taken from \
# https://stackoverflow.com/questions/24935271/django-custom-user-email-account-verification

# Testing Flag used for calling form in testing \
# setup in order to avoid recaptcha
class RegistrationForm(forms.Form):
    username = forms.CharField(
        label="",
        validators=[UnicodeUsernameValidator()],
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Username',
                'class': 'form-control input-perso'
            }
        ),
        max_length=150)

    email = forms.EmailField(
        label="",
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Email',
                'class': 'form-control input-perso'
            }
        ),
        max_length=100,
        error_messages={
            'invalid': ("Invalid Email.")
        }
    )

    first_name = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Your first name',
                'class': 'form-control input-perso'
            }
        ),
        max_length=100
    )

    last_name = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Your last name',
                'class': 'form-control input-perso'
            }
        ),
        max_length=100
    )

    password1 = forms.CharField(
        label="",
        max_length=50,
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password',
                'class': 'form-control input-perso'
            }
        )
    )

    password2 = forms.CharField(
        label="",
        max_length=50,
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Confirm Password',
                'class': 'form-control input-perso'
            }
        )
    )

    i_agree = forms.BooleanField()

    invitation_code = forms.CharField(
        label="",
        widget=forms.HiddenInput(),
        max_length=100
    )

    if not settings.DEBUG:
        captcha = ReCaptchaField(label="", widget=ReCaptchaV2Checkbox(
            attrs={'data-theme': 'light', 'data-size': 'normal'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError(
            u'A user with username "%s" is already registered.' % username)

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(
            u'A user with email "%s" is already registered.' % email)

    def clean_i_agree(self):
        i_agree = self.cleaned_data.get('i_agree')
        if i_agree is False:
            raise forms.ValidationError(
                "You must read and agree to Cinemaple's Privacy Policy."
            )

    def clean_invitation_code(self):
        invitation_code = self.cleaned_data.get('invitation_code')

        # Look for Location Permission Object
        try:
            loc_p = LocationPermission.objects.get(
                invitation_code=invitation_code
            )
            if loc_p.can_invite():
                return invitation_code
            else:
                raise forms.ValidationError("Invalid Invitation Code")

        except loc_p.DoesNotExist:
            raise forms.ValidationError("Invalid Invitation Code")

    # Override clean method to check password match
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

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
            datetime.datetime.now() + datetime.timedelta(days=2),
            "%Y-%m-%d %H:%M:%S"
        )
        u.profile.save()

        location = LocationPermission.objects.get(
            invitation_code=datas["invitation_code"]
        ).location
        invitor = LocationPermission.objects.get(
            invitation_code=datas["invitation_code"]
        ).user

        lp = LocationPermission.objects.create(
            location=location,
            user=u,
            inviter=invitor,
        )

        lp.save()

        # Add revoke access hash by feeding LocationPermission id as seed
        vh = VerificationHash()
        revoke_access_hash = vh.gen_rev_access_hash(lp.id)
        lp.rev_access_hash = revoke_access_hash
        lp.save()

        # Notify Invitor about signup
        sender_email = "info@cinemaple.com"
        sender_name = "Cinemaple"
        subject = "Cinemaple User Signup with Your Link"
        recipients = [invitor.email]
        context_email = {
            'invitor'           : invitor,
            'u'                 : u,
            'location'          : location,
            'rev_access_hash'   : revoke_access_hash
        }
        content = render_to_string(
            "userhandling/emails/cinemaple_email_invite_guest.html",
            context_email
        )

        email = EmailMultiAlternatives(
            subject,
            '',
            sender_name + " <" + sender_email + ">",
            recipients
        )

        email.attach_alternative(content, "text/html")
        email.send()

        return u

    # Sending activation email
    def send_activation_email(self, datas):

        link = "http://www.cinemaple.com/activate/" + datas['activation_key']

        sender_email = "info@cinemaple.com"
        sender_name = "Cinemaple"
        subject = "Please Verify Email"
        recipients = [datas['email']]

        context_email = {
            'firstname'    : datas["first_name"],
            'link'   : link
        }
        content = render_to_string(
            "userhandling/emails/cinemaple_email_activate.html",
            context_email
        )

        email = EmailMultiAlternatives(
            subject,
            '',
            sender_name + " <" + sender_email + ">",
            recipients
        )

        email.attach_alternative(content, "text/html")
        email.send()


class LoginForm(forms.Form):
    username = forms.CharField(
        label="",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Username',
                'class': 'form-control input-perso'
            }
        ),
        max_length=100
    )

    password = forms.CharField(
        label="",
        max_length=50,
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password',
                'class': 'form-control input-perso'
            }
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        # Check if user exists.
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError(u'Invalid login data.')

        # Check if password mathes.
        # Note that we return the same error message for every login error.\
        #  This way, it is not possible to poll the \
        #  site for existing usernames.
        if not user.check_password(password):
            raise forms.ValidationError(u'Invalid login data.')

        # Check if user is valid
        if not user.is_active:
            raise forms.ValidationError(
                u'User account is not activated, please verify email adress.')

        # if all checks passed, user should be valid:
        return cleaned_data


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        label="",
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Email',
                'class': 'form-control input-perso'
            }
        ),
        max_length=100,
        error_messages={
            'invalid': ("Invalid Email.")
        }
    )

    def populate_passwordreset_send_email(self):
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

            link = "http://www.cinemaple.com/reset/" + reset_key

            sender_email = "info@cinemaple.com"
            sender_name = "Cinemaple"
            subject = "Password Reset Link"
            recipients = [email]
            context_email = {
                'firstname'     : user.first_name,
                'link'          : link
            }
            content = render_to_string(
                "userhandling/emails/cinemaple_email_pw_reset.html",
                context_email
            )

            email_send = EmailMultiAlternatives(
                subject,
                '',
                sender_name + " <" + sender_email + ">",
                recipients
            )

            email_send.attach_alternative(content, "text/html")
            email_send.send()
        return email


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label="",
        max_length=50,
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'New Password',
                'class': 'form-control input-perso'
            }
        )
    )

    password2 = forms.CharField(
        label="",
        max_length=50,
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Confirm new Password',
                'class': 'form-control input-perso'
            }
        )
    )

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password1 != password2:
            # self.error_class=DivErrorList
            self.add_error("password1", 'Passwords do not match.')
            self.add_error("password2", "Passwords do not match.")
            # self.as_p()

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

        # in order to avoid problems arising from starting from scratch
        try:
            location_choices = [location.name for location
                                in Location.objects.all()]
            widgets = {
                # default date-format %m/%d/%Y will be used
                'date': DateTimePickerInput(),
                'description': forms.TextInput(
                    attrs={
                        "id": "tinymice"
                    }
                ),
                'motto': forms.TextInput(
                    attrs={
                        'placeholder': '',
                        'class': 'form-control input-perso'
                    }
                ),
                'MaxAttendence': forms.NumberInput(
                    attrs={
                        'placeholder': '',
                        'class': 'form-control input-perso'
                    }
                ),
                'location': forms.Select(
                    choices=location_choices,
                    attrs={
                        'placeholder': '',
                        'class': 'form-control input-perso'
                    }
                ),
            }
        except OperationalError:
            pass


class MovieAddForm(forms.Form):

    movieid1 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieid2 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieid3 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieid4 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieid5 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieid6 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieid7 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieid8 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieid9 = forms.CharField(required=False, widget=forms.HiddenInput())
    movieid10 = forms.CharField(required=False, widget=forms.HiddenInput())


class SneakymovienightIDForm(forms.Form):
    movienightid = forms.CharField(required=False, widget=forms.HiddenInput())


# forms.HiddenInput

class VotePreferenceForm(forms.Form):
    movieid = forms.IntegerField(widget=forms.HiddenInput())
    rating = forms.IntegerField(widget=forms.HiddenInput())


class ToppingForm(forms.Form):
    def __init__(self, movienight, *args, **kwargs):

        # retrieve available topping
        _, available_topings = movienight.get_topping_list()

        super(ToppingForm, self).__init__(*args, **kwargs)
        self.fields['toppings'] = forms.MultipleChoiceField(
            choices=[(o.id, str(o.topping)) for o in available_topings],
            widget=(forms.CheckboxSelectMultiple(
                attrs={"style": "list-style: none"})),
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
            'topping': forms.TextInput(
                attrs={
                    'placeholder': '',
                    'class': 'form-control input-perso'
                }
            )
        }


class MyPasswordChangeForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super(MyPasswordChangeForm, self).__init__(*args, **kwargs)

        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={
                'placeholder': 'Old password',
                'class': 'form-control input-perso'
            }
        )

        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={
                'placeholder': 'New password',
                'class': 'form-control input-perso'
            }
        )

        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={
                'placeholder': 'Confirm new password',
                'class': 'form-control input-perso'
            }
        )


class ProfileUpdateForm(ModelForm):

    def clean_email(self):
        email = self.cleaned_data['email']
        username = self.cleaned_data['username']

        # if new email entered: Make sure no user already has it
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email

        # if instanticated form is called, don't raise \
        # error if email is current email
        user = User.objects.get(email=email)
        thisuser = User.objects.get(username=username)

        if user == thisuser:
            return email

        raise forms.ValidationError(
            u'A user with email "%s" is already registered.' % email)

    # remove helper text (thanks \
    # https://stackoverflow.com/questions/13202845/ \
    # removing-help-text-from-django-usercreateform )
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)

        for fieldname in ['username', 'first_name', 'last_name', 'email']:
            self.fields[fieldname].help_text = None

    # Sending activation email
    def send_activation_new_email(self, datas):

        link = "http://www.cinemaple.com/activate/update_email/"\
               + datas['activation_key']

        sender_email = "info@cinemaple.com"
        sender_name = "Cinemaple"
        subject = "Email Verification"
        recipients = [datas['email']]
        context_email = {
            'firstname'    : datas["first_name"],
            'link'   : link
        }
        content = render_to_string(
            "userhandling/emails/cinemaple_email_activate.html",
            context_email
        )

        email = EmailMultiAlternatives(
            subject,
            '',
            sender_name + " <" + sender_email + ">",
            recipients
        )

        email.attach_alternative(content, "text/html")
        email.send()

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(
                attrs={
                    'placeholder': '',
                    'class': 'form-control input-perso',
                    'readonly': 'readonly'
                }
            ),
            'first_name': forms.TextInput(
                attrs={
                    'placeholder': '',
                    'class': 'form-control input-perso'
                }
            ),
            'last_name': forms.TextInput(
                attrs={
                    'placeholder': '',
                    'class': 'form-control input-perso'
                }
            ),
            'email': forms.TextInput(
                attrs={
                    'placeholder': '',
                    'class': 'form-control input-perso'
                }
            )
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
            'role': forms.Select(
                choices=ROLE_CHOICES,
                attrs={
                    'placeholder': '',
                    'class': 'form-control input-perso'
                }
            ),
        }
