# Research: Apps and Games Download Support

**Feature**: 001-apps-games-download
**Date**: 2025-01-15
**Purpose**: Resolve technical unknowns and establish implementation approach

## Executive Summary

This research document analyzes the Vodu store platform structure, evaluates HTML parsing strategies, and establishes technical decisions for implementing apps/games download functionality. Key findings: Vodu store is a Vue.js SPA requiring JavaScript rendering for dynamic content. Recommended approach: Use Selenium with headless Chrome for reliability, with BeautifulSoup4 as fallback for static content.

## Research Questions & Decisions

### Q1: HTML Parsing Strategy for Vue.js SPA

**Problem**: Vodu store (https://share.vodu.store) is a Vue.js single-page application. Initial HTML only contains `<div id="app"></div>` and script tags. Download links are rendered dynamically via JavaScript after page load.

**Investigation**:

Analyzed the initial HTML response from `https://share.vodu.store/#/details/214620`:

```html
<!DOCTYPE html>
<html lang="ara" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>vodu-store</title>
  <link rel="stylesheet" href="/css/app.09c796dc.css">
  <script src="https://unpkg.com/vue-recaptcha@latest/dist/vue-recaptcha.js"></script>
</head>
<body>
  <noscript>
    <strong>We're sorry but vodu-store doesn't work properly without JavaScript enabled.</strong>
  </noscript>
  <div id="app"></div>
  <script src="/js/chunk-vendors.246fb097.js"></script>
  <script src="/js/app.aa83b892.js"></script>
</body>
</html>
```

**Key Findings**:
- No "تحميل" buttons in initial HTML (requires JavaScript execution)
- Vue.js app bundles are minified and split across multiple JS files
- Page uses client-side routing (hash-based: `#/details/214620`)
- Download URLs are likely fetched from an API endpoint and rendered dynamically

**Options Evaluated**:

| Option | Pros | Cons | Feasibility |
|--------|------|------|-------------|
| **A. Selenium with Headless Chrome** | - Renders JavaScript fully<br>- Reliable for SPAs<br>- Maintains session state | - Heavy dependency (~100MB)<br>- Slower startup time<br>- Requires ChromeDriver | ✅ **RECOMMENDED** |
| **B. Reverse-engineer API** | - Lightweight<br>- Fast execution<br>- No browser overhead | - May break if API changes<br>- Requires authentication/headers<br>- CORS issues possible | ⚠️ FALLBACK |
| **C. Parse embedded JSON** | - Fastest approach<br>- No dependencies | - Data likely not in initial HTML<br>- Fragile if structure changes | ❌ NOT VIABLE |

**Decision**: **Option A - Selenium with Headless Chrome**

**Rationale**:
- Most reliable for JavaScript-heavy SPAs
- Handles dynamic content rendering correctly
- Maintains session state (cookies, headers) automatically
- Industry-standard for web scraping SPAs
- Aligns with constitution principle "Robust Error Handling" - fewer edge cases

**Alternative Path**: If Vodu store exposes a public API for download metadata (discovered during implementation), can switch to Option B for better performance. This would be a Phase 2 optimization.

**Implementation Notes**:
- Use `selenium` package with `chromedriver-autoinstaller` for automatic driver management
- Configure headless mode: `options.add_argument('--headless')`
- Set page load timeout: 30 seconds
- Wait for "تحميل" buttons to appear: `WebDriverWait(driver, 10).until(...)`
- Fall back to BeautifulSoup4 if page loads without JavaScript (graceful degradation)

---

### Q2: Resume Checkpoint Storage Strategy

**Problem**: Need to persist download state across app restarts to support resume functionality. Must balance simplicity, reliability, and performance.

**Options Evaluated**:

| Option | Pros | Cons | Complexity |
|--------|------|------|------------|
| **A. In-memory only** | - Zero storage overhead<br>- No file I/O<br>- Simplest implementation | - Lost on app close<br>- No resume after restart<br>- Poor UX for large downloads | ⭐ Lowest |
| **B. JSON file in app directory** | - Persistent across sessions<br>- Human-readable (debuggable)<br>- Simple format<br>- Fast read/write | - Manual file locking needed<br>- Potential corruption if crash during write | ⭐⭐ Medium |
| **C. SQLite database** | - ACID guarantees<br>- Structured queries<br>- Handles concurrent access | - Overkill for single-user app<br>- Additional dependency<br>- More complex schema | ⭐⭐⭐ Highest |

**Decision**: **Option B - JSON File in App Directory**

**Rationale**:
- Balances persistence with simplicity
- Sufficient for single-user desktop app (no concurrency concerns)
- Easy to debug (can open JSON file to inspect state)
- Fast enough for typical use (3-10 parts, <1KB per session)
- No new dependencies (uses standard `json` library)

**Implementation Details**:

**File Location**: `$HOME/.vodu_downloader/resume_state.json` (Windows: `C:\Users\<User>\.vodu_downloader\resume_state.json`)

**JSON Schema**:

```json
{
  "sessions": [
    {
      "session_id": "214620",
      "vodu_store_url": "https://share.vodu.store/#/details/214620",
      "download_location": "C:\\Downloads\\Games",
      "app_name": "Marvels-SpiderMan-2-v1-526--DODI-Repack",
      "total_parts": 5,
      "completed_parts": ["part01.rar", "part02.rar"],
      "incomplete_parts": [
        {
          "filename": "part03.rar",
          "url": "https://share.vodu.store:9999/store-files/part03.rar",
          "bytes_downloaded": 1073741824,
          "expected_size": 2147483648,
          "status": "incomplete"
        }
      ],
      "last_updated": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**Operations**:
- **Load on startup**: Read JSON file, index sessions by `session_id`
- **Save on part completion**: Atomic write (write to temp file, then rename)
- **Cleanup on successful completion**: Remove session from JSON
- **Manual resume**: User re-enters same URL → app looks up session by ID

**Error Handling**:
- If JSON file corrupted: Start with empty state (log warning)
- If file missing: Create new file (first run)
- If write fails: Log error, continue download (resume not available for this session)

---

### Q3: Dependency Additions

**Problem**: Constitution limits dependencies to "requests, tqdm, urllib3". HTML parsing and JavaScript rendering require additional libraries. Need to justify additions and minimize bloat.

**Current Dependencies** (from requirements.txt):
```
requests
urllib3
tqdm
```

**Proposed Additions**:

| Dependency | Purpose | Size | Justification |
|------------|---------|------|---------------|
| **beautifulsoup4** | HTML parsing (fallback) | ~200KB | Standard library for HTML parsing, lightweight |
| **selenium** | JavaScript rendering (primary) | ~10MB code + driver | Required for Vue.js SPA |
| **chromedriver-autoinstaller** | Auto-manage ChromeDriver | ~50KB | Automates driver installation, user-friendly |

**Updated requirements.txt**:
```
requests
urllib3
tqdm
beautifulsoup4
selenium
chromedriver-autoinstaller
```

**Constitution Compliance Check**:

Constitution states: *"Third-party dependencies MUST be limited to: requests, tqdm, urllib3"*

**Violation Analysis**:
- **Violates**: Dependency limit principle
- **Justification**: Vodu store is a Vue.js SPA requiring JavaScript rendering. Cannot implement feature without HTML parsing + JS execution.
- **Mitigation**: Minimized additions (only 3 new libs, all industry standards). No web frameworks, databases, or heavy toolkits.
- **Constitution Amendment Required**: Yes, update Technical Standards section to include HTML parsing dependencies.

**Recommendation**: Update constitution to allow:
> *"Third-party dependencies should be minimized. Standard libraries: requests, tqdm, urllib3. Additional dependencies permitted for domain requirements (e.g., HTML parsing, JavaScript rendering) with technical justification."*

---

### Q4: Disk Space Checking Strategy

**Problem**: Need to validate available disk space before download starts to prevent "disk full" errors mid-download.

**Research**: Cross-platform disk space checking in Python

**Options Evaluated**:

| Option | Pros | Cons | Cross-Platform |
|--------|------|------|----------------|
| **A. shutil.disk_usage()** | - Standard library (Python 3.3+)<br>- Cross-platform<br>- Simple API | - Returns bytes only (need conversion) | ✅ Yes |
| **B. psutil.disk_usage()** | - More detailed info<br>- Human-readable formatting | - External dependency | ⚠️ Requires install |
| **C. Platform-specific APIs** | - Native performance | - Different code per OS<br>- Complex | ❌ No |

**Decision**: **Option A - shutil.disk_usage()** (standard library)

**Implementation**:

```python
import shutil

def check_disk_space(path, required_bytes):
    """Check if sufficient disk space available."""
    try:
        usage = shutil.disk_usage(path)
        available = usage.free
        return available >= required_bytes
    except OSError as e:
        # Cannot determine space, proceed with warning
        print(f"Warning: Cannot check disk space: {e}")
        return True  # Allow download to proceed
```

**Usage**:
- Call before starting download: `check_disk_space(download_path, total_size)`
- Sum all part sizes from HTTP headers (Content-Length)
- Display user-friendly message: "Need 50GB, only 30GB available"
- Offer option to select different location

**Error Handling**:
- If cannot check space (permissions, network drive): Show warning, allow download
- If insufficient space: Block download, suggest alternative location

---

### Q5: HTTP Range Request Implementation

**Problem**: Resume incomplete file downloads by continuing from last byte downloaded. Requires HTTP range requests (RFC 7233).

**Research**: HTTP range request support in Python requests library

**Technical Details**:

**HTTP Headers**:
- **Request**: `Range: bytes=1024-` (resume from byte 1024 to end)
- **Response** (if supported): `206 Partial Content`, `Content-Range: bytes 1024-2047/2048`
- **Response** (if not supported): `200 OK`, full content (fallback to re-download)

**Implementation with requests**:

```python
import requests

def download_with_resume(url, save_path):
    """Download file with resume support using HTTP range requests."""
    # Check existing file
    if os.path.exists(save_path):
        existing_size = os.path.getsize(save_path)
        headers = {'Range': f'bytes={existing_size}-'}
        mode = 'ab'  # append binary
    else:
        headers = {}
        mode = 'wb'  # write binary

    response = requests.get(url, headers=headers, stream=True)

    # Check if server supports range requests
    if response.status_code == 206:
        # Partial content - resume successful
        print(f"Resuming from byte {existing_size}")
    elif response.status_code == 200:
        # Server doesn't support ranges, re-downloading
        if existing_size > 0:
            print("Server doesn't support resume, re-downloading...")
            os.remove(save_path)
            mode = 'wb'
    else:
        raise Exception(f"HTTP {response.status_code}: {response.reason}")

    # Download and append to file
    with open(save_path, mode) as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
```

**Testing Strategy**:
- Test with Vodu store download URLs (verify range request support)
- Simulate interruption: Kill script mid-download, restart
- Validate file integrity: Compare MD5/SHA256 before and after resume

**Fallback**: If server doesn't support range requests, re-download entire file (document to user)

---

## Best Practices Research

### BP1: Multi-Part Download State Management

**Pattern**: Use a coordinator function to manage part sequence and state transitions.

**Best Practices**:
1. **State Machine**: Each part has states: `pending` → `downloading` → `completed` or `failed`
2. **Sequential Downloads**: Download one part at a time (simpler, more reliable)
3. **Progress Tracking**: Track overall progress: `(total_bytes_downloaded / total_size) * 100`
4. **Error Isolation**: One part failure doesn't invalidate other parts
5. **Retry Logic**: Retry failed parts before giving up (3 attempts)

**Anti-Patterns to Avoid**:
- ❌ Parallel downloads (too complex, bandwidth issues)
- ❌ Global state for part tracking (use session object)
- ❌ Blocking GUI during download (use background thread)

### BP2: GUI Responsiveness in tkinter

**Problem**: Long-running downloads block GUI, causing "Not Responding" freezes.

**Solution**: Use `threading.Thread` for background work, `window.after()` for GUI updates.

**Implementation Pattern**:

```python
import threading

def start_download_apps_games():
    """Start download in background thread."""
    download_thread = threading.Thread(target=download_apps_games_worker)
    download_thread.daemon = True  # Kill thread when app closes
    download_thread.start()

def download_apps_games_worker():
    """Worker function for download (runs in background thread)."""
    # Download logic here
    for part in parts:
        download_part(part)
        # Thread-safe GUI update
        window.after(0, lambda: update_progress(part.progress))
```

**Best Practices**:
- ✅ Use daemon threads (auto-cleanup on app close)
- ✅ Update GUI via `window.after(0, callback)` for thread safety
- ✅ Disable "Download" button during download (prevent double-click)
- ✅ Show progress bar and status label
- ❌ Don't use `time.sleep()` in main thread (blocks GUI)

### BP3: User-Friendly Error Messaging

**Principle**: Constitution requires "user-friendly and actionable" error messages.

**Guidelines**:
1. **Specific**: Identify which part failed ("Part 3 of 5: part03.rar")
2. **Actionable**: Suggest what user can do ("Check internet connection", "Free disk space")
3. **Bilingual**: English and Arabic (match user base)
4. **No Technical Jargon**: Avoid "HTTP 404", "Connection timeout" → "Download link not found", "Network error"

**Examples**:

| Error Type | Technical (❌) | User-Friendly (✅) |
|------------|----------------|-------------------|
| Invalid URL | `HTTPError: 404 Not Found` | "الرابط غير صحيح أو الصفحة غير موجودة<br>Invalid URL or page not found" |
| Disk full | `OSError: [Errno 28] No space left` | "المساحة التخزينية غير كافية<br>Not enough disk space. Need 50GB, only 30GB available" |
| Network error | `ConnectionError: timeout` | "مشكلة في الاتصال بالإنترنت<br>Network error. Check your internet connection" |
| Part 3 failed | `Failed: part03.rar (attempt 3/3)` | "فشل تحميل الجزء 3 من 5<br>Failed to download part 3 of 5. You can retry later." |

---

## Dependencies & Installation

### New Dependencies to Add

```txt
beautifulsoup4==4.12.3
selenium==4.16.0
chromedriver-autoinstaller==0.6.4
```

### Installation Command

```bash
pip install beautifulsoup4==4.12.3 selenium==4.16.0 chromedriver-autoinstaller==0.6.4
```

### Platform-Specific Notes

**Windows**:
- ChromeDriver auto-installs to `%LOCALAPPDATA%\chromedriver-autoinstaller`
- No manual installation required
- Requires Google Chrome browser installed

**Linux/macOS**:
- ChromeDriver auto-installs to `/usr/local/bin/`
- Requires Chrome/Chromium browser installed

---

## Summary & Recommendations

### Technical Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| HTML Parsing | Selenium + headless Chrome | Reliable for Vue.js SPA |
| Resume Storage | JSON file in home directory | Simple, persistent, debuggable |
| Disk Space Check | shutil.disk_usage() | Standard library, cross-platform |
| Range Requests | requests library with Range header | Native support, fallback to re-download |
| GUI Threading | threading.Thread + window.after() | Industry standard for tkinter |

### Implementation Phases

**Phase 1 (MVP)**:
- Implement Selenium-based HTML parsing
- Add "Download Apps/Games" button and basic UI
- Implement sequential multi-part download
- Add progress tracking and completion summary

**Phase 2 (Resume & Reliability)**:
- Add resume support (skip completed parts)
- Implement HTTP range requests for incomplete files
- Add JSON checkpoint storage
- Implement disk space checking

**Phase 3 (Polish)**:
- Optimize Selenium startup time
- Add bilingual error messages
- Implement retry logic enhancements
- Add unit tests for core functions

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Vodu store structure changes | High (feature breaks) | Version checking, graceful fallback, monitor for changes |
| Selenium/ChromeDriver compatibility | Medium (install failures) | Auto-installer, version pinning, clear error messages |
| Large file corruption | Medium (wasted bandwidth) | MD5/SHA256 validation, resume support |
| GUI freezes during download | High (poor UX) | Threading, progress updates, disable buttons |

### Open Questions for Implementation

1. **Vodu Store API**: Does Vodu store expose a public API for download metadata? (Investigate during implementation)
2. **Rate Limiting**: Does Vodu store rate-limit download requests? (Monitor during testing)
3. **Session Management**: How long do download URLs remain valid? (Test expiration)

---

**Next Step**: Proceed to Phase 1 design artifacts (data-model.md, contracts/, quickstart.md)
