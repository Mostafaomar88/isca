# ISCA Website

A bilingual Flask website for ISCA, with dedicated company, services, training, news and contact pages.

## Routes

- `/` — home page
- `/about/` — company information
- `/services/` — service directory
- `/services/<service-slug>/` — individual service details
- `/training/` — training information
- `/news/` — news and updates
- `/contact/` — inquiry form

The login and client/staff portal routes are intentionally not exposed until authentication and role-based access control are implemented.

Service photographs are served from `static/images/services/` and mapped to their service pages by descriptive source filenames. The homepage hero uses the optimized images in `static/images/gallery/` as a full-section background slideshow, configured bilingually in `app.py`. It changes images every 2 seconds and pauses on hover, a hidden browser tab, or when reduced motion is enabled. The background slideshow has no manual controls.

The carousel configuration is ready to be moved to a database when a CMS is introduced; image uploads and database-backed slide management are not enabled yet.

## Run locally

1. Use Python 3.10 or later.
2. Install dependencies with `python -m pip install -r requirements.txt`.
3. Set a local `SECRET_KEY` and the SMTP settings listed in `.env.example`.
4. Start the development server with `python app.py`.

The site opens in Arabic by default. Use the language switch in the header to view the English version.

## Configure Hostinger

Create a Python application in hPanel with `passenger_wsgi.py` as the startup file and `application` as the WSGI entry point. Install the packages from `requirements.txt`, then configure these environment variables in the hosting environment:

- `APP_ENV=production`
- `SECRET_KEY` with a securely generated random value
- `MAIL_USERNAME` and `MAIL_PASSWORD` for the Hostinger mailbox
- `MAIL_DEFAULT_SENDER` set to the same mailbox
- `SUPPORT_EMAIL=support@isca-eg.com`
- `MAIL_SERVER=smtp.hostinger.com`, `MAIL_PORT=465`, `MAIL_USE_SSL=true`, and `MAIL_USE_TLS=false`

Do not commit real credentials. The inquiry form reports an error instead of indicating success when mail delivery is not configured or fails.

Attachments are limited to 8 MB and accepted only as PDF, image, or Office document files. They are emailed to the support mailbox and are not written to a publicly accessible folder.

## Tests

Run the application tests with `python -m unittest discover -s tests`.
