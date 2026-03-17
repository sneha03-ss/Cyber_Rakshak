from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivy.clock import Clock
from threading import Thread
from chatbot_logic import CyberRakshakBot
from deepfake_detector import DeepfakeDetector
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import BooleanProperty, StringProperty, ListProperty
from kivy.uix.filechooser import FileChooserIconView
from kivy.metrics import dp
import os
from config import SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET

# --- Imports required ONLY for the new DetectorsScreen ---
import re
import whois
from urllib.parse import urlparse
import socket
import ssl
from datetime import datetime
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
import webbrowser
from kivy.uix.image import Image as KivyImage
from kivy.uix.boxlayout import BoxLayout
# --- End of new imports ---


class SplashScreen(Screen):
    pass

class MainScreen(Screen):
    pass

# A custom widget to be used for chat bubbles in the KV file.
# Although defined in KV, Kivy needs the Python class to exist.
class ChatMessage(MDBoxLayout):
    is_user = BooleanProperty(True)  # Default to True, will be set when creating the widget

# --- Helper & Logic Classes required ONLY for the new DetectorsScreen ---
class Tab(MDBoxLayout, MDTabsBase):
    '''Class implementing content for a tab.'''
    pass

class AdvancedPhishingDetector:
    def __init__(self):
        # Enhanced keyword databases with scoring
        self.email_keywords = {
            'urgent': 4, 'action required': 4, 'account suspended': 5,
            'verify your account': 4, 'security alert': 4, 'confirm identity': 4,
            'winner': 5, 'lottery': 5, 'inheritance': 5, 'prize': 4,
            'click here': 3, 'act now': 3, 'limited time': 3,
            'tax refund': 4, 'irs': 5, 'social security': 4,
            'suspended': 4, 'locked': 4, 'expired': 3, 'pin':6,
            'bitcoin': 4, 'cryptocurrency': 3, 'crypto':3, 'investment opportunity': 4,
            'delivery failed': 4, 'package': 3, 'track': 3,'cvv':6, 'otp':6,
            'click link': 4, 'reply stop': 2, 'congratulations': 3,'cvv required': 6,'otp required': 6,
            'credit card required': 6,'bank details': 5,'account number': 5,
            'pin number': 6,'wire transfer': 5,'payment required': 5,'urgent payment': 5,'loan approval': 4,
        }

        self.sms_keywords = {
            'winner': 5, 'free': 3, 'claim now': 4, 'limited time': 3,
            'delivery failed': 4, 'package': 3, 'track': 3,
            'account locked': 5, 'suspended': 4, 'verify': 4,'cvv':6, 'otp':6,
            'click link': 4, 'reply stop': 2, 'congratulations': 3,'urgent': 4,
            'action required': 4, 'tax refund': 4, 'irs': 5, 'pin':6,
            'bitcoin': 4, 'cryptocurrency': 3, 'crypto':3, 'cvv required': 6,'otp required': 6,
            'credit card required': 6,'bank details': 5,'account number': 5,
            'pin number': 6,'wire transfer': 5,'payment required': 5,'urgent payment': 5,'loan approval': 4,
        }

        self.vishing_keywords = {
            'social security administration': 5, 'irs': 5, 'warrant': 5,
            'microsoft support': 4, 'apple support': 4, 'virus': 4,
            'suspend': 4, 'arrest': 5, 'fraud department': 4,'cvv':6, 'otp':6,
            'verify purchase': 3, 'amazon prime': 3, 'refund': 3,  'cvv required': 6,'otp required': 6,
            'credit card required': 6,'bank details': 5,'account number': 5,'pin':6,
            'pin number': 6,'wire transfer': 5,'payment required': 5,'urgent payment': 5,'loan approval': 4,
        }

        self.suspicious_phone_patterns = {
            '+1876': {'country': 'Jamaica', 'description': 'Lottery/Sweepstakes scams', 'lengths': [10]},
            '+1809': {'country': 'Dominican Republic', 'description': 'Premium rate scams', 'lengths': [10]},
            '+92':   {'country': 'Pakistan', 'description': 'Common tech support/impersonation scams', 'lengths': [10,11]},
            '+234':  {'country': 'Nigeria', 'description': 'Advance fee / 419 scams', 'lengths': [10,11]},
        }

        self.suspicious_tlds = ['.tk', '.ml', '.ga', '.cf', '.xyz', '.top', '.club', '.biz', '.info']
        self.url_shorteners = ['bit.ly', 'tinyurl.com', 'goo.gl', 'is.gd', 't.co']

    def analyze_domain_age(self, domain: str) -> dict:
        try:
            w = whois.whois(domain)
            if w.creation_date:
                creation_date = w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date
                age_days = (datetime.now() - creation_date).days
                return {'age_days': age_days, 'is_new': age_days < 90}
        except Exception:
            return {'age_days': -1, 'is_new': False}
        return {'age_days': -1, 'is_new': False}

    def check_ssl_certificate(self, domain: str) -> dict:
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    ssock.getpeercert()
            return {'valid': True}
        except Exception:
            return {'valid': False, 'error': 'Certificate validation failed or host unreachable'}

    def advanced_url_analysis(self, url: str) -> dict:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            risk_score, flags = 0, []

            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):
                risk_score += 5; flags.append(f"Direct IP address used instead of a domain name")
            domain_info = self.analyze_domain_age(domain)
            if domain_info.get('is_new'):
                risk_score += 4; flags.append(f"Domain is very new (created {domain_info.get('age_days')} days ago)")
            if not self.check_ssl_certificate(domain).get('valid'):
                risk_score += 5; flags.append("SSL Certificate is invalid or missing")
            if any(domain.endswith(tld) for tld in self.suspicious_tlds):
                risk_score += 3; flags.append(f"Uses a suspicious top-level domain")
            if any(shortener in domain for shortener in self.url_shorteners):
                risk_score += 3; flags.append(f"Hides destination using a URL shortener")

            return {'url': url, 'risk_score': risk_score, 'flags': flags}
        except Exception as e:
            return {'url': url, 'error': str(e), 'risk_score': 2, 'flags': ['Error analyzing URL']}

    def check_phone_reputation(self, phone: str) -> dict:
        clean_phone = re.sub(r'[^\d+]', '', phone)
        risk_score, flags = 0, []
        for prefix, data in self.suspicious_phone_patterns.items():
            if clean_phone.startswith(prefix):
                risk_score += 4
                flags.append(f"Originates from a high-risk region: {data['description']}")
                break
        return {'phone': clean_phone, 'risk_score': risk_score, 'flags': flags}

    def calculate_text_risk_score(self, text: str, keywords: dict) -> tuple[int, list]:
        text_lower, total_score, found_keywords = text.lower(), 0, []
        for keyword, score in keywords.items():
            if keyword in text_lower:
                total_score += score
                found_keywords.append(f"'{keyword}' (risk: +{score})")
        return total_score, found_keywords

    def get_recommendations(self, threat_level: str) -> list:
        if threat_level in ["HIGH", "VERY HIGH"]:
            return ["Recommendation: DO NOT CLICK any links.", "Recommendation: Block the sender/caller immediately.", "Recommendation: Delete this message."]
        if threat_level == "MEDIUM":
            return ["Recommendation: Be extremely cautious.", "Recommendation: Verify the sender through a separate, trusted channel."]
        return ["No specific threats detected, but always remain vigilant."]

    def detect_email_phishing(self, subject: str, body: str) -> dict:
        full_text = f"{subject} {body}"
        urls = re.findall(r'https?://[^\s<>"]+', full_text)
        text_score, keywords_found = self.calculate_text_risk_score(full_text, self.email_keywords)
        url_analyses, url_risk_score = [], 0
        for url in set(urls):
            analysis = self.advanced_url_analysis(url)
            url_analyses.append(analysis)
            url_risk_score += analysis.get('risk_score', 0)
        total_risk_score = text_score + url_risk_score
        threat_level = "HIGH" if total_risk_score >= 10 else "MEDIUM" if total_risk_score >= 5 else "LOW" if total_risk_score > 0 else "MINIMAL"
        return {'threat_level': threat_level, 'risk_score': total_risk_score, 'keywords_found': keywords_found, 'url_analyses': url_analyses, 'recommendations': self.get_recommendations(threat_level)}

    def detect_sms_phishing(self, message: str) -> dict:
        urls = re.findall(r'https?://[^\s<>"]+', message)
        text_score, keywords_found = self.calculate_text_risk_score(message, self.sms_keywords)
        url_analyses, url_risk_score = [], 0
        for url in set(urls):
            analysis = self.advanced_url_analysis(url)
            url_analyses.append(analysis)
            url_risk_score += analysis.get('risk_score', 0)
        total_risk_score = text_score + url_risk_score
        threat_level = "HIGH" if total_risk_score >= 9 else "MEDIUM" if total_risk_score >= 4 else "LOW" if total_risk_score > 0 else "MINIMAL"
        return {'threat_level': threat_level, 'risk_score': total_risk_score, 'keywords_found': keywords_found, 'url_analyses': url_analyses, 'recommendations': self.get_recommendations(threat_level)}

    def detect_vishing_attack(self, transcript: str, caller_id: str) -> dict:
        text_score, keywords_found = self.calculate_text_risk_score(transcript, self.vishing_keywords)
        phone_analysis = self.check_phone_reputation(caller_id)
        phone_risk_score = phone_analysis.get('risk_score', 0)
        total_risk_score = text_score + phone_risk_score
        threat_level = "HIGH" if total_risk_score >= 8 else "MEDIUM" if total_risk_score >= 4 else "LOW" if total_risk_score > 0 else "MINIMAL"
        return {'threat_level': threat_level, 'risk_score': total_risk_score, 'keywords_found': keywords_found, 'caller_analysis': phone_analysis, 'recommendations': self.get_recommendations(threat_level)}

