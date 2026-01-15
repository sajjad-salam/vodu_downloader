# API Contracts: Vodu Store Integration

**Feature**: 001-apps-games-download
**Date**: 2025-01-15
**Purpose**: Document external API contracts and data formats for Vodu store integration

## Overview

This document specifies the external contracts between Vodu Downloader and the Vodu store platform (https://share.vodu.store). Since Vodu store does not publish a public API, these contracts are based on reverse-engineering of the web interface and may change without notice.

## Contract 1: Vodu Store Page Structure

### Endpoint

**URL Pattern**: `https://share.vodu.store/#/details/[ID]`

**Example**: `https://share.vodu.store/#/details/214620`

**Method**: GET (via browser/Selenium)

### Response Format

**Content-Type**: `text/html`

**Initial HTML Response**:

```html
<!DOCTYPE html>
<html lang="ara" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>vodu-store</title>
  <link rel="icon" href="/favicon.ico">
  <link rel="stylesheet" href="/css/app.09c796dc.css">
  <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-app.js"></script>
  <script src="https://www.gstatic.com/firebasejs/8.10.0/firebase-messaging.js"></script>
  <link href="/css/chunk-vendors.3e9b4b9d.css" rel="preload" as="style">
  <link href="/css/app.09c796dc.css" rel="preload" as="style">
  <script src="/js/chunk-vendors.246fb097.js" rel="preload"></script>
  <script src="/js/app.aa83b892.js" rel="preload"></script>
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

**Key Characteristics**:
- Single-page application (Vue.js)
- Content rendered dynamically via JavaScript
- Initial HTML contains only `<div id="app"></div>` placeholder
- Download links NOT present in initial HTML (require JavaScript execution)

### Expected DOM Structure (After JavaScript Rendering)

**Selector**: `.download-button` or `[text="تحميل"]`

**Button Pattern**:

```html
<button class="download-button" onclick="downloadFile('https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar')">
  تحميل
</button>
<button class="download-button" onclick="downloadFile('https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part02.rar')">
  تحميل
</button>
<!-- ... more buttons ... -->
```

**Expected Elements**:
- Multiple buttons with text "تحميل" (Arabic for "Download")
- Each button contains a download URL in `onclick` attribute or `href` attribute
- URLs follow pattern: `https://share.vodu.store:9999/store-files/[filename]`

### Selenium Extraction Strategy

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_download_urls(vodu_store_url):
    """Extract all download URLs from Vodu store page."""
    # Setup Chrome driver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in background
    driver = webdriver.Chrome(options=options)

    try:
        # Navigate to URL
        driver.get(vodu_store_url)

        # Wait for download buttons to appear
        wait = WebDriverWait(driver, 30)
        download_buttons = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), 'تحميل')]"))
        )

        # Extract URLs from buttons
        urls = []
        for button in download_buttons:
            # Try onclick attribute first
            onclick = button.get_attribute('onclick')
            if onclick and 'http' in onclick:
                # Extract URL from onclick="downloadFile('URL')"
                url = onclick.split("'")[1]
                urls.append(url)
            else:
                # Try href attribute
                href = button.get_attribute('href')
                if href:
                    urls.append(href)

        return urls

    finally:
        driver.quit()
```

### Error Scenarios

| Scenario | Expected Behavior | HTTP Status |
|----------|-------------------|-------------|
| Valid URL | Returns HTML with Vue.js app | 200 OK |
| Invalid ID | Page loads but shows "not found" message | 200 OK (SPA handles errors) |
| Network error | Connection timeout/failure | N/A (network error) |
| Rate limiting | May block or throttle requests | 429 Too Many Requests (possible) |

---

## Contract 2: Download URL Format

### URL Pattern

**Format**: `https://share.vodu.store:9999/store-files/[filename]`

**Components**:
- **Protocol**: `https`
- **Host**: `share.vodu.store:9999` (port 9999)
- **Path**: `/store-files/[filename]`
- **Filename**: Derived from app/game name + part number

