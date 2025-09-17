import re
from collections import Counter

# --- 1. 設定 ---

# 檔案路徑
FILE_PATHS = ['gossiping.txt', 'hatepolitics.txt']

# 定義關鍵詞 (用來篩選出相關文章)
RECALL_KEYWORDS = ['罷免', '罷團', '青鳥', '關稅', '淹水', '賴清德', '民進黨', '國民黨', '川普', '颱風', '丹娜絲']
    
# 定義立場關鍵詞
# 支持罷免案 (希望罷免成功)
SUPPORT_KEYWORDS = [
    '支持罷免', '同意罷免', '讚成罷免', '罷免到底', '必須罷免', '罷下去', '讓他滾', '下架'
]

# 反對罷免案 (希望罷免失敗，或批評罷免動機)
OPPOSE_KEYWORDS = [
    '反對罷免', '不同意罷免', '反惡罷', '浪費資源', '政治追殺', '政治鬥爭', '勞民傷財',
    '輸不起', '鬧劇', '可悲', '吃相難看'
]

# --- 2. 資料處理與分析函式 ---

def parse_docs_from_file(file_path):
    """從單一檔案路徑載入並解析 PTT 文章"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 使用分隔線切分文章
        posts = content.split('======================================================================')
        # 回傳非空的文章列表
        return [post.strip() for post in posts if post.strip()]
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {file_path}，將跳過此檔案。")
        return []
    except Exception as e:
        print(f"讀取檔案 {file_path} 時發生錯誤: {e}")
        return []

def analyze_sentiment(documents, analysis_title):
    """
    對給定的文章列表進行立場分析並顯示結果。
    
    Args:
        documents (list): 要分析的文章字串列表。
        analysis_title (str): 這次分析的標題 (例如, 'gossiping.txt 看板分析').
    """
    print(f"\n{'='*20}")
    print(f" {analysis_title} ")
    print(f"{'='*20}")
    
    if not documents:
        print("沒有載入任何資料，無法進行分析。")
        return

    # 步驟 1: 篩選相關文章
    #recall_docs = [doc for doc in documents if any(key in doc for key in RECALL_KEYWORDS)]
    recall_docs = documents
    print(f"  > 總文章數: {len(documents)}")
    print(f"  > 篩選出相關討論數: {len(recall_docs)}")

    if not recall_docs:
        print("  > 未篩選出相關討論，無法進行立場分析。")
        return

    # 步驟 2: 計算各立場關鍵詞出現次數
    support_counts = Counter()
    oppose_counts = Counter()

    for doc in recall_docs:
        # 為了避免在同一篇文章中重複計算同一個關鍵詞，我們可以使用集合
        found_support = set()
        found_oppose = set()
        
        for keyword in SUPPORT_KEYWORDS:
            if keyword in doc:
                found_support.add(keyword)
        
        for keyword in OPPOSE_KEYWORDS:
            if keyword in doc:
                found_oppose.add(keyword)
        
        support_counts.update(found_support)
        oppose_counts.update(found_oppose)
    
    total_support_mentions = sum(support_counts.values())
    total_oppose_mentions = sum(oppose_counts.values())
    
    # 步驟 3: 顯示分析結果
    print("\n--- 分析結果 ---")
    print(f"總體立場傾向：")
    print(f"  - 提及「支持罷免案」相關詞彙的文章總數: {total_support_mentions}")
    print(f"  - 提及「反對罷免案」或「批評罷免動機」相關詞彙的文章總數: {total_oppose_mentions}")
    
    if total_support_mentions == 0 and total_oppose_mentions == 0:
        print("\n結論：在相關討論中，未偵測到明確的支持或反對立場關鍵詞。")
    elif total_oppose_mentions > total_support_mentions:
        ratio = total_oppose_mentions / total_support_mentions if total_support_mentions > 0 else float('inf')
        conclusion = "反對或批評的聲量大於支持"
        if ratio != float('inf'):
            print(f"\n結論：數據顯示，{conclusion}，約為支持聲量的 {ratio:.2f} 倍。")
        else:
            print(f"\n結論：數據顯示，{conclusion}，而支持聲量為 0。")

    else:
        ratio = total_support_mentions / total_oppose_mentions if total_oppose_mentions > 0 else float('inf')
        conclusion = "支持罷免的聲量大於或等於反對"
        if ratio != float('inf'):
            print(f"\n結論：數據顯示，{conclusion}，約為反對聲量的 {ratio:.2f} 倍。")
        else:
            print(f"\n結論：數據顯示，{conclusion}，而反對聲量為 0。")


    print("\n--- 「支持罷免案」詞彙 Top 5 ---")
    if not support_counts:
        print("  - (無)")
    else:
        for word, count in support_counts.most_common(5):
            print(f"  - {word}: {count} 次")
        
    print("\n--- 「反對/批評罷免案」詞彙 Top 5 ---")
    if not oppose_counts:
        print("  - (無)")
    else:
        for word, count in oppose_counts.most_common(5):
            print(f"  - {word}: {count} 次")

# --- 3. 主程式執行流程 ---

def main():
    print("--- PTT 罷免立場傾向分析 ---")
    
    all_documents_combined = []

    # --- 階段一: 對每個看板進行獨立分析 ---
    print("\n\n*** 階段一: 各看板獨立分析 ***")
    for path in FILE_PATHS:
        # 載入單一檔案的資料
        documents = parse_docs_from_file(path)
        # 進行分析
        analyze_sentiment(documents, f"看板 '{path}' 分析")
        # 將資料加入到總列表中，以供後續合併分析
        all_documents_combined.extend(documents)
    
    # --- 階段二: 對所有看板進行合併分析 ---
    print("\n\n*** 階段二: 所有看板合併分析 ***")
    if not all_documents_combined:
        print("未能從任何檔案載入資料，無法進行合併分析。")
        return
        
    analyze_sentiment(all_documents_combined, "所有看板合併分析")

if __name__ == '__main__':
    main()