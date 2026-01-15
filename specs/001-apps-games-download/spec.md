# Feature Specification: Apps and Games Download Support

**Feature Branch**: `001-apps-games-download`
**Created**: 2025-01-15
**Status**: Draft
**Input**: User description: "we want to add new section it is download apps and games in the main.py the url the user will give it like this https://share.vodu.store/#/details/214620 try to analyze the html file there is button with name تحميل and there is many buttons in the page html because there is many part in the app or game so the script main.py will download all files the url download like this https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar also the script main.py in this new feature we want it support to resume downloading when the internet back"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download Apps and Games with All Parts (Priority: P1)

User wants to download a large game or application that is split into multiple parts (e.g., Marvel's Spider-Man 2 with parts 01, 02, 03, etc.) from the Vodu store. The user provides the Vodu store details page URL, and the application automatically finds all download links (buttons labeled "تحميل" - "Download") and downloads all parts sequentially to the selected location.

**Why this priority**: This is the core functionality - without the ability to download multi-part apps/games, the feature provides no value to users. This is the primary use case that differentiates apps/games from simple video downloads.

**Independent Test**: Can be fully tested by providing a Vodu store URL for a multi-part game, verifying that all download parts are discovered, downloaded sequentially with progress tracking, and saved to the selected directory. Delivers complete game files ready for installation.

**Acceptance Scenarios**:

1. **Given** the user has entered a valid Vodu store URL (e.g., `https://share.vodu.store/#/details/214620`), **When** the user clicks "Download Apps/Games" and selects a download location, **Then** the application analyzes the page, finds all "تحميل" buttons, extracts all download URLs (e.g., `https://share.vodu.store:9999/store-files/Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar`, `part02.rar`, etc.), and downloads all files sequentially with progress indication for each part.
2. **Given** a download is in progress, **When** the user views the progress bar, **Then** they see the current part being downloaded (e.g., "Downloading part 2 of 5: Marvels-SpiderMan-2-part02.rar"), the overall progress across all parts, and estimated time remaining.
3. **Given** all parts have been successfully downloaded, **When** the download completes, **Then** the user receives a completion message showing the total number of files downloaded, total size, and location where files were saved.

---

### User Story 2 - Resume Interrupted Downloads (Priority: P2)

User's internet connection drops during a large multi-part game download (e.g., after downloading 3 of 5 parts). When internet is restored and the user restarts the application or clicks download again with the same URL, the application detects which parts have already been fully downloaded and skips them, continuing from the first incomplete or missing part.

**Why this priority**: Resume capability is critical for large downloads (games can be 50GB+ split across multiple parts). Without this, users would waste bandwidth re-downloading completed parts and likely abandon the feature entirely. However, it's P2 because users can retry manually if needed, though with poor user experience.

**Independent Test**: Can be tested by starting a download, interrupting it (disconnect internet or close application) after 1-2 parts complete, then restarting the download with the same URL. Verify that completed parts are skipped and download resumes from the first incomplete part. Delivers bandwidth savings and faster completion of interrupted downloads.

**Acceptance Scenarios**:

1. **Given** a previous download was interrupted after completing 2 of 5 parts, **When** the user initiates download again with the same Vodu store URL to the same location, **Then** the application detects that parts 1 and 2 are fully downloaded (matching expected file sizes), skips them, and begins downloading from part 3.
2. **Given** a partially downloaded file exists (download interrupted mid-file), **When** the user resumes the download, **Then** the application checks the existing file size and resumes download from the last byte downloaded, avoiding re-downloading the first portion of the file.
3. **Given** the user selects a different download location than the previous attempt, **When** the download starts, **Then** the application downloads all parts from scratch (does not attempt to resume from different location).

---

### User Story 3 - Handle Download Errors and Retry Logic (Priority: P3)

During download, a temporary network error occurs for one part (e.g., part 3 of 5 fails due to connection timeout). The application automatically retries the failed part up to 3 times with delays between attempts before giving up and reporting an error to the user.

**Why this priority**: This is P3 because it's an enhancement to reliability - the core download functionality works without it, but users will encounter frustration with transient failures. The existing video download feature already has retry logic, so this maintains consistency across the application.

**Independent Test**: Can be tested by simulating network failures (disconnect internet momentarily during a part download) or by using a URL that temporarily fails. Verify that the application retries the failed part automatically up to 3 times before reporting an error, and that successfully downloaded parts are preserved. Delivers improved reliability and fewer failed downloads.

**Acceptance Scenarios**:

1. **Given** a download part fails due to network timeout, **When** the error occurs, **Then** the application waits 5 seconds and automatically retries the same part up to 3 times before marking it as failed.
2. **Given** a part fails after all retry attempts, **When** the failure is confirmed, **Then** the application displays a clear error message to the user indicating which part failed (e.g., "Failed to download part 3 after 3 attempts"), preserves any successfully downloaded parts, and offers the user the option to retry later.
3. **Given** a retry attempt succeeds, **When** the download resumes, **Then** the application continues with the next part in sequence and updates the progress bar accordingly.

---

### Edge Cases

- What happens when the Vodu store URL is invalid or the page doesn't exist?
- What happens when the page structure changes and "تحميل" buttons cannot be found?
- What happens when some download URLs are invalid or return 404 errors?
- What happens when the user's disk runs out of space mid-download?
- What happens when the user doesn't have write permissions to the selected download location?
- What happens when download parts are inconsistent (e.g., missing part 3, has parts 1, 2, 4, 5)?
- What happens when the downloaded file is corrupted or doesn't match expected size?
- What happens when the user tries to download to a location with existing partial files from a different app/game?
- What happens when the Vodu store server rate-limits or blocks the download requests?
- What happens when a single part download takes more than 30 minutes (very large file)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept Vodu store URLs in the format `https://share.vodu.store/#/details/[ID]` from the user via a text input field.
- **FR-002**: System MUST analyze the HTML content of the Vodu store details page to find all elements/buttons containing the text "تحميل" (Download).
- **FR-003**: System MUST extract download URLs from the "تحميل" button links, which follow the pattern `https://share.vodu.store:9999/store-files/[filename]`.
- **FR-004**: System MUST download all discovered parts sequentially when the user initiates the download.
- **FR-005**: System MUST allow the user to select a download location via a directory picker dialog.
- **FR-006**: System MUST display download progress showing current part number (e.g., "Part 2 of 5"), current part filename, overall progress percentage, and estimated time remaining.
- **FR-007**: System MUST support resuming interrupted downloads by detecting already-downloaded files and skipping them based on filename and file size matching expected size.
- **FR-008**: System MUST support resuming incomplete file downloads by checking existing file size and continuing from the last downloaded byte using HTTP range requests.
- **FR-009**: System MUST implement retry logic for failed downloads with up to 3 attempts and 5-second delays between retries.
- **FR-010**: System MUST provide clear error messages for download failures, specifying which part failed and the reason (e.g., network error, server error, disk full).
- **FR-011**: System MUST preserve successfully downloaded parts even if later parts fail, allowing users to retry only failed parts.
- **FR-012**: System MUST validate that downloaded files match expected sizes (from Content-Length header) and report corruption if sizes don't match.
- **FR-013**: System MUST handle disk space errors by checking available space before download and alerting the user if insufficient space exists.
- **FR-014**: System MUST organize downloaded files in the user-selected directory without creating additional subdirectories (unlike video downloads which create season folders).
- **FR-015**: System MUST display a completion summary after successful download showing number of files, total size, and save location.

### Key Entities

- **Vodu Store Page**: Represents the web page at `https://share.vodu.store/#/details/[ID]` containing download links for an app or game. Key attributes: page URL, page ID, list of download parts (URLs, filenames, sizes).
- **Download Part**: Represents a single file component of a multi-part app/game download. Key attributes: part URL, part filename (e.g., `Marvels-SpiderMan-2-v1-526--DODI-Repack--part01.rar`), part size, download status (pending, in-progress, completed, failed), bytes downloaded.
- **Download Session**: Represents a complete multi-part download operation for one app/game. Key attributes: session ID (from Vodu store URL), list of parts, download location, overall progress, status (downloading, completed, partially-completed, failed), retry count.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully download all parts of a multi-part game or app by providing only the Vodu store URL, with 100% of parts downloaded and saved to the selected location.
- **SC-002**: Resume functionality correctly skips already-downloaded parts and resumes incomplete parts, reducing download time for interrupted sessions by 100% of the size of completed parts (no re-downloading of completed content).
- **SC-003**: Download progress updates in real-time, with progress bar refresh rate at least 2 times per second, providing current part, overall percentage, and time remaining estimates.
- **SC-004**: Error messages are clear and actionable, with 95% of users able to understand what went wrong (which part failed, why) without needing additional documentation.
- **SC-005**: Retry logic successfully recovers from transient network failures in at least 80% of cases, avoiding unnecessary user intervention for temporary issues.
- **SC-006**: Users can complete a typical 5-part game download (approximately 50GB total) with no more than 5% of users experiencing unrecoverable errors that require manual intervention.
- **SC-007**: The download feature integrates seamlessly into the existing Vodu Downloader interface, with users able to switch between video downloads and app/game downloads without confusion or additional training.
