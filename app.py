import streamlit as st
import google.generativeai as genai
import time
import json

# --- 1. Gemini API設定（動的モデル検出） ---
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secretsに 'GEMINI_API_KEY' が設定されていません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = None
        for name in ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]:
            if name in models:
                target = name
                break
        if not target and models: target = models[0]
        if not target: raise Exception("利用可能なモデルが見つかりませんでした。")
        return genai.GenerativeModel(target), target
    except Exception as e:
        st.error(f"モデルのリスト取得に失敗しました: {e}")
        st.stop()

model, model_name = init_gemini()

# --- 2. 問題生成関数 ---
def generate_quiz(category_type):
    if category_type == "MECE":
        instruction = "MECE（漏れなくダブりなく）に関する3択問題を作成。1つだけが正解であること。"
    else:
        instruction = "フェルミ推定（論理的な数式構築）に関する3択問題を作成。数値そのものではなく、立式のロジックを問うこと。"

    prompt = f"""
    あなたは戦略コンサルタント育成トレーナーです。
    実務3年目レベルの{category_type}の問題を1問作成し、以下のJSON形式(日本語)で出力してください。
    {{
        "title": "タイトル",
        "q": "問題文（思考力を問う実戦的な内容）",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "cor": "正解の選択肢",
        "exp": "ロジカルな解説（100文字程度）"
    }}
    【指示】{instruction}
    """
    try:
        response = model.generate_content(prompt)
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except Exception as e:
        return {"title": "生成エラー", "q": f"エラー: {str(e)}", "opts": ["再試行"], "cor": "再試行", "exp": "APIの接続を確認してください。"}

# --- 3. 音声再生 ---
def play_correct_sound():
    sound_url = "https://raw.githubusercontent.com/t-okada/assets/main/correct.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mpeg"></audio>', height=0)

# --- 4. セッション管理 ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'q_index' not in st.session_state: st.session_state.q_index = 0
if 'answered' not in st.session_state: st.session_state.answered = False

# --- 5. メイン画面 ---
st.set_page_config(page_title="Biz Logic Gym AI", page_icon="🧠")

if not st.session_state.game_active:
    st.title("🧠 Biz Logic Gym: Infinite")
    st.success(f"接続成功: 使用モデル **{model_name.replace('models/', '')}**")
    st.write("※制限時間はありません。じっくり考えてから回答してください。")
    if st.button("▶ 特訓開始（MECE 3問 + フェルミ 2問）", type="primary"):
        st.session_state.score = 0
        st.session_state.q_index = 0
        st.session_state.game_active = True
        st.session_state.answered = False
        with st.spinner("AIがMECE問題を生成中..."):
            st.session_state.current_q = generate_quiz("MECE")
        st.rerun()

else:
    if st.session_state.q_index >= 5:
        st.balloons()
        st.title("🏁 特訓終了！")
        st.header(f"最終スコア: {st.session_state.score} / 5")
        if st.button("ホームへ戻る"):
            st.session_state.game_active = False
            st.rerun()
    else:
        q = st.session_state.current_q
        st.subheader(f"{'🧩 MECE' if st.session_state.q_index < 3 else '📐 フェルミ'} 第 {st.session_state.q_index + 1} 問")
        st.info(f"**{q['title']}**\n\n{q['q']}")

        if not st.session_state.answered:
            # 回答ボタンの表示（タイマー処理を削除）
            for opt in q['opts']:
                if st.button(opt, key=f"{st.session_state.q_index}_{opt}", use_container_width=True):
                    st.session_state.answered = True
                    if opt == q['cor']:
                        st.session_state.score += 1
                        st.session_state.last_result = "CORRECT"
                        play_correct_sound()
                    else:
                        st.session_state.last_result = "WRONG"
                    st.rerun()
        else:
            # 結果表示
            if st.session_state.last_result == "CORRECT": st.success("⭕ 正解！")
            else: st.error(f"❌ 不正解... 正解は「{q['cor']}」")
            
            st.markdown(f"**AIの解説:** {q['exp']}")
            if st.button("次の問題へ ➔", type="primary"):
                st.session_state.q_index += 1
                st.session_state.answered = False
                if st.session_state.q_index < 5:
                    next_cat = "MECE" if st.session_state.q_index < 3 else "フェルミ推定"
                    with st.spinner(f"AIが{next_cat}問題を生成中..."):
                        st.session_state.current_q = generate_quiz(next_cat)
                st.rerun()
