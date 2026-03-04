"""
Main Vodu Downloader Application
iOS-style GUI with smooth animations and modern design.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import Optional, Callable

from .styles import COLORS, FONTS, SPACING, CORNER_RADIUS, configure_ctk_theme
from .widgets import GlassCard, SmoothProgressBar, StatusLabel, SegmentedControl
from .pages import MoviesPage, AppsPage


class VoduDownloaderApp(ctk.CTk):
    """
    Main application class for Vodu Downloader.
    Features iOS-style dark mode design with glassmorphism effects.
    """

    def __init__(self, download_handlers: Optional[dict] = None):
        """
        Initialize the Vodu Downloader application.

        Args:
            download_handlers: Dictionary of download handler functions:
                - 'video': function(url, quality, season)
                - 'subtitle': function(url)
                - 'apps_download': function(url)
                - 'apps_open_urls': function(url)
                - 'open_video_urls': function(url, quality, season)
        """
        super().__init__()

        self.download_handlers = download_handlers or {}

        # Configure theme
        configure_ctk_theme()

        # Setup window
        self._setup_window()

        # Create widgets
        self._create_widgets()

        # Show default page
        self.show_page('movies')

    def _setup_window(self):
        """Configure the main window."""
        self.title("Vodu Downloader")
        self.geometry("500x900")  # Larger window for better visibility
        self.configure(fg_color=COLORS['background'])

        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

        # Make resizable for flexibility
        self.resizable(True, True)
        self.minsize(450, 700)  # Set minimum size

    def _create_widgets(self):
        """Create all UI widgets."""
        # ====================================================================
        # Header
        # ====================================================================
        self.header = ctk.CTkFrame(self, fg_color=COLORS['secondary'], height=60)
        self.header.pack(fill='x', side='top')
        self.header.pack_propagate(False)

        # Logo/Title area
        title_container = ctk.CTkFrame(self.header, fg_color=COLORS['secondary'])
        title_container.pack(fill='x', expand=True, padx=SPACING['md'], pady=SPACING['sm'])

        # App title
        self.app_title = ctk.CTkLabel(
            title_container,
            text='Vodu Downloader',
            font=FONTS['title1'],
            text_color=COLORS['text_primary']
        )
        self.app_title.pack(side='left', padx=(SPACING['sm'], 0))

        # Developer info button (small heart icon)
        self.dev_btn = ctk.CTkButton(
            title_container,
            text='❤️',
            width=36,
            height=36,
            corner_radius=CORNER_RADIUS['medium'],
            fg_color=COLORS['secondary'],
            hover_color=COLORS['tertiary'],
            text_color=COLORS['error'],
            font=('Segoe UI', 14),
            command=self._show_developer_info
        )
        self.dev_btn.pack(side='right')

        # ====================================================================
        # Segmented Control (Navigation)
        # ====================================================================
        nav_container = ctk.CTkFrame(self, fg_color=COLORS['background'])
        nav_container.pack(fill='x', padx=SPACING['md'], pady=(SPACING['sm'], SPACING['md']))

        self.segmented_control = SegmentedControl(
            nav_container,
            choices=['Movies', 'Apps'],
            default=0,
            on_change=self._on_tab_change
        )
        self.segmented_control.pack(fill='x')

        # ====================================================================
        # Content Area
        # ====================================================================
        self.content_frame = ctk.CTkFrame(self, fg_color=COLORS['background'])
        self.content_frame.pack(fill='both', expand=True, padx=SPACING['sm'], pady=(0, SPACING['sm']))

        # Create pages
        self._create_pages()

        # ====================================================================
        # Progress Section (Bottom)
        # ====================================================================
        self.progress_section = ctk.CTkFrame(self, fg_color=COLORS['secondary'], height=140)
        self.progress_section.pack(fill='x', side='bottom')
        self.progress_section.pack_propagate(False)

        # Progress bar
        progress_container = ctk.CTkFrame(self.progress_section, fg_color=COLORS['secondary'])
        progress_container.pack(fill='x', padx=SPACING['md'], pady=(SPACING['sm'], SPACING['xs']))

        self.progress_bar = SmoothProgressBar(
            progress_container,
            width=400,
            height=25
        )
        self.progress_bar.pack()

        # Status label
        self.status_label = StatusLabel(
            self.progress_section,
            height=60
        )
        self.status_label.pack(fill='both', expand=True, padx=SPACING['md'], pady=(SPACING['xs'], SPACING['xs']))

        # Time remaining label
        self.time_label = ctk.CTkLabel(
            self.progress_section,
            text='',
            font=FONTS['caption1'],
            text_color=COLORS['text_secondary']
        )
        self.time_label.pack(padx=SPACING['md'], pady=(0, SPACING['sm']))

    def _create_pages(self):
        """Create page frames."""
        # Movies/TV Shows Page
        self.movies_page = MoviesPage(
            self.content_frame,
            download_callbacks={
                'video': self._handle_video_download,
                'subtitle': self._handle_subtitle_download,
                'open_urls': self._handle_open_video_urls
            }
        )

        # Apps/Games Page
        self.apps_page = AppsPage(
            self.content_frame,
            download_callbacks={
                'download': self._handle_apps_download,
                'open_urls': self._handle_apps_open_urls
            }
        )

        self._current_page = None
        self._pages = {
            'movies': self.movies_page,
            'apps': self.apps_page
        }

    # ========================================================================
    # Page Navigation
    # ========================================================================

    def show_page(self, page_name: str):
        """
        Show a specific page.

        Args:
            page_name: 'movies' or 'apps'
        """
        # Hide current page
        if self._current_page:
            self._pages[self._current_page].pack_forget()

        # Show new page
        page = self._pages.get(page_name)
        if page:
            page.pack(fill='both', expand=True)
            self._current_page = page_name

    def _on_tab_change(self, index: int, name: str):
        """Handle segmented control change."""
        page_name = 'movies' if name == 'Movies' else 'apps'
        self.show_page(page_name)

    # ========================================================================
    # Download Handlers (Bridge to external handlers)
    # ========================================================================

    def _handle_video_download(self, url: str, quality: str, season: str):
        """Handle video download request."""
        if 'video' in self.download_handlers:
            self.download_handlers['video'](
                url=url,
                quality=quality,
                season=season,
                progress_bar=self.progress_bar,
                status_label=self.status_label,
                time_label=self.time_label,
                window=self
            )

    def _handle_subtitle_download(self, url: str):
        """Handle subtitle download request."""
        if 'subtitle' in self.download_handlers:
            self.download_handlers['subtitle'](
                url=url,
                progress_bar=self.progress_bar,
                status_label=self.status_label,
                window=self
            )

    def _handle_open_video_urls(self, url: str, quality: str, season: str):
        """Handle open video URLs request."""
        if 'open_video_urls' in self.download_handlers:
            self.download_handlers['open_video_urls'](
                url=url,
                quality=quality,
                season=season
            )

    def _handle_apps_download(self, url: str):
        """Handle apps/games download request."""
        if 'apps_download' in self.download_handlers:
            self.download_handlers['apps_download'](
                url=url,
                progress_bar=self.progress_bar,
                status_label=self.status_label,
                time_label=self.time_label,
                window=self
            )

    def _handle_apps_open_urls(self, url: str):
        """Handle open apps URLs request."""
        if 'apps_open_urls' in self.download_handlers:
            self.download_handlers['apps_open_urls'](url=url)

    # ========================================================================
    # UI Methods
    # ========================================================================

    def _show_developer_info(self):
        """Show developer information dialog."""
        from tkinter import messagebox
        messagebox.showinfo(
            "Developer Information",
            "Name: sajjad salam\n"
            "Email: sajjad.salam.teama@gmail.com\n"
            "Website: https://github.com/sajjad-salam\n"
            "GitHub: https://github.com/sajjad-salam\n"
            "LinkedIn: https://www.linkedin.com/in/sajjad-salam-963043244/"
        )

    # ========================================================================
    # Progress Update Methods (for external use)
    # ========================================================================

    def update_progress(self, value: float):
        """Update progress bar value."""
        self.progress_bar.set_progress(value)

    def update_status(self, text: str):
        """Update status label text."""
        self.status_label.set_text(text)

    def append_status(self, text: str):
        """Append text to status label."""
        self.status_label.append_text(text)

    def update_time_remaining(self, text: str):
        """Update time remaining label."""
        self.time_label.configure(text=text)

    def get_current_page(self) -> str:
        """Get the currently displayed page name."""
        return self._current_page

    def get_movies_url(self) -> str:
        """Get URL from movies page."""
        return self.movies_page.get_url()

    def get_apps_url(self) -> str:
        """Get URL from apps page."""
        return self.apps_page.get_url()

    # ========================================================================
    # Show Info/Error Messages
    # ========================================================================

    def show_info(self, title: str, message: str):
        """Show an info dialog."""
        messagebox.showinfo(title, message)

    def show_error(self, title: str, message: str):
        """Show an error dialog."""
        messagebox.showerror(title, message)

    def show_warning(self, title: str, message: str):
        """Show a warning dialog."""
        messagebox.showwarning(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Show a yes/no dialog and return True if Yes."""
        return messagebox.askyesno(title, message)

    def ask_directory(self, title: str = "Choose Download Path") -> Optional[str]:
        """Show directory selection dialog."""
        return filedialog.askdirectory(title=title)


# ============================================================================
# Application Entry Point
# ============================================================================

def run_app(download_handlers: dict = None):
    """
    Run the Vodu Downloader application.

    Args:
        download_handlers: Dictionary of download handler functions
    """
    app = VoduDownloaderApp(download_handlers)
    app.mainloop()
