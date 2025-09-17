import re
import pandas as pd
import jieba
from gensim import corpora, models
from opencc import OpenCC
from collections import Counter
import numpy as np

# --- 1. 設定與資料載入 ---

# 檔案路徑 (現在會對列表中每個檔案單獨分析，然後再合併分析)
FILE_PATHS = ['gossiping.txt', 'hatepolitics.txt']

# LDA 模型參數
NUM_TOPICS = 5      # 探勘5個主題
PASSES = 15         # 迭代次數
RANDOM_STATE = 42   # 隨機種子

# 建立繁體中文停用詞列表
def get_stopwords():
    # ... (此處省略您提供的完整停用詞列表，直接使用)
    return {
    'Fw', 'Fw:', 'JPTT', 'LIVE', 'Re', 'Re:', 'Sent', 'be', 'bbs', 'cc',
    'chinatimes', 'cna', 'com', 'cts', 'ettoday', 'ftv', 'gif', 'html',
    'http', 'https', 'iPhone', 'imgur', 'jpg', 'jpeg', 'line', 'ltn',
    'msn', 'my', 'nownews', 'newtalk', 'on', 'png', 'ptt', 'setn', 'storm',
    'tvbs', 'udn', 'www', 'yahoo', 'youtu', 'from', '一', '一些', '一個',
    '七', '三', '上', '下', '不', '不只', '不如', '不知', '不僅', '不但',
    '不過', '兩種', '為', '為了', '為什麼', '為何', '為止', '為此', '之',
    '之前', '之後', '之內', '之類', '之間', '九', '也', '了', '二', '五',
    '些', '亦', '人', '人們', '人家', '什麼', '什麼樣', '他', '他們',
    '他人', '其他', '其餘', '其它', '其次', '具体', '内容', '出來', '別',
    '別人', '別的', '前', '前者', '加之', '即', '即使', '又', '及', '及時',
    '受', '另外', '只', '只見', '只好', '只是', '只有', '另', '另方面',
    '另行', '呀', '吧', '嗎', '否則', '吧', '吱', '啊', '呃', '哪', '哪個',
    '哪些', '哪兒', '哪天', '哪年', '哪怕', '哪樣', '哪裡', '哦', '喔',
    '啦', '啥', '喲', '哦', '唉', '嗚', '嗚呼', '呢', '呵', '呵呵', '哥',
    '哦', '哼', '唉', '哎', '哎呀', '哎喲', '四', '因', '因此', '因為',
    '在', '在下', '在於', '地', '多', '多少', '大', '大家', '她', '她們',
    '好', '如', '如何', '如其', '如果', '如此', '如若', '存在', '它',
    '它們', '對', '對於', '對方', '對此', '將', '小', '尚且', '就', '就是',
    '就是說', '儘管', '豈但', '己', '已', '已經', '帶', '常', '常常', '平時',
    '年', '並', '並且', '廣泛', '應', '應該', '從', '從不', '從此', '從而',
    '待', '得', '後', '後者', '從', '然後', '很', '很多', '我', '我們',
    '或', '或是', '或者', '所有', '所以', '把', '按', '接著', '故', '故此',
    '整', '整個', '既', '既是', '既然', '日', '時', '時候', '是', '是的',
    '更', '曾', '曾經', '替', '最', '月', '有', '有些', '有關', '有的',
    '朝', '本', '本地', '本著', '本身', '來', '來自', '來說', '然', '然後',
    '然而', '照', '照著', '猶且', '猶自', '甚麼', '甚而', '甚至', '用',
    '由', '由於', '由是', '的', '的確', '的話', '直到', '眾', '眾人',
    '眾所周知', '知', '知道', '硬是', '社', '神', '祥', '竟', '竟然', '第',
    '等', '等等', '簡直', '經', '經過', '繼而', '缺', '者', '而', '而且',
    '而是', '而外', '而後', '而論', '聯同', '肯', '能否', '能夠', '自',
    '自個兒', '自各兒', '自後', '自家', '自己', '自打', '自身', '至', '至今',
    '至於', '若', '若是', '莫若', '見', '豈', '豈不', '覺得', '視', '話',
    '該', '說', '說來', '誰', '誰人', '誰知', '誰料', '誰讓', '論', '諸位',
    '誰', '跟', '路', '轉', '較', '邊', '過', '還', '還是', '還有', '這',
    '這個', '這麼', '這麼些', '這麼樣', '這麼點兒', '這些', '這兒', '這就是',
    '這樣', '這般', '這裡', '這麽', '還', '還不', '還是', '還有', '進',
    '進而', '進行', '遠', '連', '連同', '連聲', '連著', '邊', '那', '那個',
    '那麼', '那麼些', '那麼樣', '那些', '那兒', '那樣', '那裡', '都',
    '鄙人', '鑒於', '阿', '隨', '隨後', '隨時', '隨著', '零', '順', '順著',
    '首先', '︿', '！', '＃', '＄', '％', '＆', '（', '）', '＊', '＋', '，',
    '－', '．', '／', '：', '；', '＜', '＞', '？', '＠', '［', '］', '＾',
    '＿', '｀', '｛', '｜', '｝', '～', '《', '》', '〈', '〉', '「', '」',
    '『', '』', '【', '】', '〔', '〕', '︵', '︶', '〝', '〞', '一派', '上下',
    '不一定', '不同', '不免', '不再', '不力', '不及', '不只', '不可', '不在',
    '不僅', '不盡', '不惟', '不必', '不怎麼', '想', '惹', '成', '我', '或',
    '所', '所有', '打', '找', '是', '有關', '無', '無寧', '無可', '無論',
    '既', '旦', '是', '顯然', '時候', '是的', '更', '會', '有', '有關',
    '有的', '望', '朝', '本', '本著', '本身', '權', '次', '此', '此中',
    '此後', '此時', '此次', '此間', '毋寧', '每', '每當', '比', '比如',
    '比方', '沒', '沒有', '沿', '沿著', '漫說', '焉', '然則', '然後',
    '然而', '照', '照著', '猶且', '猶自', '特別', '的', '的確', '的話',
    '看', '看來', '看做', '看起來', '矣', '矣乎', '矣哉', '離', '竟', '竟然',
    '第', '等', '等等', '管', '類', '類乎', '經', '經過', '結果', '給',
    '繼之', '繼後', '繼而', '緊接著', '縱', '縱令', '縱使', '縱然', '經',
    '罷了', '老', '者', '而', '而且', '而況', '而外', '而後', '而罷了',
    '而論', '耍', '聞', '聞說', '聯合', '聯總', '聯袂', '臨', '自', '自個兒',
    '自各兒', '自後', '自家', '自己', '自打', '自身', '至', '至今', '至若',
    '至於', '致', '般的', '若', '若夫', '若是', '若非', '莫不然', '莫如',
    '莫若', '雖', '雖則', '雖然', '雖說', '被', '見', '要', '要不', '要不是',
    '要不然', '要么', '要是', '覺得', '親', '親口', '親手', '親眼', '親自',
    '觀', '言', '譬喻', '譬如', '讓', '許多', '論', '論說', '諸', '諸位',
    '諸如', '誰', '誰人', '誰知', '誰料', '誰讓', '豈', '豈不', '豈止', '起',
    '起見', '趁', '趁著', '跟', '蹤', '踞', '較', '較之', '邊', '過', '還',
    '還是', '還有', '這', '這個', '這麼', '這麼些', '這麼樣', '這麼點兒',
    '這些', '這兒', '這就是', '這樣', '這般', '這裡', '這麽', '還', '還不',
    '還是', '還有', '進', '進而', '進行', '遠', '連', '連同', '連聲', '連著',
    '邊', '那', '那個', '那麼', '那麼些', '那麼樣', '那些', '那兒', '那樣',
    '那裡', '都', '鄙人', '鑒於', '阿', '隨', '隨後', '隨時', '隨著', '零',
    '順', '順著', '首先', '...', '---', '==', '[協尋]', '[公告]', '[快新聞]',
    '[問卦]', '[轉錄]', '[討論]', '[新聞]', '[舊聞]', '[爆卦]', '[黑特]', 'Fw: [協尋]',
    'Fw: [公告]', 'Fw: [快新聞]', 'Fw: [問卦]', 'Fw: [轉錄]', 'Fw: [討論]', 'Fw: [新聞]',
    'Fw: [舊聞]', 'Fw: [爆卦]', 'Fw: [黑特]', 'Re: [協尋]', 'Re: [公告]', 'Re: [快新聞]',
    'Re: [問卦]', 'Re: [轉錄]', 'Re: [討論]', 'Re: [新聞]', 'Re: [舊聞]', 'Re: [爆卦]',
    'Re: [黑特]', '一個', '一些', '什麼', '哪個', '之', '與', '及', '而', '且', '但',
    '因為', '所以', '以', '於', '著', '吧', '嗎', '啊', '呢', '喔', '哦',
    '啦', '欸', '嘿', '哼', '嗯', '唉', '※', '◆', '→', '推', '噓',
    '作者', '看板', '標題', '時間', '發信站', '批踢踢實業坊', '文章網址',
    '引述', '媒體來源', '記者署名', '完整新聞標題', '完整新聞內文', '完整新聞連結',
    '備註', '不可用', '轉載媒體', '協尋', '公告', '快新聞', '問卦', '轉錄',
    '討論', '新聞', '舊聞', '爆卦', '黑特','可以',
    '不是','真的','怎麼','現在',
    '不要','不會','這種','可能','有人','一樣','一下','一堆','看到'
    }

