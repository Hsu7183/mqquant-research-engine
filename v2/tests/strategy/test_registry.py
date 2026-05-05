import pytest

from mqre_v2.forward.forward_log import ForwardTestRecord, append_forward_record
from mqre_v2.strategy.registry import (
    StrategyRegistryRecord,
    append_strategy_registry_record,
    promote_from_forward_log,
    read_strategy_registry,
    retire_strategy,
)


def _forward_record(strategy_name: str, status: str = "promoted") -> ForwardTestRecord:
    return ForwardTestRecord(
        strategy_name=strategy_name,
        txt_path=f"{strategy_name}.txt",
        status=status,
        created_at="2026-05-06T00:00:00+00:00",
        updated_at="2026-05-06T00:00:00+00:00",
        source_score=123.0,
        source_pass_rate=0.8,
        source_total_test_net_profit=5000.0,
        notes="forward evaluation score=123.0",
    )


def _registry_record(
    strategy_name: str,
    status: str = "active",
) -> StrategyRegistryRecord:
    return StrategyRegistryRecord(
        strategy_name=strategy_name,
        txt_path=f"{strategy_name}.txt",
        status=status,
        promoted_at="2026-05-06T00:00:00+00:00",
        source="forward_log",
        notes="ready",
    )


def test_append_and_read_registry(tmp_path) -> None:
    registry_path = tmp_path / "strategy_registry.csv"
    append_strategy_registry_record(str(registry_path), _registry_record("alpha"))

    records = read_strategy_registry(str(registry_path))

    assert len(records) == 1
    assert records[0].strategy_name == "alpha"
    assert records[0].status == "active"
    assert records[0].source == "forward_log"


def test_promote_from_forward_log_imports_promoted(tmp_path) -> None:
    forward_log_path = tmp_path / "forward_test_log.csv"
    registry_path = tmp_path / "strategy_registry.csv"
    append_forward_record(str(forward_log_path), _forward_record("alpha"))

    added = promote_from_forward_log(str(forward_log_path), str(registry_path))
    records = read_strategy_registry(str(registry_path))

    assert len(added) == 1
    assert len(records) == 1
    assert records[0].strategy_name == "alpha"
    assert records[0].status == "active"
    assert records[0].source == "forward_log"
    assert records[0].notes == "forward evaluation score=123.0"


def test_promote_from_forward_log_skips_active_duplicate(tmp_path) -> None:
    forward_log_path = tmp_path / "forward_test_log.csv"
    registry_path = tmp_path / "strategy_registry.csv"
    append_forward_record(str(forward_log_path), _forward_record("alpha"))

    first_added = promote_from_forward_log(str(forward_log_path), str(registry_path))
    second_added = promote_from_forward_log(str(forward_log_path), str(registry_path))
    records = read_strategy_registry(str(registry_path))

    assert len(first_added) == 1
    assert second_added == []
    assert len(records) == 1
    assert records[0].strategy_name == "alpha"


def test_retire_strategy_updates_active_to_retired(tmp_path) -> None:
    registry_path = tmp_path / "strategy_registry.csv"
    append_strategy_registry_record(str(registry_path), _registry_record("alpha"))

    retire_strategy(str(registry_path), "alpha", notes="replaced by challenger")
    records = read_strategy_registry(str(registry_path))

    assert len(records) == 1
    assert records[0].strategy_name == "alpha"
    assert records[0].status == "retired"
    assert records[0].notes == "replaced by challenger"


def test_retire_missing_strategy_raises(tmp_path) -> None:
    registry_path = tmp_path / "strategy_registry.csv"
    append_strategy_registry_record(str(registry_path), _registry_record("alpha"))

    with pytest.raises(ValueError):
        retire_strategy(str(registry_path), "missing")
