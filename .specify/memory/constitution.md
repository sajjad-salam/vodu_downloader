<!--
  SYNC IMPACT REPORT
  ===================
  Version Change: Initial → 1.0.0
  Modified Principles: N/A (initial version)
  Added Sections:
    - Core Principles (5 principles defined)
    - Technical Standards
    - Development Workflow
    - Governance
  Removed Sections: N/A
  Templates Status:
    ✅ plan-template.md - Reviewed, aligns with constitution
    ✅ spec-template.md - Reviewed, aligns with constitution
    ✅ tasks-template.md - Reviewed, aligns with constitution
  Follow-up TODOs: None
-->

# Vodu Downloader Constitution

## Core Principles

### I. User Experience First

The application MUST prioritize simple, intuitive user experience over complex features.

**Rules**:
- GUI MUST be responsive and provide clear feedback for all operations (progress bars, status messages)
- ALL error messages MUST be user-friendly and actionable (no raw stack traces to end users)
- Critical operations (downloads, URL opening) MUST require user confirmation before execution
- UI MUST support bilingual labels (English and Arabic) as appropriate for the user base
- Default settings SHOULD be sensible for typical use cases (360p quality, all seasons)

**Rationale**: This is a desktop tool used by non-technical users. Clarity and predictability are more important than advanced features.

### II. Robust Error Handling

The application MUST handle network failures gracefully and never crash due to temporary issues.

**Rules**:
- ALL download operations MUST implement retry logic with exponential backoff (max 3 retries)
- Network failures MUST be logged with sufficient detail for debugging
- Incomplete downloads MUST be detected and resumed or restarted
- File system errors (permission denied, disk full) MUST be caught and presented clearly
- Invalid URLs or missing content MUST be detected early with clear error messages

**Rationale**: Downloading content over unreliable networks requires defensive programming. Users should not see cryptic errors.

### III. Content Organization

Downloaded content MUST be organized automatically to prevent clutter and confusion.

**Rules**:
- TV series episodes MUST be grouped into season folders (format: `{Series_Name}_Season_{NN}`)
- Movies and standalone videos MUST be saved directly to the selected download path
- Subtitle filenames MUST match their corresponding video files for easy association
- File names MUST preserve the original naming scheme from the source (Series_S##E##_quality)
- Folder structure creation MUST NOT fail if folders already exist (use os.makedirs with exist_ok=True)

**Rationale**: Users downloading multiple seasons need organized output. Manual organization is error-prone and time-consuming.

### IV. Quality Selection Flexibility

The application MUST support multiple quality options to accommodate different bandwidth and storage constraints.

**Rules**:
- Supported qualities: 360p, 720p, 1080p
- Quality selection MUST persist across sessions (default to 360p for compatibility)
- If a specific quality is not available, the app MUST inform the user rather than silently falling back
- Quality patterns MUST match the flexible URL schemes used by vodu.me (support -360, _360, -360p, _360p variations)
- Quality selection applies uniformly to all episodes in a batch download

**Rationale**: Users have varying internet speeds and storage limits. The tool must accommodate these constraints without guesswork.

### V. Season Granularity

The application MUST allow users to download specific seasons rather than forcing all-or-nothing downloads.

**Rules**:
- Users MUST be able to select: "All Seasons" or individual seasons (S1-S10, extensible)
- Season filtering MUST occur before download starts (no wasted bandwidth)
- Season information MUST be extracted from filenames using regex pattern `_S(\d+)E\d+`
- If no videos match the selected season, display a clear message suggesting available seasons
- Opening URLs in browser MUST respect season selection to prevent opening hundreds of tabs

**Rationale**: Users often want to catch up on specific seasons or re-watch particular content. Selective downloading saves time and bandwidth.

## Technical Standards

### Technology Stack

- **Language**: Python 3.9+ (tested on 3.9.7)
- **GUI Framework**: tkinter (included with Python)
- **HTTP Client**: requests library with streaming support
- **Progress Display**: tqdm for download progress bars
- **Platform**: Windows (primary), with potential for cross-platform support

### Code Organization

```
vodu_downloader/
├── main.py                 # Entry point, GUI setup, event handlers
├── gui/                    # GUI assets (images, icons)
│   └── assets/
├── requirements.txt        # Python dependencies
└── README.md              # User-facing documentation
```

### Dependency Management

- ALL dependencies MUST be listed in requirements.txt
- Third-party dependencies MUST be limited to: requests, tqdm, urllib3
- Standard library usage preferred over external packages where possible

## Development Workflow

### Feature Addition Process

1. **Specification**: Create feature spec using `/speckit.specify` with clear user scenarios
2. **Planning**: Execute `/speckit.plan` to generate technical design and implementation approach
3. **Task Breakdown**: Run `/speckit.tasks` to create actionable, dependency-ordered task list
4. **Implementation**: Follow tasks.md sequentially, marking items complete as you progress
5. **Validation**: Test features manually against acceptance scenarios in spec.md

### Code Quality Standards

- Function length SHOULD be under 50 lines (extract helpers if longer)
- Functions MUST have single, clear responsibilities
- Comments MUST explain "why", not "what" (code should be self-documenting)
- Arabic comments in code are acceptable for team context but English is preferred for clarity
- Global state MUST be minimized (pass parameters explicitly where possible)

### Testing Approach

- Manual testing REQUIRED for all GUI interactions
- Network failure scenarios SHOULD be tested (simulate network issues)
- Edge cases MUST be validated: empty URLs, invalid URLs, disk full, permission errors
- Multi-scenario testing: different seasons, qualities, series types

## Governance

### Amendment Process

1. Amendments MUST be proposed via pull request with clear rationale
2. Constitution version MUST follow semantic versioning (MAJOR.MINOR.PATCH)
3. All dependent templates MUST be reviewed and updated when constitution changes
4. Changes to core principles require MAJOR version bump
5. Adding new principles or sections requires MINOR version bump
6. Clarifications and wording improvements require PATCH version bump

### Compliance Review

- ALL pull requests MUST verify compliance with current constitution
- Features violating principles MUST have documented justification in plan.md Complexity Tracking table
- When in doubt, favor simplicity over features (YAGNI - You Aren't Gonna Need It)

### Version History

- **1.0.0** (2025-01-15): Initial constitution establishing core principles for Vodu Downloader project

**Version**: 1.0.0 | **Ratified**: 2025-01-15 | **Last Amended**: 2025-01-15
