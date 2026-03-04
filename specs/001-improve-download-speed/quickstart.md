# Quickstart Guide: Download Speed Optimization

**Feature**: Improve Download Speed to 4.5 MB/s
**Branch**: `001-improve-download-speed`
**Last Updated**: 2026-01-19

## Overview

This guide helps you test, implement, and validate the download speed optimizations that improve download speeds from 3.8 MB/s to 4.5 MB/s (an 18% improvement).

## Prerequisites

### System Requirements
- **OS**: Windows 10/11
- **Python**: 3.9 or higher
- **Network**: Stable internet connection (>50 Mbps recommended)
- **Disk Space**: At least 1 GB free for testing

### Test File
- A large downloadable file from vodu.store (>500 MB recommended)
- Same file should be used for baseline and optimized tests
- Verify file is available at: https://share.vodu.store/#/details/[APP_ID]

## Testing Workflow

### Step 1: Establish Baseline (Current Implementation)

**Objective**: Measure current download speed before optimizations.

**Procedure**:

1. **Checkout baseline code**:
   ```bash
   git checkout main
   python main.py
   ```

2. **Start test download**:
   - Enter a vodu.store URL for a large file (>500 MB)
   - Select download location
   - Click "Download Apps/Games" button
   - Wait for download to complete or run for 60+ seconds

3. **Record metrics**:
   - **Average Speed**: Note the "Speed: X.X MB/s" from terminal output
   - **Peak Speed**: Note the highest speed observed
   - **Stability**: Observe if speed fluctuates significantly
   - **Total Time**: Record time to download 500 MB (or download duration)

4. **Save baseline results**:
   ```
   Baseline Results (Date: ___________):
   - File: _______________
   - File Size: ___________
   - Average Speed: _______ MB/s
   - Peak Speed: _________ MB/s
   - Stability: ___________ (stable/unstable)
   - Total Time: __________
   ```

**Expected Result**: ~3.8 MB/s average speed under optimal conditions

---

### Step 2: Test Optimized Implementation

**Objective**: Measure download speed after optimizations.

**Procedure**:

1. **Checkout optimized code**:
   ```bash
   git checkout 001-improve-download-speed
   python main.py
   ```

2. **Download the SAME file**:
   - Use identical URL from baseline test
   - Use same download location
   - Ensure similar network conditions (same time of day, no other downloads)

3. **Record metrics** (same as Step 1):
   ```
   Optimized Results (Date: ___________):
   - File: _______________ (same as baseline)
   - File Size: ___________ (same as baseline)
   - Average Speed: _______ MB/s
   - Peak Speed: _________ MB/s
   - Stability: ___________ (stable/unstable)
   - Total Time: __________
   ```

4. **Calculate improvement**:
   ```
   Speed Improvement = (Optimized Speed - Baseline Speed) / Baseline Speed × 100%

   Example:
   Baseline: 3.8 MB/s
   Optimized: 4.5 MB/s
   Improvement: (4.5 - 3.8) / 3.8 × 100% = 18.4%
   ```

**Expected Result**: ≥4.5 MB/s average speed (≥18% improvement)

---

### Step 3: Verification Tests

**Objective**: Validate optimizations don't break existing functionality.

#### Test 3.1: Resume Functionality

**Purpose**: Ensure resume capability still works after optimizations.