# --- End of new classes ---


class AIChatbotScreen(Screen):
    def send_message(self):
        """Handles sending a message from the user input field."""
        user_input_field = self.ids.user_input
        user_message = user_input_field.text.strip()

        if user_message:
            # Add the user's message to the UI
            self.add_chat_message(user_message, is_user=True)
            user_input_field.text = "" # Clear the input

            # Display a thinking indicator for the bot
            self.add_chat_message("Cyber Rakshak is thinking...", is_user=False, is_thinking=True)

            # Run the API call in a separate thread to avoid freezing the UI
            Thread(target=self.get_bot_response, args=(user_message,)).start()

    def get_bot_response(self, user_message):
        """
        Fetches the bot's response in a background thread.
        """
        bot = MDApp.get_running_app().bot
        response = bot.get_response(user_message)
        # Schedule the UI update back on the main thread
        Clock.schedule_once(lambda dt: self.update_bot_message(response))

    def add_chat_message(self, message, is_user, is_thinking=False):
        """Adds a new chat bubble to the chat history."""
        chat_history = self.ids.chat_history

        chat_bubble = ChatMessage(is_user=is_user)
        chat_bubble.children[0].text = message # The first child is the MDLabel

        # Align the bubble left for bot, right for user
        if is_user:
            chat_bubble.pos_hint = {"right": 1}
            chat_bubble.size_hint_x = 0.75
        else:
            chat_bubble.pos_hint = {"left": 1}
            chat_bubble.size_hint_x = 0.75
            if is_thinking:
                # Store the thinking bubble to update it later
                self.thinking_bubble = chat_bubble

        chat_history.add_widget(chat_bubble)
        # Auto-scroll to the bottom
        self.ids.scroll_view.scroll_y = 0

    def update_bot_message(self, response_text):
        """Updates the 'thinking...' message with the actual response."""
        if hasattr(self, 'thinking_bubble'):
            self.thinking_bubble.children[0].text = response_text
            # Clean up the reference
            del self.thinking_bubble


