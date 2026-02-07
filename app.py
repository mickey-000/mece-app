import streamlit as st
import random
import time

# --- 音声再生関数 ---
def play_correct_sound():
    # 正解時の「ピンポン」音（パブリックな音源URL）
    sound_url = "https://raw.githubusercontent.com/t-okada/assets/main/correct.mp3"
    st.components.v1.html(
        f"""
        <audio autoplay>
            <source src="{sound_url}" type="audio/mpeg">
        </audio>
        """,
        height=0,
    )

# --- 問題データベース（サンプル：ここを100問まで増やせます） ---
quiz_dataset = [
    {
        "type": "fermi",
        "level": "フェルミ",
        "title": "スタバの店舗数",
        "q": "日本国内のスタバ店舗数を推定する際、最も筋の良いアプローチ（計算式）を選んでください。",
        "opts": ["人口 × コーヒー飲用率 × シェア", "（主要駅数×周辺数）＋（モール数×内数）＋ロードサイド", "都内店舗数 × 47都道府県"],
        "cor": "（主要駅数×周辺数）＋（モール数×内数）＋ロードサイド",
        "exp": "立地タイプで分解して積み上げるのが、最も実務的で精度の高いアプローチです。"
    },
    {
        "type": "mece",
        "level": "上級",
        "title": "売上不振の分解",
        "q": "ある飲食店の売上不振の原因を、MECEに分解しているのは？",
        "opts": ["客数 × 客単価", "ランチの味 / 接客の質 / 立地の悪さ", "新規顧客数 / 既存顧客（リピート）数"],
        "cor": "新規顧客数 / 既存顧客（リピート）数",
        "exp": "客数を新規と既存に分けることで、具体的な打ち手（販促か改善か）を明確に切り分けられます。"
    },
    # ここにAIで作らせた問題を順次追加してください
]

# --- セッション管理 ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'q_index' not in st.session_state: st.session_state.q_index = 0
if 'answered' not in st.session_state: st.session_state.answered = False

# --- メイン画面 ---
if not st.session_state.game_active:
    st.title("⚡ Biz Logic Gym: Time Attack")
    st.write("1問15秒。すべての問題をボタン選択だけでスピーディーに回答。")
    if st.button("▶ 特訓開始（5問）", type="primary"):
        st.session_state.questions = random.sample(quiz_dataset, min(5, len(quiz_dataset)))
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.game_active = True
        st.session_state.answered = False
        st.rerun()

else:
    if st.session_state.q_index >= len(st.session_state.questions):
        st.balloons()
        st.title("🏁 終了！")
        st.header(f"スコア: {st.session_state.score} / {len(st.session_state.questions)}")
        if st.button("もう一度やる"):
            st.session_state.game_active = False
            st.rerun()
    else:
        q = st.session_state.questions[st.session_state.q_index]
        st.subheader(f"第 {st.session_state.q_index + 1} 問: {q['title']}")
        st.info(q['q'])

        # --- 15秒カウントダウン・タイマー ---
        timer_placeholder = st.empty()
        if not st.session_state.answered:
            limit = 15
            for t in range(limit, -1, -1):
                timer_placeholder.metric("⏳ 残り時間", f"{t}s")
                if t == 0:
                    st.session_state.answered = True
                    st.session_state.last_result = "TIMEOUT"
                    st.rerun()
                time.sleep(1)

        # --- 回答ボタン（フェルミもMECEも共通） ---
        if not st.session_state.answered:
            for opt in q['opts']:
                if st.button(opt, use_container_width=True):
                    st.session_state.answered = True
                    if opt == q['cor']:
                        st.session_state.score += 1
                        st.session_state.last_result = "CORRECT"
                        play_correct_sound()
                    else:
                        st.session_state.last_result = "WRONG"
                    st.rerun()
        
        # --- 結果表示 ---
        else:
            if st.session_state.last_result == "CORRECT":
                st.success("⭕ 正解！")
            elif st.session_state.last_result == "TIMEOUT":
                st.warning("⏰ タイムアップ！")
            else:
                st.error(f"❌ 残念！ 正解は「{q['cor']}」")
            
            st.markdown(f"**解説:** {q['exp']}")
            if st.button("次へ進む ➔", type="primary"):
                st.session_state.q_index += 1
                st.session_state.answered = False
                st.rerun()
