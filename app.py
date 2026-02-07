import streamlit as st
import google.generativeai as genai
import json
import time

# --- 1. Gemini API設定 ---
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets設定エラー: 'GEMINI_API_KEY' がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 利用可能なモデルを自動探索
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 優先順位リスト
        priority = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        target = next((m for m in priority if m in models), models[0] if models else None)
            
        if not target: raise Exception("有効なモデルが見つかりません")
        return genai.GenerativeModel(target), target
    except Exception as e:
        st.error(f"接続エラー: {e}")
        st.stop()

model, model_name_used = init_gemini()

# --- 2. 問題生成関数 ---
def generate_quiz(category_type):
    if category_type == "MECE":
        theme = "ビジネスのMECE（漏れなくダブりなく）"
        inst = "3つの選択肢のうち、1つだけが『完全にMECE』な切り口であること。"
    else:
        theme = "フェルミ推定（因数分解のロジック）"
        inst = "3つの選択肢のうち、1つだけが『最も筋の良い計算式』であること。"

    # JSONテンプレートをシンプルに定義
    prompt = f"""
    あなたはコンサルタント育成の師範です。
    実務3年目レベルの「{theme}」の問題を1問作成してください。
    条件: {inst}
    
    以下のJSON形式(日本語)のみを出力してください:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "cor": "正解の選択肢",
        "exp": "解説"
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

# --- 3. 音声再生 ---
def play_correct_sound():
    sound_url = "https://raw.githubusercontent.com/t-okada/assets/main/correct.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mpeg"></audio>', height=0)

# --- 4. メイン処理 ---
st.set_page_config(page_title="思考力道場", page_icon="🥋", layout="centered")

if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'q_index' not in st.session_state: st.session_state.q_index = 0
if 'answered' not in st.session_state: st.session_state.answered = False

if not st.session_state.game_active:
    st.title("🥋 コンサル脳を鍛える思考力道場")
    st.caption(f"師範AI: {model_name_used.replace('models/', '')}")
    st.info("MECE 3問 + フェルミ 2問。制限時間なし。")
    
    if st.button("▶ 入門する", type="primary", use_container_width=True):
        st.session_state.score = 0
        st.session_state.q_index = 0
        st.session_state.game_active = True
        st.session_state.answered = False
        with st.spinner("出題準備中..."):
            st.session_state.current_q = generate_quiz("MECE")
        st.rerun()

else:
    if st.session_state.q_index >= 5:
        st.balloons()
        st.title("🏁 免許皆伝")
        st.header(f"スコア: {st.session_state.score} / 5")
        if st.button("戻る", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()
    else:
        q = st.session_state.current_q
        cat = "MECE" if st.session_state.q_index < 3 else "フェルミ推定"
        st.subheader(f"{cat} 第{st.session_state.q_index + 1}問")
        st.info(f"**{q['title']}**\n\n{q['q']}")

        if not st.session_state.answered:
            for opt in q['opts']:
                if st.button(opt, key=f"btn_{st.session_state.q_index}_{opt}", use_container_width=True):
                    st.session_state.answered = True
                    if opt == q['cor']:
                        st.session_state.score += 1
                        st.session_state.last_result = "CORRECT"
                        play_correct_sound()
                    else:
                        st.session_state.last_result = "WRONG"
                    st.rerun()
        else:
            if st.session_state.last_result == "CORRECT":
                st.success("⭕ 正解（見事なり）")
            else:
                st.error(f"❌ 不正解... 正解は「{q['cor']}」")
            st.markdown(f"**【指南】** {q['exp']}")
            
            if st.button("次へ ➔", type="primary", use_container_width=True):
                st.session_state.q_index += 1
                st.session_state.answered = False
                if st.session_state.q_index < 5:
                    next_cat = "MECE" if st.session_state.q_index < 3 else "フェルミ推定
