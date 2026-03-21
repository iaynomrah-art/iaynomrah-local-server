import os
import re
import time
import importlib
from app.core.supabase import get_supabase

close_position_module = importlib.import_module("app.automation.tradelocker.close-position")
close_position = close_position_module.close_position


def _resolve_db_account_id(supabase, platform_id: str) -> str:
    """
    Resolves platform account_id to trading_accounts.id via credential relation chain.
    """
    try:
        res = supabase.table("credentials") \
            .select("id, package(id, funder_account(id, trading_accounts(id)))") \
            .eq("platform_id", platform_id) \
            .execute()

        if res.data and len(res.data) > 0:
            for row in res.data:
                pkgs = row.get("package", [])
                pkg = pkgs[0] if isinstance(pkgs, list) and pkgs else pkgs
                if not pkg:
                    continue

                funder_accounts = pkg.get("funder_account", [])
                funder = funder_accounts[0] if isinstance(funder_accounts, list) and funder_accounts else funder_accounts
                if not funder:
                    continue

                trading_accounts = funder.get("trading_accounts", [])
                trading_acc = trading_accounts[0] if isinstance(trading_accounts, list) and trading_accounts else trading_accounts
                if trading_acc:
                    return trading_acc.get("id")
    except Exception as e:
        print(f"  ⚠ Error resolving DB account ID: {e}")

    return None


def _position_row_exists(page, symbol: str) -> bool:
    """
    Best-effort check that a position row for `symbol` exists in the TradeLocker UI.
    Mirrors the row-finding heuristic used by `close-position`.
    """
    if not symbol:
        return False
    symbol_text = str(symbol).strip().upper()
    try:
        positions_panel = page.locator(
            'div:has-text("Positions"):has-text("Closed Positions"), div:has-text("Positions"):has-text("Instrument")'
        ).first
        row = None
        try:
            if positions_panel.is_visible(timeout=600):
                row = positions_panel.locator(
                    f'tr:has-text("{symbol_text}"), div[role="row"]:has-text("{symbol_text}"), div:has-text("{symbol_text}")'
                ).first
        except Exception:
            row = None

        if not row:
            row = page.locator(
                f'tr:has-text("{symbol_text}"), div[role="row"]:has-text("{symbol_text}"), div:has-text("{symbol_text}")'
            ).first

        return row.is_visible(timeout=800)
    except Exception:
        return False


