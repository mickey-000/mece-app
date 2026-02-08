import streamlit as st
import google.generativeai as genai
import json

# --- 1. API設定 (全モデル検索ロジック) ---
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets設定エラー: 'GEMINI_API_KEY' がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # 利用可能なモデルをリストアップし、最適なものを自動選択
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順位: 1.5-flash -> 1.5-pro -> gemini-pro (部分一致で検索)
        target = None
        for keyword in ["flash", "1.5-pro", "gemini-pro"]:
            for m in all_models:
                if keyword in m:
                    target = m
                    break
            if target: break
        
        if not target and all_models:
            target = all_models[0]
            
        if not target:
            st.error("利用可能なモデルが見つかりませんでした。")
            st.stop()
            
        return genai.GenerativeModel(target), target

    except Exception as e:
        st.error(f"API接続エラー: {e}")
        st.stop()

# モデル初期化
model, model_name_used = init_gemini()

# --- 2. 問題生成関数 (日常から実戦への5段階) ---
def generate_quiz(idx):
    # シーンと難易度の設定
    scenes = [
        ("MECE", "初級(日常)", "日常生活（旅行の準備や家事の分担）"),
        ("MECE", "中級(業務)", "オフィス業務（会議の準備やタスク管理）"),
        ("MECE", "上級(営業実戦)", "顧客商談（ヒアリング内容の構造化）"),
        ("フェルミ推定", "初級・中級", "身近な数字（コンビニの売上など）"),
        ("フェルミ推定", "上級(営業実戦)", "営業分析（顧客企業の市場規模算出）")
    ]
    cat, level, scene = scenes[idx]

    prompt = f"""
    あなたは営業マネージャーです。入社1〜3年目の若手向けに「{cat}」の問題を1問作成してください。
    【レベル】{level} 【シーン】{scene}
    指示: 解説は営業現場へのアドバイスを含めること。
    以下のJSON形式(日本語)のみを出力すること:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["A", "B", "C"],
        "ans_idx": 0,
        "exp": "解説"
    }}
    ※ans_idxは0, 1, 2の数値。
    """
    try:
        res = model.generate_content(prompt)
        # JSON部分のみを抽出
        text = res.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {"title": "再試行してください", "q": "生成に失敗しました。", "opts": ["A","B","C"], "ans_idx": 0, "exp": "エラー"}

# --- 3. アプリ画面構築 ---
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

# セッション状態の初期化
if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.caption(f"接続AI: {model_name_used.replace('models/', '')}")
    st.info("日常の整理から、営業の数値試算まで。全5問の思考特訓。")
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
        labels = ["🟢 初級(日常)", "🟡 中級(業務)", "🔴 上級(営業)", "🟡 推定(日常)", "🔴 推定(営業)"]
        st.subheader(f"第{st.session_state.idx + 1}問：{labels[st.session_state.idx]}")
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
            if st.session_state.last_res: st.success("⭕ 正解")
            else: st.error(f"❌ 不正解... 正解は「{q['opts'][q['ans_idx']]}」")
            st.markdown(f"**【指南】**\n{q['exp']}")
            if st.button("次の立ち合いへ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner("次なる課題を生成中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()

# === 完 ===
