"""
iOS Design Tokens and Style Constants
Defines the visual design system for the Vodu Downloader iOS-style GUI.
"""

import customtkinter as ctk

# ============================================================================
# Color Palette (iOS Dark Mode)
# ============================================================================

COLORS = {
    # Background colors
    'background': '#000000',           # Pure black (main background)
    'secondary': '#1c1c1e',           # iOS dark gray (cards, elevated surfaces)
    'tertiary': '#2c2c2e',            # iOS elevated surface
    'quaternary': '#3a3a3c',          # iOS border color

    # Accent colors (iOS system colors)
    'accent': '#0a84ff',              # iOS blue (primary action)
    'accent_hover': '#409cff',        # Lighter blue for hover
    'success': '#30d158',             # iOS green
    'warning': '#ff9f0a',             # iOS orange
    'error': '#ff453a',               # iOS red
    'info': '#64d2ff',                # iOS cyan

    # Text colors
    'text_primary': '#ffffff',        # White (primary text)
    'text_secondary': '#8e8e93',      # iOS gray (secondary text)
    'text_tertiary': '#48484a',       # Darker gray (tertiary text)
    'text_quaternary': '#636366',     # Medium gray

    # Glass effect (converted to hex for tkinter compatibility)
    'glass': '#1c1c1e',  # Semi-transparent dark -> solid dark
    'glass_border': '#3a3a3c',  # Subtle border -> quaternary color
    'glass_shadow': '#000000',  # Drop shadow -> black

    # Progress colors
    'progress_start': '#ff453a',      # Red (start)
    'progress_mid': '#ff9f0a',        # Orange (mid)
    'progress_end': '#30d158',        # Green (complete)
}

# ============================================================================
# Typography (iOS-style fonts)
# ============================================================================

# SF Pro alternatives - using system fonts that match iOS
FONTS = {
    # Display fonts (large titles)
    'large_title': ('Segoe UI', 28, 'bold'),      # iOS Large Title
    'title1': ('Segoe UI', 22, 'bold'),           # iOS Title 1
    'title2': ('Segoe UI', 20, 'bold'),           # iOS Title 2
    'title3': ('Segoe UI', 18, 'bold'),           # iOS Title 3

    # Body fonts
    'headline': ('Segoe UI', 17, 'bold'),         # iOS Headline
    'body': ('Segoe UI', 15, 'normal'),           # iOS Body
    'body_emphasized': ('Segoe UI', 15, 'bold'),  # iOS Body Emphasized
    'callout': ('Segoe UI', 14, 'normal'),        # iOS Callout

    # Caption fonts
    'subheadline': ('Segoe UI', 13, 'normal'),    # iOS Subheadline
    'footnote': ('Segoe UI', 11, 'normal'),       # iOS Footnote
    'caption1': ('Segoe UI', 10, 'normal'),       # iOS Caption 1
    'caption2': ('Segoe UI', 10, 'bold'),         # iOS Caption 2

    # Monospace for URLs and code
    'monospace': ('Consolas', 13, 'normal'),
}

# ============================================================================
# Layout Constants
# ============================================================================

SPACING = {
    'xs': 4,    # Tight spacing
    'sm': 8,    # Small spacing
    'md': 16,   # Medium spacing (standard)
    'lg': 24,   # Large spacing
    'xl': 32,   # Extra large spacing
    'xxl': 48,  # Section spacing
}

# ============================================================================
# Corner Radius (iOS-style rounded corners)
# ============================================================================

CORNER_RADIUS = {
    'small': 6,      # Small elements (chips, tags)
    'medium': 10,    # Buttons, inputs
    'large': 14,     # Cards, containers
    'xlarge': 20,    # Large cards, modals
    'xxlarge': 28,   # Special large elements
}

# ============================================================================
# Shadow Effects
# ============================================================================

SHADOWS = {
    'small': {
        'blur': 4,
        'offset': (0, 2),
        'color': 'rgba(0, 0, 0, 0.2)',
    },
    'medium': {
        'blur': 8,
        'offset': (0, 4),
        'color': 'rgba(0, 0, 0, 0.3)',
    },
    'large': {
        'blur': 16,
        'offset': (0, 8),
        'color': 'rgba(0, 0, 0, 0.4)',
    },
}

# ============================================================================
# Animation Durations (in milliseconds)
# ============================================================================

ANIMATION_DURATION = {
    'fast': 150,      # Quick transitions (hover effects)
    'normal': 250,    # Standard transitions
    'slow': 350,      # Deliberate transitions (page changes)
    'slower': 500,    # Very slow transitions (special effects)
}

