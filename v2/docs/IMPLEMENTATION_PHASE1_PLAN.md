# IMPLEMENTATION_PHASE1_PLAN

## Phase 1 dependency note
- `pandas`：用於 1 分 K 資料載入、欄位標準化與時間序列資料處理。
- `pydantic`：用於 contracts（設定檔與資料結構）驗證，先擋掉不合法輸入。
- `PyYAML`：用於讀取策略/回測設定 YAML。
- `typer`：用於建立最小可用 CLI（例如載入資料與切分流程的指令入口）。
