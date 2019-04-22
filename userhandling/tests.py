from django.test import TestCase
from django.shortcuts import get_object_or_404
from .utils import Mailchimp, Mailgun
from django.contrib.auth.models import User
import random
import urllib, json
import string
from .forms import *
from django.conf import settings


# Test Mailchimp Class: Subscribe and unsubscribe test email

class MailchimpSubscribeTest(TestCase):

    # random test email
    test_email =  ''.join(random.choices(string.ascii_uppercase + string.digits, k=5)) + "@cinemaple.com"

    # TODO: Add delay to subscribe welcome email to prevent triggering by tests.
    def subscribeemail(self):
        """
        Checks if Mailchimp subscription works
        """
        mc = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID_TEST)
        mc.add_email(self.test_email)
        self.assertEqual(mc.check_subscription_status(self.test_email)[1]["status"], "subscribed")

    def unsubscribeemail(self):
        """
        Checks if Mailchimp unsubscription works
        """
        mc = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID_TEST)
        mc.unsubscribe(self.test_email)
        self.assertEqual(mc.check_subscription_status(self.test_email)[1]["status"], "unsubscribed")

    def test_all(self):
        """
        Run tests
        """
        self.subscribeemail()
        self.unsubscribeemail()

class omdb_check(TestCase):

    check_imdb_id = 'tt0110912'
    check_title = 'Pulp Fiction'

    def test_retrieveOMDB_record(self):
        """
        Retrieves record from OMDB and checks whether title is correct.
        """
        args = {"apikey": settings.OMDB_API_KEY, "i": self.check_imdb_id, "plot" : "full"}
        url_api = " http://www.omdbapi.com/?{}".format(urllib.parse.urlencode(args))

        # Load Return Object Into JSON
        try:
            with urllib.request.urlopen(url_api) as url:
                data = json.loads(url.read().decode())
        except:
            raise Exception("{} is not valid IMDB ID")

        self.assertEqual(data["Title"], self.check_title)

class Mailgun_check(TestCase):

    def test_send_mg_email(self):
        """
        Send email and checks if status is ok.
        """
        mg = Mailgun()

        sender_email    = "mg_test@cinemaple.com"
        sender_name     = "Cinemaple Mailgun Test"
        subject         = "Cinemaple Mailgun Test"
        recipients      = ["mg_test@cinemaple.com", "can.knaut@gmail.com"]
        content         = "This is a test email!"

        # Send message and retrieve status and return JSON object.
        status_code, r_json = mg.send_email(sender_email, sender_name, subject, recipients, content)

        # Check if everything went ok.
        self.assertEqual(status_code, 200)
        self.assertEqual(r_json['message'], 'Queued. Thank you.')


class Email_Verification_Check(TestCase):

    # random username
    randuser = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    # Valid Form Data
    def UserForm_valid(self, data):
        form = RegistrationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_register_user(self):
        data = {
        'username'  : self.randuser,
        'email'     : 'testuser@cinemaple.com',
        'password1' : 'password123',
        'password2' : 'password123'
        }

        # CHeck if userform is correct (which it should be)
        self.UserForm_valid(data)

        # Call the register view with a valid form.
        self.client.post("/register/", data)

        # Try to retrieve a newly created user.
        u = get_object_or_404(User, username=data['username'])

        # Check content of fields.
        self.assertEqual(u.username, data['username'])
        self.assertEqual(u.email, data['email'])

        # Check is password matches.
        self.assertTrue(u.check_password(data['password1']))

    # Invalid Form Data
    def test_UserForm_invalid(self):
        data = {
            'username' : "",
            'email'     : 'testuser@cinemaple.com',
            'password1' : '1',
            'password2' : '2'
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
