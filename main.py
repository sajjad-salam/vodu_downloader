import threading
import shutil
from enum import Enum
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass
import re
import os
import json
import tkinter
import requests
from tqdm import tqdm
import time
import sys
from urllib3.exceptions import IncompleteRead
import tkinter as tk
import tkinter
from tkinter import Tk, Canvas,  Button, PhotoImage, filedialog, ttk,  messagebox
from tkinter import Tk, scrolledtext,  messagebox, ttk, filedialog
import urllib.request
from urllib.parse import urlparse
import webbrowser

# Selenium imports for JavaScript rendering
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

# Global variables for video quality and season selection (will be initialized after window creation)
selected_quality = None
selected_season = None

# ============================================================================
# Apps and Games Download - Data Classes and Enums
# ============================================================================


class PartStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class SessionStatus(Enum):
    INITIALIZED = "initialized"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadPart:
    part_number: int
    filename: str
    download_url: str
    expected_size: int
    downloaded_size: int = 0
    status: PartStatus = PartStatus.PENDING
    retry_count: int = 0
    local_path: Optional[str] = None
    last_attempt_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def is_complete(self) -> bool:
        return self.status in [PartStatus.COMPLETED, PartStatus.SKIPPED]

    def is_resumable(self) -> bool:
        return self.downloaded_size > 0 and self.downloaded_size < self.expected_size


@dataclass
class DownloadSession:
    session_id: str
    vodu_store_url: str
    download_location: str
    app_name: str
    parts: List[DownloadPart]
    total_parts: int
    completed_parts: int = 0
    overall_progress: float = 0.0
    total_downloaded_bytes: int = 0
    total_expected_bytes: int = 0
    status: SessionStatus = SessionStatus.INITIALIZED
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def calculate_progress(self) -> float:
        if self.total_expected_bytes == 0:
            return 0.0
        self.total_downloaded_bytes = sum(
            p.downloaded_size for p in self.parts)
        self.overall_progress = (
            self.total_downloaded_bytes / self.total_expected_bytes) * 100
        return self.overall_progress

    def get_next_pending_part(self) -> Optional[DownloadPart]:
        for part in self.parts:
            if part.status in [PartStatus.PENDING, PartStatus.FAILED]:
                return part
        return None

    def mark_part_completed(self, part: DownloadPart):
        part.status = PartStatus.COMPLETED
        part.completed_at = datetime.now()
        self.completed_parts += 1
        self.calculate_progress()


# ============================================================================
# Apps and Games Download - Foundational Functions
# ============================================================================

def check_disk_space(path, required_bytes):
    """Check if sufficient disk space available."""
    try:
        usage = shutil.disk_usage(path)
        available = usage.free
        return available >= required_bytes
    except OSError as e:
        print(f"Warning: Cannot check disk space: {e}")
        return True  # Allow download to proceed


def get_resume_state_path():
    """Get the path to the resume state JSON file."""
    home_dir = os.path.expanduser("~")
    vodu_dir = os.path.join(home_dir, ".vodu_downloader")
    os.makedirs(vodu_dir, exist_ok=True)
    return os.path.join(vodu_dir, "resume_state.json")


def load_resume_state():
    """Load download sessions from JSON file."""
    json_path = get_resume_state_path()
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data.get('sessions', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_resume_state(sessions):
    """Save download sessions to JSON file (atomic write)."""
    json_path = get_resume_state_path()
    data = {
        'version': '1.0',
        'sessions': sessions
    }
    temp_path = json_path + '.tmp'
    with open(temp_path, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, json_path)


def check_existing_part(file_path, expected_size):
    """Check if part already exists and matches expected size."""
    if os.path.exists(file_path):
        actual_size = os.path.getsize(file_path)
        return actual_size == expected_size
    return False

# ============================================================================
# Apps and Games Download - Core Functions
# ============================================================================


def extract_download_links(html_content):
    """
    Extract download URLs from Vodu store HTML content.
    Looks for links matching pattern: https://share.vodu.store:9999/store-files/[filename]
    Enhanced with edge case handling and JavaScript-rendered content detection.
    """
    if not html_content:
        print("Warning: Empty HTML content provided")
        return []

    # First, try to find URLs directly in HTML
    url_pattern = r'https://share\.vodu\.store:9999/store-files/[^\s"\'<>]+'

    try:
        download_urls = re.findall(url_pattern, html_content)
    except re.error as e:
        print(f"Regex error: {e}")
        return []

    # If no URLs found, try to extract from embedded JSON data (Vue.js pattern)
    if not download_urls:
        # Look for JSON data in script tags (common Vue.js pattern)
        json_pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        json_match = re.search(json_pattern, html_content, re.DOTALL)

        if json_match:
            try:
                import json as json_module
                data = json_module.loads(json_match.group(1))
                # Extract URLs from the JSON data
                # This is a common pattern where Vue apps embed initial state
                json_str = str(data)
                download_urls = re.findall(url_pattern, json_str)
                print(f"Found {len(download_urls)} URLs in embedded JSON data")
            except:
                pass

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in download_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Edge case: No download links found
    if not unique_urls:
        print("=" * 60)
        print("WARNING: No download links found!")
        print("=" * 60)
        print("This Vodu store page uses JavaScript to load content.")
        print("The download links appear after the page loads in a browser.")
        print("")
        print("Possible solutions:")
        print("1. Open the URL in your browser, then copy the download links manually")
        print("2. Check if the page has a different format than expected")
        print("3. The URL might be invalid or the page doesn't exist")
        print("=" * 60)

        # Check if it's a Vue.js SPA
        if 'vue' in html_content.lower() or '<div id="app">' in html_content:
            print("DETECTED: This is a Vue.js Single Page Application")
            print("The content requires JavaScript rendering to display download links.")
            print("=" * 60)
            print("")
            print("WORKAROUND: Try opening the page in your browser and check")
            print("the Network tab in Developer Tools (F12) for API requests.")
            print("Look for requests that return download URLs in JSON format.")
            print("=" * 60)

    return unique_urls


def get_file_info_api(app_id):
    """
    Call the /api/v1/file/{app_id} endpoint to get file list,
    then call /api/v1/download/no-recaptcha/{file_id} for each file.
    This is the 2-step process discovered through API analysis.
    """
    api_url = f"https://share.vodu.store/api/v1/file/{app_id}"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://share.vodu.store/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    cookies = {
        "G_ENABLED_IDPS": "google"
    }

    try:
        print(f"[INFO] Step 1: Fetching file list from API: {api_url}")
        response = requests.get(api_url, headers=headers,
                                cookies=cookies, timeout=30)

        if response.status_code != 200:
            print(f"[X] API returned status {response.status_code}")
            if response.status_code == 404:
                print("  -> App/Game ID not found (404)")
            return None

        print(f"[OK] API returned 200 OK")
        data = response.json()

        # Check if objectFiles exists
        if 'objectFiles' not in data:
            print("[X] No 'objectFiles' found in API response")
            print(f"Available keys: {list(data.keys())}")
            return None

        object_files = data['objectFiles']
        if not object_files:
            print("[X] objectFiles array is empty")
            return None

        print(f"[OK] Found {len(object_files)} files")
        for i, file_info in enumerate(object_files, 1):
            print(
                f"  {i}. {file_info.get('name', 'Unknown')} (ID: {file_info.get('id')}, Size: {file_info.get('size')} bytes)")

        # Step 2: Get download URL for each file
        print(
            f"\n[INFO] Step 2: Fetching download URLs for {len(object_files)} files...")
        download_urls = []

        for i, file_info in enumerate(object_files, 1):
            file_id = file_info.get('id')
            file_name = file_info.get('name')

            print(
                f"[{i}/{len(object_files)}] Fetching download URL for: {file_name}")

            # Call the download API with file ID
            download_url = get_download_url_for_file(file_id)

            if download_url:
                download_urls.append(download_url)
                print(f"  [OK] Got URL: {os.path.basename(download_url)}")
            else:
                print(
                    f"  [X] Failed to get download URL for file ID {file_id}")

        print()
        if download_urls:
            print(f"[SUCCESS] Found {len(download_urls)} download URL(s)!")
            return download_urls
        else:
            print("[X] No download URLs retrieved")
            return None

    except Exception as e:
        print(f"[X] API request failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_download_url_for_file(file_id):
    """
    Call /api/v1/download/no-recaptcha/{file_id} to get download URL for a specific file.
    """
    api_url = f"https://share.vodu.store/api/v1/download/no-recaptcha/{file_id}"

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://share.vodu.store/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    cookies = {
        "G_ENABLED_IDPS": "google"
    }

    try:
        response = requests.get(api_url, headers=headers,
                                cookies=cookies, timeout=30)

        if response.status_code == 200:
            data = response.json()

            # Check for the "messge" key (typo in the API)
            if "messge" in data:
                message_value = data["messge"]
                if isinstance(message_value, str) and 'share.vodu.store:9999' in message_value:
                    return message_value

        return None

    except Exception as e:
        print(f"  [X] Error fetching download URL: {e}")
        return None


