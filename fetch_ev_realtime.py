import asyncio
import json
from playwright.async_api import async_playwright

async def fetch_ev_data():
    """從 CEM 網站爬取實時 EV 充電位數據"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print('Fetching EV data from CEM...', file=__import__('sys').stderr)
        await page.goto('https://ev.cem-macau.com/zh/WhereToCharge', 
                       wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(10000)
        
        # 在頁面上下文中執行 JavaScript
        result = await page.evaluate('''
            data.list.map(s => {
                const availablePiles = s.pilerecords ? s.pilerecords.filter(p => p.status === 0).length : 0;
                const totalPiles = s.pilerecords ? s.pilerecords.length : 0;
                let name = s.stationname.replace(/停車場$/, '').trim();
                return { name: name, available: availablePiles, total: totalPiles };
            })
        ''')
        
        await browser.close()
        
        # 轉換為 Dict[name] = available
        result_dict = {}
        for item in result:
            result_dict[item['name']] = item['available']
        
        return result_dict

if __name__ == '__main__':
    import sys
    result = asyncio.run(fetch_ev_data())
    print(json.dumps(result, ensure_ascii=False))