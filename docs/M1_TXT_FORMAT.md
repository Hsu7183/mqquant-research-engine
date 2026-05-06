# M1 TXT Format

M1 TXT 是行情資料，不是交易紀錄。

歷史 `01-01-01` bundle 曾提供 M1 行情範例，原始格式如下：

```text
20200102 084500 12044 12047 12040 12047
```

在 v2 標準版中，舊 `01-01-01/` bundle 已移除；M1 parser 不依賴該資料包。實際使用時請將 M1 TXT 放在自己的 run/data 來源位置，再用 `parse_m1_txt()` 讀取。

常見格式為無 header、空白分隔。

欄位意義：

- date
- time
- open
- high
- low
- close
- volume（可選）

## 與 Trade TXT 的差異

Trade TXT 是交易紀錄，會被解析成 `TradeRecord`，包含：

- entry_time
- exit_time
- entry_price
- exit_price
- direction
- pnl

M1 TXT 是行情 K 棒資料，會被解析成 `BarRecord`，包含：

- ts
- open
- high
- low
- close
- volume

兩者不可混用。M1 TXT 只是行情輸入，尚未代表任何策略交易。

## 支援格式

`parse_m1_txt()` 支援：

- 逗號分隔
- tab 分隔
- 空白分隔
- 有 header
- 無 header

支援時間格式：

- `YYYYMMDDhhmmss`
- `YYYY/MM/DD HH:MM`
- `YYYY-MM-DD HH:MM`

## 下一步

下一步會使用：

```text
M1 TXT + strategy logic -> TradeRecord
```

也就是說，未來 backtest engine 會先讀取 M1 行情，再由策略邏輯產生標準交易紀錄。M1 parser 本身不做回測、不下單，也不連接券商或 XQ API。
