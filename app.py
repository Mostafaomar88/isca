import logging
import mimetypes
import os
import secrets
import smtplib
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import FileField, HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Regexp
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"}
SUPPORTED_LANGUAGES = {"ar", "en"}
SERVICE_KEYS = ("consultation", "training", "kitchen_design")
SERVICE_SLUGS = {
    "commercial-kitchen-design": 0,
    "food-safety-consulting": 1,
    "food-safety-audits": 2,
    "training-and-coaching": 3,
    "iso-certification-readiness": 4,
    "supplier-qualification": 5,
    "licensing-and-compliance": 6,
    "ongoing-support": 7,
}
SERVICE_IMAGES = {
    "commercial-kitchen-design": [
        ("Baked goods inside a restaurant.jpg", "مراجعة إعداد الطعام داخل منشأة غذائية", "Reviewing food preparation in a food business"),
        ("Factory workers' security2.jpg", "فني يعمل على تجهيزات مطبخ تجاري", "Technician working on commercial kitchen equipment"),
        ("quality-service-38.jpg", "خط إنتاج داخل مصنع للأغذية", "Food production line in a factory"),
    ],
    "food-safety-consulting": [
        ("food safety practices & procodures.jpg", "دليل ممارسات وإجراءات سلامة الغذاء", "Food safety practices and procedures guide"),
        ("Fork and knife.jpg", "تقييم مخاطر سلامة الغذاء وجودته", "Food safety and quality risk assessment"),
        ("quality-service-36.jpg", "خطوات تطبيق ممارسات سلامة الغذاء", "Steps for applying food safety practices"),
        ("quality-service-37.jpg", "ممارسات النظافة في مصنع أغذية", "Hygiene practices in a food factory"),
    ],
    "food-safety-audits": [
        ("quality control .jpg", "مراجعة الجودة والرقابة على الأغذية", "Food quality control review"),
        ("Factory workers' security.jpg", "فريق يراجع جودة العمليات في منشأة غذائية", "Team reviewing quality in a food operation"),
        ("Factory workers' security3.jpg", "فحص وصيانة معدات صناعية", "Inspection and maintenance of industrial equipment"),
        ("quality-service-27.jpg", "فحص هندسي لمرافق ومعدات صناعية", "Engineering inspection of industrial facilities"),
        ("quality-service-29.jpg", "متابعة أداء نظام ضمان الجودة", "Quality assurance system follow-up"),
        ("quality-service-30.jpg", "فريق يراجع متطلبات السلامة في موقع عمل", "Team reviewing safety requirements on site"),
    ],
    "training-and-coaching": [
        ("Firefighting drills.jpg", "تدريب ميداني على إجراءات السلامة", "Practical safety procedures training"),
        ("Kitchen staff safety.jpg", "تدريب العاملين على التعامل الآمن مع الغذاء", "Training staff in safe food handling"),
        ("worker safety.jpg", "توعية العاملين بمهمات وإجراءات السلامة", "Worker safety equipment and procedures"),
        ("Factory workers' security4.jpg", "تطبيق إجراءات النظافة في منشأة إنتاج", "Hygiene practices in a production facility"),
        ("quality-service-33.jpg", "تدريب على معايير السلامة والجودة", "Safety and quality standards training"),
    ],
    "iso-certification-readiness": [
        ("quality-service-28.jpg", "مخطط لنظام ضمان الجودة والتحسين", "Quality assurance and improvement system diagram"),
        ("quality-service-34.jpg", "ممارسات ضمان الجودة في بيئة العمل", "Quality assurance practices in the workplace"),
    ],
    "supplier-qualification": [
        ("Food analysis.jpg", "تحليل عينات غذائية في المختبر", "Food sample analysis in a laboratory"),
        ("Food analysis2.jpg", "فحوصات مخبرية على المنتجات الغذائية", "Laboratory testing of food products"),
        ("quality-service-31.jpg", "اختبارات ميكروبية لعينات غذائية", "Microbiological testing of food samples"),
        ("quality-service-32.jpg", "مختبر لفحص جودة وسلامة الغذاء", "Laboratory assessing food quality and safety"),
        ("quality-service-35.jpg", "مراجعة جودة المنتجات الغذائية", "Food product quality review"),
    ],
    "licensing-and-compliance": [
        ("Factory workers' security2.jpg", "مراجعة جاهزية معدات ومرافق المنشأة", "Review of facility equipment and readiness"),
        ("quality-service-27.jpg", "تقييم هندسي لمرافق المنشأة", "Engineering assessment of facility infrastructure"),
    ],
    "ongoing-support": [
        ("quality-service-29.jpg", "متابعة خطة ضمان الجودة", "Quality assurance plan follow-up"),
        ("quality-service-36.jpg", "ممارسات يومية لدعم سلامة الغذاء", "Daily practices supporting food safety"),
    ],
}

