"""
Custom iOS-Style Widgets
Provides reusable components with iOS-style design and smooth animations.
"""

import tkinter as tk
from typing import Optional, Callable, List
import customtkinter as ctk
from .styles import (
    COLORS, FONTS, SPACING, CORNER_RADIUS,
    get_button_style, get_entry_style, get_card_style
)
from .animations import ButtonAnimator, AnimatedProgress


# ============================================================================
# Glass Card Container
# ============================================================================

class GlassCard(ctk.CTkFrame):
    """
    A container with glassmorphism effect - semi-transparent background
    with subtle border and shadow.
    """

    def __init__(self, master, **kwargs):
        style = get_card_style()
        kwargs.setdefault('fg_color', style['fg_color'])
        kwargs.setdefault('corner_radius', style['corner_radius'])
        kwargs.setdefault('border_width', style['border_width'])
        kwargs.setdefault('border_color', style['border_color'])

        super().__init__(master, **kwargs)


# ============================================================================
# Animated Button
# ============================================================================

class AnimatedButton(ctk.CTkButton):
    """
    A button with smooth hover and click animations.
    """

    def __init__(self, master, style_type: str = 'primary',
                 on_click: Optional[Callable[[], None]] = None, **kwargs):
        """
        Args:
            master: Parent widget
            style_type: 'primary', 'secondary', 'success', or 'danger'
            on_click: Callback function
            **kwargs: Additional button arguments
        """
        style = get_button_style(style_type)
        kwargs.setdefault('fg_color', style['fg_color'])
        kwargs.setdefault('hover_color', style['hover_color'])
        kwargs.setdefault('text_color', style['text_color'])
        kwargs.setdefault('corner_radius', style['corner_radius'])
        kwargs.setdefault('height', style['height'])
        kwargs.setdefault('font', style['font'])

        self._on_click_callback = on_click
        self._is_animating = False

        super().__init__(master, command=self._on_click, **kwargs)

        # Setup animations
        self._setup_animations()

    def _on_click(self):
        """Handle button click with animation."""
        if self._is_animating:
            return

        self._is_animating = True

        # Visual feedback - slight color shift
        original_color = self.cget('fg_color')
        pressed_color = self._darker_color(original_color)
        self.configure(fg_color=pressed_color)

        # Reset after delay
        self.after(100, lambda: (
            self.configure(fg_color=original_color),
            setattr(self, '_is_animating', False),
            self._on_click_callback() if self._on_click_callback else None
        ))

    def _darker_color(self, hex_color: str) -> str:
        """Return a darker version of the color."""
        if hex_color.startswith('#'):
            hex_color = hex_color[1:]
        try:
            r = max(0, int(hex_color[0:2], 16) - 30)
            g = max(0, int(hex_color[2:4], 16) - 30)
            b = max(0, int(hex_color[4:6], 16) - 30)
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return hex_color

    def _setup_animations(self):
        """Setup hover animations."""
        # CustomTkinter handles hover colors automatically via hover_color
        pass


# ============================================================================
# Smooth Progress Bar
# ============================================================================

class SmoothProgressBar(ctk.CTkFrame):
    """
    iOS-style progress bar with smooth animations and gradient colors.
    """

    def __init__(self, master, width: int = 400, height: int = 30, **kwargs):
        kwargs.setdefault('fg_color', COLORS['background'])
        super().__init__(master, width=width, height=height, **kwargs)

        self._width = width
        self._height = height
        self._progress = 0.0

        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg='#1a1a1a',
            highlightthickness=2,
            highlightbackground='#333333',
            highlightcolor='#333333',
            bd=0
        )
        self.canvas.pack(fill='both', expand=True)

        # Initialize display
        self._draw_progress()

    def set_progress(self, value: float, animated: bool = True):
        """
        Set progress value (0-100).

        Args:
            value: Progress percentage
            animated: Whether to animate the transition
        """
        self._progress = max(0, min(100, value))
        self._draw_progress()

    def _draw_progress(self):
        """Draw the progress bar with current value."""
        from .styles import get_progress_color

        self.canvas.delete("all")

        # Background
        self.canvas.create_rectangle(
            2, 2, self._width - 2, self._height - 2,
            fill='#1a1a1a',
            outline='#00ff00',
            width=2,
            tags="progress_bg"
        )

        # Progress fill
        if self._progress > 0:
            fill_width = 2 + ((self._width - 4) * self._progress / 100)
            color = get_progress_color(self._progress)

            self.canvas.create_rectangle(
                2, 2, fill_width, self._height - 2,
                fill=color,
                outline="",
                width=0,
                tags="progress_fill"
            )

        # Percentage text
        self.canvas.create_text(
            self._width / 2, self._height / 2,
            text=f"{self._progress:.1f}%",
            fill='#ffffff',
            font=('Segoe UI', 10, 'bold'),
            tags="progress_text"
        )


