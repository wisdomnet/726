import re
from datetime import datetime
from collections import Counter

# --- 1. 設定 ---

# 要分析的檔案路徑列表
FILE_PATHS = ['gossiping.txt', 'hatepolitics.txt']

# 定義時間切點 (年, 月, 日, 時, 分)
# 假設年份為 2025 年，您可以根據資料的實際年份修改
CUTOFF_TIME = datetime(2025, 7, 26, 16, 30)


# --- 2. 角色與函式定義 ---

def get_entity_map():
    """返回詳盡的實體及其別名對照表"""
    return {
        # --- 7/26 被罷免對象 (24+1) ---
        "王鴻薇": ["王鴻薇", "鴻薇", "落跑議員"], "李彥秀": ["李彥秀", "彥秀"],
        "羅智強": ["羅智強", "智強", "強哥", "小強"],
        "徐巧芯": ["徐巧芯", "巧芯", "松信蜜獾", "早餐芯", "蜜獾", "美鳳", "100萬", "芯朋友"],
        "賴士葆": ["賴士葆", "士葆"], "洪孟楷": ["洪孟楷", "孟楷"], "葉元之": ["葉元之", "元之", "元之助"],
        "張智倫": ["張智倫", "智倫"], "林德福": ["林德福", "德福"], "廖先翔": ["廖先翔", "先翔"],
        "牛煦庭": ["牛煦庭", "煦庭"], "涂權吉": ["涂權吉", "權吉"], "魯明哲": ["魯明哲", "明哲"],
        "萬美玲": ["萬美玲", "美玲"], "呂玉玲": ["呂玉玲", "玉玲"], "邱若華": ["邱若華", "若華"],
        "林沛祥": ["林沛祥", "沛祥"], "鄭正鈐": ["鄭正鈐", "正鈐"], "廖偉翔": ["廖偉翔", "偉翔"],
        "黃健豪": ["黃健豪", "健豪"], "羅廷瑋": ["羅廷瑋", "廷瑋"], "丁學忠": ["丁學忠", "學忠"],
        "傅崐萁": ["傅崐萁", "花蓮王", "總召", "傅總召", "崑萁", "昆萁"],
        "黃建賓": ["黃建賓", "建賓"], "高虹安": ["高虹安", "虹安", "安安", "助理費"],
        # --- 8/23 被罷免對象 ---
        "顏寬恒": ["顏寬恒", "寬恒", "冬瓜標"], "楊瓊瓔": ["楊瓊瓔", "瓊瓔"], "江啟臣": ["江啟臣", "啟臣"],
        "馬文君": ["馬文君", "文君", "潛艦"], "游顥": ["游顥"], "羅明才": ["羅明才", "明才"],
        "林思銘": ["林思銘", "思銘"],
        # --- 其他關鍵政治人物 ---
        "韓國瑜": ["韓國瑜", "韓總", "韓導", "禿子", "草包", "發大財"],
        "黃國昌": ["黃國昌", "國昌", "昌神", "戰神", "國蔥", "咆哮", "蔥哥", "老師"],
        "賴清德": ["賴清德", "清德", "賴神", "賴功德", "賴皮", "德德"],
        "柯建銘": ["柯建銘", "老柯"],
        "朱立倫": ["朱立倫", "朱朱倫", "主席", "立倫"],
        "沈伯洋": ["沈伯洋", "Puma", "撲馬", "認知作戰"],
        "曹興誠": ["曹興誠", "曹董", "老曹", "黑熊學院"],
        "盧秀燕": ['盧市長', '媽媽市長',  '台中市長', '燕子',  '盧媽',  '燕子市長'],
        "苗博雅": [ '阿苗', '苗委員', '苗議員', '社民黨主席'],
        "陳其邁": ['陳市長', '高雄市長', '邁邁', '暖男市長', '緊緊緊', '陳副院長'],
        "黃偉哲": ['黃市長', '台南市長', '最強業配王', '黃立委'],
        "趙少康": ["趙少康", "中廣董事長", "政治金童", "戰鬥藍領袖", "少康先生", "趙先生", "老趙"],
        "王義川": ["王義川", "民進黨政策會執行長", "前台中市交通局長", "王局長", "憨川", "國師", "TBC", "不演了新聞台台長", "義川天兵", "三大國師之一"],
        # --- 高度相關網紅與意見領袖 ---
        "陳之漢": ["陳之漢", "館長", "飆捍", "館兒", "阿館", "成吉思汗"],
        "八炯": ["八炯", "溫子渝"], "Cheap": ["Cheap", "歷史哥", "LSE"],
        "波特王": ["波特王", "Potter King", "陳加晉"], "鈞鈞": ["鈞鈞"], "高雄歷史哥": ["高雄歷史哥"],
        "惡骨大": ["惡骨大", "David Wu"], "陳揮文": ["陳揮文"], "黃智賢": ["黃智賢"], "黃暐瀚": ["黃暐瀚"]
    }

