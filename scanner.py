import yfinance as yf
import pandas as pd
import akshare as ak
import datetime

print("正在獲取最新港股通成份股名單...")
try:
    ggt_df = ak.stock_hk_ggt_components_em()
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
data = yf.download(tickers, period="3mo", interval="1d", group_by="ticker", threads=True, progress=False)

results = []

for ticker in tickers:
    try:
        df = data[ticker].dropna()
        if len(df) < 50:
            continue

        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['VOL_MA20'] = df['Volume'].rolling(window=20).mean()

        today = df.iloc[-1]
        if today['VOL_MA20'] <= 0:
            continue
            
        vol_ratio = today['Volume'] / today['VOL_MA20']

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

out_df = pd.DataFrame(results)
if not out_df.empty:
    out_df = out_df.sort_values(by="成交量倍數", ascending=False)
    out_df["成交量倍數"] = out_df["成交量倍數"].astype(str) + "x"

out_df.to_csv("results.csv", index=False, encoding="utf-8-sig")

hk_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M")
with open("last_update.txt", "w") as f:
    f.write(hk_time)

table_html = out_df.to_html(index=False, border=0, classes="stock-table") if not out_df.empty else "<p class='empty'>今日暫時未有港股通股票符合條件。</p>"

html_content = f"""<!DOCTYPE html>
<html lang="zh-HK">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>港股通 MA + 大成交訊號</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 16px; background: #f8f9fa; color: #212529; }}
  .container {{ max-width: 680px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
  h1 {{ font-size: 22px; margin: 0 0 8px 0; }}
  .time {{ font-size: 13px; color: #6c757d; margin-bottom: 16px; }}
  .metric {{ background: #eef4ff; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }}
  .metric-label {{ font-size: 13px; color: #495057; }}
  .metric-val {{ font-size: 28px; font-weight: bold; color: #0d6efd; }}
  .table-wrap {{ overflow-x: auto; }}
  .stock-table {{ width: 100%; border-collapse: collapse; font-size: 14px; text-align: left; }}
  .stock-table th {{ background: #f1f3f5; padding: 10px 8px; border-bottom: 2px solid #dee2e6; white-space: nowrap; }}
  .stock-table td {{ padding: 10px 8px; border-bottom: 1px solid #eee; white-space: nowrap; }}
  .empty {{ color: #6c757d; padding: 20px 0; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <h1>📈 港股通 MA + 大成交訊號</h1>
  <div class="time">最後更新時間 (HKT)：{hk_time}（每日 16:15 自動更新）</div>
  <div class="metric">
    <div class="metric-label">今日符合條件股票數量</div>
    <div class="metric-val">{len(out_df)}</div>
  </div>
  <div class="table-wrap">{table_html}</div>
</div>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"港股通掃描及網頁生成完成！共 {len(results)} 隻。")
