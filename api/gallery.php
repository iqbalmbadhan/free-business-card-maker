<?php
/**
 * Business Card Maker – AiInfos: design ideas gallery.
 *
 *   GET gallery.php?page=1&per=24&q=gold  ->  { total, page, pages, per, items: [{ name, title, url }] }
 *
 * Read-only. Lists image files from ONE folder (no sub-folders, no paths from the visitor).
 * Set the two values below to where your card images live.
 */
declare(strict_types=1);

// Folder on disk that holds the images, and the public web address of that same folder.
// Default: a folder named "cards-demo" at your web root, next to "business-card-maker".
const GALLERY_DIR = __DIR__ . '/../../cards-demo';
const GALLERY_URL = '/cards-demo/';

const IMAGE_TYPES = '/\.(jpe?g|png|webp|avif|gif)$/i';
const MAX_PER_PAGE = 60;

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: public, max-age=300');

function out(array $data, int $status = 200): void
{
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? 'GET') !== 'GET') {
    out(['error' => 'Use GET.'], 405);
}

$dir = realpath(GALLERY_DIR);
if ($dir === false || !is_dir($dir)) {
    out(['total' => 0, 'page' => 1, 'pages' => 0, 'per' => 0, 'items' => []]);
}

/** Turns "abstract-black-and-gold-brushes-business-card-set-free-vector.jpg" into "Abstract black and gold brushes". */
function nice_title(string $file, int $n): string
{
    $t = preg_replace('/\.[a-z0-9]+$/i', '', $file);
    if (preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i', $t) || !preg_match('/[a-z]{3}/i', $t)) {
        return 'Design ' . $n;
    }
    $t = str_replace(['-', '_', '+'], ' ', $t);
    $t = preg_replace('/\b(free|vector|vectors|template|templates|set|design|card|cards|business|psd|eps|ai|stock|illustration|premium|\d+)\b/i', ' ', $t);
    $t = trim(preg_replace('/\s+/', ' ', (string) $t));
    if ($t === '') {
        return 'Design ' . $n;
    }
    if (!str_contains($t, ' ')) {
        $t .= ' design';   // "blue-business-card-design-01.png" -> "Blue design"
    }
    return mb_strtoupper(mb_substr($t, 0, 1)) . mb_substr($t, 1);
}

// Build (and cache for 10 minutes) the sorted file list.
$cacheFile = rtrim(sys_get_temp_dir(), '/') . '/bcm-gallery-' . md5($dir) . '.json';
$files = null;
if (is_file($cacheFile) && filemtime($cacheFile) > time() - 600 && filemtime($cacheFile) >= filemtime($dir)) {
    $files = json_decode((string) file_get_contents($cacheFile), true);
}
if (!is_array($files)) {
    $files = [];
    foreach (scandir($dir) ?: [] as $f) {
        if ($f[0] === '.' || !preg_match(IMAGE_TYPES, $f) || !is_file("$dir/$f")) {
            continue;
        }
        $files[] = $f;
    }
    // Files with descriptive names first, then the ones named with random IDs.
    $isId = fn(string $f) => (bool) preg_match('/^[0-9a-f]{8}-[0-9a-f]{4}-/i', $f) || !preg_match('/[a-z]{3}/i', preg_replace('/\.[a-z0-9]+$/i', '', $f));
    usort($files, fn($a, $b) => [$isId($a), strnatcasecmp($a, $b)] <=> [$isId($b), 0]);
    $files = array_values($files);
    @file_put_contents($cacheFile, json_encode($files), LOCK_EX);
}

$items = [];
foreach ($files as $i => $f) {
    $items[] = ['name' => $f, 'title' => nice_title($f, $i + 1), 'url' => GALLERY_URL . rawurlencode($f)];
}

$q = trim((string) ($_GET['q'] ?? ''));
if ($q !== '') {
    $q = mb_strtolower(mb_substr($q, 0, 60));
    $items = array_values(array_filter($items, function ($it) use ($q) {
        foreach (preg_split('/\s+/', $q) as $word) {
            if ($word !== '' && !str_contains(mb_strtolower($it['title'] . ' ' . $it['name']), $word)) {
                return false;
            }
        }
        return true;
    }));
}

$per = max(1, min(MAX_PER_PAGE, (int) ($_GET['per'] ?? 24)));
$total = count($items);
$pages = (int) ceil($total / $per);
$page = max(1, min(max(1, $pages), (int) ($_GET['page'] ?? 1)));

out([
    'total' => $total,
    'page'  => $page,
    'pages' => $pages,
    'per'   => $per,
    'items' => array_slice($items, ($page - 1) * $per, $per),
]);
