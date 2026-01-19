# Data Model: Download Speed Optimization

**Feature**: Improve Download Speed to 4.5 MB/s
**Date**: 2026-01-19
**Type**: Enhancement to existing data structures

## Overview

This feature enhances existing data classes to support better speed tracking and performance optimization without introducing new entities. All changes are backward compatible and additive.

## Modified Entities

### 1. DownloadPart (Enhanced)

**Location**: `main.py` lines 57-74

**Current Definition**:
```python
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
```

**Enhanced Definition** (additions marked with +):
```python
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

    # NEW: Speed tracking fields
    + instant_speed_mb: float = 0.0
    + speed_samples: List[float] = field(default_factory=list)
    + last_speed_update: Optional[datetime] = None
```

**New Fields**:

| Field | Type | Purpose | Default |
|-------|------|---------|---------|
| `instant_speed_mb` | float | Real-time download speed in MB/s | 0.0 |
| `speed_samples` | List[float] | History of speed measurements (last 10 samples) | [] |
| `last_speed_update` | Optional[datetime] | Timestamp of last speed calculation | None |

**Usage Example**:
```python
# In download_part_with_resume(), track speed
def update_speed_tracking(part: DownloadPart, bytes_downloaded: int):
    now = datetime.now()
    if part.last_speed_update:
        elapsed = (now - part.last_speed_update).total_seconds()
        if elapsed >= 1.0:  # Update every second
            speed = (bytes_downloaded / (1024 * 1024)) / elapsed
            part.instant_speed_mb = speed
            part.speed_samples.append(speed)
            if len(part.speed_samples) > 10:
                part.speed_samples.pop(0)  # Keep last 10
            part.last_speed_update = now
```

**Validation Rules**:
- `instant_speed_mb` must be >= 0.0
- `speed_samples` max length: 10 samples (FIFO queue)
- `last_speed_update` must be <= current time

**Migration**: None (additive changes with default values)

---

### 2. DownloadSession (Enhanced)

**Location**: `main.py` lines 77-119

**Current Definition**:
```python
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
```

**Enhanced Definition** (additions marked with +):
```python
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

    # NEW: Performance metrics
    + peak_speed_mb: float = 0.0
    + average_speed_mb: float = 0.0
    + speed_variance: float = 0.0
    + speed_stability_score: float = 0.0  # 0.0-1.0 (higher = more stable)
```

**New Fields**:

| Field | Type | Purpose | Default |
|-------|------|---------|---------|
| `peak_speed_mb` | float | Maximum speed achieved during session | 0.0 |
| `average_speed_mb` | float | Average speed across all parts | 0.0 |
| `speed_variance` | float | Standard deviation of speed samples | 0.0 |
| `speed_stability_score` | float | Stability metric (1.0 = perfectly stable) | 0.0 |

**Calculation Methods**:

```python
def calculate_session_metrics(session: DownloadSession):
    """Calculate performance metrics from completed parts."""
    if not session.parts:
        return

    # Collect all speed samples from all parts
    all_speeds = []
    peak = 0.0

    for part in session.parts:
        if part.speed_samples:
            all_speeds.extend(part.speed_samples)
            part_peak = max(part.speed_samples) if part.speed_samples else 0.0
            peak = max(peak, part_peak)

    if all_speeds:
        import statistics
        session.peak_speed_mb = peak
        session.average_speed_mb = statistics.mean(all_speeds)

        if len(all_speeds) > 1:
            session.speed_variance = statistics.stdev(all_speeds)
            # Stability score: inverse of variance (normalized 0-1)
            # Lower variance = higher stability
            cv = session.speed_variance / session.average_speed_mb  # Coefficient of variation
            session.speed_stability_score = max(0.0, 1.0 - cv)  # 1.0 = zero variance
        else:
            session.speed_variance = 0.0
            session.speed_stability_score = 1.0
```

