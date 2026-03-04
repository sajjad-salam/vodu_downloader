"""
Movies/TV Shows Page
Handles video and subtitle downloads with quality and season selection.
"""

import customtkinter as ctk
from ..styles import COLORS, FONTS, SPACING, QUALITIES
from ..widgets import (
    GlassCard, URLInputCard, QualitySelector, SeasonSelector,
    AnimatedButton, StatusLabel
)


class MoviesPage(ctk.CTkFrame):
    """
    Page for downloading movies and TV shows with quality and season selection.
    """

    def __init__(self, master, download_callbacks: dict, **kwargs):
        """
        Args:
            master: Parent widget
            download_callbacks: Dictionary of callback functions:
                - 'video': Callback for video download
                - 'subtitle': Callback for subtitle download
                - 'open_urls': Callback for opening video URLs
        """
        kwargs.setdefault('fg_color', COLORS['background'])
        super().__init__(master, **kwargs)

        self.download_callbacks = download_callbacks
        self._quality = '360p'
        self._season = 'all'

        self._create_widgets()

    def _create_widgets(self):
        """Create all widgets for the movies page."""
        # Scrollable container
        scrollable = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS['background'],
            label_text=''
        )
        scrollable.pack(fill='both', expand=True, padx=SPACING['md'], pady=SPACING['md'])

        # ====================================================================
        # Header
        # ====================================================================
        header = ctk.CTkFrame(scrollable, fg_color=COLORS['background'])
        header.pack(fill='x', pady=(0, SPACING['lg']))

        title_label = ctk.CTkLabel(
            header,
            text='Movies & TV Shows',
            font=FONTS['title2'],
            text_color=COLORS['text_primary']
        )
        title_label.pack(anchor='w')

        subtitle_label = ctk.CTkLabel(
            header,
            text='Download videos and subtitles',
            font=FONTS['subheadline'],
            text_color=COLORS['text_secondary']
        )
        subtitle_label.pack(anchor='w')

        # ====================================================================
        # URL Input Card
        # ====================================================================
        self.url_card = URLInputCard(
            scrollable,
            placeholder='Paste movie/TV show URL here...'
        )
        self.url_card.pack(fill='x', pady=SPACING['sm'])

        # ====================================================================
        # Quality Selector
        # ====================================================================
        quality_card = GlassCard(scrollable)
        quality_card.pack(fill='x', pady=SPACING['sm'])

        quality_label = ctk.CTkLabel(
            quality_card,
            text='Quality',
            font=FONTS['subheadline'],
            text_color=COLORS['text_secondary']
        )
        quality_label.pack(anchor='w', padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))

        self.quality_selector = QualitySelector(
            quality_card,
            choices=QUALITIES,
            default='360p',
            on_change=self._on_quality_change
        )
        self.quality_selector.pack(padx=SPACING['md'], pady=(0, SPACING['md']))

        # ====================================================================
        # Season Selector
        # ====================================================================
        season_card = GlassCard(scrollable)
        season_card.pack(fill='x', pady=SPACING['sm'])

        season_label = ctk.CTkLabel(
            season_card,
            text='Season',
            font=FONTS['subheadline'],
            text_color=COLORS['text_secondary']
        )
        season_label.pack(anchor='w', padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))

        self.season_selector = SeasonSelector(
            season_card,
            num_seasons=10,
            default='all',
            on_change=self._on_season_change
        )
        self.season_selector.pack(padx=SPACING['md'], pady=(0, SPACING['md']))

        # ====================================================================
        # Download Buttons
        # ====================================================================
        buttons_card = GlassCard(scrollable)
        buttons_card.pack(fill='x', pady=SPACING['sm'])

        # Download Video button
        self.download_video_btn = AnimatedButton(
            buttons_card,
            text='⬇  Download Video',
            style_type='primary',
            on_click=self._on_download_video
        )
        self.download_video_btn.pack(fill='x', padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))

        # Download Subtitle button
        self.download_subtitle_btn = AnimatedButton(
            buttons_card,
            text='💬  Download Subtitle',
            style_type='secondary',
            on_click=self._on_download_subtitle
        )
        self.download_subtitle_btn.pack(fill='x', padx=SPACING['md'], pady=SPACING['xs'])

        # Open URLs button
        self.open_urls_btn = AnimatedButton(
            buttons_card,
            text='🌐  Open in Browser',
            style_type='secondary',
            on_click=self._on_open_urls
        )
        self.open_urls_btn.pack(fill='x', padx=SPACING['md'], pady=(SPACING['xs'], SPACING['md']))

        # ====================================================================
        # Info Card
        # ====================================================================
        info_card = GlassCard(scrollable)
        info_card.pack(fill='x', pady=SPACING['sm'])

        info_text = ctk.CTkLabel(
            info_card,
            text='ℹ️  Make sure to verify the movie/TV show URL is correct before downloading.',
            font=FONTS['caption1'],
            text_color=COLORS['text_secondary'],
            wraplength=350
        )
        info_text.pack(padx=SPACING['md'], pady=SPACING['sm'])

        # Add bottom padding
        padding_frame = ctk.CTkFrame(scrollable, fg_color=COLORS['background'], height=SPACING['lg'])
        padding_frame.pack(fill='x')

    # ========================================================================
    # Callbacks
    # ========================================================================

    def _on_quality_change(self, quality: str):
        """Handle quality selection change."""
        self._quality = quality

    def _on_season_change(self, season: str):
        """Handle season selection change."""
        self._season = season

    def _on_download_video(self):
        """Handle download video button click."""
        url = self.url_card.get_url()
        if not url:
            return

        if 'video' in self.download_callbacks:
            self.download_callbacks['video'](
                url=url,
                quality=self._quality,
                season=self._season
            )

    def _on_download_subtitle(self):
        """Handle download subtitle button click."""
        url = self.url_card.get_url()
        if not url:
            return

        if 'subtitle' in self.download_callbacks:
            self.download_callbacks['subtitle'](url=url)

    def _on_open_urls(self):
        """Handle open URLs button click."""
        url = self.url_card.get_url()
        if not url:
            return

        if 'open_urls' in self.download_callbacks:
            self.download_callbacks['open_urls'](
                url=url,
                quality=self._quality,
                season=self._season
            )

    # ========================================================================
    # Public Methods
    # ========================================================================

    def get_url(self) -> str:
        """Get the current URL from the input."""
        return self.url_card.get_url()

    def get_quality(self) -> str:
        """Get the selected quality."""
        return self.quality_selector.get_selected()

    def get_season(self) -> str:
        """Get the selected season."""
        return self.season_selector.get_selected()

    def set_url(self, url: str):
        """Set the URL in the input."""
        self.url_card.set_url(url)

    def set_quality(self, quality: str):
        """Set the quality selection."""
        self.quality_selector.set_selected(quality)

    def set_season(self, season: str):
        """Set the season selection."""
        self.season_selector.set_selected(season)

    def clear_url(self):
        """Clear the URL input."""
        self.url_card.clear()

    def set_buttons_enabled(self, enabled: bool):
        """Enable or disable all buttons."""
        state = 'normal' if enabled else 'disabled'
        self.download_video_btn.configure(state=state)
        self.download_subtitle_btn.configure(state=state)
        self.open_urls_btn.configure(state=state)
