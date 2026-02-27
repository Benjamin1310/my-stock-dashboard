import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. 網頁基本設定
st.set_page_config(page_title="半導體監控與損益計算器", layout="wide")

# --- 側邊欄：設定區 ---
st.sidebar.header("📊 設定與資產配置")

# 預設追蹤清單
default_list = ["2344.TW", "MU", "2330.TW", "NVDA", "TSM", "ASML"]
selected_tickers = st.sidebar.multiselect("追蹤標的：", 
                                          ["2344.TW", "MU", "2330.TW", "NVDA", "TSM", "ASML", "AMD", "INTC", "WDC"], 
                                          default=default_list)

st.sidebar.markdown("---")
st.sidebar.subheader("💰 我的持倉試算 (以華邦電為例)")
buy_price = st.sidebar.number_input("平均買入成本 (元):", value=130.0)
shares = st.sidebar.number_input("持有張數 (1張=1000股):", value=1.0)

# --- 資料處理區 (加上快取避免被鎖 IP) ---
@st.cache_data(ttl=600)
def fetch_data(ticker_list):
    results = []
    for t in ticker_list:
        try:
            s = yf.Ticker(t)
            df = s.history(period="1d")
            if not df.empty:
                current = df['Close'].iloc[-1]
                prev = s.info.get('previousClose', current)
                change = ((current - prev) / prev) * 100
                results.append({"ticker": t, "name": s.info.get('shortName', t), "price": current, "change": change})
        except:
            continue
    return results

# --- 主畫面佈局 ---
st.title("🌐 全球半導體板塊監控")

data = fetch_data(selected_tickers)

if data:
    # 顯示數據卡片
    cols = st.columns(len(data))
    for i, item in enumerate(data):
        color = "normal" if item['change'] >= 0 else "inverse"
        cols[i].metric(label=item['ticker'], 
                       value=f"{item['price']:.2f}", 
                       delta=f"{item['change']:.2f}%", 
                       delta_color=color)

    st.markdown("---")

    # 損益計算展示 (假設針對 2344.TW)
    wb_data = next((x for x in data if x['ticker'] == "2344.TW"), None)
    if wb_data:
        st.subheader("📝 2344.TW 持倉即時損益")
        current_price = wb_data['price']
        total_cost = buy_price * shares * 1000
        current_value = current_price * shares * 1000
        profit = current_value - total_cost
        roi = (profit / total_cost) * 100 if total_cost > 0 else 0

        p_cols = st.columns(3)
        p_cols[0].write(f"**總投入成本:** ${total_cost:,.0f}")
        p_cols[1].write(f"**目前總價值:** ${current_value:,.0f}")
        
        # 根據損益顯示顏色
        profit_color = "red" if profit >= 0 else "green" # 台股邏輯：漲紅跌綠
        st.markdown(f"### 目前損益： <span style='color:{profit_color}'>{profit:,.0f} ({roi:.2f}%)</span>", unsafe_allow_index=True)

    st.markdown("---")

    # K線圖 (修復多重索引問題)
    main_t = selected_tickers[0]
    st.subheader(f"📈 {main_t} 歷史走勢 (近三個月)")
    hist = yf.download(main_t, period="3mo", auto_adjust=True)
    
    if not hist.empty:
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist['Open'], high=hist['High'],
            low=hist['Low'], close=hist['Close']
        )])
        fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.error("暫時抓不到數據，請等 10 分鐘後重整頁面（Yahoo API 頻率限制）。")

st.caption("資料來源：Yahoo Finance | 本網站僅供參考，投資有風險。")
