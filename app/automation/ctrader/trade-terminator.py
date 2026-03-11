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

def terminate_trade(page, symbol: str, account_id: str = None):
    print(f"\n👀 Monitoring started for {symbol} on account {account_id}...")

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
        db_account_id = None  # The resolved DB hex ID
        
        if account_id:
            try:
                # Resolve cTrader platform_id -> trading_accounts DB hex ID
                # Chain: credentials.platform_id -> package.credential_id -> funder_account.package_id -> trading_accounts.funder_account_id
                db_account_id = _resolve_db_account_id(supabase, account_id)
                
                if db_account_id:
                    print(f"🔑 Resolved platform ID '{account_id}' -> DB ID '{db_account_id}'")
                    
                    # Find the pairing where this account is either primary or secondary
                    res = supabase.table("paired_trading_accounts").select("id, primary_account_id, secondary_account_id").or_(f"primary_account_id.eq.{db_account_id},secondary_account_id.eq.{db_account_id}").eq("is_active", True).execute()
                    if res.data and len(res.data) > 0:
                        record = res.data[0]
                        paired_record_id = record['id']
                        is_primary = (record['primary_account_id'] == db_account_id)
                        print(f"🔗 Paired trade detected. DB Record: {paired_record_id} (Is Primary: {is_primary})")
                else:
                    print(f"  ⚠ Could not resolve platform ID '{account_id}' to a DB account ID")
            except Exception as e:
                print(f"  ⚠ Failed to query paired account status: {e}")

        # 2. Poll for balance changes AND database signals
        while True:
            # Wait 2 seconds between checks
            page.wait_for_timeout(2000)
            
            # --- Check Database Signal ---
            if paired_record_id:
                try:
                    res = supabase.table("paired_trading_accounts").select("exit_signal, exit_triggered_by").eq("id", paired_record_id).execute()
                    if res.data and len(res.data) > 0:
                        db_signal = res.data[0].get("exit_signal")
                        trigger = res.data[0].get("exit_triggered_by")
                        
                        # Only act if there is a signal AND we didn't trigger it ourselves
                        if db_signal and trigger != db_account_id:
                            print(f"\n📡 RECEIVED EXIT SIGNAL FROM DB: {db_signal} (Triggered by {trigger})")
                            print("🔪 Executing 'close-position' to terminate paired trade...")
                            close_result = close_position(page, symbol)
                            
                            # Mark our termination status as completed
                            status_col = "primary_termination_status" if is_primary else "secondary_termination_status"
                            try:
                                supabase.table("paired_trading_accounts").update({
                                    status_col: "completed",
                                    "trade_status": "done"  # Set overall status to done
                                }).eq("id", paired_record_id).execute()
                            except Exception:
                                pass
                                
                            return {"success": True, "reason": f"Closed via DB paired signal: {db_signal}", "warning": close_result.get("reason")}
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
        
        # --- Broadcast Exit Signal to Partner ---
        if paired_record_id and signal_type:
            try:
                print(f"📢 Broadcasting {signal_type} to DB so partner device can close...")
                supabase.table("paired_trading_accounts").update({
                    "exit_signal": signal_type,
                    "exit_triggered_by": db_account_id,  # Use resolved DB ID
                    "trade_status": "done"               # Mark as done
                }).eq("id", paired_record_id).execute()
            except Exception as e:
                print(f"  ⚠ Failed to broadcast exit signal: {e}")
        
        return {"success": True, "reason": f"Trade closed. Result: {result}", "warning": None}
    
    except Exception as e:
        print(f"Error monitoring close: {str(e)}")
        return {"success": False, "reason": str(e), "warning": None}