# --- REPLACED: The original DetectorsScreen placeholder is now the functional version ---
class DetectorsScreen(Screen):
    result_email = StringProperty("Awaiting analysis...")
    result_sms = StringProperty("Awaiting analysis...")
    result_vishing = StringProperty("Awaiting analysis...")
    result_email_color = ListProperty([1, 1, 1, 1])
    result_sms_color = ListProperty([1, 1, 1, 1])
    result_vishing_color = ListProperty([1, 1, 1, 1])
    green_color, yellow_color, orange_color, red_color = [0.2, 0.8, 0.2, 1], [1, 1, 0, 1], [1, 0.6, 0, 1], [1, 0.2, 0.2, 1]
    phone_dialog = None # To hold the phone format warning dialog

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.detector = AdvancedPhishingDetector()

    def format_results(self, result: dict) -> str:
        threat = result.get('threat_level', 'UNKNOWN')
        score = result.get('risk_score', 0)
        output = [f"Threat Level: {threat} (Risk Score: {score})"]
        if result.get('keywords_found'):
            output.append("\nSuspicious Keywords:")
            output.extend([f"- {kw}" for kw in result['keywords_found']])
        if result.get('url_analyses'):
            output.append("\nURL Analysis:")
            for analysis in result['url_analyses']:
                if analysis.get('flags'):
                    output.append(f"  URL: {analysis['url']}")
                    output.extend([f"    - {flag}" for flag in analysis['flags']])
        if result.get('caller_analysis'):
            caller_info = result['caller_analysis']
            if caller_info.get('flags'):
                output.append("\nCaller ID Analysis:")
                output.extend([f"- {flag}" for flag in caller_info['flags']])
        if result.get('recommendations'):
            output.append("\n" + "="*20)
            output.extend(result['recommendations'])
        return "\n".join(output)

    def get_color_for_threat(self, threat_level: str):
        if threat_level == "HIGH": return self.red_color
        if threat_level == "MEDIUM": return self.orange_color
        if threat_level == "LOW": return self.yellow_color
        return self.green_color

    def detect_mail(self, subject, body):
        if not subject.strip() and not body.strip():
            return
        result_dict = self.detector.detect_email_phishing(subject, body)
        self.result_email = self.format_results(result_dict)
        self.result_email_color = self.get_color_for_threat(result_dict['threat_level'])

    def detect_sms(self, sms):
        if not sms.strip():
            return
        result_dict = self.detector.detect_sms_phishing(sms)
        self.result_sms = self.format_results(result_dict)
        self.result_sms_color = self.get_color_for_threat(result_dict['threat_level'])

    def detect_vishing(self, transcript, phone):
        if not transcript.strip() and not phone.strip():
            return
        if not phone.strip().startswith('+'):
            if not self.phone_dialog:
                self.phone_dialog = MDDialog(
                    title="Invalid Phone Number Format",
                    text="Please include the country code starting with a '+' sign (e.g., +91 for India, +1 for USA).",
                    buttons=[MDFlatButton(text="OK", on_release=lambda x: self.phone_dialog.dismiss())]
                )
            self.phone_dialog.open()
            return
        result_dict = self.detector.detect_vishing_attack(transcript, phone)
        self.result_vishing = self.format_results(result_dict)
        self.result_vishing_color = self.get_color_for_threat(result_dict['threat_level'])
