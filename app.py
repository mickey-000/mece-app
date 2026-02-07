import streamlit as st
import google.generativeai as genai
import json
import time

# ==========================================
# 1. Gemini API設定 (最強の接続ロジック)
# ==========================================
def init_gemini():
    # Secretsのチェック
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("【エラー】Secretsに 'GEMINI_API_KEY' が設定されていません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 利用可能なモデルを自動探索
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順位: Flash(高速) -> Pro(高性能) -> 無印
        target = None
        priority_list = [
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-pro", 
            "models/gemini-1.5-flash-001",
            "models/gemini-pro"
        ]
        
        for p in priority_list:
            if p in models:
                target = p
                break
        
        if not target and models:
            target = models[0]
            
        if not target:
            raise Exception("利用可能なモデルが見つかりませんでした。")
            
        return genai.GenerativeModel(target), target
    except Exception as e:
        st.error(f"AIモデルの接続に失敗しました: {e}")
        st.stop()

# アプリ起動時にモデルを初期化
model, model_name_used = init_gemini()

# ==========================================
# 2. 問題生成ロジック
# ==========================================
def generate_quiz(category_type):
    if category_type == "MECE":
        theme = "ビジネス課題におけるMECE（漏れなくダブりなく）の構造化"
        instruction = "3つの選択肢のうち、1つだけが『完全にMECE』な切り口であること。"
    else:
        theme = "フェルミ推定（未知の数値を論理的に導く計算式）"
        instruction = "3つの選択肢のうち、1つだけが『最も筋の良い因数分解（計算式）』であること。"

    # プロンプト内のJSONテンプレート（エラー防止のため分離）
    json_template = """
    {
        "title": "問題のタイトル（短く）",
        "q": "問題文（思考力を問う具体的な状況設定）",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "cor": "正解の選択肢（optsの中身と完全一致させること）",
        "exp": "師範からの解説（なぜその選択肢が最適で、他がダメなのかを鋭く指摘）"
    }
    """

    # AIへの指示文
    prompt = f"""
    あなたは戦略コンサルタントを育成する『道場の師範』です。
    実務3年目レベルの難易度で、以下のテーマの問題を1問作成してください。

    【テーマ】{theme}
    【条件】{instruction}
    
    以下のJSON形式(日本語)のみを出力してください。余計な挨拶は不要です。
    {json_template}
    """
    
    try:
        response = model.generate_content(prompt)
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except Exception as e:
        return {
            "title": "通信の乱れ", 
            "q": f"申し訳ない。通信エラーが発生したようだ。\n詳細: {str(e)}", 
            "opts": ["再読み込み"], 
            "cor": "再読み込み", 
            "exp": "画面をリロードして再度挑戦せよ。"
        }

# ==========================================
# 3. 音声再生
# ==========================================
def play_correct_sound():
    sound_url = "https://raw.githubusercontent.com/t-okada/assets/main/correct.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mpeg"></audio>', height=0)

# ==========================================
# 4. アプリ設定 & セッション管理
# ==========================================
st.set_page_config(
    page_title="コンサル脳を鍛える思考力道場", 
    page_icon="🥋",
    layout="centered"
)

if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'q_index' not in st.session_state: st.session_state.q_index = 0
if 'answered' not in st.session_state: st.session_state.answered = False
if 'current_q' not in st.session_state: st.session_state.current_q = None
if 'last_result' not in st.session_state: st.session_state.last_result = None

# ==========================================
# 5. メイン画面
# ==========================================
if not st.session_state.game_active:
    st.title("🥋 コンサル脳を鍛える思考力道場")
    st.markdown("### 「型」を磨き、論理の精度を高める。")
    st.caption(f"接続中のAI師範: {model_name_used.replace('models/', '')}")
    
    st.info("""
    **【道場の掟】**
    1. **MECE (構造化)** を3問、**フェルミ推定 (因数分解)** を2問行う。
    2. 制限時間はない。納得いくまで思考を巡らせること。
    3. AIがその場で実務レベルの難問を生成する。
    """)
    
    if st.button("▶ 入門する（特訓開始）", type="primary", use_container_width=True):
        st.session_state.score = 0
        st.session_state.q_index = 0
        st.session_state.game_active = True
        st.session_state.answered = False
        with st.spinner("師範が問題を練り上げています..."):
            st.session_state.current_q = generate_quiz("MECE")
        st.rerun()

else:
    if st.session_state.q_index >= 5:
        st.balloons()
        st.title("🏁 免許皆伝（特訓終了）")
        
        score = st.session_state.score
        if score == 5:
            rank = "【師範代レベル】 見事な論理力だ。"
        elif score >= 3:
            rank = "【高弟レベル】 基礎はできている。さらに磨け。"
        else:
            rank = "【門下生レベル】 まだまだ修行が足りぬ。"
            
        st.header(f"正答数: {score} / 5")
        st.subheader(rank)
        
        if st.button("道場の入り口に戻る", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()

    else:
        q = st.session_state.current_q
        cat_label = "🧩 構造化の型 (MECE)" if st.session_state.q_index < 3 else "📐 推定の型 (フェルミ)"
        
        st.subheader(f"{cat_label} 第 {st.session_state.q_index + 1} 問")
        st.info(f"**{q['title']}**\n\n{q['q']}")

        if not st.session_state.answered:
            st.write("▼ 回答を選択せよ（制限時間なし）")
            for opt in q['opts']:
                if st.button(opt, key=f"q{st.session_state.q_index}_{opt}", use_container_width=True):
                    st.
