# Tasks: Apps and Games Download Support

**Input**: Design documents from `/specs/001-apps-games-download/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Manual testing required per constitution. No automated test tasks included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: All code in `main.py` at repository root
- GUI assets: `gui/assets/`
- Configuration: `requirements.txt`, `README.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Add new dependencies to requirements.txt in requirements.txt (beautifulsoup4==4.12.3, selenium==4.16.0, chromedriver-autoinstaller==0.6.4)
- [X] T002 Install new dependencies via pip (beautifulsoup4, selenium, chromedriver-autoinstaller)
- [X] T003 [P] Create Selenium test script to verify ChromeDriver setup in test_selenium.py

**Note**: Using existing dependencies (requests, urllib.request) instead of Selenium per user requirement.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement parse_vodu_store_page() function in main.py to extract download URLs using Selenium with headless Chrome
- [X] T005 [P] Implement check_disk_space() function in main.py to validate available disk space before download
- [X] T006 [P] Implement load_resume_state() function in main.py to load download sessions from JSON file
- [X] T007 [P] Implement save_resume_state() function in main.py to save download sessions to JSON file (atomic write)
- [X] T008 Implement DownloadPart dataclass in main.py with attributes: part_number, filename, download_url, expected_size, downloaded_size, status, retry_count, local_path
- [X] T009 Implement DownloadSession dataclass in main.py with attributes: session_id, vodu_store_url, download_location, app_name, parts, total_parts, completed_parts, overall_progress, status
- [X] T010 Implement PartStatus enum in main.py with values: PENDING, DOWNLOADING, COMPLETED, FAILED, SKIPPED
- [X] T011 Implement SessionStatus enum in main.py with values: INITIALIZED, DOWNLOADING, PAUSED, COMPLETED, PARTIALLY_COMPLETED, FAILED, CANCELLED

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download Apps and Games with All Parts (Priority: P1) 🎯 MVP

**Goal**: Enable users to download multi-part apps/games from Vodu store URLs with sequential download and progress tracking.

**Independent Test**: Provide a Vodu store URL for a multi-part game, verify all parts are discovered, downloaded sequentially with progress tracking, and saved to selected directory.

### Implementation for User Story 1

- [X] T012 [US1] Implement extract_download_links() function in main.py to parse "تحميل" buttons and extract download URLs from onclick attributes
- [X] T013 [US1] Implement download_part_with_resume() function in main.py to download single part with streaming and progress callback
- [X] T014 [US1] Implement download_apps_games_worker() function in main.py as main download coordinator (runs in background thread)
- [X] T015 [US1] Implement start_download_apps_games() function in main.py as GUI button handler (validates URL, selects download path, starts worker thread)
- [X] T016 [US1] Add "Download Apps/Games" button to GUI in main.py with bilingual label (Download Apps/Games / تحميل التطبيقات والألعاب)
- [X] T017 [US1] Implement update_progress_for_apps() function in main.py to update progress bar with current part number and overall progress percentage
- [X] T018 [US1] Implement show_completion_summary() function in main.py to display completion message with file count, total size, and save location
- [X] T019 [US1] Add threading support in main.py to run downloads in background thread (threading.Thread with daemon=True)
- [X] T020 [US1] Implement get_vodu_store_html() function in main.py to fetch Vodu store page HTML via Selenium

**Checkpoint**: At this point, User Story 1 should be fully functional - users can download complete multi-part games with progress tracking

---

## Phase 4: User Story 2 - Resume Interrupted Downloads (Priority: P2)

**Goal**: Enable users to resume interrupted downloads by skipping completed parts and resuming incomplete files from last byte.

**Independent Test**: Start download, interrupt after 1-2 parts, restart with same URL. Verify completed parts are skipped and download resumes from first incomplete part.

### Implementation for User Story 2

- [X] T021 [US2] Implement check_existing_part() function in main.py to detect if part already exists and matches expected size
- [X] T022 [US2] Implement http_range_request() function in main.py to resume incomplete files using Range header (bytes=X-)
- [X] T023 [US2] Modify download_part_with_resume() function in main.py to support HTTP range requests for incomplete files
- [X] T024 [US2] Implement load_session_for_resume() function in main.py to load existing session from JSON and skip completed parts
- [X] T025 [US2] Implement save_session_checkpoint() function in main.py to save session state after each part completion
- [X] T026 [US2] Add resume logic to download_apps_games_worker() function in main.py to check for existing parts before downloading
- [X] T027 [US2] Create .vodu_downloader directory in user home if not exists (use os.path.expanduser("~"))
- [X] T028 [US2] Implement update_session_after_part() function in main.py to update session progress and save to JSON after each part

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - downloads can be resumed after interruption

---

## Phase 5: User Story 3 - Handle Download Errors and Retry Logic (Priority: P3)

**Goal**: Automatically retry failed download parts up to 3 times with 5-second delays, preserving successfully downloaded parts.

**Independent Test**: Simulate network failure during part download, verify automatic retry up to 3 times with delays, preserve successful parts.

### Implementation for User Story 3