# --- END of replaced DetectorsScreen ---


class DeepfakeDetectionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.detector = None
        self.selected_image_path = None

    def initialize_detector(self):
        """Initialize the deepfake detector with API credentials."""
        if SIGHTENGINE_API_USER == "your_api_user_here" or SIGHTENGINE_API_SECRET == "your_api_secret_here":
            self.show_message("❌ Please set your API credentials in the .env file first!")
            return False

        self.detector = DeepfakeDetector(SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET)
        return True

    def select_image(self):
        """Open file chooser to select an image."""
        if not self.detector:
            if not self.initialize_detector():
                return

        # Simple file selection using Kivy's file chooser
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button

        content = BoxLayout(orientation='vertical')
        file_chooser = FileChooserIconView(
            path=os.path.expanduser("~"),
            filters=["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif"]
        )

        btn_layout = BoxLayout(size_hint_y=None, height='48dp', spacing=dp(10), padding=[dp(10), 0])
        btn_cancel = Button(
            text='Cancel',
            background_color=(0.8, 0.2, 0.2, 1),
            color=(1, 1, 1, 1),
            font_size=dp(14)
        )
        btn_select = Button(
            text='Select Image',
            background_color=(0.54, 0.17, 0.89, 1),
            color=(1, 1, 1, 1),
            font_size=dp(14)
        )

        btn_layout.add_widget(btn_cancel)
        btn_layout.add_widget(btn_select)

        content.add_widget(file_chooser)
        content.add_widget(btn_layout)

        popup = Popup(
            title='📁 Select Image File',
            content=content,
            size_hint=(0.8, 0.8),
            title_size=dp(18),
            title_color=(1, 1, 1, 1),
            background_color=(0.1, 0.1, 0.1, 1),
            separator_color=(0.54, 0.17, 0.89, 1)
        )

        def select_file(instance):
            if file_chooser.selection:
                self.selected_image_path = file_chooser.selection[0]
                popup.dismiss()

                # Update UI to show selected image with better messaging
                self.ids.selected_image.source = self.selected_image_path
                self.ids.selected_image.opacity = 1
                self.ids.detect_button.disabled = False
                self.ids.result_text.text = "✅ Image selected successfully!\n\nClick 'Analyze Image for Deepfakes' to start the analysis."
                self.ids.result_text.theme_text_color = "Custom"
                self.ids.result_text.text_color = (0.2, 0.8, 0.2, 1)  # Green for success
            else:
                self.show_message("❌ Please select an image file.")

        def cancel_selection(instance):
            popup.dismiss()

        btn_select.bind(on_press=select_file)
        btn_cancel.bind(on_press=cancel_selection)

        popup.open()

    def detect_deepfake(self):
        """Detect if the selected image is a deepfake."""
        if not self.selected_image_path:
            self.show_message("Please select an image first.")
            return

        if not self.detector:
            if not self.initialize_detector():
                return

        # Show loading state
        self.ids.detect_button.disabled = True
        self.ids.result_text.text = "🔍 Analyzing image with AI...\n\nPlease wait while our advanced algorithms examine the image for deepfake indicators."
        self.ids.result_text.theme_text_color = "Custom"
        self.ids.result_text.text_color = (0.4, 0.8, 1, 1)  # Blue for processing

        # Run detection in background thread
        Thread(target=self._run_detection, daemon=True).start()

    def _run_detection(self):
        """Run deepfake detection in background thread."""
        try:
            result = self.detector.detect_from_file(self.selected_image_path)
            summary = self.detector.get_detection_summary(result)

            # Schedule UI update on main thread
            Clock.schedule_once(lambda dt: self._update_detection_result(result, summary))

        except Exception as e:
            error_msg = f"Detection failed: {str(e)}"
            Clock.schedule_once(lambda dt: self._update_detection_error(error_msg))

    def _update_detection_result(self, result, summary):
        """Update UI with detection results."""
        self.ids.detect_button.disabled = False

        if result['success']:
            # Update result text with color coding
            self.ids.result_text.text = summary
            self.ids.result_text.theme_text_color = "Custom"
            self.ids.result_text.text_color = result.get('color', (1, 1, 1, 1))
        else:
            self.ids.result_text.text = f"Error: {result['error']}"
            self.ids.result_text.theme_text_color = "Custom"
            self.ids.result_text.text_color = (1, 0.2, 0.2, 1)  # Red for error

    def _update_detection_error(self, error_msg):
        """Update UI with detection error."""
        self.ids.detect_button.disabled = False
        self.ids.result_text.text = error_msg
        self.ids.result_text.theme_text_color = "Custom"
        self.ids.result_text.text_color = (1, 0.2, 0.2, 1)  # Red for error

    def clear_selection(self):
        """Clear the selected image and reset the UI."""
        self.selected_image_path = None
        self.ids.selected_image.source = ""
        self.ids.selected_image.opacity = 0
        self.ids.detect_button.disabled = True
        self.ids.result_text.text = "Select an image to analyze for deepfakes."
        self.ids.result_text.theme_text_color = "Custom"
        self.ids.result_text.text_color = (0.8, 0.8, 0.8, 1)

    def show_message(self, message):
        """Show a message to the user."""
        self.ids.result_text.text = message

