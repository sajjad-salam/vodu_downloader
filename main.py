"""
Vodu Downloader - Modern iOS-Style GUI
Main entry point with download logic preserved and new iOS-style GUI.
"""

import threading
import shutil
from enum import Enum
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass
import re
import os
import json
import time
import sys
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog

import requests
from tqdm import tqdm
from urllib3.exceptions import IncompleteRead
from urllib.parse import urlparse

# Connection pooling optimization
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Selenium imports for JavaScript rendering
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller

# Import the new iOS-style GUI
from src.gui import VoduDownloaderApp

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
    instant_speed_mb: float = 0.0
    speed_samples: List[float] = None
    last_speed_update: Optional[datetime] = None

    def __post_init__(self):
        if self.speed_samples is None:
            self.speed_samples = []

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
    peak_speed_mb: float = 0.0
    average_speed_mb: float = 0.0
    speed_variance: float = 0.0
    speed_stability_score: float = 0.0

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
# Speed Tracking Functions
# ============================================================================

def update_speed_tracking(part: DownloadPart, bytes_downloaded: int, elapsed_seconds: float):
    if elapsed_seconds <= 0:
        return
    speed_mb = (bytes_downloaded / (1024 * 1024)) / elapsed_seconds
    part.instant_speed_mb = speed_mb
    part.last_speed_update = datetime.now()
    part.speed_samples.append(speed_mb)
    if len(part.speed_samples) > 10:
        part.speed_samples.pop(0)


def calculate_session_metrics(session: DownloadSession):
    if not session.parts:
        return
    all_speeds = []
    peak = 0.0
    for part in session.parts:
        if part.speed_samples:
            all_speeds.extend(part.speed_samples)
            part_peak = max(part.speed_samples)
            peak = max(peak, part_peak)
    if all_speeds:
        import statistics
        session.peak_speed_mb = peak
        session.average_speed_mb = statistics.mean(all_speeds)
        if len(all_speeds) > 1:
            session.speed_variance = statistics.stdev(all_speeds)
            if session.average_speed_mb > 0:
                cv = session.speed_variance / session.average_speed_mb
                session.speed_stability_score = max(0.0, 1.0 - cv)
            else:
                session.speed_stability_score = 0.0
        else:
            session.speed_variance = 0.0
            session.speed_stability_score = 1.0


# ============================================================================
# Connection Pooling Optimization
# ============================================================================

