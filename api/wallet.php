<?php
/**
 * Free Business Card Maker: Apple Wallet and Google Wallet pass endpoint.
 *
 *   POST wallet.php?type=apple   JSON card  -> { "downloadUrl": "...wallet.php?download=TOKEN" }
 *   GET  wallet.php?download=TOKEN          -> the signed .pkpass (valid for 10 minutes, one download)
 *   POST wallet.php?type=google  JSON card  -> { "saveUrl": "https://pay.google.com/gp/v/save/..." }
 *
 * No external libraries. Needs PHP 8+, with the openssl, zip, curl and (optionally) gd extensions.
 * Settings live in config.php (copy config.sample.php). Card details are not stored by this script:
 * Apple passes are deleted after download; Google keeps the pass on its own servers.
 */
declare(strict_types=1);

header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: no-referrer');

final class UserFacingError extends RuntimeException
{
    public function __construct(string $message, public int $status = 503)
    {
        parent::__construct($message);
    }
}

const PASS_TTL = 600;          // seconds a generated .pkpass waits for its download
const MAX_BODY = 700000;       // bytes; enough for a ~400 KB logo as a data URL

function send_json(int $status, array $data): void
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}

function fail(int $status, string $message): void
{
    send_json($status, ['error' => $message]);
}

$configFile = __DIR__ . '/config.php';

// Which wallets are switched on (lets the page hide buttons that would not work).
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'GET' && isset($_GET['status'])) {
    $c = is_file($configFile) ? require $configFile : [];
    send_json(200, ['apple' => !empty($c['apple']['enabled']), 'google' => !empty($c['google']['enabled'])]);
}
if (!is_file($configFile)) {
    fail(503, 'Wallet passes are not set up on this server yet.');
}
$cfg = require $configFile;

$tmpDir = rtrim(sys_get_temp_dir(), '/') . '/bcm-wallet';
if (!is_dir($tmpDir)) {
    @mkdir($tmpDir, 0700, true);
}

// Remove expired passes now and then.
if (random_int(1, 20) === 1) {
    foreach (glob($tmpDir . '/*.pkpass') ?: [] as $old) {
        if (filemtime($old) < time() - PASS_TTL) {
            @unlink($old);
        }
    }
}

// ---------------------------------------------------------------- download a generated Apple pass
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'GET' && isset($_GET['download'])) {
    $token = (string) $_GET['download'];
    $file = $tmpDir . '/' . $token . '.pkpass';
    if (!preg_match('/^[a-f0-9]{32}$/', $token) || !is_file($file) || filemtime($file) < time() - PASS_TTL) {
        http_response_code(404);
        header('Content-Type: text/plain; charset=utf-8');
        echo "This wallet pass has expired. Go back and tap Add to Apple Wallet again.";
        exit;
    }
    header('Content-Type: application/vnd.apple.pkpass');
    header('Content-Disposition: attachment; filename="business-card.pkpass"');
    header('Content-Length: ' . filesize($file));
    header('Cache-Control: no-store');
    readfile($file);
    @unlink($file);
    exit;
}

// ---------------------------------------------------------------- same-site requests only
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
$allowed = $cfg['allowed_origins'] ?? [];
if ($origin !== '') {
    if (!in_array($origin, $allowed, true)) {
        fail(403, 'This site is not allowed to create wallet passes here.');
    }
    header('Access-Control-Allow-Origin: ' . $origin);
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type');
    header('Vary: Origin');
}
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
    http_response_code(204);
    exit;
}
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    fail(405, 'Use POST.');
}

// ---------------------------------------------------------------- simple per-IP rate limit
$limit = (int) ($cfg['rate_limit_per_hour'] ?? 30);
if ($limit > 0) {
    $ipFile = $tmpDir . '/rl-' . hash('sha256', ($_SERVER['REMOTE_ADDR'] ?? '') . __DIR__) . '.json';
    $hits = is_file($ipFile) ? (json_decode((string) file_get_contents($ipFile), true) ?: []) : [];
    $hits = array_values(array_filter($hits, fn($t) => is_int($t) && $t > time() - 3600));
    if (count($hits) >= $limit) {
        fail(429, 'Too many wallet passes from this connection. Try again in an hour.');
    }
    $hits[] = time();
    file_put_contents($ipFile, json_encode($hits), LOCK_EX);
}

// ---------------------------------------------------------------- read and clean the card
$raw = file_get_contents('php://input', false, null, 0, MAX_BODY + 1);
if ($raw === false || strlen($raw) > MAX_BODY) {
    fail(413, 'The card data is too large. Try a smaller logo image.');
}
$in = json_decode($raw, true);
if (!is_array($in)) {
    fail(400, 'The card data could not be read.');
}

