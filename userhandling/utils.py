# From https://www.codingforentrepreneurs.com/blog/mailchimp-integration/

import hashlib
import random
import re
import json
import requests
from django.conf import settings


# Wrap Bootrap Badge HTML around string
def badgify(string, badge_type):
    badge_html = "<span class='badge badge-" + badge_type + "'>" + string + "</span>"
    return badge_html

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

# Get secret salt used for hash generation for email reset
EMAIL_VERIFICATION_SECRET_SALT = getattr(settings, "MAILCHIMP_API_KEY", None)
if EMAIL_VERIFICATION_SECRET_SALT is None:
    raise NotImplementedError("EMAIL_VERIFICATION_SECRET_SALT must be set in the settings")

PW_RESET_SECRET_SALT = getattr(settings, "PW_RESET_SECRET_SALT", None)
if PW_RESET_SECRET_SALT is None:
    raise NotImplementedError("PW_RESET_SECRET_SALT must be set in the settings")




def check_email(email):
    if not re.match(r".+@.+\..+", email):
        raise ValueError('String ' + email + ' is not a valid email address')
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

class VerificationHash(object):
    def __init__(self):
        super(VerificationHash, self).__init__()
        self.salt =  hashlib.sha256(str(random.getrandbits(256)).encode('utf-8')).hexdigest()

    def gen_ver_hash(self, username):
        ''' Get Hasch by combining username, salt based on user creation, and secret salt'''
        return hashlib.sha1((self.salt+username+EMAIL_VERIFICATION_SECRET_SALT).encode('utf-8')).hexdigest()

    def gen_pw_hash(self, username):
        ''' Get Hasch by combining username, salt based on user creation, and secret salt'''
        return hashlib.sha1((self.salt+username+PW_RESET_SECRET_SALT).encode('utf-8')).hexdigest()

