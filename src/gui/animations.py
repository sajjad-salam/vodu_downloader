"""
Animation Utilities for iOS-Style GUI
Provides smooth, 60fps animations for UI elements using the after() method.
"""

import time
from typing import Callable, Optional
import customtkinter as ctk


# ============================================================================
# Easing Functions
# ============================================================================

def ease_in_out(t: float) -> float:
    """Ease-in-out cubic easing function for smooth animations."""
    return t * t * (3 - 2 * t) if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2


def ease_out(t: float) -> float:
    """Ease-out cubic easing function."""
    return 1 - pow(1 - t, 3)


def ease_in(t: float) -> float:
    """Ease-in cubic easing function."""
    return t * t * t


# ============================================================================
# Animation Manager
# ============================================================================

class AnimationManager:
    """Manages multiple animations and ensures smooth 60fps playback."""

    def __init__(self, fps: int = 60):
        self.fps = fps
        self.frame_time = 1000 // fps  # ms per frame
        self.active_animations = []

    def animate(self,
                duration_ms: int,
                update_func: Callable[[float], bool],
                complete_func: Optional[Callable[[], None]] = None,
                easing_func: Callable[[float], float] = ease_in_out) -> str:
        """
        Start a new animation.

        Args:
            duration_ms: Duration of animation in milliseconds
            update_func: Callback that receives progress (0.0-1.0) and returns True to continue
            complete_func: Callback when animation completes
            easing_func: Easing function to use

        Returns:
            Animation ID string
        """
        animation_id = f"anim_{id(update_func)}_{time.time()}"

        def animation_loop(start_time: float, widget: ctk.CTk):
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration_ms / 1000), 1.0)
            eased_progress = easing_func(progress)

            # Call update function
            should_continue = update_func(eased_progress)

            if progress < 1.0 and should_continue:
                widget.after(self.frame_time, lambda: animation_loop(start_time, widget))
            else:
                # Animation complete
                if complete_func:
                    complete_func()
                if animation_id in self.active_animations:
                    self.active_animations.remove(animation_id)

        self.active_animations.append(animation_id)
        # Start animation on next frame
        return animation_id

    def cancel_all(self):
        """Cancel all active animations."""
        self.active_animations.clear()


# Global animation manager instance
_animation_manager = AnimationManager()


def get_animation_manager() -> AnimationManager:
    """Get the global animation manager instance."""
    return _animation_manager


# ============================================================================
# Widget Animation Functions
# ============================================================================

class FadeAnimation:
    """Fade in/out animation for widgets."""

    @staticmethod
    def fade_in(widget: ctk.CTk, duration_ms: int = 250,
                complete_func: Optional[Callable[[], None]] = None) -> str:
        """
        Fade in a widget using alpha transparency simulation.
        Note: CustomTkinter doesn't support true alpha, so we simulate with color interpolation.
        """
        if not hasattr(widget, '_fade_original_color'):
            widget._fade_original_color = widget.cget('fg_color')

        start_color = COLORS = widget.cget('fg_color')
        # For fade in, we'll use the configured color
        target_color = getattr(widget, '_fade_original_color', start_color)

        # Simple implementation - just show the widget
        if hasattr(widget, 'grid_info'):
            if widget.winfo_ismapped():
                widget.grid()
        else:
            widget.pack()

        if complete_func:
            widget.after(duration_ms, complete_func)

        return "fade_in"

    @staticmethod
    def fade_out(widget: ctk.CTk, duration_ms: int = 250,
                 complete_func: Optional[Callable[[], None]] = None) -> str:
        """Fade out a widget and hide it."""
        # Simple implementation - just hide after delay
        widget.after(duration_ms, lambda: (
            widget.grid_remove() if widget.winfo_ismapped() else widget.pack_forget(),
            complete_func() if complete_func else None
        ))
        return "fade_out"


class SlideAnimation:
    """Slide animation for page transitions."""

    @staticmethod
    def slide_in_from_right(widget: ctk.CTk, container: ctk.CTk,
                            duration_ms: int = 300,
                            complete_func: Optional[Callable[[], None]] = None) -> str:
        """Slide a widget in from the right."""
        widget.place(relx=1.0, rely=0.0, anchor='ne')
        widget.lift()

        start_x = 1.0
        target_x = 0.5
        start_time = time.time()

        def update(progress: float) -> bool:
            current_x = start_x + (target_x - start_x) * progress
            widget.place(relx=current_x, rely=0.0, anchor='ne')
            return True

        manager = get_animation_manager()
        return manager.animate(duration_ms, update, complete_func, ease_out)

    @staticmethod
    def slide_in_from_left(widget: ctk.CTk, container: ctk.CTk,
                           duration_ms: int = 300,
                           complete_func: Optional[Callable[[], None]] = None) -> str:
        """Slide a widget in from the left."""
        widget.place(relx=0.0, rely=0.0, anchor='nw')
        widget.lift()

        start_x = 0.0
        target_x = 0.5
        start_time = time.time()

        def update(progress: float) -> bool:
            current_x = start_x + (target_x - start_x) * progress
            widget.place(relx=current_x, rely=0.0, anchor='n')
            return True

        manager = get_animation_manager()
        return manager.animate(duration_ms, update, complete_func, ease_out)


