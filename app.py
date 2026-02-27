import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 網頁標題設定
st.set_page_config(page_title="全球半導體監控儀表板", layout="wide")
st.title("🌐 全球半導體板塊即時監控")
st.write("目前追蹤對象：記憶體、晶圓代工、設備商與設計廠")

# 2. 定義快取函式 (設定 ttl 為 600 秒，代表 10 分鐘內不會重複抓取)
@st.cache_data(ttl=600)
def get_stock_data(ticker_list):
    data_list = []
    for t in ticker_list:
        try:
            stock = yf.Ticker(t)
            # 抓取最新的 1 天資料
            hist = stock.history(period="1d")
            if not hist.empty:
                info = stock.info
                current_price = hist['Close'].iloc[-1]
                prev_close = info.get('previousClose', current_price)
                change = ((current_price - prev_close) / prev_close) * 100
                data_list.append({
                    "標的": t,
                    "名稱": info.get('shortName', 'N/A'),
                    "現價": round(current_price, 2),
                    "漲跌幅 (%)": round(change, 2),
                    "幣別": info.get('currency', 'USD')
                })
        except Exception as e:
            st.error(f"抓取 {t} 時發生錯誤: {e}")
            continue
    return pd.DataFrame(data_list)

# 3. 定義預設監控清單
default_tickers = ["2344.TW", "MU", "2330.TW", "TSM", "NVDA", "ASML", "WDC"]
tickers = st.sidebar.multiselect("增加或移除追蹤標的：", 
                                 ["2344.TW", "MU", "2330.TW", "TSM", "NVDA", "ASML", "WDC", "AMD", "INTC"], 
                                 default=default_tickers)

# 4. 顯示儀表板數據
if tickers:
    df = get_stock_data(tickers)
    
    if not df.empty:
        # 顯示數據卡片
        cols = st.columns(len(df))
        for i, row in df.iterrows():
            # 根據漲跌顯示顏色，台股漲是紅，美股漲是綠
            delta_color = "normal" if row['漲跌幅 (%)'] >= 0 else "inverse"
            cols[i].metric(label=row['標的'], value=row['現價'], delta=f"{row['漲跌幅 (%)']}%", delta_color=delta_color)

        # 5. 繪製歷史走勢圖
        st.subheader(f"📈 {tickers[0]} 歷史走勢 (近三個月)")
        hist_data = yf.download(tickers[0], period="3mo")
        fig = go.Figure(data=[go.Candlestick(x=hist_data.index,
                        open=hist_data['Open'], high=hist_data['High'],
                        low=hist_data['Low'], close=hist_data['Close'])])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("暫時無法取得數據，可能是 Yahoo Finance 存取受限，請稍後再重整頁面。")
else:
    st.warning("請在左側選單選擇至少一個標的。")

st.markdown("---")
st.caption("資料來源：Yahoo Finance API | 快取時間：10 分鐘")
