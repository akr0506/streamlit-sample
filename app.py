import yfinance as yf
import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime, timedelta

st.title('株価可視化アプリ')

# S&P 500の銘柄リストを取得
@st.cache_data
def get_sp500_tickers():
    try:
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        payload = pd.read_html(url)
        # Wikipediaのテーブルからティッカーシンボルを取得
        tickers = payload[0]['Symbol'].tolist()
        return tickers
    except Exception as e:
        st.error(f"S&P 500の銘柄リストの取得に失敗しました: {e}")
        # フォールバック用の基本的な銘柄リスト
        return ['AAPL', 'META', 'GOOGL', 'MSFT', 'NFLX', 'AMZN']

# サイドバー
st.sidebar.header('条件設定')

# 銘柄選択
all_tickers = get_sp500_tickers()
selected_tickers = st.sidebar.multiselect(
    '銘柄を検索・選択してください',
    all_tickers,
    ['AAPL', 'GOOGL']  # デフォルトで選択されている銘柄
)

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
        
        # Adj Closeを試す
        try:
            if isinstance(tickers, list) and len(tickers) > 1:
                stock_data = data['Adj Close']
            else:
                stock_data = data[['Adj Close']].rename(columns={'Adj Close': tickers[0]})
        except KeyError:
            st.warning(" 'Adj Close' が見つかりませんでした。'Close' を使用します。")
            if isinstance(tickers, list) and len(tickers) > 1:
                stock_data = data['Close']
            else:
                stock_data = data[['Close']].rename(columns={'Close': tickers[0]})

        if stock_data.empty:
            st.error('株価データが見つかりません。')
            return pd.DataFrame()
            
        return stock_data
            
    except Exception as e:
        st.error(f'データ取得中にエラーが発生しました: {str(e)}')
        return pd.DataFrame()

if selected_tickers:
    stock_data = get_stock_data(selected_tickers, start_date, end_date)

    if not stock_data.empty:
        # 単一銘柄の場合、カラム名をティッカーシンボルに設定
        if len(selected_tickers) == 1:
            stock_data.columns = selected_tickers

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
