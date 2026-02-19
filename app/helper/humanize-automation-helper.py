"""
Humanize Automation Helper
--------------------------
Utility functions that make Playwright browser automation appear more human-like
by adding randomized delays, natural mouse movements, and realistic typing patterns.

Usage:
    from app.helper.humanize_automation_helper import Human

    human = Human(page)
    human.delay()
    human.move_to(selector)
    human.move_randomly()
    human.click(selector)
    human.type(selector, "hello world")
"""

import random
import math


class Human:
    """Wraps a Playwright page with human-like interaction methods."""

    def __init__(self, page):
        self.page = page
        self._last_x = random.randint(100, 800)
        self._last_y = random.randint(100, 500)

    # ------------------------------------------------------------------ #
    #  DELAY
    # ------------------------------------------------------------------ #

    def delay(self, min_ms=400, max_ms=2000):
        """
        Wait a random amount of time between actions.
        Simulates the natural pause a human takes before doing something.
        """
        duration = random.randint(min_ms, max_ms)
        self.page.wait_for_timeout(duration)
        return duration

    def short_delay(self):
        """A quick micro-pause (100–500ms), like between keystrokes or small actions."""
        return self.delay(100, 500)

    def medium_delay(self):
        """A medium pause (500–1500ms), like reading a label or thinking."""
        return self.delay(500, 1500)

    def long_delay(self):
        """A longer pause (1500–4000ms), like scanning the page or deciding."""
        return self.delay(1500, 4000)

    # ------------------------------------------------------------------ #
    #  MOUSE MOVEMENT
    # ------------------------------------------------------------------ #

    def move_to(self, selector, offset_x=0, offset_y=0):
        """
        Move the mouse to an element with a natural curve, not a straight line.
        Optionally offset the landing point slightly so it doesn't always
        land dead-center.
        """
        element = self.page.locator(selector).first
        box = element.bounding_box()

        if not box:
            print(f"Warning: Could not find bounding box for '{selector}'")
            return

        # Land somewhere near the center, not exactly on it
        jitter_x = random.randint(-5, 5) + offset_x
        jitter_y = random.randint(-3, 3) + offset_y
        target_x = box["x"] + box["width"] / 2 + jitter_x
        target_y = box["y"] + box["height"] / 2 + jitter_y

        self._human_mouse_move(target_x, target_y)

    def move_to_element(self, locator, offset_x=0, offset_y=0):
        """
        Same as move_to but accepts a Playwright Locator directly
        instead of a CSS selector string.
        """
        box = locator.bounding_box()

        if not box:
            print("Warning: Could not find bounding box for locator")
            return

        jitter_x = random.randint(-5, 5) + offset_x
        jitter_y = random.randint(-3, 3) + offset_y
        target_x = box["x"] + box["width"] / 2 + jitter_x
        target_y = box["y"] + box["height"] / 2 + jitter_y

        self._human_mouse_move(target_x, target_y)

    def move_randomly(self):
        """
        Move the mouse to a random spot on the page, like a bored human
        drifting the cursor while thinking. Useful between actions to
        break up predictable patterns.
        """
        viewport = self.page.viewport_size
        if not viewport:
            viewport = {"width": 1280, "height": 720}

        # Stay within a comfortable margin (not right at the edges)
        margin = 80
        target_x = random.randint(margin, viewport["width"] - margin)
        target_y = random.randint(margin, viewport["height"] - margin)

        self._human_mouse_move(target_x, target_y)

    def _human_mouse_move(self, target_x, target_y):
        """
        Internal: Move the mouse from current position to target using
        a bezier-ish curve with randomized intermediate points, so the
        path looks organic instead of a straight teleport.
        """
        steps = random.randint(15, 35)
        start_x, start_y = self._last_x, self._last_y

        # Create a random control point for a quadratic bezier curve
        ctrl_x = (start_x + target_x) / 2 + random.randint(-100, 100)
        ctrl_y = (start_y + target_y) / 2 + random.randint(-80, 80)

        for i in range(steps + 1):
            t = i / steps
            # Quadratic bezier interpolation
            x = (1 - t) ** 2 * start_x + 2 * (1 - t) * t * ctrl_x + t ** 2 * target_x
            y = (1 - t) ** 2 * start_y + 2 * (1 - t) * t * ctrl_y + t ** 2 * target_y

            # Add tiny per-step jitter for hand tremor
            x += random.uniform(-1.5, 1.5)
            y += random.uniform(-1.5, 1.5)

            self.page.mouse.move(x, y)

            # Variable speed — slow at start and end, faster in the middle
            speed_factor = math.sin(t * math.pi)  # peaks at 0.5
            step_delay = random.randint(3, 12) - int(speed_factor * 5)
            step_delay = max(1, step_delay)
            self.page.wait_for_timeout(step_delay)

        self._last_x = target_x
        self._last_y = target_y

    # ------------------------------------------------------------------ #
    #  CLICK
    # ------------------------------------------------------------------ #

    def click(self, selector, move_first=True):
        """
        Click an element with optional human-like mouse movement first.
        Adds a small random delay before and after clicking.
        """
        if move_first:
            self.move_to(selector)
            self.short_delay()

        self.page.click(selector)
        self.short_delay()

    def click_element(self, locator, move_first=True):
        """
        Same as click but accepts a Playwright Locator directly.
        """
        if move_first:
            self.move_to_element(locator)
            self.short_delay()

        locator.click()
        self.short_delay()

    def double_click(self, selector, move_first=True):
        """Double-click an element with human-like behavior."""
        if move_first:
            self.move_to(selector)
            self.short_delay()

        self.page.dblclick(selector)
        self.short_delay()

    # ------------------------------------------------------------------ #
    #  TYPING
    # ------------------------------------------------------------------ #

    def type(self, selector, text, clear_first=True):
        """
        Type text into an input field character by character with
        randomized delays between keystrokes, like a real human typing.
        Optionally clears the field first.
        """
        if clear_first:
            self.page.click(selector, click_count=3)  # select all
            self.short_delay()
            self.page.keyboard.press("Backspace")
            self.short_delay()

        for char in text:
            self.page.keyboard.type(char)
            # Randomized keystroke delay — faster for common letters,
            # slightly slower for numbers and special chars
            if char in " \t\n":
                delay = random.randint(50, 180)
            elif char.isalpha():
                delay = random.randint(30, 120)
            else:
                delay = random.randint(60, 200)
            self.page.wait_for_timeout(delay)

    def type_element(self, locator, text, clear_first=True):
        """
        Same as type but accepts a Playwright Locator directly.
        Clicks the element first to focus it, then types character by character.
        """
        locator.click()
        self.short_delay()

        if clear_first:
            self.page.keyboard.press("Control+a")
            self.short_delay()
            self.page.keyboard.press("Backspace")
            self.short_delay()

        for char in text:
            self.page.keyboard.type(char)
            if char in " \t\n":
                delay = random.randint(50, 180)
            elif char.isalpha():
                delay = random.randint(30, 120)
            else:
                delay = random.randint(60, 200)
            self.page.wait_for_timeout(delay)

    def fill(self, selector, text):
        """
        A faster alternative to type() — uses Playwright's fill() but
        still adds a human delay before and after.
        """
        self.medium_delay()
        self.page.fill(selector, text)
        self.short_delay()

    # ------------------------------------------------------------------ #
    #  SCROLL
    # ------------------------------------------------------------------ #

    def scroll(self, direction="down", amount=None):
        """
        Scroll the page in a given direction with a random amount.
        Direction: 'up' or 'down'.
        """
        if amount is None:
            amount = random.randint(100, 400)

        delta = amount if direction == "down" else -amount
        self.page.mouse.wheel(0, delta)
        self.short_delay()
