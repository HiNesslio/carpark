# 澳門停車場實時資訊

一個提供澳門公共停車場即時車位資訊的網頁應用程式。

## 功能特色

- 🚗 顯示附近停車場的即時車位數據（私家車、電單車、貨車）
- ⚡ EV 充電位顯示與過濾
- 🗺️ Google 地圖顯示用戶位置
- 📱 響應式設計，支援手機和平板

## 技術栈

- **後端**: Python Flask
- **前端**: HTML/CSS/JavaScript
- **數據來源**: 
  - DSAT 澳門交通事務局 API
  - CEM 澳電 EV 充電站數據（使用 Playwright 爬蟲）

## 安裝

```bash
# 安裝依賴
pip install -r requirements.txt

# 安裝 Node.js 依賴（用於 Playwright）
npm install
```

## 運行

```bash
python app.py
```

訪問 http://localhost:5000

## 項目結構

```
.
├── app.py                    # Flask 後端 API
├── carpark_service.py       # 停車場數據服務
├── carpark_locations.py     # 停車場座標數據
├── templates/
│   └── index.html           # 前端頁面
├── test_*.py                # 測試文件
└── DESIGN.md                # 設計系統
```

## License

MIT