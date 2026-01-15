# Data Model: Apps and Games Download Support

**Feature**: 001-apps-games-download
**Date**: 2025-01-15
**Purpose**: Define data structures and entities for multi-part app/game downloads

## Overview

This document defines the core entities and data structures for the apps/games download feature. The data model supports multi-part downloads, resume functionality, and progress tracking while maintaining simplicity for a single-user desktop application.

## Core Entities

### 1. VoduStorePage

Represents a Vodu store details page containing download links for an app or game.

**Attributes**:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `page_url` | string | Full URL of the Vodu store page | `"https://share.vodu.store/#/details/214620"` |
| `page_id` | string | Extracted ID from URL (last segment) | `"214620"` |
| `app_name` | string | Name of app/game (extracted from page or filenames) | `"Marvels-SpiderMan-2-v1-526--DODI-Repack"` |
| `download_parts` | list[DownloadPart] | List of download parts found on page | See DownloadPart entity |
| `total_parts` | int | Total number of parts | `5` |
| `total_size` | int | Sum of all part sizes in bytes | `53687091200` (50GB) |
| `fetched_at` | datetime | Timestamp when page was parsed | `2025-01-15T10:30:00Z` |

**Validation Rules**:
- `page_url` MUST match pattern: `https://share.vodu.store/#/details/[ID]`
- `page_id` MUST be extracted from URL (non-empty string)
- `download_parts` MUST NOT be empty (at least 1 part required)
- `total_size` MUST be > 0

**State Transitions**: None (immutable snapshot of page state)

---

### 2. DownloadPart

Represents a single file component (e.g., `.rar` archive) of a multi-part app/game download.

**Attributes**:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `part_number` | int | Sequential part number (1-based) | `1` |
| `filename` | string | Download filename (preserved from URL) | `"Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar"` |
| `download_url` | string | Full URL to download this part | `"https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar"` |
| `expected_size` | int | Expected file size in bytes (from Content-Length header) | `10737418240` (10GB) |
| `downloaded_size` | int | Actual bytes downloaded (for resume checking) | `5368709120` (5GB, half complete) |
| `status` | enum | Current download status | See Status Enum |
| `retry_count` | int | Number of retry attempts made | `2` |
| `local_path` | string | Full local filesystem path where part is saved | `"C:\\Downloads\\Games\\Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar"` |
| `last_attempt_at` | datetime | Timestamp of last download attempt | `2025-01-15T10:35:00Z` |
| `completed_at` | datetime | Timestamp when download completed (null if incomplete) | `2025-01-15T10:40:00Z` |

**Status Enum**:

| Value | Description | Next States |
|-------|-------------|-------------|
| `pending` | Part not yet downloaded | `downloading`, `failed` |
| `downloading` | Currently downloading | `completed`, `failed` |
| `completed` | Successfully downloaded and validated | (terminal) |
| `failed` | Failed after max retries | (terminal) |
| `skipped` | Already downloaded, skipped (resume scenario) | (terminal) |

**State Transition Diagram**:

```
pending → downloading → completed
                    ↘ failed
  (already downloaded) → skipped
```

**Validation Rules**:
- `part_number` MUST be >= 1
- `filename` MUST match pattern: `*--part{DD}.*` or `*--part{D}.*` (e.g., `part01.rar`, `part1.rar`)
- `expected_size` MUST be > 0
- `downloaded_size` MUST be >= 0 and <= `expected_size`
- `retry_count` MUST be <= 3 (constitution requirement)
- `status` MUST be one of the enum values
- `local_path` MUST be absolute path (not relative)

**Resume Logic**:
- If file exists at `local_path` AND `downloaded_size == expected_size`: Set status to `skipped`
- If file exists AND `downloaded_size < expected_size`: Resume from `downloaded_size` byte
- If file doesn't exist: Set status to `pending`, start fresh download

---

### 3. DownloadSession

Represents a complete multi-part download operation for one app/game, managing state across all parts.

**Attributes**:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `session_id` | string | Unique identifier (Vodu store page ID) | `"214620"` |
| `vodu_store_url` | string | Original Vodu store URL | `"https://share.vodu.store/#/details/214620"` |
| `download_location` | string | Directory where parts are saved | `"C:\\Downloads\\Games"` |
| `app_name` | string | Name of app/game (for display) | `"Marvels-SpiderMan-2-v1-526--DODI-Repack"` |
| `parts` | list[DownloadPart] | All parts in this session (ordered by part_number) | See DownloadPart entity |
| `total_parts` | int | Total number of parts | `5` |
| `completed_parts` | int | Number of successfully completed parts | `2` |
| `overall_progress` | float | Overall progress percentage (0.0-100.0) | `40.0` (2 of 5 parts complete) |
| `total_downloaded_bytes` | int | Total bytes downloaded across all parts | `21474836480` (20GB) |
| `total_expected_bytes` | int | Total expected bytes across all parts | `53687091200` (50GB) |
| `status` | enum | Session-level status | See Status Enum |
| `created_at` | datetime | Timestamp when session was created | `2025-01-15T10:30:00Z` |
| `started_at` | datetime | Timestamp when first download started | `2025-01-15T10:31:00Z` |
| `completed_at` | datetime | Timestamp when session completed (null if active) | `2025-01-15T10:50:00Z` |
| `last_error` | string | Last error message (null if no errors) | `"Failed to download part 3: Network error"` |

