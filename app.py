import streamlit as st
import google.generativeai as genai
import json
import time
import re

# --- 1. API設定 ---
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets設定エラー: 'GEMINI_API_KEY' が設定されていません。")
        st.stop()
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        priority = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        target = next((m for m in priority if m in models), models[0] if models else None)
        return genai.GenerativeModel(target)
    except:
        st.error("AIへの接続に失敗しました。")
        st.stop()

model = init_gemini()

# --- 2. 問題生成関数 (頑丈な再試行ロジック付) ---
def generate_quiz(idx):
    # 難易度とシーンの設定
    if idx == 0:
        cat, level, scene = "MECE", "初級", "日常生活（旅行準備、家事、買い物など）"
    elif idx == 1:
        cat, level, scene = "MECE", "中級", "一般的なオフィス業務（会議、タスク管理）"
    elif idx == 2:
        cat, level, scene = "MECE", "上級（営業実戦）", "ソリューション営業（顧客課題分析）"
    elif idx == 3:
        cat, level, scene = "フェルミ推定", "初級", "身近な数字（コンビニの売上、電柱の数など）"
    else:
        cat, level, scene = "フェルミ推定", "上級（営業実戦）", "B2B営業（市場規模、顧客予算算出）"

    prompt = f"""
    あなたは若手営業（1〜3年目）のメンターです。以下の条件でクイズを作成してください。
    【テーマ】{cat}
    【レベル】{level}
    【シーン】{scene}

    JSON形式(日本語)のみ出力してください:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["A", "B", "C"],
        "ans_idx": 0, 
        "exp": "解説（営業視点のアドバイス含む）"
    }}
    ※ ans_idx は正解の配列インデックス(0,1,2の数値)
    """

    # 安全フィルター設定（過剰反応を防ぐ）
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # 最大3回までリトライする
    for attempt in range(3):
        try:
            res = model.generate_content(prompt, safety_settings=safety_settings)
            
            # JSONの抽出とクリーニング
            text = res.text
            # ```json ... ``` の中身だけを取り出す工夫
            match = re.search(r'\{.*\}', text, re.DOTALL) 
            if match:
                json_str = match.group(0)
            else:
                json_str = text # そのままトライ

            return json.loads(json_str)
        except Exception as e:
            # 失敗したら少し待って再挑戦
            time.sleep(1)
            continue
            
    # 3回失敗した場合のバックアップ
    return {
        "title": "通信エラー", 
        "q": "問題の生成に失敗しました。もう一度「次へ」を押してください。", 
        "opts": ["再試行"], 
        "ans_idx": 0, 
        "exp": "アクセスが集中している可能性があります。"
    }

# --- 3. メイン画面 ---
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.markdown("### 日常から実戦へ。論理の「型」を習得せよ。")
    st.info("""
    **【特訓メニュー】**
    1. **日常MECE** (初級): 身近な整理整頓
    2. **業務MECE** (中級): 仕事の構造化
    3. **営業MECE** (上級): 顧客課題の深掘り
    4. **日常フェルミ**: 身近な数値の推計
    5. **営業フェルミ**: 市場・予算の試算
    """)
    
    if st.button("▶ 入門する（特訓開始）", type="primary", use_container_width=True):
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
        st.title("🏁 特訓完了")
        score = st.session_state.score
        st.header(f"結果: {score} / 5")
        
        if score == 5: st.subheader("【免許皆伝】素晴らしい論理力です。")
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
            # 選択肢ボタン
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
            # 結果画面
            correct_text = q['opts'][q['ans_idx']]
            if st.session_state.last_res: st.success("⭕ 正解！")
            else: st.error(f"❌ 不正解... 正解は「{correct_text}」")
            
            st.markdown(f"**【指南】**\n{q['exp']}")
            
            if st.button("次の立ち合いへ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner(f"次の課題を読み込み中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()