**Validation Rules**:
- `peak_speed_mb` >= `average_speed_mb` (peak must be >= average)
- `speed_variance` >= 0.0
- `speed_stability_score` in range [0.0, 1.0]

**Migration**: None (additive changes with default values)

---

## Relationships

### Existing Relationships (Unchanged)

```
DownloadSession (1) ────< (N) DownloadPart
    ├─ session.parts: List[DownloadPart]
    └─ Aggregates part metrics for session-level stats
```

### New Relationships

```
DownloadPart.speed_samples (N) ──> Float (speed measurements)
    └─ FIFO queue: max 10 samples per part

DownloadSession.aggregates ──> DownloadPart.speed_samples
    └─ Collects all samples for session-level metrics
```

---

## State Transitions

### DownloadPart Status (Unchanged)

```
PENDING → DOWNLOADING → COMPLETED
   ↓           ↓
  FAILED   (retry)
```

**Speed Tracking States**:
- `PENDING`: All speed fields = 0.0 or empty
- `DOWNLOADING`: `instant_speed_mb` updated every 1 second
- `COMPLETED`: Final metrics calculated, stored in `speed_samples`
- `FAILED`: Last known speed preserved in `speed_samples`

### DownloadSession Status (Unchanged)

```
INITIALIZED → DOWNLOADING → COMPLETED
                   ↓
            PARTIALLY_COMPLETED
                   ↓
                 FAILED
```

**Metric Calculation States**:
- `INITIALIZED`: All metrics = 0.0
- `DOWNLOADING`: Real-time metrics updated from active parts
- `COMPLETED`: Final metrics calculated and frozen
- `PARTIALLY_COMPLETED`: Metrics based on completed parts only
- `FAILED`: Metrics calculated up to failure point

---

## Data Flow

### Speed Tracking Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Download Starts                                      │
│    - DownloadPart instantiated                          │
│    - instant_speed_mb = 0.0                             │
│    - speed_samples = []                                 │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Chunk Downloaded (every 1 second)                    │
│    - Calculate speed: bytes / elapsed_time              │
│    - Update instant_speed_mb                            │
│    - Append to speed_samples (max 10)                   │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Part Completed                                       │
│    - Final speed recorded                               │
│    - Update DownloadSession metrics                     │
│    - Calculate average, peak, variance                  │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Session Completed                                    │
│    - Aggregate all part metrics                         │
│    - Calculate final session stats                      │
│    - Store peak_speed_mb, average_speed_mb, etc.        │
└─────────────────────────────────────────────────────────┘
```

---

## Persistence

### Current Persistence (Resume State)

**Location**: `~/.vodu_downloader/resume_state.json`

**Current Schema** (simplified):
```json
{
  "version": "1.0",
  "sessions": [
    {
      "session_id": "abc123",
      "vodu_store_url": "...",
      "download_location": "...",
      "app_name": "...",
      "parts": [
        {
          "part_number": 1,
          "filename": "...",
          "downloaded_size": 1048576,
          "status": "completed"
        }
      ]
    }
  ]
}
```

**Enhanced Schema** (additions marked with +):
```json
{
  "version": "1.1",  // Version bump
  "sessions": [
    {
      "session_id": "abc123",
      "vodu_store_url": "...",
      "download_location": "...",
      "app_name": "...",
      "parts": [
        {
          "part_number": 1,
          "filename": "...",
          "downloaded_size": 1048576,
          "status": "completed",
          + "instant_speed_mb": 4.2,
          + "speed_samples": [4.0, 4.1, 4.2, 4.3, 4.2]
        }
      ],
      + "peak_speed_mb": 4.5,
      + "average_speed_mb": 4.2,
      + "speed_variance": 0.15,
      + "speed_stability_score": 0.96
    }
  ]
}
```

**Migration Strategy**:
- Version 1.0 resumes work (speed fields default to 0.0)
- Version 1.1 saves with enhanced metrics
- Backward compatible: Old files can be read (missing fields = defaults)

---

## Performance Considerations

### Memory Impact

| Entity | Current Memory | Enhanced Memory | Increase |
|--------|---------------|-----------------|----------|
| DownloadPart | ~200 bytes | ~300 bytes | +100 bytes |
| DownloadSession (10 parts) | ~2 KB | ~3 KB | +1 KB |

**Total Impact**: Negligible (<1 MB per 1000 concurrent parts)

### CPU Impact

**Speed Calculations**:
- Per-part update: ~0.1ms (every 1 second)
- Session aggregation: ~1ms (on part completion)
- **Overhead**: <0.01% of download time

### Disk I/O Impact

**Resume State File Size**:
- Current: ~500 bytes per session
- Enhanced: ~700 bytes per session
- **Increase**: ~40% (but still <1 KB per session)

---

## Validation

### Data Validation Rules

**DownloadPart**:
```python
def validate_download_part(part: DownloadPart) -> bool:
    # Validate speed fields
    if part.instant_speed_mb < 0:
        raise ValueError("instant_speed_mb cannot be negative")

    if len(part.speed_samples) > 10:
        raise ValueError("speed_samples exceeds maximum length (10)")

    # Validate timestamps
    if part.last_speed_update and part.last_speed_update > datetime.now():
        raise ValueError("last_speed_update is in the future")

    return True
