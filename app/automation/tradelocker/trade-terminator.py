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
        print(f"Error resolving DB account ID: {e}")

    return None


def _parse_balance(text: str) -> float:
    clean = re.sub(r"[^\d.]", "", (text or "").replace("\n", " "))
    if not clean:
        return 0.0
    return float(clean)


def _get_balance_locator(page):
    locators = [
        page.locator("div:has-text('Balance')").last,
        page.locator("span:has-text('Balance') >> xpath=../..").last,
        page.locator("div:has-text('BALANCE')").last,
        page.locator("div:has-text('Equity')").last,
        page.locator("div:has-text('EQUITY')").last,
    ]
    for loc in locators:
        try:
            if loc.is_visible(timeout=800):
                return loc
        except Exception:
            continue
    return None


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

    timeout_seconds = int(os.getenv("TRADELOCKER_TERMINATOR_TIMEOUT_SEC", "3600"))
    start_ts = time.time()

    try:
        supabase = get_supabase()
        paired_record_id = None
        is_primary = None

        if not db_account_id and account_id:
            db_account_id = _resolve_db_account_id(supabase, account_id)

        if db_account_id:
            try:
                res = supabase.table("paired_trading_accounts").select("id, primary_account_id, secondary_account_id").or_(
                    f"primary_account_id.eq.{db_account_id},secondary_account_id.eq.{db_account_id}"
                ).eq("is_active", True).execute()
                if res.data:
                    record = res.data[0]
                    paired_record_id = record["id"]
                    is_primary = (record["primary_account_id"] == db_account_id)
            except Exception as e:
                print(f"Failed to query paired account status: {e}")

        balance_locator = _get_balance_locator(page)
        initial_balance = None
        if balance_locator:
            try:
                initial_balance = _parse_balance(balance_locator.inner_text())
            except Exception:
                initial_balance = None

        while True:
            if time.time() - start_ts > timeout_seconds:
                return {
                    "success": False,
                    "reason": f"Trade terminator timed out after {timeout_seconds}s",
                    "warning": None,
                }

            _refresh_workspace(page)
            page.wait_for_timeout(300)

            if paired_record_id:
                try:
                    res = supabase.table("paired_trading_accounts").select("exit_signal, exit_triggered_by").eq("id", paired_record_id).execute()
                    if res.data:
                        signal = res.data[0].get("exit_signal")
                        triggered_by = res.data[0].get("exit_triggered_by")
                        if signal and triggered_by != db_account_id:
                            close_result = close_position(page, symbol)
                            status_col = "primary_termination_status" if is_primary else "secondary_termination_status"
                            try:
                                supabase.table("paired_trading_accounts").update({
                                    status_col: "completed",
                                    "trade_status": "done"
                                }).eq("id", paired_record_id).execute()
                            except Exception:
                                pass

                            return {
                                "success": True,
                                "reason": f"Closed via DB paired signal: {signal}",
                                "warning": close_result.get("reason") if isinstance(close_result, dict) else None,
                            }
                except Exception as e:
                    print(f"DB poll error: {e}")

            if balance_locator and initial_balance is not None:
                try:
                    current_balance = _parse_balance(balance_locator.inner_text())
                    if current_balance != initial_balance:
                        signal_type = "pair_tp" if current_balance > initial_balance else "pair_sl"
                        if paired_record_id and db_account_id:
                            try:
                                supabase.table("paired_trading_accounts").update({
                                    "exit_signal": signal_type,
                                    "exit_triggered_by": db_account_id,
                                    "trade_status": "done"
                                }).eq("id", paired_record_id).execute()
                            except Exception:
                                pass

                        return {
                            "success": True,
                            "reason": "Trade termination condition detected from balance change",
                            "warning": None,
                        }
                except Exception:
                    pass

    except Exception as e:
        return {"success": False, "reason": str(e), "warning": None}
