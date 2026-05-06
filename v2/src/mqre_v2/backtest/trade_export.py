from __future__ import annotations

from pathlib import Path

from mqre_v2.core.trades import TradeRecord


def export_trades_to_xs_txt(
    trades: list[TradeRecord],
    output_path: str,
    strategy_name: str,
) -> None:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"Strategy={strategy_name},Version=backtest"]
    for trade in trades:
        lines.append(_entry_line(trade))
        lines.append(_exit_line(trade))

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _entry_line(trade: TradeRecord) -> str:
    action = "新買" if trade.direction == 1 else "新賣"
    return f"{trade.entry_time:%Y%m%d%H%M%S} {_format_price(trade.entry_price)} {action}"


def _exit_line(trade: TradeRecord) -> str:
    action = "平賣" if trade.direction == 1 else "平買"
    return f"{trade.exit_time:%Y%m%d%H%M%S} {_format_price(trade.exit_price)} {action}"


def _format_price(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


__all__ = ["export_trades_to_xs_txt"]
