# Word of the Day

A tiny static site that shows one sophisticated, uncommon English word at random on every visit, with a definition, part of speech, an example, and optionally pronunciation and synonyms.

Live: <https://matthewdejager.github.io/word-of-the-day/>

Plain HTML, CSS and JavaScript. No framework, no build step for the site, no backend and no network calls beyond loading its own files. It works offline once you've visited it.

## Files

| File | What it is |
| --- | --- |
| `index.html` | Markup only |
| `style.css` | All styles (light and dark mode via `prefers-color-scheme`) |
| `app.js` | Loads `words.json`, picks a random word, handles the button and spacebar, registers the service worker |
| `words.xlsx` | **The source of truth** for the word list. Edit this one. |
| `words.json` | Generated from `words.xlsx` by `build_words.py`. **Never edit it by hand.** |
| `build_words.py` | Converts `words.xlsx` into `words.json` |
| `manifest.json`, `service-worker.js` | Install-as-app and offline support |
| `icons/` | `icon-192.png`, `icon-512.png` (app icons), `icon.ico` (Windows shortcut) |

## One-time setup: Python dependencies

You need Python 3 installed. Then, in the repo folder:

```bash
pip install -r requirements.txt
```

That installs `openpyxl`, which the build script uses to read the spreadsheet.

## Adding or editing a word

1. Open `words.xlsx` in Excel and add or edit a row. Search, filter and sort however you like; row order doesn't matter to the app.
2. **Save and close Excel.** The build script can't read the file while Excel has it locked.
3. Rebuild the JSON:

   ```bash
   python build_words.py
   ```

   If a row has a problem, the script lists every bad row by its Excel row number and does **not** touch `words.json`. Fix the rows and run it again.
4. Commit and push both files:

   ```bash
   git add words.xlsx words.json
   ```

   ```bash
   git commit -m "Add new words"
   ```

   ```bash
   git push
   ```

GitHub Pages redeploys in a minute or so. You **don't** need to bump the service worker version for word changes, because `words.json` is always fetched fresh when you're online.

### Spreadsheet columns

| Column | Required | Notes |
| --- | --- | --- |
| `word` | yes | Multi-word entries (e.g. `sotto voce`) are fine. Duplicates are rejected (case-insensitive). |
| `pos` | yes | `noun`, `verb`, `adjective`, `adverb` (also `pronoun`, `preposition`, `conjunction`, `interjection`, `phrase`). Combine with a slash: `adverb / adjective`. Typos are rejected. To allow another value, add it to `KNOWN_POS` in `build_words.py`. |
| `pronunciation` | no | Phonetic respelling. See the convention below. |
| `definition` | yes | |
| `example` | yes | Don't add quotation marks; the app adds curly quotes. |
| `synonyms` | no | Separate with semicolons: `discernment; acumen; insight`. |

Keep the header row exactly as it is: `word | pos | pronunciation | definition | example | synonyms`. Empty rows are skipped. Leave optional cells blank when they don't apply, and the app hides that section entirely.

## Pronunciation convention

Use plain-text respelling, not IPA:

- **Syllables are lowercase and separated by hyphens.**
- **The stressed syllable is in UPPERCASE.**
- **Separate words with a space** (each word gets its own hyphenated syllables).

Examples:

| Word | Respelling |
| --- | --- |
| perspicacity | `per-spi-KASS-i-tee` |
| obstreperous | `uhb-STREP-er-uhs` |
| quotidian | `kwoh-TID-ee-uhn` |
| sotto voce | `SOT-oh VOH-chay` |

These spellings keep the sounds consistent:

| Sound | Write | As in |
| --- | --- | --- |
| unstressed "uh" (schwa) | `uh` | **a**bout → `uh` |
| long a | `ay` | d**ay** |
| long e | `ee` | s**ee** |
| long i | `y` / `eye` | `REK-uhn-dyte`, `EYE-dee-uh` |
| long o | `oh` | g**o** |
| "oo" | `oo` | f**oo**d |
| "yoo" | `yoo` | **u**se |
| "er" | `er` | h**er** |
| "zh" | `zh` | mea**s**ure |

