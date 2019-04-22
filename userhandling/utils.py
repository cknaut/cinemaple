# From https://www.codingforentrepreneurs.com/blog/mailchimp-integration/

import hashlib
import re
import json
import requests
from django.conf import settings

# Mailchimp utils
MAILCHIMP_API_KEY = getattr(settings, "MAILCHIMP_API_KEY", None)
if MAILCHIMP_API_KEY is None:
    raise NotImplementedError("MAILCHIMP_API_KEY must be set in the settings")

MAILCHIMP_DATA_CENTER = getattr(settings, "MAILCHIMP_DATA_CENTER", None)

if MAILCHIMP_DATA_CENTER is None:
    raise NotImplementedError("MAILCHIMP_DATA_CENTER must be set in the settings, something like us17")

MAILCHIMP_EMAIL_LIST_ID = getattr(settings, "MAILCHIMP_EMAIL_LIST_ID", None)

if MAILCHIMP_EMAIL_LIST_ID is None:
    raise NotImplementedError("MAILCHIMP_EMAIL_LIST_ID must be set in the settings, something like us17")

MAILCHIMP_EMAIL_LIST_ID_TEST = getattr(settings, "MAILCHIMP_EMAIL_LIST_ID", None)

if MAILCHIMP_EMAIL_LIST_ID_TEST is None:
    raise NotImplementedError("MAILCHIMP_EMAIL_LIST_ID_TEST must be set in the settings, something like us17")



def check_email(email):
    if not re.match(r".+@.+\..+", email):
        raise ValueError('String passed is not a valid email address')
    return


def get_subscriber_hash(member_email):
    '''
    This makes a email hash which is required by the Mailchimp API
    '''
    check_email(member_email)
    member_email = member_email.lower().encode()
    m = hashlib.md5(member_email)
    return m.hexdigest()


class Mailchimp(object):
    def __init__(self, listid):
        super(Mailchimp, self).__init__()
        self.key = MAILCHIMP_API_KEY
        self.api_url  = 'https://{dc}.api.mailchimp.com/3.0'.format(
                                    dc=MAILCHIMP_DATA_CENTER
                                )
        self.list_id = listid
        self.list_endpoint = '{api_url}/lists/{list_id}'.format(
                                    api_url = self.api_url,
                                    list_id=self.list_id
                        )

    def get_members_endpoint(self):
        endpoint = '{list_endpoint}/members'.format(
                                    list_endpoint=self.list_endpoint)
        return endpoint

    def add_email(self, email):
        check_email(email)
        endpoint = self.get_members_endpoint()
        data = {
                "email_address": email,
                "status": "subscribed"
                }
        r = requests.post(endpoint,
                    auth=("", MAILCHIMP_API_KEY),
                    data=json.dumps(data)
                    )
        return r.status_code, r.json()


    def check_valid_status(self, status):
        choices = ['subscribed','unsubscribed', 'cleaned', 'pending']
        if status not in choices:
            raise ValueError("Not a valid choice")
        return status

    def change_subscription_status(self, email, status):
        subscriber_hash     = get_subscriber_hash(email)
        members_endpoint       = self.get_members_endpoint()
        endpoint            = "{members_endpoint}/{sub_hash}".format(
                                members_endpoint=members_endpoint,
                                sub_hash=subscriber_hash
                                )
        data                = {
                                "status": self.check_valid_status(status)
                            }
        r                   = requests.put(endpoint,
                                auth=("", MAILCHIMP_API_KEY),
                                data=json.dumps(data)
                                )
        return r.status_code, r.json()

    def check_subscription_status(self, email):
        subscriber_hash     = get_subscriber_hash(email)
        members_endpoint       = self.get_members_endpoint()
        endpoint            = "{members_endpoint}/{sub_hash}".format(
                                members_endpoint=members_endpoint,
                                sub_hash=subscriber_hash
                                )
        r                   = requests.get(endpoint,
                                auth=("", MAILCHIMP_API_KEY)
                                )
        return r.status_code, r.json()

    def resubscribe(self, email):
        return self.change_subscription_status(email, status = 'subscribed')


    def unsubscribe(self, email):
        return self.change_subscription_status(email, status='unsubscribed')

# Mailgun Utils


MAILGUN_DOMAIN_NAME = getattr(settings, "MAILGUN_DOMAIN_NAME", None)
if MAILGUN_DOMAIN_NAME is None:
    raise NotImplementedError("MAILGUN_DOMAIN_NAME must be set in the settings")


MAILGUN_API_KEY = getattr(settings, "MAILGUN_API_KEY", None)
if MAILGUN_API_KEY is None:
    raise NotImplementedError("MAILGUN_API_KEY must be set in the settings")

class Mailgun(object):

        def __init__(self):
            super(Mailgun, self).__init__()
            self.key = MAILGUN_API_KEY
            self.api_url  = 'https://api.mailgun.net/v3/{dm}/messages'.format(
                                        dm=MAILGUN_DOMAIN_NAME
                                    )

        def send_email(self, sender_email, sender_name, subject, recipients, content):

            # Check emails
            check_email(sender_email)
            for recipient in recipients:
                check_email(recipient)

            auth=("api", self.key)

            data={  "from": sender_name + ' <' + sender_email + '>',
                    "to": recipients,
                    "subject": subject,
                    "text": content
            }

            r = requests.post(self.api_url, auth=auth, data=data)
            return r.status_code, r.json()