```

**DownloadSession**:
```python
def validate_download_session(session: DownloadSession) -> bool:
    # Validate peak >= average
    if session.peak_speed_mb < session.average_speed_mb:
        raise ValueError("peak_speed_mb must be >= average_speed_mb")

    # Validate variance
    if session.speed_variance < 0:
        raise ValueError("speed_variance cannot be negative")

    # Validate stability score
    if not (0.0 <= session.speed_stability_score <= 1.0):
        raise ValueError("speed_stability_score must be in [0.0, 1.0]")

    return True
```

---

## Testing Strategy

### Unit Tests

```python
def test_speed_tracking():
    """Test speed calculation and tracking."""
    part = DownloadPart(part_number=1, filename="test.zip",
                       download_url="http://example.com/test.zip",
                       expected_size=1024*1024)

    # Simulate speed updates
    update_speed_tracking(part, 2*1024*1024)  # 2 MB in 1 second
    assert part.instant_speed_mb == 2.0
    assert len(part.speed_samples) == 1

def test_session_metrics():
    """Test session-level metric aggregation."""
    session = DownloadSession(...)
    # Add parts with different speeds
    session.parts = [
        DownloadPart(..., speed_samples=[4.0, 4.1, 4.2]),
        DownloadPart(..., speed_samples=[4.3, 4.4, 4.5])
    ]

    calculate_session_metrics(session)
    assert 4.0 <= session.average_speed_mb <= 4.5
    assert session.peak_speed_mb == 4.5
    assert 0.0 <= session.speed_stability_score <= 1.0
```

### Integration Tests

```python
def test_end_to_end_speed_tracking():
    """Test speed tracking during actual download."""
    # Download test file
    session = download_file("http://example.com/test.zip")

    # Validate metrics
    assert session.peak_speed_mb > 0
    assert session.average_speed_mb > 0
    assert session.average_speed_mb <= session.peak_speed_mb
    assert 0.0 <= session.speed_stability_score <= 1.0
```

---

## Summary

**Changes Summary**:
- **Modified Entities**: 2 (DownloadPart, DownloadSession)
- **New Fields**: 7 total (3 in DownloadPart, 4 in DownloadSession)
- **New Entities**: 0
- **Relationships**: Enhanced (metric aggregation)
- **Persistence**: Version 1.0 → 1.1 (backward compatible)
- **Memory Impact**: ~100 bytes per part (negligible)
- **CPU Impact**: <0.01% overhead

**Backward Compatibility**: ✓ Fully compatible (all new fields have defaults)

**Migration Required**: ✗ No migration needed (additive changes only)