function clean(mixed $v, int $max): string
{
    if (!is_string($v)) {
        return '';
    }
    $v = preg_replace('/[\x00-\x1F\x7F]+/u', ' ', $v) ?? '';
    return trim(mb_substr(trim($v), 0, $max));
}

function hex_color(mixed $v, string $fallback): string
{
    return (is_string($v) && preg_match('/^#[0-9a-fA-F]{6}$/', $v)) ? strtoupper($v) : $fallback;
}

$card = [
    'name'    => clean($in['name'] ?? '', 80),
    'title'   => clean($in['title'] ?? '', 80),
    'company' => clean($in['company'] ?? '', 80),
    'phone'   => clean($in['phone'] ?? '', 40),
    'email'   => clean($in['email'] ?? '', 120),
    'website' => clean($in['website'] ?? '', 120),
    'address' => clean($in['address'] ?? '', 160),
    'tagline' => clean($in['tagline'] ?? '', 120),
];
if ($card['email'] !== '' && !filter_var($card['email'], FILTER_VALIDATE_EMAIL)) {
    $card['email'] = '';
}
$card['url'] = '';
if ($card['website'] !== '') {
    $u = preg_match('#^https?://#i', $card['website']) ? $card['website'] : 'https://' . $card['website'];
    if (filter_var($u, FILTER_VALIDATE_URL)) {
        $card['url'] = $u;
    }
    $card['website'] = preg_replace('#^https?://#i', '', rtrim($card['website'], '/'));
}
if ($card['name'] === '' && $card['company'] === '') {
    fail(422, 'Add your name or company before creating a wallet pass.');
}
$colors = [
    'bg'    => hex_color($in['colors']['bg'] ?? null, '#1F5E78'),
    'fg'    => hex_color($in['colors']['fg'] ?? null, '#FFFFFF'),
    'label' => hex_color($in['colors']['label'] ?? null, '#D6E2E8'),
];

function vcard(array $c): string
{
    $esc = fn(string $s) => str_replace([',', ';'], ['\\,', '\\;'], str_replace('\\', '\\\\', $s));
    $words = preg_split('/\s+/u', $c['name'], -1, PREG_SPLIT_NO_EMPTY) ?: [];
    $last = count($words) > 1 ? array_pop($words) : '';
    $first = implode(' ', $words);
    $l = ['BEGIN:VCARD', 'VERSION:3.0', 'N:' . $esc($last) . ';' . $esc($first) . ';;;', 'FN:' . $esc($c['name'] ?: $c['company'])];
    if ($c['company'] !== '') $l[] = 'ORG:' . $esc($c['company']);
    if ($c['title'] !== '')   $l[] = 'TITLE:' . $esc($c['title']);
    if ($c['phone'] !== '')   $l[] = 'TEL;TYPE=CELL:' . $c['phone'];
    if ($c['email'] !== '')   $l[] = 'EMAIL:' . $c['email'];
    if ($c['url'] !== '')     $l[] = 'URL:' . $c['url'];
    if ($c['address'] !== '') $l[] = 'ADR:;;' . $esc($c['address']) . ';;;;';
    $l[] = 'END:VCARD';
    return implode("\r\n", $l);
}

$type = $_GET['type'] ?? '';
try {
    if ($type === 'apple') {
        $token = make_apple_pass($cfg['apple'] ?? [], $card, $colors, $in['logo'] ?? null, $tmpDir);
        $self = strtok($_SERVER['REQUEST_URI'] ?? 'wallet.php', '?');
        send_json(200, ['downloadUrl' => $self . '?download=' . $token]);
    } elseif ($type === 'google') {
        send_json(200, ['saveUrl' => make_google_pass($cfg['google'] ?? [], $allowed, $card, $colors, $tmpDir)]);
    }
    fail(400, 'Unknown wallet type.');
} catch (UserFacingError $e) {
    fail($e->status, $e->getMessage());
} catch (Throwable $e) {
    error_log('[business-card wallet] ' . $e->getMessage());
    fail(500, 'The wallet pass could not be created. Please try again later.');
}

// ================================================================ Apple Wallet
function rgb(string $hex): string
{
    return sprintf('rgb(%d, %d, %d)', hexdec(substr($hex, 1, 2)), hexdec(substr($hex, 3, 2)), hexdec(substr($hex, 5, 2)));
}