def _find_relevant_pairing(supabase, db_account_id: str):
    """
    Find the most relevant paired_trading_accounts row for this account.

    Important: we must NOT exclude trade_status='done' rows blindly, because one device
    can broadcast an exit (and set trade_status=done) before the partner device's
    terminator attaches/restarts. In that case we still need to pick up exit_signal
    and close locally if our termination status is not completed yet.
    """
    if not db_account_id:
        return None

    try:
        res = (
            supabase.table("paired_trading_accounts")
            .select(
                "id, primary_account_id, secondary_account_id, trade_status, is_active, "
                "exit_signal, exit_triggered_by, primary_termination_status, secondary_termination_status"
            )
            .or_(f"primary_account_id.eq.{db_account_id},secondary_account_id.eq.{db_account_id}")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
    except Exception as e:
        print(f"  ⚠ Failed to query paired account status: {e}")
        return None

    rows = res.data or []
    if not rows:
        return None

    for record in rows:
        is_primary = (record.get("primary_account_id") == db_account_id)
        status_col = "primary_termination_status" if is_primary else "secondary_termination_status"
        my_status = record.get(status_col)
        exit_signal = record.get("exit_signal")
        trade_status = record.get("trade_status")

        # Prefer still-active trades; but also allow "done" trades if there's an exit_signal
        # and this side hasn't acknowledged completion yet.
        if trade_status != "done":
            return record
        if exit_signal and my_status != "completed":
            return record

    return None


def _parse_balance(text: str) -> float:
    # Strip out new lines to make it a single string
    text = (text or "").replace('\n', ' ')
    
    # Isolate just the balance part if both labels exist (TradeLocker format)
    if "BALANCE" in text.upper() and ("PROFIT" in text.upper() or "EQUITY" in text.upper()):
        try:
            split1 = text.upper().split("BALANCE")[1]
            if "PROFIT" in split1:
                text = split1.split("PROFIT")[0]
            elif "EQUITY" in split1:
                text = split1.split("EQUITY")[0]
            else:
                text = split1
        except Exception:
            pass
        
    # Strip all letters, spaces, and currency symbols, keep only numbers and decimals
    clean = re.sub(r"[^\d.]", "", text)
    if not clean:
        return 0.0
    return float(clean)


def _get_balance_locator(page):
    locators = [
        # Based on codegen getByText('Balance$') or similar
        page.get_by_text(re.compile(r"Balance\s*\$?", re.I)).last,
        page.locator("div:has-text('Balance')").last,
        page.locator("span:has-text('Balance') >> xpath=../..").last,
        page.locator("div:has-text('BALANCE')").last,
        page.locator("div:has-text('Equity')").last,
        page.locator("div:has-text('EQUITY')").last,
        page.locator("div:has(> div:has-text('BALANCE'))").last,
    ]
    for loc in locators:
        try:
            if loc.is_visible(timeout=800):
                text = loc.inner_text()
                if _parse_balance(text) > 0:
                    return loc
        except Exception:
            continue
    return locators[1]


def _refresh_workspace(page):
    try:
        refresh = page.locator('button:has-text("Refresh"), [data-testid*="refresh" i]').first
        if refresh.is_visible(timeout=600):
            refresh.click(timeout=1000)
            page.wait_for_timeout(200)
            return
    except Exception:
        pass


def terminate_trade(page, symbol: str, account_id: str = None, db_account_id: str = None):
    if not symbol:
        return {"success": False, "reason": "symbol is required for trade-terminator", "warning": None}

    print(f"\n👀 Monitoring started for {symbol} on account {account_id} / DB {db_account_id}...")

    timeout_seconds = int(os.getenv("TRADELOCKER_TERMINATOR_TIMEOUT_SEC", "3600"))
    start_ts = time.time()

    try:
        supabase = get_supabase()
        paired_record_id = None
        is_primary = None
        saw_position_row = False

        def _update_paired_record(record_id, payload):
            """Update a paired_trading_accounts record and log the full response so errors are visible."""
            nonlocal saw_position_row
            try:
                # Guard: don't write to DB until we've confirmed the trade position exists in UI at least once.
                if not saw_position_row:
                    saw_position_row = _position_row_exists(page, symbol)
                    if not saw_position_row:
                        time.sleep(1)
                        saw_position_row = _position_row_exists(page, symbol)
                if not saw_position_row:
                    print("  ⚠ DB update skipped — no position row detected in platform yet")
                    return None

                # Guard: the paired row might not exist yet (race with creator). Confirm existence first.
                exists = (
                    supabase.table("paired_trading_accounts")
                    .select("id")
                    .eq("id", record_id)
                    .limit(1)
                    .execute()
                )
                if not (exists.data and len(exists.data) > 0):
                    time.sleep(1)
                    exists = (
                        supabase.table("paired_trading_accounts")
                        .select("id")
                        .eq("id", record_id)
                        .limit(1)
                        .execute()
                    )
                if not (exists.data and len(exists.data) > 0):
                    print(f"  ⚠ DB update skipped — paired_trading_accounts row not found: id={record_id}")
                    return None

                # Small delay to avoid immediate write races after detection.
                time.sleep(1)
                res = supabase.table("paired_trading_accounts").update(payload).eq("id", record_id).execute()
                if res.data:
                    print(f"  📝 DB update OK — {list(payload.keys())}")
                else:
                    print(f"  ⚠ DB update returned no data — payload={payload} | response={res}")
                return res
            except Exception as e:
                print(f"  ❌ DB update FAILED — payload={payload} | error={e}")
                return None

        if not db_account_id and account_id:
            db_account_id = _resolve_db_account_id(supabase, account_id)
            if db_account_id:
                print(f"🔑 Resolved DB account ID '{db_account_id}' from platform ID '{account_id}'")

        balance_locator = _get_balance_locator(page)
        initial_text = balance_locator.inner_text() if balance_locator else ""
        initial_balance = _parse_balance(initial_text) if initial_text else 0.0
        
        print(f"DEBUG - Full Footer Text Captured: {initial_text}")
        print(f"💰 Starting Balance: {initial_balance}")
        print(f"⏳ Waiting for balance to change from {initial_balance} to detect Take Profit / Stop Loss...")

        if db_account_id:
            record = _find_relevant_pairing(supabase, db_account_id)
            if record:
                paired_record_id = record["id"]
                is_primary = (record["primary_account_id"] == db_account_id)
                print(f"🔗 Paired trade detected. DB Record: {paired_record_id} (Is Primary: {is_primary})")

                # Write starting balance to DB immediately (best-effort)
                balance_col = "primary_starting_balance" if is_primary else "secondary_starting_balance"
                _update_paired_record(paired_record_id, {balance_col: initial_balance})
                print(f"💾 Saved starting balance {initial_balance} → {balance_col}")
            else:
                print("ℹ️ No relevant paired trade found (yet). Running balance-only monitoring.")

        final_balance = None
        loop_i = 0
        
        while True:
            loop_i += 1
            if time.time() - start_ts > timeout_seconds:
                return {
                    "success": False,
                    "reason": f"Trade terminator timed out after {timeout_seconds}s",
                    "warning": None,
                }

            _refresh_workspace(page)
            page.wait_for_timeout(300)

            # --- Try to attach to pairing if we didn't find it yet ---
            if (not paired_record_id) and db_account_id and (loop_i % 8 == 0):  # ~ every 2.4s
                record = _find_relevant_pairing(supabase, db_account_id)
                if record:
                    paired_record_id = record["id"]
                    is_primary = (record["primary_account_id"] == db_account_id)
                    print(f"🔗 Paired trade detected (late attach). DB Record: {paired_record_id} (Is Primary: {is_primary})")

            # --- Check Database Signal ---
            if paired_record_id:
                try:
                    res = supabase.table("paired_trading_accounts").select(
                        "exit_signal, exit_triggered_by, primary_termination_status, secondary_termination_status"
                    ).eq("id", paired_record_id).execute()
                    if res.data and len(res.data) > 0:
                        db_signal = res.data[0].get("exit_signal")
                        trigger = res.data[0].get("exit_triggered_by")
                        status_col = "primary_termination_status" if is_primary else "secondary_termination_status"
                        my_status = res.data[0].get(status_col)
                        
                        if db_signal and trigger != db_account_id and my_status != "completed":
                            role = "PRIMARY" if is_primary else "SECONDARY"
                            print(f"\n📡 [{role}] RECEIVED exit signal '{db_signal}' from partner (triggered by {trigger})")
                            print(f"🤖 [{role}] This device is closing position via AUTOMATION (partner triggered)")
                            print("🔪 Executing 'close-position' to terminate paired trade...")
                            close_result = close_position(page, symbol)
                            
                            # Wait for balance to update after closing, then read it
                            final_balance_received = None
                            try:
                                print(f"⏳ Waiting for balance to update from {initial_balance}...")
                                for attempt in range(50):  # 50 x 300ms = 15 seconds max
                                    page.wait_for_timeout(300)
                                    final_text = balance_locator.inner_text()
                                    final_balance_received = _parse_balance(final_text)
                                    if final_balance_received != initial_balance and final_balance_received > 0:
                                        print(f"💾 Final balance after automation close: {final_balance_received} (took ~{(attempt+1)*0.3:.1f}s)")
                                        break
                                else:
                                    print(f"⚠️ Balance didn't change after 15s. Using last read: {final_balance_received}")
                            except Exception as e:
                                print(f"⚠️ Error reading final balance: {e}")
                                final_balance_received = None
                                
                            balance_col = "primary_final_balance" if is_primary else "secondary_final_balance"
                            
                            update_payload = {
                                status_col: "completed",
                                "trade_status": "done",
                                "is_active": False
                            }
                            if final_balance_received is not None:
                                update_payload[balance_col] = final_balance_received
                                
                            _update_paired_record(paired_record_id, update_payload)
                            print(f"✅ [{role}] Closed by AUTOMATION — trade_status=done, {status_col}=completed")

                            return {
                                "success": True,
                                "reason": f"[AUTOMATION] Closed via DB signal: {db_signal}",
                                "warning": close_result.get("reason") if isinstance(close_result, dict) else None,
                            }
                except Exception as e:
                    print(f"  ⚠ DB Poll Error: {e}")

            # --- Check Physical Balance ---
            if balance_locator and initial_balance > 0:
                try:
                    current_text = balance_locator.inner_text()
                    current_balance = _parse_balance(current_text)
                    if current_balance != initial_balance and current_balance > 0:
                        final_balance = current_balance
                        break
                except Exception:
                    pass

        # 3. Evaluate the result
        print("\n🚨 Balance changed! Reacting immediately...")
        print("-" * 40)
        signal_type = None
        
        if final_balance > initial_balance:
            print(f"✅ SUCCESS: TAKE PROFIT HIT! (Balance increased to {final_balance})")
            result = "TAKE_PROFIT"
            signal_type = "pair_tp"
        else: # final_balance < initial_balance
            print(f"❌ SUCCESS: STOP LOSS HIT! (Balance decreased to {final_balance})")
            result = "STOP_LOSS"
            signal_type = "pair_sl"
        print("-" * 40)
        
        # --- Broadcast Exit Signal + Write OWN termination status + final balance ---
        role = "PRIMARY" if is_primary else "SECONDARY"
        print(f"\n🚀 [{role}] This device TRIGGERED the close — broadcasting signal to partner...")
        if paired_record_id and signal_type:
            status_col = "primary_termination_status" if is_primary else "secondary_termination_status"
            balance_col = "primary_final_balance" if is_primary else "secondary_final_balance"
            
            _update_paired_record(paired_record_id, {
                "exit_signal": signal_type,
                "exit_triggered_by": db_account_id,
                "trade_status": "done",
                "is_active": False,
                status_col: "completed",
                balance_col: final_balance
            })
            print(f"✅ [{role}] TRIGGERED close — exit_signal={signal_type}, {status_col}=completed, trade_status=done")

        return {"success": True, "reason": f"Trade closed. Result: {result}", "warning": None}

    except Exception as e:
        print(f"Error monitoring close: {str(e)}")
        return {"success": False, "reason": str(e), "warning": None}
