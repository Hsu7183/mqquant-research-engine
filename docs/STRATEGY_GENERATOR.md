# Strategy Generator

## 定位

mqquant 不固定使用 0313，也不固定使用 1001plus+。

1001plus+ 只作為技術元件與設計參考，不是唯一策略來源。

目前系統會根據台指期 1 分 K M1 行情，自動生成多種日當沖策略族群，並將結果送進 L1-L4 流程篩選。

## 策略族群

- `trend_breakout`：趨勢突破
- `open_range_breakout`：開盤區間突破 ORB
- `vwap_pullback`：VWAP 趨勢拉回
- `mean_reversion_range`：區間反轉
- `volume_breakout`：量能爆發突破
- `breakdown_momentum`：急跌追空 / 急拉追多
- `slow_grind_trend`：緩漲 / 緩跌趨勢
- `afternoon_trend_extension`：午後趨勢延伸

每個 family 都支援：

- long
- short
- both

## 生成方式

`generate_intraday_futures_strategies()` 會依指定 family 與 seed 產生可重現的策略集合。

策略包含：

- strategy_id
- family
- direction
- params

同一 seed 會產生相同策略清單。

## 回測規則

所有 generated strategy 回測都遵守：

- 只使用 M1 bar
- 只能用前一根或更早資料判斷進場
- 當根 open 進場
- 出場優先
- 單 bar 單次交易
- 不隔夜
- force_exit_time 強制平倉
- pnl 使用點數

## L1-L4 篩選

所有策略都必須經過：

```text
M1 行情
-> 策略生成器
-> 多策略回測
-> Ranking
-> Detail
-> Forward
-> Auto Promotion
-> Dashboard
```

## 風險與邊界

- 不接券商
- 不接 XQ API
- 不下單
- 策略生成不保證獲利
- 必須經過 forward test
- promotion recommendation 仍需人工確認

## 交易成本模型

策略搜尋、WFO ranking、weekly_pnl、equity_curve、strategy_detail KPI 與 dashboard 顯示，預設全部使用扣成本後 net pnl。

預設台指期成本假設：

- 小台 `point_value = 50`
- 單邊滑點 `slippage_points_per_side = 2`
- 來回滑點 4 點
- 期交稅率 `tax_rate = 0.00002`
- 單邊手續費 `fee_money_per_side = 0`，可用 `--fee-money` 指定
- 口數 `qty = 1`

1 分 K 短線策略若不納入滑點、手續費與期交稅，績效會嚴重高估。因此所有 generated strategy 都必須經過成本壓力測試，觀察 2、3、4、5 點單邊滑點情境下是否仍具備正淨利與合理 PF。

## 效能建議

策略搜尋支援多核心 parallel backtest、進度 log 與快速資料切片。

常用指令：

```powershell
# debug
python -m mqre_v2.cli.run_strategy_search --m1-path M1.txt --num-strategies 5 --workers 1 --sample-bars 50000 --start-date 2020-01-01 --end-date 2026-12-31

# 小測
python -m mqre_v2.cli.run_strategy_search --m1-path M1.txt --num-strategies 20 --workers 2 --start-date 2020-01-01 --end-date 2026-12-31

# 正式
python -m mqre_v2.cli.run_strategy_search --m1-path M1.txt --num-strategies 300 --workers 0 --start-date 2020-01-01 --end-date 2026-12-31
```

參數說明：

- `--workers 0`：自動使用 `cpu_count - 1`
- `--workers 1`：單核心，適合 debug
- `--sample-bars N`：只用最後 N 根 M1 bars 做快速測試
- `--dry-run`：只生成策略，不跑回測、不產生 TXT
- `--progress-every N`：每完成 N 組策略輸出一次進度

若電腦卡住，可用：

```powershell
Stop-Process -Name python -Force
```