function make_apple_pass(array $a, array $c, array $colors, mixed $logo, string $tmpDir): string
{
    if (empty($a['enabled'])) {
        throw new UserFacingError('Apple Wallet is not set up on this server yet.');
    }
    foreach (['cert_pem', 'key_pem', 'wwdr_pem'] as $k) {
        if (empty($a[$k]) || !is_readable($a[$k])) {
            throw new RuntimeException("Apple Wallet file missing or unreadable: $k");
        }
    }

    $dir = $tmpDir . '/build-' . bin2hex(random_bytes(8));
    mkdir($dir, 0700);
    try {
        // Icons are required; logos are optional.
        foreach (['icon.png', 'icon@2x.png', 'icon@3x.png'] as $f) {
            copy(__DIR__ . '/assets/' . $f, "$dir/$f");
        }
        $hasLogo = write_logo($logo, $dir);

        $vc = vcard($c);
        $fields = static fn(array $pairs) => array_values(array_filter(array_map(
            static fn($p) => $p[2] === '' ? null : ['key' => $p[0], 'label' => $p[1], 'value' => $p[2]],
            $pairs
        )));
        $pass = [
            'formatVersion'      => 1,
            'passTypeIdentifier' => $a['pass_type_id'],
            'teamIdentifier'     => $a['team_id'],
            'serialNumber'       => bin2hex(random_bytes(16)),
            'organizationName'   => $c['company'] ?: ($a['organization_name'] ?? 'Business card'),
            'description'        => 'Business card for ' . ($c['name'] ?: $c['company']),
            'foregroundColor'    => rgb($colors['fg']),
            'backgroundColor'    => rgb($colors['bg']),
            'labelColor'         => rgb($colors['label']),
            'generic' => [
                'primaryFields'   => $fields([['name', $c['title'], $c['name'] ?: $c['company']]]),
                'secondaryFields' => $fields([['company', 'COMPANY', $c['name'] ? $c['company'] : '']]),
                'auxiliaryFields' => $fields([['phone', 'PHONE', $c['phone']], ['email', 'EMAIL', $c['email']]]),
                'backFields'      => $fields([
                    ['b-phone', 'Phone', $c['phone']],
                    ['b-email', 'Email', $c['email']],
                    ['b-web', 'Website', $c['url']],
                    ['b-address', 'Address', $c['address']],
                    ['b-tagline', 'About', $c['tagline']],
                ]),
            ],
            'barcodes' => [[
                'format'          => 'PKBarcodeFormatQR',
                'message'         => $vc,
                'messageEncoding' => preg_match('/[^\x00-\x7F]/', $vc) ? 'utf-8' : 'iso-8859-1',
                'altText'         => 'Scan to save contact',
            ]],
        ];
        if (!$hasLogo) {
            $pass['logoText'] = $c['company'] ?: $c['name'];
        }
        file_put_contents("$dir/pass.json", json_encode($pass, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));

        // manifest.json: SHA-1 of every file in the pass
        $manifest = [];
        foreach (scandir($dir) as $f) {
            if ($f[0] !== '.') {
                $manifest[$f] = sha1_file("$dir/$f");
            }
        }
        file_put_contents("$dir/manifest.json", json_encode($manifest, JSON_UNESCAPED_SLASHES));

        // signature: detached PKCS#7 of manifest.json, signed with the Pass Type ID certificate + Apple WWDR
        $smime = "$dir/../" . basename($dir) . '.smime';
        $ok = openssl_pkcs7_sign(
            "$dir/manifest.json", $smime,
            'file://' . $a['cert_pem'],
            ['file://' . $a['key_pem'], (string) ($a['key_password'] ?? '')],
            [], PKCS7_BINARY | PKCS7_DETACHED, $a['wwdr_pem']
        );
        if (!$ok) {
            throw new RuntimeException('openssl_pkcs7_sign failed: ' . openssl_error_string());
        }
        file_put_contents("$dir/signature", smime_to_der((string) file_get_contents($smime)));
        @unlink($smime);

        $token = bin2hex(random_bytes(16));
        $zipPath = "$tmpDir/$token.pkpass";
        $zip = new ZipArchive();
        if ($zip->open($zipPath, ZipArchive::CREATE | ZipArchive::OVERWRITE) !== true) {
            throw new RuntimeException('Could not create the pass file.');
        }
        foreach (scandir($dir) as $f) {
            if ($f[0] !== '.') {
                $zip->addFile("$dir/$f", $f);
            }
        }
        $zip->close();
        return $token;
    } finally {
        foreach (glob("$dir/*") ?: [] as $f) {
            @unlink($f);
        }
        @rmdir($dir);
    }
}

