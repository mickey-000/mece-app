import streamlit as st
import google.generativeai as genai
import json
import time

# --- 1. Gemini API設定 & モデル自動検出 ---
def configure_gemini():
    # Secretsからキーを取得
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("【設定エラー】Secretsに 'GEMINI_API_KEY' が設定されていません。")
        st.stop()
    
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)

    # 利用可能なモデルを自動で探す
    target_model_name = "gemini-pro" # 万が一のためのデフォルト
    try:
        # モデル一覧を取得
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # 優先順位: 1.5-flash -> 1.5-pro -> gemini-pro
        # "models/" という接頭辞がついている場合があるので部分一致で探す
        flash_models = [m for m in available_models if "flash" in m.lower() and "1.5" in m]
        pro_models = [m for m in available_models if "pro" in m.lower() and "1.5" in m]
        
        if flash_models:
            target_model_name = flash_models[0] # 最新のFlashを使う
        elif pro_models:
            target_model_name = pro_models[0]
        elif "models/gemini-pro" in available_models:
            target_model_name = "models/gemini-pro"
            
    except Exception as e:
        # 一覧取得に失敗した場合は、最も一般的な名前を試す
        pass

    return genai.GenerativeModel(target_model_name), target_model_name

# モデルの初期化
try:
    model, model_name_used = configure_gemini()
except Exception as e:
    st.error(f"AIの接続に失敗しました: {e}")
    st.stop()

# --- 2. 問題生成関数 ---
def generate_quiz(category_type):
    # カテゴリに応じた詳細なプロンプトを作成
    if category_type == "MECE":
        detail = "ビジネス課題（売上、組織、工程など）を『漏れなくダブりなく』分解する切り口を問う問題。3択のうち1つだけが完璧なMECEであること。"
    else:
        detail = "未知の数値を推定するための『計算式（因数分解）』を問う問題。3択のうち1つだけが最も論理的で筋の良い数式であること。"

    prompt = f"""
    あなたは戦略コンサルタントの育成トレーナーです。
    以下の指示に従い、{category_type}の問題を1問作成してJSONで出力してください。

    【難易度】コンサル実務3年目レベル
    【テーマ】{detail}

    出力形式（日本語のみ）:
    {{
        "title": "問題のタイトル",
        "q": "問題文（15秒で読める短文）",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "cor": "正解の選択肢（opts内の文字列と完全一致）",
        "exp": "なぜそれが正解か、ロジカルな解説（100文字程度）"
    }}
    """
    try:
        response = model.generate_content(prompt)
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except Exception as e:
        return {
            "title": "生成エラー", 
            "q": f"問題の生成に失敗しました。\n使用モデル: {model_name_used}\nエラー: {str(e)}", 
            "opts": ["再読み込み"], 
            "cor": "再読み込み", 
            "exp": "AIの調子が悪いようです。もう一度試してみてください。"
        }

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
    st.title("🧠 Biz Logic Gym: AI Mode")
    st.write(f"Gemini ({model_name_used.replace('models/', '')}) がその場で難問を作成します。")
    
    if st.button("▶ 特訓開始", type="primary"):
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
        st.header(f"スコア: {st.session_state.score} / 5")
        if st.button("ホームへ戻る"):
            st.session_state.game_active = False
            st.rerun()
    else:
        q = st.session_state.current_q
        # 進行度の表示
        cat_label = "🧩 MECE編" if st.session_state.q_index < 3 else "📐 フェルミ推定編"
        st.subheader(f"{cat_label} 第 {st.session_state.q_index + 1} 問")
        
        # エラー表示対応
        if "生成エラー" in q['title']:
            st.error(q['q'])
            if st.button("再試行"):
                st.rerun()
        else:
            st.info(f"**{q['title']}**\n\n{q['q']}")

            if not st.session_state.answered:
                for opt in q['opts']:
                    if st.button(opt, key=opt, use_container_width=True):
                        st.session_state.answered = True
                        if opt == q['cor']:
                            st.session_state.score += 1
                            st.session_state.last_result = "CORRECT"
                            play_correct_sound()
                        else:
                            st.session_state.last_result = "WRONG"
                        st.rerun()

                # タイマー表示
                t_placeholder = st.empty()
                for t in range(15, -1, -1):
                    t_placeholder.metric("⏳ 残り時間", f"{t}s")
                    if t == 0:
                        st.session_state.answered = True
                        st.session_state.last_result = "TIMEOUT"
                        st.rerun()
                    time.sleep(1)
            else:
                if st.session_state.last_result == "CORRECT": st.success("⭕ 正解！")
                elif st.session_state.last_result == "TIMEOUT": st.warning("⏰ タイムアップ！")
                else: st.error(f"❌ 残念！ 正解は「{q['cor']}」")
                
                st.markdown(f"**解説:** {q['exp']}")
                if st.button("次の問題へ ➔", type="primary"):
                    st.session_state.q_index += 1
                    st.session_state.answered = False
                    if st.session_state.q_index < 5:
                        # 次のカテゴリを判定
                        next_cat = "MECE" if st.session_state.q_index < 3 else "フェルミ推定"
                        with st.spinner(f"AIが{next_cat}問題を生成中..."):
                            st.session_state.current_q = generate_quiz(next_cat)
                    st.rerun()