**Status Enum**:

| Value | Description | Next States |
|-------|-------------|-------------|
| `initialized` | Session created, no downloads started | `downloading`, `failed` |
| `downloading` | actively downloading parts | `completed`, `partially_completed`, `failed` |
| `paused` | User paused download | `downloading`, `cancelled` |
| `completed` | All parts downloaded successfully | (terminal) |
| `partially_completed` | Some parts failed, others succeeded | `downloading` (retry), `failed` |
| `failed` | All parts failed or critical error | (terminal) |
| `cancelled` | User cancelled download | (terminal) |

**State Transition Diagram**:

```
initialized → downloading → completed
                            ↘ partially_completed
                              → downloading (retry)
                            ↘ failed
              → paused → downloading
              → cancelled
```

**Validation Rules**:
- `session_id` MUST be unique (derived from Vodu store page ID)
- `download_location` MUST be an existing directory with write permissions
- `parts` MUST be ordered by `part_number` (ascending)
- `total_parts` MUST equal `len(parts)`
- `completed_parts` MUST equal count of parts with status `completed` or `skipped`
- `overall_progress` MUST equal `(total_downloaded_bytes / total_expected_bytes) * 100`
- `total_downloaded_bytes` MUST equal sum of `downloaded_size` across all parts

**Session Lifecycle**:

1. **Initialization**: User provides Vodu store URL → Parse page → Create `DownloadSession` with all parts in `pending` status
2. **Active Download**: Iterate through parts in order → Set part status to `downloading` → On complete, set to `completed` → Update session progress
3. **Resume Scenario**: User re-enters same URL → Load existing session from JSON → Skip completed parts → Continue from first `pending` or `failed` part
4. **Completion**: All parts `completed` or `skipped` → Set session status to `completed` → Show completion summary
5. **Partial Failure**: Some parts `completed`, some `failed` → Set session status to `partially_completed` → Offer user option to retry failed parts

**Progress Calculation**:

```python
overall_progress = (total_downloaded_bytes / total_expected_bytes) * 100
```

**Retry Logic**:
- When a part fails: Increment `retry_count`
- If `retry_count < 3`: Re-add part to download queue (status: `pending`)
- If `retry_count == 3`: Mark part as `failed`, continue to next part
- After all parts processed: Check if any parts still `failed` → Set session status to `partially_completed` or `completed`

---

## Relationships

### Entity Relationship Diagram

```
VoduStorePage (1) ─── (1) DownloadSession
                               │
                               │ (1)
                               │
                               │ (has many)
                               ↓
                        (N) DownloadPart
```

**Relationships**:
- **VoduStorePage → DownloadSession**: 1-to-1 (one page = one download session)
- **DownloadSession → DownloadPart**: 1-to-many (one session = multiple parts)

**Cascading Rules**:
- When `DownloadSession` is deleted: All associated `DownloadPart` objects are deleted
- When `DownloadPart` fails: Parent `DownloadSession` status may change to `partially_completed` or `failed`

---

## Persistent Storage (JSON Format)

### File Location

**Windows**: `C:\Users\<User>\.vodu_downloader\resume_state.json`
**Linux/macOS**: `~/.vodu_downloader/resume_state.json`

### JSON Schema

