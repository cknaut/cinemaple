# From https://www.codingforentrepreneurs.com/blog/mailchimp-integration/

import hashlib
import json
import random
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import requests

from .models import Location


# Wrap Bootrap Badge HTML around string
def badgify(string, badge_type):
    badge_html = "<span class='badge badge-" + \
        badge_type + "'>" + string + "</span>"
    return badge_html


# Mailchimp utils
MAILCHIMP_API_KEY = getattr(settings, "MAILCHIMP_API_KEY", None)
if MAILCHIMP_API_KEY is None:
    raise NotImplementedError("MAILCHIMP_API_KEY must be set in the settings")

MAILCHIMP_DATA_CENTER = getattr(settings, "MAILCHIMP_DATA_CENTER", None)

if MAILCHIMP_DATA_CENTER is None:
    raise NotImplementedError(
        "MAILCHIMP_DATA_CENTER must be set in the settings, \
        something like us17"
    )

MAILCHIMP_EMAIL_LIST_ID = getattr(settings, "MAILCHIMP_EMAIL_LIST_ID", None)

if MAILCHIMP_EMAIL_LIST_ID is None:
    raise NotImplementedError(
        "MAILCHIMP_EMAIL_LIST_ID must be set in the settings"
    )

MAILCHIMP_EMAIL_LIST_ID_TEST = getattr(
    settings,
    "MAILCHIMP_EMAIL_LIST_ID",
    None
)

if MAILCHIMP_EMAIL_LIST_ID_TEST is None:
    raise NotImplementedError(
        "MAILCHIMP_EMAIL_LIST_ID_TEST must be set in the settings"
    )

# Get secret salt used for hash generation for email reset
EMAIL_VERIFICATION_SECRET_SALT = getattr(settings, "MAILCHIMP_API_KEY", None)
if EMAIL_VERIFICATION_SECRET_SALT is None:
    raise NotImplementedError(
        "EMAIL_VERIFICATION_SECRET_SALT must be set in the settings"
    )

PW_RESET_SECRET_SALT = getattr(settings, "PW_RESET_SECRET_SALT", None)
if PW_RESET_SECRET_SALT is None:
    raise NotImplementedError(
        "PW_RESET_SECRET_SALT must be set in the settings"
    )

REV_USER_ACCESS_SECRET_SALT = getattr(
    settings,
    "REV_USER_ACCESS_SECRET_SALT",
    None
)

if REV_USER_ACCESS_SECRET_SALT is None:
    raise NotImplementedError(
        "REV_USER_ACCESS_SECRET_SALT must be set in the settings"
    )


def check_email(email):
    if not re.match(r".+@.+\..+", email):
        raise ValueError('String ' + email + ' is not a valid email address')
    return


# This makes a email hash which is required by the Mailchimp API
def get_subscriber_hash(member_email):
    check_email(member_email)
    member_email = member_email.lower().encode()
    md5 = hashlib.md5(member_email)
    return md5.hexdigest()


