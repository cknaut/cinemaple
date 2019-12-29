import json
import random
import string
import urllib

import tmdbsimple as tmdb
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.shortcuts import get_object_or_404
from django.test import TestCase

from .forms import *
from .utils import Mailchimp

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


    def test_no_email_sent(self):
        ''' No email is sent, check if outbox is empty '''
        self.assertEqual(len(mail.outbox), 0)


    def test_send_mg_email(self):
        """
        Send email and checks if status is ok.
        """

        sender_email    = "mg_test@cinemaple.com"
        subject         = "Cinemaple Mailgun Test"
        recipients      = ["mg_test@cinemaple.com", "can.knaut@gmail.com"]
        content         = "This is a test email!"

        # TODO: Check why this fails.
        email = EmailMessage(subject,content, sender_email,recipients)
        email.send(fail_silently=False)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].body, content)




class Email_Verification_Check(TestCase):

    # random username
    randuser = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    # Valid Form Data
    def UserForm_valid(self, data):
        form = RegistrationForm(data=data, testing=True)
        self.assertTrue(form.is_valid())

    def test_register_user(self):
        data = {
        'email'         : self.randuser + "@cinemaple.com",
        'first_name'    : 'Clément',
        'last_name'     : 'Müller',
        'password1'     : 'password123',
        'password2'     : 'password123'
        }

        # CHeck if userform is correct (which it should be)
        import pdb; pdb.set_trace()
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
            'email'          : '@cinemaple.com',
            'first_name'     : 'Hans',
            'last_name'     : 'Müller',
            'password1' : '1',
            'password2' : '2'
        }
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())


class themovieDB(TestCase):
    ''' Test the TheMovie DB '''

    def test_movite_title(self):
        tmdb.API_KEY = settings.TMDB_API_KEY

        movie = tmdb.Movies(603)
        response = movie.info()
        import pdb; pdb.set_trace()
        self.assertEquals(response.title, 'The Matrix')
