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

# --- 2. 問題生成関数 (営業実戦プロンプト) ---
def generate_quiz(category_type):
    if category_type == "MECE":
        theme = "営業現場での顧客課題の構造化（MECE）"
        inst = "若手営業が顧客ニーズを整理したり、提案の柱を立てる際の『切り口』を問う実戦的な問題。"
    else:
        theme = "営業のための数値予測（フェルミ推定）"
        inst = "顧客の市場規模や予算規模を、営業の限られた情報から論理的に推計する立式の問題。"

    prompt = f"""
    あなたは営業とコンサルの両方の経験を持つシニアマネージャーです。
    入社1〜3年目の営業職が「コンサルティング思考」を武器にするための、{theme}の問題を1問作成してください。

    【難易度】若手営業（1〜3年目）レベル
    【条件】
    1. 営業活動（提案、商談準備、分析）に直結するシーン設定にすること。
    2. 3つの選択肢のうち、1つだけが論理的に正しいものにすること。
    
    以下のJSON形式(日本語)のみを出力してください:
    {{
        "title": "営業シーン設定（短く）",
        "q": "問題文（現場で起こりうる具体的な状況）",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "cor": "正解の選択肢",
        "exp": "若手へのアドバイス（なぜこの考え方が受注や顧客満足に繋がるかの解説）"
    }}
    【指示詳細】{inst}
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
st.set_page_config(page_title="営業×コンサル思考道場", page_icon="💼", layout="centered")

if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'q_index' not in st.session_state: st.session_state.q_index = 0
if 'answered' not in st.session_state: st.session_state.answered = False

if not st.session_state.game_active:
    st.title("🥋 思考力道場：営業実戦編")
    st.markdown("### コンサル思考を武器に、営業の『質』を変える。")
    st.info("""
    **【この特訓の目的】**
    単なる物売りではなく、顧客の課題を構造化し、数値の裏付けを持って提案できる「ソリューション営業」へのステップアップ。
    
    - 第1〜3問：**構造化の型 (MECE)**：顧客ニーズや課題の整理
    - 第4〜5問：**推計の型 (フェルミ)**：市場規模やポテンシャルの算出
    """)
    
    if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
        st.session_state.score = 0
        st.session_state.q_index = 0
        st.session_state.game_active = True
        st.session_state.answered = False
        with st.spinner("営業課題を生成中..."):
            st.session_state.current_q = generate_quiz("MECE")
        st.rerun()

else:
    if st.session_state.q_index >= 5:
        st.balloons()
        st.title("🏁 特訓完了")
        score = st.session_state.score
        if score == 5: msg = "素晴らしい！顧客に信頼されるコンサル営業の資質があります。"
        elif score >= 3: msg = "良きセンスです。現場でこの論理を意識して使いましょう。"
        else: msg = "伸びしろがあります。まずは顧客の話を「分ける」ことから始めましょう。"
        
        st.header(f"今回の評価スコア: {score} / 5")
        st.write(msg)
        if st.button("道場の入り口へ戻る", use_container_width=True):
            st.session_state.game_active = False
            st.rerun()
    else:
        q = st.session_state.current_q
        cat = "🧩 構造化編" if st.session_state.q_index < 3 else "📐 推計編"
        st.subheader(f"{cat} 第{st.session_state.q_index + 1}問")
        st.info(f"**{q['title']}**\n\n{q['q']}")

        if not st.session_state.answered:
            for opt in q['opts']:
                if st.button(opt, key=f"btn_{st.session_state.q_index}_{opt}", use_container_width=True):
                    st.session_state.answered = True
                    if opt == q['cor']:
                        st.session_state.score += 1
                        st.session_state.last_result = "CORRECT"
                    else:
                        st.session_state.last_result = "WRONG"
                    st.rerun()
        else:
            if st.session_state.last_result == "CORRECT":
                st.success("⭕ 正解です")
            else:
                st.error(f"❌ 不正解... 正解は「{q['cor']}」")
            st.markdown(f"**【マネージャーのアドバイス】**\n{q['exp']}")
            
            if st.button("次の課題へ ➔", type="primary", use_container_width=True):
                st.session_state.q_index += 1
                st.session_state.answered = False
                if st.session_state.q_index < 5:
                    next_cat = "MECE" if st.session_state.q_index < 3 else "フェルミ推定"
                    with st.spinner(f"次なる課題を読み
