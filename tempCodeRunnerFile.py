from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.app import MDApp
from kivy.clock import Clock
from threading import Thread
from chatbot_logic import CyberRakshakBot
from deepfake_detector import DeepfakeDetector
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import BooleanProperty
from kivy.uix.filechooser import FileChooserIconView
from kivy.metrics import dp
import os
from config import SIGHTENGINE_API_USER, SIGHTENGINE_API_SECRET


class SplashScreen(Screen):
    pass

class MainScreen(Screen):
    pass

# A custom widget to be used for chat bubbles in the KV file.
# Although defined in KV, Kivy needs the Python class to exist.
class ChatMessage(MDBoxLayout):
    is_user = BooleanProperty(True)  # Default to True, will be set when creating the widget

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

class DetectorsScreen(Screen):
    pass

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

class ReportScreen(Screen):
    pass

class TrustCircleScreen(Screen):
    pass

class BlockedListScreen(Screen):
    pass

class ScamRadarScreen(Screen):
    pass

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