TRANSLATIONS = {
    "ar": {
        "language_name": "العربية",
        "page_title": "ISCA | سلامة الغذاء والاستشارات والتدريب",
        "page_description": "حلول عملية ومستدامة لسلامة الغذاء، تصميم المطابخ التجارية، التدقيق والتدريب.",
        "nav_training": "التدريب",
        "nav_news": "الأخبار",
        "skip_link": "انتقل إلى المحتوى",
        "nav_home": "الرئيسية",
        "nav_about": "من نحن",
        "nav_services": "خدماتنا",
        "nav_clients": "قطاعات نخدمها",
        "nav_contact": "تواصل معنا",
        "language_switch": "English",
        "language_switch_label": "عرض الموقع باللغة الإنجليزية",
        "nav_label": "التنقل الرئيسي",
        "menu_label": "فتح القائمة",
        "menu_close_label": "إغلاق القائمة",
        "hero_eyebrow": "استشارات سلامة الغذاء والتدريب",
        "hero_title": "سلامة غذاء <span>بسيطة، ذكية، ومستدامة.</span>",
        "hero_text": "نساعد منشآت الأغذية والضيافة على بناء ممارسات أكثر أمانًا وكفاءة، بحلول عملية تناسب واقع التشغيل.",
        "hero_primary": "اكتشف خدماتنا",
        "hero_secondary": "اطلب استشارة",
        "hero_card_label": "منهجنا",
        "hero_card_title": "حلول واقعية تبدأ من احتياجك",
        "hero_card_text": "من تصميم المطبخ إلى تأهيل الفريق، نعمل معك على خطوات واضحة وقابلة للتطبيق.",
        "hero_card_tag": "Simple · Smart · Sustainable",
        "gallery": {
            "role": "معرض شرائح",
            "label": "معرض خدمات ISCA",
            "previous": "الصورة السابقة",
            "next": "الصورة التالية",
            "pause": "إيقاف العرض التلقائي",
            "resume": "استئناف العرض التلقائي",
            "slide": "الشريحة",
            "of": "من",
            "slides": [
                {
                    "image": "slide-01.jpg",
                    "title": "تصميم المطابخ وخدمات الأغذية",
                    "alt": "مختصان يراجعان منتجات مخبوزة داخل منشأة غذائية",
                    "endpoint": "service_detail",
                    "view_args": {"service_slug": "commercial-kitchen-design"},
                },
                {
                    "image": "slide-02.jpg",
                    "title": "فحص سلامة وجودة الغذاء",
                    "alt": "مختص يفحص عينة غذائية في المختبر",
                    "endpoint": "service_detail",
                    "view_args": {"service_slug": "supplier-qualification"},
                },
                {
                    "image": "slide-03.jpg",
                    "title": "تدريب الفرق على إجراءات السلامة",
                    "alt": "فريق يتدرب على إجراءات السلامة في موقع العمل",
                    "endpoint": "training",
                    "view_args": {},
                },
            ],
        },
        "trust_label": "مجالات نساندها",
        "trust_hotels": "الفنادق والضيافة",
        "trust_food": "منشآت الأغذية",
        "trust_factories": "المصانع والموردون",
        "about_eyebrow": "من نحن",
        "about_title": "خبرة متخصصة، وشراكة تصنع فرقًا في التشغيل.",
        "about_text": "تأسست ISCA عام 2023 لتقديم استشارات وتدريب متخصصين في سلامة الغذاء. نؤمن بأن الحل الجيد هو ما يرفع مستوى السلامة ويظل عمليًا ومستدامًا في بيئة العمل.",
        "about_note": "نعمل بعقلية قائمة على تقييم المخاطر، وبشراكة وثيقة مع فرق عملائنا.",
        "about_vision_label": "رؤيتنا",
        "about_vision": "أن نكون الشريك الأول لمنشآت الأغذية التي تبحث عن حلول حقيقية وثقافة راسخة لسلامة الغذاء.",
        "services_eyebrow": "خدماتنا",
        "services_title": "دعم فني يواكب احتياج منشأتك.",
        "services_intro": "حلول متكاملة تبدأ من التخطيط والتأسيس، وتمتد إلى التدريب والتدقيق والتحسين المستمر.",
        "services": [
            {
                "title": "تصميم المطابخ التجارية",
                "description": "مراجعة وتخطيط المطابخ ومناطق إعداد الطعام بما يراعي سير العمل ومتطلبات السلامة والتشغيل.",
            },
            {
                "title": "استشارات سلامة الغذاء",
                "description": "دعم فني لتقييم الوضع الحالي، وتحديد فرص التحسين، وبناء ممارسات مناسبة لطبيعة المنشأة.",
            },
            {
                "title": "التدقيق وتحليل الفجوات",
                "description": "تقييم الأنظمة والممارسات التشغيلية، وتحديد نقاط الضعف، ومساندة الفريق في الإجراءات التصحيحية.",
            },
            {
                "title": "التدريب والتوجيه",
                "description": "برامج تدريبية تفاعلية مصممة لاحتياج العمل، من فرق التشغيل إلى المشرفين والإدارة.",
            },
            {
                "title": "التأهيل لشهادات ISO",
                "description": "استشارات وتدقيق وتدريب لتأهيل المنشأة للحصول على الشهادة من جهة منح خارجية.",
            },
            {
                "title": "تأهيل الموردين وفحص المنتجات",
                "description": "مساندة المنشآت في تقييم الموردين وفحص المنتجات وتعزيز سلامة وجودة سلسلة الإمداد.",
            },
            {
                "title": "دعم التراخيص والامتثال",
                "description": "إرشاد فني لتنظيم متطلبات تراخيص منشآت الأغذية ومتابعة متطلبات الجهات المختصة.",
            },
            {
                "title": "المتابعة والتحسين المستمر",
                "description": "متابعة الأداء وتوثيق الملاحظات ومساندة فرق العمل في ترسيخ الممارسات اليومية.",
            },
        ],
        "services_disclaimer": "تُقدَّم خدمات التأهيل لشهادات ISO بالتعاون مع جهات منح خارجية؛ ولا تصدر ISCA شهادات ISO للمنشآت.",
        "approach_eyebrow": "كيف نعمل",
        "approach_title": "خطوات واضحة، من التقييم إلى التحسين.",
        "approach_steps": [
            {
                "title": "نفهم احتياجك",
                "description": "نتعرف على نوع المنشأة وطبيعة التشغيل والتحديات التي تريد معالجتها.",
            },
            {
                "title": "نقيّم ونخطط",
                "description": "نحدد الأولويات ونقترح خطوات عملية تناسب فريقك ومتطلبات نشاطك.",
            },
            {
                "title": "ندرب ونتابع",
                "description": "نساند التنفيذ ونبني المعرفة اللازمة لاستمرار التحسين داخل المنشأة.",
            },
        ],
        "sectors_eyebrow": "خبرتنا في الميدان",
        "sectors_title": "نساند قطاعات متعددة في منظومة الغذاء والضيافة.",
        "sectors_intro": "تشمل خبرات الشركة الفنادق والرحلات النيلية والمطاعم والمصانع ومنشآت إعداد وتقديم الطعام.",
        "sector_hotels": "الفنادق والمنتجعات",
        "sector_cruises": "الرحلات النيلية",
        "sector_restaurants": "المطاعم والمطابخ",
        "sector_factories": "مصانع الأغذية",
        "sector_suppliers": "الموردون والتوزيع",
        "contact_eyebrow": "ابدأ الحديث معنا",
        "contact_title": "ما التحدي الذي تريد أن نساعدك فيه؟",
        "contact_intro": "أرسل تفاصيل طلبك، وسيتمكن فريقنا من فهم احتياجك والتواصل معك.",
        "contact_email_label": "البريد الإلكتروني",
        "contact_email_note": "يمكنك مراسلتنا مباشرة في أي وقت.",
        "form_name": "الاسم",
        "form_name_placeholder": "الاسم الكامل",
        "form_company": "اسم المنشأة",
        "form_company_placeholder": "اسم الشركة أو المنشأة (اختياري)",
        "form_email": "البريد الإلكتروني",
        "form_email_placeholder": "name@example.com",
        "form_phone": "رقم الهاتف",
        "form_phone_placeholder": "رقم يمكننا التواصل عبره (اختياري)",
        "form_service": "الخدمة المطلوبة",
        "form_service_placeholder": "اختر الخدمة",
        "service_consultation": "استشارة سلامة الغذاء",
        "service_training": "التدريب",
        "service_kitchen_design": "تصميم مطبخ تجاري",
        "form_message": "تفاصيل الطلب",
        "form_message_placeholder": "اكتب نبذة عن احتياجك أو التحدي الذي تواجهه...",
        "form_file": "مرفق (اختياري)",
        "form_file_note": "PDF أو صورة أو مستند Office — بحد أقصى 8 ميجابايت.",
        "form_file_size_error": "حجم الملف المرفق أكبر من الحد المسموح (8 ميجابايت).",
        "form_submit": "إرسال الطلب",
        "form_privacy": "لن تُحفظ الملفات في مجلد عام. تُرسل المرفقات إلى فريق ISCA عبر البريد.",
        "form_success": "شكرًا لتواصلك. تم إرسال طلبك إلى فريق ISCA بنجاح.",
        "form_error": "تعذر إرسال الطلب حاليًا. يرجى مراسلتنا مباشرة على",
        "form_validation_error": "يرجى مراجعة البيانات المطلوبة في النموذج.",
        "form_file_error": "نوع الملف غير مسموح. ارفع PDF أو صورة أو مستند Office فقط.",
        "form_size_error": "حجم الطلب أكبر من الحد المسموح (10 ميجابايت).",
        "form_spam_error": "تعذر إرسال الطلب. حاول مرة أخرى.",
        "footer_tagline": "سلامة الغذاء، ببساطة وذكاء واستدامة.",
        "footer_rights": "جميع الحقوق محفوظة.",
        "footer_founded": "تأسست عام 2023",
    },
    "en": {
        "language_name": "English",
        "page_title": "ISCA | Food Safety Consulting & Training",
        "page_description": "Practical, sustainable food safety, commercial kitchen design, auditing and training solutions.",
        "nav_training": "Training",
        "nav_news": "News",
        "skip_link": "Skip to content",
        "nav_home": "Home",
        "nav_about": "About",
        "nav_services": "Services",
        "nav_clients": "Who we serve",
        "nav_contact": "Contact",
        "language_switch": "العربية",
        "language_switch_label": "View the website in Arabic",
        "nav_label": "Main navigation",
        "menu_label": "Open menu",
        "menu_close_label": "Close menu",
        "hero_eyebrow": "Food safety consulting & training",
        "hero_title": "Food safety made <span>simple, smart and sustainable.</span>",
        "hero_text": "We help food and hospitality businesses build safer, more efficient practices with practical solutions shaped around real operations.",
        "hero_primary": "Explore our services",
        "hero_secondary": "Request a consultation",
        "hero_card_label": "Our approach",
        "hero_card_title": "Practical solutions start with you",
        "hero_card_text": "From kitchen design to team development, we work with you on clear, actionable steps.",
        "hero_card_tag": "Simple · Smart · Sustainable",
        "gallery": {
            "role": "Image slideshow",
            "label": "ISCA services gallery",
            "previous": "Previous slide",
            "next": "Next slide",
            "pause": "Pause automatic slideshow",
            "resume": "Resume automatic slideshow",
            "slide": "Slide",
            "of": "of",
            "slides": [
                {
                    "image": "slide-01.jpg",
                    "title": "Commercial kitchen and food service design",
                    "alt": "Specialists reviewing baked products in a food facility",
                    "endpoint": "service_detail",
                    "view_args": {"service_slug": "commercial-kitchen-design"},
                },
                {
                    "image": "slide-02.jpg",
                    "title": "Food safety and quality testing",
                    "alt": "Specialist examining a food sample in a laboratory",
                    "endpoint": "service_detail",
                    "view_args": {"service_slug": "supplier-qualification"},
                },
                {
                    "image": "slide-03.jpg",
                    "title": "Safety training for operational teams",
                    "alt": "A team participating in on-site safety training",
                    "endpoint": "training",
                    "view_args": {},
                },
            ],
        },
        "trust_label": "Supporting",
        "trust_hotels": "Hotels & hospitality",
        "trust_food": "Food businesses",
        "trust_factories": "Factories & suppliers",
        "about_eyebrow": "About us",
        "about_title": "Specialist knowledge. A partnership that improves operations.",
        "about_text": "Founded in 2023, ISCA provides specialist food safety consulting and training. We believe good solutions improve safety while remaining practical and sustainable in the workplace.",
        "about_note": "We take a risk-based approach and work in close partnership with our clients' teams.",
        "about_vision_label": "Our vision",
        "about_vision": "To be the first choice for food businesses seeking a trusted partner, practical solutions and a lasting food safety culture.",
        "services_eyebrow": "What we do",
        "services_title": "Technical support shaped around your business.",
        "services_intro": "From planning and setup to training, auditing and continuous improvement.",
        "services": [
            {
                "title": "Commercial kitchen design",
                "description": "Reviewing and planning kitchens and food preparation areas around workflow, safety and operational needs.",
            },
            {
                "title": "Food safety consulting",
                "description": "Practical support to assess current practices, identify opportunities and build solutions for your operation.",
            },
            {
                "title": "Audits & gap assessments",
                "description": "Assessing systems and operational practices, identifying gaps and supporting corrective actions.",
            },
            {
                "title": "Training & coaching",
                "description": "Interactive training tailored to your workplace, from frontline teams to supervisors and management.",
            },
            {
                "title": "ISO certification readiness",
                "description": "Consulting, auditing and training to prepare your organization for certification by an external certification body.",
            },
            {
                "title": "Supplier qualification & product inspection",
                "description": "Support with supplier assessment, product inspection and stronger food supply-chain quality and safety.",
            },
            {
                "title": "Licensing & compliance support",
                "description": "Technical guidance to organize food-business licensing requirements and engage with relevant authorities.",
            },
            {
                "title": "Ongoing support & improvement",
                "description": "Follow-up, documented observations and support that help teams sustain better daily practices.",
            },
        ],
        "services_disclaimer": "ISO readiness services support certification by external certification bodies. ISCA does not issue ISO certificates to businesses.",
        "approach_eyebrow": "How we work",
        "approach_title": "Clear steps, from assessment to improvement.",
        "approach_steps": [
            {
                "title": "Understand your needs",
                "description": "We learn about your business, operations and the challenges you want to address.",
            },
            {
                "title": "Assess and plan",
                "description": "We identify priorities and recommend practical steps for your team and business.",
            },
            {
                "title": "Train and follow up",
                "description": "We support implementation and build the knowledge needed for lasting improvement.",
            },
        ],
        "sectors_eyebrow": "On-the-ground experience",
        "sectors_title": "Supporting businesses across food and hospitality.",
        "sectors_intro": "The company's experience includes hotels, Nile cruises, restaurants, factories and food service operations.",
        "sector_hotels": "Hotels & resorts",
        "sector_cruises": "Nile cruise boats",
        "sector_restaurants": "Restaurants & kitchens",
        "sector_factories": "Food factories",
        "sector_suppliers": "Suppliers & distribution",
        "contact_eyebrow": "Let's talk",
        "contact_title": "What would you like help with?",
        "contact_intro": "Tell us a little about your request so our team can understand your needs and get in touch.",
        "contact_email_label": "Email us",
        "contact_email_note": "You can also contact us directly at any time.",
        "form_name": "Name",
        "form_name_placeholder": "Your full name",
        "form_company": "Business name",
        "form_company_placeholder": "Company or business name (optional)",
        "form_email": "Email address",
        "form_email_placeholder": "name@example.com",
        "form_phone": "Phone number",
        "form_phone_placeholder": "A number where we can reach you (optional)",
        "form_service": "Service of interest",
        "form_service_placeholder": "Choose a service",
        "service_consultation": "Food safety consulting",
        "service_training": "Training",
        "service_kitchen_design": "Commercial kitchen design",
        "form_message": "Request details",
        "form_message_placeholder": "Tell us about your needs or the challenge you are facing...",
        "form_file": "Attachment (optional)",
        "form_file_note": "PDF, image or Office document — up to 8 MB.",
        "form_file_size_error": "The attachment exceeds the maximum allowed size of 8 MB.",
        "form_submit": "Send your request",
        "form_privacy": "Files are not stored in a public folder. Attachments are emailed to the ISCA team.",
        "form_success": "Thank you for reaching out. Your request was sent to the ISCA team.",
        "form_error": "We could not send your request right now. Please email us directly at",
        "form_validation_error": "Please review the required information in the form.",
        "form_file_error": "This file type is not allowed. Please upload a PDF, image or Office document.",
        "form_size_error": "Your request exceeds the maximum allowed size of 10 MB.",
        "form_spam_error": "We could not send your request. Please try again.",
        "footer_tagline": "Food safety, made simple, smart and sustainable.",
        "footer_rights": "All rights reserved.",
        "footer_founded": "Founded in 2023",
    },
}

