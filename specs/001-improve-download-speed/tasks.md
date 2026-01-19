# Tasks: Improve Download Speed to 4.5 MB/s

**Input**: Design documents from `/specs/001-improve-download-speed/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓

**Tests**: Manual testing per constitution - no automated test tasks included

**Organization**: Tasks are grouped by user story to enable independent implementation and validation of each optimization phase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: All changes in `main.py` (lines 516-563 for download_part_with_resume, lines 584-871 for download_apps_games_worker, lines 713-793 for progress callback)
- **Data model changes**: `main.py` lines 57-74 (DownloadPart), lines 77-119 (DownloadSession)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish baseline and prepare for optimization implementation

- [ ] T001 Create baseline speed measurement by downloading test file (>500 MB) with current implementation and recording average speed in MB/s
- [ ] T002 Document current implementation details in main.py lines 516-563 (download_part_with_resume function)
- [ ] T003 Document current session management approach in main.py lines 528-532
- [ ] T004 Document current chunk size configuration in main.py line 546
- [ ] T005 Document current progress callback implementation in main.py lines 713-793

**Checkpoint**: Baseline established and current implementation documented

---

## Phase 2: Foundational (Data Model Enhancements)

**Purpose**: Enhance data structures to support speed tracking BEFORE implementing optimizations

**⚠️ CRITICAL**: No optimization implementation can begin until this phase is complete

- [x] T006 [P] Add speed tracking fields to DownloadPart dataclass in main.py lines 57-74: instant_speed_mb, speed_samples, last_speed_update
- [x] T007 [P] Add performance metrics fields to DownloadSession dataclass in main.py lines 77-119: peak_speed_mb, average_speed_mb, speed_variance, speed_stability_score
- [x] T008 Implement update_speed_tracking() function to calculate and record speed samples for DownloadPart instances
- [x] T009 Implement calculate_session_metrics() function to aggregate speed metrics from DownloadPart parts into DownloadSession
- [x] T010 Update save_resume_state() function to persist new speed tracking fields to resume_state.json (version bump to 1.1)
- [x] T011 Update load_resume_state() function to load speed tracking fields with backward compatibility for version 1.0

**Checkpoint**: Data model ready - optimization implementation can now begin ✅

---

## Phase 3: User Story 1 - Achieve Maximum Download Speed (Priority: P1) 🎯 MVP

**Goal**: Implement HTTP connection pooling and session reuse optimizations to achieve 4.5 MB/s download speed (18% improvement from 3.8 MB/s baseline)

**Independent Test**: Download same test file used in T001 and verify speed reaches 4.5 MB/s sustained over 30+ seconds

### Implementation for User Story 1

- [x] T012 [P] [US1] Import HTTPAdapter and Retry classes from requests.adapters and urllib3.util.retry at top of main.py
- [x] T013 [P] [US1] Create create_optimized_session() function in main.py to configure session with HTTPAdapter (pool_connections=20, pool_maxsize=20, max_retries=Retry(total=3, backoff_factor=0.1))
- [x] T014 [P] [US1] Modify download_apps_games_worker() function signature to accept optional session parameter
- [x] T015 [US1] Update download_apps_games_worker() to create optimized session if no session provided (around line 589)
- [x] T016 [US1] Mount HTTPAdapter to session for both http:// and https:// in create_optimized_session()
- [x] T017 [US1] Modify download_part_with_resume() function signature to accept optional session parameter (line 516)
- [x] T018 [US1] Update download_part_with_resume() to use provided session or create default session (around line 528)
- [x] T019 [US1] Update download_apps_games_worker() to pass session to download_part_with_resume() calls (around line 794)
- [x] T020 [US1] Add session.close() call in download_apps_games_worker() after all parts complete (around line 842)
- [x] T021 [US1] Integrate speed tracking in download_part_with_resume() by calling update_speed_tracking() every 1 second during download loop
- [x] T022 [US1] Update progress callback (lines 713-793) to display instant_speed_mb from DownloadPart in GUI label
- [ ] T023 [US1] Test connection pooling optimization with single file download and measure speed improvement

**Checkpoint**: At this point, User Story 1 should be fully functional - download speeds should reach 4.5 MB/s ✅

---

## Phase 4: User Story 2 - Maintain Download Stability at Higher Speeds (Priority: P2)

**Goal**: Implement chunk size tuning and GUI throttling optimizations to ensure download stability at 4.5 MB/s speed

**Independent Test**: Download multiple files concurrently and verify all maintain stable speed without failures or significant fluctuations

### Implementation for User Story 2

- [x] T024 [P] [US2] Change chunk_size from 1 MB to 2 MB in download_part_with_resume() function (line 546)
- [ ] T025 [P] [US2] Add chunk size constant at top of main.py for easy tuning: OPTIMAL_CHUNK_SIZE = 2 * 1024 * 1024
- [x] T026 [US2] Implement GUI update throttling in progress callback (lines 713-793) with 500ms throttle interval
- [x] T027 [US2] Add last_gui_update_time variable to track GUI update timing in progress callback scope
- [x] T028 [US2] Wrap GUI update calls (progress_bar, progress_label, progress_canvas) in throttle condition: if current_time - last_gui_update_time >= 0.5
- [ ] T029 [US2] Test chunk size optimization with large file (>1 GB) and monitor memory usage
- [ ] T030 [US2] Test GUI throttling with multiple concurrent downloads and verify GUI remains responsive
- [x] T031 [US2] Call calculate_session_metrics() at end of download_apps_games_worker() to record final session performance metrics
- [ ] T032 [US2] Test download stability with 3-5 concurrent downloads and verify all maintain ≥4.0 MB/s speed

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - downloads are fast AND stable ✅

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validation, edge case handling, and documentation

- [ ] T033 [P] Test resume functionality by interrupting download and verifying it resumes with optimized speed
- [ ] T034 [P] Test slow connection scenario (<10 Mbps) and verify downloads still succeed
- [ ] T035 [P] Test unstable network by disconnecting and reconnecting during download
- [ ] T036 [P] Test edge case: very large file download (>2 GB) and verify memory usage remains acceptable
- [ ] T037 [P] Test edge case: multiple concurrent downloads (5+ files) and verify no significant speed degradation across downloads
- [ ] T038 Run baseline vs optimized comparison test using same file and document speed improvement percentage
- [ ] T039 Validate SC-001: Download speeds reach 4.5 MB/s (30+ second sustained measurement)
- [ ] T040 Validate SC-002: 18% improvement over 3.8 MB/s baseline achieved
- [ ] T041 Validate SC-003: 95%+ download success rate maintained (test 20 downloads)
- [ ] T042 Validate SC-006: Speed within 10% of peak for 90% of download duration
- [ ] T043 Update README.md with performance improvement notes (if applicable)
- [ ] T044 Document rollback procedure in code comments if optimizations need to be disabled

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (data model must be enhanced first)
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion - implements connection pooling optimization
- **User Story 2 (Phase 4)**: Depends on User Story 1 completion - builds on speed optimizations with stability improvements
- **Polish (Phase 5)**: Depends on both user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 completion - stability optimizations build on speed optimizations

### Within Each User Story

- Data model enhancements (Phase 2) MUST be complete before any optimization code
- US1 tasks T012-T022 can proceed in order (session setup before usage)
- US2 tasks T024-T027 can proceed independently (chunk size and GUI throttling are independent)
- All testing tasks (Phase 5) depend on implementation completion

### Parallel Opportunities

- **Phase 1**: All setup tasks can run in parallel
- **Phase 2**: Tasks T006-T007 (data model changes) can run in parallel
- **Phase 3 (US1)**: Tasks T012-T013 (create helper functions) can run in parallel
- **Phase 4 (US2)**: Tasks T024-T025 (chunk size) can run in parallel with T026-T028 (GUI throttling)
- **Phase 5**: All validation tasks T033-T037 can run in parallel once implementation is complete

---

## Parallel Example: User Story 1

```bash
# Launch helper function creation together:
Task: "Create create_optimized_session() function in main.py"
Task: "Import HTTPAdapter and Retry classes at top of main.py"

