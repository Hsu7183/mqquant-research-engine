# M1 Backtest MVP

## 目的

M1 TXT 是行情資料，內容代表每一分鐘的 OHLC bar。

Trade TXT 是交易紀錄，內容代表策略實際產生的進出場事件。Dashboard、WFO pipeline、weekly equity、weekly pnl 與 KPI 都需要 TradeRecord 才能運作。

本 MVP 建立最小流程：

```text
M1 TXT -> BarRecord -> SimpleM1StrategyParams -> TradeRecord -> Trade TXT
```

## MVP 策略

目前策略為簡化 momentum 範例，不是正式 0313 / 1001 策略。

進場：

- 前一根 bar 上漲超過 `entry_buffer`，下一根 open 做多
- 前一根 bar 下跌超過 `entry_buffer`，下一根 open 做空

出場：

- take profit
- stop loss
- max hold bars
- force exit time

所有進出場都使用當根 open，進場訊號只使用前一根已完成 bar，避免未來值。

## CLI

```powershell
python -m mqre_v2.cli.backtest_m1 `
  --m1-path M1.txt `
  --output-trade-txt tmp/m1_backtest_demo.txt `
  --strategy-name simple_m1_demo
```

輸出 JSON summary，並產生可被 `parse_xs_txt()` 讀回的 Trade TXT。

## Dashboard Demo Flow

可用：

```powershell
python -m mqre_v2.cli.backtest_m1_to_latest --m1-path M1.txt --strategy-name simple_m1_demo
```

這會輸出：

```text
runs/latest/txt/simple_m1_demo.txt
```

後續可再接 WFO / Run Pipeline 產生 `runs/latest/reports/` 與 dashboard detail JSON。

## 邊界

- 不接券商
- 不下單
- 不接 XQ API
- 不修改歷史 01-01-01
- 不代表正式 0313 / 1001 策略績效

後續可將正式策略邏輯接入同一個 `BarRecord -> TradeRecord` 介面。