# 建立自定義詞典
def setup_jieba():
    # ... (此處省略您提供的完整 jieba 設定，直接使用)
    highly_relevant_synonyms = {
        "王鴻薇": ["鴻薇", "落跑議員"], "李彥秀": ["彥秀"], "羅智強": ["智強", "強哥", "小強"],
        "徐巧芯": ["巧芯", "松信蜜獾", "早餐芯", "蜜獾", "美鳳", "100萬", "芯朋友"], "賴士葆": ["士葆"],
        "洪孟楷": ["孟楷"], "葉元之": ["元之", "元之助"], "張智倫": ["智倫"], "林德福": ["德福"],
        "廖先翔": ["先翔"], "牛煦庭": ["煦庭"], "涂權吉": ["權吉"], "魯明哲": ["明哲"], "萬美玲": ["美玲"],
        "呂玉玲": ["玉玲"], "邱若華": ["若華"], "林沛祥": ["沛祥"], "鄭正鈐": ["正鈐"], "廖偉翔": ["偉翔"],
        "黃健豪": ["健豪"], "羅廷瑋": ["廷瑋"], "丁學忠": ["學忠"],
        "傅崐萁": ["花蓮王", "總召", "傅總召", "崑萁", "昆萁"], "黃建賓": ["建賓"], "高虹安": ["虹安", "安安", "助理費"],
        "顏寬恒": ["寬恒", "冬瓜標"], "楊瓊瓔": ["瓊瓔"], "江啟臣": ["啟臣"], "馬文君": ["文君", "潛艦"],
        "游顥": ["游顥"], "羅明才": ["明才"], 
        "林思銘": ["思銘"],
        "韓國瑜": ["韓總", "韓導", "禿子", "草包", "發大財"], 
        "黃國昌": ["國昌", "昌神", "戰神", "國蔥", "咆哮", "蔥哥", "老師"],
        "賴清德": ["清德", "賴神", "賴功德", "賴皮", "德德"], "柯建銘": ["老柯", "總召"],
        "朱立倫": ["朱朱倫", "主席", "立倫"], 
        "沈伯洋": ["Puma", "撲馬", "認知作戰"],
        "曹興誠": ["曹董", "老曹", "黑熊學院"], "趙少康": ["中廣董事長", "政治金童", "戰鬥藍領袖", "少康先生", "趙先生", "老趙"],
        "王義川": ["民進黨政策會執行長", "前台中市交通局長", "王局長", "憨川", "國師", "TBC", "不演了新聞台台長", "義川天兵", "三大國師之一"],
        "陳之漢": ["館長", "飆捍", "館兒", "阿館", "成吉思汗"], "八炯": ["溫子渝"], "Cheap": ["歷史哥", "LSE"],
        "波特王": ["Potter King", "陳加晉"], "鈞鈞": [], "高雄歷史哥": [], "惡骨大": ["David Wu"],
        "陳揮文": [], "黃智賢": [], "黃暐瀚": []
    }
    recall_keywords_list = [
        ["罷免", "連署", "投票", "門檻", "拆彈", "提議", "中選會"],
        ["國會改革", "擴權", "藐視國會", "反質詢", "聽證權", "黑箱", "程序正義", "花東三法"],
        ["青鳥行動", "藍鳥", "小草", "罷免團體", "公民團體", "綠衛兵"],
        ["蔥師表", "毀憲亂政", "惡罷", "政治鬥爭", "勞民傷財", "撕裂社會", "民主倒退", "我們必將再起"]
    ]
    negotiation_keywords_list = [
        ["關稅", "稅率", "談判", "協商", "經貿", "貿易", "市場", "開放市場", "產業利益", "國家利益", "糧食安全", "國民健康", "貨物稅", "讓利", "犧牲", "互惠", "電價", "核電", "綠電"],
        ["第四輪關稅實體談判", "協商三個月", "拖延戰術", "黑箱", "秘密", "自導自演", "政治操作", "影響力"],
        ["台灣", "美國", "川普", "趙少康", "鄭麗君", "經濟部長", "台積電", "執政黨", "民進黨", "在野黨", "國民黨", "民眾黨", "中國"],
        ["大罷免", "726", "政治人物", "黃國昌", "柯文哲", "盧秀燕", "苗博雅", "羅大佑", "館長", "青鳥", "小草"],
        ["蓋牌", "公布", "新聞製造機", "路透社", "自由時報"],
        ["獨裁", "綠共", "綠衛兵", "文化大革命", "司法", "羈押", "掏空", "雙標", "造謠", "貪污", "撕裂台灣"],
        ["中華台北", "一中憲法", "舔共", "抗中保台", "烏克蘭"]
    ]
    typhoon_keywords_list = [
        ["颱風", "雨", "狂風暴雨", "天氣", "天災", "淹水", "水患"],
        ["災情", "救災", "復原", "修繕", "缺工", "缺料", "價格紊亂", "停班停課"],
        ["政府", "中央", "地方政府", "陳其邁", "黃偉哲", "盧秀燕", "民進黨", "黑熊", "青鳥", "小草", "南部人", "死忠"],
        ["大罷免", "726", "蓋牌", "政治操作", "投票", "募款", "超徵"]
    ]
    all_custom_words = set()
    for name, aliases in highly_relevant_synonyms.items():
        all_custom_words.add(name)
        for alias in aliases:
            all_custom_words.add(alias)
    all_keyword_lists = (
        recall_keywords_list +
        negotiation_keywords_list +
        typhoon_keywords_list
    )
    for category in all_keyword_lists:
        for keyword in category:
            all_custom_words.add(keyword)
    print(f"開始將 {len(all_custom_words)} 個獨特的自定義詞彙加入 Jieba 詞典...")
    for word in sorted(list(all_custom_words)):
        jieba.add_word(word)

