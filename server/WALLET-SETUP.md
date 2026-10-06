# Apple Wallet and Google Wallet setup

The **Add to Apple Wallet** and **Add to Google Wallet** buttons need a small server-side script, because Apple and Google only accept passes signed with your own private keys. Those keys must never be put in the browser. The script is `api/wallet.php`: plain PHP with no Composer packages.

This setup is optional. Without it, both buttons still work for free: they show the card's contact QR code with steps for Apple Wallet's **Create a Pass** (iOS 27 and later) and Google Wallet's **Everything else** (Android). The setup below upgrades them to finished passes in one tap.

## What you need

| | Apple Wallet | Google Wallet |
|---|---|---|
| Account | [Apple Developer Program](https://developer.apple.com/programs/) (paid membership) | [Google Pay & Wallet Console](https://pay.google.com/business/console) (free) and a [Google Cloud](https://console.cloud.google.com) project |
| Credentials | Pass Type ID certificate + Apple WWDR G4 certificate | Issuer ID + service account JSON key |
| Works on | iPhone, iPad, Apple Watch, Mac Safari | Android phones with Google Wallet |

Server: HTTPS, PHP 8 or newer with the `openssl`, `zip`, `curl` and `gd` extensions. CloudPanel's PHP includes all four.

## 1. Upload and create the config

1. Upload the app folder (it contains `api/`).
2. Create a folder for keys **outside** the web root, for example:
   ```bash
   mkdir -p /home/SITE-USER/wallet-certs && chmod 700 /home/SITE-USER/wallet-certs
   ```
3. Copy the sample config and edit it:
   ```bash
   cd /home/SITE-USER/htdocs/YOUR-DOMAIN/business-card-maker/api
   cp config.sample.php config.php
   ```
   Set `allowed_origins` to the exact sites that use the tool, for example `https://iqbalmahmud.com`.

## 2. Apple Wallet

1. In [Certificates, Identifiers & Profiles](https://developer.apple.com/account/resources/identifiers/list), add an identifier of type **Pass Type IDs**, for example `pass.org.womenailabs.businesscard`.
2. On the server, create a private key and a certificate request:
   ```bash
   cd /home/SITE-USER/wallet-certs
   openssl genrsa -out pass-key.pem 2048
   openssl req -new -key pass-key.pem -out pass.csr -subj "/emailAddress=iqbal@womenailabs.org/CN=Business Card Pass/C=BD"
   ```
3. In the developer portal, open **Certificates → +**, choose **Pass Type ID Certificate**, pick your Pass Type ID and upload `pass.csr`. Download the certificate (`pass.cer`) and upload it to the same folder.
4. Download **Worldwide Developer Relations - G4** from [Apple PKI](https://www.apple.com/certificateauthority/) into the same folder.
5. Convert both to PEM and lock down the files:
   ```bash
   openssl x509 -inform DER -in pass.cer -out pass-cert.pem
   openssl x509 -inform DER -in AppleWWDRCAG4.cer -out AppleWWDRCAG4.pem
   chmod 600 *.pem
   ```
6. In `config.php`, fill in the `apple` section: `enabled => true`, your Pass Type ID, your **Team ID** (Account → Membership details) and the three file paths.
7. On an iPhone, open the tool in Safari and tap **Add to Apple Wallet**. A preview of the pass should appear.

## 3. Google Wallet

1. In the [Google Pay & Wallet Console](https://pay.google.com/business/console), open **Google Wallet API** and note your **Issuer ID**.
2. In [Google Cloud](https://console.cloud.google.com), create or pick a project and enable the **Google Wallet API**.
3. Under **IAM & Admin → Service accounts**, create a service account, then **Keys → Add key → JSON**. Upload the JSON file to your `wallet-certs` folder and `chmod 600` it.
4. Back in the Wallet console, open **Users** and invite the service account's email address with the **Developer** role.
5. In `config.php`, fill in the `google` section: `enabled => true`, the Issuer ID and the path to the JSON key. Optionally set `logo_url` to a public HTTPS image at least 660 × 660 px.
6. On an Android phone, tap **Add to Google Wallet**.

**Demo mode:** a new issuer account starts in demo mode, where only the Google accounts you add as test users in the console can save passes. When everything works, use **Request publishing access** in the console so everyone can save them.

The script creates the pass class (`ISSUER_ID.business_card`) automatically the first time.

## 4. Check that it works

```bash
curl -s -X POST "https://YOUR-DOMAIN/business-card-maker/api/wallet.php?type=apple" \
  -H "Content-Type: application/json" -H "Origin: https://YOUR-DOMAIN" \
  -d '{"name":"Test Person","company":"Test Co","phone":"+880 1700-000000"}'
```

A working setup returns `{"downloadUrl": "..."}` (Apple) or `{"saveUrl": "https://pay.google.com/gp/v/save/..."}` (Google). Detailed errors go to the PHP error log, prefixed with `[business-card wallet]`.

| Problem | Likely cause |
|---|---|
| Apple button shows the free QR steps instead of a pass | `config.php` missing, or Apple `enabled` is `false` |
| Google button shows the free QR steps instead of a pass | Google `enabled` is `false` in `config.php`. On iPhones the Google button is hidden on purpose |
| iPhone says the pass can't be added | Pass Type ID or Team ID in `config.php` doesn't match the certificate, or the WWDR G4 file is wrong |
| Google shows "Something went wrong" | Service account not invited in the Wallet console, wrong Issuer ID, or the account isn't a test user while in demo mode |
| "This site is not allowed" | Add the site to `allowed_origins` |
| "Too many wallet passes" | The per-hour limit in `rate_limit_per_hour` was reached |

## Privacy and security

- Card details are sent to `wallet.php` only when someone taps a wallet button.
- Apple passes are written to the server's temp folder and deleted on download, or after 10 minutes.
- Google passes are created through Google's API and stored by Google as part of Google Wallet.
- The script keeps a hashed per-IP counter for rate limiting and nothing else.
- Keep `wallet-certs` outside the web root. Anyone with your Pass Type ID key can issue passes in your name.
