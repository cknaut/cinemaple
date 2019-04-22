from django.test import TestCase
from .utils import Mailchimp, Mailgun
import random
import urllib, json
import string
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