# ============================================================================
# Segmented Control (iOS-style tab selector)
# ============================================================================

class SegmentedControl(ctk.CTkFrame):
    """
    iOS-style segmented control for switching between options.
    Like a pill-shaped tab selector.
    """

    def __init__(self, master, choices: List[str],
                 default: int = 0,
                 on_change: Optional[Callable[[int, str], None]] = None,
                 **kwargs):
        """
        Args:
            master: Parent widget
            choices: List of option names
            default: Default selected index
            on_change: Callback when selection changes (index, name)
            **kwargs: Additional frame arguments
        """
        kwargs.setdefault('fg_color', COLORS['tertiary'])
        kwargs.setdefault('corner_radius', CORNER_RADIUS['medium'])

        super().__init__(master, **kwargs)

        self._choices = choices
        self._selected_index = default
        self._on_change_callback = on_change
        self._buttons = []

        self._create_buttons()

    def _create_buttons(self):
        """Create buttons for each option."""
        for i, choice in enumerate(self._choices):
            btn = ctk.CTkButton(
                self,
                text=choice,
                font=FONTS['subheadline'],
                corner_radius=CORNER_RADIUS['small'],
                height=36,
                fg_color=(
                    COLORS['accent'] if i == self._selected_index
                    else COLORS['tertiary']
                ),
                hover_color=(
                    COLORS['accent_hover'] if i == self._selected_index
                    else COLORS['quaternary']
                ),
                text_color=(
                    COLORS['text_primary'] if i == self._selected_index
                    else COLORS['text_secondary']
                ),
                command=lambda idx=i: self._select_option(idx)
            )
            btn.pack(side='left', expand=True, fill='x', padx=2, pady=2)
            self._buttons.append(btn)

    def _select_option(self, index: int):
        """Select an option and update display."""
        if index == self._selected_index:
            return

        # Update button states
        for i, btn in enumerate(self._buttons):
            if i == index:
                btn.configure(
                    fg_color=COLORS['accent'],
                    hover_color=COLORS['accent_hover'],
                    text_color=COLORS['text_primary']
                )
            else:
                btn.configure(
                    fg_color=COLORS['tertiary'],
                    hover_color=COLORS['quaternary'],
                    text_color=COLORS['text_secondary']
                )

        old_index = self._selected_index
        self._selected_index = index

        # Callback
        if self._on_change_callback:
            self._on_change_callback(index, self._choices[index])

    def get_selected(self) -> tuple[int, str]:
        """Get current selection as (index, name)."""
        return self._selected_index, self._choices[self._selected_index]

    def set_selected(self, index: int):
        """Set selection programmatically."""
        self._select_option(index)


# ============================================================================
# Modern Entry Field
# ============================================================================

class ModernEntry(ctk.CTkEntry):
    """
    Clean input field with iOS styling and placeholder animation.
    """

    def __init__(self, master, placeholder: str = "", **kwargs):
        style = get_entry_style()
        kwargs.setdefault('fg_color', style['fg_color'])
        kwargs.setdefault('border_color', style['border_color'])
        kwargs.setdefault('border_width', style['border_width'])
        kwargs.setdefault('text_color', style['text_color'])
        kwargs.setdefault('placeholder_text', placeholder)
        kwargs.setdefault('placeholder_text_color', style['placeholder_text_color'])
        kwargs.setdefault('corner_radius', style['corner_radius'])
        kwargs.setdefault('height', style['height'])
        kwargs.setdefault('font', style['font'])

        self._original_border_color = style['border_color']
        self._focus_border_color = COLORS['accent']

        super().__init__(master, **kwargs)

        self._setup_focus_animation()

    def _setup_focus_animation(self):
        """Setup focus/blur animations."""
        self.bind('<FocusIn>', self._on_focus)
        self.bind('<FocusOut>', self._on_focus_out)

    def _on_focus(self, event):
        """Handle focus event."""
        self.configure(border_color=self._focus_border_color)

    def _on_focus_out(self, event):
        """Handle focus out event."""
        self.configure(border_color=self._original_border_color)


