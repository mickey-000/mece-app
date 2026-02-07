import streamlit as st
import google.generativeai as genai
import json

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

# --- 2. 問題生成関数 (難易度・シーン可変型) ---
def generate_quiz(idx):
    # 問題の属性をインデックス(0-4)に基づいて設定
    if idx == 0:
        cat, level, scene = "MECE", "初級", "日常生活（旅行の準備、冷蔵庫の整理など）"
    elif idx == 1:
        cat, level, scene = "MECE", "中級", "一般的なオフィス業務（会議準備、タスク管理など）"
    elif idx == 2:
        cat, level, scene = "MECE", "上級（営業実戦）", "ソリューション営業（顧客課題の深掘り、提案骨子など）"
    elif idx == 3:
        cat, level, scene = "フェルミ推定", "初級・中級", "日常生活や身近な市場（近所のコンビニの売上、街の美容室の数など）"
    else:
        cat, level, scene = "フェルミ推定", "上級（営業実戦）", "B2B営業（顧客の年間予算、ターゲット企業の潜在需要など）"

    prompt = f"""
    あなたは若手営業（入社1〜3年目）を育てるマネージャーです。
    以下の条件で「思考力の型」を鍛える問題を1問作成してください。

    【形式】{cat}
    【難易度】{level}
    【シーン】{scene}

    指示:
    - 3択問題とし、1つだけが論理的に最適な回答にすること。
    - 解説は「営業現場でどう活かせるか」という視点を必ず含めること。
    - 以下のJSON形式のみを出力すること。

    {{
        "title": "今回の修行テーマ",
        "q": "状況設定と問い",
        "opts": ["選択肢1", "選択肢2", "選択肢3"],
        "ans_idx": 0,
        "exp": "マネージャーからの指南（解説）"
    }}
    """
    try:
        res = model.generate_content(prompt)
        text = res.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {"title": "通信途絶", "q": "再試行せよ", "opts": ["A","B","C"], "ans_idx": 0, "exp": "エラー"}

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
    **【特訓のステップ】**
    1. **日常MECE**：身近な事象を漏れなく分ける（初級）
    2. **業務MECE**：仕事の進め方を構造化する（中級）
    3. **営業MECE**：顧客課題を鋭く分析する（実戦）
    4. **日常フェルミ**：身近な数字を論理で導く
    5. **営業フェルミ**：顧客の予算やポテンシャルを弾く
    """)
    
    if st.button("▶ 入門する（特訓開始）", type="primary", use_container_width=True):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("師範が第一の課題を作成中..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

else:
    if st.session_state.idx >= 5:
        st.balloons()
        st.title("🏁 特訓完了")
        score = st.session_state.score
        st.header(f"五番勝負の結果: {score} / 5")
        
        if score == 5: st.subheader("【免許皆伝】素晴らしい。現場でもその論理を振るえ。")
        elif score >= 3: st.subheader("【高弟】基本は身についた。あとは実戦あるのみ。")
        else: st.subheader("【門下生】焦るな。日常のすべてが修行の場である。")

        if st.button("道場の入り口に戻る", use_container_width=True):
            st.session_state.game = False
            st.rerun()
            
    else:
        q = st.session_state.q
        # 難易度バッジを表示
        level_icons = ["🟢 初級", "🟡 中級", "🔴 上級(営業実戦)", "🟡 中級", "🔴 上級(営業実戦)"]
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
            if st.session_state.last_res: st.success("⭕ 正解（お見事）")
            else: st.error(f"❌ 不正解... 正解は「{q['opts'][q['ans_idx']]}」")
            
            st.markdown(f"**【指南】**\n{q['exp']}")
            
            if st.button("次の立ち合いへ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner(f"第{st.session_state.idx+1}の課題を読み込み中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()
