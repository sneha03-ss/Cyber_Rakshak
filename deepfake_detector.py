import requests
import json
import os
from typing import Dict, Any, Optional
import base64
from io import BytesIO
from PIL import Image

class DeepfakeDetector:
    """
    A class to detect deepfake/AI-generated images using the Sightengine API.
    """
    
    def __init__(self, api_user: str, api_secret: str):
        """
        Initialize the DeepfakeDetector with API credentials.
        
        Args:
            api_user (str): Sightengine API user ID
            api_secret (str): Sightengine API secret key
        """
        self.api_user = api_user
        self.api_secret = api_secret
        self.base_url = "https://api.sightengine.com/1.0/check.json"
    
    def detect_from_url(self, image_url: str) -> Dict[str, Any]:
        """
        Detect if an image is AI-generated using image URL.
        
        Args:
            image_url (str): URL of the image to analyze
            
        Returns:
            Dict containing detection results and status
        """
        try:
            params = {
                'url': image_url,
                'models': 'genai',
                'api_user': self.api_user,
                'api_secret': self.api_secret
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return self._process_response(result)
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Network error: {str(e)}",
                'ai_generated_score': None,
                'confidence': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'ai_generated_score': None,
                'confidence': None
            }
    
    def detect_from_file(self, image_path: str) -> Dict[str, Any]:
        """
        Detect if an image is AI-generated using local file path.
        
        Args:
            image_path (str): Path to the local image file
            
        Returns:
            Dict containing detection results and status
        """
        try:
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': "Image file not found",
                    'ai_generated_score': None,
                    'confidence': None
                }
            
            params = {
                'models': 'genai',
                'api_user': self.api_user,
                'api_secret': self.api_secret
            }
            
            with open(image_path, 'rb') as image_file:
                files = {'media': image_file}
                response = requests.post(self.base_url, files=files, data=params, timeout=30)
                response.raise_for_status()
            
            result = response.json()
            return self._process_response(result)
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Network error: {str(e)}",
                'ai_generated_score': None,
                'confidence': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'ai_generated_score': None,
                'confidence': None
            }
    
    def detect_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect if an image is AI-generated using image bytes.
        
        Args:
            image_bytes (bytes): Image data as bytes
            
        Returns:
            Dict containing detection results and status
        """
        try:
            params = {
                'models': 'genai',
                'api_user': self.api_user,
                'api_secret': self.api_secret
            }
            
            files = {'media': BytesIO(image_bytes)}
            response = requests.post(self.base_url, files=files, data=params, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return self._process_response(result)
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f"Network error: {str(e)}",
                'ai_generated_score': None,
                'confidence': None
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'ai_generated_score': None,
                'confidence': None
            }
    
    def _process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the API response and format it for the UI.
        
        Args:
            response (Dict): Raw API response
            
        Returns:
            Dict containing formatted detection results
        """
        try:
            if response.get('status') == 'success':
                ai_score = response.get('type', {}).get('ai_generated', 0.0)
                
                # Determine confidence level and result
                if ai_score >= 0.8:
                    confidence = "High"
                    result = "AI-Generated"
                    color = (1, 0.2, 0.2, 1)  # Red
                elif ai_score >= 0.5:
                    confidence = "Medium"
                    result = "Possibly AI-Generated"
                    color = (1, 0.6, 0.2, 1)  # Orange
                elif ai_score >= 0.2:
                    confidence = "Low"
                    result = "Likely Real"
                    color = (0.2, 0.8, 1, 1)  # Light Blue
                else:
                    confidence = "Very Low"
                    result = "Real"
                    color = (0.2, 1, 0.2, 1)  # Green
                
                return {
                    'success': True,
                    'ai_generated_score': ai_score,
                    'confidence': confidence,
                    'result': result,
                    'color': color,
                    'raw_response': response
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.get('error', 'Unknown error')}",
                    'ai_generated_score': None,
                    'confidence': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Error processing response: {str(e)}",
                'ai_generated_score': None,
                'confidence': None
            }
    
    def get_detection_summary(self, result: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of the detection result.
        
        Args:
            result (Dict): Detection result from detect methods
            
        Returns:
            str: Formatted summary string
        """
        if not result['success']:
            return f"❌ Error: {result['error']}"
        
        score = result['ai_generated_score']
        confidence = result['confidence']
        detection_result = result['result']
        
        return f"""
🔍 **Deepfake Detection Results**

**Detection:** {detection_result}
**Confidence:** {confidence}
**AI Score:** {score:.2f} (0.0 = Real, 1.0 = AI-Generated)

**Analysis:**
{self._get_analysis_text(score)}
        """.strip()
    
    def _get_analysis_text(self, score: float) -> str:
        """
        Get analysis text based on the AI score.
        
        Args:
            score (float): AI generation score (0-1)
            
        Returns:
            str: Analysis text
        """
        if score >= 0.8:
            return "This image shows strong indicators of being AI-generated. Exercise caution when using or sharing this content."
        elif score >= 0.5:
            return "This image may be AI-generated. Consider verifying the source before trusting or sharing."
        elif score >= 0.2:
            return "This image appears to be mostly authentic, but some AI elements may be present."
        else:
            return "This image appears to be authentic with minimal AI generation indicators."
