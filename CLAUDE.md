# 賓果賓果專案 - Claude 行為規則

## 通知規則

完成長時間任務（或需要使用者決定才能繼續）時，**必須**執行以下 PowerShell 通知：

```powershell
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show("任務完成說明", "Claude 通知", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
```

- 長任務完成 → 彈窗說明完成了什麼
- 需要授權才能繼續 → 彈窗寫清楚「需要你決定：XXX」
- 短任務（幾秒內）→ 只在對話框回覆，不彈窗

## 反提問規則（重要）

**每次收到功能需求前，必須先提問釐清**，不能直接動手：

1. 有任何不確定的實作方向 → 先列出選項讓使用者選
2. 需要外部資源（圖片、檔案）才能完成 → 先說明需要什麼再動手
3. 影響範圍大的改動（版面、流程）→ 先描述計畫確認
4. 只有一種做法且非常明確的小修正 → 可以直接做，但完成後說明做了什麼

## 專案結構

- `index.html` — 主遊戲頁面（單一 HTML 檔案）
- `proxy.py` — 本地 CORS 代理，port 8765，抓台彩官方 API
- `.claude/launch.json` — 預覽伺服器設定，port 3333

## 啟動方式

1. `python proxy.py` — 啟動資料代理
2. 預覽伺服器或直接開 `index.html`
