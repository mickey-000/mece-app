import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 接続設定 (APIキー & モデル検索)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("エラー: Secretsに GEMINI_API_KEY がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # 利用可能なモデルを検索
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順位: Flash -> Pro
        target = None
        for keyword in ["flash", "1.5-pro", "gemini-pro"]:
            for m in all_models:
                if keyword in m:
                    target = m
                    break
            if target: break
        
        if not target and all_models: target = all_models[0]
        if not target:
            st.error("利用可能なモデルが見つかりませんでした。")
            st.stop()
            
        return genai.GenerativeModel(target)

    except Exception as e:
        st.error(f"接続エラー: {e}")
        st.stop()

model = init_gemini()

# ==========================================
# 2. 問題生成ロジック (フェルミ＝思考プロセス)
# ==========================================
def generate_quiz(idx):
    scenes = [
        ("MECE", "初級(日常)", "旅行の準備、冷蔵庫の整理"),
        ("MECE", "中級(業務)", "会議アジェンダ、タスク整理"),
        ("MECE", "上級(営業)", "顧客ヒアリング整理、提案構成"),
        ("フェルミ推定", "初級", "コンビニの売上、電柱の数"),
        ("フェルミ推定", "上級", "市場規模算出、顧客予算")
    ]
    cat, level, scene = scenes[idx]

    # フェルミ推定の場合は「式」を答えさせる
    if "フェルミ" in cat:
        instruction = "選択肢は数値ではなく『計算式（分解の軸）』にすること。（例: 客単価×客数）"
    else:
        instruction = "選択肢は具体的な行動や分類項目にすること。"

    prompt = f"""
    あなたは営業マネージャーです。以下の条件でクイズを作成してください。
    テーマ:{cat} レベル:{level} シーン:{scene}
    指示:{instruction}
    
    出力は以下のJSON形式(日本語)のみ:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["A", "B", "C"],
        "ans_idx": 0,
        "exp": "解説"
    }}
    ※ ans_idxは正解の番号(0,1,2)
    """
    
    try:
        res = model.generate_content(prompt)
        text = res.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        # 念のためインデックスを整数化
        data['ans_idx'] = int(data['ans_idx'])
        return data
    except:
        return {
            "title": "通信エラー", "q": "再読み込みしてください", 
            "opts": ["再試行"], "ans_idx": 0, "exp": "エラー"
        }

# ==========================================
# 3. アプリ画面 (表示バグ修正版)
# ==========================================
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

# セッション初期化
if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

# --- スタート画面 ---
if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.info("答えの「数字」ではなく、導き出す「ロジック」を鍛える特訓。")
    if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("課題を作成中..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

# --- クイズ画面 ---
else:
    # 終了判定
    if st.session_state.idx >= 5:
        st.balloons()
        st.title("🏁 免許皆伝")
        st.header(f"戦績: {st.session_state.score} / 5")
        if st.button("道場の入り口に戻る", use_container_width=True):
            st.session_state.game = False
            st.rerun()
            
    # 問題表示
    else:
        q = st.session_state.q
        labels = ["🟢 MECE(日常)", "🟡 MECE(業務)", "🔴 MECE(営業)", "🟡 フェルミ(日常)", "🔴 フェルミ(営業)"]
        
        st.subheader(f"第{st.session_state.idx + 1}問：{labels[st.session_state.idx]}")
        st.info(f"**{q['title']}**\n\n{q['q']}")
        
        # A. 未回答の場合：ボタンを表示
        if st.session_state.ans == False:
            for i, opt in enumerate(q['opts']):
                if st.button(opt, key=f"btn_{st.session_state.idx}_{i}", use_container_width=True):
                    st.session_state.ans = True
                    # 正誤判定
                    if i == q['ans_idx']:
                        st.session_state.last_res = True
                        st.session_state.score += 1
                    else:
                        st.session_state.last_res = False
                    st.rerun()
        
        # B. 回答済みの場合：結果と解説を表示
        else:
            # 正解の選択肢を取得
            correct_opt = q['opts'][q['ans_idx']]
            
            if st.session_state.last_res:
                st.success("⭕ 正解！その通り！")
            else:
                st.error(f"❌ 不正解... 正しいアプローチは「{correct_opt}」")
            
            st.markdown(f"**【解説】**\n{q['exp']}")
            
            if st.button("次の立ち合いへ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner("次の課題を準備中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()

# === END ===
