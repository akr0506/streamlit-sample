import yfinance as yf
import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime, timedelta

st.title('株価可視化アプリ')

# 銘柄リスト
tickers = {
    'Apple': 'AAPL',
    'Facebook': 'META',
    'Google': 'GOOGL',
    'Microsoft': 'MSFT',
    'Netflix': 'NFLX',
    'Amazon': 'AMZN'
}

# サイドバー
st.sidebar.header('条件設定')

# 銘柄選択
selected_tickers_jp = st.sidebar.multiselect(
    '銘柄を選択してください',
    list(tickers.keys()),
    ['Apple', 'Google']
)
selected_tickers_en = [tickers[ticker] for ticker in selected_tickers_jp]

# 期間選択
end_date = datetime.today()
start_date = st.sidebar.date_input(
    '取得開始日',
    end_date - timedelta(days=365)
)

st.sidebar.write('取得期間:', start_date, '〜', end_date.date())


# 株価取得
@st.cache_data
def get_stock_data(tickers, start, end):
    try:
        # データを取得
        data = yf.download(tickers, start=start, end=end)
        
        # データが空でないかチェック
        if data.empty:
            st.error('データの取得に失敗しました。銘柄または期間を変更してください。')
            return pd.DataFrame()
        
        # 利用可能なカラムを確認
        available_columns = data.columns.get_level_values(0).unique() if isinstance(data.columns, pd.MultiIndex) else data.columns
        
        # 'Adj Close'が利用可能な場合はそれを使用、そうでなければ'Close'を使用
        if 'Adj Close' in available_columns:
            return data['Adj Close']
        elif 'Close' in available_columns:
            st.info('調整後終値が利用できないため、終値を使用します。')
            return data['Close']
        else:
            st.error('株価データが見つかりません。')
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f'データ取得中にエラーが発生しました: {str(e)}')
        return pd.DataFrame()

if selected_tickers_en:
    stock_data = get_stock_data(selected_tickers_en, start_date, end_date)

    if not stock_data.empty:
        st.header('株価 (USD)')
        st.dataframe(stock_data)

        # データフレームをAltairが扱える形式に変換
        data = stock_data.reset_index().melt('Date', var_name='Ticker', value_name='Price')

        # チャート作成
        chart = (
            alt.Chart(data)
            .mark_line(opacity=0.8, clip=True)
            .encode(
                x="Date:T",
                y=alt.Y("Price:Q", stack=None, scale=alt.Scale(domain=[data['Price'].min()*0.95, data['Price'].max()*1.05])),
                color="Ticker:N"
            )
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning('選択された期間のデータがありません。')
else:
    st.info('銘柄を選択してください。')