/** openssl_pkcs7_sign writes S/MIME text; Wallet needs the raw DER signature inside it. */
function smime_to_der(string $smime): string
{
    $marker = 'filename="smime.p7s"';
    $start = strpos($smime, $marker);
    if ($start === false) {
        throw new RuntimeException('Unexpected signature format.');
    }
    $body = substr($smime, $start + strlen($marker));
    $end = strpos($body, '------');
    $der = base64_decode(trim($end === false ? $body : substr($body, 0, $end)), true);
    if ($der === false || $der === '') {
        throw new RuntimeException('Could not decode the signature.');
    }
    return $der;
}

/** Saves the uploaded logo as logo.png / @2x / @3x (max 160 x 50 pt). Returns false if there is none. */
function write_logo(mixed $logo, string $dir): bool
{
    if (!is_string($logo) || !function_exists('imagecreatefromstring')) {
        return false;
    }
    if (!preg_match('#^data:image/(png|jpe?g|webp);base64,([A-Za-z0-9+/=]+)$#', $logo, $m)) {
        return false;
    }
    $bytes = base64_decode($m[2], true);
    if ($bytes === false || strlen($bytes) > 500000) {
        return false;
    }
    $src = @imagecreatefromstring($bytes);
    if (!$src) {
        return false;
    }
    $w = imagesx($src);
    $h = imagesy($src);
    foreach (['logo.png' => 1, 'logo@2x.png' => 2, 'logo@3x.png' => 3] as $name => $scale) {
        $r = min(160 * $scale / $w, 50 * $scale / $h);
        $nw = max(1, (int) round($w * $r));
        $nh = max(1, (int) round($h * $r));
        $dst = imagecreatetruecolor($nw, $nh);
        imagealphablending($dst, false);
        imagesavealpha($dst, true);
        imagefill($dst, 0, 0, imagecolorallocatealpha($dst, 0, 0, 0, 127));
        imagecopyresampled($dst, $src, 0, 0, 0, 0, $nw, $nh, $w, $h);
        imagepng($dst, "$dir/$name");
        imagedestroy($dst);
    }
    imagedestroy($src);
    return true;
}

// ================================================================ Google Wallet
function b64url(string $s): string
{
    return rtrim(strtr(base64_encode($s), '+/', '-_'), '=');
}

