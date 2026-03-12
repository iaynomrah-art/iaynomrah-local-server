import re
import time
import importlib
from app.core.supabase import get_supabase

close_position_module = importlib.import_module("app.automation.ctrader.close-position")
close_position = close_position_module.close_position

def _resolve_db_account_id(supabase, platform_id: str) -> str:
    """
    Resolves a cTrader numeric platform_id (e.g. '5752716') to its 
    corresponding database hex ID in the 'trading_accounts' table.
    """
    try:
        # Chain: credentials.platform_id -> package.credential_id -> funder_account.package_id -> trading_accounts.funder_account_id
        res = supabase.table("credentials") \
            .select("id, package(id, funder_account(id, trading_accounts(id)))") \
            .eq("platform_id", platform_id) \
            .execute()
        
        if res.data and len(res.data) > 0:
            # A single platform_id might have multiple credential rows, some of which 
            # might not have a full package -> funder_account -> trading_accounts chain.
            # We iterate through all of them to find the first valid trading account ID.
            for row in res.data:
                pkgs = row.get("package", [])
                pkg = pkgs[0] if isinstance(pkgs, list) and pkgs else pkgs
                if pkg:
                    f_accs = pkg.get("funder_account", [])
                    f_acc = f_accs[0] if isinstance(f_accs, list) and f_accs else f_accs
                    if f_acc:
                        t_accs = f_acc.get("trading_accounts", [])
                        t_acc = t_accs[0] if isinstance(t_accs, list) and t_accs else t_accs
                        if t_acc:
                            return t_acc.get("id")
        return None
    except Exception as e:
        print(f"  ⚠ Error resolving DB account ID: {e}")
        return None

