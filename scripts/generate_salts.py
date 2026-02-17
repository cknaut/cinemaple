#!/usr/bin/env python3
"""Generate the three secret salts needed for Cinemaple env vars (no Heroku access)."""
import secrets

print("Paste these into Render -> Environment (one value per variable):\n")
print("EMAIL_VERIFICATION_SECRET_SALT =", secrets.token_urlsafe(32))
print("PW_RESET_SECRET_SALT =", secrets.token_urlsafe(32))
print("REV_USER_ACCESS_SECRET_SALT =", secrets.token_urlsafe(32))
