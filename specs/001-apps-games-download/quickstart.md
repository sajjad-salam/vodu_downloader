# Quickstart Guide: Apps and Games Download Support

**Feature**: 001-apps-games-download
**Date**: 2025-01-15
**Audience**: Developers implementing or testing the apps/games download feature

## Overview

This guide provides step-by-step instructions for setting up, testing, and validating the apps/games download functionality in Vodu Downloader.

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11 (primary), Linux/macOS (secondary)
- **Python**: 3.9 or higher (tested on 3.9.7)
- **Disk Space**: At least 50GB free for testing large game downloads
- **Browser**: Google Chrome (required for Selenium/ChromeDriver)
- **Internet**: Stable connection for downloading (5-10GB per part)

### Python Dependencies

Install required packages:

```bash
# Navigate to project directory
cd vodu_downloader

# Install existing dependencies
pip install -r requirements.txt

# Install new dependencies for apps/games feature
pip install beautifulsoup4==4.12.3
pip install selenium==4.16.0
pip install chromedriver-autoinstaller==0.6.4
```

**Verify Installation**:
```bash
python -c "import bs4, selenium; print('Dependencies OK')"
```

Expected output: `Dependencies OK`

---

## Setup Instructions

### 1. Update requirements.txt

Add new dependencies to `requirements.txt`:

```txt
requests
urllib3
tqdm
beautifulsoup4==4.12.3
selenium==4.16.0
chromedriver-autoinstaller==0.6.4
```

### 2. Verify Chrome Installation

Ensure Google Chrome is installed:

**Windows**:
- Check: `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Or: `C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`

**Linux**:
```bash
which google-chrome
# or
which chromium
```

**Download Chrome** (if not installed): https://www.google.com/chrome/

### 3. Test Selenium Setup

Create test script `test_selenium.py`:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

# Auto-install ChromeDriver
chromedriver_autoinstaller.install()

# Setup headless Chrome
options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

try:
    # Test with Vodu store
    driver.get("https://share.vodu.store/#/details/214620")

    # Wait for page load
    wait = WebDriverWait(driver, 30)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Selenium setup successful!")
    print(f"Page title: {driver.title}")

finally:
    driver.quit()
```

Run test:
```bash
python test_selenium.py
```

Expected output:
```
Selenium setup successful!
Page title: vodu-store
```

---

## Development Workflow

### 1. Implement Core Functions

Add these functions to `main.py`:

**Function 1: Parse Vodu Store Page**
```python
def parse_vodu_store_page(vodu_store_url):
    """Extract download URLs from Vodu store page."""
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import chromedriver_autoinstaller

    # Auto-install ChromeDriver
    chromedriver_autoinstaller.install()

    # Setup Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(vodu_store_url)

        # Wait for download buttons
        wait = WebDriverWait(driver, 30)
        buttons = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//*[contains(text(), 'تحميل')]"))
        )

        # Extract URLs
        urls = []
        for btn in buttons:
            onclick = btn.get_attribute('onclick')
            if onclick and 'http' in onclick:
                url = onclick.split("'")[1]
                urls.append(url)

        return urls

    finally:
        driver.quit()
```

**Function 2: Download Part with Resume**
```python
def download_part_with_resume(url, save_path, progress_callback):
    """Download a single part with resume support."""
    import requests
    import os

    headers = {}
    mode = 'wb'

    # Check for resume
    if os.path.exists(save_path):
        existing_size = os.path.getsize(save_path)
        headers['Range'] = f'bytes={existing_size}-'
        mode = 'ab'

    # Download
    response = requests.get(url, headers=headers, stream=True)

    with open(save_path, mode) as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            progress_callback(len(chunk))

    return True
```

### 2. Add GUI Elements

Add "Download Apps/Games" button to `main.py`:

```python
# Create button
apps_games_button = Button(
    window,
    text="Download Apps/Games\nتحميل التطبيقات والألعاب",
    command=start_download_apps_games,
    bg="#404040",
    fg="#FFFFFF",
    font=("Roboto Medium", 12)
)

# Position button (below existing buttons)
apps_games_button.place(x=18.0, y=550.0, width=414.0, height=47.0)
```