def create_optimized_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(
        pool_connections=30,
        pool_maxsize=30,
        max_retries=retry_strategy,
        pool_block=False
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({
        'Connection': 'keep-alive',
        'Accept-Encoding': 'identity',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    })
    return session


# ============================================================================
# Resume State Functions
# ============================================================================

def get_resume_state_path():
    home_dir = os.path.expanduser("~")
    vodu_dir = os.path.join(home_dir, ".vodu_downloader")
    os.makedirs(vodu_dir, exist_ok=True)
    return os.path.join(vodu_dir, "resume_state.json")


def load_resume_state():
    json_path = get_resume_state_path()
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        version = data.get('version', '1.0')
        sessions_data = data.get('sessions', [])
        sessions = []
        for session_dict in sessions_data:
            session = DownloadSession(
                session_id=session_dict['session_id'],
                vodu_store_url=session_dict['vodu_store_url'],
                download_location=session_dict['download_location'],
                app_name=session_dict['session_id'],
                parts=[],
                total_parts=session_dict.get('total_parts', 0),
                completed_parts=session_dict.get('completed_parts', 0),
                overall_progress=session_dict.get('overall_progress', 0.0),
                total_downloaded_bytes=session_dict.get('total_downloaded_bytes', 0),
                total_expected_bytes=session_dict.get('total_expected_bytes', 0),
                status=SessionStatus(session_dict.get('status', 'initialized')),
                created_at=datetime.fromisoformat(session_dict['created_at']) if session_dict.get('created_at') else datetime.now(),
                started_at=datetime.fromisoformat(session_dict['started_at']) if session_dict.get('started_at') else None,
                completed_at=datetime.fromisoformat(session_dict['completed_at']) if session_dict.get('completed_at') else None,
                last_error=session_dict.get('last_error'),
                peak_speed_mb=session_dict.get('peak_speed_mb', 0.0),
                average_speed_mb=session_dict.get('average_speed_mb', 0.0),
                speed_variance=session_dict.get('speed_variance', 0.0),
                speed_stability_score=session_dict.get('speed_stability_score', 0.0)
            )
            for part_dict in session_dict.get('parts', []):
                part = DownloadPart(
                    part_number=part_dict['part_number'],
                    filename=part_dict['filename'],
                    download_url=part_dict['download_url'],
                    expected_size=part_dict['expected_size'],
                    downloaded_size=part_dict.get('downloaded_size', 0),
                    status=PartStatus(part_dict.get('status', 'pending')),
                    retry_count=part_dict.get('retry_count', 0),
                    local_path=part_dict.get('local_path'),
                    last_attempt_at=datetime.fromisoformat(part_dict['last_attempt_at']) if part_dict.get('last_attempt_at') else None,
                    completed_at=datetime.fromisoformat(part_dict['completed_at']) if part_dict.get('completed_at') else None,
                    instant_speed_mb=part_dict.get('instant_speed_mb', 0.0),
                    speed_samples=part_dict.get('speed_samples', []),
                    last_speed_update=datetime.fromisoformat(part_dict['last_speed_update']) if part_dict.get('last_speed_update') else None
                )
                session.parts.append(part)
            sessions.append(session)
        return sessions
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_resume_state(sessions):
    json_path = get_resume_state_path()
    sessions_data = []
    for session in sessions:
        session_dict = {
            'session_id': session.session_id,
            'vodu_store_url': session.vodu_store_url,
            'download_location': session.download_location,
            'app_name': session.app_name,
            'total_parts': session.total_parts,
            'completed_parts': session.completed_parts,
            'overall_progress': session.overall_progress,
            'total_downloaded_bytes': session.total_downloaded_bytes,
            'total_expected_bytes': session.total_expected_bytes,
            'status': session.status.value if isinstance(session.status, SessionStatus) else session.status,
            'created_at': session.created_at.isoformat() if session.created_at else None,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            'last_error': session.last_error,
            'peak_speed_mb': session.peak_speed_mb,
            'average_speed_mb': session.average_speed_mb,
            'speed_variance': session.speed_variance,
            'speed_stability_score': session.speed_stability_score,
            'parts': []
        }
        for part in session.parts:
            part_dict = {
                'part_number': part.part_number,
                'filename': part.filename,
                'download_url': part.download_url,
                'expected_size': part.expected_size,
                'downloaded_size': part.downloaded_size,
                'status': part.status.value if isinstance(part.status, PartStatus) else part.status,
                'retry_count': part.retry_count,
                'local_path': part.local_path,
                'last_attempt_at': part.last_attempt_at.isoformat() if part.last_attempt_at else None,
                'completed_at': part.completed_at.isoformat() if part.completed_at else None,
                'instant_speed_mb': part.instant_speed_mb,
                'speed_samples': part.speed_samples,
                'last_speed_update': part.last_speed_update.isoformat() if part.last_speed_update else None
            }
            session_dict['parts'].append(part_dict)
        sessions_data.append(session_dict)
    data = {
        'version': '1.1',
        'sessions': sessions_data
    }
    temp_path = json_path + '.tmp'
    with open(temp_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(temp_path, json_path)


def check_existing_part(file_path, expected_size):
    if os.path.exists(file_path):
        actual_size = os.path.getsize(file_path)
        return actual_size == expected_size
    return False


def check_disk_space(path, required_bytes):
    try:
        usage = shutil.disk_usage(path)
        available = usage.free
        return available >= required_bytes
    except OSError:
        return True


# ============================================================================
# URL Extraction Functions
# ============================================================================

def extract_download_links(html_content):
    if not html_content:
        return []
    url_pattern = r'https://share\.vodu\.store:9999/store-files/[^\s"\'<>]+'
    try:
        download_urls = re.findall(url_pattern, html_content)
    except re.error:
        return []
    if not download_urls:
        json_pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        json_match = re.search(json_pattern, html_content, re.DOTALL)
        if json_match:
            try:
                import json as json_module
                data = json_module.loads(json_match.group(1))
                json_str = str(data)
                download_urls = re.findall(url_pattern, json_str)
            except:
                pass
    seen = set()
    unique_urls = []
    for url in download_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    if not unique_urls:
        print("No download links found!")
    return unique_urls


def get_file_info_api(app_id):
    api_url = f"https://share.vodu.store/api/v1/file/{app_id}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://share.vodu.store/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    cookies = {"G_ENABLED_IDPS": "google"}
    try:
        print(f"[INFO] Fetching file list from API: {api_url}")
        response = requests.get(api_url, headers=headers, cookies=cookies, timeout=30)
        if response.status_code != 200:
            return None
        data = response.json()
        if 'objectFiles' not in data or not data['objectFiles']:
            return None
        object_files = data['objectFiles']
        download_urls = []
        for file_info in object_files:
            file_id = file_info.get('id')
            download_url = get_download_url_for_file(file_id)
            if download_url:
                download_urls.append(download_url)
        return download_urls if download_urls else None
    except Exception:
        return None


def get_download_url_for_file(file_id):
    api_url = f"https://share.vodu.store/api/v1/download/no-recaptcha/{file_id}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://share.vodu.store/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    cookies = {"G_ENABLED_IDPS": "google"}
    try:
        response = requests.get(api_url, headers=headers, cookies=cookies, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if "messge" in data:
                message_value = data["messge"]
                if isinstance(message_value, str) and 'share.vodu.store:9999' in message_value:
                    return message_value
        return None
    except Exception:
        return None


def try_api_endpoint(url):
    id_match = re.search(r'/details/(\d+)', url)
    if not id_match:
        return None
    app_id = id_match.group(1)
    print(f"\nTrying /api/v1/file/ endpoint for ID: {app_id}")
    result = get_file_info_api(app_id)
    if result:
        return result
    api_url = f"https://share.vodu.store/api/v1/download/no-recaptcha/{app_id}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://share.vodu.store/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0"
    }
    cookies = {"G_ENABLED_IDPS": "google"}
    try:
        response = requests.get(api_url, headers=headers, cookies=cookies, timeout=30)
        if response.status_code == 200:
            data = response.json()
            download_urls = []
            if isinstance(data, dict):
                if "messge" in data:
                    message_value = data["messge"]
                    if isinstance(message_value, str) and 'share.vodu.store:9999' in message_value:
                        download_urls.append(message_value)
                elif "files" in data:
                    for item in data["files"]:
                        urls = re.findall(r'https://share\.vodu\.store:9999/store-files/[^\s"\'<>]+', str(item))
                        download_urls.extend(urls)
            if not download_urls:
                data_str = str(data)
                download_urls = re.findall(r'https://share\.vodu\.store:9999/store-files/[^\s"\'<>]+', data_str)
            seen = set()
            unique_urls = []
            for url in download_urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            return unique_urls if unique_urls else None
    except Exception:
        pass
    return None


def download_part_with_resume(url, save_path, progress_callback=None, session=None, download_part=None):
    headers = {}
    mode = 'wb'
    if os.path.exists(save_path):
        existing_size = os.path.getsize(save_path)
        headers['Range'] = f'bytes={existing_size}-'
        mode = 'ab'
    close_session = False
    if session is None:
        session = create_optimized_session()
        close_session = True
    try:
        response = session.get(url, headers=headers, stream=True, timeout=600)
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        if mode == 'ab':
            total_size = existing_size + total_size
        downloaded_size = os.path.getsize(save_path) if mode == 'ab' else 0
        chunk_size = 4 * 1024 * 1024
        last_update_time = time.time()
        bytes_since_last_update = 0
        with open(save_path, mode, buffering=256 * 1024) as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    bytes_since_last_update += len(chunk)
                    current_time = time.time()
                    elapsed = current_time - last_update_time
                    if download_part and elapsed >= 1.0:
                        update_speed_tracking(download_part, bytes_since_last_update, elapsed)
                        last_update_time = current_time
                        bytes_since_last_update = 0
                    if progress_callback:
                        progress_callback(len(chunk), downloaded_size, total_size)
        return True
    except requests.exceptions.RequestException:
        return False
    finally:
        if close_session:
            session.close()


def get_vodu_download_links_with_selenium(url):
    driver = None
    try:
        print("[INFO] Initializing Chrome with network logging...")
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        if not chrome_path:
            return None
        service = Service(chromedriver_autoinstaller.install())
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.binary_location = chrome_path
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print(f"[INFO] Loading page: {url}")
        driver.get(url)
        time.sleep(5)
        download_buttons = driver.find_elements("xpath", "//button[contains(text(), 'تحميل') or contains(@class, 'download')]")
        download_urls = set()
        for button in download_buttons[:10]:
            try:
                driver.execute_script("arguments[0].scrollIntoView();", button)
                time.sleep(0.5)
                button.click()
                time.sleep(2)
                logs = driver.get_log('performance')
                for entry in logs:
                    try:
                        log = json.loads(entry['message'])['message']
                        if log.get('method') == 'Network.responseReceived':
                            response_url = log.get('params', {}).get('response', {}).get('url', '')
                            if 'share.vodu.store:9999/store-files/' in response_url:
                                download_urls.add(response_url)
                    except:
                        continue
            except:
                continue
        page_source = driver.page_source
        url_pattern = r'https://share\.vodu\.store:9999/store-files/[^\s"\'<>]+'
        urls_in_html = re.findall(url_pattern, page_source)
        for url in urls_in_html:
            download_urls.add(url)
        return list(download_urls) if download_urls else None
    except Exception:
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


# ============================================================================
# Helper Functions
# ============================================================================

def get_html_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException:
        return None


def get_expected_file_size(video_url):
    try:
        response = requests.head(video_url)
        content_length = response.headers.get('content-length')
        if content_length:
            return int(content_length)
    except:
        pass
    return None


def download_with_retry(url, save_path, progress_bar=None, status_label=None, window=None, max_retries=3):
    for retry in range(max_retries + 1):
        try:
            response = requests.get(url, stream=True, timeout=600)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            with open(save_path, "wb") as file:
                for data in response.iter_content(chunk_size=1024 * 1024):
                    file.write(data)
                    downloaded_size += len(data)
                    if progress_bar and window:
                        progress = int((downloaded_size / total_size) * 100) if total_size > 0 else 0
                        # Update the progress bar
                        if hasattr(progress_bar, 'set_progress'):
                            progress_bar.set_progress(progress)
                        else:
                            progress_bar["value"] = progress
                        window.update_idletasks()
            return True
        except Exception as e:
            if retry < max_retries:
                print(f"Retrying {url} (attempt {retry + 2}/{max_retries + 1})...")
                time.sleep(5)
            else:
                print(f"Failed to download {url}")
                return False
    return False


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


# ============================================================================
# Download Workers
# ============================================================================

def download_apps_games_worker(vodu_store_url, download_path, progress_bar, status_label, time_label, window):
    session = create_optimized_session()
    try:
        print("\n" + "=" * 60)
        print("Fetching download links from API...")
        print("=" * 60 + "\n")

        download_urls = try_api_endpoint(vodu_store_url)

        if not download_urls:
            print("\n" + "=" * 60)
            print("API failed, trying Selenium...")
            print("=" * 60 + "\n")
            download_urls = get_vodu_download_links_with_selenium(vodu_store_url)

        if not download_urls:
            messagebox.showinfo("Info", "No download links found.")
            return

        total_parts = len(download_urls)
        total_size = 0
        completed_parts = 0
        failed_parts = []
        overall_start_time = time.time()
        total_downloaded_bytes = 0

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

        if total_size > 0 and not check_disk_space(download_path, total_size):
            messagebox.showerror("Error", f"Not enough disk space. Need {total_size / (1024**3):.2f}GB")
            return

        for i, url in enumerate(download_urls, 1):
            filename = os.path.basename(url)
            save_path = os.path.join(download_path, filename)
            expected_size = part_sizes.get(filename, 0)

            if expected_size > 0 and check_existing_part(save_path, expected_size):
                if hasattr(status_label, 'set_text'):
                    status_label.set_text(f"✓ Skipping: Part {i}/{total_parts} - {filename}\n(already downloaded)")
                else:
                    status_label.config(text=f"✓ Skipping: Part {i}/{total_parts}")
                window.update_idletasks()
                completed_parts += 1
                total_downloaded_bytes += expected_size
                overall_progress = (completed_parts / total_parts) * 100
                if hasattr(progress_bar, 'set_progress'):
                    progress_bar.set_progress(overall_progress)
                else:
                    progress_bar["value"] = overall_progress
                window.update_idletasks()
                continue

            part_start_time = time.time()
            part_downloaded_bytes = 0
            last_print_time = time.time()
            last_print_bytes = 0
            last_gui_update_time = time.time()

            download_part = DownloadPart(
                part_number=i,
                filename=filename,
                download_url=url,
                expected_size=expected_size,
                downloaded_size=0,
                status=PartStatus.PENDING
            )

            success = False
            for attempt in range(3):
                if attempt > 0:
                    if hasattr(status_label, 'set_text'):
                        status_label.set_text(f"⚠ Retrying: Part {i}/{total_parts} - {filename}\nAttempt {attempt + 1}/3...")
                    else:
                        status_label.config(text=f"⚠ Retrying: Part {i}/{total_parts}")
                    window.update_idletasks()
                    time.sleep(5)
                else:
                    if hasattr(status_label, 'set_text'):
                        status_label.set_text(f"⬇ Downloading: Part {i}/{total_parts} - {filename}\nStarting...")
                    else:
                        status_label.config(text=f"⬇ Downloading: Part {i}/{total_parts}")
                    window.update_idletasks()

                def update_progress(chunk_bytes, downloaded, total):
                    nonlocal part_downloaded_bytes, last_print_time, last_print_bytes, last_gui_update_time
                    part_downloaded_bytes = downloaded
                    current_time = time.time()

                    if total > 0:
                        part_progress = (downloaded / total) * 100
                        current_total_downloaded = total_downloaded_bytes + downloaded
                        overall_progress = (current_total_downloaded / total_size * 100) if total_size > 0 else (completed_parts / total_parts) * 100 + (part_progress / total_parts)

                        elapsed_time = time.time() - part_start_time
                        speed_mb = (downloaded / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
                        display_speed = download_part.instant_speed_mb if download_part.instant_speed_mb > 0 else speed_mb

                        if speed > 0 and downloaded < total:
                            remaining_bytes = total - downloaded
                            eta_seconds = remaining_bytes / speed
                            eta_str = f"{int(eta_seconds // 60)}:{int(eta_seconds % 60):02d}"
                        else:
                            eta_str = "Calculating..."

                        if current_time - last_print_time >= 2.0:
                            time_diff = current_time - last_print_time
                            bytes_diff = downloaded - last_print_bytes
                            current_speed = (bytes_diff / time_diff / (1024 * 1024)) if time_diff > 0 else display_speed
                            print(f"\r  Progress: {part_progress:5.1f}% | {downloaded / (1024*1024):7.1f} MB | Speed: {current_speed:6.1f} MB/s | ETA: {eta_str}", end='', flush=True)
                            last_print_time = current_time
                            last_print_bytes = downloaded

                        if current_time - last_gui_update_time >= 0.5:
                            if hasattr(progress_bar, 'set_progress'):
                                progress_bar.set_progress(overall_progress)
                            else:
                                progress_bar["value"] = overall_progress

                            progress_text = (
                                f"⬇ Part {i}/{total_parts}: {filename}\n"
                                f"{part_progress:.1f}% | Speed: {display_speed:.1f} MB/s | ETA: {eta_str}\n"
                                f"Overall: {overall_progress:.1f}%"
                            )
                            if hasattr(status_label, 'set_text'):
                                status_label.set_text(progress_text)
                            else:
                                status_label.config(text=progress_text)
                            window.update_idletasks()
                            last_gui_update_time = current_time

                success = download_part_with_resume(url, save_path, update_progress, session, download_part)
                if success:
                    break

            if success:
                completed_parts += 1
                total_downloaded_bytes += part_downloaded_bytes
                part_size_mb = part_downloaded_bytes / (1024 * 1024)
                elapsed_time = time.time() - part_start_time
                avg_speed = part_downloaded_bytes / elapsed_time / (1024 * 1024) if elapsed_time > 0 else 0

                if hasattr(status_label, 'set_text'):
                    status_label.set_text(f"✓ Completed: Part {i}/{total_parts} - {filename}\nSize: {part_size_mb:.1f} MB")
                else:
                    status_label.config(text=f"✓ Completed: {i}/{total_parts}")
                window.update_idletasks()
            else:
                failed_parts.append((i, filename))

        session.close()

        final_progress = 100 if not failed_parts else (completed_parts / total_parts) * 100
        if hasattr(progress_bar, 'set_progress'):
            progress_bar.set_progress(final_progress)
        else:
            progress_bar["value"] = final_progress
        window.update_idletasks()

        if failed_parts:
            failed_list = "\n".join([f"  - Part {idx}: {name}" for idx, name in failed_parts])
            message = f"Download completed with errors:\n\nSuccessfully downloaded: {completed_parts}/{total_parts} files\n\nFailed parts:\n{failed_list}"
            if hasattr(status_label, 'set_text'):
                status_label.set_text(f"Partial completion: {completed_parts}/{total_parts} files")
            messagebox.showinfo("Download Partially Complete", message)
        else:
            if hasattr(status_label, 'set_text'):
                status_label.set_text("Download completed successfully")
            messagebox.showinfo("Download Complete", f"Successfully downloaded {total_parts} files to:\n{download_path}")

    except Exception as e:
        error_msg = str(e)
        if "Connection" in error_msg or "timeout" in error_msg.lower():
            error_msg = "Network error: Please check your internet connection"
        elif "Permission" in error_msg or "denied" in error_msg.lower():
            error_msg = "Permission denied: Choose a different location"
        messagebox.showerror("Error", f"An error occurred:\n\n{error_msg}")
        if hasattr(status_label, 'set_text'):
            status_label.set_text("Download failed")


# ============================================================================
# Adapter Functions for GUI
# ============================================================================

class DownloadHandlers:
    """Adapter class to connect GUI with download logic."""

    def __init__(self, app):
        self.app = app
        self.selected_quality = '360p'
        self.selected_season = 'all'
        self.html_cache = None

    def set_quality(self, quality: str):
        self.selected_quality = quality

    def set_season(self, season: str):
        self.selected_season = season

    def handle_video_download(self, url, quality, season, progress_bar, status_label, time_label, window):
        """Handle video download request."""
        if not url:
            messagebox.showinfo("Info", "Please enter a URL.")
            return

        # Get HTML content
        sample_text = get_html_content(url)
        if not sample_text:
            messagebox.showinfo("Info", "Failed to fetch content from URL.")
            return

        self.html_cache = sample_text

        # Create video URL pattern based on quality
        qnum = {"360p": "360", "720p": "720", "1080p": "1080"}.get(quality, "360")
        video_url_pattern = rf"https://\S+-{qnum}\.mp4"
        video_matches = re.findall(video_url_pattern, sample_text)

        if not video_matches:
            alternative_patterns = [
                rf"https://\S+-{qnum}p\.mp4",
                rf"https://\S+_{qnum}\.mp4",
                rf"https://\S+_{qnum}p\.mp4",
            ]
            for pattern in alternative_patterns:
                video_matches = re.findall(pattern, sample_text)
                if video_matches:
                    break

        if not video_matches:
            available_qualities = []
            for q in ["360", "720", "1080"]:
                if re.findall(rf"https://\S+-{q}\.mp4", sample_text):
                    available_qualities.append(f"{q}p")
            if available_qualities:
                qualities_str = ", ".join(available_qualities)
                messagebox.showinfo("Info", f"No {quality} videos found.\n\nAvailable: {qualities_str}")
            else:
                messagebox.showinfo("Info", f"No {quality} videos found.")
            return

        # Select download path
        base_download_path = filedialog.askdirectory(title="Choose Download Path")
        if not base_download_path:
            return

        # Group videos by season
        season_videos = {}
        series_name = "Unknown_Series"
        if video_matches:
            first_video = os.path.basename(video_matches[0])
            match = re.match(r"(.+?)_S\d+E\d+", first_video)
            if match:
                series_name = match.group(1)

        for video_link in video_matches:
            video_filename = os.path.basename(video_link)
            season_match = re.search(r"_S(\d+)E\d+", video_filename)
            if season_match:
                season_num = int(season_match.group(1))
                if season != "all" and season_num != int(season):
                    continue
                if season_num not in season_videos:
                    season_videos[season_num] = []
                season_videos[season_num].append(video_link)

        if not season_videos:
            messagebox.showinfo("Info", "No videos found for the selected season.")
            return

        total_videos = sum(len(videos) for videos in season_videos.values())
        current_video = 0

        # Download videos
        for season_num in sorted(season_videos.keys()):
            videos = season_videos[season_num]
            season_folder_name = f"{series_name}_Season_{season_num:02d}"
            season_download_path = os.path.join(base_download_path, season_folder_name)
            os.makedirs(season_download_path, exist_ok=True)

            for video_link in videos:
                current_video += 1
                video_filename = os.path.basename(video_link)
                video_save_path = os.path.join(season_download_path, video_filename)

                if os.path.exists(video_save_path):
                    existing_size = os.path.getsize(video_save_path)
                    expected_size = get_expected_file_size(video_link)
                    if expected_size and existing_size == expected_size:
                        continue

                progress_text = f"Downloading {video_filename} ({quality}) - S{season_num} ({current_video}/{total_videos})"
                if hasattr(status_label, 'set_text'):
                    status_label.set_text(progress_text)
                else:
                    status_label.config(text=progress_text)
                window.update_idletasks()

                if download_with_retry(video_link, video_save_path, progress_bar, status_label, window):
                    print(f"Downloaded '{video_filename}'")

        if hasattr(progress_bar, 'set_progress'):
            progress_bar.set_progress(100)
        else:
            progress_bar["value"] = 100
        if hasattr(status_label, 'set_text'):
            status_label.set_text("Download Completed")
        messagebox.showinfo("Download Complete", f"Downloaded {total_videos} videos to:\n{base_download_path}")

    def handle_subtitle_download(self, url, progress_bar, status_label, window):
        """Handle subtitle download request."""
        if not url:
            messagebox.showinfo("Info", "Please enter a URL.")
            return

        sample_text = get_html_content(url)
        if not sample_text:
            messagebox.showinfo("Info", "Failed to fetch content from URL.")
            return

        download_path = filedialog.askdirectory(title="Choose Download Path")
        if not download_path:
            return

        os.makedirs(download_path, exist_ok=True)

        subtitle_url_pattern = r"https://movie\.vodu\.me/subtitles/(.*?)_S(\d+)E(\d+)_(\d+)\.webvtt\" data-srt=\"(.*?)\.srt"
        subtitle_matches = re.findall(subtitle_url_pattern, sample_text)

        for series_name, season_number, episode_number, _, subtitle_link in subtitle_matches:
            subtitle_filename = f"{series_name}_S{season_number}E{episode_number}.srt"
            subtitle_save_path = os.path.join(download_path, subtitle_filename)

            if not subtitle_link.endswith(".srt"):
                subtitle_link += ".srt"

            if hasattr(status_label, 'set_text'):
                status_label.set_text(f"Downloading {subtitle_filename}")
            else:
                status_label.config(text=f"Downloading {subtitle_filename}")
            window.update_idletasks()

            download_with_retry(subtitle_link, subtitle_save_path, progress_bar, status_label, window)

        if hasattr(progress_bar, 'set_progress'):
            progress_bar.set_progress(100)
        if hasattr(status_label, 'set_text'):
            status_label.set_text("Subtitle download completed")
        messagebox.showinfo("Complete", "Subtitle download completed.")

    def handle_open_video_urls(self, url, quality, season):
        """Handle open video URLs request."""
        if not url:
            messagebox.showinfo("Info", "Please enter a URL.")
            return

        sample_text = get_html_content(url)
        if not sample_text:
            messagebox.showinfo("Info", "Failed to fetch content from URL.")
            return

        qnum = {"360p": "360", "720p": "720", "1080p": "1080"}.get(quality, "360")
        video_url_pattern = rf"https://\S+-{qnum}\.mp4"
        video_matches = re.findall(video_url_pattern, sample_text)

        if not video_matches:
            alternative_patterns = [
                rf"https://\S+-{qnum}p\.mp4",
                rf"https://\S+_{qnum}\.mp4",
                rf"https://\S+_{qnum}p\.mp4",
            ]
            for pattern in alternative_patterns:
                video_matches = re.findall(pattern, sample_text)
                if video_matches:
                    break

        if not video_matches:
            messagebox.showinfo("Info", f"No {quality} videos found.")
            return

        # Filter by season
        filtered_videos = []
        for video_link in video_matches:
            video_filename = os.path.basename(video_link)
            season_match = re.search(r"_S(\d+)E\d+", video_filename)
            if season_match:
                season_num = int(season_match.group(1))
                if season == "all" or season_num == int(season):
                    filtered_videos.append(video_link)

        if not filtered_videos:
            messagebox.showinfo("Info", "No videos found for the selected season.")
            return

        # Confirm before opening
        num_videos = len(filtered_videos)
        if num_videos > 10:
            if not messagebox.askyesno("Confirm", f"This will open {num_videos} URLs. Continue?"):
                return
        elif num_videos > 1:
            if not messagebox.askyesno("Confirm", f"Open {num_videos} URLs?"):
                return

        # Open URLs
        for video_url in filtered_videos:
            try:
                webbrowser.open(video_url)
                time.sleep(0.5)
            except Exception as e:
                print(f"Failed to open URL: {e}")

        messagebox.showinfo("URLs Opened", f"Opened {num_videos} video URLs in your browser.")

    def handle_apps_download(self, url, progress_bar, status_label, time_label, window):
        """Handle apps/games download request."""
        if not url:
            messagebox.showinfo("Info", "Please enter a Vodu store URL")
            return
        if "share.vodu.store" not in url:
            messagebox.showinfo("Info", "Please enter a valid Vodu store URL")
            return

        download_path = filedialog.askdirectory(title="Choose Download Path")
        if not download_path:
            return

        download_thread = threading.Thread(
            target=download_apps_games_worker,
            args=(url, download_path, progress_bar, status_label, time_label, window),
            daemon=True
        )
        download_thread.start()

    def handle_apps_open_urls(self, url):
        """Handle open apps URLs request."""
        if not url:
            messagebox.showinfo("Info", "Please enter a Vodu store URL")
            return
        if "share.vodu.store" not in url:
            messagebox.showinfo("Info", "Please enter a valid Vodu store URL")
            return

        download_urls = try_api_endpoint(url)
        if not download_urls:
            download_urls = get_vodu_download_links_with_selenium(url)

        if not download_urls:
            messagebox.showinfo("Info", "No download links found.")
            return

        num_urls = len(download_urls)
        if num_urls > 10:
            if not messagebox.askyesno("Confirm", f"Open {num_urls} URLs?"):
                return

        for i, download_url in enumerate(download_urls, 1):
            try:
                webbrowser.open(download_url)
                time.sleep(0.5)
            except:
                pass

        messagebox.showinfo("URLs Opened", f"Opened {num_urls} file URLs in your browser.")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point for the application."""
    # Create and run the app
    app = VoduDownloaderApp()

    # Create download handlers
    handlers = DownloadHandlers(app)

    # Connect handlers to the app
    app.download_handlers = {
        'video': handlers.handle_video_download,
        'subtitle': handlers.handle_subtitle_download,
        'open_video_urls': handlers.handle_open_video_urls,
        'apps_download': handlers.handle_apps_download,
        'apps_open_urls': handlers.handle_apps_open_urls,
    }

    app.mainloop()


if __name__ == "__main__":
    main()
