import io
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import quote

from app import SERVICE_IMAGES, create_app


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "WTF_CSRF_ENABLED": False,
                "MAIL_USERNAME": None,
                "MAIL_PASSWORD": None,
                "MAIL_DEFAULT_SENDER": None,
            }
        )
        self.client = self.app.test_client()

    def test_homepage_defaults_to_arabic(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('lang="ar" dir="rtl"', response.get_data(as_text=True))
        self.assertIn("تأسست ISCA عام 2023", response.get_data(as_text=True))
        self.assertIn('href="/services/?lang=ar"', response.get_data(as_text=True))
        self.assertIn('href="/contact/?lang=ar"', response.get_data(as_text=True))

    def test_homepage_can_switch_to_english(self):
        response = self.client.get("/?lang=en")
        content = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('lang="en" dir="ltr"', content)
        self.assertIn("Founded in 2023", content)
        self.assertIn('href="/services/?lang=en"', content)

    def test_header_has_accessible_active_navigation_in_both_languages(self):
        for language, current_link, nav_label, menu_labels in (
            (
                "ar",
                '<a href="/?lang=ar" aria-current="page">الرئيسية</a>',
                'aria-label="التنقل الرئيسي"',
                'data-open-label="فتح القائمة" data-close-label="إغلاق القائمة"',
            ),
            (
                "en",
                '<a href="/?lang=en" aria-current="page">Home</a>',
                'aria-label="Main navigation"',
                'data-open-label="Open menu" data-close-label="Close menu"',
            ),
        ):
            with self.subTest(language=language):
                response = self.client.get(f"/?lang={language}")
                content = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn(current_link, content)
                self.assertIn(nav_label, content)
                self.assertIn(menu_labels, content)
                self.assertIn('aria-controls="primary-nav"', content)

        service_response = self.client.get("/services/iso-certification-readiness/?lang=en")
        self.assertIn(
            '<a href="/services/?lang=en" aria-current="page">Services</a>',
            service_response.get_data(as_text=True),
        )

    def test_homepage_has_dynamic_bilingual_carousel_slides(self):
        carousel_script = (
            Path(__file__).parents[1] / "static" / "js" / "site.js"
        ).read_text(encoding="utf-8")
        for language, expected_title in (
            ("ar", "تصميم المطابخ وخدمات الأغذية"),
            ("en", "Commercial kitchen and food service design"),
        ):
            with self.subTest(language=language):
                response = self.client.get(f"/?lang={language}")
                content = response.get_data(as_text=True)
                self.assertEqual(response.status_code, 200)
                self.assertIn('data-carousel role="region"', content)
                self.assertIn(expected_title, content)
                self.assertEqual(content.count('data-carousel-slide'), 3)
                self.assertNotIn('data-carousel-to=', content)
                self.assertNotIn('data-carousel-next', content)
                self.assertNotIn('data-carousel-prev', content)
                self.assertIn("setInterval(showNext, 2000)", carousel_script)

    def test_carousel_images_are_available(self):
        gallery = Path(self.app.static_folder) / "images" / "gallery"
        image_paths = sorted(gallery.glob("slide-*.jpg"))
        self.assertEqual(len(image_paths), 3)

        for image_path in image_paths:
            with self.subTest(image=image_path.name):
                response = self.client.get(
                    f"/static/images/gallery/{quote(image_path.name, safe='')}"
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "image/jpeg")
                response.close()

    def test_primary_pages_render_in_both_languages(self):
        routes = ("/about/", "/services/", "/training/", "/news/", "/contact/")
        for route in routes:
            for language in ("ar", "en"):
                with self.subTest(route=route, language=language):
                    response = self.client.get(f"{route}?lang={language}")
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(
                        f'<html lang="{language}" dir="{"rtl" if language == "ar" else "ltr"}">',
                        response.get_data(as_text=True),
                    )

    def test_service_detail_routes_and_unknown_services(self):
        response = self.client.get("/services/iso-certification-readiness/?lang=en")
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "ISCA does not issue ISO certificates.",
            response.get_data(as_text=True),
        )
        self.assertEqual(
            self.client.get("/services/unknown-service/").status_code,
            404,
        )

    def test_service_images_match_files_and_are_embedded_in_pages(self):
        image_names = {
            filename
            for images in SERVICE_IMAGES.values()
            for filename, _alt_ar, _alt_en in images
        }
        available_images = {
            path.name
            for path in (Path(self.app.static_folder) / "images" / "services").glob("*.jpg")
        }
        self.assertEqual(image_names, available_images)

        services_page = self.client.get("/services/?lang=ar").get_data(as_text=True)
        self.assertEqual(services_page.count('class="service-card-image"'), 8)
        for filename in image_names:
            with self.subTest(filename=filename):
                response = self.client.get(
                    f"/static/images/services/{quote(filename, safe='')}"
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "image/jpeg")
                response.close()

        training_page = self.client.get("/services/training-and-coaching/?lang=en")
        self.assertEqual(training_page.status_code, 200)
        self.assertEqual(
            training_page.get_data(as_text=True).count('decoding="async"'),
            len(SERVICE_IMAGES["training-and-coaching"]),
        )

    def test_future_portal_routes_are_not_exposed(self):
        for route in ("/login/", "/portal/client/", "/portal/staff/"):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(route).status_code, 404)

    def test_training_page_links_to_prefilled_training_inquiry(self):
        response = self.client.get("/training/?lang=en")
        self.assertIn(
            '/contact/?lang=en&amp;service=training',
            response.get_data(as_text=True),
        )
        contact = self.client.get("/contact/?lang=en&service=training")
        self.assertEqual(contact.status_code, 200)
        self.assertIn('<option selected value="training">Training</option>', contact.get_data(as_text=True))

    def test_inquiry_requires_configured_mail_delivery(self):
        with self.client.session_transaction() as current_session:
            current_session["csrf_token"] = "test-token"

        response = self.client.post(
            "/contact",
            data={
                "csrf_token": "test-token",
                "language": "en",
                "name": "Test Client",
                "company": "Example Foods",
                "email": "client@example.com",
                "phone": "",
                "service": "consultation",
                "message": "We need food safety consulting.",
                "website": "",
            },
        )
        content = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 503)
        self.assertIn("We could not send your request right now.", content)

    def test_inquiry_sends_allowed_attachment(self):
        self.app.config.update(
            MAIL_USERNAME="support@isca-eg.com",
            MAIL_PASSWORD="test-password",
            MAIL_DEFAULT_SENDER="support@isca-eg.com",
        )
        with self.client.session_transaction() as current_session:
            current_session["csrf_token"] = "test-token"

        with patch("app.Mail.send") as send_mail:
            response = self.client.post(
                "/contact",
                data={
                    "csrf_token": "test-token",
                    "language": "en",
                    "name": "Test Client",
                    "company": "Example Foods",
                    "email": "client@example.com",
                    "phone": "",
                    "service": "consultation",
                    "message": "We need food safety consulting.",
                    "website": "",
                    "attachment": (io.BytesIO(b"sample document"), "invoice.pdf"),
                },
            )

        self.assertEqual(response.status_code, 302)
        send_mail.assert_called_once()
        sent_message = send_mail.call_args.args[-1]
        self.assertEqual(sent_message.recipients, ["support@isca-eg.com"])
        self.assertEqual(sent_message.reply_to, "client@example.com")
        self.assertEqual(sent_message.attachments[0].filename, "invoice.pdf")

    def test_disallowed_attachment_is_rejected(self):
        with self.client.session_transaction() as current_session:
            current_session["csrf_token"] = "test-token"

        response = self.client.post(
            "/contact",
            data={
                "csrf_token": "test-token",
                "language": "en",
                "name": "Test Client",
                "company": "",
                "email": "client@example.com",
                "phone": "",
                "service": "training",
                "message": "Please contact me.",
                "website": "",
                "attachment": (io.BytesIO(b"not an executable"), "invoice.exe"),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "This file type is not allowed.",
            response.get_data(as_text=True),
        )

    def test_security_headers_are_present(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])


if __name__ == "__main__":
    unittest.main()
