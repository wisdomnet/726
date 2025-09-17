import re
import os
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.font_manager as fm

# --- 1. 設定 ---

# ++ 請確認字型檔案名稱與路徑正確 ++
FONT_FILENAME = "NotoSansTC-Regular.ttf"

# 檔案路徑 (每個檔案代表一個要分析的版面)
FILE_PATHS = ['gossiping.txt', 'hatepolitics.txt']

# 擴增後的情感詞典
POSITIVE_WORDS = {
    '支持', '贊成', '同意', '肯定', '成功', '勝利', '加油', '感謝', '做得好', '讚', '挺', '看好', '穩定', '進步',
    '猛', '強', '神', '佩服', '佛心', '優質', '有料', '合理', '中肯', '專業', 'respect', '推', '屌', '帥',
    '沒毛病', '先知', '正確', '大推', '認同'
}
NEGATIVE_WORDS = {
    '反對', '無能', '失敗', '可悲', '垃圾', '白癡', '智障', '噁心', '賣台', '黑箱', '無恥', '輸不起',
    '鬧劇', '追殺', '鬥爭', '浪費', '災難', '崩潰', '滾', '下台', '爛', '廢物', '幹',
    '笑死', '可憐', '噁', '媽的', '腦殘', '白痴', '低能', '可笑', '唬爛', '造謠', '虛偽', '雙標',
    '笑話', '廢到笑', '狗屁', ' bullshit', '丟臉', '難看', '無言', '弱智', '笑死人', '塔綠班', '綠共',
    '巨嬰', '媽寶', '無腦', '側翼', '好了啦', '下去', '可憐哪', '崩潰了'
}

# --- 2. 資料處理函式 ---

def parse_ptt_posts_from_file(file_path):
    """從單一 PTT 檔案中，提取每篇文章的日期和內容"""
    posts = []
    date_pattern = re.compile(r'時間\s+([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+2025)')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        posts_content = content.split('======================================================================')
        for post_text in posts_content:
            post_text = post_text.strip()
            if not post_text: continue
            date_match = date_pattern.search(post_text)
            if date_match:
                date_str = date_match.group(1)
                try:
                    post_date = pd.to_datetime(date_str, format='%a %b %d %H:%M:%S %Y').date()
                    posts.append({'date': post_date, 'text': post_text})
                except ValueError: continue
    except FileNotFoundError: print(f"錯誤：找不到檔案 {file_path}。")
    except Exception as e: print(f"處理檔案 {file_path} 時發生錯誤: {e}")
    return posts

def calculate_sentiment_score(text):
    """計算單一文本的情感分數"""
    pos_count = sum(1 for word in POSITIVE_WORDS if word in text)
    neg_count = sum(1 for word in NEGATIVE_WORDS if word in text)
    total_mentions = pos_count + neg_count
    if total_mentions == 0: return 0.0
    return (pos_count - neg_count) / total_mentions

# --- 3. 主程式執行流程 ---