Add download handler function:
```python
def start_download_apps_games():
    """Handle apps/games download button click."""
    url = text_widget.get("1.0", tk.END).strip()

    if not url:
        messagebox.showinfo("Info", "Please enter a Vodu store URL.")
        return

    # Select download location
    download_path = filedialog.askdirectory(title="Choose Download Path")
    if not download_path:
        return

    # Parse page and start download
    try:
        urls = parse_vodu_store_page(url)

        if not urls:
            messagebox.showinfo("Info", "No download links found.")
            return

        # Download in background thread
        threading.Thread(
            target=download_all_parts,
            args=(urls, download_path)
        ).start()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to parse page: {e}")
```

### 3. Run Application

```bash
python main.py
```

---

## Testing Guide

### Test Case 1: Basic Multi-Part Download

**Objective**: Verify successful download of all parts

**Steps**:
1. Launch Vodu Downloader
2. Enter URL: `https://share.vodu.store/#/details/214620`
3. Click "Download Apps/Games"
4. Select download location
5. Monitor progress bar

**Expected Results**:
- Progress bar shows "Part 1 of 5", "Part 2 of 5", etc.
- All parts downloaded to selected location
- Completion message shows: "Downloaded 5 files (50GB) to [location]"

**Validation**:
```bash
# Check files exist
ls -lh /path/to/download/location/*.rar

# Expected output:
# -rw-r--r-- 1 user group 10G Jan 15 10:35 Marvels-SpiderMan-2--part01.rar
# -rw-r--r-- 1 user group 10G Jan 15 10:40 Marvels-SpiderMan-2--part02.rar
# ...
```

### Test Case 2: Resume After Interruption

**Objective**: Verify resume functionality skips completed parts

**Steps**:
1. Start download as in Test Case 1
2. After 2 parts complete, interrupt download:
   - Option A: Close application (kill process)
   - Option B: Disconnect internet
3. Restart application
4. Re-enter same URL: `https://share.vodu.store/#/details/214620`
5. Select same download location
6. Click "Download Apps/Games"

**Expected Results**:
- Application detects parts 1 and 2 already downloaded
- Skips to part 3 (shows "Skipping part 1", "Skipping part 2")
- Downloads parts 3, 4, 5
- Completion message: "Resumed: Downloaded 3 new files, skipped 2 existing files"

**Validation**:
```bash
# Check no duplicate files
ls -lh /path/to/download/location/*.rar | wc -l
# Expected: 5 files (not 10)
```

### Test Case 3: Retry Logic

**Objective**: Verify automatic retry on network failure

**Steps**:
1. Start download
2. Simulate network failure:
   - Disconnect internet during part 3 download
   - Wait 10 seconds
   - Reconnect internet
3. Monitor logs/progress

**Expected Results**:
- Download pauses with "Network error" message
- Application waits 5 seconds
- Automatically retries part 3
- Continues to part 4 after retry succeeds
- Console shows: "Retrying part 3... Attempt 2"

### Test Case 4: Error Handling

**Objective**: Verify clear error messages for failure scenarios

**Test Scenarios**:

| Scenario | Input | Expected Message |
|----------|-------|------------------|
| Invalid URL | `https://example.com` | "Invalid Vodu store URL" |
| Page not found | `https://share.vodu.store/#/details/999999` | "Page not found or no download links" |
| Disk full | (simulate) | "Not enough disk space. Need 50GB, only 5GB available" |
| Permission denied | (protected folder) | "Permission denied. Choose a different location" |

### Test Case 5: Large File Handling

**Objective**: Verify performance with large files (10GB per part)

**Steps**:
1. Download a 5-part game (50GB total)
2. Monitor:
   - Memory usage (should remain stable, not grow)
   - Progress updates (should refresh ≥2x/second)
   - GUI responsiveness (should not freeze)

**Expected Results**:
- Memory usage: <500MB (streaming download)
- Progress updates: Every 0.5 seconds
- GUI remains responsive (can move window, click buttons)

---

## Debugging Tips

### Enable Verbose Logging

