import streamlit as st
import google.generativeai as genai
import json
import time

# --- 1. API設定 ---
def init_gemini():
    # Secretsチェック
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("エラー: Secretsに GEMINI_API_KEY がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 接続テスト
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in ["models/gemini-1.5-flash", "models/gemini-pro"] if m in models), models[0] if models else None)
        return genai.GenerativeModel(target)
    except:
        st.error("AIへの接続に失敗しました。")
        st.stop()

model = init_gemini()

# --- 2. 問題生成 ---
def generate_quiz(cat):
    theme = "営業現場のMECE(構造化)" if cat == "MECE" else "営業のためのフェルミ推定"
    inst = "若手営業(1-3年目)向けの実戦問題。3択。"
    
    # プロンプト（テンプレートを明確化）
    prompt = f"""
    あなたは営業マネージャーです。「{theme}」について、{inst}
    以下のJSON形式(日本語)のみを出力してください:
    {{
        "title": "タイトル",
        "q": "問題文(現場のシーン設定)",
        "opts": ["A", "B", "C"],
        "cor": "正解の選択肢",
        "exp": "解説(アドバイス)"
    }}
    """
    try:
        res = model.generate_content(prompt)
        return json.loads(res.text.replace('```json', '').replace('```', '').strip())
    except:
        return {"title": "通信エラー", "q": "再読み込みしてください", "opts": ["再試行"], "cor": "再試行", "exp": "エラー"}

# --- 3. メイン画面 ---
st.set_page_config(page_title="営業思考道場", page_icon="💼")

# セッション初期化
if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

# スタート画面
if not st.session_state.game:
    st.title("💼 営業×コンサル思考道場")
    st.info("若手営業向け：顧客課題の構造化(MECE)と数値試算(フェルミ)の特訓。制限時間なし。")
    
    if st.button("特訓を開始する", type="primary"):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("課題を作成中..."):
            st.session_state.q = generate_quiz("MECE")
        st.rerun()

# クイズ画面
else:
    if st.session_state.idx >= 5:
        st.balloons()
        st.title("完了")
        st.write(f"スコア: {st.session_state.score}/5")
        if st.button("戻る"):
            st.session_state.game = False
            st.rerun()
    else:
        q = st.session_state.q
        cat = "MECE" if st.session_state.idx < 3 else "フェルミ"
        st.subheader(f"第{st.session_state.idx + 1}問 ({cat})")
        st.info(f"**{q['title']}**\n\n{q['q']}")
        
        if not st.session_state.ans:
            for opt in q['opts']:
                if st.button(opt, use_container_width=True):
                    st.session_state.ans = True
                    st.session_state.last_res = (opt == q['cor'])
                    if st.session_state.last_res: st.session_state.score += 1
                    st.rerun()
        else:
            if st.session_state.last_res: st.success("⭕ 正解")
            else: st.error(f"❌ 不正解... 正解: {q['cor']}")
            st.write(f"**解説:** {q['exp']}")
            
            if st.button("次へ", type="primary"):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    next_cat = "MECE" if st.session_state.idx < 3 else "フェルミ"
                    with st.spinner("次へ..."):
                        st.session_state.q = generate_quiz(next_cat)
                st.rerun()
