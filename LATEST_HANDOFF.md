# LATEST_HANDOFF

## 目前狀態（截至 2026-05-04）

1. 已建立 `v2` 乾淨骨架（目前僅保留必要目錄與 placeholder）。
2. 尚未導入舊版 `01-01-01` 內容。
3. 目前 `v2` 程式層仍為 placeholder，尚未進入策略實作。
4. 尚未實作真實策略邏輯。
5. 尚未實作完整 WFO/OOS 計算流程。

## 本次骨架收斂與版控清理

- 新增/更新 `.gitignore`，納入 Python 快取、虛擬環境、日誌、執行產物、資料檔、憑證與系統垃圾檔忽略規則。
- 保留 `v2/runs/.gitkeep` 追蹤方式，並確保 `v2/data/samples/`、`v2/data/schemas/` 可被追蹤。
- 補上 Phase 1 依賴用途說明（`pandas`、`pydantic`、`PyYAML`、`typer`）。

## 目前尚未完成事項

- 尚未建立真實策略訊號與下單決策邏輯。
- 尚未建立完整 optimizer。
- 尚未實作 PBO/DSR、Forward Test、Baseline/Challenger。

## 下一步建議

先完成 `contracts + loaders + WFO splitter` 三個基礎模組，再進入後續策略與驗證流程。
