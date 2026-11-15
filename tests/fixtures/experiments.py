from types import SimpleNamespace
import json
import numpy as np
import pandas as pd
from betalens.factor.mining_audit import FactorMiningResult, MiningResult
from betalens.experiments.snapshot import Snapshot

def bt():
    days = pd.date_range("2025-01-02", periods=8, name="datetime")
    returns = pd.Series([.01, -.02, .03, .005, -.008, .02, .01, -.003], index=days)
    amounts = (1 + returns).cumprod() * 100_000
    nav = pd.concat([pd.Series([1.], index=pd.DatetimeIndex([pd.Timestamp("2025-01-01")], name="datetime")), amounts / 100_000]).rename("nav")
    weights = pd.DataFrame({"000001.SZ": .8, "cash": .2}, index=days)
    values = weights.mul(amounts, axis=0)
    logs = pd.DataFrame(columns=["datetime", "code", "direction", "shares", "signed_shares", "value", "price", "equity_before", "fee"])
    prices = pd.DataFrame({"000001.SZ": np.linspace(10., 11., len(days)), "cash": 1.}, index=days)
    return SimpleNamespace(nav=nav, daily_returns=returns, daily_amount=amounts,
        weight=weights, actual_weight=weights.copy(), daily_weight=weights.copy(),
        daily_position_value=values, daily_pnl=weights.mul(amounts.diff().fillna(1000), axis=0),
        position=values / prices, rebalance_log=logs, cost_price=prices,
        synthetic_settlements=pd.DataFrame(), risk_events=pd.DataFrame(),
        symbol="测试组合", metric="close", initial_amount=100_000, ftc=0., ptc=0.,
        start=days[0], end=days[-1], calculation_version="backtest-v2-drift-risk", data_sources={"prices": "database"})


def config(window=20):
    return {"factor_spec": {"compute_kwargs": {"window": window}}, "run": {"rebal_freq": "W"}}


def mining_result(tmp_path, *, captured=False, capture_error=False):
    rows = pd.DataFrame([
        {"candidate_id": c, "params_json": json.dumps({"window": w}), "window_id": f"252/21/{i}",
         "window_start": "2025-01-01", "window_end": "2025-01-09", "sharpe": score, "ann_ret": .1, "error": None}
        for c, w, score in (("c1", 20, 1.), ("c2", 60, 2.)) for i in range(2)])
    summary = pd.DataFrame([{"candidate_id": c, "params_json": json.dumps({"window": w}), "objective": score, "sharpe_median": score} for c, w, score in (("c1", 20, 1.), ("c2", 60, 2.))])
    snapshot = Snapshot(tables={"nav": pd.Series([1., 1.1], index=pd.date_range("2025-01-01", periods=2))}, metrics={"夏普比率": 3.})
    run = FactorMiningResult("动量", "run-1", tmp_path, "complete", stage_window_results={"coarse": rows, "fine": rows.copy()},
        stage_summaries={"coarse": summary, "fine": summary.copy()}, selected_candidates=summary.iloc[1:].copy(),
        archive_context={"factor_class": "量价", "strategy_type": "cross_sectional"},
        candidate_configs={"c1": config(20), "c2": config(60)},
        selected_results={"c2": {"scopes": {"total": snapshot}, "config": config(60)}} if captured else {},
        capture_errors={"c2": "capture failed"} if capture_error else {})
    return MiningResult("launch-1", (run,))
