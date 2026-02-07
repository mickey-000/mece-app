import streamlit as st
import google.generativeai as genai
import json
import time

# --- 1. Gemini API設定 ---
def init_gemini():
    # Secretsチェック
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("エラー: Secretsに GEMINI_API_KEY が設定されていません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # モデル接続テスト（自動選択）
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        target = next((m for m in priority if m in models), models[0] if models else None)
        
        if not target: raise Exception("有効なモデルが見つかりません")
        return genai.GenerativeModel(target), target
    except Exception as e:
        st.error(f"接続エラー: {e}")
        st.stop()

model, model_name_used = init_gemini()

# --- 2. 問題生成関数 (営業実戦仕様) ---
def generate_quiz(category_type):
    if category_type == "MECE":
        theme = "営業現場での顧客課題の構造化"
        inst = "若手営業（1-3年目）が顧客ニーズを整理するシーン。3択。"
    else:
        theme = "営業のための数値予測（フェルミ推定）"
        inst = "市場規模や予算規模を論理的に推計する営業シーン。3択。"

    # プロンプト（営業・コンサル融合視点）
    prompt = f"""
    あなたは営業とコンサルの経験を持つマネージャーです。
    「{theme}」について、入社1〜3年目の営業職向けの問題を1問作成してください。
    
    【条件】
    1. 現場で起こりうる具体的な営業シーン（ヒアリング、提案、分析など）設定。
    2. {inst}
    3. 以下のJSON形式(日本語)のみを出力すること。

    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "cor": "正解の選択肢",
        "exp": "マネージャーからの実戦的アドバイス"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {
            "title": "通信エラー", "q": "再読み込みしてください", 
            "opts": ["再試行"], "cor": "再試行", "exp": "エラー"
        }

# --- 3. メイン画面設定 ---
st.set_page_config(page_title="営業思考力道場", page_icon="💼", layout="centered")

if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'q_index' not in st.session_state: st.session_state.q_index = 0
if 'answered' not in st.session_state: st.session_state.answered = False

if not st.session_state.game_active:
    st.title("💼 営業×コンサル思考道場")
    st.caption("〜若手営業（1-3年目）向け 実戦トレーニング〜")
    
    st.info("""
    **【特訓内容】**
    顧客の課題を整理し、数字で語れる「ソリューション営業」を目指します。
    - **前半3問 (MECE)**：顧客情報の整理・構造化
    - **後半2問 (フェルミ)**：市場規模・ポテンシャルの試算
    ※制限時間はありません。
    """)
    
    if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
        st.session_state.score = 0
        st.session_state
