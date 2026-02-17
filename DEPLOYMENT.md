# Cinemaple redeployment plan

Heroku notified that the account and apps will be **deleted in 30 days** due to inactivity. Heroku no longer offers free dynos (since Nov 2022), so redeploying “free” means either logging in to keep the app and then paying, or moving to a platform with a free tier.

---

## Immediate (within 30 days)

1. **Log into Heroku**  
   Go to [dashboard.heroku.com](https://dashboard.heroku.com) and sign in. This stops the 30‑day deletion of your account and app.  
   Your app and config (including env vars) stay until you delete them or they’re purged by Heroku.

2. **Export config and data (optional but recommended)**  
   - In Heroku Dashboard → your app → **Settings** → **Reveal Config Vars**. Copy or screenshot all variable names (values are secret). You’ll need these on the new host.  
   - If you had Heroku Postgres and need the data: use **Heroku Postgres** → **Durability** (or **Settings**) → **Manual backup** / `pg_dump` before the account or add-on is removed.

---

## Option A: Stay on Heroku (paid)

- **Cost:** Basic dyno ~\$25/month; Postgres add-on extra (see [Heroku pricing](https://www.heroku.com/pricing)).  
- **Steps:**  
  1. Log in (above).  
  2. Upgrade the app: **Resources** → change dyno from (none) to **Basic** (or Eco if available).  
  3. If the app used Heroku Postgres and it was removed, re-add **Heroku Postgres** and restore from backup if you have one; otherwise you’ll start with a fresh DB.  
  4. Redeploy from your repo (e.g. **Deploy** → **Deploy from GitHub** or `git push heroku main`).  
  5. Re-add custom domain **www.cinemaple.com** under **Settings → Domains** and point Cloudflare CNAME to `your-app.herokuapp.com`.

---

## Option B: Move to a free-tier host (recommended for “free”)

Best match for “free like old Heroku” is **Render** (free web service + free Postgres with limits). Alternatives: **Railway** (\$5 free credit/month), **Fly.io** (free allowance).

**→ Step-by-step for moving to Render: see [RENDER.md](RENDER.md).** The repo includes `render.yaml` (Blueprint) so you can create the web service and database in one go.

### Render free tier (summary)

- **Web service:** 750 hours/month, spins down after ~15 min inactivity (~1 min cold start).  
- **PostgreSQL:** Free DB; check [Render Free Tier](https://render.com/docs/free) for current limits (e.g. 90-day expiry on some free DBs).  
- **SSL:** Included.  
- **No credit card** required for free tier.

### Steps to deploy Cinemaple on Render

1. **Prepare the repo (already done in this project)**  
   - `runtime.txt` – Python version.  
   - `build.sh` – install deps, `collectstatic`, `migrate`.  
   - Settings use `DATABASE_URL` when set (works with Render’s Postgres).  
   - `ALLOWED_HOSTS` includes your Render URL and `www.cinemaple.com`.

2. **Render Dashboard**  
   - [dashboard.render.com](https://dashboard.render.com) → **New** → **Web Service**.  
   - Connect your GitHub repo (e.g. `cinemaple`).  
   - **Build command:** `./build.sh` (ensure `build.sh` is executable; Render runs from repo root).  
   - **Start command:** `gunicorn cinemaple.wsgi` (use this instead of the Procfile’s New Relic command unless you configure New Relic on Render).  
   - **Instance type:** Free.

3. **Database**  
   - **New** → **PostgreSQL**. Create a free DB, then copy the **Internal Database URL**.  
   - In the **Web Service** → **Environment**: add `DATABASE_URL` = that URL.  
   - Render can auto-inject `DATABASE_URL` if you link the DB to the service.

4. **Environment variables**  
   Copy from your Heroku Config Vars (or from the list below). In Render → **Environment**, add each key/value.  
   Required (app will not start without them):  
   - `SECRET_KEY_DJANGO`  
   - `DJANGO_ENV` = `PRODUCTION`  
   - `MAILCHIMP_API_KEY`, `MAILCHIMP_DATA_CENTER`, `MAILCHIMP_EMAIL_LIST_ID`, `MAILCHIMP_EMAIL_LIST_ID_TEST`  
   - `MAILGUN_API_KEY`, `MAILGUN_DOMAIN_NAME`  
   - `RECAPTCHA_SECRET_KEY`, `RECAPTCHA_SITE_KEY`  
   - `EMAIL_VERIFICATION_SECRET_SALT`, `PW_RESET_SECRET_SALT`, `REV_USER_ACCESS_SECRET_SALT`  
   - `TMDB_API_KEY`  

   Optional: set `DATABASE_URL` if not auto-set by linking the Postgres service.

5. **Deploy**  
   Save; Render will build and deploy. First request after spin-down may take ~1 minute.

6. **Custom domain (cinemaple.com)**  
   - In Render → your Web Service → **Settings** → **Custom Domains**: add `www.cinemaple.com` (and `cinemaple.com` if you use it).  
   - In **Cloudflare**: set CNAME for `www` (and root if applicable) to the host Render shows (e.g. `your-service.onrender.com`).  
   - SSL: Cloudflare **Full** or **Full (strict)** once Render has issued the cert.

---

## Required environment variables (checklist)

Use this to recreate Config Vars on Heroku or any new host. **Mailchimp and Mailgun are optional** – if unset, the app runs with emails to console and mailing-list features disabled.

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `SECRET_KEY_DJANGO` | Yes | Django secret key |
| `DJANGO_ENV` | Yes | `DEBUG` or `PRODUCTION` |
| `DATABASE_URL` | Yes | Postgres URL (often set by host) |
| `RECAPTCHA_SECRET_KEY` | Yes | reCAPTCHA secret |
| `RECAPTCHA_SITE_KEY` | Yes | reCAPTCHA site key |
| `EMAIL_VERIFICATION_SECRET_SALT` | Yes | Email verification |
| `PW_RESET_SECRET_SALT` | Yes | Password reset |
| `REV_USER_ACCESS_SECRET_SALT` | Yes | Revocation/access |
| `TMDB_API_KEY` | Yes | TMDb API |
| `MAILCHIMP_API_KEY` | Optional | Mailchimp API (leave empty to disable) |
| `MAILCHIMP_DATA_CENTER` | Optional | Mailchimp DC (e.g. us21) |
| `MAILCHIMP_EMAIL_LIST_ID` | Optional | Main list ID |
| `MAILCHIMP_EMAIL_LIST_ID_TEST` | Optional | Test list ID |
| `MAILGUN_API_KEY` | Optional | Mailgun sending (leave empty → console backend) |
| `MAILGUN_DOMAIN_NAME` | Optional | Mailgun domain |

---

## After redeployment

- **Cloudflare:** Point DNS (CNAME) to the new host (e.g. `yourapp.onrender.com` or `yourapp.herokuapp.com`).  
- **ALLOWED_HOSTS:** Already includes `www.cinemaple.com`, `cinemaple.com`, and `.herokuapp.com`; for Render add your `*.onrender.com` host (or set it via env if you add that logic).  
- **New Relic:** Optional. On Render you can drop `newrelic-admin run-program` from the start command and remove the `newrelic` package if you don’t use it.

---

## Summary

- **Urgent:** Log into Heroku within 30 days to prevent account/app deletion; export env var names and backup DB if needed.  
- **Free option:** Deploy to **Render** (free web + free Postgres) using this repo’s `build.sh`, `runtime.txt`, and env vars above.  
- **Paid option:** Stay on Heroku; upgrade to a paid dyno (and Postgres if needed), then redeploy and reattach domain.
