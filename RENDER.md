# Move Cinemaple to Render (step-by-step)

Use this checklist to deploy Cinemaple on Render’s free tier and point www.cinemaple.com to it.

---

## Quick start (minimal order)

1. **Secrets** – Get reCAPTCHA (v2) keys, [TMDb API key](https://www.themoviedb.org/settings/api), and run `python scripts/generate_salts.py` for the three salts. (Mailchimp/Mailgun optional.)
2. **Git** – Push this repo to GitHub (branch `main` or `master`).
3. **Render** – [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint** → connect repo → **Apply**.
4. **Env** – In the new **cinemaple** web service → **Environment**, add: `RECAPTCHA_SECRET_KEY`, `RECAPTCHA_SITE_KEY`, `EMAIL_VERIFICATION_SECRET_SALT`, `PW_RESET_SECRET_SALT`, `REV_USER_ACCESS_SECRET_SALT`, `TMDB_API_KEY`.
5. **Domain** – In Render → **Custom Domains** add `www.cinemaple.com`; in Cloudflare set CNAME for `www` to the Render URL.

Details for each step are below. See also [.render-pre-deploy-checklist.md](.render-pre-deploy-checklist.md) for a short pre-deploy checklist.

---

## No Heroku access?

If the 30-day window has passed and you no longer have access to Heroku:

- You **cannot** recover the old Config Vars or database from Heroku.
- You need to **create or look up** the required secrets below (see [Step 1](#1-get-or-create-all-required-secrets-no-heroku-access)).
- The app will start with a **fresh database** on Render (new users, no old movie nights). There is no way to restore old data without a backup file you already have.

---

## Mailchimp and Mailgun optional

**Mailchimp** and **Mailgun** are **optional**. If you don’t set them (e.g. accounts discontinued):

- The app **still runs**. You only need: reCAPTCHA, TMDb, and the three salts (plus Render’s SECRET_KEY_DJANGO, DATABASE_URL, DJANGO_ENV).
- **Email:** Without Mailgun, Django uses the **console** backend: outgoing emails are printed in the Render logs instead of being sent. You can add a different email provider later (e.g. SendGrid, Resend) if you want real delivery.
- **Mailchimp:** Without it, mailing-list features (scheduled campaigns, list health page) are no-ops. User signup, movie nights, and voting still work; “Schedule email” for a movie night won’t send real campaigns.

---

## 1. Get or create all required secrets (no Heroku access)

The app will **not** start until these are set. Optional variables can be left empty.

| Variable | Required? | Where to get it |
|----------|-----------|-----------------|
| **SECRET_KEY_DJANGO** | Yes | Set by Render from the Blueprint (auto-generated). |
| **DJANGO_ENV** | Yes | Set by Blueprint as `PRODUCTION`. |
| **DATABASE_URL** | Yes | Set by Render when you link the PostgreSQL database. |
| **RECAPTCHA_SECRET_KEY** | Yes | [Google reCAPTCHA Admin](https://www.google.com/recaptcha/admin) → create a v2 “I’m not a robot” site → Secret key. |
| **RECAPTCHA_SITE_KEY** | Yes | Same reCAPTCHA site → Site key. |
| **EMAIL_VERIFICATION_SECRET_SALT** | Yes | Generate a random string (see below). |
| **PW_RESET_SECRET_SALT** | Yes | Generate a different random string (see below). |
| **REV_USER_ACCESS_SECRET_SALT** | Yes | Generate another random string (see below). |
| **TMDB_API_KEY** | Yes | [TMDb](https://www.themoviedb.org/settings/api) → API → Request an API Key (free). |
| **MAILCHIMP_API_KEY** | Optional | Leave empty to disable Mailchimp. |
| **MAILCHIMP_DATA_CENTER** | Optional | e.g. `us21` – leave empty if not using Mailchimp. |
| **MAILCHIMP_EMAIL_LIST_ID** | Optional | Leave empty if not using Mailchimp. |
| **MAILCHIMP_EMAIL_LIST_ID_TEST** | Optional | Leave empty if not using Mailchimp. |
| **MAILGUN_API_KEY** | Optional | Leave empty → emails go to console/logs. |
| **MAILGUN_DOMAIN_NAME** | Optional | Leave empty if not using Mailgun. |

**Generate the three salts** (use a different value for each):

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run it three times and use the outputs for `EMAIL_VERIFICATION_SECRET_SALT`, `PW_RESET_SECRET_SALT`, and `REV_USER_ACCESS_SECRET_SALT`. Or use the script in the repo: `python scripts/generate_salts.py` (see below).

Keep all values in a safe place (e.g. password manager); you’ll paste them into Render in Step 4.

---

## 2. Push the repo to GitHub

Render deploys from Git. If the project isn’t on GitHub yet:

```bash
cd /path/to/cinemaple
git add .
git commit -m "Add Render config (render.yaml, build.sh, RENDER.md)"
git remote add origin https://github.com/YOUR_USERNAME/cinemaple.git   # or your repo URL
git push -u origin main
```

(Use `master` if that’s your default branch.)

---

## 3. Create the service on Render with the Blueprint

1. Go to [dashboard.render.com](https://dashboard.render.com) and sign in (GitHub is fine).
2. Click **New** → **Blueprint**.
3. Connect the GitHub account/repo that contains **cinemaple** (the one with `render.yaml` in the root).
4. Select the **cinemaple** repo and the branch (e.g. `main`).
5. Render will read `render.yaml` and show:
   - 1 PostgreSQL database: **cinemaple-db** (free)
   - 1 Web Service: **cinemaple** (free)
6. Click **Apply**.  
   Render will create the database and the web service and link `DATABASE_URL` to the new DB.  
   It will also generate `SECRET_KEY_DJANGO` and set `DJANGO_ENV=PRODUCTION`.

---

## 4. Add the rest of the environment variables

1. In Render Dashboard, open the **cinemaple** web service.
2. Go to **Environment**.
3. Add these **required** variables (from Step 1):

   - `RECAPTCHA_SECRET_KEY`
   - `RECAPTCHA_SITE_KEY`
   - `EMAIL_VERIFICATION_SECRET_SALT`
   - `PW_RESET_SECRET_SALT`
   - `REV_USER_ACCESS_SECRET_SALT`
   - `TMDB_API_KEY`

4. **Optional** (only if you use Mailchimp/Mailgun): add `MAILCHIMP_*` and `MAILGUN_*`. If you don’t, leave them unset – the app runs without them (emails to console, no mailing list).

5. Save. Render will redeploy with the new env vars.

---

## 5. Make sure the build runs

- **Build command** should be: `./build.sh`
- **Start command** should be: `gunicorn cinemaple.wsgi`

If you didn’t use the Blueprint, set these manually.  
If the build fails because `build.sh` isn’t executable, in your repo run:

```bash
git update-index --chmod=+x build.sh
git add build.sh
git commit -m "Make build.sh executable"
git push
```

Then trigger a new deploy on Render.

---

## 6. Custom domain (www.cinemaple.com)

1. In the **cinemaple** web service → **Settings** → **Custom Domains**.
2. Add **www.cinemaple.com** (and **cinemaple.com** if you use the root domain).  
   Render will show the DNS target (e.g. a CNAME like `cinemaple-xxxx.onrender.com`).
3. In **Cloudflare** (where cinemaple.com is hosted):
   - **DNS** → Edit the record for **www** (and **@** for root if needed).
   - Set **www** to **CNAME** → target = the Render hostname (e.g. `cinemaple-xxxx.onrender.com`).
   - For **@** (root), use CNAME to that same hostname, or use Cloudflare’s “proxy to root” if you use it.
4. In Cloudflare **SSL/TLS**, use **Full** or **Full (strict)** so HTTPS works end-to-end.

After DNS propagates, https://www.cinemaple.com will hit your Render app.

---

## 7. Optional: restore a database backup

Only relevant if you have an **existing backup file** (e.g. from before Heroku was removed). If you never exported the DB, skip this.

1. In Render → **cinemaple-db** → **Info** → copy the **External Database URL** (or Internal if you’re restoring from a machine that can reach it).
2. Restore the dump:

   ```bash
   psql "PASTE_RENDER_DATABASE_URL_HERE" < your_backup.sql
   ```

3. Redeploy the **cinemaple** web service.  
   If you have no backup, the app runs with a **fresh database** (new users, new movie nights).

---

## Summary

| Step | Action |
|------|--------|
| 1 | Get or create **required** secrets: reCAPTCHA, TMDb, 3 salts (Mailchimp/Mailgun optional). |
| 2 | Push repo (with `render.yaml`, `build.sh`) to GitHub. |
| 3 | Render → New → Blueprint → connect repo → Apply. |
| 4 | Add required env vars in Render → Environment (reCAPTCHA, salts, TMDB; skip Mailchimp/Mailgun if not using). |
| 5 | Confirm build = `./build.sh`, start = `gunicorn cinemaple.wsgi`. |
| 6 | Add www.cinemaple.com (and cinemaple.com) in Render; point Cloudflare CNAME to Render. |

After the first deploy, the app will be at `https://cinemaple-xxxx.onrender.com`. After DNS is set, it will also be at **https://www.cinemaple.com**.  
Free tier: service spins down after ~15 min inactivity; first request after that may take up to ~1 minute.  
**No Heroku access:** You’re starting with a new DB and new secrets; old user/movie data is not recoverable without a backup you already have.