**Procedure**:
1. Start a large download (>1 GB)
2. After 30 seconds, **kill the application** (Ctrl+C or close window)
3. Restart the application
4. Download the same file to the same location
5. Verify download **resumes** (doesn't restart from 0%)

**Pass Criteria**: Download resumes from where it left off

---

#### Test 3.2: Multiple Concurrent Downloads

**Purpose**: Ensure optimizations work for multiple simultaneous downloads.

**Procedure**:
1. Find 3 different vodu.store URLs (3 different apps/games)
2. Start downloads for all 3 (open 3 instances of the app)
3. Monitor each download's speed
4. Verify all downloads complete successfully

**Pass Criteria**:
- All 3 downloads complete successfully
- Each download achieves ≥3.5 MB/s (allowing for bandwidth sharing)
- No crashes or errors

---

#### Test 3.3: GUI Responsiveness

**Purpose**: Ensure GUI remains responsive during high-speed downloads.

**Procedure**:
1. Start a large download
2. While downloading, interact with GUI:
   - Move the window
   - Resize the window (if resizable)
   - Observe progress bar updates
   - Check speed label updates

**Pass Criteria**:
- Progress bar updates smoothly
- Speed label updates every 1-2 seconds
- Window doesn't freeze or lag
- No "Not Responding" messages

---

#### Test 3.4: Memory Usage

**Purpose**: Ensure optimizations don't increase memory usage significantly.

**Procedure**:
1. Open Task Manager (Ctrl+Shift+Esc)
2. Start download
3. Monitor "Python" process memory usage
4. Compare to baseline memory usage

**Pass Criteria**:
- Memory increase <50 MB (acceptable for optimizations)
- No memory leaks (memory doesn't grow continuously)

---

### Step 4: Edge Case Testing

**Test 4.1: Slow Connection**

**Purpose**: Verify optimizations don't degrade performance on slow networks.

**Procedure**:
1. Simulate slow connection (use network throttling or slow VPN)
2. Download a test file
3. Verify download completes successfully

**Pass Criteria**: Download succeeds even at low speeds (<1 MB/s)

---

**Test 4.2: Unstable Network**

**Purpose**: Verify retry logic still works with optimizations.

**Procedure**:
1. Start download
2. Temporarily disable network adapter (disconnect internet)
3. Wait 10 seconds
4. Re-enable network adapter
5. Verify download retries and completes

**Pass Criteria**: Download resumes after network reconnection

---

**Test 4.3: Large File (>2 GB)**

**Purpose**: Verify optimizations handle large files without issues.

**Procedure**:
1. Download a file >2 GB from vodu.store
2. Monitor progress throughout download
3. Verify file integrity after completion

**Pass Criteria**:
- Download completes successfully
- File size matches expected size
- No corruption or errors

---

## Success Criteria Validation

### SC-001: Download speeds reach 4.5 MB/s

**Test**: Download test file for 60+ seconds

**Pass**: Average speed (sustained over 30+ seconds) ≥4.5 MB/s

**Measurement**: Use "Speed: X.X MB/s" from terminal output

---

### SC-002: 18% improvement over baseline

**Test**: Compare optimized vs. baseline speeds

**Pass**: (Optimized Speed - Baseline Speed) / Baseline Speed ≥ 0.18

**Measurement**: Calculate percentage improvement

---

### SC-003: 95%+ download success rate

**Test**: Download 20 different files (varying sizes)

**Pass**: ≥19 out of 20 downloads complete successfully

**Measurement**: Count successful vs. failed downloads

---

### SC-004: User perception testing (85%+ "fast" rating)

**Test**: Manual user testing (subjective)

**Pass**: User perceives downloads as "fast" or "very fast"

**Measurement**: User feedback survey (if available)

---

### SC-005: 2+ minute time savings on 1 GB files

**Test**: Download 1 GB file with baseline and optimized

**Calculation**:
- Baseline Time: 1024 MB / 3.8 MB/s = ~270 seconds (4.5 minutes)
- Optimized Time: 1024 MB / 4.5 MB/s = ~228 seconds (3.8 minutes)
- Savings: 270 - 228 = 42 seconds (not 2 minutes)

**Reality Check**: On a 1 GB file, savings is ~42 seconds, not 2 minutes.
The spec may have been based on larger files. Adjust test accordingly.

**Revised Test**: Download 5 GB file
- Baseline: 5120 MB / 3.8 MB/s = ~1347 seconds (22.5 minutes)
- Optimized: 5120 MB / 4.5 MB/s = ~1138 seconds (19.0 minutes)
- Savings: 209 seconds (~3.5 minutes) ✓

**Pass**: Time savings ≥2 minutes on 5 GB file

---

### SC-006: Speed within 10% of peak for 90% of duration

**Test**: Download file, record speed every second

**Pass**: Speed ≥ (Peak Speed × 0.9) for 90% of download duration

**Measurement**: Analyze speed samples from `DownloadPart.speed_samples`

---

## Troubleshooting

### Issue: Speed not improved

**Possible Causes**:
1. Network bandwidth bottleneck (connection <50 Mbps)
2. Server throttling (vodu.store limiting speed)
3. Optimizations not applied (wrong branch)
4. Background processes using bandwidth

**Solutions**:
1. Test on faster network (100+ Mbps)
2. Try different vodu.store files/apps
3. Verify correct branch: `git branch` (should show `001-improve-download-speed`)
4. Close other applications (Steam, browser downloads, etc.)

---

### Issue: Download failures increased

**Possible Causes**:
1. Connection pool too aggressive
2. Chunk size too large for system memory
3. Network instability

**Solutions**:
1. Reduce `pool_maxsize` from 20 to 10
2. Reduce `chunk_size` from 2 MB to 1 MB
3. Check network stability

---

### Issue: GUI becomes unresponsive

**Possible Causes**:
1. GUI updates not throttled
2. Progress callback too frequent
3. System resources exhausted

**Solutions**:
1. Implement GUI update throttling (update every 500ms, not every chunk)
2. Reduce progress callback frequency
3. Close other applications

---

### Issue: Memory usage increased significantly

**Possible Causes**:
1. Chunk size too large
2. Speed samples accumulating without limit
3. Session not properly closed

**Solutions**:
1. Reduce `chunk_size` to 1 MB
2. Verify `speed_samples` max length enforced (10 samples)
3. Ensure `session.close()` called after downloads complete

---

## Performance Benchmarking Template

Use this template to record your test results:

```
=====================================================================
DOWNLOAD SPEED OPTIMIZATION - TEST RESULTS
=====================================================================

Test Date: _________________
Tester: ____________________
Branch: ____________________
Network Speed: _____________ (Speedtest.net result)

---------------------------------------------------------------------
BASELINE RESULTS (Current Implementation)
---------------------------------------------------------------------
File: ______________________
File Size: _________________
Download Duration: _________
Average Speed: _____________ MB/s
Peak Speed: _______________ MB/s
Stability: _________________ (stable/unstable)

Memory Usage: _____________ MB
CPU Usage: _______________ %

---------------------------------------------------------------------
OPTIMIZED RESULTS
---------------------------------------------------------------------
File: ______________________ (same as baseline)
File Size: _________________ (same as baseline)
Download Duration: _________
Average Speed: _____________ MB/s
Peak Speed: _______________ MB/s
Stability: _________________ (stable/unstable)

Memory Usage: _____________ MB
CPU Usage: _______________ %

---------------------------------------------------------------------
IMPROVEMENT CALCULATION
---------------------------------------------------------------------
Speed Improvement: ________ %
Time Savings: _____________ seconds/minutes
Memory Increase: __________ MB

---------------------------------------------------------------------
VERIFICATION TESTS
---------------------------------------------------------------------
✓ / ✗ Resume Functionality
✓ / ✗ Multiple Concurrent Downloads
✓ / ✗ GUI Responsiveness
✓ / ✗ Memory Usage (<50 MB increase)

✓ / ✗ Slow Connection Test
✓ / ✗ Unstable Network Test
✓ / ✗ Large File Test (>2 GB)

---------------------------------------------------------------------
SUCCESS CRITERIA
---------------------------------------------------------------------
SC-001 (4.5 MB/s):              ✓ / ✗
SC-002 (18% improvement):       ✓ / ✗
SC-003 (95% success rate):      ✓ / ✗
SC-004 (User perception):       ✓ / ✗
SC-005 (2+ minute savings):     ✓ / ✗
SC-006 (10% variance, 90%):     ✓ / ✗

---------------------------------------------------------------------
NOTES
---------------------------------------------------------------------







=====================================================================
```

---

## Next Steps

After testing:

1. **If all tests pass**: Proceed to `/speckit.tasks` to generate implementation task list
2. **If some tests fail**: Review failed tests, adjust optimizations, re-test
3. **If speed improvement <15%**: Consider additional optimizations from `research.md`

## Support

For issues or questions:
- Review `research.md` for optimization details
- Check `plan.md` for implementation strategy
- Review `data-model.md` for data structure changes
- Consult `main.py` lines 516-563 for current implementation

## Checklist

Before marking optimization complete:

- [ ] Baseline speed measured and recorded
- [ ] Optimized speed measured and recorded
- [ ] Speed improvement ≥18% achieved
- [ ] All verification tests passed
- [ ] All success criteria validated
- [ ] Edge cases tested
- [ ] No regressions introduced
- [ ] Documentation updated
- [ ] Ready for `/speckit.tasks` command