# ============================================================================
# Icon Characters (using Unicode symbols where possible)
# ============================================================================

ICONS = {
    'download': '⬇',
    'play': '▶',
    'pause': '⏸',
    'stop': '⏹',
    'check': '✓',
    'close': '✕',
    'search': '🔍',
    'settings': '⚙',
    'info': 'ℹ',
    'warning': '⚠',
    'error': '✖',
    'film': '🎬',
    'apps': '📱',
    'browser': '🌐',
    'subtitle': '💬',
    'link': '🔗',
}

# ============================================================================
# Quality Options
# ============================================================================

QUALITIES = ['360p', '720p', '1080p']

# ============================================================================
# Season Options
# ============================================================================

SEASONS = ['All', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10']

# ============================================================================
# CustomTkinter Theme Configuration
# ============================================================================

def configure_ctk_theme():
    """Configure CustomTkinter with iOS dark theme colors."""
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")  # Use "blue" theme as base, we'll override colors

    # Custom colors for CustomTkinter widgets
    CTK_COLORS = {
        'fg': COLORS['background'],           # Foreground (widget color)
        'bg': COLORS['background'],           # Background
        'button': COLORS['accent'],           # Button color
        'button_hover': COLORS['accent_hover'],  # Button hover
        'text': COLORS['text_primary'],       # Text color
        'text_disabled': COLORS['text_secondary'],  # Disabled text
    }
    return CTK_COLORS


# ============================================================================
# Gradient Colors for Progress Bar
# ============================================================================

def get_progress_color(percentage: float) -> str:
    """
    Return a color based on progress percentage.
    Goes from red (0%) -> orange (30%) -> yellow (70%) -> green (100%)
    """
    if percentage < 30:
        # Red to orange
        ratio = percentage / 30
        red = 255
        green = int(69 + (165 - 69) * ratio)
        blue = 58
    elif percentage < 70:
        # Orange to yellow
        ratio = (percentage - 30) / 40
        red = 255
        green = int(165 + (159 - 165) * ratio)
        blue = int(58 + (10 - 58) * ratio)
    else:
        # Yellow to green
        ratio = (percentage - 70) / 30
        red = int(255 - (255 - 48) * ratio)
        green = int(159 + (208 - 159) * ratio)
        blue = int(10 + (88 - 10) * ratio)

    return f'#{red:02x}{green:02x}{blue:02x}'


# ============================================================================
# Widget Style Helpers
# ============================================================================

def get_button_style(style_type: str = 'primary') -> dict:
    """Get style dictionary for button types."""
    if style_type == 'primary':
        return {
            'fg_color': COLORS['accent'],
            'hover_color': COLORS['accent_hover'],
            'text_color': COLORS['text_primary'],
            'corner_radius': CORNER_RADIUS['medium'],
            'height': 44,
            'font': FONTS['headline'],
        }
    elif style_type == 'secondary':
        return {
            'fg_color': COLORS['secondary'],
            'hover_color': COLORS['tertiary'],
            'text_color': COLORS['text_primary'],
            'corner_radius': CORNER_RADIUS['medium'],
            'height': 44,
            'font': FONTS['headline'],
        }
    elif style_type == 'success':
        return {
            'fg_color': COLORS['success'],
            'hover_color': '#32d368',
            'text_color': '#000000',
            'corner_radius': CORNER_RADIUS['medium'],
            'height': 44,
            'font': FONTS['headline'],
        }
    elif style_type == 'danger':
        return {
            'fg_color': COLORS['error'],
            'hover_color': '#ff5550',
            'text_color': COLORS['text_primary'],
            'corner_radius': CORNER_RADIUS['medium'],
            'height': 44,
            'font': FONTS['headline'],
        }
    return get_button_style('primary')


def get_entry_style() -> dict:
    """Get style dictionary for entry widgets."""
    return {
        'fg_color': COLORS['tertiary'],
        'border_color': COLORS['quaternary'],
        'border_width': 1,
        'text_color': COLORS['text_primary'],
        'placeholder_text_color': COLORS['text_secondary'],
        'corner_radius': CORNER_RADIUS['medium'],
        'height': 44,
        'font': FONTS['body'],
    }


def get_card_style() -> dict:
    """Get style dictionary for card containers."""
    return {
        'fg_color': COLORS['secondary'],
        'corner_radius': CORNER_RADIUS['large'],
        'border_width': 1,
        'border_color': COLORS['glass_border'],
    }