# --- 2. 資料前處理 ---

def parse_ptt_file(file_path):
    """解析 PTT 原始 txt 檔案格式"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        posts = content.split('======================================================================')
        all_texts = []
        for post in posts:
            post = post.strip()
            if not post:
                continue
            parts = re.split(r'※ 發信站: 批踢踢實業坊\(ptt\.cc\)', post)
            main_content = parts[0]
            main_content = re.sub(r'^作者.*\n', '', main_content, flags=re.MULTILINE)
            main_content = re.sub(r'^看板.*\n', '', main_content, flags=re.MULTILINE)
            main_content = re.sub(r'^標題.*\n', '', main_content, flags=re.MULTILINE)
            main_content = re.sub(r'^時間.*\n', '', main_content, flags=re.MULTILINE)
            main_content = re.sub(r': ※ 引述.*', '', main_content)
            full_text = main_content.strip()
            if len(parts) > 1:
                comments_text = ' '.join(re.findall(r'[:→推噓]\s.*', parts[1]))
                full_text += " " + comments_text
            all_texts.append(full_text)
        return all_texts
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {file_path}。請確認檔案名稱與路徑是否正確。")
        return []
    except Exception as e:
        print(f"讀取或解析檔案 {file_path} 時發生錯誤: {e}")
        return []

def preprocess_text(text, stopwords, cc):
    """文本清洗、簡轉繁、斷詞、移除停用詞"""
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'[^a-zA-Z\u4e00-\u9fa5]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = cc.convert(text)
    words = jieba.lcut(text)
    words = [word for word in words if word not in stopwords and len(word) > 1]
    return words

# --- 3. 核心分析函式 ---

def run_lda_analysis(documents, source_name, stopwords, cc, num_topics, passes, random_state):
    """
    對給定的文檔列表執行完整的LDA分析並印出結果。
    
    :param documents: (list) 待分析的文本列表。
    :param source_name: (str) 數據來源名稱，用於報告輸出。
    :param stopwords: (set) 停用詞集合。
    :param cc: (OpenCC) OpenCC 實例。
    :param num_topics: (int) 要提取的主題數量。
    :param passes: (int) LDA 訓練的迭代次數。
    :param random_state: (int) 隨機種子。
    """
    print("\n" + "="*80)
    print(f"|| 開始分析來源: {source_name} ||")
    print(f"|| 文章總數: {len(documents)} 篇 ||")
    print("="*80)

    if not documents:
        print("\n錯誤：此來源沒有可供分析的文章，跳過此分析。")
        return

    # 步驟 1: 文本前處理
    print("\n[步驟 1/4] 正在進行文本前處理...")
    processed_docs = [preprocess_text(doc, stopwords, cc) for doc in documents]
    processed_docs = [doc for doc in processed_docs if doc] # 確保沒有空文檔
    if not processed_docs:
        print("\n錯誤：前處理後沒有剩下任何有效詞語，無法進行分析。")
        return
    print("  > 前處理完成。")

    # 步驟 2: 建立詞袋與語料庫
    print("\n[步驟 2/4] 正在建立詞袋與語料庫...")
    dictionary = corpora.Dictionary(processed_docs)
    dictionary.filter_extremes(no_below=10, no_above=0.6) # 過濾極端詞彙
    corpus = [dictionary.doc2bow(doc) for doc in processed_docs]
    
    if not corpus or not any(corpus):
        print("\n錯誤：建立詞袋後，語料庫為空。可能是篩選條件過於嚴格或文本內容過短。")
        return
    print("  > 詞袋與語料庫建立完成。")

    # 步驟 3: 訓練 LDA 模型
    print("\n[步驟 3/4] 正在訓練 LDA 主題模型...")
    lda_model = models.LdaMulticore(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        random_state=random_state,
        chunksize=100,
        passes=passes,
        per_word_topics=True,
        workers=4
    )
    print("  > 模型訓練完成。")

    # 步驟 4: 顯示結果
    print("\n" + "---" * 10 + f" {source_name} 分析結果 " + "---" * 10)
    
    # 顯示主題關鍵詞
    print(f"\n共識別出 {num_topics} 個主題，每個主題的前15個關鍵詞如下：\n")
    topics = lda_model.print_topics(num_words=15)
    for i, topic in enumerate(topics):
        topic_num, words_str = topic
        words = re.findall(r'"(.*?)"', words_str)
        print(f"主題 {i+1}: {'、'.join(words)}")
        
    # 計算並顯示每個主題的佔比
    print("\n--- 主題佔比分析 ---")
    doc_topics = [lda_model.get_document_topics(doc, minimum_probability=0.0) for doc in corpus]
    
    dominant_topics = []
    if doc_topics:
        for doc_topic in doc_topics:
            if doc_topic:
                dominant_topic = sorted(doc_topic, key=lambda x: x[1], reverse=True)[0][0]
                dominant_topics.append(dominant_topic)
    
    if dominant_topics:
        topic_counts = Counter(dominant_topics)
        total_docs_in_model = len(dominant_topics)
        print("此數據顯示各主題作為文章主要議題的百分比。\n")
        for topic_id, count in sorted(topic_counts.items()):
            percentage = (count / total_docs_in_model) * 100
            print(f"主題 {topic_id + 1}: 佔比 {percentage:.2f}% ({count}/{total_docs_in_model} 篇文章)")
    else:
        print("無法計算主題佔比，因為沒有文章能明確對應到任一主題。")
    print("---" * 10 + " 分析結束 " + "---" * 10 + "\n")


# --- 4. 主程式執行流程 ---

def main():
    print("--- PTT 輿論主題模型分析 ---")
    
    # 初始化共享資源
    print("\n[初始化] 正在設定 Jieba 自定義詞典...")
    setup_jieba()
    stopwords = get_stopwords()
    cc = OpenCC('s2twp')

    # --- 針對每個版面獨立進行 LDA 分析 ---
    print("\n[第一階段] 開始對每個版面進行獨立分析...")
    all_docs_for_combined_analysis = []
    for path in FILE_PATHS:
        docs = parse_ptt_file(path)
        if docs:
            run_lda_analysis(docs, f"單獨版面: {path}", stopwords, cc, NUM_TOPICS, PASSES, RANDOM_STATE)
            all_docs_for_combined_analysis.extend(docs)
        else:
            print(f"\n警告：檔案 {path} 為空或讀取失敗，將在合併分析中跳過此檔案。")

    # --- 針對所有版面合併進行 LDA 分析 ---
    if len(FILE_PATHS) > 1 and all_docs_for_combined_analysis:
        print("\n[第二階段] 開始對所有版面進行合併分析...")
        run_lda_analysis(all_docs_for_combined_analysis, "所有版面合併", stopwords, cc, NUM_TOPICS, PASSES, RANDOM_STATE)
    elif len(FILE_PATHS) <= 1:
         print("\n提示：只有一個檔案，無需進行合併分析。")
    else:
        print("\n錯誤：所有檔案均無法讀取，無法進行合併分析。")
        
    print("\n--- 所有分析任務已完成 ---")


if __name__ == '__main__':
    main()