Add to `main.py`:
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='vodu_downloader.log'
)
```

View logs:
```bash
tail -f vodu_downloader.log
```

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| ChromeDriver not found | Chrome not installed or wrong version | Install Google Chrome |
| Timeout waiting for buttons | Slow internet or page structure changed | Increase timeout in WebDriverWait |
| "No download links found" | Button selector incorrect | Inspect page HTML with browser DevTools |
| Resume not working | Server doesn't support range requests | Re-download entire file (document in logs) |
| GUI freezes | Download running in main thread | Ensure threading.Thread() is used |

### Inspect Vodu Store Page Structure

1. Open URL in Chrome: `https://share.vodu.store/#/details/214620`
2. Press F12 (DevTools)
3. Click Elements tab
4. Search for "تحميل" (Ctrl+F)
5. Verify button structure matches expectations

**Example**:
```html
<button class="btn-download" onclick="download('https://share.vodu.store:9999/store-files/file.rar')">
  تحميل
</button>
```

### Test Selenium Selectors

Create test script:
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://share.vodu.store/#/details/214620")

# Try different selectors
selectors = [
    "//*[contains(text(), 'تحميل')]",
    "//button[contains(text(), 'تحميل')]",
    ".download-button",
]

for selector in selectors:
    try:
        elements = driver.find_elements(By.XPATH, selector)
        print(f"Selector '{selector}' found {len(elements)} elements")
    except Exception as e:
        print(f"Selector '{selector}' failed: {e}")

driver.quit()
```

---

## Performance Benchmarks

### Expected Performance

| Metric | Target | Acceptable |
|--------|--------|------------|
| Page parsing time | <10 seconds | <30 seconds |
| Download speed | Network limit | Network limit |
| Resume check time | <2 seconds | <5 seconds |
| Memory usage | <500MB | <1GB |
| Progress update rate | ≥2x/second | ≥1x/second |

### Benchmark Test

```python
import time

def benchmark_page_parsing():
    start = time.time()
    urls = parse_vodu_store_page("https://share.vodu.store/#/details/214620")
    elapsed = time.time() - start

    print(f"Parsed {len(urls)} URLs in {elapsed:.2f} seconds")
    assert elapsed < 30, "Parsing too slow!"
```

---

## Sample URLs for Testing

### Valid Vodu Store URLs

- **Test URL 1**: `https://share.vodu.store/#/details/214620` (Marvel's Spider-Man 2)
- **Test URL 2**: `https://share.vodu.store/#/details/214621` (example game)
- **Test URL 3**: `https://share.vodu.store/#/details/214622` (example app)

**Note**: Use real URLs from Vodu store for testing. These examples may not be active.

### Invalid URLs for Error Testing

- `https://example.com` (wrong domain)
- `https://share.vodu.store/#/details/999999` (non-existent ID)
- `https://share.vodu.store/invalid` (malformed URL)

---

## Validation Checklist

Before marking feature complete, verify:

- [ ] Can parse Vodu store URLs and extract download links
- [ ] Can download all parts of a multi-part game
- [ ] Progress bar shows current part and overall progress
- [ ] Resume works after app restart (skips completed parts)
- [ ] Resume works for incomplete files (continues from last byte)
- [ ] Retry logic works (3 attempts with 5-second delays)
- [ ] Error messages are clear and bilingual (English/Arabic)
- [ ] Disk space check works (blocks download if insufficient space)
- [ ] GUI remains responsive during download
- [ ] Completion summary shows correct file count and total size

---

## Next Steps

After completing development:

1. **Manual Testing**: Follow test cases in this guide
2. **Edge Case Testing**: Test with 10+ parts, very large files (20GB per part)
3. **User Acceptance Testing**: Have a non-technical user test the feature
4. **Documentation Update**: Update README.md with apps/games download instructions
5. **Release**: Create pull request with feature branch

---

## Support & Troubleshooting

### Getting Help

- Check logs: `vodu_downloader.log`
- Review error messages in GUI
- Test Selenium setup with `test_selenium.py`
- Inspect Vodu store page structure with browser DevTools

### Reporting Issues

When reporting bugs, include:
1. Vodu store URL used
2. Error message (screenshot or text)
3. Log file excerpt
4. Steps to reproduce
5. System information (OS, Python version, Chrome version)

---

**End of Quickstart Guide**

For implementation details, see:
- [Data Model](data-model.md)
- [API Contracts](contracts/vodu-store-api.md)
- [Research Document](research.md)
- [Implementation Plan](plan.md)