PAGE_COPY = {
    "ar": {
        "home": {
            "title": "سلامة الغذاء والاستشارات والتدريب",
            "description": "حلول عملية ومستدامة لسلامة الغذاء، تصميم المطابخ التجارية، التدقيق والتدريب.",
        },
        "about": {
            "title": "من نحن",
            "description": "تعرف على ISCA ونهجها في استشارات سلامة الغذاء والتدريب.",
            "eyebrow": "عن ISCA",
            "heading": "شريك متخصص في سلامة الغذاء.",
            "intro": "تأسست ISCA عام 2023 لتقديم استشارات وتدريب متخصصين في سلامة الغذاء ودعم منشآت الأغذية والضيافة.",
            "approach_heading": "حلول بسيطة، ذكية، ومستدامة",
            "approach": "نعمل بعقلية قائمة على تقييم المخاطر، ونصمم توصيات عملية تراعي واقع التشغيل وتساعد فرق العمل على ترسيخ ثقافة سلامة الغذاء.",
            "vision_heading": "رؤيتنا",
            "vision": "أن نكون الشريك الأول لمنشآت الأغذية التي تبحث عن حلول حقيقية وثقافة راسخة لسلامة الغذاء.",
            "leadership_heading": "خبرة تقودها المعرفة",
            "leadership": "تقود ISCA خبرات متخصصة في تصميم خدمات الأغذية والمطابخ التجارية والتدقيق والتدريب والاستشارات.",
            "scope_heading": "نطاق الشهادات",
            "scope": "تقدم ISCA خدمات الاستشارات والتدقيق والتدريب لتأهيل المنشآت للحصول على شهادات ISO من جهات منح خارجية. لا تصدر ISCA شهادات ISO للمنشآت.",
        },
        "services": {
            "title": "خدماتنا",
            "description": "استكشف خدمات ISCA في استشارات سلامة الغذاء والتدقيق والتدريب وتصميم المطابخ.",
            "eyebrow": "ما نقدمه",
            "heading": "خدمات عملية تناسب احتياج منشأتك.",
            "intro": "اختر مجال الدعم المناسب، أو تواصل معنا لمناقشة احتياجات منشأتك.",
            "detail_label": "تفاصيل الخدمة",
            "contact": "اطلب هذه الخدمة",
            "back": "العودة إلى الخدمات",
        },
        "training": {
            "title": "التدريب",
            "description": "برامج تدريب وتوجيه في سلامة الغذاء مصممة لاحتياجات فرق العمل.",
            "eyebrow": "أكاديمية التدريب",
            "heading": "معرفة عملية تدعم فرقك.",
            "intro": "تصمم ISCA برامج تدريب وتوجيه متخصصة في سلامة الغذاء وفق طبيعة المنشأة واحتياجات فريقها.",
            "programs_heading": "مجالات التدريب",
            "program_one": "أساسيات وتشريعات سلامة الغذاء",
            "program_two": "ممارسات التشغيل والتعامل الآمن مع الغذاء",
            "program_three": "تدريب مخصص للفرق والمشرفين والإدارة",
            "note": "تختلف موضوعات التدريب وطريقته وفق احتياج المنشأة. تواصل معنا لمناقشة البرنامج المناسب والمواعيد المتاحة.",
            "register": "استفسر عن التدريب",
        },
        "news": {
            "title": "الأخبار",
            "description": "آخر الأخبار والتحديثات من ISCA.",
            "eyebrow": "المعرفة والتحديثات",
            "heading": "أخبار ISCA",
            "intro": "تظهر هنا المقالات والتحديثات والفعاليات بعد اعتماد محتواها للنشر.",
            "empty": "لا توجد أخبار منشورة حاليًا. تابعنا للاطلاع على التحديثات القادمة.",
        },
        "contact": {
            "title": "تواصل معنا",
            "description": "تواصل مع ISCA للاستشارات أو التدريب أو تصميم المطابخ التجارية.",
            "eyebrow": "نحن هنا للمساعدة",
            "heading": "أخبرنا كيف يمكننا دعمك.",
            "intro": "أرسل تفاصيل استفسارك، ويمكنك إرفاق ملف يساعدنا على فهم احتياج منشأتك.",
        },
        "service_detail": {
            "title": "تفاصيل الخدمة",
            "description": "معلومات حول خدمات ISCA في سلامة الغذاء والتدريب والاستشارات.",
            "eyebrow": "خدمات ISCA",
            "detail_label": "عن هذه الخدمة",
            "contact": "اطلب هذه الخدمة",
            "back": "العودة إلى الخدمات",
            "iso_note": "خدمات التأهيل لشهادات ISO تدعم الحصول على الشهادة من جهة منح خارجية؛ ولا تصدر ISCA شهادات ISO.",
        },
    },
    "en": {
        "home": {
            "title": "Food safety consulting & training",
            "description": "Practical, sustainable food safety, commercial kitchen design, auditing and training solutions.",
        },
        "about": {
            "title": "About us",
            "description": "Learn about ISCA and its approach to food safety consulting and training.",
            "eyebrow": "About ISCA",
            "heading": "Your specialist food safety partner.",
            "intro": "Founded in 2023, ISCA provides specialist food safety consulting and training to food and hospitality businesses.",
            "approach_heading": "Simple, smart and sustainable solutions",
            "approach": "We take a risk-based approach and develop practical recommendations shaped around real operations and lasting food safety culture.",
            "vision_heading": "Our vision",
            "vision": "To be the first choice for food businesses seeking a trusted partner, practical solutions and a lasting food safety culture.",
            "leadership_heading": "Expertise guided by knowledge",
            "leadership": "ISCA is led by specialists in food service and commercial kitchen design, auditing, training and consulting.",
            "scope_heading": "Certification scope",
            "scope": "ISCA provides consulting, auditing and training to prepare businesses for ISO certification by external certification bodies. ISCA does not issue ISO certificates to businesses.",
        },
        "services": {
            "title": "Our services",
            "description": "Explore ISCA food safety consulting, auditing, training and kitchen design services.",
            "eyebrow": "What we do",
            "heading": "Practical services for your business.",
            "intro": "Choose the support you need, or contact us to discuss your business requirements.",
            "detail_label": "About this service",
            "contact": "Request this service",
            "back": "Back to services",
        },
        "training": {
            "title": "Training",
            "description": "Food safety training and coaching shaped around your team's needs.",
            "eyebrow": "Training academy",
            "heading": "Practical knowledge for your team.",
            "intro": "ISCA develops specialist food safety training and coaching based on your operation and your team's needs.",
            "programs_heading": "Training topics",
            "program_one": "Food safety fundamentals and regulations",
            "program_two": "Operational practices and safe food handling",
            "program_three": "Tailored training for teams, supervisors and management",
            "note": "Training topics and format are tailored to each business. Contact us to discuss a suitable program and available dates.",
            "register": "Enquire about training",
        },
        "news": {
            "title": "News",
            "description": "The latest news and updates from ISCA.",
            "eyebrow": "Knowledge & updates",
            "heading": "ISCA news",
            "intro": "Articles, updates and events will appear here once they are approved for publication.",
            "empty": "There are no published updates yet. Please check back for future news.",
        },
        "contact": {
            "title": "Contact us",
            "description": "Contact ISCA about consulting, training or commercial kitchen design.",
            "eyebrow": "We are here to help",
            "heading": "Tell us how we can support you.",
            "intro": "Send us the details of your request and attach a file to help us understand your needs.",
        },
        "service_detail": {
            "title": "Service details",
            "description": "Learn more about ISCA food safety, training and consulting services.",
            "eyebrow": "ISCA services",
            "detail_label": "About this service",
            "contact": "Request this service",
            "back": "Back to services",
            "iso_note": "ISO readiness services support certification by external certification bodies. ISCA does not issue ISO certificates.",
        },
    },
}


