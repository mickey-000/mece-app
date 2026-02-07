import streamlit as st
import google.generativeai as genai
import time
import json
import traceback # エラー詳細を表示するためのライブラリ

# --- 1. Gemini API設定 ---
try:
    # ここでキーを読み込んでいます
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-1.5-flash')
    else:
        # Secretsにキーがない場合のエラー
        st.error("【設定エラー】Secretsに 'GEMINI_API_KEY' が見つかりません。")
        st.stop()
except Exception as e:
    st.error(f"【設定エラー】API設定中にエラーが発生しました: {e}")
    st.stop()

# --- 2. 問題生成関数 ---
def generate_quiz(category_type):
    if category_type == "MECE":
        detail = "ビジネス課題を『漏れなくダブりなく』分解する切り口を問う問題。3択。"
    else:
        detail = "数値を推定するための『計算式』を問うフェルミ推定の問題。3択。"

    prompt = f"""
    あなたは戦略コンサルタントの育成トレーナーです。
    {category_type}の問題を1問作成し、以下のJSON形式(日本語)で出力してください。
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["A", "B", "C"],
        "cor": "正解の選択肢",
        "exp": "解説"
    }}
    【テーマ】{detail}
    """
    try:
        response = model.generate_content(prompt)
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except Exception as e:
        # ここでエラーの正体を画面に出します
        error_msg = f"エラー詳細: {str(e)}"
        return {"title": "通信エラー発生", "q": error_msg, "opts": ["再読込", "設定確認", "待機"], "cor": "再読込", "exp": "Secretsの設定か、APIキーの有効性を確認してください。"}

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
st.set_page_config(page_title="Biz Logic Gym Debug", page_icon="🔧")

if not st.session_state.game_active:
    st.title("🔧 AI Logic Gym: Debug Mode")
    st.write("エラーの原因を特定するためのモードです。")
    if st.button("▶ テスト開始", type="primary"):
        st.session_state.score = 0
        st.session_state.q_index = 0
        st.session_state.game_active = True
        st.session_state.answered = False
        with st.spinner("AIに接続テスト中..."):
            st.session_state.current_q = generate_quiz("MECE")
        st.rerun()

else:
    if st.session_state.q_index >= 5:
        st.balloons()
        st.title("完了")
        if st.button("戻る"):
            st.session_state.game_active = False
            st.rerun()
    else:
        q = st.session_state.current_q
        st.subheader(f"第 {st.session_state.q_index + 1} 問")
        
        # エラー時は赤文字で表示
        if "エラー詳細" in q['q']:
            st.error(q['title'])
            st.code(q['q'], language='text') # エラー内容をコピーしやすく表示
            st.warning("上記のエラーメッセージを確認してください。")
        else:
            st.info(q['q'])

        if not st.session_state.answered:
            for opt in q['opts']:
                if st.button(opt, key=opt, use_container_width=True):
                    st.session_state.answered = True
                    if opt == q['cor']:
                        st.session_state.last_result = "CORRECT"
                    else:
                        st.session_state.last_result = "WRONG"
                    st.rerun()
        else:
            if st.session_state.last_result == "CORRECT": st.success("⭕ 正解！")
            else: st.error(f"❌ 不正解... 正解は「{q['cor']}」")
            st.write(q['exp'])
            if st.button("次へ"):
                st.session_state.q_index += 1
                st.session_state.answered = False
                if st.session_state.q_index < 5:
                    cat = "MECE" if st.session_state.q_index < 3 else "フェルミ"
                    st.session_state.current_q = generate_quiz(cat)
                st.rerun()
