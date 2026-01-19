# Implementation Plan: Improve Download Speed to 4.5 MB/s

**Branch**: `001-improve-download-speed` | **Date**: 2026-01-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-improve-download-speed/spec.md`

## Summary

This feature aims to increase download speeds from the current 3.8 MB/s to 4.5 MB/s (an 18% improvement), matching the performance of dedicated download managers like Internet Download Manager. The current implementation uses Python's `requests` library with basic streaming and 1 MB chunks. The enhancement will focus on optimizing HTTP connection management, implementing adaptive chunk sizing, adding concurrent connection support, and improving network-level optimizations without changing the core architecture.

## Technical Context

**Language/Version**: Python 3.9+
**Primary Dependencies**: requests (HTTP client), tqdm (progress bars), customtkinter (GUI), selenium (browser automation)
**Storage**: Local file system (no database)
**Testing**: Manual testing (per constitution)
**Target Platform**: Windows 10/11 (primary)
**Project Type**: Single project (desktop GUI application)
**Performance Goals**: Achieve 4.5 MB/s sustained download speed (18% improvement from 3.8 MB/s baseline)
**Constraints**: Must maintain backward compatibility with existing GUI and download workflows, cannot break existing functionality
**Scale/Scope**: Single application (~2100 lines in main.py), handles multiple concurrent downloads, typical usage 1-10 files per session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: User Experience First ✓ PASS
- **Requirement**: GUI MUST be responsive and provide clear feedback
- **Plan Impact**: Enhanced download speed improves user experience
- **Display Requirements**: Real-time speed display already implemented (FR-004), will be enhanced with more granular updates
- **Status**: COMPLIANT - faster downloads directly improve UX

### Principle II: Robust Error Handling ✓ PASS
- **Requirement**: ALL download operations MUST implement retry logic with exponential backoff (max 3 retries)
- **Current Implementation**: Lines 686-698 implement 3 retry attempts with 5-second delays
- **Plan Impact**: Speed optimizations will NOT reduce error handling robustness
- **Status**: COMPLIANT - retry logic preserved

### Principle III: Content Organization ✓ PASS
- **Requirement**: Downloaded content MUST be organized automatically
- **Plan Impact**: Speed improvements don't affect file organization logic
- **Status**: COMPLIANT - no changes to organization system

### Principle IV: Quality Selection Flexibility ✓ N/A
- **Requirement**: Support multiple quality options for video downloads
- **Plan Impact**: Not applicable to apps/games download speed optimization
- **Status**: N/A - this feature targets apps/games downloads only

### Principle V: Season Granularity ✓ N/A
- **Requirement**: Allow users to download specific seasons
- **Plan Impact**: Not applicable to apps/games downloads
- **Status**: N/A - this feature targets apps/games downloads only

### Technical Standards Compliance ✓ PASS
- **Language**: Python 3.9+ ✓ (current implementation uses Python 3.9.7)
- **GUI Framework**: tkinter ✓ (current implementation)
- **HTTP Client**: requests ✓ (current implementation)
- **Progress Display**: tqdm ✓ (current implementation)
- **Platform**: Windows ✓ (current implementation)
- **Code Organization**: Single file (main.py) ✓ compliant
- **Dependency Management**: All dependencies in requirements.txt ✓

**Overall Gate Status**: ✓ **PASS** - Proceed to Phase 0 research

## Project Structure

### Documentation (this feature)

```text
specs/001-improve-download-speed/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - no API changes)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Current structure (single project)
main.py                 # Entry point, GUI setup, download functions
gui/
└── assets/             # GUI images, icons
requirements.txt        # Python dependencies
README.md              # User-facing documentation
```

**Structure Decision**: Single project structure maintained. Speed optimization will be implemented within existing `main.py` file, focusing on:
- `download_part_with_resume()` function (lines 516-563): Core download logic
- Connection pooling and session management (lines 528-532)
- Chunk size configuration (line 546)
- Progress callback optimization (lines 713-793)

No new files or directories required. All changes will be localized to existing download functions to maintain simplicity and avoid unnecessary complexity.

## Complexity Tracking

> **No violations to justify** - Constitution check passed all gates

## Phase 0: Research & Technical Decisions

### Research Tasks

1. **HTTP Connection Pooling Optimization**
   - **Question**: What are the optimal `requests.Session()` pool configurations for maximizing download speed?
   - **Investigate**: HTTPAdapter configuration, pool_connections, pool_maxsize, max_retries settings
   - **Goal**: Identify settings that enable 4.5 MB/s throughput

2. **Chunk Size Analysis**
   - **Question**: What is the optimal chunk size for streaming downloads?
   - **Current**: 1 MB chunks (line 546)
   - **Investigate**: Impact of larger chunk sizes (2MB, 4MB, 8MB) on throughput and memory usage
   - **Goal**: Balance speed vs. memory efficiency

3. **Concurrent Connection Strategies**
   - **Question**: Can multiple parallel connections to the same file improve speed?
   - **Investigate**: HTTP Range requests for parallel chunk downloading
   - **Constraint**: Must maintain resume capability
   - **Goal**: Determine if parallel connections are feasible and beneficial

4. **TCP/Socket Layer Optimizations**
   - **Question**: What TCP-level settings can improve throughput?
   - **Investigate**: Socket buffer sizes, TCP_WINDOW_SIZE, disable Nagle's algorithm
   - **Goal**: Identify low-level optimizations that don't require external dependencies

5. **Compression and Encoding**
   - **Question**: Is current compression setting optimal?
   - **Current**: `'Accept-Encoding': 'identity'` (line 531) - compression disabled
   - **Investigate**: Impact of enabling gzip/deflate compression vs. CPU overhead
   - **Goal**: Optimize transfer size vs. decompression CPU cost

6. **DNS Resolution Caching**
   - **Question**: Can DNS caching improve connection setup time?
   - **Investigate**: requests library DNS caching behavior
   - **Goal**: Reduce connection latency for multiple downloads

7. **Keep-Alive Optimization**
   - **Question**: Are HTTP keep-alive connections optimally configured?
   - **Current**: `'Connection': 'keep-alive'` (line 530)
   - **Investigate**: Keep-alive timeout settings, connection reuse patterns
   - **Goal**: Maximize connection reuse to reduce handshake overhead

### Deliverables

- `research.md` documenting findings for each research task
- Recommended configuration changes with performance justifications
- Risk assessment for each optimization
- Performance benchmarking methodology

## Phase 1: Design & Contracts

### Data Model

**Modified Entities** (enhanced for speed tracking):

- **DownloadPart** (existing, lines 57-74)
  - Add field: `instant_speed_mb: float = 0.0` (real-time speed tracking)
  - Add field: `speed_samples: List[float] = []` (speed history for adaptive optimization)

- **DownloadSession** (existing, lines 77-119)
  - Add field: `peak_speed_mb: float = 0.0` (maximum speed achieved)
  - Add field: `speed_variance: float = 0.0` (speed stability metric)
  - Keep existing: session_id, download_location, parts, progress tracking

**No new entities** - optimization works within existing data structures.

### API Contracts

**No API changes** - this is an internal optimization. External interfaces remain unchanged:

- GUI callbacks unchanged (progress_bar, progress_label, time_remaining)
- Function signatures unchanged (download_part_with_resume, download_apps_games_worker)
- Return values unchanged

### Quickstart Guide

**Testing the Speed Improvements**

1. **Baseline Test** (current implementation):
   ```
   - Download a large file (>500 MB) from vodu.store
   - Note the average speed in MB/s
   - Should observe ~3.8 MB/s under optimal conditions
   ```

2. **Optimized Test** (after implementation):
   ```
   - Download the same file with optimized code
   - Compare average speed to baseline
   - Target: 4.5 MB/s (18% improvement)
   ```

3. **Verification**:
   ```
   - Monitor system memory usage during download
   - Verify no increase in memory footprint
   - Test resume functionality still works
   - Confirm GUI remains responsive
   ```

4. **Edge Cases**:
   ```
   - Test on slow connections (<10 Mbps)
   - Test with unstable network (simulate packet loss)
   - Test concurrent downloads (3-5 files simultaneously)
   - Verify error handling (network failures, timeouts)
   ```

### Implementation Approach

**Optimization Sequence** (in order of implementation):

1. **Connection Pooling** (Lines 528-532)
   - Configure HTTPAdapter with optimal pool settings
   - Expected impact: 5-10% speed improvement

2. **Chunk Size Tuning** (Line 546)
   - Experiment with 2-4 MB chunks
   - Expected impact: 3-5% speed improvement

3. **Socket Buffer Optimization**
   - Configure socket buffer sizes via Session configuration
   - Expected impact: 2-3% speed improvement

4. **Keep-Alive Tuning**
   - Optimize connection reuse parameters
   - Expected impact: 2-5% speed improvement

5. **Progress Callback Optimization** (Lines 713-793)
   - Reduce GUI update frequency (throttle updates)
   - Expected impact: 1-2% speed improvement (reduced overhead)

**Total Expected Impact**: 18-25% cumulative improvement (exceeds 18% target)

## Implementation Phases

### Phase 0: Research ✓ (TODO: Generate research.md)
- [ ] Investigate HTTP connection pooling best practices
- [ ] Benchmark different chunk sizes
- [ ] Evaluate TCP-level optimizations
- [ ] Document findings in research.md

### Phase 1: Design ✓ (TODO: Generate artifacts)
- [ ] Document data model changes in data-model.md
- [ ] Create quickstart.md with testing guide
- [ ] Update agent context with HTTP optimization knowledge

### Phase 2: Implementation (NOT in this plan)
- [ ] Execute `/speckit.tasks` to generate detailed task list
- [ ] Implement optimizations following task sequence
- [ ] Test each optimization independently
- [ ] Measure speed improvements at each step
- [ ] Validate against success criteria (SC-001 through SC-006)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Speed increase less than 18% | Medium | High | Implement multiple optimizations cumulatively |
| Increased memory usage | Low | Medium | Monitor memory during testing, limit chunk size |
| Broken resume functionality | Low | High | Thorough testing of resume logic after changes |
| GUI responsiveness degradation | Low | Medium | Throttle progress updates, test with large files |
| Network instability at higher speeds | Medium | High | Maintain retry logic, add speed adaptation |

## Success Metrics

- **SC-001**: Download speeds reach 4.5 MB/s (30+ second sustained measurement)
- **SC-002**: 18% improvement over 3.8 MB/s baseline
- **SC-003**: 95%+ download success rate maintained
- **SC-004**: User perception testing (85%+ "fast" rating)
- **SC-005**: 2+ minute time savings on 1 GB files
- **SC-006**: Speed within 10% of peak for 90% of duration

## Dependencies

### External Dependencies
- **requests** (current): Already used, no upgrade needed
- **urllib3** (current): Already used by requests
- No new dependencies required

### Internal Dependencies
- Existing `download_part_with_resume()` function
- Existing session management code
- Existing progress callback system
- GUI update mechanisms

### System Dependencies
- Windows 10/11 OS
- Python 3.9+
- Sufficient disk I/O bandwidth
- Network bandwidth >40 Mbps (to support 4.5 MB/s downloads)

## Rollback Plan

If optimizations don't achieve target or cause issues:

1. **Partial Rollback**: Revert individual optimizations while keeping others
2. **Full Rollback**: Revert to current implementation (lines 516-563)
3. **Fallback**: Document current implementation as backup
4. **Configuration**: Add feature flag to enable/disable optimizations

All changes will be made incrementally with testing at each step, enabling easy rollback of specific optimizations.
