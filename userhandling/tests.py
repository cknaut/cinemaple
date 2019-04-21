from django.test import TestCase
from .utils import Mailchimp
import random
import string
import pdb


# Test Mailchimp Class: Subscribe and unsubscribe test email


class MailchimpSubscribeTest(TestCase):

    # random test email
    test_email =  "testing@cinemaple.com"

    # TODO: Add delay to subscribe welcome email to prevent triggering by tests.
    def subscribeemail(self):
        """
        Checks if Mailchimp subscription works
        """
        mc = Mailchimp()
        mc.resubscribe(self.test_email)
        self.assertEqual(mc.check_subscription_status(self.test_email)[1]["status"], "subscribed")

    def unsubscribeemail(self):
        """
        Checks if Mailchimp unsubscription works
        """
        mc = Mailchimp()
        mc.unsubscribe(self.test_email)
        self.assertEqual(mc.check_subscription_status(self.test_email)[1]["status"], "unsubscribed")

    def test_all(self):
        """
        Run tests
        """
        self.subscribeemail()
        self.unsubscribeemail()




