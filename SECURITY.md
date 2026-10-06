# Security

## Reporting a problem

Please don't open a public issue for security problems. Email **iqbal@womenailabs.org** with the details and, if you can, steps to reproduce. You'll get a reply within a few days.

## How the app is protected

**The page (every edition)**
- Everything happens in the visitor's browser. Card details never leave the device unless the visitor taps a wallet button.
- A strict Content Security Policy (a meta tag added at build time) allows only the page's own scripts, identified by their SHA-256 fingerprints, plus Google Fonts. Injected script would be refused.
- User input is only drawn on a canvas or set as plain text; it's never inserted as HTML. Website and social links always get `https://` in front, so `javascript:` links aren't possible.
- Saved designs are read back from browser storage field by field, with type and length checks; anything else is ignored.
- The Google Wallet tab opens without a link back to the app, and only Google's own save address is accepted.

**Wallet script (`server/api/wallet.php`, optional)**
- Only your own pages can create passes: requests without an allowed `Origin` are refused.
- Limits: 30 passes per visitor per hour (IPv6 counted per /64), a daily total (1,000 by default), and at most 2 passes built at the same time. If a limit can't be checked, the request is refused rather than allowed.
- Logos are checked before decoding: PNG, JPEG or WebP only, matching the declared type, at most 1000 × 1000 pixels. This stops "decompression bomb" images that claim huge sizes.
- Text fields are cleaned of control, zero-width and direction-override characters (used to disguise text); ZWJ and ZWNJ are kept because Bengali needs them.
- Passes are written with owner-only permissions to a private folder (refused if other accounts can read it), downloaded once, then deleted. A download is claimed atomically, so two requests can't both get it.
- Errors never show internal details to visitors; they go to the server's error log.

**Server settings (`dist/server-setup/<edition>/`)**
- Settings, keys, backups, editor files and dot files (`.git`, `.env`) return 404. On nginx these use exact and prefix matches, which win over other rules wherever they're pasted.
- Security headers: `X-Frame-Options`, `frame-ancestors`, `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy` and `Permissions-Policy`.

## Your part

- Keep Apple and Google keys **outside the web root**, never in `api/`. `.gitignore` keeps `config.php`, keys and `.json` files in `server/api/` out of git.
- Behind Cloudflare, set up the real-IP lines in `nginx.conf`, using only Cloudflare's published ranges, so the wallet limits count each visitor separately.
- Optionally turn on the nginx burst limit for `wallet.php` (instructions in `nginx.conf`).
