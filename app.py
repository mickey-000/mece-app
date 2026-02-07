import streamlit as st
import random
import time

# --------------------------------------------------
# 1. 音声再生用の関数（HTML/JSを使用）
# --------------------------------------------------
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

# --------------------------------------------------
# 2. 問題データベース（サンプル）
# --------------------------------------------------
quiz_dataset = [
    {"type": "mece", "level": "上級", "title": "工場の生産性低下", "q": "工場の生産性が落ちている原因を、設備の視点からMECEに分解しているのは？", "opts": ["故障停止 / 段取り替え / 速度低下 / 不良品手直し", "機械が古い / 作業員が遅い / やる気がない", "停止時間 / 稼働時間"], "cor": "故障停止 / 段取り替え / 速度低下 / 不良品手直し", "exp": "TPM（総合的設備保全）の『7大ロス』に基づいた切り口です。"},
    {"type": "fermi", "level": "フェルミ", "title": "スタバの店舗数", "q": "日本国内のスタバ店舗数を推定する際、最も筋の良いアプローチは？", "opts": ["人口 × コーヒー飲用率", "（主要駅数×周辺数）＋（モール数×内数）＋ロードサイド", "都内店舗数 × 47"], "cor": "（主要駅数×周辺数）＋（モール数×内数）＋ロードサイド", "exp": "立地タイプで分けるのが最も精度が高くなります。"},
    # ...（ここにお題を増やしていけます）
]

# --------------------------------------------------
# 3. アプリ設定 & セッション管理
# --------------------------------------------------
st.set_page_config(page_title="Biz Logic Gym - Time Attack", page_icon="⚡")

if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'q_index' not in st.session_state:
    st.session_state.q_index = 0
if 'answered' not in st.session_state:
    st.session_state.answered = False

# --- スタート画面 ---
if not st.session_state.game_active:
    st.title("⚡ Biz Logic Gym: Time Attack")
    st.write("1問15秒の限界突破トレーニング。")
    if st.button("▶ 特訓開始（5問）", type="primary"):
        st.session_state.questions = random.sample(quiz_dataset, min(5, len(quiz_dataset)))
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.game_active = True
        st.session_state.answered = False
        st.rerun()

# --- クイズ画面 ---
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

        # --- 【目玉機能】タイムアタック・タイマー ---
        timer_placeholder = st.empty()
        
        # 回答待ちの間だけタイマーを回す
        if not st.session_state.answered:
            limit = 15
            start_time = time.time()
            
            # 簡易的なカウントダウンループ
            # 注：Streamlitの仕様上、ループ中はボタン反応が少し重くなるため1秒刻みにしています
            for t in range(limit, -1, -1):
                timer_placeholder.metric("⏳ 残り時間", f"{t}s")
                if t == 0:
                    st.session_state.answered = True
                    st.session_state.last_result = "TIMEOUT"
                    st.rerun()
                time.sleep(1)
                # ユーザーがボタンを押すと、このループを抜けてリロードがかかります
        
        # --- 回答ボタン ---
        if not st.session_state.answered:
            for opt in q['opts']:
                if st.button(opt, use_container_width=True):
                    st.session_state.answered = True
                    if opt == q['cor']:
                        st.session_state.score += 1
                        st.session_state.last_result = "CORRECT"
                        play_correct_sound() # 音を鳴らす
                    else:
                        st.session_state.last_result = "WRONG"
                    st.rerun()
        
        # --- フィードバック ---
        else:
            if st.session_state.last_result == "CORRECT":
                st.success("⭕ 正解！")
            elif st.session_state.last_result == "TIMEOUT":
                st.warning("⏰ 時間切れ！")
            else:
                st.error(f"❌ 残念！ 正解は「{q['cor']}」")
            
            st.write(f"**解説:** {q['exp']}")
            if st.button("次へ進む ➔", type="primary"):
                st.session_state.q_index += 1
                st.session_state.answered = False
                st.rerun()
