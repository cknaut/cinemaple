# Gunicorn config for Render (bind to PORT from environment)
import os

bind = "0.0.0.0:{}".format(os.environ.get("PORT", "10000"))
workers = 1
threads = 2
timeout = 120