# After helper functions exist, proceed with integration tasks sequentially
```

---

## Parallel Example: User Story 2

```bash
# Launch chunk size and GUI throttling tasks in parallel:
Task: "Change chunk_size from 1 MB to 2 MB in download_part_with_resume() (line 546)"
Task: "Implement GUI update throttling in progress callback (lines 713-793)"

# Both are independent optimizations affecting different parts of the code
```

---

## Parallel Example: Phase 5 Validation

```bash
# Launch all edge case tests in parallel (if using multiple test machines):
Task: "Test resume functionality by interrupting download"
Task: "Test slow connection scenario (<10 Mbps)"
Task: "Test unstable network by disconnecting/reconnecting"
Task: "Test edge case: very large file download (>2 GB)"
Task: "Test edge case: multiple concurrent downloads (5+ files)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline measurement)
2. Complete Phase 2: Foundational (data model enhancements) - **CRITICAL**
3. Complete Phase 3: User Story 1 (connection pooling optimization)
4. **STOP and VALIDATE**: Test download speed with T023, verify 4.5 MB/s achieved
5. If ≥15% improvement gained, proceed to User Story 2
6. If <15% gained, debug connection pooling implementation before proceeding

### Incremental Delivery

1. Complete Setup + Foundational → Data model ready
2. Add User Story 1 (speed optimization) → Test independently → Verify 4.5 MB/s target (MVP!)
3. Add User Story 2 (stability optimization) → Test independently → Verify stable high-speed downloads
4. Complete Polish phase → Validate all success criteria
5. Each phase adds value without breaking previous work

### Rollback Strategy

If any optimization phase causes issues:
- **T012-T022 (US1)**: Revert session parameter changes, restore original session creation
- **T024-T025 (US2 chunk size)**: Revert chunk_size to 1 MB (1024 * 1024)
- **T026-T028 (US2 GUI throttling)**: Remove throttle condition, restore GUI updates on every chunk
- Individual optimizations can be disabled independently while keeping others

---

## Notes

- **[P] tasks** = different files or independent code sections, no blocking dependencies
- **[Story] label** = maps task to specific user story for traceability
- **Line numbers** refer to current main.py implementation - may shift as code is modified
- **Manual testing** = per constitution, all validation is manual via quickstart.md workflow
- **Commit strategy** = Commit after each task or logical group (e.g., all of US1)
- **Validation checkpoints** = Stop at any checkpoint to test that phase independently
- **Success criteria** = All SC-001 through SC-006 must pass before feature is complete
- **Expected improvement** = 18-25% cumulative (5-10% from US1, 3-5% from US2 chunk size, 1-2% from US2 GUI throttling)
- **Avoid**: Skipping data model enhancements (Phase 2), implementing US2 before US1, changing compression settings without testing
