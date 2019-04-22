import requests
from django.conf import settings


def send_simple_message():
	return requests.post(
		"https://api.mailgun.net/v3/" + settings.MAILGUN_DOMAIN_NAME + "/messages",
		auth=("api", settings.MAILGUN_API_KEY),
		data={"from": "Excited User <mg@cinemaple.com>",
			"to": ["can_knaut@yahoo.de", "me@cinemaple.com"],
			"subject": "Hello",
			"text": "Testing some Mailgun awesomness!"})

send_simple_message()