# ============================================================================
# Quality Selector (Pill Buttons)
# ============================================================================

class QualitySelector(ctk.CTkFrame):
    """
    Quality selector with pill-shaped buttons instead of radio buttons.
    """

    def __init__(self, master, choices: List[str] = None,
                 default: str = '360p',
                 on_change: Optional[Callable[[str], None]] = None,
                 **kwargs):
        """
        Args:
            master: Parent widget
            choices: List of quality options (default: ['360p', '720p', '1080p'])
            default: Default selected quality
            on_change: Callback when selection changes
            **kwargs: Additional frame arguments
        """
        if choices is None:
            choices = ['360p', '720p', '1080p']

        kwargs.setdefault('fg_color', COLORS['background'])
        super().__init__(master, **kwargs)

        self._choices = choices
        self._selected_quality = default
        self._on_change_callback = on_change
        self._buttons = {}

        self._create_buttons()

    def _create_buttons(self):
        """Create pill buttons for each quality option."""
        for quality in self._choices:
            btn = ctk.CTkButton(
                self,
                text=quality,
                font=FONTS['callout'],
                corner_radius=CORNER_RADIUS['small'],
                width=70,
                height=32,
                fg_color=(
                    COLORS['accent'] if quality == self._selected_quality
                    else COLORS['secondary']
                ),
                hover_color=(
                    COLORS['accent_hover'] if quality == self._selected_quality
                    else COLORS['tertiary']
                ),
                text_color=COLORS['text_primary'],
                command=lambda q=quality: self._select_quality(q)
            )
            btn.pack(side='left', padx=SPACING['xs'])
            self._buttons[quality] = btn

    def _select_quality(self, quality: str):
        """Select a quality and update display."""
        if quality == self._selected_quality:
            return

        # Update button states
        for q, btn in self._buttons.items():
            if q == quality:
                btn.configure(
                    fg_color=COLORS['accent'],
                    hover_color=COLORS['accent_hover']
                )
            else:
                btn.configure(
                    fg_color=COLORS['secondary'],
                    hover_color=COLORS['tertiary']
                )

        self._selected_quality = quality

        # Callback
        if self._on_change_callback:
            self._on_change_callback(quality)

    def get_selected(self) -> str:
        """Get current selected quality."""
        return self._selected_quality

    def set_selected(self, quality: str):
        """Set selection programmatically."""
        if quality in self._choices:
            self._select_quality(quality)


# ============================================================================
# Season Selector (Horizontal Scrollable Chips)
# ============================================================================

class SeasonSelector(ctk.CTkScrollableFrame):
    """
    Horizontal scrollable season selector with chip-style buttons.
    """

    def __init__(self, master, num_seasons: int = 10,
                 default: str = 'all',
                 on_change: Optional[Callable[[str], None]] = None,
                 **kwargs):
        """
        Args:
            master: Parent widget
            num_seasons: Number of seasons to display
            default: Default selected season ('all' or 'S1', 'S2', etc.)
            on_change: Callback when selection changes
            **kwargs: Additional frame arguments
        """
        kwargs.setdefault('fg_color', COLORS['background'])
        kwargs.setdefault('height', 50)

        super().__init__(master, **kwargs)

        self._on_change_callback = on_change
        self._selected_season = default
        self._buttons = {}

        self._create_seasons(num_seasons)

    def _create_seasons(self, num_seasons: int):
        """Create season chips."""
        # "All" button
        all_btn = ctk.CTkButton(
            self,
            text='All',
            font=FONTS['callout'],
            corner_radius=CORNER_RADIUS['small'],
            width=50,
            height=32,
            fg_color=(
                COLORS['accent'] if self._selected_season == 'all'
                else COLORS['secondary']
            ),
            hover_color=COLORS['accent_hover'] if self._selected_season == 'all' else COLORS['tertiary'],
            text_color=COLORS['text_primary'],
            command=lambda: self._select_season('all')
        )
        all_btn.pack(side='left', padx=SPACING['xs'])
        self._buttons['all'] = all_btn

        # Season buttons
        for i in range(1, num_seasons + 1):
            season_key = str(i)
            btn = ctk.CTkButton(
                self,
                text=f'S{i}',
                font=FONTS['callout'],
                corner_radius=CORNER_RADIUS['small'],
                width=45,
                height=32,
                fg_color=(
                    COLORS['accent'] if self._selected_season == season_key
                    else COLORS['secondary']
                ),
                hover_color=COLORS['accent_hover'] if self._selected_season == season_key else COLORS['tertiary'],
                text_color=COLORS['text_primary'],
                command=lambda s=season_key: self._select_season(s)
            )
            btn.pack(side='left', padx=SPACING['xs'])
            self._buttons[season_key] = btn

    def _select_season(self, season: str):
        """Select a season and update display."""
        if season == self._selected_season:
            return

        # Update button states
        for s, btn in self._buttons.items():
            if s == season:
                btn.configure(
                    fg_color=COLORS['accent'],
                    hover_color=COLORS['accent_hover']
                )
            else:
                btn.configure(
                    fg_color=COLORS['secondary'],
                    hover_color=COLORS['tertiary']
                )

        self._selected_season = season

        # Callback
        if self._on_change_callback:
            self._on_change_callback(season)

    def get_selected(self) -> str:
        """Get current selected season."""
        return self._selected_season

    def set_selected(self, season: str):
        """Set selection programmatically."""
        self._select_season(season)


