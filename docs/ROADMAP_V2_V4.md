# mqquant Roadmap v2～v4

## v1：Strategy Governance System

狀態：stable / frozen

定位：

- 策略研究
- WFO 驗證
- Forward Test 管理
- Strategy Registry

不得新增實驗功能到 v1。

## v2：XQ Semi-Automation Layer

目標：

- 管理 XS 批次產生
- 管理 XQ 回測輸出 TXT
- 強化 TXT pipeline
- 建立批次任務資料夾規範

不包含：

- 不控制券商
- 不自動下單
- 不接交易 API

預計功能：

- runs/ 批次任務資料夾
- batch manifest
- XS → TXT 對應關係
- 回測結果完整性檢查
- 缺檔 / 壞檔報告

## v3：Cloud Report Layer

目標：

- JSON 報表標準化
- GitHub Actions 自動跑測試
- Supabase / 靜態網站讀報表
- 策略排行榜視覺化

不包含：

- 不自動交易
- 不直接修改策略

預計功能：

- reports/*.json schema
- dashboard data export
- GitHub Actions report validation
- website data contract

## v4：Auto Decision Layer

目標：

- 系統自動產生策略升級建議
- baseline / challenger / registry 整合
- 自動產生 promote / reject recommendation
- 仍需人工確認，不自動交易

不包含：

- 不下單
- 不接券商
- 不自動切換實盤策略

預計功能：

- promotion recommendation report
- risk warning
- forward test score
- baseline replacement suggestion
- decision audit log

## v5：Execution Layer

暫不開發。

原因：

- 風險最高
- 需要券商 / XQ 實盤細節
- 需要完整風控與停機機制