class InquiryForm(FlaskForm):
    language = HiddenField()
    name = StringField(
        validators=[DataRequired(), Length(max=120)],
    )
    company = StringField(validators=[Length(max=160)])
    email = StringField(
        validators=[
            DataRequired(),
            Length(max=254),
            Regexp(
                r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                message="Enter a valid email address.",
            ),
        ],
    )
    phone = StringField(validators=[Length(max=40)])
    service = SelectField(
        choices=[],
        validators=[DataRequired()],
    )
    message = TextAreaField(validators=[DataRequired(), Length(max=3000)])
    attachment = FileField()
    website = StringField()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        APP_ENV=os.environ.get("APP_ENV", "development"),
        MAIL_SERVER=os.environ.get("MAIL_SERVER", "smtp.hostinger.com"),
        MAIL_PORT=int(os.environ.get("MAIL_PORT", "465")),
        MAIL_USE_SSL=os.environ.get("MAIL_USE_SSL", "true").lower() == "true",
        MAIL_USE_TLS=os.environ.get("MAIL_USE_TLS", "false").lower() == "true",
        MAIL_USERNAME=os.environ.get("MAIL_USERNAME"),
        MAIL_PASSWORD=os.environ.get("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.environ.get("MAIL_DEFAULT_SENDER")
        or os.environ.get("MAIL_USERNAME"),
        SUPPORT_EMAIL=os.environ.get("SUPPORT_EMAIL", "support@isca-eg.com"),
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("APP_ENV", "development")
        == "production",
        WTF_CSRF_TIME_LIMIT=3600,
    )
    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        if app.config["APP_ENV"] == "production":
            raise RuntimeError("Set SECRET_KEY in the production environment.")
        app.config["SECRET_KEY"] = secrets.token_hex(32)
    if app.config["MAIL_USE_SSL"] and app.config["MAIL_USE_TLS"]:
        raise RuntimeError("Configure only one of MAIL_USE_SSL or MAIL_USE_TLS.")

    app.logger.setLevel(logging.INFO)
    mail = Mail(app)

    def get_language():
        requested_language = request.args.get("lang")
        if requested_language in SUPPORTED_LANGUAGES:
            session["language"] = requested_language
        elif request.method == "POST":
            posted_language = request.form.get("language")
            if posted_language in SUPPORTED_LANGUAGES:
                session["language"] = posted_language
        language = session.get("language", "ar")
        return language if language in SUPPORTED_LANGUAGES else "ar"

    def set_form_labels(inquiry_form, texts):
        inquiry_form.language.data = get_language()
        inquiry_form.name.label.text = texts["form_name"]
        inquiry_form.company.label.text = texts["form_company"]
        inquiry_form.email.label.text = texts["form_email"]
        inquiry_form.phone.label.text = texts["form_phone"]
        inquiry_form.service.label.text = texts["form_service"]
        inquiry_form.message.label.text = texts["form_message"]
        inquiry_form.attachment.label.text = texts["form_file"]
        inquiry_form.service.choices = [
            ("consultation", texts["service_consultation"]),
            ("training", texts["service_training"]),
            ("kitchen_design", texts["service_kitchen_design"]),
        ]
        return inquiry_form

    def render_page(template, page_key, form=None, status=200, **context):
        language = get_language()
        texts = TRANSLATIONS[language]
        page = dict(PAGE_COPY[language][page_key])
        if page_key == "service_detail":
            page["title"] = context["service"]["title"]
            page["description"] = context["service"]["description"]
        inquiry_form = set_form_labels(form or InquiryForm(), texts) if page_key == "contact" else None
        if page_key in {"home", "services"}:
            services_by_index = {index: slug for slug, index in SERVICE_SLUGS.items()}
            context["services"] = [
                {
                    **service,
                    "slug": services_by_index[index],
                    "image": get_service_images(services_by_index[index], language)[0],
                }
                for index, service in enumerate(texts["services"])
            ]
        if page_key == "home":
            context["gallery"] = texts["gallery"]
            context["gallery_slides"] = [
                {
                    **slide,
                    "url": url_for(slide["endpoint"], lang=language, **slide["view_args"]),
                }
                for slide in texts["gallery"]["slides"]
            ]
        if page_key == "training":
            context["training_images"] = get_service_images(
                "training-and-coaching",
                language,
            )
        if inquiry_form and request.method == "GET":
            selected_service = request.args.get("service")
            if selected_service in SERVICE_KEYS:
                inquiry_form.service.data = selected_service
        return (
            render_template(
                template,
                language=language,
                texts=texts,
                page=page,
                form=inquiry_form,
                year=datetime.now().year,
                **context,
            ),
            status,
        )

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; form-action 'self'; base-uri 'self'; "
            "frame-ancestors 'none'",
        )
        return response

    @app.get("/")
    def home():
        return render_page("index.html", "home")

    @app.get("/about/")
    def about():
        return render_page("about.html", "about")

    @app.get("/services/")
    def services():
        return render_page("services.html", "services")

    @app.get("/services/<service_slug>/")
    def service_detail(service_slug):
        service_index = SERVICE_SLUGS.get(service_slug)
        if service_index is None:
            abort(404)
        language = get_language()
        service = dict(TRANSLATIONS[language]["services"][service_index])
        service["slug"] = service_slug
        service["images"] = get_service_images(service_slug, language)
        return render_page(
            "service_detail.html",
            "service_detail",
            service=service,
            service_slug=service_slug,
        )

    @app.get("/training/")
    def training():
        return render_page("training.html", "training")

    @app.get("/news/")
    def news():
        return render_page("news.html", "news")

    @app.get("/contact/")
    def contact_page():
        return render_page("contact.html", "contact")

    @app.post("/contact")
    @app.post("/contact/")
    def contact():
        language = get_language()
        texts = TRANSLATIONS[language]
        form = set_form_labels(InquiryForm(), texts)

        if form.website.data:
            flash(texts["form_spam_error"], "error")
            return redirect(url_for("contact_page", lang=language))

        if not form.validate_on_submit():
            flash(texts["form_validation_error"], "error")
            return render_page("contact.html", "contact", form, 400)

        attachment = form.attachment.data
        attachment_name = None
        if attachment and attachment.filename:
            attachment_name = secure_filename(attachment.filename)
            extension = Path(attachment_name).suffix.lower().lstrip(".")
            if extension not in ALLOWED_EXTENSIONS:
                flash(texts["form_file_error"], "error")
                return render_page("contact.html", "contact", form, 400)
            if not attachment_name:
                flash(texts["form_file_error"], "error")
                return render_page("contact.html", "contact", form, 400)
            attachment_data = attachment.read()
            if len(attachment_data) > 8 * 1024 * 1024:
                flash(texts["form_file_size_error"], "error")
                return render_page("contact.html", "contact", form, 400)
        else:
            attachment_data = None

        mail_ready = all(
            app.config.get(key)
            for key in (
                "MAIL_SERVER",
                "MAIL_USERNAME",
                "MAIL_PASSWORD",
                "MAIL_DEFAULT_SENDER",
                "SUPPORT_EMAIL",
            )
        )
        if not mail_ready:
            flash(texts["form_error"], "error")
            return render_page("contact.html", "contact", form, 503)

        service_label = dict(form.service.choices).get(form.service.data, "")
        body_lines = [
            f"Name: {form.name.data.strip()}",
            f"Business: {form.company.data.strip() or '-'}",
            f"Email: {form.email.data.strip()}",
            f"Phone: {form.phone.data.strip() or '-'}",
            f"Service: {service_label}",
            "",
            "Request details:",
            form.message.data.strip(),
        ]
        message = Message(
            subject=f"ISCA website inquiry: {service_label}",
            recipients=[app.config["SUPPORT_EMAIL"]],
            body="\n".join(body_lines),
            reply_to=form.email.data.strip(),
        )
        if attachment_name:
            message.attach(
                filename=attachment_name,
                content_type=mimetypes.guess_type(attachment_name)[0]
                or "application/octet-stream",
                data=attachment_data,
            )

        try:
            mail.send(message)
        except (smtplib.SMTPException, OSError):
            app.logger.exception("Failed to deliver an ISCA website inquiry.")
            flash(texts["form_error"], "error")
            return render_page("contact.html", "contact", form, 503)

        app.logger.info(
            "Website inquiry delivered for service %s.",
            form.service.data,
        )
        flash(texts["form_success"], "success")
        return redirect(url_for("contact_page", lang=language))

    @app.errorhandler(413)
    def request_too_large(_error):
        language = session.get("language", "ar")
        if language not in SUPPORTED_LANGUAGES:
            language = "ar"
        flash(TRANSLATIONS[language]["form_size_error"], "error")
        return redirect(url_for("contact_page", lang=language))

    @app.errorhandler(404)
    def page_not_found(_error):
        language = get_language()
        return (
            render_template(
                "404.html",
                language=language,
                texts=TRANSLATIONS[language],
                page={
                    "title": "404",
                    "description": (
                        "الصفحة المطلوبة غير موجودة."
                        if language == "ar"
                        else "The requested page was not found."
                    ),
                },
                year=datetime.now().year,
            ),
            404,
        )

    return app


def get_service_images(service_slug, language):
    return [
        {
            "filename": filename,
            "alt": alt_ar if language == "ar" else alt_en,
        }
        for filename, alt_ar, alt_en in SERVICE_IMAGES[service_slug]
    ]


app = create_app()


if __name__ == "__main__":
    app.run()