The build script checks the basic shape: every syllable must be all lowercase or ALL UPPERCASE, and at least one must be uppercase.

## Testing locally

Opening `index.html` by double-clicking won't work, because browsers block `fetch('words.json')` over `file://`. Serve the folder instead:

```bash
python -m http.server 8000
```

Then open <http://localhost:8000>. Press `Ctrl+C` in the terminal to stop the server.

The service worker also runs on `localhost`, so you may see cached shell files while testing. In Chrome or Edge, open DevTools → **Application** → **Service workers** and tick **Update on reload**.

## Updating the app shell (service worker cache version)

The service worker caches the app shell (`index.html`, `style.css`, `app.js`, `manifest.json`, icons) **cache-first**, so the app opens instantly and works offline. `words.json` is **network-first**: it's fetched fresh when you're online, and the cached copy is used when you're offline or the network takes longer than 4 seconds.

**Whenever you change any shell file, bump the version** at the top of `service-worker.js`:

```js
const CACHE_VERSION = "v1";   // change to "v2", "v3", …
```

Commit and push it with your other changes. On the next visit while online, the browser sees that `service-worker.js` has changed, installs the new version, deletes the old cache, and the page reloads itself once with the new files.

If you forget to bump it, visitors keep the old shell files indefinitely.

## Install on your phone

### iPhone / iPad (Safari)

1. Open the site in **Safari** (other browsers on iOS may not show the option).
2. Tap the **Share** button (square with an up arrow).
3. Scroll down and tap **Add to Home Screen**.
4. Keep the name "Word of the Day" and tap **Add**.

It opens full-screen without browser bars and works offline.

### Android (Chrome)

1. Open the site in **Chrome**.
2. Tap the **⋮** menu → **Install app** (on some versions it's **Add to Home screen** → **Install**).
3. Confirm.

## Mobile caching gotchas and how to force a refresh

- **GitHub Pages caches files for about 10 minutes.** Right after a push, wait a minute for the deploy, and allow up to 10 minutes before assuming something is broken.
- **Shell changes need a version bump** (see above). Without one, the installed app keeps the old HTML, CSS and JS.
- **New words appear on the next online visit.** Updated shell files show up after one automatic reload.
- **iOS home-screen apps keep their own storage**, separate from Safari tabs. To pick up an update, fully close the app (swipe it away in the app switcher) and reopen it while online.

If something still looks stale:

- **iOS:** Settings → Apps → Safari → Advanced → Website Data → find `github.io` → swipe to delete. (On older iOS: Settings → Safari → Advanced → Website Data.) If it's installed to the home screen, delete and re-add the icon.
- **Android Chrome:** open the site → tap the padlock/tune icon left of the address → **Site settings** → **Delete data** (or **Clear & reset**). Then reload.
- **Desktop Chrome/Edge:** `Ctrl+Shift+R` bypasses the cache for one load. For a full reset: DevTools → **Application** → **Storage** → **Clear site data**.

## Windows desktop shortcut with a custom icon

A ready-made `icons/icon.ico` is included. Windows shortcuts need the icon file on your disk, so first copy it somewhere permanent where you won't delete it, e.g. `C:\Users\<you>\Documents\Icons\word-of-the-day.ico`. (If you'd rather make your own: upload `icons/icon-512.png` to any online PNG-to-ICO converter such as icoconvert.com or convertio.co, download the `.ico`, and put that in the same permanent spot.)

1. Right-click an empty spot on the desktop → **New** → **Shortcut**.
2. For the location, paste:

   ```
   https://matthewdejager.github.io/word-of-the-day/
   ```

   Click **Next**.
3. Name it `Word of the Day` → **Finish**.
4. Right-click the new shortcut → **Properties** → **Web Document** tab → **Change Icon…**
5. Click **Browse…**, select your `.ico` file, click **OK**, then **OK** again.

Double-clicking it opens the site in your default browser. If the icon doesn't update right away, sign out and back in, or restart Explorer.

**Alternative:** in Chrome or Edge, visit the site and choose **Install** from the address bar (or ⋮ → **Cast, save and share** → **Install page as app**). That creates a desktop or Start-menu entry with the app icon that opens in its own window and works offline.
