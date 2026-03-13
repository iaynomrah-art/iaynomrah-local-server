def first_visible(page, selectors, timeout=3000):
    """Return the first visible locator from candidate selectors."""
    for selector in selectors:
        try:
            loc = page.locator(selector).first
            if loc.is_visible(timeout=timeout):
                return loc
        except Exception:
            continue
    return None


def click_first(page, selectors, timeout=3000, click_timeout=2000):
    """Click the first visible element from selectors."""
    target = first_visible(page, selectors, timeout=timeout)
    if not target:
        return False

    try:
        target.click(timeout=click_timeout)
        return True
    except Exception:
        return False


def clear_and_fill(locator, page, value):
    """Clear an input and fill with value."""
    locator.click(timeout=1500)
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    locator.fill(str(value))


def get_text_if_visible(locator, timeout=1000):
    try:
        if locator.is_visible(timeout=timeout):
            return (locator.inner_text() or "").strip()
    except Exception:
        pass
    return None