```json
{
  "version": "1.0",
  "sessions": [
    {
      "session_id": "214620",
      "vodu_store_url": "https://share.vodu.store/#/details/214620",
      "download_location": "C:\\Downloads\\Games",
      "app_name": "Marvels-SpiderMan-2-v1-526--DODI-Repack",
      "total_parts": 5,
      "completed_parts": 2,
      "overall_progress": 40.0,
      "total_downloaded_bytes": 21474836480,
      "total_expected_bytes": 53687091200,
      "status": "partially_completed",
      "created_at": "2025-01-15T10:30:00Z",
      "started_at": "2025-01-15T10:31:00Z",
      "completed_at": null,
      "last_error": "Failed to download part 3: Network error",
      "parts": [
        {
          "part_number": 1,
          "filename": "Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar",
          "download_url": "https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar",
          "expected_size": 10737418240,
          "downloaded_size": 10737418240,
          "status": "completed",
          "retry_count": 0,
          "local_path": "C:\\Downloads\\Games\\Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar",
          "last_attempt_at": "2025-01-15T10:31:00Z",
          "completed_at": "2025-01-15T10:35:00Z"
        },
        {
          "part_number": 2,
          "filename": "Marvels-SpiderMan-2-v1-526--DODI-Repack--part02.rar",
          "download_url": "https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part02.rar",
          "expected_size": 10737418240,
          "downloaded_size": 10737418240,
          "status": "completed",
          "retry_count": 0,
          "local_path": "C:\\Downloads\\Games\\Marvels-SpiderMan-2-v1-526--DODI-Repack--part02.rar",
          "last_attempt_at": "2025-01-15T10:35:00Z",
          "completed_at": "2025-01-15T10:40:00Z"
        },
        {
          "part_number": 3,
          "filename": "Marvels-SpiderMan-2-v1-526--DODI-Repack--part03.rar",
          "download_url": "https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part03.rar",
          "expected_size": 10737418240,
          "downloaded_size": 5368709120,
          "status": "failed",
          "retry_count": 3,
          "local_path": "C:\\Downloads\\Games\\Marvels-SpiderMan-2-v1-526--DODI-Repack--part03.rar",
          "last_attempt_at": "2025-01-15T10:45:00Z",
          "completed_at": null
        },
        {
          "part_number": 4,
          "filename": "Marvels-SpiderMan-2-v1-526--DODI-Repack--part04.rar",
          "download_url": "https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part04.rar",
          "expected_size": 10737418240,
          "downloaded_size": 0,
          "status": "pending",
          "retry_count": 0,
          "local_path": "C:\\Downloads\\Games\\Marvels-SpiderMan-2-v1-526--DODI-Repack--part04.rar",
          "last_attempt_at": null,
          "completed_at": null
        },
        {
          "part_number": 5,
          "filename": "Marvels-SpiderMan-2-v1-526--DODI-Repack--part05.rar",
          "download_url": "https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part05.rar",
          "expected_size": 10737418240,
          "downloaded_size": 0,
          "status": "pending",
          "retry_count": 0,
          "local_path": "C:\\Downloads\\Games\\Marvels-SpiderMan-2-v1-526--DODI-Repack--part05.rar",
          "last_attempt_at": null,
          "completed_at": null
        }
      ]
    }
  ]
}
```

### JSON Operations

**Load Sessions**:
```python
import json

def load_resume_state(json_path):
    """Load download sessions from JSON file."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data.get('sessions', [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Return empty list if file doesn't exist or is corrupted
```

**Save Sessions**:
```python
def save_resume_state(json_path, sessions):
    """Save download sessions to JSON file (atomic write)."""
    data = {
        'version': '1.0',
        'sessions': sessions
    }
    # Atomic write: write to temp file, then rename
    temp_path = json_path + '.tmp'
    with open(temp_path, 'w') as f:
        json.dump(data, f, indent=2)
    os.replace(temp_path, json_path)  # Atomic replace
```

**Update Session**:
```python
def update_session(json_path, session):
    """Update a specific session in the JSON file."""
    sessions = load_resume_state(json_path)
    # Find and replace session by session_id
    sessions = [s if s['session_id'] != session['session_id'] else session for s in sessions]
    save_resume_state(json_path, sessions)
```

---

## In-Memory Representation (Python Classes)

### Python Class Definitions

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from enum import Enum

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
        """Check if part is complete (downloaded or skipped)."""
        return self.status in [PartStatus.COMPLETED, PartStatus.SKIPPED]

    def is_resumable(self) -> bool:
        """Check if part can be resumed (partially downloaded)."""
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
        """Recalculate overall progress from parts."""
        if self.total_expected_bytes == 0:
            return 0.0
        self.total_downloaded_bytes = sum(p.downloaded_size for p in self.parts)
        self.overall_progress = (self.total_downloaded_bytes / self.total_expected_bytes) * 100
        return self.overall_progress

    def get_next_pending_part(self) -> Optional[DownloadPart]:
        """Get the next part to download (first pending or failed part)."""
        for part in self.parts:
            if part.status in [PartStatus.PENDING, PartStatus.FAILED]:
                return part
        return None

    def mark_part_completed(self, part: DownloadPart):
        """Mark a part as completed and update session progress."""
        part.status = PartStatus.COMPLETED
        part.completed_at = datetime.now()
        self.completed_parts += 1
        self.calculate_progress()
```

---

## Summary

This data model provides a simple, robust foundation for multi-part app/game downloads with the following key features:

1. **Clarity**: Three core entities with clear responsibilities
2. **Resume Support**: Persistent JSON storage for cross-session resume
3. **Progress Tracking**: Real-time progress calculation across all parts
4. **Error Handling**: Status enums track both success and failure states
5. **Simplicity**: No database required (JSON file sufficient for single-user desktop app)

**Next Step**: Generate API contracts (contracts/vodu-store-api.md) and quickstart guide (quickstart.md)
