# 澳門停車場空位查詢系統

即時查詢澳門各停車場空位狀況。

## 功能

- 即時顯示 82 個停車場空位數據
- 交通燈式狀態顯示（綠/黃/紅）
- 每 60 秒自動刷新
- 按剩餘車位/總車位/名稱排序

## 技術棧

- Frontend: React 19 + Vite + Tailwind CSS
- Backend: Express.js + TypeScript + PostgreSQL
- 數據來源: 澳門交通事務局 API

## 快速開始

```bash
# 安裝依賴
cd backend && npm install
cd ../frontend && npm install

# 配置環境變量
cp backend/.env.example backend/.env

# 運行數據庫遷移
cd backend && npx prisma migrate dev

# 啟動後端
cd backend && npm run dev

# 啟動前端
cd frontend && npm run dev
```

## API 端點

- `GET /api/carparks` - 獲取所有停車場
- `POST /api/carparks/refresh` - 刷新數據
- `GET /api/carparks/stats` - 獲取統計信息