class Mailchimp(object):
    def __init__(self, listid):
        super(Mailchimp, self).__init__()
        self.key = MAILCHIMP_API_KEY
        self.list_id = listid

        self.api_url = 'https://{dc}.api.mailchimp.com/3.0'.format(
            dc=MAILCHIMP_DATA_CENTER
        )

        self.list_endpoint = '{api_url}/lists/{list_id}'.format(
            api_url=self.api_url,
            list_id=self.list_id
        )

        self.segment_endpoint = '{list_endpoint}/segments'.format(
            list_endpoint=self.list_endpoint,
        )

    def get_members_endpoint(self):
        endpoint = '{list_endpoint}/members'.format(
            list_endpoint=self.list_endpoint
        )
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
        req = requests.post(
            endpoint,
            auth=("", MAILCHIMP_API_KEY),
            data=json.dumps(data)
        )
        return req.status_code, req.json()

    def check_list_details(self, tag_id):

        # TODO: Make sure that we will never retrieve more than 1000 users.
        data = {
            "count" : "1000"
        }

        if tag_id is None:
            endpoint = self.get_members_endpoint()
        else:
            segment_endpoint = self.segment_endpoint
            endpoint = "{segment_endpoint}/{tag_id}/members".format(
                segment_endpoint=segment_endpoint,
                tag_id=tag_id
            )

        req = requests.get(
            endpoint,
            auth=("", MAILCHIMP_API_KEY),
            params=data
        )

        return req.status_code, req.json()

    def search_tag(self, tag):
        # Looks up alrady defined tags and returns tag_id if it exists

        data = {
            "count" : "1000"
        }

        req = requests.get(
            self.segment_endpoint,
            auth=("", MAILCHIMP_API_KEY),
            params=data
        )

        res = req.json()
        tag_dicts = res["segments"]
        num_tags = len(tag_dicts)

        for i in range(num_tags):
            if tag_dicts[i]["name"] == tag:
                return True, tag_dicts[i]["id"]

        return False, ""

    def create_tag(self, tag):

        # Create Tag
        data = {
            "name": tag,
            "static_segment": [],
        }

        req = requests.post(
            self.segment_endpoint,
            auth=("", MAILCHIMP_API_KEY),
            data=json.dumps(data)
        )

        res = req.json()
        return res["id"]

    def create_or_retrieve_tag(self, tag):
        # Returns ID of existing or newly created tag
        tag_exists, tag_id = self.search_tag(tag)

        if not tag_exists:
            tag_id = self.create_tag(tag)

        return tag_id

    def add_tag_to_user(self, tag, email):

        tag_id = self.create_or_retrieve_tag(tag)

        data = {
            "email_address": email
        }

        endpoint = "{}/{}/members".format(self.segment_endpoint, tag_id)

        req = requests.post(
            endpoint,
            auth=("", MAILCHIMP_API_KEY),
            data=json.dumps(data)
        )

        return req.status_code, req.json()

    def untag(self, tag, email):
        tag_id = self.create_or_retrieve_tag(tag)

        subscriber_hash = get_subscriber_hash(email)
        list_endpoint = self.list_endpoint
        endpoint = "{list_endpoint}/segments/{tag_id}/members/{sub_hash}".\
            format(
                list_endpoint=list_endpoint,
                tag_id=tag_id,
                sub_hash=subscriber_hash
            )

        req = requests.delete(
            endpoint,
            auth=("", MAILCHIMP_API_KEY)
        )

        return req.status_code

    def create_campaign(self, date, reply_to, subject_line,
                        preview_text, title, from_name, html_body,
                        location_id):
        """Create Mailchimp Campaign.

        Creates Mailchimp Campaing and schedules it according to date
        date is datetime object and roudn ded to nearest 15mins
        """
        campaigns_endpoint = '{api_url}/campaigns'.format(
            api_url=self.api_url
        )

        # Retrieve ids of location tag
        location_tag = "{}{}".format(settings.MC_PREFIX_HASACCESSID,
                                     location_id)
        location_tag_id = self.create_or_retrieve_tag(location_tag)

        data = {
            "type": "regular",
            "recipients": {
                "list_id": self.list_id,
                "segment_opts": {
                    "saved_segment_id": location_tag_id
                }
            },
            "settings": {
                "subject_line"      : subject_line,
                "preview_text"      : preview_text,
                "from_name"         : from_name,
                "title"             : title,
                "reply_to"          : reply_to,
                "to_name"           : "*|FNAME|*",
            }
        }

        req = requests.post(
            campaigns_endpoint,
            auth=("", MAILCHIMP_API_KEY),
            data=json.dumps(data)
        )

        campaign_id = req.json()['id']

        # upload html to campaign
        campaign_endpoint = '{campaigns_endpoint}/{campaign_id}'.format(
            campaigns_endpoint=campaigns_endpoint,
            campaign_id=campaign_id
        )

        campaign_content_endpoint = '{campaign_endpoint}/content'.format(
            campaign_endpoint=campaign_endpoint
        )

        data = {
            'html'  : html_body
        }

        # Retrieve HTML of Tempalte
        req = requests.put(
            campaign_content_endpoint,
            auth=("", MAILCHIMP_API_KEY),
            data=json.dumps(data)
        )

        # Schedule Campaign
        campaign_scheduled_endpoint = '{campaign_endpoint}/actions/schedule'.\
            format(
                campaign_endpoint=campaign_endpoint
            )

        # round_down to the next 15 mins
        date = date.isoformat()
        data = {
            'schedule_time'  : date
        }

        req = requests.post(
            campaign_scheduled_endpoint,
            auth=("", MAILCHIMP_API_KEY),
            data=json.dumps(data)
        )

        return req.status_code


    def get_member_list(self, tag_id=None):

        list_details = self.check_list_details(tag_id)
        res = list_details[1]
        status = list_details[0]
        mailchimp_id = self.list_id

        # TODO: FInd out why new mailchimp audience doesnt work
        # Somehow these print statements are needed
        print(res)
        print(status)

        # Check if response is ok
        results = ""
        if status == 200:
            # retrieve list of subscribed and unsubscribed emails
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
        choices = ['subscribed', 'unsubscribed', 'cleaned', 'pending']
        if status not in choices:
            raise ValueError("Not a valid choice")
        return status

    def change_subscription_status(self, email, status):
        subscriber_hash = get_subscriber_hash(email)
        members_endpoint = self.get_members_endpoint()

        endpoint = "{members_endpoint}/{sub_hash}".format(
            members_endpoint=members_endpoint,
            sub_hash=subscriber_hash
        )

        data = {
            "status": self.check_valid_status(status)
        }

        req = requests.put(
            endpoint,
            auth=("", MAILCHIMP_API_KEY),
            data=json.dumps(data)
        )

        return req.status_code, req.json()

    def check_subscription_status(self, email):
        subscriber_hash = get_subscriber_hash(email)
        members_endpoint = self.get_members_endpoint()

        endpoint = "{members_endpoint}/{sub_hash}".format(
            members_endpoint=members_endpoint,
            sub_hash=subscriber_hash
        )

        req = requests.get(
            endpoint,
            auth=("", MAILCHIMP_API_KEY)
        )

        return req.status_code, req.json()

    def change_subscriber_email(self, old_email, newemail):
        subscriber_hash = get_subscriber_hash(old_email)
        members_endpoint = self.get_members_endpoint()
        endpoint = "{members_endpoint}/{sub_hash}".format(
            members_endpoint=members_endpoint,
            sub_hash=subscriber_hash
        )

        data = {
            "email_address": newemail,
        }
        req = requests.put(
            endpoint,
            auth=("", MAILCHIMP_API_KEY),
            data=json.dumps(data)
        )
        return req.status_code, req.json()

    def resubscribe(self, email):
        return self.change_subscription_status(email, status='subscribed')

    def unsubscribe(self, email):
        return self.change_subscription_status(email, status='unsubscribed')

    def get_all_campaign(self):
        members_endpoint = self.get_members_endpoint()
        endpoint = "{members_endpoint}/campaigns".format(
            members_endpoint=members_endpoint
        )
        req = requests.get(endpoint)
        return req.status_code, req.json()