def parse_docs_with_dates(file_path):
    """
    從檔案路徑載入文章，並將每篇文章與其發布日期配對。
    只回傳有成功解析出日期的文章。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {file_path}，將跳過此檔案。")
        return []
    except Exception as e:
        print(f"讀取檔案 {file_path} 時發生錯誤: {e}")
        return []

    posts = content.split('======================================================================')
    parsed_data = []
    date_pattern = re.compile(r"時間\s+([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4})")

    for post in posts:
        if not post.strip():
            continue
        
        match = date_pattern.search(post)
        if match:
            date_str = match.group(1)
            try:
                date_obj = datetime.strptime(date_str, '%a %b %d %H:%M:%S %Y')
                # 將文章內容與日期物件配對儲存
                parsed_data.append({'doc': post, 'date': date_obj})
            except ValueError:
                # 忽略無法解析的日期
                pass
    return parsed_data

def report_date_range(dates, analysis_title):
    """報告所提供日期列表的時間範圍。"""
    print(f"\n--- {analysis_title} ---")
    if not dates:
        print("  - 未能找到任何有效的日期資訊。")
        return
    min_date = min(dates)
    max_date = max(dates)
    date_format_str = "%Y-%m-%d %H:%M:%S"
    print(f"  - 總共找到 {len(dates)} 篇包含日期的文章。")
    print(f"  - 最早文章日期: {min_date.strftime(date_format_str)}")
    print(f"  - 最晚文章日期: {max_date.strftime(date_format_str)}")

def analyze_entity_volume(documents, entity_map, analysis_title):
    """分析文章中不同人物的聲量（總提及次數）。"""
    print(f"\n--- {analysis_title} ---")
    if not documents:
        print("  - 此時間區間內沒有文件可供分析。")
        return

    entity_counter = Counter()
    
    for doc in documents:
        for main_entity, aliases in entity_map.items():
            occurrences_in_doc = 0
            for alias in aliases:
                occurrences_in_doc += doc.count(alias)
            
            if occurrences_in_doc > 0:
                entity_counter[main_entity] += occurrences_in_doc

    print(f"  - 在 {len(documents)} 篇文章中進行分析。")
    print(f"  - 以下為聲量最高的前 20 位人物（總提及次數）：")
    if not entity_counter:
        print("    - (未找到任何指定人物的提及)")
        return
    
    for i, (entity, count) in enumerate(entity_counter.most_common(20), 1):
        print(f"    {i}. {entity}: {count} 次")

# --- 3. 主程式執行流程 ---

def main():
    """主程式，執行檔案讀取、日期與人物聲量分析"""
    print("--- PTT 文章資料分析 ---")
    print(f"時間切點設定為: {CUTOFF_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    
    entity_map = get_entity_map()
    all_parsed_data_combined = []

    # --- 階段一: 對每個看板進行獨立分析 ---
    print("\n\n******************************")
    print("*** 階段一: 各看板獨立分析 ***")
    print("******************************")
    for path in FILE_PATHS:
        print(f"\n\n========== 開始分析檔案: {path} ==========")
        
        # 1. 讀取並解析文章與日期
        documents_with_dates = parse_docs_with_dates(path)
        
        # 2. 報告整體日期範圍
        all_dates_in_file = [item['date'] for item in documents_with_dates]
        report_date_range(all_dates_in_file, f"檔案 '{path}' 整體日期範圍")
        
        # 3. 根據時間切點篩選文章
        docs_before = [item['doc'] for item in documents_with_dates if item['date'] <= CUTOFF_TIME]
        docs_after = [item['doc'] for item in documents_with_dates if item['date'] > CUTOFF_TIME]
        
        # 4. 分別進行聲量分析
        analyze_entity_volume(docs_before, entity_map, f"檔案 '{path}' 人物聲量分析 (至 {CUTOFF_TIME.strftime('%Y-%m-%d %H:%M')} 為止)")
        analyze_entity_volume(docs_after, entity_map, f"檔案 '{path}' 人物聲量分析 ({CUTOFF_TIME.strftime('%Y-%m-%d %H:%M')} 以後)")
        
        # 匯集資料以供後續合併分析
        all_parsed_data_combined.extend(documents_with_dates)
    
    # --- 階段二: 對所有看板進行合併分析 ---
    print("\n\n********************************")
    print("*** 階段二: 所有檔案合併分析 ***")
    print("********************************")
    if not all_parsed_data_combined:
        print("未能從任何檔案載入資料，無法進行合併分析。")
        return
    
    # 1. 報告合併後的整體日期範圍
    all_dates_combined = [item['date'] for item in all_parsed_data_combined]
    report_date_range(all_dates_combined, "所有檔案合併後整體日期範圍")

    # 2. 篩選合併後的資料
    combined_docs_before = [item['doc'] for item in all_parsed_data_combined if item['date'] <= CUTOFF_TIME]
    combined_docs_after = [item['doc'] for item in all_parsed_data_combined if item['date'] > CUTOFF_TIME]
    
    # 3. 進行合併後的聲量分析
    analyze_entity_volume(combined_docs_before, entity_map, f"所有檔案合併人物聲量分析 (至 {CUTOFF_TIME.strftime('%Y-%m-%d %H:%M')} 為止)")
    analyze_entity_volume(combined_docs_after, entity_map, f"所有檔案合併人物聲量分析 ({CUTOFF_TIME.strftime('%Y-%m-%d %H:%M')} 以後)")

if __name__ == '__main__':
    main()