def try_api_endpoint(url):
    """
    Try to fetch download data from API endpoint.
    Uses the discovered Vodu store API pattern.
    """
    # Extract ID from URL: https://share.vodu.store/#/details/218974
    id_match = re.search(r'/details/(\d+)', url)
    if not id_match:
        return None

    app_id = id_match.group(1)

    # First try the new /api/v1/file/{id} endpoint
    print(f"\nTrying /api/v1/file/ endpoint for ID: {app_id}")
    result = get_file_info_api(app_id)
    if result:
        return result

    # Fallback to the old endpoint pattern
    print(f"\nTrying fallback API endpoint for ID: {app_id}")

    # Use the discovered API pattern
    api_url = f"https://share.vodu.store/api/v1/download/no-recaptcha/{app_id}"

    # Set up headers similar to the browser request
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Authorization": "Bearer null",
        "Referer": "https://share.vodu.store/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0"
    }

    # Set up cookies
    cookies = {
        "G_ENABLED_IDPS": "google"
    }

    try:
        print(f"Requesting: {api_url}")
        response = requests.get(api_url, headers=headers,
                                cookies=cookies, timeout=30)

        if response.status_code == 200:
            print(f"[OK] SUCCESS: API returned 200 OK")

            try:
                data = response.json()

                # The API response structure based on actual API behavior
                download_urls = []

                if isinstance(data, dict):
                    # FIRST: Check for the actual API response key "messge" (note: typo in API)
                    # API returns: {"messge": "url"}
                    if "messge" in data:
                        message_value = data["messge"]
                        # The value can be a single URL string or potentially a list/object
                        if isinstance(message_value, str):
                            # Check if it's a download URL
                            if 'share.vodu.store:9999/store-files/' in message_value:
                                download_urls.append(message_value)
                                print(
                                    f"[OK] Found download URL in 'messge' field")
                        elif isinstance(message_value, list):
                            # If it's a list, extract URLs from each item
                            for item in message_value:
                                item_str = str(item)
                                urls = re.findall(
                                    r'https://share\.vodu\.store:9999/store-files/[^\s"\'<>]+', item_str)
                                download_urls.extend(urls)

                    # SECOND: Try other common keys if "messge" didn't work
                    if not download_urls:
                        possible_keys = ['files', 'downloads', 'links', 'parts',
                                         'data', 'downloadUrls', 'download_links', 'url', 'message']

                        for key in possible_keys:
                            if key in data:
                                items = data[key]
                                if isinstance(items, list):
                                    for item in items:
                                        item_str = str(item)
                                        urls = re.findall(
                                            r'https://share\.vodu\.store:9999/store-files/[^\s"\'<>]+', item_str)
                                        download_urls.extend(urls)
                                elif isinstance(items, dict):
                                    for v in items.values():
                                        if isinstance(v, str) and 'share.vodu.store:9999' in v:
                                            download_urls.append(v)
                                elif isinstance(items, str) and 'share.vodu.store:9999' in items:
                                    download_urls.append(items)

                # If still no URLs, try searching the entire JSON response as fallback
                if not download_urls:
                    data_str = str(data)
                    download_urls = re.findall(
                        r'https://share\.vodu\.store:9999/store-files/[^\s"\'<>]+', data_str)

                # Remove duplicates
                seen = set()
                unique_urls = []
                for url in download_urls:
                    if url not in seen:
                        seen.add(url)
                        unique_urls.append(url)

                if unique_urls:
                    print(
                        f"[OK] Found {len(unique_urls)} download URLs via API!")
                    for i, url in enumerate(unique_urls, 1):
                        filename = os.path.basename(url)
                        print(f"  {i}. {filename}")
                    return unique_urls
                else:
                    print("[X] API returned data but no download URLs found")
                    print(
                        f"Response structure: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            except json.JSONDecodeError as e:
                print(f"[X] Failed to parse JSON response: {e}")
                print(f"Response (first 500 chars): {response.text[:500]}")
        else:
            print(f"[X] API returned status {response.status_code}")
            if response.status_code == 404:
                print("  -> App/Game ID not found (404)")
            elif response.status_code == 403:
                print("  -> Access forbidden (403)")
            print(f"Response (first 200 chars): {response.text[:200]}")

    except Exception as e:
        print(f"[X] API request failed: {e}")

    print("No download URLs found via API endpoint.")
    return None


def download_part_with_resume(url, save_path, progress_callback=None):
    """Download a single part with streaming support."""
    headers = {}
    mode = 'wb'

    # Check for resume
    if os.path.exists(save_path):
        existing_size = os.path.getsize(save_path)
        headers['Range'] = f'bytes={existing_size}-'
        mode = 'ab'

    # Use session with connection pooling for better performance
    session = requests.Session()
    session.headers.update({
        'Connection': 'keep-alive',
        'Accept-Encoding': 'identity'  # Disable compression to reduce CPU usage
    })

    try:
        response = session.get(url, headers=headers, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        if mode == 'ab':
            # For resume, total_size is the remaining content
            total_size = existing_size + total_size

        downloaded_size = os.path.getsize(save_path) if mode == 'ab' else 0

        # Use larger chunk size for better performance (1MB chunks instead of 8KB)
        chunk_size = 1024 * 1024  # 1 MB chunks for faster downloads

        with open(save_path, mode) as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    if progress_callback:
                        progress_callback(
                            len(chunk), downloaded_size, total_size)

        return True

    except requests.exceptions.RequestException as e:
        print(f"Download failed for {url}: {e}")
        return False
    finally:
        session.close()  # Clean up session


def validate_file_integrity(file_path, expected_size):
    """
    Validate that downloaded file matches expected size.
    Returns True if valid, False otherwise.
    """
    if not os.path.exists(file_path):
        return False

    actual_size = os.path.getsize(file_path)

    if expected_size > 0 and actual_size != expected_size:
        print(f"File integrity check failed: {file_path}")
        print(f"Expected: {expected_size} bytes, Got: {actual_size} bytes")
        return False

    return True


def download_apps_games_worker(vodu_store_url, download_path, progress_bar, progress_label, time_remaining_label, window):
    """
    Worker function to download apps/games (runs in background thread).
    Enhanced with resume support, retry logic, and API-first approach.
    """
    try:
        # FIRST: Try the direct API endpoint (fastest)
        print("\n" + "=" * 60)
        print("Fetching download links from API...")
        print("=" * 60 + "\n")

        download_urls = try_api_endpoint(vodu_store_url)

        # SECOND: If API fails, use Selenium with network interception
        if not download_urls:
            print("\n" + "=" * 60)
            print("API failed, trying Selenium with network interception...")
            print("=" * 60 + "\n")

            download_urls = get_vodu_download_links_with_selenium(
                vodu_store_url)

        if not download_urls:
            messagebox.showinfo("Info",
                                "No download links found.\n\n"
                                "This could mean:\n"
                                "1. The App/Game ID doesn't exist in Vodu store\n"
                                "2. The page has no downloadable files\n"
                                "3. The page structure has changed\n\n"
                                "Please verify:\n"
                                "- The URL is correct\n"
                                "- The page has download buttons when opened in browser")
            return

        total_parts = len(download_urls)
        total_size = 0
        completed_parts = 0
        failed_parts = []

        # Track overall download statistics for ETA calculation
        overall_start_time = time.time()
        total_downloaded_bytes = 0  # Bytes downloaded across all parts

        # Get expected sizes for all parts
        part_sizes = {}
        for url in download_urls:
            try:
                response = requests.head(url, timeout=30)
                size = int(response.headers.get("content-length", 0))
                total_size += size
                filename = os.path.basename(url)
                part_sizes[filename] = size
            except:
                part_sizes[os.path.basename(url)] = 0

        # Check disk space
        if total_size > 0 and not check_disk_space(download_path, total_size):
            messagebox.showerror(
                "Error", f"Not enough disk space. Need {total_size / (1024**3):.2f}GB")
            return

        # Download each part sequentially with resume and retry support
        for i, url in enumerate(download_urls, 1):
            filename = os.path.basename(url)
            save_path = os.path.join(download_path, filename)
            expected_size = part_sizes.get(filename, 0)

            # Check if part already exists and is complete (Resume functionality)
            if expected_size > 0 and check_existing_part(save_path, expected_size):
                # Terminal output
                print(f"\n{'='*70}")
                print(f"✓ SKIPPING: Part {i}/{total_parts}")
                print(f"  File: {filename}")
                print(f"  Reason: Already downloaded (size matches)")
                print(f"{'='*70}")

                # GUI output
                progress_label.config(
                    text=f"✓ Skipping: Part {i}/{total_parts} - {filename}\n(already downloaded)")
                window.update_idletasks()
                completed_parts += 1
                total_downloaded_bytes += expected_size  # Track completed part bytes
                # Update progress bar for skipped part
                overall_progress = (completed_parts / total_parts) * 100
                progress_bar["value"] = overall_progress

                # Update colorful progress bar
                if hasattr(window, 'progress_canvas'):
                    update_colorful_progress_bar(
                        window.progress_canvas, overall_progress)

                window.update_idletasks()
                continue

            # Track download statistics for this file
            part_start_time = time.time()
            part_downloaded_bytes = 0
            last_print_time = time.time()
            last_print_bytes = 0

            # Download with retry logic (up to 3 attempts)
            success = False
            for attempt in range(3):
                if attempt > 0:
                    # Terminal output
                    print(f"\n⚠ RETRYING: Part {i}/{total_parts} - {filename}")
                    print(f"  Attempt {attempt + 1}/3...")

                    # GUI output
                    progress_label.config(
                        text=f"⚠ Retrying: Part {i}/{total_parts} - {filename}\nAttempt {attempt + 1}/3...")
                    window.update_idletasks()
                    time.sleep(5)  # Wait 5 seconds before retry
                else:
                    # Terminal output
                    print(f"\n{'='*70}")
                    print(f"⬇ DOWNLOADING: Part {i}/{total_parts}")
                    print(f"  File: {filename}")
                    if expected_size > 0:
                        size_mb = expected_size / (1024 * 1024)
                        print(f"  Size: {size_mb:.1f} MB")
                    print(f"{'='*70}")

                    # GUI output
                    progress_label.config(
                        text=f"⬇ Downloading: Part {i}/{total_parts} - {filename}\nStarting...")
                    window.update_idletasks()

                # Progress callback with detailed stats
                def update_progress(chunk_bytes, downloaded, total):
                    nonlocal part_downloaded_bytes, last_print_time, last_print_bytes
                    part_downloaded_bytes = downloaded

                    if total > 0:
                        # Calculate progress percentages
                        part_progress = (downloaded / total) * 100

                        # Calculate overall downloaded bytes (completed parts + current part)
                        current_total_downloaded = total_downloaded_bytes + downloaded
                        overall_progress = (current_total_downloaded / total_size * 100) if total_size > 0 else (
                            (completed_parts) / total_parts * 100) + (part_progress / total_parts)

                        # Calculate download speed
                        elapsed_time = time.time() - part_start_time
                        if elapsed_time > 0:
                            speed = downloaded / elapsed_time  # bytes per second
                            speed_mb = speed / (1024 * 1024)  # MB/s
                        else:
                            speed_mb = 0

                        # Calculate ETA for current part
                        if speed > 0 and downloaded < total:
                            remaining_bytes = total - downloaded
                            eta_seconds = remaining_bytes / speed
                            eta_minutes = int(eta_seconds / 60)
                            eta_secs = int(eta_seconds % 60)
                            eta_str = f"{eta_minutes}:{eta_secs:02d}"
                        else:
                            eta_str = "Calculating..."

                        # Calculate overall ETA
                        overall_elapsed = time.time() - overall_start_time
                        if overall_elapsed > 0 and current_total_downloaded > 0 and total_size > 0:
                            overall_speed = current_total_downloaded / overall_elapsed
                            remaining_total = total_size - current_total_downloaded
                            overall_eta_seconds = remaining_total / overall_speed
                            overall_eta_minutes = int(overall_eta_seconds / 60)
                            overall_eta_secs = int(overall_eta_seconds % 60)
                            overall_eta_str = f"{overall_eta_minutes}:{overall_eta_secs:02d}"
                        else:
                            overall_eta_str = "Calculating..."

                        # Format sizes
                        downloaded_mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)

                        # Print to terminal every 2 seconds (to avoid spam)
                        current_time = time.time()
                        if current_time - last_print_time >= 2.0:
                            # Calculate current speed
                            time_diff = current_time - last_print_time
                            bytes_diff = downloaded - last_print_bytes
                            current_speed = (
                                bytes_diff / time_diff / (1024 * 1024)) if time_diff > 0 else speed_mb

                            # Terminal output (update in-place with \r)
                            print(f"\r  Progress: {part_progress:5.1f}% | {downloaded_mb:7.1f} MB / {total_mb:.1f} MB | "
                                  f"Speed: {current_speed:6.1f} MB/s | ETA: {eta_str} | Overall: {overall_progress:5.1f}% | Overall ETA: {overall_eta_str}", end='', flush=True)

                            last_print_time = current_time
                            last_print_bytes = downloaded

                        # Update progress bar and label in GUI
                        progress_bar["value"] = overall_progress

                        # Update the colorful custom progress bar
                        if hasattr(window, 'progress_canvas'):
                            update_colorful_progress_bar(
                                window.progress_canvas, overall_progress)

                        # Detailed progress message for GUI
                        progress_text = (
                            f"⬇ Part {i}/{total_parts}: {filename}\n"
                            f"{part_progress:.1f}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)\n"
                            f"Speed: {speed_mb:.1f} MB/s | ETA: {eta_str}\n"
                            f"Overall: {overall_progress:.1f}% | Overall ETA: {overall_eta_str}"
                        )
                        progress_label.config(text=progress_text)
                        window.update_idletasks()

                success = download_part_with_resume(
                    url, save_path, update_progress)
                if success:
                    break

            if success:
                completed_parts += 1
                # Track total bytes for overall ETA
                total_downloaded_bytes += part_downloaded_bytes

                # Show completion of this file
                part_size_mb = part_downloaded_bytes / (1024 * 1024)
                elapsed_time = time.time() - part_start_time
                avg_speed = part_downloaded_bytes / elapsed_time / \
                    (1024 * 1024) if elapsed_time > 0 else 0

                # Terminal output
                print(f"\n✓ COMPLETED: Part {i}/{total_parts} - {filename}")
                print(f"  Size: {part_size_mb:.1f} MB")
                print(
                    f"  Time: {int(elapsed_time // 60)}:{int(elapsed_time % 60):02d}")
                print(f"  Avg Speed: {avg_speed:.1f} MB/s")
                print(
                    f"  Overall Progress: {(completed_parts / total_parts) * 100:.1f}% ({completed_parts}/{total_parts} files)")
                print(f"{'='*70}")

                # GUI output
                progress_label.config(
                    text=f"✓ Completed: Part {i}/{total_parts} - {filename}\n"
                    f"Size: {part_size_mb:.1f} MB | Avg Speed: {avg_speed:.1f} MB/s\n"
                    f"Overall: {(completed_parts / total_parts) * 100:.1f}% ({completed_parts}/{total_parts} files)"
                )
                window.update_idletasks()
            else:
                failed_parts.append((i, filename))
                # Log error but continue with next part
                print(f"\n✗ FAILED: Part {i} - {filename} after 3 attempts")

        # Update progress bar to final state
        final_progress = 100 if not failed_parts else (
            completed_parts / total_parts) * 100
        progress_bar["value"] = final_progress

        # Update colorful progress bar to final state
        if hasattr(window, 'progress_canvas'):
            update_colorful_progress_bar(
                window.progress_canvas, final_progress)

        window.update_idletasks()

        # Completion summary
        if failed_parts:
            # Partial completion
            failed_list = "\n".join(
                [f"  - Part {idx}: {name}" for idx, name in failed_parts])
            message = f"Download completed with errors:\n\nSuccessfully downloaded: {completed_parts}/{total_parts} files\n\nFailed parts:\n{failed_list}\n\nLocation: {download_path}\n\nYou can retry the failed parts later."
            progress_label.config(
                text=f"Partial completion: {completed_parts}/{total_parts} files downloaded")
            messagebox.showinfo("Download Partially Complete", message)
        else:
            # Complete success
            progress_label.config(text="Download completed successfully")
            messagebox.showinfo(
                "Download Complete", f"Successfully downloaded {total_parts} files to:\n{download_path}")

    except Exception as e:
        error_msg = str(e)
        # User-friendly error messages (bilingual)
        if "Connection" in error_msg or "timeout" in error_msg.lower():
            error_msg = "Network error: Please check your internet connection\nخطأ في الشبكة: يرجى التحقق من اتصال الإنترنت"
        elif "Permission" in error_msg or "denied" in error_msg.lower():
            error_msg = "Permission denied: Choose a different location\nتم رفض الإذن: اختر موقعًا مختلفًا"
        elif "space" in error_msg.lower() or "disk" in error_msg.lower():
            error_msg = "Disk full: Free up space and try again\nالقرص ممتلئ: أفرغ المساحة وحاول مرة أخرى"

        messagebox.showerror("Error", f"An error occurred:\n\n{error_msg}")
        progress_label.config(text="Download failed")


def start_download_apps_games():
    """Handle apps/games download button click."""
    url = text_widget.get("1.0", tk.END).strip()

    if not url:
        messagebox.showinfo("Info", "Please enter a Vodu store URL")
        return

    # Validate URL format
    if "share.vodu.store" not in url:
        messagebox.showinfo("Info", "Please enter a valid Vodu store URL")
        return

    # Select download location
    download_path = filedialog.askdirectory(title="Choose Download Path")
    if not download_path:
        return

    # Start download in background thread
    download_thread = threading.Thread(
        target=download_apps_games_worker,
        args=(url, download_path, progress_bar,
              progress_label, time_remaining, window),
        daemon=True
    )
    download_thread.start()


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        # For bundled executable
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def download_with_retry(url, save_path, max_retries=3, retry_delay=300):
    for retry in range(max_retries + 1):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an exception if the response status is not 200

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            with open(save_path, "wb") as file, tqdm(
                desc=os.path.basename(url),
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                start_time = time.time()
                for data in response.iter_content(chunk_size=1024):
                    bar.update(len(data))
                    downloaded_size += len(data)
                    file.write(data)
                    update_progress(downloaded_size, total_size)
            return True
        except (IncompleteRead, requests.exceptions.RequestException):
            if retry < max_retries:
                print(
                    f"Retrying download for {url} after {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to download {url} after {max_retries} retries.")
                return False


def update_progress(downloaded_size, total_size):
    progress_value = int((downloaded_size / total_size) * 100)
    progress_bar["value"] = progress_value

    # Update colorful progress bar for video downloads
    if hasattr(window, 'progress_canvas'):
        update_colorful_progress_bar(window.progress_canvas, progress_value)

    start_time = time.time()
    if progress_value > 0:
        elapsed_time = time.time() - start_time
        remaining_time = (elapsed_time / progress_value) * \
            (100 - progress_value)
        time_remaining.config(
            text=f"Downloading... Estimated time remaining: {format_time(remaining_time)}")
    else:
        time_remaining.config(
            text="Downloading... Estimated time remaining: Calculating...")

    window.update_idletasks()


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def update_colorful_progress_bar(progress_canvas, percentage):
    """
    Update the custom colorful progress bar with gradient colors based on percentage.
    Colors change from red (0%) -> yellow (50%) -> green (100%)
    """
    if not progress_canvas:
        return

    # Calculate width based on percentage
    max_width = 426  # 428 - 2 (borders)
    fill_width = 2 + (max_width * percentage / 100)

    # Determine color based on progress
    if percentage < 30:
        # Red to orange (0-30%)
        red = 255
        green = int((percentage / 30) * 165)
        blue = 0
        color = f"#{red:02x}{green:02x}{blue:02x}"
    elif percentage < 70:
        # Orange to yellow (30-70%)
        red = 255
        green = 165 + int(((percentage - 30) / 40) * 90)
        blue = 0
        color = f"#{red:02x}{green:02x}{blue:02x}"
    else:
        # Yellow to green (70-100%)
        red = 255 - int(((percentage - 70) / 30) * 255)
        green = 255
        blue = 0
        color = f"#{red:02x}{green:02x}{blue:02x}"

    # Update the progress fill rectangle
    progress_canvas.delete("progress_fill")
    progress_canvas.create_rectangle(
        2, 2,
        fill_width, 28,
        fill=color,
        outline="",
        width=0,
        tags="progress_fill"
    )

    # Add percentage text overlay
    progress_canvas.delete("progress_text")
    progress_canvas.create_text(
        214, 14,  # Center of progress bar
        text=f"{percentage:.1f}%",
        fill="#ffffff",
        font=("Arial", 10, "bold"),
        tags="progress_text"
    )


def get_html_content_with_selenium(url):
    """
    Get HTML content using Selenium for JavaScript rendering.
    This is required for Vue.js Single Page Applications.
    """
    driver = None
    try:
        print("[INFO] Initializing Chrome driver for JavaScript rendering...")

        # Check if Chrome is installed
        import shutil
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(
                r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(
                r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        ]

        chrome_found = False
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_found = True
                print(f"[OK] Found Chrome at: {path}")
                break

        if not chrome_found:
            print("[X] Chrome browser not found!")
            print("Please install Google Chrome from: https://www.google.com/chrome/")
            return None

        # Try to install ChromeDriver
        try:
            from selenium.webdriver.chrome.service import Service
            service = Service(chromedriver_autoinstaller.install())
            print("[OK] ChromeDriver auto-installed successfully")
        except Exception as e:
            print(f"[WARNING] ChromeDriver auto-install failed: {e}")
            print("Trying alternative method...")

        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Use new headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Add binary location if needed
        chrome_options.binary_location = chrome_paths[0]

        # Ignore SSL errors
        chrome_options.add_argument('--ignore-ssl-errors=yes')
        chrome_options.add_argument('--ignore-certificate-errors')

        # Disable logging
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Create driver with service
        try:
            driver = webdriver.Chrome(service=service, options=chrome_options)
        except:
            # Fallback: Try without service
            driver = webdriver.Chrome(options=chrome_options)

        print(f"[INFO] Loading page: {url}")
        driver.get(url)

        # Wait for JavaScript to render
        import time
        print("[INFO] Waiting for page to render (5 seconds)...")
        time.sleep(5)  # Wait 5 seconds for page to load

        # Get the fully rendered HTML
        html_content = driver.page_source
        print(
            f"[OK] Page loaded successfully ({len(html_content)} characters)")

        return html_content

    except Exception as e:
        print(f"[X] Error with Selenium: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Google Chrome is installed")
        print("2. Try running: pip install --upgrade selenium chromedriver-autoinstaller")
        print("3. Restart the application")
        return None
    finally:
        # Always close the driver
        if driver:
            try:
                driver.quit()
                print("[INFO] Chrome driver closed")
            except:
                pass


def get_vodu_download_links_with_selenium(url):
    """
    Get download links by intercepting network requests with Selenium.
    This loads the page, clicks download buttons, and captures API responses.
    """
    import json

    driver = None
    try:
        print("[INFO] Initializing Chrome with network logging...")

        # Check if Chrome is installed
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(
                r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(
                r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(
                r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        ]

        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                print(f"[OK] Found Chrome at: {path}")
                break

        if not chrome_path:
            print("[X] Chrome browser not found!")
            return None

        # Install ChromeDriver
        from selenium.webdriver.chrome.service import Service
        service = Service(chromedriver_autoinstaller.install())

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.binary_location = chrome_path

        # Disable logging
        chrome_options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Enable performance logging (Selenium 4 way)
        chrome_options.set_capability(
            'goog:loggingPrefs', {'performance': 'ALL'})

        # Create driver with network logging
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("[OK] Chrome launched with network logging")

        print(f"[INFO] Loading page: {url}")
        driver.get(url)

        # Wait for initial page load
        import time
        print("[INFO] Waiting for page load...")
        time.sleep(5)

        # Look for download buttons (تحميل means "Download" in Arabic)
        print("[INFO] Looking for download buttons...")
        download_buttons = driver.find_elements(
            "xpath", "//button[contains(text(), 'تحميل') or contains(@class, 'download') or contains(@class, 'btn')]")

        if not download_buttons:
            # Try alternative selectors
            download_buttons = driver.find_elements(
                "css selector", "a[href*='download'], .download-btn, [class*='download']")

        print(
            f"[INFO] Found {len(download_buttons)} potential download buttons")

        # Click each button and capture network requests
        download_urls = set()

        # Limit to first 10 buttons
        for i, button in enumerate(download_buttons[:10], 1):
            try:
                print(f"[INFO] Clicking button {i}/{len(download_buttons)}...")
                driver.execute_script("arguments[0].scrollIntoView();", button)
                time.sleep(0.5)
                button.click()
                time.sleep(2)  # Wait for API call

                # Get network logs
                logs = driver.get_log('performance')

                # Parse logs for API responses
                for entry in logs:
                    try:
                        log = json.loads(entry['message'])['message']

                        # Look for API responses
                        if log.get('method') == 'Network.responseReceived':
                            response = log.get(
                                'params', {}).get('response', {})
                            request_url = response.get('url', '')

                            # Check if it's a Vodu API response
                            if 'share.vodu.store/api' in request_url or 'share.vodu.store:9999' in request_url:
                                print(f"[FOUND] API call: {request_url}")

                                # Try to get the response body
                                request_id = log.get(
                                    'params', {}).get('requestId')

                                # Look for download URLs in the URL itself
                                if 'share.vodu.store:9999/store-files/' in request_url:
                                    download_urls.add(request_url)
                                    print(f"  -> Download URL found!")

                    except (json.JSONDecodeError, KeyError):
                        continue

            except Exception as e:
                print(f"[WARNING] Error clicking button {i}: {e}")
                continue

        # Also search page source for any download URLs
        print("[INFO] Searching page source for download URLs...")
        page_source = driver.page_source
        url_pattern = r'https://share\.vodu\.store:9999/store-files/[^\s"\'<>]+'
        urls_in_html = re.findall(url_pattern, page_source)

        for url in urls_in_html:
            download_urls.add(url)

        # Convert to list
        download_urls = list(download_urls)

        if download_urls:
            print(f"\n[SUCCESS] Found {len(download_urls)} download URL(s):")
            for i, url in enumerate(download_urls, 1):
                filename = os.path.basename(url)
                print(f"  {i}. {filename}")
        else:
            print("\n[X] No download URLs found")

        return download_urls

    except Exception as e:
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if driver:
            try:
                driver.quit()
                print("[INFO] Chrome driver closed")
            except:
                pass


def get_html_content(url):
    """Simple HTML fetch using requests (for non-JavaScript pages)."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the response status is not 200
        html_content = response.text
        return html_content
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

    # هاي الدالة تابعة الى الترجمة فقط


def download_html_from_url(url, path):
    try:
        response = urllib.request.urlopen(url)
        html_content = response.read().decode("utf-8")

        # Generate a valid file name from the URL
        parsed_url = urlparse(url)
        file_name = parsed_url.netloc + parsed_url.path
        file_name = file_name.replace("/", "_").replace(".", "_")

        # Save the HTML content to a file
        save_path = os.path.join(path, f"{file_name}.html")
        with open(save_path, "w", encoding="utf-8") as file:
            file.write(html_content)

        return html_content
    except Exception as e:
        print("Failed to download HTML content.")
        print(e)
        return None


def start_download_subtitle():
    url = text_widget.get("1.0", tk.END)
    if not url:
        messagebox.showinfo("Info", "Please enter a URL.")
        return

    download_path = filedialog.askdirectory(title="Choose Download Path")
    sample_text = download_html_from_url(path=download_path, url=url)
    sample_text = str(sample_text)
    subtitle_url_pattern = r"https://movie\.vodu\.me/subtitles/(.*?)_S(\d+)E(\d+)_(\d+)\.webvtt\" data-srt=\"(.*?)\.srt"

    subtitle_matches = re.findall(subtitle_url_pattern, sample_text)

    if not download_path:
        messagebox.showinfo("Info", "Download path not selected.")
        return

    os.makedirs(download_path, exist_ok=True)

    text_widget.delete("1.0", tk.END)
    text_widget.insert(tk.END, sample_text)
    text_widget.update_idletasks()
    for series_name, season_number, episode_number, _, subtitle_link in subtitle_matches:
        subtitle_filename = f"{series_name}_S{season_number}E{episode_number}.srt"
        subtitle_save_path = os.path.join(download_path, subtitle_filename)

        progress_bar["value"] = 0
        progress_label.config(text=f"Downloading {subtitle_filename}")

        if not subtitle_link.endswith(".srt"):
            subtitle_link += ".srt"

        if download_with_retry(subtitle_link, subtitle_save_path):
            print("done")
        else:
            print("error")

    progress_bar["value"] = 100
    progress_label.config(text="Download Completed")
    # result_text.insert(tk.END, "Subtitle download completed.\n")


def get_expected_file_size(video_url):
    response = requests.head(video_url)
    content_length_header = response.headers.get('content-length')

    if content_length_header:
        return int(content_length_header)
    else:
        return None


def start_download_video():
    url = text_widget.get("1.0", tk.END).strip()
    if not url:
        messagebox.showinfo("Info", "Please enter a URL.")
        return

    # Get selected quality
    quality = selected_quality.get()
    if not quality:
        messagebox.showinfo(
            "Info", "Please select video quality (360p, 720p, or 1080p).")
        return

    # Get selected season
    season_choice = selected_season.get()
    if not season_choice:
        messagebox.showinfo(
            "Info", "Please select a season option.")
        return

    # Extract the simple text from the URL
    sample_text = get_html_content(url)

    if not sample_text:
        messagebox.showinfo(
            "Info", "Failed to extract simple text from the URL.")
        return

    text_widget.delete("1.0", tk.END)
    text_widget.insert(tk.END, sample_text)
    text_widget.update_idletasks()

    # Create pattern based on selected quality (supports 360p, 720p, 1080p)
    qnum = {
        "360p": "360",
        "720p": "720",
        "1080p": "1080",
    }.get(quality)

    # Primary pattern commonly used on the site
    video_url_pattern = rf"https://\S+-{qnum}\.mp4"
    video_matches = re.findall(video_url_pattern, sample_text)

    # If no matches found for the selected quality, try alternative common patterns
    if not video_matches:
        alternative_patterns = [
            rf"https://\S+-{qnum}p\.mp4",  # e.g., -720p.mp4
            rf"https://\S+_{qnum}\.mp4",   # e.g., _720.mp4
            rf"https://\S+_{qnum}p\.mp4",  # e.g., _720p.mp4
        ]
        for pattern in alternative_patterns:
            video_matches = re.findall(pattern, sample_text)
            if video_matches:
                break

        if not video_matches:
            messagebox.showinfo(
                "Info", f"No {quality} videos found. Try another quality option.")
            return

    # Choose base download path
    base_download_path = filedialog.askdirectory(title="Choose Download Path")

    if not base_download_path:
        messagebox.showinfo("Info", "Download path not selected.")
        return

    # Group videos by season and create folders
    season_videos = {}

    # Extract series name from the first video for folder naming
    series_name = "Unknown_Series"
    if video_matches:
        first_video = os.path.basename(video_matches[0])
        # Extract series name (everything before _S##E##)
        match = re.match(r"(.+?)_S\d+E\d+", first_video)
        if match:
            series_name = match.group(1)

    for video_link in video_matches:
        video_filename = os.path.basename(video_link)

        # Extract season number from filename
        season_match = re.search(r"_S(\d+)E\d+", video_filename)
        if season_match:
            season_num = int(season_match.group(1))

            # Filter based on season selection
            if season_choice != "all" and season_num != int(season_choice):
                continue

            # Group videos by season
            if season_num not in season_videos:
                season_videos[season_num] = []
            season_videos[season_num].append(video_link)

    if not season_videos:
        if season_choice == "all":
            messagebox.showinfo(
                "Info", "No videos found with season information.")
        else:
            messagebox.showinfo(
                "Info", f"No episodes found for Season {season_choice}. Please check if this season exists.")
        return

    total_videos = sum(len(videos) for videos in season_videos.values())
    current_video = 0

    # Download videos grouped by season
    for season_num in sorted(season_videos.keys()):
        videos = season_videos[season_num]

        # Create season folder
        season_folder_name = f"{series_name}_Season_{season_num:02d}"
        season_download_path = os.path.join(
            base_download_path, season_folder_name)
        os.makedirs(season_download_path, exist_ok=True)

        print(f"Created folder: {season_folder_name}")

        for video_link in videos:
            current_video += 1
            video_filename = os.path.basename(video_link)
            video_save_path = os.path.join(
                season_download_path, video_filename)

            if os.path.exists(video_save_path):
                existing_file_size = os.path.getsize(video_save_path)
                expected_file_size = get_expected_file_size(video_link)

                if expected_file_size and existing_file_size == expected_file_size:
                    print(
                        f"File '{video_filename}' already exists and has the correct size. Skipping download.")
                    continue

            progress_bar["value"] = 0
            season_info = f"Season {season_num}" if season_choice != "all" else f"Season {season_num}"
            progress_label.config(
                text=f"Downloading {video_filename} ({quality}) - {season_info} ({current_video}/{total_videos})")

            if download_with_retry(video_link, video_save_path):
                print(
                    f"Downloaded '{video_filename}' to {season_folder_name} in {quality}")
            else:
                print(
                    f"Failed to download '{video_filename}' from {video_link}")

    progress_bar["value"] = 100
    progress_label.config(text="Download Completed")

    # Show completion message with folder info
    completed_seasons = list(season_videos.keys())
    if len(completed_seasons) == 1:
        messagebox.showinfo(
            "Download Complete", f"Downloaded Season {completed_seasons[0]} to folder: {series_name}_Season_{completed_seasons[0]:02d}")
    else:
        season_list = ", ".join([str(s) for s in sorted(completed_seasons)])
        messagebox.showinfo(
            "Download Complete", f"Downloaded Seasons {season_list} to separate folders in:\n{base_download_path}")


def open_video_urls():
    url = text_widget.get("1.0", tk.END).strip()
    if not url:
        messagebox.showinfo("Info", "Please enter a URL.")
        return

    # Get selected quality
    quality = selected_quality.get()
    if not quality:
        messagebox.showinfo(
            "Info", "Please select video quality (360p, 720p, or 1080p).")
        return

    # Get selected season
    season_choice = selected_season.get()
    if not season_choice:
        messagebox.showinfo(
            "Info", "Please select a season option.")
        return

    # Extract the simple text from the URL
    sample_text = get_html_content(url)

    if not sample_text:
        messagebox.showinfo(
            "Info", "Failed to extract simple text from the URL.")
        return

    text_widget.delete("1.0", tk.END)
    text_widget.insert(tk.END, sample_text)
    text_widget.update_idletasks()

    # Create pattern based on selected quality (supports 360p, 720p, 1080p)
    qnum = {
        "360p": "360",
        "720p": "720",
        "1080p": "1080",
    }.get(quality)

    # Primary pattern commonly used on the site
    video_url_pattern = rf"https://\S+-{qnum}\.mp4"
    video_matches = re.findall(video_url_pattern, sample_text)

    # If no matches found for the selected quality, try alternative common patterns
    if not video_matches:
        alternative_patterns = [
            rf"https://\S+-{qnum}p\.mp4",  # e.g., -720p.mp4
            rf"https://\S+_{qnum}\.mp4",   # e.g., _720.mp4
            rf"https://\S+_{qnum}p\.mp4",  # e.g., _720p.mp4
        ]
        for pattern in alternative_patterns:
            video_matches = re.findall(pattern, sample_text)
            if video_matches:
                break

        if not video_matches:
            messagebox.showinfo(
                "Info", f"No {quality} videos found. Try another quality option.")
            return

    # Filter videos by season selection
    filtered_videos = []
    if season_choice == "all":
        filtered_videos = video_matches
    else:
        season_num = int(season_choice)
        for video_link in video_matches:
            video_filename = os.path.basename(video_link)
            # Extract season number from filename
            season_match = re.search(r"_S(\d+)E\d+", video_filename)
            if season_match and int(season_match.group(1)) == season_num:
                filtered_videos.append(video_link)

    if not filtered_videos:
        if season_choice == "all":
            messagebox.showinfo("Info", "No videos found.")
        else:
            messagebox.showinfo(
                "Info", f"No episodes found for Season {season_choice}. Please check if this season exists.")
        return

    # Ask user for confirmation before opening multiple URLs
    num_videos = len(filtered_videos)
    if num_videos > 10:
        result = messagebox.askyesno(
            "Confirm",
            f"This will open {num_videos} video URLs in your browser. This might be a lot of tabs. Do you want to continue?"
        )
        if not result:
            return
    elif num_videos > 1:
        result = messagebox.askyesno(
            "Confirm",
            f"This will open {num_videos} video URLs in your browser. Continue?"
        )
        if not result:
            return

    # Open URLs in browser
    opened_count = 0
    for video_url in filtered_videos:
        try:
            webbrowser.open(video_url)
            opened_count += 1
            time.sleep(0.5)  # Small delay to prevent overwhelming the browser
        except Exception as e:
            print(f"Failed to open URL: {video_url}, Error: {e}")

    # Show completion message
    if season_choice == "all":
        season_info = "all seasons"
    else:
        season_info = f"Season {season_choice}"

    messagebox.showinfo(
        "URLs Opened",
        f"Opened {opened_count} video URLs ({quality}) for {season_info} in your browser."
    )


def show_developer_info():
    message = "Developer Information:\n\n" \
              "Name: sajjad salam\n" \
              "Email: sajjad.salam.teama@gmail.com\n" \
              "Website: https://github.com/sajjad-salam \n" \
              "GitHub: https://github.com/sajjad-salam\n" \
              "LinkedIn: https://www.linkedin.com/in/sajjad-salam-963043244/ "

    messagebox.showinfo("Developer Information", message)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def paste_text():
    text_widget.event_generate("<<Paste>>")


def paste_text_apps():
    """Paste function for apps/games text widget"""
    if 'apps_text_widget' in globals() and apps_text_widget:
        apps_text_widget.event_generate("<<Paste>>")


def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)


window = Tk()
window.title("vodu Downloader")
window.geometry("450x870")  # Increased height for apps/games button
window.configure(bg="#282828")
# window.iconbitmap(icon_path)
window.iconbitmap(default="info")

# Initialize the quality and season selection variables after window creation
selected_quality = tk.StringVar()
selected_season = tk.StringVar()
# Set default quality to 360p and season to all
selected_quality.set("360p")
selected_season.set("all")

canvas = Canvas(
    window,
    bg="#282828",
    height=870,  # Increased height for apps/games button
    width=450,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)

canvas.place(x=0, y=0)


image_path3 = resource_path("gui/assets/button_3.png")
image_image_3 = PhotoImage(file=image_path3)
# About Button
button_3 = Button(
    # name="developer",
    # text="dev.",
    image=image_image_3,
    command=show_developer_info,
    borderwidth=0,
    highlightthickness=0,
    activebackground="#202020",
    cursor="heart",
    relief="flat"
)
button_3.place(
    x=20.0,
    y=21.0,
    width=30.0,
    height=30.0
)

image_path6 = resource_path("gui/assets/logo.png")

image_image_6 = PhotoImage(file=image_path6)
image_6 = canvas.create_image(
    225.0,
    37.0,
    image=image_image_6
)


text_widget = scrolledtext.ScrolledText(
    canvas,
    width=50,
    height=0.1,
    bg="#000000",          # Black background - better contrast
    fg="#00FF00",          # Bright green text - now visible!
    insertbackground="#00FF00",  # Green cursor
    font=("Consolas", 10),  # Monospaced font
    relief="flat",
    borderwidth=2
)
canvas.create_window(224.5, 137.5, window=text_widget)

context_menu = tk.Menu(window, tearoff=0)
context_menu.add_command(label="Paste", command=paste_text)

text_widget.bind("<Button-3>", show_context_menu)

canvas.create_text(
    20.0,
    98.0,
    anchor="nw",
    text=" المسلسل او الفيلم رابط",
    justify="right",
    fill="#FFFFFF",
    font=("Roboto Medium", 14 * -1)
)


# "Include Anonymous Intro" Toggle Button
canvas.create_text(
    75.0,
    178.0,
    anchor="nw",
    text="يجب التأكد جيدا من رابط المسلسل او الفيلم",
    fill="#FFFFFF",
    font=("Roboto Regular", 14 * -1)
)

# Quality selection label
canvas.create_text(
    20.0,
    210.0,
    anchor="nw",
    text="Video Quality / جودة الفيديو:",
    fill="#FFFFFF",
    font=("Roboto Medium", 14 * -1)
)

# Quality selection radio buttons
quality_frame = tk.Frame(canvas, bg="#282828")
canvas.create_window(225.0, 240.0, window=quality_frame)

radio_360p = tk.Radiobutton(
    quality_frame,
    text="360p",
    variable=selected_quality,
    value="360p",
    bg="#282828",
    fg="#FFFFFF",
    selectcolor="#404040",
    activebackground="#282828",
    activeforeground="#FFFFFF",
    font=("Roboto", 12)
)
radio_360p.pack(side="left", padx=10)

radio_720p = tk.Radiobutton(
    quality_frame,
    text="720p",
    variable=selected_quality,
    value="720p",
    bg="#282828",
    fg="#FFFFFF",
    selectcolor="#404040",
    activebackground="#282828",
    activeforeground="#FFFFFF",
    font=("Roboto", 12)
)
radio_720p.pack(side="left", padx=10)

radio_1080p = tk.Radiobutton(
    quality_frame,
    text="1080p",
    variable=selected_quality,
    value="1080p",
    bg="#282828",
    fg="#FFFFFF",
    selectcolor="#404040",
    activebackground="#282828",
    activeforeground="#FFFFFF",
    font=("Roboto", 12)
)
radio_1080p.pack(side="left", padx=10)

# Season selection label
canvas.create_text(
    20.0,
    270.0,
    anchor="nw",
    text="Season Selection / اختيار الموسم:",
    fill="#FFFFFF",
    font=("Roboto Medium", 14 * -1)
)

# Season selection frame
season_frame = tk.Frame(canvas, bg="#282828")
canvas.create_window(225.0, 300.0, window=season_frame)

# Create radio buttons for seasons
radio_all = tk.Radiobutton(
    season_frame,
    text="All Seasons",
    variable=selected_season,
    value="all",
    bg="#282828",
    fg="#FFFFFF",
    selectcolor="#404040",
    activebackground="#282828",
    activeforeground="#FFFFFF",
    font=("Roboto", 10)
)
radio_all.pack(side="left", padx=5)

# Season 1-5 radio buttons
for i in range(1, 6):
    radio_season = tk.Radiobutton(
        season_frame,
        text=f"S{i}",
        variable=selected_season,
        value=str(i),
        bg="#282828",
        fg="#FFFFFF",
        selectcolor="#404040",
        activebackground="#282828",
        activeforeground="#FFFFFF",
        font=("Roboto", 10)
    )
    radio_season.pack(side="left", padx=3)

# Second row for more seasons
season_frame2 = tk.Frame(canvas, bg="#282828")
canvas.create_window(225.0, 330.0, window=season_frame2)

# Season 6-10 radio buttons
for i in range(6, 11):
    radio_season = tk.Radiobutton(
        season_frame2,
        text=f"S{i}",
        variable=selected_season,
        value=str(i),
        bg="#282828",
        fg="#FFFFFF",
        selectcolor="#404040",
        activebackground="#282828",
        activeforeground="#FFFFFF",
        font=("Roboto", 10)
    )
    radio_season.pack(side="left", padx=3)


image_path_subtitle = resource_path("gui/assets/button_subtitle.png")

# Download Subtitle Button
Download_subtitle_button_image = PhotoImage(
    file=image_path_subtitle)

Download_subtitle_button = Button(
    command=start_download_subtitle,
    image=Download_subtitle_button_image,
    borderwidth=0,
    highlightthickness=0,
    activebackground="#202020",
    relief="flat"
)
Download_subtitle_button.place(
    x=18.0,
    y=370.0,  # Moved down to make room for season selection
    width=414.0,
    height=47.0
)

# Simulate existing content height (adjust this value based on your content)
existing_content_height = 200  # Adjusted for new layout

image_path_video = resource_path("gui/assets/button_video.png")

# Download Video Button
Download_video_button_image = PhotoImage(
    file=image_path_video)

Download_video_button = Button(
    command=start_download_video,
    image=Download_video_button_image,
    borderwidth=0,
    highlightthickness=0,
    activebackground="#202020",
    relief="flat"
)

# Calculate y coordinate for the second button
second_button_y = 430  # Fixed position for better layout

Download_video_button.place(
    x=18.0,
    y=second_button_y,
    width=414.0,
    height=47.0
)

# Open URLs Button
Open_urls_button = Button(
    window,
    text="فتح روابط الفيديو في المتصفح",
    command=open_video_urls,
    bg="#404040",
    fg="#FFFFFF",
    activebackground="#505050",
    activeforeground="#FFFFFF",
    font=("Roboto Medium", 12),
    borderwidth=2,
    relief="raised",
    cursor="hand2"
)

# Calculate y coordinate for the third button
third_button_y = 490  # Position after the download video button

Open_urls_button.place(
    x=18.0,
    y=third_button_y,
    width=414.0,
    height=47.0
)

# ============================================================================
# Download Apps/Games Button
# ============================================================================

apps_games_button = Button(
    window,
    text="Download Apps/Games\nتحميل التطبيقات والألعاب",
    command=start_download_apps_games,
    bg="#404040",
    fg="#FFFFFF",
    activebackground="#505050",
    activeforeground="#FFFFFF",
    font=("Roboto Medium", 12),
    borderwidth=2,
    relief="raised",
    cursor="hand2"
)

# Calculate y coordinate for the apps/games button
apps_games_button_y = 550  # Position after the Open URLs button

apps_games_button.place(
    x=18.0,
    y=apps_games_button_y,
    width=414.0,
    height=47.0
)

# Custom style for the progress bar
style = ttk.Style()
style.theme_use('clam')

# Create colorful progress bar style with gradient effect
style.configure(
    "Custom.Horizontal.TProgressbar",
    troughcolor='#1a1a1a',      # Dark gray background
    bordercolor='#000000',
    lightcolor='#00ff00',       # Light green (highlight)
    darkcolor='#00aa00',        # Dark green (shadow)
    background='linear',        # Will be set to gradient color
    borderwidth=0,
    thickness=25,               # Thicker bar
    relief='flat'
)

# Configure the progress bar with custom colors
# Note: We'll update the color dynamically in the progress callback
progress_bar = ttk.Progressbar(
    window,
    orient="horizontal",
    mode="determinate",
    style="Custom.Horizontal.TProgressbar",
    length=430                 # Fixed width
)

# Adjusted position for larger window with apps/games button
progress_bar.pack(padx=10, pady=15, side="bottom")

# Create a custom colored canvas for the progress bar (better styling)
progress_canvas = tkinter.Canvas(
    window,
    width=430,
    height=30,
    bg="#1a1a1a",
    highlightthickness=2,
    highlightbackground="#333333",
    highlightcolor="#00ff00"
)
progress_canvas.pack(padx=10, pady=(0, 10), side="bottom")

# Draw gradient background for progress bar (empty state)
progress_canvas.create_rectangle(
    2, 2, 428, 28,
    fill="#1a1a1a",
    outline="#00ff00",
    width=2,
    tags="progress_bg"
)

# Draw the actual progress bar (will be updated dynamically)
progress_canvas.create_rectangle(
    2, 2, 2, 28,
    fill="",  # Will be set to gradient color
    outline="",
    width=0,
    tags="progress_fill"
)

# Store reference to update progress bar later
window.progress_canvas = progress_canvas

# Create and position the progress label with better styling for multi-line display
progress_label = tkinter.Label(
    window,
    text="",
    font=("Consolas", 9),  # Monospaced font for better alignment
    justify="left",         # Left-align text
    bg="#282828",          # Match window background
    fg="#00FF00",          # Green text for progress
    wraplength=430,        # Wrap text at this width
    height=6               # Show up to 6 lines of text
)
progress_label.pack(padx=10, pady=5, side="bottom")

# Create and position the time remaining label
time_remaining = tkinter.Label(window, text="", font=("Helvetica", 10))
time_remaining.pack(side="bottom")


window.resizable(False, False)
window.mainloop()

# End of GUI Code