def terminate_trade(page, symbol: str, account_id: str = None, db_account_id: str = None):
    print(f"\n👀 Monitoring started for {symbol} on account {account_id} / DB {db_account_id}...")

    def _update_paired_record(supabase, record_id, payload):
        """Update a paired_trading_accounts record and log the full response so errors are visible."""
        try:
            res = supabase.table("paired_trading_accounts").update(payload).eq("id", record_id).execute()
            if res.data:
                print(f"  📝 DB update OK — {list(payload.keys())}")
            else:
                print(f"  ⚠ DB update returned no data — payload={payload} | response={res}")
            return res
        except Exception as e:
            print(f"  ❌ DB update FAILED — payload={payload} | error={e}")
            return None

    def parse_balance(text: str) -> float:
        # Strip out new lines to make it a single string
        text = text.replace('\n', ' ')
        
        # Isolate just the balance part if both labels exist
        if "Balance:" in text and "Equity:" in text:
            # Get the substring between "Balance:" and "Equity:"
            text = text.split("Balance:")[1].split("Equity:")[0]
            
        # Strip all letters, spaces, and currency symbols, keep only numbers and decimals
        clean_string = re.sub(r'[^\d.]', '', text)
        if not clean_string:
            print(f"⚠️ Failed to parse balance from string: '{text}'")
            return 0.0
            
        return float(clean_string)

    def get_balance_locator():
        # First strategy: The exact hierarchy from the screenshot
        # A div that has a child div containing 'Balance:' exactly
        locs = [
            page.locator("div:has(> div:has-text('Balance:'))").last,
            # Fallback 1: Look for any container that has BOTH words to force it up the tree
            page.locator("div:has-text('Balance:'):has-text('Equity:')").last,
            # Fallback 2: Find the span containing Balance:, go up two parents
            page.locator("span:has-text('Balance:') >> xpath=../..").last,
            # Fallback 3: Find the word Balance:, go to the next sibling div
            page.locator("div:has-text('Balance:') + div").last
        ]
        
        for loc in locs:
            try:
                if loc.is_visible(timeout=1000):
                    text = loc.inner_text()
                    if parse_balance(text) > 0:
                        return loc
            except Exception:
                pass
                
        # If all fail, return the first one as fallback and hope for the best
        return locs[0]

    try:
        # 1. Grab Initial Balance
        balance_locator = get_balance_locator()
        
        initial_text = balance_locator.inner_text()
        print(f"DEBUG - Full Footer Text Captured: {initial_text}")
        
        initial_balance = parse_balance(initial_text)
        print(f"💰 Starting Balance: {initial_balance}")
        print(f"⏳ Waiting for balance to change from {initial_balance} to detect Take Profit / Stop Loss...")

        # -- Setup Supabase Connection --
        supabase = get_supabase()
        paired_record_id = None
        is_primary = None
        
        # If db_account_id wasn't passed in, try to resolve it from the platform account_id
        if not db_account_id and account_id:
            db_account_id = _resolve_db_account_id(supabase, account_id)
            if db_account_id:
                print(f"🔑 Resolved DB account ID '{db_account_id}' from platform ID '{account_id}'")
        
        if db_account_id:
            try:
                print(f"🔑 Using DB ID '{db_account_id}' directly from pairing session.")
                
                # Find the pairing where this account is either primary or secondary
                res = supabase.table("paired_trading_accounts").select("id, primary_account_id, secondary_account_id").or_(f"primary_account_id.eq.{db_account_id},secondary_account_id.eq.{db_account_id}").neq("trade_status", "done").order("created_at", desc=True).limit(1).execute()
                if res.data and len(res.data) > 0:
                    record = res.data[0]
                    paired_record_id = record['id']
                    is_primary = (record['primary_account_id'] == db_account_id)
                    print(f"🔗 Paired trade detected. DB Record: {paired_record_id} (Is Primary: {is_primary})")
                    
                    # Write starting balance to DB immediately
                    balance_col = "primary_starting_balance" if is_primary else "secondary_starting_balance"
                    _update_paired_record(supabase, paired_record_id, {balance_col: initial_balance})
                    print(f"💾 Saved starting balance {initial_balance} → {balance_col}")
            except Exception as e:
                print(f"  ⚠ Failed to query paired account status: {e}")
        else:
            print(f"  ⚠ No db_account_id provided for platform ID '{account_id}'")

        # 2. Poll for balance changes AND database signals
        while True:
            # Wait 200ms between checks for near-instant reaction
            page.wait_for_timeout(200)
            
            # --- Check Database Signal ---
            if paired_record_id:
                try:
                    res = supabase.table("paired_trading_accounts").select("exit_signal, exit_triggered_by").eq("id", paired_record_id).execute()
                    if res.data and len(res.data) > 0:
                        db_signal = res.data[0].get("exit_signal")
                        trigger = res.data[0].get("exit_triggered_by")
                        
                        # Only act if there is a signal AND we didn't trigger it ourselves
                        if db_signal and trigger != db_account_id:
                            role = "PRIMARY" if is_primary else "SECONDARY"
                            print(f"\n📡 [{role}] RECEIVED exit signal '{db_signal}' from partner (triggered by {trigger})")
                            print(f"🤖 [{role}] This device is closing position via AUTOMATION (partner triggered)")
                            print("🔪 Executing 'close-position' to terminate paired trade...")
                            close_result = close_position(page, symbol)
                            
                            # Read final balance after closing
                            try:
                                final_text = balance_locator.inner_text()
                                final_balance_received = parse_balance(final_text)
                                print(f"💾 Final balance after automation close: {final_balance_received}")
                            except Exception:
                                final_balance_received = None
                            
                            # Write termination status + final balance + trade_status = done
                            status_col = "primary_termination_status" if is_primary else "secondary_termination_status"
                            balance_col = "primary_final_balance" if is_primary else "secondary_final_balance"
                            update_payload = {
                                status_col: "completed",
                                "trade_status": "done",
                                "is_active": False
                            }
                            if final_balance_received is not None:
                                update_payload[balance_col] = final_balance_received
                            _update_paired_record(supabase, paired_record_id, update_payload)
                            print(f"✅ [{role}] Closed by AUTOMATION — trade_status=done, {status_col}=completed")
                                
                            return {"success": True, "reason": f"[AUTOMATION] Closed via DB signal: {db_signal}", "warning": close_result.get("reason")}
                except Exception as e:
                    print(f"  ⚠ DB Poll Error: {e}")
            
            # --- Check Physical Balance ---
            current_text = balance_locator.inner_text()
            current_balance = parse_balance(current_text)
            
            if current_balance != initial_balance:
                final_balance = current_balance
                break

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
            _update_paired_record(supabase, paired_record_id, {
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