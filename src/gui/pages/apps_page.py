"""
Apps & Games Page
Handles app and game downloads from Vodu store.
"""

import customtkinter as ctk
from ..styles import COLORS, FONTS, SPACING
from ..widgets import (
    GlassCard, URLInputCard, AnimatedButton
)


class AppsPage(ctk.CTkFrame):
    """
    Page for downloading apps and games from Vodu store.
    """

    def __init__(self, master, download_callbacks: dict, **kwargs):
        """
        Args:
            master: Parent widget
            download_callbacks: Dictionary of callback functions:
                - 'download': Callback for app/game download
                - 'open_urls': Callback for opening app URLs in browser
        """
        kwargs.setdefault('fg_color', COLORS['background'])
        super().__init__(master, **kwargs)

        self.download_callbacks = download_callbacks

        self._create_widgets()

    def _create_widgets(self):
        """Create all widgets for the apps page."""
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
            text='Apps & Games',
            font=FONTS['title2'],
            text_color=COLORS['text_primary']
        )
        title_label.pack(anchor='w')

        subtitle_label = ctk.CTkLabel(
            header,
            text='Download apps and games from Vodu store',
            font=FONTS['subheadline'],
            text_color=COLORS['text_secondary']
        )
        subtitle_label.pack(anchor='w')

        # ====================================================================
        # URL Input Card
        # ====================================================================
        self.url_card = URLInputCard(
            scrollable,
            placeholder='Paste Vodu store URL here...'
        )
        self.url_card.pack(fill='x', pady=SPACING['sm'])

        # ====================================================================
        # Info Card
        # ====================================================================
        info_card = GlassCard(scrollable)
        info_card.pack(fill='x', pady=SPACING['sm'])

        info_title = ctk.CTkLabel(
            info_card,
            text='ℹ️  How to use',
            font=FONTS['callout'],
            text_color=COLORS['text_primary']
        )
        info_title.pack(anchor='w', padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))

        info_steps = ctk.CTkLabel(
            info_card,
            text='1. Go to share.vodu.store\n'
                 '2. Find your app/game\n'
                 '3. Copy the page URL\n'
                 '4. Paste above and download',
            font=FONTS['caption1'],
            text_color=COLORS['text_secondary'],
            justify='left'
        )
        info_steps.pack(anchor='w', padx=SPACING['md'], pady=(0, SPACING['md']))

        # ====================================================================
        # Download Buttons
        # ====================================================================
        buttons_card = GlassCard(scrollable)
        buttons_card.pack(fill='x', pady=SPACING['sm'])

        # Download button
        self.download_btn = AnimatedButton(
            buttons_card,
            text='📱  Download',
            style_type='primary',
            on_click=self._on_download
        )
        self.download_btn.pack(fill='x', padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))

        # Open URLs button
        self.open_urls_btn = AnimatedButton(
            buttons_card,
            text='🌐  Open in Browser',
            style_type='secondary',
            on_click=self._on_open_urls
        )
        self.open_urls_btn.pack(fill='x', padx=SPACING['md'], pady=(SPACING['xs'], SPACING['md']))

        # ====================================================================
        # Features Card
        # ====================================================================
        features_card = GlassCard(scrollable)
        features_card.pack(fill='x', pady=SPACING['sm'])

        features_title = ctk.CTkLabel(
            features_card,
            text='✨  Features',
            font=FONTS['callout'],
            text_color=COLORS['text_primary']
        )
        features_title.pack(anchor='w', padx=SPACING['md'], pady=(SPACING['md'], SPACING['xs']))

        features_text = ctk.CTkLabel(
            features_card,
            text='• Fast downloads with resume support\n'
                 '• Automatic retry on failure\n'
                 '• Progress tracking with speed display\n'
                 '• Multiple file support',
            font=FONTS['caption1'],
            text_color=COLORS['text_secondary'],
            justify='left'
        )
        features_text.pack(anchor='w', padx=SPACING['md'], pady=(0, SPACING['md']))

        # Add bottom padding
        padding_frame = ctk.CTkFrame(scrollable, fg_color=COLORS['background'], height=SPACING['lg'])
        padding_frame.pack(fill='x')

    # ========================================================================
    # Callbacks
    # ========================================================================

    def _on_download(self):
        """Handle download button click."""
        url = self.url_card.get_url()
        if not url:
            return

        if 'share.vodu.store' not in url:
            return

        if 'download' in self.download_callbacks:
            self.download_callbacks['download'](url=url)

    def _on_open_urls(self):
        """Handle open URLs button click."""
        url = self.url_card.get_url()
        if not url:
            return

        if 'share.vodu.store' not in url:
            return

        if 'open_urls' in self.download_callbacks:
            self.download_callbacks['open_urls'](url=url)

    # ========================================================================
    # Public Methods
    # ========================================================================

    def get_url(self) -> str:
        """Get the current URL from the input."""
        return self.url_card.get_url()

    def set_url(self, url: str):
        """Set the URL in the input."""
        self.url_card.set_url(url)

    def clear_url(self):
        """Clear the URL input."""
        self.url_card.clear()

    def set_buttons_enabled(self, enabled: bool):
        """Enable or disable all buttons."""
        state = 'normal' if enabled else 'disabled'
        self.download_btn.configure(state=state)
        self.open_urls_btn.configure(state=state)
