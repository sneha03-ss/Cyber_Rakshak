# Configuration file for CyberRakshak
# Loads API credentials from .env file

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Sightengine API credentials for deepfake detection
# Get your API keys from: https://sightengine.com/
SIGHTENGINE_API_USER = os.getenv("SIGHTENGINE_API_USER", "your_api_user_here")
SIGHTENGINE_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET", "your_api_secret_here")

# Instructions:
# 1. Sign up at https://sightengine.com/
# 2. Get your API credentials from the dashboard
# 3. Update the .env file with your actual credentials
# 4. Keep the .env file secure and don't commit it to version control
