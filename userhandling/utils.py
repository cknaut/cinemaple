# From https://www.codingforentrepreneurs.com/blog/mailchimp-integration/

import hashlib
import random
import re
import json
import requests
from django.conf import settings
from django.contrib.auth.models import User



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

        print(endpoint)
        return endpoint

    def add_email(self, email, firstname, lastname):
        check_email(email)
        endpoint = self.get_members_endpoint()
        data = {
                "email_address": email,
                "status": "subscribed",
                "merge_fields": {
                        "FNAME": firstname,
                        "LNAME": lastname
                    }
                }
        r = requests.post(endpoint,
                    auth=("", MAILCHIMP_API_KEY),
                    data=json.dumps(data)
                    )
        return r.status_code, r.json()

    def check_list_details(self):
        members_endpoint       = self.get_members_endpoint()
        r                   = requests.get(members_endpoint,
                                auth=("", MAILCHIMP_API_KEY)
                                )
        return r.status_code, r.json()


    def create_campaign(self, template_id, reply_to, subject_line, preview_text, title, from_name, html):
        campaigns_endpoint       = self.list_endpoint = '{api_url}/campaigns'.format(
                                    api_url = self.api_url)

        tempaltes_endpoint       = self.list_endpoint = '{api_url}/templates/{tempalte_id}/default-content'.format(
                                    api_url = self.api_url,
                                    tempalte_id=template_id)

        data = {
                    "type": "regular",
                    "recipients": {
                            "list_id": self.list_id,
                        },
                    "settings": {
                            "subject_line"      : subject_line,
                            "preview_text"      : preview_text,
                            "from_name"         : from_name,
                            "title"             : title,
                            "reply_to"          : reply_to,
                            "to_name"           : "*|FNAME|*",
                            "template_id"       : int(template_id)
                    }
                    }
        r = requests.post(campaigns_endpoint,
                    auth=("", MAILCHIMP_API_KEY),
                    data=json.dumps(data)
                    )

        r_tempalte = requests.get(tempaltes_endpoint,
                    auth=("", MAILCHIMP_API_KEY),
                    )


        return r.status_code, r.json()

    ''''
    "settings": {
                            "subject_line"      : subject_line,
                            "preview_text"      : preview_text,
                            "from_name"         : from_name,
                            "title"             : title,
                            "reply_to"          : reply_to,
                            "to_name"           : "*|FNAME|*",
                            "template_id"       : template_id
                    }
    '''

    def get_member_list(self):
        list_details = self.check_list_details()
        res = list_details[1]
        status = list_details[0]
        mailchimp_id = self.list_id

        #TODO: FInd out why new mailchimp audience doesnt work
        # Somehow these print statements are needed
        print(res)
        print(status)

        # Check if response is ok
        results = ""
        if status == 200:
            #retrieve list of subscribed and unsubscribed emails
            num_total = len(res['members'])
            emails_subscribed = []
            emails_unubscribed = []
            for i in range(num_total):
                email = res['members'][i]['email_address']
                subscr_status = res['members'][i]['status']
                if subscr_status == 'subscribed':
                    emails_subscribed.append(email)
                elif subscr_status == 'unsubscribed':
                    emails_unubscribed.append(email)

                results = {
                    "emails_subscribed" : emails_subscribed,
                    "emails_unsubscribed" : emails_unubscribed,
                }

        return status, results, mailchimp_id


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


    def change_subscriber_email(self, old_email, newemail):
        subscriber_hash     = get_subscriber_hash(old_email)
        members_endpoint       = self.get_members_endpoint()
        endpoint            = "{members_endpoint}/{sub_hash}".format(
                                members_endpoint=members_endpoint,
                                sub_hash=subscriber_hash
                                )

        data                = {
                                "email_address": newemail,
                            }
        r                   = requests.put(endpoint,
                                auth=("", MAILCHIMP_API_KEY),
                                data=json.dumps(data)
                                )
        return r.status_code, r.json()

    def resubscribe(self, email):
        return self.change_subscription_status(email, status = 'subscribed')


    def unsubscribe(self, email):
        return self.change_subscription_status(email, status='unsubscribed')

    def get_all_campaign(self):
        members_endpoint       = self.get_members_endpoint()
        endpoint                = "{members_endpoint}/campaigns".format(members_endpoint=members_endpoint)
        r                   = requests.get(endpoint)
        return r.status_code, r.json()



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

def check_ml_health():
    '''
    Compares listed members in the Mailchimp mailinglist (including subscribed and unsubscribed ones) to registered users
    If not all cinemaple users are in  Mailchimp list, raise problem.

    '''
    mc = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)
    status, members_list, mailchimp_id = mc.get_member_list()

    if status == 200:
        statusok = True
        print(members_list)
        status = badgify(str(status), 'success')
        subs = [badgify(email, 'secondary') for email in members_list['emails_subscribed']]
        usubs = [badgify(email, 'secondary') for email in members_list['emails_unsubscribed']]

        # Get emails of all users

        users = User.objects.filter(is_active=True)
        user_emails = [users[i].email for i in range(len(users))]
        user_emails_badged = [badgify(email, 'secondary') for email in user_emails]

        users_not_in_mc = []

        for email in user_emails:
            if email not in members_list['emails_subscribed'] and  email not in members_list['emails_unsubscribed']:
                users_not_in_mc.append(email)

        users_not_in_mc_badged = [badgify(email, 'secondary') for email in users_not_in_mc]

        if len(users_not_in_mc_badged) != 0:
            healthy = False
            healthprint = badgify("Unhealthy", 'danger')
        else:
            healthy = True
            healthprint = badgify("Healthy", 'success')

        context = {
            'status'            : status,
            'statusok'          : statusok,
            'mc_id'             : mailchimp_id,
            'subs'              : subs,
            'usubs'             : usubs,
            'user_emails'       : user_emails_badged,
            'users_not_in_mc'   : users_not_in_mc_badged,
            'health'            : healthprint
        }

    else:
        statusok = False
        status = badgify(str(status), 'danger')
        context = {
            'status'            : status,
            'statusok'          : statusok,
            'mc_id'             : mailchimp_id,
            'subs'              : 0,
            'usubs'             : 0,
            'user_emails'       : 0,
            'users_not_in_mc'   : 0,
            'health'            : 0
        }

    return healthy, context