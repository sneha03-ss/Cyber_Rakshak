# Deepfake Detector - CyberRakshak

This module provides deepfake detection capabilities for the CyberRakshak application using the Sightengine API.

## Features

- **Image Upload**: Upload images from your device for analysis
- **AI Detection**: Uses advanced AI to detect if images are AI-generated
- **Confidence Levels**: Provides confidence scores and detailed analysis
- **User-Friendly Interface**: Clean, intuitive UI with real-time feedback
- **Multiple Formats**: Supports JPG, PNG, BMP, and GIF formats

## Setup Instructions

### 1. Get API Credentials

1. Visit [Sightengine.com](https://sightengine.com/)
2. Create a free account
3. Navigate to your dashboard to get your API credentials
4. Copy your `API User` and `API Secret` values

### 2. Configure the Application

1. Open the `.env` file
2. Replace the placeholder values with your actual API credentials:

```env
SIGHTENGINE_API_USER=your_actual_api_user
SIGHTENGINE_API_SECRET=your_actual_api_secret
```

### 3. Install Dependencies

Make sure you have all required packages installed:

```bash
pip install -r requirements.txt
```

## How to Use

1. **Launch the Application**: Run `main.py`
2. **Navigate to Deepfake Detection**: Click on "Deepfake Detection" from the main menu
3. **Select an Image**: Click "Select Image" to choose a file from your device
4. **Analyze**: Click "Detect Deepfake" to start the analysis
5. **View Results**: The results will show:
   - Detection result (Real/AI-Generated)
   - Confidence level (High/Medium/Low)
   - AI Score (0.0 = Real, 1.0 = AI-Generated)
   - Detailed analysis

## Understanding the Results

### AI Score Interpretation
- **0.0 - 0.2**: Very Low confidence - Likely Real
- **0.2 - 0.5**: Low confidence - Mostly Real
- **0.5 - 0.8**: Medium confidence - Possibly AI-Generated
- **0.8 - 1.0**: High confidence - AI-Generated

### Color Coding
- 🟢 **Green**: Real/authentic image
- 🔵 **Blue**: Likely real with minimal AI elements
- 🟠 **Orange**: Possibly AI-generated
- 🔴 **Red**: High confidence AI-generated

## API Limits

- Free tier: Limited requests per month
- Paid plans: Higher limits and additional features
- Check your Sightengine dashboard for usage details

## Troubleshooting

### Common Issues

1. **"API Credentials Required" Error**
   - Make sure you've updated `.env` file with your actual credentials
   - Verify your credentials are correct

2. **"Network Error"**
   - Check your internet connection
   - Verify the Sightengine API is accessible

3. **"Image file not found"**
   - Make sure the image file exists and is accessible
   - Try selecting a different image

4. **"Detection failed"**
   - Check if the image format is supported
   - Try with a different image
   - Verify your API quota hasn't been exceeded

### Supported Image Formats
- JPG/JPEG
- PNG
- BMP
- GIF

## Security Notes

- Keep your API credentials secure
- Don't commit `.env` file to version control
- The `.env` file is automatically ignored by git

## Technical Details

The deepfake detector uses:
- **Sightengine API**: For AI-generated content detection
- **Requests**: For HTTP API calls
- **Pillow**: For image processing
- **Threading**: For non-blocking UI operations

## Support

For issues related to:
- **API**: Contact Sightengine support
- **Application**: Check the main CyberRakshak documentation
- **Code**: Review the implementation in `deepfake_detector.py`
