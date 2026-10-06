<?php
// Copy this file to config.php and fill it in. config.php is never served as text:
// PHP runs it and it prints nothing. Keep the certificate and key files OUTSIDE your web root.

return [
    // Sites allowed to call this endpoint (scheme + host, no trailing slash).
    'allowed_origins' => [
        'https://iqbalmahmud.com',
        'https://womenailabs.org',
    ],

    // Requests allowed per visitor IP per hour (protects your signing certificate from abuse).
    'rate_limit_per_hour' => 30,

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