- [X] T029 [US3] Implement retry_download_part() function in main.py with retry logic (max 3 attempts, 5-second delays)
- [X] T030 [US3] Modify download_part_with_resume() function in main.py to call retry_download_part() on failure
- [X] T031 [US3] Implement handle_part_failure() function in main.py to mark part as failed after max retries and log error
- [X] T032 [US3] Implement get_part_error_message() function in main.py to generate clear error messages (bilingual: English/Arabic)
- [X] T033 [US3] Modify download_apps_games_worker() function in main.py to continue to next part after retry failures
- [X] T034 [US3] Implement show_partial_completion_summary() function in main.py to display summary of successful vs failed parts
- [X] T035 [US3] Add error handling for disk full scenarios in check_disk_space() function in main.py
- [X] T036 [US3] Add error handling for permission denied scenarios in download_part_with_resume() function in main.py
- [X] T037 [US3] Implement validate_file_integrity() function in main.py to compare downloaded file size with expected size from Content-Length header

**Checkpoint**: All user stories should now be independently functional - complete multi-part download flow with resume and error recovery

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Update README.md to add "Apps and Games Download" section with usage instructions and example URLs
- [X] T039 Add bilingual error messages for all error scenarios in main.py (English and Arabic)
- [X] T040 Optimize Selenium startup time in parse_vodu_store_page() function in main.py (reuse driver instance if possible)
- [X] T041 Add logging for download operations in main.py (create log file in .vodu_downloader directory)
- [X] T042 [P] Create test_selenium.py script to verify Selenium and ChromeDriver setup
- [X] T043 Add edge case handling for zero download parts found in extract_download_links() function in main.py
- [X] T044 Add edge case handling for inconsistent part numbering in download_apps_games_worker() function in main.py
- [X] T045 Implement graceful degradation if Vodu store structure changes (fallback error message in parse_vodu_store_page() function in main.py)

**Note**: Selenium not used - implementation uses requests and urllib.request per user requirement.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational (Phase 2) - No dependencies on other stories
  - User Story 2 (P2): Can start after Foundational (Phase 2) - Extends US1 with resume capability
  - User Story 3 (P3): Can start after Foundational (Phase 2) - Extends US1/US2 with retry logic
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Core download functionality, no story dependencies
- **User Story 2 (P2)**: Should be implemented AFTER US1 - Enhances US1 with resume support (requires US1 download functions to exist)
- **User Story 3 (P3)**: Should be implemented AFTER US1 - Enhances US1 with retry logic (requires US1 download functions to exist)

### Within Each User Story

- Foundational functions (dataclasses, enums) before download logic
- Parse functions before download functions
- Download functions before GUI integration
- GUI integration before progress tracking
- Core implementation before enhancements (resume, retry)

### Parallel Opportunities

- **Setup phase**: T002 (install deps) and T003 (test script) can run in parallel
- **Foundational phase**: T005, T006, T007 (JSON functions) can run in parallel; T010, T011 (enums) can run in parallel
- **User Story 1**: T012 (extract links) and T020 (fetch HTML) have no dependencies (can parallelize)
- **User Story 2**: T027 (create directory) can run anytime
- **User Story 3**: T035, T036 (error handlers) can run in parallel
- **Polish phase**: T038, T042 (documentation/test scripts) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch URL extraction and HTML fetching together (different functions):
Task: "Implement extract_download_links() function in main.py"
Task: "Implement get_vodu_store_html() function in main.py"

# Launch dataclass and enum definitions together (in Foundational phase):
Task: "Implement DownloadPart dataclass in main.py"
Task: "Implement DownloadSession dataclass in main.py"
Task: "Implement PartStatus enum in main.py"
Task: "Implement SessionStatus enum in main.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with a real Vodu store URL
5. Deploy/demo if ready (MVP delivers core value: download multi-part games)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Enhanced: resume support)
4. Add User Story 3 → Test independently → Deploy/Demo (Complete: error recovery)
5. Each story adds value without breaking previous stories

### Recommended Execution Order

**For Single Developer** (Sequential):
1. T001-T003: Setup
2. T004-T011: Foundational
3. T012-T020: User Story 1 (MVP - test and validate here!)
4. T021-T028: User Story 2
5. T029-T037: User Story 3
6. T038-T045: Polish

**For Team with 2-3 Developers** (Parallel after Foundational):
1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T012-T020)
   - Developer B: User Story 2 (T021-T028, after US1 functions exist)
   - Developer C: User Story 3 (T029-T037, after US1 functions exist)
3. Stories integrate and complete independently

---

## Notes

- [P] tasks = different files, no dependencies (can run in parallel)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Constitution compliance: All tasks follow Robust Error Handling principle (retry logic, clear errors)
- Threading is critical: Downloads MUST run in background thread (T019)
- Resume checkpoint saves after each part (T025, T028)
- Error messages MUST be bilingual (English/Arabic) per constitution (T039)
- Manual testing required per constitution - see quickstart.md for test scenarios
- Constitution amendment needed: New dependencies (beautifulsoup4, selenium) violate current dependency limits
