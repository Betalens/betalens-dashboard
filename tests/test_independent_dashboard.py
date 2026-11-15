import copy
from pathlib import Path
import runpy
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest
import yaml

from dashboard.backend import factors, runs
from dashboard.backend.main import app
from dashboard.backend.schemas import RunRequest


@pytest.fixture
def research(tmp_path, monkeypatch):
    root = tmp_path / "a-separate-research-checkout"
    folder = root / "demo/SAMPLE"
    folder.mkdir(parents=True)
    (root / "demo/class_demo.yaml").write_text("meta: {class: demo, name: demo}\n")
    config = {
        "meta": {"class": "demo", "name": "SAMPLE", "formula": "synthetic"},
        "factor_spec": {"inputs": {"close": "close"}, "compute_kwargs": {}, "direction": "positive",
                        "table_name": "market_daily_post_adjusted", "index_code": "000906.SH",
                        "use_industry": False, "use_mktcap": False, "backtest_metric": "close"},
        "weight": {"mode": "classic-long-short", "long_groups": None, "short_groups": None},
        "run": {"start_date": "2025-01-01", "end_date": "2025-01-10", "rebal_freq": "D",
                "n_quantiles": 2, "initial_amount": 100000, "include_profiling": False,
                "dump_excel": False, "output_dir": "${BETALENS_RUNTIME_DIR}/runs/demo/SAMPLE"},
        "experiment_export": {"enabled": False},
    }
    (folder / "factor_SAMPLE.yaml").write_text(yaml.safe_dump(config))
    (folder / "factor_SAMPLE.py").write_text('"""Independent synthetic factor."""\n')
    monkeypatch.setattr(factors, "FACTOR_ROOT", root)
    monkeypatch.setattr(runs, "RUNTIME_ROOT", tmp_path / "runtime")
    monkeypatch.setattr(runs, "_CACHE_ROOT", tmp_path / "runtime/cache")
    factors.clear_factor_cache()
    yield folder, config
    factors.clear_factor_cache()


def test_api_discovers_explicit_external_checkout(research):
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"status": "ok"}
        response = client.get("/api/factors?refresh=true")
        assert response.status_code == 200
        assert [(item["factor_class"], item["name"]) for item in response.json()] == [("demo", "SAMPLE")]
        assert client.get("/api/factors/demo/SAMPLE").json()["formula"] == "synthetic"


def test_execution_delegates_with_matching_identity_and_absolute_outputs(research, tmp_path, monkeypatch):
    from betalens.analyst import Analyst
    folder, config = research
    fixtures = runpy.run_path(str(Path(__file__).parent / "fixtures/experiments.py"))
    backtest = fixtures["bt"]()
    analyst = Analyst.from_backtest(backtest)
    analyst._name_map = {"000001.SZ": "测试证券"}
    result = SimpleNamespace(backtest=backtest, analyst=analyst, factor_values=None,
                             experiment_export={"status": "disabled"})
    calls = []
    def execute(config_path, *, run_id, output_dir):
        effective = yaml.safe_load(Path(config_path).read_text())
        calls.append((run_id, Path(output_dir), effective))
        return result
    monkeypatch.setattr(runs, "load_factor_module", lambda _: SimpleNamespace(FactorPipeline=object, run_from_config=execute))
    manager = runs.RunManager()
    monkeypatch.setattr(manager, "_dump_excel", lambda *_: None)
    run = runs.DashboardRun(RunRequest(factor_class="demo", name="SAMPLE"))
    try:
        manager._execute(run)
        assert run.status == "completed", run.error
        identity, output, effective = calls[0]
        assert identity == run.run_id
        assert output == tmp_path / "runtime/runs/demo/SAMPLE" / run.run_id
        assert effective["run"]["output_dir"] == str(output)
        assert (output / "run_config.yaml").is_file()
    finally:
        manager._executor.shutdown(wait=True)


def test_missing_checkout_has_explicit_configuration_error(tmp_path, monkeypatch):
    from betalens.factor.config import ConfigError
    monkeypatch.setattr(factors, "FACTOR_ROOT", tmp_path / "missing")
    factors.clear_factor_cache()
    with pytest.raises(ConfigError, match="BETALENS_FACTOR_ROOT"):
        factors.discover_factors()
    factors.clear_factor_cache()
