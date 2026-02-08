import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 堅牢なAPI接続 (全モデル検索 & エラー回避)
# ==========================================
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets設定エラー: 'GEMINI_API_KEY' がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # 使えるモデルを全検索
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順位: 1.5-flash -> 1.5-pro -> gemini-pro
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
            
        return genai.GenerativeModel(target), target

    except Exception as e:
        st.error(f"API接続エラー: {e}")
        st.stop()

model, model_name_used = init_gemini()

# ==========================================
# 2. 問題生成 (フェルミは「式」を問う形へ)
# ==========================================
def generate_quiz(idx):
    # シーン設定
    scenes = [
        ("MECE", "初級(日常)", "旅行の準備、冷蔵庫の整理、家事の分担"),
        ("MECE", "中級(業務)", "会議アジェンダ作成、タスクの優先順位"),
        ("MECE", "上級(営業実戦)", "顧客ヒアリングの整理、提案書の構成"),
        ("フェルミ推定", "初級(日常)", "日本にある電柱の数、コンビニの売上"),
        ("フェルミ推定", "上級(営業実戦)", "顧客企業の年間予算、ターゲット市場規模")
    ]
    cat, level, scene = scenes[idx]

    # ★ここが変更点：フェルミ推定なら「式」を答えさせる
    if "フェルミ" in cat:
        instruction = """
        【重要：思考プロセスを問う問題】
        - 選択肢に「具体的な数値（例: 100億円）」は絶対に入れないこと。
        - 選択肢は「推定するための計算式（分解の軸）」にすること。
        - 正解は、最も論理的で納得感のある分解式（MECE）であること。
        - 例: 「売上」を問う場合 → 正解選択肢: 「客単価 × 客数 × 回転率」
        """
    else:
        instruction = """
        - 3択問題とし、1つだけが論理的に最適な回答にすること。
        - 選択肢は具体的な行動や分類項目にすること。
        """

    prompt = f"""
    あなたは営業マネージャーです。若手向けに「{cat}」の問題を1問作成してください。
    【レベル】{level} 【シーン】{scene}
    
    {instruction}

    解説は「なぜその分解が妥当か」を営業視点で説くこと。
    以下のJSON形式(日本語)のみを出力すること:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "ans_idx": 0,
        "exp": "解説"
    }}
    ※ans_idxは0, 1, 2の数値。
    """
    
    try:
        res = model.generate_content(prompt)
        text = res.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        return {"title": "エラー", "q": str(e), "opts": ["再試行"], "ans_idx": 0, "exp": "エラー"}

# ==========================================
# 3. アプリ画面
# ==========================================
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.caption(f"Power by {model_name_used.replace('models/', '')}")
    st.info("答えの「数字」ではなく、導き出す「ロジック」を鍛える5番勝負。")
    
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
        labels = ["🟢 MECE(日常)", "🟡 MECE(業務)", "🔴 MECE(営業)", "🟡 フェルミ(日常)", "🔴 フェルミ(営業)"]
        
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
