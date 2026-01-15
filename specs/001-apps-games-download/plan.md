# Implementation Plan: Apps and Games Download Support

**Branch**: `001-apps-games-download` | **Date**: 2025-01-15 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-apps-games-download/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add apps and games download functionality to Vodu Downloader by parsing Vodu store URLs (https://share.vodu.store/#/details/[ID]), extracting all "تحميل" (Download) button links, and downloading multi-part archives sequentially with resume support, retry logic, and progress tracking. The implementation will leverage existing download infrastructure (retry logic, progress display) and add specialized handling for HTML parsing and multi-part session management.

## Technical Context

**Language/Version**: Python 3.9+ (tested on 3.9.7, per constitution)
**Primary Dependencies**: requests (HTTP), tqdm (progress), tkinter (GUI), BeautifulSoup4 (HTML parsing, NEW), selenium (JavaScript rendering, NEEDS CLARIFICATION - see research.md)
**Storage**: Local file system (user-selected directory), no database required
**Testing**: Manual testing per constitution (GUI application), network simulation for resume/retry scenarios
**Target Platform**: Windows 10/11 (primary per constitution)
**Project Type**: Single desktop application (monolithic main.py)
**Performance Goals**: Support downloads up to 50GB+ split across multiple parts; resume within 2 seconds; progress updates ≥2x/second; handle 5-10 parts per session
**Constraints**: Must handle Vue.js single-page application (may require JavaScript rendering); limited to dependencies in requirements.txt; must not block GUI during downloads; must work with unstable internet connections
**Scale/Scope**: Typically 3-10 parts per game/app; individual parts 1-10GB each; concurrent sessions: 1 (single-user desktop app)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: User Experience First ✅ PASS

**Requirements**:
- Responsive GUI with progress bars (FR-006)
- User-friendly error messages (FR-010)
- Confirmation for critical operations (FR-005: directory picker)
- Bilingual support (English/Arabic labels for new UI elements)

**Verification**: Spec explicitly requires progress tracking ("Part 2 of 5"), clear error messages, and completion summaries. No violations identified.

### Principle II: Robust Error Handling ✅ PASS

**Requirements**:
- Retry logic with max 3 attempts (FR-009, Constitution: 3 retries)
- Resume incomplete downloads (FR-007, FR-008)
- File system error handling (FR-013: disk space, permissions)
- Network failure logging (implied by FR-010 error messages)

**Verification**: Spec aligns with constitution requirements. Retry logic matches constitution standard (3 attempts). Resume support exceeds minimum requirements.

### Principle III: Content Organization ✅ PASS

**Requirements**:
- Apps/games saved directly to selected path (FR-014)
- No subdirectories created (unlike video season folders)
- Preserve original filenames from URLs

**Verification**: Spec explicitly states "without creating additional subdirectories" - follows constitution principle of automatic organization while adapting to apps/games domain (different from TV series structure).

### Principle IV: Quality Selection Flexibility ⚠️ N/A

**Verification**: Not applicable to apps/games (no quality options). This is domain-appropriate - apps/games are distributed as fixed archives, not variable quality videos.

### Principle V: Season Granularity ⚠️ N/A

**Verification**: Not applicable to apps/games (no seasons). This is domain-appropriate - apps/games use part-based organization instead of season-based.

**Overall Constitution Check**: ✅ **PASS** - All applicable principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-apps-games-download/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── vodu-store-api.md # Vodu store page structure and download URL patterns
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
vodu_downloader/
├── main.py                 # Entry point, GUI setup, event handlers (MODIFY)
│   # New functions to add:
│   ├── parse_vodu_store_page()      # Extract download URLs from Vodu store page
│   ├── download_apps_games()        # Main download coordinator for apps/games
│   ├── download_part_with_resume()  # Single part download with resume support
│   ├── check_disk_space()           # Validate available disk space before download
│   ├── get_vodu_store_html()        # Fetch Vodu store page HTML
│   └── extract_download_links()     # Parse "تحميل" buttons and extract URLs
│
├── gui/                    # GUI assets (images, icons)
│   └── assets/
│       ├── button_apps_games.png    # NEW: Download Apps/Games button
│       └── [existing assets]
├── requirements.txt        # Python dependencies (MODIFY - add BeautifulSoup4, selenium)
└── README.md              # User-facing documentation (UPDATE - add apps/games section)
```

**Structure Decision**: Single project structure (Option 1) - Vodu Downloader is a monolithic desktop application with all code in main.py. No new directories required. New functions will be added to existing main.py following current code organization patterns (similar to `start_download_video()`, `start_download_subtitle()`).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

N/A - No constitution violations. Feature aligns with all applicable principles.

## Phase 0: Research & Technical Decisions

### Unknowns to Resolve

1. **HTML Parsing Strategy for Vue.js SPA**
   - **Problem**: Vodu store is a Vue.js single-page application. Initial HTML only contains `<div id="app"></div>` and script tags. Download links are rendered dynamically via JavaScript.
   - **Options**:
     - A. Selenium/Playwright with headless browser (renders JavaScript, but heavy dependency)
     - B. Reverse-engineer Vodu store API endpoints (lightweight, but may break if API changes)
     - C. Parse embedded JSON/data from initial HTML (fragile if structure changes)
   - **Research Needed**: Inspect Vodu store page network requests to identify API endpoints serving download data.

2. **Resume Checkpoint Storage**
   - **Problem**: Need to persist download state across app restarts to support resume functionality.
   - **Options**:
     - A. In-memory only (lost on app close, simplest)
     - B. JSON file in app directory (persistent, simple)
     - C. SQLite database (robust, but overkill for single-user desktop app)
   - **Research Needed**: Evaluate user expectations for resume after app restart vs. same-session resume only.

3. **Dependency Constraints**
   - **Problem**: Constitution limits dependencies to "requests, tqdm, urllib3". HTML parsing requires additional libraries.
   - **Options**:
     - A. BeautifulSoup4 (lightweight, standard for HTML parsing)
     - B. lxml (faster but heavier)
     - C. selenium + webdriver (heavy, but required for JavaScript rendering)
   - **Research Needed**: Determine if BeautifulSoup4 alone suffices or if selenium is required for JavaScript rendering.

### Research Tasks

1. Analyze Vodu store page structure and network requests
2. Identify API endpoint serving download metadata (if exists)
3. Test if download URLs are embedded in initial HTML or require JavaScript execution
4. Evaluate selenium vs. BeautifulSoup4 for parsing requirements
5. Research Python disk space checking best practices (cross-platform)
6. Research HTTP range request implementation for resume functionality

### Best Practices to Investigate

1. Multi-part download state management patterns
2. Resume checkpoint storage for desktop applications
3. HTML parsing for single-page applications in Python
4. GUI responsiveness during long-running operations (tkinter threading)
5. User-friendly error messaging for download failures

## Phase 1: Design Artifacts

### Data Model (see data-model.md)

Entities:
- **VoduStorePage**: Page URL, page ID, list of DownloadPart
- **DownloadPart**: Part URL, filename, size, status (enum), bytes_downloaded, retry_count
- **DownloadSession**: Session ID (from URL), parts list, download_location, overall_progress, status (enum)

### API Contracts (see contracts/vodu-store-api.md)

External contracts:
- Vodu store page structure and "تحميل" button patterns
- Download URL format: `https://share.vodu.store:9999/store-files/[filename]`
- HTTP range request support for resume (Content-Length, Content-Range, Accept-Ranges headers)

### Quickstart Guide (see quickstart.md)

Developer onboarding:
- How to test apps/games download functionality
- Sample Vodu store URLs for testing
- How to simulate network failures for resume testing
- How to verify multi-part download completion

## Implementation Notes

### Integration Points

1. **Existing Functions to Reuse**:
   - `download_with_retry()` - Already implements retry logic with exponential backoff
   - `update_progress()` - Progress bar update mechanism
   - `format_time()` - Time formatting for progress display
   - `get_expected_file_size()` - File size validation

2. **New GUI Elements Required**:
   - "Download Apps/Games" button (similar to existing video/subtitle buttons)
   - Mode selection mechanism (tabs or radio buttons to switch between video and apps/games modes)
   - Apps/games-specific progress display (current part, overall progress)

3. **Error Handling Enhancements**:
   - Part-specific error messages (which part failed, why)
   - Disk space validation before download starts
   - Partial completion summaries (X of Y parts downloaded successfully)

### Threading Considerations

- Downloads MUST run in background thread to avoid blocking GUI (current pattern in main.py)
- Progress updates MUST use thread-safe GUI updates (window.update_idletasks())
- Resume checks MUST be fast (avoid scanning large files unnecessarily)

### Testing Strategy

Per constitution, manual testing required for:
1. Valid Vodu store URL parsing and part extraction
2. Multi-part download sequence (3-10 parts)
3. Resume after interruption (network disconnect, app close)
4. Retry logic (simulate network failures)
5. Error scenarios: invalid URL, missing parts, disk full, permissions
6. Edge cases: zero parts found, inconsistent part numbering, corrupted files
