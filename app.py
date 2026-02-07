import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 最強のAPI接続 (全モデル検索ロジック)
# ==========================================
def init_gemini():
    # Secretsチェック
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("エラー: Secretsに GEMINI_API_KEY が設定されていません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # 【ここがポイント】利用可能なモデルを全てリストアップする
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順位: 1.5 Flash (高速) -> 1.5 Pro (高性能) -> Pro (旧安定版)
        # 部分一致で探すことで、バージョン番号が変わっても対応できる
        target_model_name = None
        priority_keywords = ["flash", "1.5-pro", "gemini-pro"]
        
        for keyword in priority_keywords:
            for m in all_models:
                if keyword in m:
                    target_model_name = m
                    break
            if target_model_name: break
        
        # もし優先モデルが見つからなくても、リストにある最初のモデルを使う（絶対につながる）
        if not target_model_name and all_models:
            target_model_name = all_models[0]
            
        if not target_model_name:
            st.error("利用可能なモデルが見つかりませんでした。")
            st.stop()
            
        return genai.GenerativeModel(target_model_name), target_model_name

    except Exception as e:
        st.error(f"接続エラー: {e}")
        st.stop()

# モデルの初期化
model, model_name_used = init_gemini()

# ==========================================
# 2. 問題生成 (日常→実戦の5段階)
# ==========================================
def generate_quiz(idx):
    # 難易度とシーンの設定
    if idx == 0:
        cat, level, scene = "MECE", "初級(日常)", "旅行の準備、冷蔵庫の整理、掃除の分担"
    elif idx == 1:
        cat, level, scene = "MECE", "中級(業務)", "会議アジェンダ作成、タスクの優先順位"
    elif idx == 2:
        cat, level, scene = "MECE", "上級(営業実戦)", "顧客ヒアリングの整理、提案書の構成"
    elif idx == 3:
        cat, level, scene = "フェルミ推定", "初級(日常)", "日本にある電柱の数、コンビニの売上"
    else:
        cat, level, scene = "フェルミ推定", "上級(営業実戦)", "顧客企業の年間予算、ターゲット市場規模"

    prompt = f"""
    あなたは若手営業（1〜3年目）のメンターです。
    以下の条件でクイズを1問作成してください。

    【テーマ】{cat}
    【レベル】{level}
    【シーン】{scene}

    指示:
    - 3択問題。
    - 解説は「営業現場での活かし方」を含めること。
    - 以下のJSON形式(日本語)のみを出力すること。

    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "ans_idx": 0,
        "exp": "解説"
    }}
    ※ ans_idx は正解の番号(0, 1, 2)です。
    """

    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {
            "title": "通信エラー", 
            "q": "再試行してください", 
            "opts": ["再試行"], 
            "ans_idx": 0, 
            "exp": "エラー"
        }

# ==========================================
# 3. アプリ画面
# ==========================================
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

# --- スタート画面 ---
if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.caption(f"接続中のAI: {model_name_used.replace('models/', '')}") # 安心のため接続モデルを表示
    st.info("日常の整理から営業実戦まで。全5問の思考特訓。")
    
    if st.button("▶ 入門する（特訓開始）", type="primary", use_container_width=True):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("第一の課題を作成中..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

# --- クイズ画面 ---
else:
    if st.session_state.idx >= 5:
        st.balloons()
        st.title("🏁 特訓完了")
        st.header(f"結果: {st.session_state.score} / 5")
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
            if st.session_state.last_res: st.success("⭕ 正解！")
            else: st.error(f"❌ 不正解... 正解は「{q['opts'][q['ans_idx']]}」")
            
            st.markdown(f"**【指南】**\n{q['exp']}")
            
            if st.button("次の立ち合いへ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner("次の課題を準備中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()
