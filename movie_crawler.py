import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# --- 爬蟲設定 ---
BASE_URL = "https://ssr1.scrape.center/page/"
TOTAL_PAGES = 10

# --- 爬蟲核心函式 ---
def fetch_movie_data(progress_bar, status_text):
    """
    爬取 10 頁電影資料，並即時更新 Streamlit 進度條
    """
    all_movies = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for page in range(1, TOTAL_PAGES + 1):
        url = f"{BASE_URL}{page}"
        
        # 更新狀態文字
        status_text.text(f"正在爬取第 {page}/{TOTAL_PAGES} 頁資料...")
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all('div', class_='el-card')
                
                for item in items:
                    # 1. 名稱
                    name_tag = item.find('h2')
                    name = name_tag.text.strip() if name_tag else "N/A"
                    
                    # 2. 圖片
                    img_tag = item.find('img', class_='cover')
                    image_url = img_tag['src'] if img_tag else "https://via.placeholder.com/150"
                    
                    # 3. 評分
                    score_tag = item.find('p', class_='score')
                    score = float(score_tag.text.strip()) if score_tag and score_tag.text.strip() else 0.0
                    
                    # 4. 類型
                    categories = []
                    cat_div = item.find('div', class_='categories')
                    if cat_div:
                        buttons = cat_div.find_all('button')
                        for btn in buttons:
                            categories.append(btn.text.strip())
                    type_str = ", ".join(categories) if categories else "無分類"
                    
                    all_movies.append({
                        "電影名稱": name,
                        "圖片連結": image_url,
                        "評分": score,
                        "類型": type_str
                    })
            else:
                st.error(f"第 {page} 頁請求失敗: {response.status_code}")
                
        except Exception as e:
            st.error(f"第 {page} 頁發生錯誤: {e}")
        
        # 更新進度條 (0.0 ~ 1.0)
        progress_bar.progress(page / TOTAL_PAGES)
        
        # 禮貌性延遲
        time.sleep(random.uniform(0.5, 1.0))
    
    return pd.DataFrame(all_movies)

# ==========================================
# Streamlit 介面設計
# ==========================================
st.set_page_config(page_title="電影爬蟲看板", page_icon="🎬", layout="wide")

st.title("🎬 即時電影資訊爬蟲 (SSR1)")
st.markdown("""
點擊下方的 **「🚀 開始爬取最新資料」** 按鈕，程式將即時訪問目標網站的 10 個頁面，
抓取電影名稱、封面、評分與類型，並整理成美觀的列表。
""")

# --- 側邊欄控制區 ---
with st.sidebar:
    st.header("控制面板")
    start_btn = st.button("🚀 開始爬取最新資料", type="primary")
    st.info("目標：https://ssr1.scrape.center/")
    st.info(f"總頁數：{TOTAL_PAGES} 頁")

# --- 主邏輯區 ---
if start_btn:
    # 初始化進度條元件
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with st.spinner("爬蟲啟動中，請稍候..."):
        # 執行爬蟲
        df = fetch_movie_data(progress_bar, status_text)
        
    status_text.success("✅ 爬取完成！")
    st.session_state['movie_data'] = df  # 將資料存入 session，避免重整後消失

# --- 資料顯示區 ---
if 'movie_data' in st.session_state and not st.session_state['movie_data'].empty:
    df = st.session_state['movie_data']
    
    # 1. 顯示統計數據
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("電影總數", f"{len(df)} 部")
    col2.metric("平均評分", f"{df['評分'].mean():.1f} 分")
    col3.download_button(
        label="📥 下載 CSV 檔案",
        data=df.to_csv(index=False, encoding='utf-8-sig'),
        file_name="movie.csv",
        mime="text/csv"
    )
    
    st.divider()
    st.subheader("📽️ 電影列表展示")

    # 2. 卡片式顯示 (每行顯示 2 部電影)
    # 這裡使用 iterrows 來遍歷資料
    for index, row in df.iterrows():
        # 每兩部電影使用一個 container 區塊，增加間距感
        if index % 2 == 0:
            cols = st.columns([1, 1], gap="large")
        
        # 決定現在要放在左欄還是右欄
        current_col = cols[index % 2]
        
        with current_col:
            # 建立一個內部框架 (Container) 讓外觀像卡片
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                
                with c1:
                    st.image(row['圖片連結'], use_container_width=True)
                
                with c2:
                    st.subheader(row['電影名稱'])
                    
                    # 根據分數顯示不同顏色的標籤
                    score = row['評分']
                    if score >= 9.0:
                        st.markdown(f"⭐ **評分**: :green[{score}]")
                    elif score >= 7.0:
                        st.markdown(f"⭐ **評分**: :orange[{score}]")
                    else:
                        st.markdown(f"⭐ **評分**: :red[{score}]")
                        
                    st.markdown(f"🏷️ **類型**: {row['類型']}")

    # 3. 原始資料表格 (放在最下面折疊起來)
    with st.expander("查看原始資料表格"):
        st.dataframe(df, use_container_width=True)

else:
    # 預設畫面
    st.info("👈 請點擊左側的按鈕開始爬取資料")