import streamlit as st
import google.generativeai as genai
import json

# --- 1. API設定 ---
def init_gemini():
    # Secretsのチェック
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("設定エラー: Secretsに GEMINI_API_KEY がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # 利用可能なモデルを探す
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        
        target_model = None
        for p in priority:
            if p in available_models:
                target_model = p
                break
        
        if not target_model and available_models:
            target_model = available_models[0]
            
        if not target_model:
            st.error("利用可能なAIモデルが見つかりませんでした。")
            st.stop()
            
        return genai.GenerativeModel(target_model)

    except Exception as e:
        st.error(f"接続エラーが発生しました: {e}")
        st.stop()

# モデル初期化
model = init_gemini()

# --- 2. 問題生成関数 ---
def generate_quiz(idx):
    # 難易度とシーン設定
    if idx == 0:
        cat, level, scene = "MECE", "初級(日常)", "旅行の準備、冷蔵庫の整理、家事の分担"
    elif idx == 1:
        cat, level, scene = "MECE", "中級(業務)", "会議の準備、タスクの優先順位付け"
    elif idx == 2:
        cat, level, scene = "MECE", "上級(営業実戦)", "顧客の潜在ニーズ分析、提案書の構成"
    elif idx == 3:
        cat, level, scene = "フェルミ推定", "初級(日常)", "日本にある電柱の数、コンビニの売上"
    else:
        cat, level, scene = "フェルミ推定", "上級(営業実戦)", "顧客の年間予算規模、ターゲット市場の規模"

    # プロンプト（AIへの指令書）
    # 中括弧 {{ }} はJSON形式を指定するために必要です
    prompt = f"""
    あなたは若手営業（1〜3年目）のメンターです。
    以下の条件でクイズを1問作成してください。

    【テーマ】{cat}
    【レベル】{level}
    【シーン】{scene}

    以下のJSON形式(日本語)のみを出力してください:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "ans_idx": 0,
        "exp": "解説（営業での活かし方）"
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
            "q": "問題の生成に失敗しました。再試行してください。", 
            "opts": ["再試行"], 
            "ans_idx": 0, 
            "exp": "ネットワークの状態を確認してください。"
        }

# --- 3. アプリ画面構築 ---
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

# スタート画面
if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.markdown("### 日常から実戦へ。論理の「型」を習得せよ。")
    st.info("""
    **【特訓メニュー】**
    1. **日常MECE**: 身近な事象を構造化
    2. **業務MECE**: 仕事のタスクを整理
    3. **営業MECE**: 顧客課題を深掘り
    4. **日常フェルミ**: 身近な数値を推計
    5. **営業フェルミ**: 市場・予算を試算
    """)
    
    if st.button("▶ 入門する（特訓開始）", type="primary", use_container_width=True):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("第一の課題を作成中..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

# ゲーム画面
else:
    if st.session_state.idx >= 5:
        st.balloons()
        st.title("🏁 特訓完了")
        score = st.session_state.score
        st.header(f"結果: {score} / 5")
        
        if score == 5: st.subheader("【免許皆伝】素晴らしい。現場で活かしましょう。")
        elif score >= 3: st.subheader("【高弟】基礎はできています。")
        else: st.subheader("【門下生】日常から意識を変えましょう。")

        if st.button("道場の入り口に戻る", use_container_width=True):
            st.session_state.game = False
            st.rerun()
            
    else:
        q = st.session_state.q
        level_labels = ["🟢 初級(日常)", "🟡 中級(業務)", "🔴 上級(営業)", "🟡 フェルミ(日常)", "🔴 フェルミ(営業)"]
        
        st.subheader(f"第{st.session_state.idx + 1}問：{level_labels[st.session_state.idx]}")
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
                    with st.spinner(f"次の課題を読み込み中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()

# === コードここまで ===