# ============================================================================
# URL Input Card
# ============================================================================

class URLInputCard(GlassCard):
    """
    A card containing a URL input field with paste button.
    """

    def __init__(self, master, placeholder: str = "Enter URL...",
                 on_paste: Optional[Callable[[], None]] = None, **kwargs):
        """
        Args:
            master: Parent widget
            placeholder: Placeholder text for the entry
            on_paste: Callback for paste button
            **kwargs: Additional card arguments
        """
        kwargs.setdefault('fg_color', COLORS['secondary'])
        super().__init__(master, **kwargs)

        self._on_paste_callback = on_paste

        # Header label
        self.header_label = ctk.CTkLabel(
            self,
            text="URL",
            font=FONTS['subheadline'],
            text_color=COLORS['text_secondary']
        )
        self.header_label.pack(anchor='w', padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))

        # URL entry directly (no container needed)
        self.entry = ModernEntry(
            self,
            placeholder=placeholder,
            font=FONTS['monospace']
        )
        self.entry.pack(fill='x', padx=SPACING['md'], pady=(0, SPACING['xs']))

        # Paste button
        self.paste_btn = ctk.CTkButton(
            self,
            text='Paste URL',
            font=FONTS['caption1'],
            corner_radius=CORNER_RADIUS['small'],
            height=32,
            fg_color=COLORS['tertiary'],
            hover_color=COLORS['quaternary'],
            text_color=COLORS['accent'],
            command=self._on_paste
        )
        self.paste_btn.pack(anchor='e', padx=SPACING['md'], pady=(0, SPACING['md']))

    def _on_paste(self):
        """Handle paste button click."""
        try:
            # Get clipboard content
            clipboard_content = self.clipboard_get()
            self.entry.delete(0, 'end')
            self.entry.insert(0, clipboard_content)
            if self._on_paste_callback:
                self._on_paste_callback()
        except:
            pass

    def get_url(self) -> str:
        """Get the current URL from the entry."""
        return self.entry.get().strip()

    def set_url(self, url: str):
        """Set the URL in the entry."""
        self.entry.delete(0, 'end')
        self.entry.insert(0, url)

    def clear(self):
        """Clear the entry."""
        self.entry.delete(0, 'end')


# ============================================================================
# Status Label (Multiline with scrolling)
# ============================================================================

class StatusLabel(ctk.CTkTextbox):
    """
    A read-only text area for displaying download status and logs.
    """

    def __init__(self, master, height: int = 120, **kwargs):
        kwargs.setdefault('fg_color', COLORS['secondary'])
        kwargs.setdefault('border_color', COLORS['quaternary'])
        kwargs.setdefault('border_width', 1)
        kwargs.setdefault('corner_radius', CORNER_RADIUS['medium'])
        kwargs.setdefault('font', FONTS['monospace'])

        super().__init__(master, height=height, **kwargs)

        # Make read-only
        self.configure(state='disabled')

    def set_text(self, text: str):
        """Update the text content."""
        self.configure(state='normal')
        self.delete('1.0', 'end')
        self.insert('1.0', text)
        self.configure(state='disabled')

    def append_text(self, text: str):
        """Append text to the end."""
        self.configure(state='normal')
        self.insert('end', text)
        self.see('end')  # Auto-scroll to end
        self.configure(state='disabled')

    def clear(self):
        """Clear all text."""
        self.set_text('')
