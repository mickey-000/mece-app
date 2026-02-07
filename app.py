import streamlit as st
import google.generativeai as genai
import json

# --- 1. API設定（モデル自動検知機能） ---
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("設定エラー: Secretsに GEMINI_API_KEY がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # 404エラー回避策：今使えるモデルのリストを取得
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先的に使いたいモデルのキーワード
        # あなたのProプランで最適なものを選びます
        target = None
        for keyword in ["1.5-flash", "1.5-pro", "gemini-pro"]:
            for m_name in available_models:
                if keyword in m_name:
                    target = m_name
                    break
            if target: break
        
        if not target:
            target = available_models[0] # 何も見つからなければ最初の1つを使う
            
        return genai.GenerativeModel(target), target

    except Exception as e:
        st.error(f"API接続に失敗しました。キーを確認してください: {e}")
        st.stop()

# モデル初期化
model, model_name = init_gemini()

# --- 2. 問題生成関数（日常から実戦への難易度勾配） ---
def generate_quiz(idx):
    # マネージャー視点での難易度設計
    # 第1問は日常、第2問は業務、第3問は営業実戦
    if idx == 0:
        cat, level, scene = "MECE", "初級(日常)", "日常生活（旅行の準備、冷蔵庫の整理、掃除の分担など）"
    elif idx == 1:
        cat, level, scene = "MECE", "中級(業務)", "オフィスでの一般的な業務（会議のアジェンダ作り、資料の構成など）"
    elif idx == 2:
        cat, level, scene = "MECE", "上級(営業実戦)", "顧客課題の整理（ヒアリング内容の構造化、提案の柱立てなど）"
    elif idx == 3:
        cat, level, scene = "フェルミ推定", "中級(日常)", "身近な数字の推計（街のコンビニの数、1日のスマホ使用時間など）"
    else:
        cat, level, scene = "フェルミ推定", "上級(営業実戦)", "営業分析（顧客の年間予算規模、自社サービスの潜在需要など）"

    prompt = f"""
    あなたは入社1〜3年目の若手を育てる営業マネージャーです。
    「思考力の型」を鍛える問題を1問作成してください。

    【形式】{cat}
    【難易度】{level}
    【シーン】{scene}

    指示:
    - 3択問題とし、1つだけが論理的に最適な回答にすること。
    - 解説は「営業現場でどう活かせるか」というマネジメント視点のアドバイスを含めること。
    - JSON形式(日本語)のみを出力すること。

    {{
        "title": "修行テーマ",
        "q": "問い",
        "opts": ["A", "B", "C"],
        "ans_idx": 0,
        "exp": "師範の指南（解説）"
    }}
    """
    try:
        res = model.generate_content(prompt)
        text = res.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {"title": "通信エラー", "q": "再試行してください", "opts": ["A","B","C"], "ans_idx": 0, "exp": "エラー"}

# --- 3. アプリ画面 ---
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

# --- 画面遷移 ---
if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.caption(f"使用中のAI師範: {model_name.replace('models/', '')}")
    st.info("日常の整理術から、営業実戦のロジックまで。全5問の特訓です。")
    
    if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("第一の課題を作成中..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

else:
    if st.session_state.idx >= 5:
        st.balloons()
        st.title("🏁 免許皆伝")
        st.header(f"戦績: {st.session_state.score} / 5")
        if st.button("道場の入り口に戻る", use_container_width=True):
            st.session_state.game = False
            st.rerun()
    else:
        q = st.session_state.q
        level_icons = ["🟢 初級", "🟡 中級", "🔴 上級(営業実戦)", "🟡 初級・中級", "🔴 上級(営業実戦)"]
        st.subheader(f"第{st.session_state.idx + 1}問：{level_icons[st.session_state.idx]}")
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
            if st.session_state.last_res: st.success("⭕ 正解（お見事！）")
            else: st.error(f"❌ 不正解... 正解は「{q['opts'][q['ans_idx']]}」")
            st.markdown(f"**【マネージャーのアドバイス】**\n{q['exp']}")
            if st.button("次の立ち合いへ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner("次なる課題を生成中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()