class VerificationHash(object):
    def __init__(self):
        super(VerificationHash, self).__init__()
        self.salt = hashlib.sha256(
            str(random.getrandbits(256)).encode('utf-8')
        ).hexdigest()

    # Get Hasch by combining username, salt based on user creation, \
    #  and secret salt
    def gen_ver_hash(self, username):
        return hashlib.sha1((self.salt + username
                             + EMAIL_VERIFICATION_SECRET_SALT
                             ).encode('utf-8')).hexdigest()

    # Get Hasch by combining username, salt based on user creation, \
    # and secret salt
    def gen_pw_hash(self, username):
        return hashlib.sha1(
            (self.salt + username + PW_RESET_SECRET_SALT).encode('utf-8')
        ).hexdigest()

    # Get Hasch by combining username, salt based on user creation, \
    # and secret salt
    def gen_rev_access_hash(self, loc_perm_id):
        return hashlib.sha1(
            (
                self.salt + str(loc_perm_id) + PW_RESET_SECRET_SALT
            ).encode('utf-8')
        ).hexdigest()


def check_ml_health(location_id):
    """Assesses health of Mailchimp mailing list.

    Compares listed members in the Mailchimp mailinglist (including subscribed
    and unsubscribed ones) to registered users
    If not all cinemaple users are in  Mailchimp list, raise problem.
    """
    mail_chimp = Mailchimp(settings.MAILCHIMP_EMAIL_LIST_ID)
    location_tag = "{}{}".format(settings.MC_PREFIX_HASACCESSID, location_id)
    location_tag_id = mail_chimp.create_or_retrieve_tag(location_tag)
    location = Location.objects.filter(pk=location_id)

    status, members_list, mailchimp_id = mail_chimp.get_member_list(location_tag_id)

    if status == 200:
        print(members_list)
        status = badgify(str(status), 'success')
        if members_list == "":
            subs = []
            usubs = []
        else:
            subs = [badgify(email, 'secondary') for email in
                    members_list['emails_subscribed']]
            usubs = [badgify(email, 'secondary') for email in
                     members_list['emails_unsubscribed']]

        # Get emails of associated to id
        users = User.objects.filter(is_active=True)

        # search users that are associated with location:
        user_of_loc_with_id = [user.id for user in users if location[0]
                               in user.profile.get_all_locations()]
        users = User.objects.filter(id__in=user_of_loc_with_id)

        user_emails = [users[i].email for i in range(len(users))]
        user_emails_badged = [badgify(email, 'secondary') for email
                              in user_emails]

        users_not_in_mc = []

        # make sure we won't get an error if either \
        # unsubscribed or subscribed is emtpy
        if not members_list == '':
            for email in user_emails:
                if email not in members_list['emails_subscribed'] and \
                        email not in members_list['emails_unsubscribed']:
                    users_not_in_mc.append(email)

        users_not_in_mc_badged = [badgify(email, 'secondary') for email
                                  in users_not_in_mc]

        # users with revoked access

        user_revoked_id = [user.id for user in users if
                           user.profile.has_revoked(location)]
        users_revoked = User.objects.filter(id__in=user_revoked_id)
        emails_revoked = [badgify(user.email, 'secondary')
                          for user in users_revoked]

        if users_not_in_mc_badged:
            healthy = False
            healthprint = badgify("Unhealthy", 'danger')
        else:
            healthy = True
            healthprint = badgify("Healthy", 'success')

        context = {
            'status'            : status,
            'location'          : location[0],
            'statusok'          : healthy,
            'mc_id'             : mailchimp_id,
            "emails_revoked"    : emails_revoked,
            "num_revoked"       : len(emails_revoked),
            'subs'              : subs,
            'usubs'             : usubs,
            'user_emails'       : user_emails_badged,
            'users_not_in_mc'   : users_not_in_mc_badged,
            'health'            : healthprint,
        }

    else:
        status = badgify(str(status), 'danger')
        context = {
            'status'            : status,
            'statusok'          : False,
            'mc_id'             : mailchimp_id,
            'subs'              : 0,
            'usubs'             : 0,
            'user_emails'       : 0,
            'users_not_in_mc'   : 0,
            'health'            : 0
        }

    return healthy, context


def send_role_change_email(user, role, location):
    # email triggered if user status is changed to AM or HO

    sender_email = "info@cinemaple.com"
    sender_name = "Cinemaple"
    recipients = [user.email]

    context_email = {
        'firstname'    : user.first_name,
        'location'      : location
    }

    if role == 'AM':
        content = render_to_string(
            "userhandling/emails/change_to_am.html",
            context_email
        )
        subject = "User role for {} changed to Ambassador!".format(location)

    elif role == 'HO':
        content = render_to_string(
            "userhandling/emails/change_to_ho.html",
            context_email
        )
        subject = "User role for {} changed to Host!".format(location)

    email = EmailMultiAlternatives(
        subject, '', sender_name + " <" + sender_email + ">", recipients)
    email.attach_alternative(content, "text/html")
    email.send()
