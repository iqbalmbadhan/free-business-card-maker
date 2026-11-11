# Building the iOS & Android App from Windows (via GitHub Actions)

Because Apple requires macOS + Xcode to compile iOS apps, this project includes a ready-to-run **GitHub Actions cloud pipeline** (`.github/workflows/mobile-apps.yml`) that builds both your **iOS (`.ipa`)** and **Android (`.apk` / `.aab`)** apps automatically in the cloud while you work on your Windows PC.

---

## What Was Added for the Mobile App

1. **100% Offline Mobile Bundle (`build/build_mobile.py` -> `dist/mobile/`)**
   - Bundles all 11 languages (`en`, `bn`, `fr`, `de`, `es`, `hi`, `ja`, `zh`, `zh-Hant`, `ar`, `ru`), 148 card designs, QR generator, PDF writer, and **all 27 Latin + Bengali `.woff2` font families** directly into the app package so it works 100% offline on a plane or without cell service.
2. **Present Card / QR Mode (`#presentModal`)**
   - Tap **Present** (in the top Front/Back toggle, desktop export bar, or mobile Download tab) to open a clean, full-screen view of your card's front, back, and scannable vCard QR code for in-person networking, with one-tap **Share PDF** and **Save contact (.vcf)** actions.
3. **My Cards Deck (`#deckWrap` in the Saved section)**
   - Save, update, switch between, and delete up to 25 different cards on your phone (e.g., Personal, Company, Bangla version, English version).
4. **Native iOS / Android Share Sheet & Haptics**
   - When running inside the native Capacitor shell, tapping **Download PDF**, **Front PNG**, **Back PNG**, or **Save contact (.vcf)** writes the file to native cache and opens the native iOS Share Sheet (AirDrop, Save to Files, WhatsApp, Print) or Android Share Sheet.
   - Native haptic feedback (`@capacitor/haptics` with `navigator.vibrate` fallback) when flipping the card or switching tabs.

---

## Step 1: Build Your iOS `.ipa` & Android `.apk` on GitHub Actions (No Paid Accounts Needed)

1. Push this repository to your GitHub account.
2. Open your repository on GitHub and click the **Actions** tab.
3. Select **Build iOS & Android Mobile Apps** in the left sidebar.
4. Click **Run workflow** -> **Run workflow**.
5. In ~4–6 minutes, two downloadable artifact zips will appear at the bottom of the workflow summary:
   - **`Android-App-Packages`**: Contains `BusinessCardMaker-debug.apk`.
   - **`iOS-App-Packages`**: Contains `BusinessCardMaker-unsigned.ipa` and `BusinessCardMaker-Simulator.app.zip`.

---

## Step 2: Install on Your Phone From Your Windows PC

### Installing on an iPhone / iPad from Windows (Free Sideloading)
Because `BusinessCardMaker-unsigned.ipa` is built without requiring a $99/year Apple Developer account, you can install it onto your iPhone straight from your Windows PC using **Sideloadly** (free):
1. Download and install [iTunes for Windows (non-Microsoft Store version)](https://www.apple.com/itunes/) and [iCloud for Windows](https://support.apple.com/en-us/103232).
2. Download and open [Sideloadly](https://sideloadly.io/) on your Windows PC.
3. Plug your iPhone into your PC with a USB cable and tap **Trust This Computer** on your iPhone.
4. Drag `BusinessCardMaker-unsigned.ipa` into Sideloadly, enter your personal Apple ID email, and click **Start**.
5. On your iPhone, go to **Settings -> General -> VPN & Device Management**, tap your Apple ID, and tap **Trust** (and enable Developer Mode in **Settings -> Privacy & Security -> Developer Mode** on iOS 16+).

### Installing on an Android Phone
1. Copy `BusinessCardMaker-debug.apk` to your Android phone (via USB, Google Drive, or WhatsApp) and tap it to install.

---

## Step 3: Optional — Automatic App Store & Google Play Signing

When you are ready to publish to the **Apple App Store / TestFlight** or **Google Play Store**, add the following repository secrets in GitHub (**Settings -> Secrets and variables -> Actions**). The workflow automatically detects them and produces `BusinessCardMaker-signed.ipa` and `BusinessCardMaker-release.aab` / `BusinessCardMaker-release.apk`:

### iOS Signing Secrets
| Secret Name | Description |
| :--- | :--- |
| `IOS_P12_BASE64` | Base64-encoded Apple Distribution `.p12` certificate |
| `IOS_P12_PASSWORD` | Password for the `.p12` certificate |
| `IOS_MOBILEPROVISION_BASE64` | Base64-encoded App Store `.mobileprovision` profile for `com.aiinfos.businesscardmaker` |
| `IOS_TEAM_ID` | Your 10-character Apple Developer Team ID |

### Android Signing Secrets
| Secret Name | Description |
| :--- | :--- |
| `ANDROID_KEYSTORE_BASE64` | Base64-encoded `.jks` or `.keystore` file |
| `ANDROID_KEYSTORE_PASSWORD` | Keystore password |
| `ANDROID_KEY_ALIAS` | Key alias name |
| `ANDROID_KEY_PASSWORD` | Key password |
