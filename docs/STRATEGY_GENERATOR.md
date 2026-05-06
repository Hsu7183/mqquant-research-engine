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