# --- UNCHANGED: These screens remain as placeholders as per the original main.py ---
class ReportScreen(Screen):
    dialog, confirmation_dialog, saved_date = None, None, None
    
    def show_date_picker(self):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_date_save)
        date_dialog.open()
    
    def on_date_save(self, instance, value, date_range):
        self.saved_date = value
        time_dialog = MDTimePicker()
        time_dialog.bind(on_save=self.on_time_save)
        time_dialog.open()
    
    def on_time_save(self, instance, value):
        self.datetime_button.text = f"{self.saved_date} {value}"
    
    def show_report_form(self):
        if not self.dialog:
            content_box = MDBoxLayout(orientation="vertical", spacing="12dp", size_hint_y=None, height="300dp")
            self.suspect_contact = MDTextField(hint_text="Suspect Phone or Email")
            self.datetime_button = MDRectangleFlatButton(text="Select Date and Time of Incident", on_release=lambda x: self.show_date_picker())
            self.suspect_message = MDTextField(hint_text="Suspicious Message or Details", multiline=True)
            content_box.add_widget(self.suspect_contact)
            content_box.add_widget(self.datetime_button)
            content_box.add_widget(self.suspect_message)
            self.dialog = MDDialog(
                title="Report a Suspect",
                type="custom",
                content_cls=content_box,
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=MDApp.get_running_app().theme_cls.primary_color,
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="SUBMIT",
                        on_release=self.submit_report
                    )
                ]
            )
        self.suspect_contact.text = ""
        self.datetime_button.text = "Select Date and Time of Incident"
        self.suspect_message.text = ""
        self.dialog.open()
    
    def submit_report(self, *args):
        incident_time = self.datetime_button.text if self.datetime_button.text != "Select Date and Time of Incident" else "Not specified"
        print(f"Report Submitted:\n  Suspect Contact: {self.suspect_contact.text}\n  Date/Time: {incident_time}\n  Message: {self.suspect_message.text}")
        self.dialog.dismiss()
        self.show_confirmation_dialog()
    
    def show_confirmation_dialog(self):
        if not self.confirmation_dialog:
            self.confirmation_dialog = MDDialog(
                title="Report Submitted",
                text="Would you like to report another incident?",
                buttons=[
                    MDFlatButton(
                        text="NO",
                        theme_text_color="Custom",
                        text_color=MDApp.get_running_app().theme_cls.primary_color,
                        on_release=lambda x: self.confirmation_dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="YES",
                        on_release=self.report_another
                    )
                ]
            )
        self.confirmation_dialog.open()
    
    def report_another(self, *args):
        self.confirmation_dialog.dismiss()
        self.show_report_form()
    
    def open_critical_report(self):
        try:
            import webbrowser
            webbrowser.open("https://cybercrime.gov.in/Webform/Index.aspx")
        except Exception as e:
            print(f"ERROR: Could not open webbrowser. Reason: {e}")

