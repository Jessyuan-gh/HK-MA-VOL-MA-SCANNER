import yfinance as yf
import pandas as pd
import akshare as ak
import datetime

print("正在獲取最新港股通成份股名單...")
try:
    # 自動從東方財富/港股通接口獲取最新港股通股票代碼及名稱
    ggt_df = ak.stock_hk_ggt_components_em()
    # 轉換代號格式為 Yahoo Finance 適用格式 (例如 "00700" -> "0700.HK")
    code_to_name = {}
    tickers = []
    for _, row in ggt_df.iterrows():
        raw_code = str(row['代码']).zfill(5)
        yf_ticker = f"{raw_code[1:]}.HK" if raw_code.startswith('0') else f"{raw_code}.HK"
        tickers.append(yf_ticker)
        code_to_name[yf_ticker] = row['名称']
    print(f"成功獲取 {len(tickers)} 隻港股通股票！")
except Exception as e:
    print(f"獲取港股通名單失敗，改用備用名單: {e}")
    code_to_name = {"0700.HK": "騰訊控股", "9988.HK": "阿里巴巴", "3690.HK": "美團", "1810.HK": "小米集團"}
    tickers = list(code_to_name.keys())

print("正在批量下載歷史數據並計算指標...")
# 一次過批量下載所有港股通過去 3 個月數據（速度極快）
data = yf.download(tickers, period="3mo", interval="1d", group_by="ticker", threads=True, progress=False)

results = []

for ticker in tickers:
    try:
        df = data[ticker].dropna()
        if len(df) < 50:
            continue

        # 計算均線與成交量均線
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['VOL_MA20'] = df['Volume'].rolling(window=20).mean()

        today = df.iloc[-1]
        
        # 避免成交量為 0 導致除零錯誤
        if today['VOL_MA20'] <= 0:
            continue
            
        vol_ratio = today['Volume'] / today['VOL_MA20']

        # 篩選條件：收市價企穩 MA20 & MA50 + 陽燭 + 成交量 >= 1.5倍 20日均量
        if (today['Close'] > today['MA20'] and 
            today['Close'] > today['MA50'] and 
            today['Close'] > today['Open'] and 
            vol_ratio >= 1.5):
            
            results.append({
                "代號": ticker.replace(".HK", "").zfill(5),
                "名稱": code_to_name.get(ticker, ""),
                "收市價": round(float(today['Close']), 2),
                "MA20": round(float(today['MA20']), 2),
                "MA50": round(float(today['MA50']), 2),
                "成交量倍數": round(float(vol_ratio), 2)
            })
    except Exception:
        continue

# 儲存結果並按「成交量倍數」由大至小排序
out_df = pd.DataFrame(results)
if not out_df.empty:
    out_df = out_df.sort_values(by="成交量倍數", ascending=False)
    out_df["成交量倍數"] = out_df["成交量倍數"].astype(str) + "x"

out_df.to_csv("results.csv", index=False, encoding="utf-8-sig")

# 記錄香港更新時間
hk_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
with open("last_update.txt", "w") as f:
    f.write(hk_time)

print(f"港股通掃描完成！共篩選出 {len(results)} 隻符合條件股票。")