### Filename Patterns

**Pattern 1**: `{AppName}-v{Version}-{Tag}--part{DD}.{ext}`

**Examples**:
- `Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar`
- `Marvels-SpiderMan-2-v1-526--DODI-Repack--part02.rar`
- `Marvels-SpiderMan-2-v1-526--DODI-Repack--part03.rar`

**Pattern Breakdown**:
- `Marvels-SpiderMan-2`: App/game name
- `v1-526`: Version
- `DODI-Repack`: Tag/Release group
- `part01`: Part number (zero-padded to 2 digits)
- `rar`: File extension (archive format)

**Regex Pattern**:
```regex
^(.+)--part(\d+)\.(rar|zip|7z)$
```

**Extraction Groups**:
- Group 1: App name (with version and tags)
- Group 2: Part number (integer)
- Group 3: File extension

### Download Request

**Method**: GET

**Headers** (Standard):
```
Accept: */*
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...
```

**Headers** (Resume Support):
```
Range: bytes=1024-  # Resume from byte 1024
```

### Response Format

**Successful Response**:

**Status Codes**:
- `200 OK`: Full download (new download or server doesn't support ranges)
- `206 Partial Content`: Resume from specific byte position

**Headers**:
```
Content-Type: application/x-rar-compressed
Content-Length: 10737418240  # 10GB
Content-Disposition: attachment; filename="Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar"
Accept-Ranges: bytes  # Indicates range request support
```

**Headers** (Range Request Response):
```
Content-Range: bytes 1024-10737418239/10737418240  # bytes start-end/total
Content-Length: 10737418240
```

**Body**: Binary file content (streaming)

**Error Responses**:

| Status | Meaning | Action |
|--------|---------|--------|
| 404 Not Found | File not found on server | Report error: "Download link not available" |
| 403 Forbidden | Access denied (possible auth/session required) | Report error: "Access denied" |
| 410 Gone | File removed from server | Report error: "File no longer available" |
| 500+ | Server error | Retry with exponential backoff |

### Download Implementation

```python
import requests
import os

def download_part_with_resume(url, save_path, max_retries=3):
    """Download a single part with resume support."""
    retry_count = 0
    headers = {}

    # Check for existing file (resume)
    if os.path.exists(save_path):
        existing_size = os.path.getsize(save_path)
        headers['Range'] = f'bytes={existing_size}-'
        mode = 'ab'  # append binary
    else:
        mode = 'wb'  # write binary

    while retry_count < max_retries:
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=300)

            # Check response status
            if response.status_code in [200, 206]:
                # Successful download
                with open(save_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            elif response.status_code == 404:
                raise Exception(f"File not found: {url}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.reason}")

        except requests.exceptions.RequestException as e:
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(5)  # Wait before retry
            else:
                raise Exception(f"Failed after {max_retries} retries: {e}")
```

---

## Contract 3: HTTP Range Request Support

### Specification

**RFC**: [RFC 7233 - Range Requests](https://datatracker.ietf.org/doc/html/rfc7233)

### Request Headers

**Range Header**:
```
Range: bytes=<start>-<end>
```

**Examples**:
- `Range: bytes=0-` (download from byte 0 to end)
- `Range: bytes=1024-` (resume from byte 1024 to end)
- `Range: bytes=0-1023` (download first 1024 bytes)

### Response Headers

**Content-Range Header**:
```
Content-Range: bytes <start>-<end>/<total>
```

**Example**:
```
Content-Range: bytes 1024-2047/2048
```

**Accept-Ranges Header**:
```
Accept-Ranges: bytes  # Server supports range requests
Accept-Ranges: none   # Server does NOT support range requests
```

### Response Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 OK | Full content (server doesn't support ranges or no Range header sent) | Standard download |
| 206 Partial Content | Partial content (range request supported) | Resume download |
| 416 Range Not Satisfiable | Invalid range (e.g., start >= total size) | File already complete |

### Resume Logic Flow

```
1. Check if file exists locally
2. If exists:
   a. Get file size
   b. Send Range: bytes={file_size}-
   c. If 206 Partial Content: Append to file
   d. If 200 OK: Server doesn't support ranges, re-download
3. If not exists:
   a. Send normal GET request (no Range header)
   b. Write to file
```

### Validation

**After Download**:
```python
def validate_download(file_path, expected_size):
    """Validate downloaded file size matches expected."""
    actual_size = os.path.getsize(file_path)
    if actual_size != expected_size:
        raise Exception(f"File corrupted: Expected {expected_size} bytes, got {actual_size} bytes")
    return True
```

---

## Contract 4: Vodu Store API (Hypothetical)

### Note

This contract is **hypothetical** and based on common SPA patterns. The actual API endpoints, if they exist, must be discovered during implementation via browser developer tools (Network tab).

### Potential API Endpoints

**Get App/Game Details**:
```
GET /api/details/[ID]

Response:
{
  "id": "214620",
  "name": "Marvel's Spider-Man 2",
  "version": "v1-526",
  "tag": "DODI Repack",
  "parts": [
    {
      "filename": "Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar",
      "url": "https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar",
      "size": 10737418240
    },
    {
      "filename": "Marvels-SpiderMan-2-v1-526--DODI-Repack--part02.rar",
      "url": "https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part02.rar",
      "size": 10737418240
    }
  ]
}
```

### Implementation Strategy

**Phase 1**: Use Selenium (guaranteed to work)

**Phase 2** (Optimization): Investigate API endpoints via browser DevTools:
1. Open Vodu store URL in Chrome
2. Open DevTools → Network tab
3. Filter by XHR/Fetch requests
4. Look for API calls to `/api/*` or similar
5. If found, test API endpoints directly (lighter than Selenium)

**Fallback**: If API endpoints require authentication/tokens, stick with Selenium.

---

## Contract Stability & Versioning

### Stability Assessment

| Contract | Stability | Likelihood of Change | Mitigation |
|----------|-----------|---------------------|------------|
| Page Structure | Low | High (Vue.js app updates frequently) | Flexible selectors, graceful degradation |
| Download URL Format | Medium | Medium (URL structure is stable) | Regex patterns for flexibility |
| HTTP Range Requests | High | Low (standard HTTP protocol) | Standard library support |
| Vodu Store API | Unknown | Unknown (not documented) | Selenium fallback |

### Change Detection

**Monitoring Strategy**:
1. Log HTML structure changes (if download buttons not found)
2. Log URL pattern changes (if regex doesn't match)
3. User error reports: "Cannot find download buttons"
4. Automated testing with known URLs (e.g., ID 214620)

**Update Process**:
1. Investigate change (manual browser inspection)
2. Update selectors/patterns in code
3. Test with multiple Vodu store URLs
4. Release hotfix update

### Deprecation Policy

**No Official Deprecation**: Vodu store does not publish API documentation or changelog.

**Community Monitoring**: Monitor user reports and Vodu store website for changes.

**Backup Plan**: If Vodu store structure changes significantly, feature may break until updated selectors/patterns are implemented.

---

## Summary

**Key Contracts**:
1. **Vodu Store Page**: Vue.js SPA requiring JavaScript rendering (Selenium)
2. **Download URLs**: Pattern-based extraction from "تحميل" buttons
3. **HTTP Range Requests**: Standard resume support via `Range` header
4. **Vodu Store API**: Hypothetical, requires investigation

**Implementation Priority**:
1. Selenium-based parsing (guaranteed to work)
2. HTTP range request support (resume functionality)
3. API endpoint investigation (optimization, Phase 2)

**Risks**:
- Vodu store structure changes may break selectors
- No official API documentation
- Rate limiting or blocking possible

**Next Step**: Generate quickstart guide (quickstart.md)