class ScaleAnimation:
    """Scale animation for button interactions."""

    @staticmethod
    def scale_on_hover(widget: ctk.CTk, scale: float = 1.05,
                       duration_ms: int = 150) -> str:
        """Scale up widget on hover."""
        # Store original size
        if not hasattr(widget, '_original_width'):
            widget._original_width = widget.winfo_width()
            widget._original_height = widget.winfo_height()

        target_width = widget._original_width * scale
        target_height = widget._original_height * scale

        # Note: CustomTkinter doesn't support dynamic resizing easily
        # This is a placeholder for future enhancement
        return "scale_hover"

    @staticmethod
    def scale_on_click(widget: ctk.CTk, scale: float = 0.95,
                       duration_ms: int = 100) -> str:
        """Scale down widget on click."""
        # Note: CustomTkinter doesn't support dynamic resizing easily
        # This is a placeholder for future enhancement
        return "scale_click"


class PulseAnimation:
    """Pulse animation for loading states."""

    def __init__(self, widget: ctk.CTk):
        self.widget = widget
        self.is_running = False
        self.animation_id = None

    def start(self, duration_ms: int = 1000):
        """Start pulsing animation."""
        self.is_running = True
        self._pulse_loop(duration_ms)

    def _pulse_loop(self, duration_ms: int):
        if not self.is_running:
            return

        # Toggle between two states
        current_fg = self.widget.cget('fg_color')
        target_color = '#2c2c2e' if current_fg == '#1c1c1e' else '#1c1c1e'

        self.widget.configure(fg_color=target_color)
        self.widget.after(duration_ms // 2, lambda: self._pulse_loop(duration_ms))

    def stop(self):
        """Stop pulsing animation."""
        self.is_running = False


# ============================================================================
# Progress Bar Animation
# ============================================================================

class AnimatedProgress:
    """Smooth progress bar animation."""

    def __init__(self, progress_canvas):
        self.canvas = progress_canvas
        self.current_value = 0.0
        self.target_value = 0.0
        self.is_animating = False

    def set_value(self, value: float, animated: bool = True):
        """
        Set progress value (0-100).

        Args:
            value: Target progress value
            animated: Whether to animate the transition
        """
        self.target_value = max(0, min(100, value))

        if not animated:
            self.current_value = self.target_value
            self._update_display()
        elif not self.is_animating:
            self._animate_progress()

    def _animate_progress(self):
        """Animate progress bar to target value."""
        self.is_animating = True

        start_value = self.current_value
        difference = self.target_value - start_value
        duration = 300  # ms
        start_time = time.time()

        def update():
            nonlocal start_time
            elapsed = time.time() - start_time
            progress = min(elapsed / (duration / 1000), 1.0)

            self.current_value = start_value + difference * ease_out(progress)
            self._update_display()

            if progress < 1.0:
                self.canvas.after(16, update)  # ~60fps
            else:
                self.is_animating = False

        update()

    def _update_display(self):
        """Update the visual display of progress."""
        from .styles import get_progress_color

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width <= 1:  # Canvas not yet rendered
            return

        fill_width = (width - 4) * (self.current_value / 100)
        color = get_progress_color(self.current_value)

        # Clear previous drawing
        self.canvas.delete("all")

        # Draw background
        self.canvas.create_rectangle(
            2, 2, width - 2, height - 2,
            fill='#1a1a1a',
            outline='#333333',
            width=2,
            tags="progress_bg"
        )

        # Draw progress fill
        if fill_width > 2:
            self.canvas.create_rectangle(
                2, 2, fill_width, height - 2,
                fill=color,
                outline="",
                width=0,
                tags="progress_fill"
            )

        # Draw percentage text
        self.canvas.create_text(
            width / 2, height / 2,
            text=f"{self.current_value:.1f}%",
            fill='#ffffff',
            font=('Segoe UI', 10, 'bold'),
            tags="progress_text"
        )


# ============================================================================
# Button State Animation
# ============================================================================

class ButtonAnimator:
    """Manages button hover and click animations."""

    @staticmethod
    def setup_hover_animation(button: ctk.CTk,
                             normal_color: str,
                             hover_color: str,
                             pressed_color: str = None):
        """
        Setup hover animation for a button.

        Args:
            button: The button to animate
            normal_color: Color in normal state
            hover_color: Color on hover
            pressed_color: Color when pressed (optional)
        """
        if pressed_color is None:
            pressed_color = hover_color

        original_configure = button.configure

        def on_enter(event):
            button.configure(fg_color=hover_color)

        def on_leave(event):
            button.configure(fg_color=normal_color)

        def on_press(event):
            button.configure(fg_color=pressed_color)

        def on_release(event):
            button.configure(fg_color=hover_color)

        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)
        button.bind('<Button-1>', on_press)
        button.bind('<ButtonRelease-1>', on_release)


# ============================================================================
# Page Transition Animation
# ============================================================================

class PageTransition:
    """Smooth page transition animations."""

    @staticmethod
    def switch_pages(container: ctk.CTk,
                     old_page: ctk.CTkFrame,
                     new_page: ctk.CTkFrame,
                     direction: str = 'left',
                     duration_ms: int = 300):
        """
        Switch between pages with slide animation.

        Args:
            container: Parent container
            old_page: Page to hide
            new_page: Page to show
            direction: 'left' or 'right'
            duration_ms: Animation duration
        """
        # Ensure new page is ready
        new_page.place(relx=0, rely=0, relwidth=1, relheight=1)
        new_page.lift()

        if direction == 'left':
            # Slide new page from right
            SlideAnimation.slide_in_from_right(new_page, container, duration_ms)
        else:
            # Slide new page from left
            SlideAnimation.slide_in_from_left(new_page, container, duration_ms)

        # Hide old page after animation starts
        if old_page:
            old_page.place_forget()


# Import at end to avoid circular dependency
from .styles import COLORS
