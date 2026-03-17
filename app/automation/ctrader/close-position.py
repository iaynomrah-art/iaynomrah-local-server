import random

def random_delay(page, min_ms=500, max_ms=1500):
    """Wait a random duration to appear more human-like."""
    delay = random.randint(min_ms, max_ms)
    page.wait_for_timeout(delay)

def close_position(page, symbol: str) -> dict:
    """
    Closes an open position for a given symbol in the 'Positions' tab.
    
    Strategy:
    1. Ensure the Positions tab is active.
    2. Find the symbol text in the positions panel (bottom section of the page).
    3. Hover over that row area to reveal the close (X) button.
    4. Find the X button (svg#ic_access_cross) that is on the same Y-level.
    5. Click it.
    """
    print(f"Attempting to close position for: {symbol}")
    
    try:
        # Step 1: Ensure the 'Positions' tab is active
        try:
            positions_tab = page.locator('div:has-text("Positions")').first
            if positions_tab.is_visible(timeout=500):
                positions_tab.click()
        except Exception:
            pass
            
        # Step 2: Find the symbol text in the POSITIONS panel (bottom of the page).
        viewport_height = page.viewport_size["height"] if page.viewport_size else 768
        min_y_for_positions = viewport_height * 0.55
        
        print(f"  > Searching for '{symbol}' text in positions panel (y > {min_y_for_positions:.0f})...")
        
        # Find all elements with the exact symbol text
        symbol_elements = page.locator(f':text-is("{symbol}")').all()
        
        symbol_box = None
        symbol_element = None
        
        for el in symbol_elements:
            try:
                if el.is_visible(timeout=300):
                    box = el.bounding_box()
                    if box and box["y"] > min_y_for_positions:
                        symbol_box = box
                        symbol_element = el
                        print(f"  ✓ Found '{symbol}' in positions panel at y={box['y']:.0f}")
                        break
            except Exception:
                continue
        
        if not symbol_box:
            print(f"  ✗ Could not find '{symbol}' text in the positions panel area.")
            return {"success": False, "reason": f"No active position found for {symbol}", "warning": "Position may be already closed or not exist"}
        
        # Step 3: Hover over the row area to reveal the close (X) button.
        row_y_center = symbol_box["y"] + symbol_box["height"] / 2
        
        # First, hover on the symbol itself
        print("  > Hovering on the position row...")
        symbol_element.hover(timeout=1000)
        page.wait_for_timeout(200) # Minimum wait for UI state change
        
        # Step 4: Find the close X button on the same row (same Y-level).
        target_close_btn = None
        
        all_crosses = page.locator('svg#ic_access_cross').all()
        print(f"  > Found {len(all_crosses)} cross icon(s) total on page.")
        
        # Collect all crosses on the same row in the positions panel
        row_candidates = []
        
        for cross in all_crosses:
            try:
                if cross.is_visible(timeout=300):
                    cross_box = cross.bounding_box()
                    if cross_box:
                        cross_y_center = cross_box["y"] + cross_box["height"] / 2
                        y_distance = abs(row_y_center - cross_y_center)
                        cross_x = cross_box["x"]
                        
                        if y_distance < 25 and cross_box["y"] > min_y_for_positions:
                            row_candidates.append((cross, cross_x, cross_box))
                            print(f"    - Candidate cross at x={cross_x:.0f}, y={cross_box['y']:.0f}, y-dist={y_distance:.0f}")
            except Exception:
                continue
        
        print(f"  > {len(row_candidates)} candidate(s) on the position row. Checking tooltips...")
        
        # Hover each candidate and check for "Close Position" tooltip
        for cross, cross_x, cross_box in row_candidates:
            try:
                parent = cross.locator("xpath=..")
                parent.hover(timeout=1000)
                page.wait_for_timeout(200)  # Wait for tooltip to appear
                
                tooltip = page.locator('text="Close Position"')
                if tooltip.count() > 0 and tooltip.first.is_visible(timeout=300):
                    target_close_btn = parent
                    print(f"  ✓ Found the CORRECT Close Position button at x={cross_x:.0f} (tooltip confirmed!)")
                    break
            except Exception:
                continue
        
        # Fallback to rightmost X if tooltip detection fails
        if not target_close_btn and row_candidates:
            row_candidates.sort(key=lambda item: item[1], reverse=True)
            target_close_btn = row_candidates[0][0]
            print(f"  ⚠ Tooltip detection failed. Falling back to rightmost X at x={row_candidates[0][1]:.0f}")
        
        # Last fallback
        if not target_close_btn:
            try:
                close_pos_btn = page.locator('[title="Close Position"], [aria-label="Close Position"]').first
                if close_pos_btn.is_visible(timeout=500):
                    target_close_btn = close_pos_btn
                    print("  ✓ Found 'Close Position' button by title/aria-label")
            except Exception:
                pass

        if target_close_btn:
            print(f"  > Clicking the close button for {symbol}...")
            target_close_btn.click(timeout=1000)
            print(f"  ✓ Clicked the close button.")
            
            # Step 5: Handle confirmation dialog if it appears
            try:
                confirm_btn = page.locator('button:has-text("Confirm")').first
                if confirm_btn.is_visible(timeout=500):
                    print("  ⚠ Confirmation dialog detected. Clicking Confirm...")
                    confirm_btn.click(timeout=1000)
            except Exception:
                pass
            
            print(f"  ✓ Position for {symbol} successfully closed.")
            return {"success": True, "reason": None, "warning": None}
        else:
            # Last resort
            print(f"  ✗ Could not find the close X button near '{symbol}' row.")
            print(f"  > Last resort: trying to right-click the position row...")
            
            try:
                symbol_element.click(button="right", timeout=1000)
                page.wait_for_timeout(200)
                
                close_menu_item = page.locator('text="Close Position"').first
                if close_menu_item.is_visible(timeout=1000):
                    close_menu_item.click(timeout=1000)
                    print(f"  ✓ Closed position via right-click context menu.")
                    return {"success": True, "reason": None, "warning": None}
            except Exception:
                pass
            
            return {"success": False, "reason": f"Could not find close button for {symbol}", "warning": None}
            
    except Exception as e:
        err_msg = str(e)
        print(f"Error while trying to close position: {err_msg}")
        return {"success": False, "reason": err_msg, "warning": None}