class TrustCircleScreen(Screen):
    pass

class BlockedListScreen(Screen):
    pass

class ScamRadarScreen(Screen):
    from kivy.uix.image import Image
    from kivy.uix.boxlayout import BoxLayout

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        # Display the india.jpg image centered and scaled
        img = KivyImage(source="india.jpg", allow_stretch=True, keep_ratio=True)
        layout.add_widget(img)
        self.add_widget(layout)
    pass
# --- End of unchanged screens ---

class AboutUsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.about_content = {
            'title': 'About Cyber Rakshak',
            'subtitle': 'Your AI-Powered Digital Shield',
            'description': 'Cyber Rakshak is an AI-powered digital shield, designed to protect you and your loved ones from online scams and fraud. Today, as everything goes digital, facing digital fraud has become an everyday risk. Cyber Rakshak is built to be your one-stop solution; listening, blocking, alerting, and guiding you in real time, before any harm happens.',
            'how_it_works': 'The system works in the background, checking for scams, fake content and fraud messages. If a threat is detected, you get an instant alert and recommended actions. When technology can\'t catch everything, Cyber Rakshak brings in family support, making cybersecurity a team effort.',
            'key_features': [
                'Detects scams and deepfakes as they happen',
                'One-tap reporting for any suspicious activity',
                'Maintains a personal blocked list to keep threats away',
                'Provides an AI-powered helpline chatbot for quick advice',
                'Lets trusted family members help build a safer digital space'
            ],
            'mission': 'Empower everyone with peace of mind online, prevent financial losses before they happen, and build digital trust for all. Cyber Rakshak is more than an app; it\'s your digital airbag against scams, blending advanced AI with real community support.',
            'journey': 'Inspired by real cases like a couple losing ₹50 lakh to digital extortion, we\'ve researched Maharashtra Government laws, National Crime Records Bureau data, and leveraged ML datasets from Kaggle to make this a reality.',
            'call_to_action': 'Join us in making the digital space safer together, we can outsmart the scammers!'
        }

    def get_about_content(self):
        """Return the about content dictionary."""
        return self.about_content

class CodeRakshakApp(MDApp):
    def build(self):
        # Initialize the chatbot instance once when the app starts
        self.bot = CyberRakshakBot()
        self.screen_manager = Builder.load_file("cyber_rakshak.kv")
        # Schedule transition from splash to main screen after 3 seconds
        Clock.schedule_once(self.switch_to_main, 3)
        return self.screen_manager

    def switch_to_main(self, dt):
        self.screen_manager.current = "main"

    def open_nav(self):
        self.screen_manager.get_screen("main").ids.nav_drawer.set_state("toggle")

    def on_icon_press(self, icon_id):
        screen_map = {
            "aichatbot": "aichatbot",
            "detectors": "detectors",
            "deepfake": "deepfake",
            "report": "report",
            "trustcircle": "trustcircle",
            "blockedlist": "blockedlist",
            "scamradar": "scamradar",
            "aboutus": "aboutus"
        }
        target = screen_map.get(icon_id, "main")
        if target in self.screen_manager.screen_names:
            self.screen_manager.current = target

    def go_back(self):
        self.screen_manager.current = "main"


if __name__ == "__main__":
    CodeRakshakApp().run()
    
