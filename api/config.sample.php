<?php
// Copy this file to config.php and fill it in. config.php is never served as text:
// PHP runs it and it prints nothing. Keep the certificate and key files OUTSIDE your web root,
// never inside this api folder: web servers can be set up to serve .json and .pem files as plain text.

return [
    // Sites allowed to call this endpoint (scheme + host, no trailing slash).
    'allowed_origins' => [
        'https://iqbalmahmud.com',
        'https://womenailabs.org',
    ],

    // Requests allowed per visitor IP per hour (protects your signing certificate from abuse).
    // Behind Cloudflare, also set up the real-IP lines in deploy/nginx.conf so each visitor is counted separately.
    'rate_limit_per_hour' => 30,

    // Passes allowed per day in total, across all visitors. A backstop against abuse; 0 turns it off.
    'daily_limit' => 1000,

    // Private folder for passes waiting to be downloaded. Use a folder OUTSIDE your web root that only
    // this site's user can read (the script refuses a folder that other accounts can read).
    // Default: the system temp folder. On shared hosting, set your own, for example:
    // 'tmp_dir' => '/home/USER/wallet-tmp',

    // ---------------- Apple Wallet ----------------
    'apple' => [
        'enabled'            => false,
        'pass_type_id'       => 'pass.org.womenailabs.businesscard', // your Pass Type ID
        'team_id'            => 'ABCDE12345',                        // your Apple Developer Team ID
        'organization_name'  => 'Women AI Labs',                     // shown on the lock screen
        'cert_pem'           => '/home/USER/wallet-certs/pass-cert.pem',
        'key_pem'            => '/home/USER/wallet-certs/pass-key.pem',
        'key_password'       => '',                                  // leave empty if the key has no password
        'wwdr_pem'           => '/home/USER/wallet-certs/AppleWWDRCAG4.pem',
    ],

    // ---------------- Google Wallet ----------------
    'google' => [
        'enabled'              => false,
        'issuer_id'            => '3388000000000000000',             // from the Google Pay & Wallet Console
        'class_suffix'         => 'business_card',                   // created automatically on first use
        'service_account_json' => '/home/USER/wallet-certs/google-wallet-key.json',
        'issuer_name'          => 'Women AI Labs',
        // Optional public HTTPS image (at least 660 x 660 px) shown as the pass logo.
        // Leave empty to show the first letter of the card title instead.
        'logo_url'             => '',
    ],
];
