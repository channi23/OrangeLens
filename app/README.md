# TruthLens PWA Documentation

## Overview
TruthLens PWA is a Progressive Web App that provides one-tap fact verification from any mobile app via the system Share sheet.

## Features
- ✅ **One-tap verification** from any app via Share sheet
- ✅ **Text and image verification** using AI
- ✅ **Fast/Deep verification modes**
- ✅ **Multi-language support** (English, Hindi, Tamil)
- ✅ **Offline support** with service worker
- ✅ **Real-time metrics** (latency, cost)
- ✅ **Transparent AI explanations**
- ✅ **Verified citations** from fact-check databases

## Installation

### From Web
1. Visit the TruthLens PWA URL
2. Click "Add to Home Screen" when prompted
3. The app will be installed on your device

### From App Store (Coming Soon)
- iOS App Store
- Google Play Store

## Usage

### Share Sheet Integration
1. Open any app with text you want to verify
2. Select the text and tap "Share"
3. Choose "TruthLens" from the share options
4. The app will open with the text pre-filled
5. Tap "Verify Claim" to get instant results

### Manual Verification
1. Open the TruthLens app
2. Paste or type the claim you want to verify
3. Optionally upload an image
4. Choose verification mode (Fast/Deep)
5. Select language (Auto-detect available)
6. Tap "Verify Claim"

## Verification Modes

### Fast Mode
- **Speed**: 1-2 seconds
- **Cost**: Lower
- **Method**: AI-only verification
- **Use Case**: Quick fact checks

### Deep Mode
- **Speed**: 3-5 seconds
- **Cost**: Higher
- **Method**: AI + Fact Check Database
- **Use Case**: Comprehensive verification with citations

## Language Support
- **English**: Full support
- **Hindi**: Full support with Hindi explanations
- **Tamil**: Full support with Tamil explanations
- **Auto-detect**: Automatically detects language

## Verdict Types
- **✅ True**: Claim is factually accurate
- **❌ False**: Claim is factually incorrect
- **⚠️ Misleading**: Claim is partially true but misleading
- **❓ Unverified**: Cannot determine accuracy

## Offline Support
The PWA includes offline support:
- **Cached resources**: App works without internet
- **Background sync**: Verification requests sync when online
- **Offline indicator**: Shows when offline

## Performance Metrics
The app displays real-time metrics:
- **Latency**: Response time in milliseconds
- **Cost**: Estimated cost per verification
- **Confidence**: AI confidence score (0-100%)

## Privacy & Security
- **No PII storage**: User data is anonymized
- **Secure API**: All requests encrypted
- **Data retention**: Images deleted after 14 days
- **Logs retention**: Logs deleted after 30 days

## Browser Support
- **Chrome**: Full support
- **Safari**: Full support
- **Firefox**: Full support
- **Edge**: Full support
- **Mobile browsers**: Full support

## Development

### Prerequisites
- Node.js 16+
- npm or yarn

### Setup
```bash
cd app
npm install
npm start
```

### Build
```bash
npm run build
```

### Environment Variables
```bash
REACT_APP_API_URL=https://api.truthlens.app
REACT_APP_API_KEY=your-api-key
```

## Troubleshooting

### Share Sheet Not Working
1. Ensure the app is installed as PWA
2. Check browser permissions
3. Try refreshing the app

### Verification Failing
1. Check internet connection
2. Verify API key is valid
3. Try with shorter text

### Offline Mode Issues
1. Clear browser cache
2. Reinstall the PWA
3. Check service worker status

## Support
- **Email**: support@truthlens.app
- **Documentation**: https://docs.truthlens.app
- **GitHub**: https://github.com/truthlens/pwa

## Changelog

### v1.0.0
- Initial release
- Share sheet integration
- AI verification
- Multi-language support
- Offline support
