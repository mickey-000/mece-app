import streamlit as st
import google.generativeai as genai
import json

# --- 1. API設定 ---
def init_gemini():
    # Secretsチェック
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("【設定エラー】Secretsに GEMINI_API_KEY がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # モデルを「gemini-1.5-flash」に固定（最も安定しているため）
    try:
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"【モデル接続エラー】: {e}")
        st.stop()

model = init_gemini()

# --- 2. 問題生成関数（エラー詳細表示モード） ---
def generate_quiz(idx):
    # 難易度とシーン
    if idx == 0:
        cat, level, scene = "MECE", "初級(日常)", "旅行の準備、冷蔵庫の整理"
    elif idx == 1:
        cat, level, scene = "MECE", "中級(業務)", "会議準備、タスク整理"
    elif idx == 2:
        cat, level, scene = "MECE", "上級(営業実戦)", "顧客ニーズ分析、提案書構成"
    elif idx == 3:
        cat, level, scene = "フェルミ推定", "初級(日常)", "電柱の数、コンビニの売上"
    else:
        cat, level, scene = "フェルミ推定", "上級(営業実戦)", "顧客予算、市場規模"

    prompt = f"""
    あなたは若手営業のメンターです。以下の条件でクイズを1問作成してください。
    【テーマ】{cat}
    【レベル】{level}
    【シーン】{scene}

    以下のJSON形式(日本語)のみを出力してください:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["A", "B", "C"],
        "ans_idx": 0,
        "exp": "解説"
    }}
    ※ ans_idx は正解番号(0,1,2)
    """

    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        # ここでエラーの「正体」を画面に出します
        return {
            "title": "エラー発生", 
            "q": f"▼このエラー文をコピーして教えてください▼\n\n{str(e)}", 
            "opts": ["再試行"], 
            "ans_idx": 0, 
            "exp": "原因特定のため、上記のエラー文が必要です。"
        }

# --- 3. アプリ画面 ---
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.info("現在：エラー診断モード")
    
    if st.button("▶ テスト開始", type="primary"):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("接続テスト中..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

else:
    if st.session_state.idx >= 5:
        st.balloons()
        st.title("完了")
        if st.button("戻る"):
            st.session_state.game = False
            st.rerun()
    else:
        q = st.session_state.q
        st.subheader(f"第{st.session_state.idx + 1}問")
        
        # エラー時は赤字で表示
        if "エラー" in q['title']:
            st.error(q['title'])
            st.code(q['q']) # コピーしやすいようにコードブロックで表示
            st.warning("上記のエラーメッセージをチャットで教えてください！")
        else:
            st.info(f"**{q['title']}**\n\n{q['q']}")
        
        if not st.session_state.ans:
            for i, opt in enumerate(q['opts']):
                if st.button(opt, key=f"btn_{st.session_state.idx}_{i}", use_container_width=True):
                    st.session_state.ans = True
                    if i == q['ans_idx']:
                        st.session_state.last_res = True
                        st.session_state.score += 1
                    else:
                        st.session_state.last_res = False
                    st.rerun()
        else:
            if st.session_state.last_res: st.success("正解")
            else: st.error("不正解")
            st.write(f"解説: {q['exp']}")
            if st.button("次へ", type="primary"):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner("生成中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()