def main():
    if not os.path.exists(FONT_FILENAME):
        print(f"錯誤：找不到字型檔案 '{FONT_FILENAME}'。請確認字型檔與腳本在同一個資料夾。")
        return
    my_font = fm.FontProperties(fname=FONT_FILENAME)

    print("--- PTT 版面情感趨勢分析 (含總體) ---")

    # 步驟 1: 依版面載入、解析並計算情感分數
    print("\n[步驟 1/3] 正在分析各版面的文章情感傾向...")
    daily_sentiments = defaultdict(lambda: defaultdict(list))
    all_dates = set()
    for path in FILE_PATHS:
        board_name = os.path.splitext(os.path.basename(path))[0]
        print(f"  > 正在處理版面: {board_name}")
        posts = parse_ptt_posts_from_file(path)
        if not posts:
            print(f"    - 在 {path} 中未找到任何文章，已跳過。")
            continue
        print(f"    - 載入 {len(posts)} 篇文章。")
        for post in posts:
            post_date = post['date']
            sentiment_score = calculate_sentiment_score(post['text'])
            daily_sentiments[post_date][board_name].append(sentiment_score)
            all_dates.add(post_date)
    print("  > 所有版面分析完成。")

    # 步驟 2: 匯總每日平均情感分數 (含合併數據)
    print("\n[步驟 2/3] 正在匯總每日平均情感分數...")
    results = []
    if not daily_sentiments:
        print("沒有找到任何文章，無法進行分析。")
        return

    start_date, end_date = min(all_dates), max(all_dates)
    date_range = pd.date_range(start=start_date, end=end_date)
    board_names = [os.path.splitext(os.path.basename(p))[0] for p in FILE_PATHS]

    for date in date_range:
        date_obj = date.date()
        row = {'Date': date_obj}
        all_daily_scores = [] # 用於計算當日合併分數

        # 計算各獨立版面的平均分數
        for board in board_names:
            scores = daily_sentiments[date_obj][board]
            if scores:
                row[board] = sum(scores) / len(scores)
                all_daily_scores.extend(scores) # 將分數加入合併列表
            else:
                row[board] = None

        # 計算當日合併後的總平均分數
        if all_daily_scores:
            row['combined'] = sum(all_daily_scores) / len(all_daily_scores)
        else:
            row['combined'] = None

        results.append(row)

    df = pd.DataFrame(results).set_index('Date')

    # 調整欄位順序，讓 'combined' 在最後，方便圖例觀看
    if 'combined' in df.columns:
        cols = [col for col in df if col != 'combined'] + ['combined']
        df = df[cols]

    df.fillna(method='ffill', inplace=True) # 向前填充空值，使圖表連續
    df.index = pd.to_datetime(df.index)

    print("  > 匯總完成。")

    # 步驟 3: 顯示結果、儲存檔案並繪圖
    print("\n--- 每日平均情感分數結果 (繪圖數據) ---")

    output_filename = 'sentiment_analysis_with_combined_results.csv'
    df.to_csv(output_filename, encoding='utf-8-sig')
    print(f"\n分析結果已儲存至 {output_filename}")

    print("\n以下為繪製「PTT 版面情感趨勢圖」所使用的數據：")
    print(df.round(3).to_string())
    print("-" * 50)

    print("\n正在繪製情感趨勢圖...")

    plt.rcParams['axes.unicode_minus'] = False
    fig, ax = plt.subplots(figsize=(14, 8))

    # --- *** 修改處 START *** ---
    # 建立一個圖例標籤的對照字典
    label_map = {
        'gossiping': '八卦版',
        'hatepolitics': '政黑版',
        'combined': '合併'
    }
    # --- *** 修改處 END *** ---

    # 遍歷所有欄位 (包含各版面與 combined) 並繪圖
    for column_name in df.columns:
        # --- *** 修改處 START *** ---
        # 使用 get 方法從字典中獲取中文標籤，如果找不到，則使用原始欄位名
        display_label = label_map.get(column_name, column_name)
        ax.plot(df.index, df[column_name], marker='o', linestyle='-', label=display_label)
        # --- *** 修改處 END *** ---

    # 計算 7/19 到 8/2 期間的 'combined' 平均情感分數
    try:
        avg_start_date = '2025-07-19'
        avg_end_date = '2025-08-02'

        # 篩選出指定日期範圍內的數據
        avg_period_df = df.loc[avg_start_date:avg_end_date]

        # 計算 'combined' 欄位的平均值
        if not avg_period_df.empty and 'combined' in avg_period_df.columns:
            average_sentiment = avg_period_df['combined'].mean()

            # 繪製水平平均線
            ax.axhline(y=average_sentiment, color='red', linestyle='--',
                       label=f'7/19-8/2 總體平均 ({average_sentiment:.2f})')
            print(f"\n已計算 7/19 至 8/2 的總體平均情感分數為: {average_sentiment:.3f}")
        else:
            print("\n警告：在指定的 7/19-8/2 範圍內找不到 'combined' 數據，無法繪製平均線。")

    except Exception as e:
        print(f"\n計算或繪製平均線時發生錯誤: {e}")

    ax.set_title('PTT 版面情感趨勢圖 (含總體)', fontproperties=my_font, fontsize=18, pad=20)
    ax.set_xlabel('日期', fontproperties=my_font, fontsize=14)
    ax.set_ylabel('平均情感分數', fontproperties=my_font, fontsize=14)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.legend(prop=my_font, fontsize=12)

    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(my_font)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()