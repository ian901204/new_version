# 文件上傳工具

一個用於將本地文件上傳到遠程伺服器的 GUI 工具。

## 功能特色

- 🔐 安全的環境變數配置
- 📁 支援資料夾批量上傳
- ⌨️ 快捷鍵多選功能
  - **Shift + 點擊**：範圍選擇
  - **Ctrl/Cmd + 點擊**：多選/取消選擇
- 🔄 自動處理重複文件名
- 📊 上傳進度顯示

## 安裝步驟

1. 克隆或下載此專案

2. 安裝依賴套件：
```bash
pip install -r requirements.txt
```

3. 配置環境變數：
   - 複製 `.env.example` 為 `.env`
   ```bash
   cp .env.example .env
   ```
   
   - 編輯 `.env` 文件，填入您的伺服器資訊：
   ```
   SERVER_HOSTNAME=your_server_ip
   SERVER_USERNAME=your_username
   SERVER_PASSWORD=your_password
   SERVER_BASE_PATH=/home/berxel/ftp
   ```

## 使用方法

1. 運行程式：
```bash
python main.py
```

2. 在彈出的視窗中輸入伺服器用戶名和密碼（如果 .env 中未設置）

3. 選擇要上傳的本地資料夾

4. 使用快捷鍵選擇多個資料夾：
   - **單擊**：選擇單個項目
   - **Shift + 點擊**：選擇從上次點擊到當前點擊之間的所有項目
   - **Ctrl/Cmd + 點擊**：添加或移除單個項目

5. 選擇目標伺服器資料夾

6. 點擊「上傳」按鈕

## Git 使用注意事項

⚠️ **重要**：`.env` 文件已被加入 `.gitignore`，不會被提交到 Git。

在上傳到 Git 前請確保：
- `.env` 文件不在提交列表中
- 僅提交 `.env.example` 作為範本
- 不要在代碼中硬編碼任何機密資訊

## 文件結構

```
.
├── main.py                 # 程式入口
├── ui_components.py        # UI 介面組件
├── server_handler.py       # 伺服器連接處理
├── requirements.txt        # Python 依賴
├── .env                    # 環境變數（不提交到 Git）
├── .env.example            # 環境變數範本
├── .gitignore              # Git 忽略文件
└── README.md               # 說明文件
```

## 問題排除

### 無法連接到伺服器
- 檢查 `.env` 文件中的伺服器資訊是否正確
- 確認網路連接正常
- 確認伺服器允許 SSH 連接

### 導入錯誤
- 確保已安裝所有依賴：`pip install -r requirements.txt`
- 檢查 Python 版本（建議 Python 3.7+）

## 授權

此專案僅供內部使用。