function jwt_rs256(array $claims, string $privateKeyPem): string
{
    $unsigned = b64url(json_encode(['alg' => 'RS256', 'typ' => 'JWT'])) . '.'
        . b64url(json_encode($claims, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
    if (!openssl_sign($unsigned, $sig, $privateKeyPem, OPENSSL_ALGO_SHA256)) {
        throw new RuntimeException('Could not sign the Google token: ' . openssl_error_string());
    }
    return $unsigned . '.' . b64url($sig);
}

function http_json(string $method, string $url, ?string $bearer, ?array $body, array $form = []): array
{
    $ch = curl_init($url);
    $headers = [];
    if ($bearer) {
        $headers[] = 'Authorization: Bearer ' . $bearer;
    }
    if ($body !== null) {
        $headers[] = 'Content-Type: application/json';
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($body, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
    } elseif ($form) {
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($form));
    }
    curl_setopt_array($ch, [
        CURLOPT_CUSTOMREQUEST  => $method,
        CURLOPT_HTTPHEADER     => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 15,
    ]);
    $res = curl_exec($ch);
    $status = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    if ($res === false) {
        $err = curl_error($ch);
        curl_close($ch);
        throw new RuntimeException("Request to $url failed: $err");
    }
    curl_close($ch);
    return [$status, json_decode((string) $res, true) ?: []];
}

function google_token(array $sa, string $tmpDir): string
{
    $cache = $tmpDir . '/gtoken-' . md5($sa['client_email']) . '.json';
    if (is_file($cache)) {
        $t = json_decode((string) file_get_contents($cache), true);
        if (!empty($t['token']) && ($t['exp'] ?? 0) > time() + 60) {
            return $t['token'];
        }
    }
    $now = time();
    $assertion = jwt_rs256([
        'iss'   => $sa['client_email'],
        'scope' => 'https://www.googleapis.com/auth/wallet_object.issuer',
        'aud'   => 'https://oauth2.googleapis.com/token',
        'iat'   => $now,
        'exp'   => $now + 3600,
    ], $sa['private_key']);
    [$status, $res] = http_json('POST', 'https://oauth2.googleapis.com/token', null, null, [
        'grant_type' => 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion'  => $assertion,
    ]);
    if ($status !== 200 || empty($res['access_token'])) {
        throw new RuntimeException('Google sign-in failed (' . $status . '): ' . json_encode($res));
    }
    file_put_contents($cache, json_encode(['token' => $res['access_token'], 'exp' => $now + (int) ($res['expires_in'] ?? 3600)]), LOCK_EX);
    @chmod($cache, 0600);
    return $res['access_token'];
}

function make_google_pass(array $g, array $origins, array $c, array $colors, string $tmpDir): string
{
    if (empty($g['enabled'])) {
        throw new UserFacingError('Google Wallet is not set up on this server yet.');
    }
    if (empty($g['service_account_json']) || !is_readable($g['service_account_json'])) {
        throw new RuntimeException('Google service account key missing or unreadable.');
    }
    $sa = json_decode((string) file_get_contents($g['service_account_json']), true);
    if (empty($sa['client_email']) || empty($sa['private_key'])) {
        throw new RuntimeException('Google service account key is not valid.');
    }
    $issuer = (string) $g['issuer_id'];
    $classId = $issuer . '.' . preg_replace('/[^A-Za-z0-9._-]/', '_', (string) ($g['class_suffix'] ?? 'business_card'));
    $base = 'https://walletobjects.googleapis.com/walletobjects/v1';
    $token = google_token($sa, $tmpDir);

    // The pass class is created once and remembered.
    $classFlag = $tmpDir . '/gclass-' . md5($classId) . '.ok';
    if (!is_file($classFlag)) {
        [$st] = http_json('GET', "$base/genericClass/" . rawurlencode($classId), $token, null);
        if ($st === 404) {
            [$st, $res] = http_json('POST', "$base/genericClass", $token, ['id' => $classId]);
            if ($st !== 200 && $st !== 409) {
                throw new RuntimeException('Could not create the Google pass class (' . $st . '): ' . json_encode($res));
            }
        } elseif ($st !== 200) {
            throw new RuntimeException('Could not read the Google pass class (' . $st . ')');
        }
        touch($classFlag);
    }

    $lv = static fn(string $v) => ['defaultValue' => ['language' => 'en', 'value' => $v]];
    $modules = [];
    foreach ([['phone', 'Phone', $c['phone']], ['email', 'Email', $c['email']], ['website', 'Website', $c['website']],
              ['address', 'Address', $c['address']], ['about', 'About', $c['tagline']]] as [$id, $h, $v]) {
        if ($v !== '') {
            $modules[] = ['id' => $id, 'header' => $h, 'body' => $v];
        }
    }
    $links = [];
    $tel = preg_replace('/[^0-9+]/', '', $c['phone']);
    if ($tel !== '') $links[] = ['id' => 'call', 'uri' => 'tel:' . $tel, 'description' => 'Call'];
    if ($c['email'] !== '') $links[] = ['id' => 'mail', 'uri' => 'mailto:' . $c['email'], 'description' => 'Email'];
    if ($c['url'] !== '') $links[] = ['id' => 'web', 'uri' => $c['url'], 'description' => 'Website'];

    $objectId = $issuer . '.' . bin2hex(random_bytes(12));
    $object = [
        'id'                 => $objectId,
        'classId'            => $classId,
        'state'              => 'ACTIVE',
        'cardTitle'          => $lv($c['company'] ?: ($g['issuer_name'] ?? 'Business card')),
        'header'             => $lv($c['name'] ?: $c['company']),
        'hexBackgroundColor' => $colors['bg'],
        'barcode'            => ['type' => 'QR_CODE', 'value' => vcard($c), 'alternateText' => 'Scan to save contact'],
    ];
    if ($c['title'] !== '') $object['subheader'] = $lv($c['title']);
    if ($modules) $object['textModulesData'] = $modules;
    if ($links) $object['linksModuleData'] = ['uris' => $links];
    if (!empty($g['logo_url'])) {
        $object['logo'] = ['sourceUri' => ['uri' => $g['logo_url']], 'contentDescription' => $lv('Logo')];
    }

    [$st, $res] = http_json('POST', "$base/genericObject", $token, $object);
    if ($st !== 200) {
        throw new RuntimeException('Could not create the Google pass (' . $st . '): ' . json_encode($res));
    }

    // A short ("skinny") token that only points at the pass, so the link stays well under Google's 1800-character limit.
    $jwt = jwt_rs256([
        'iss'     => $sa['client_email'],
        'aud'     => 'google',
        'typ'     => 'savetowallet',
        'iat'     => time(),
        'origins' => array_values($origins),
        'payload' => ['genericObjects' => [['id' => $objectId, 'classId' => $classId]]],
    ], $sa['private_key']);
    return 'https://pay.google.com/gp/v/save/' . $jwt;
}
