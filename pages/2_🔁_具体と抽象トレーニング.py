# -*- coding: utf-8 -*-
import streamlit as st
from trainers_lib import (
    abs_generate_question,
    abs_hint,
    abs_feedback,
    apply_style,
    play_se,
    sound_toggle_sidebar,
    TOTAL_ABS,
)

st.set_page_config(page_title="具体と抽象の往復トレーニング", page_icon="🔁")
apply_style()
st.title("🔁 具体と抽象の往復トレーニング")
st.caption(f"バラバラな事象から共通の『構造』を見抜く、全{TOTAL_ABS}問のステップアップ特訓です。")

sound_toggle_sidebar()

ss = st.session_state

# 効果音の予約再生
if ss.get("abs_play"):
    play_se(ss.abs_play)
    ss.abs_play = None

# ---- 状態の初期化 ----
if "abs_stage" not in ss:
    ss.abs_stage = "intro"   # intro / answer / feedback / done
    ss.abs_q = 0
    ss.abs_problem = ""
    ss.abs_prev = []
    ss.abs_feedback = ""
    ss.abs_ans = ""
    ss.abs_hint = ""


def _reset():
    for k in list(ss.keys()):
        if k.startswith("abs_") or k.startswith("ans_"):
            ss.pop(k, None)


def _next_question():
    n = ss.abs_q + 1
    with st.spinner("師範が課題を作成中..."):
        ss.abs_problem = abs_generate_question(n, ss.abs_prev)
    ss.abs_prev.append(ss.abs_problem)
    ss.abs_q = n
    ss.abs_hint = ""
    ss.abs_stage = "answer"


# ========== イントロ画面 ==========
if ss.abs_stage == "intro":
    st.info(
        f"**【全{TOTAL_ABS}問・ステップアップ形式】**\n\n"
        "- **第1問（初級）**：日常のモノ3つの共通点を見抜く\n"
        "- **第2問（中級）**：ビジネスモデル3つの共通点を見抜く\n"
        "- **第3問（実践）**：営業・コンサルの出来事3つの共通点を見抜く\n"
        "- **第4問（上級）**：2つの例の共通点＋同じ構造の3つ目を自作\n"
        "- **第5問（最上級）**：お題に対し、同じ構造の具体例を2つ自作\n\n"
        "答えは1つではありません。**わからなければ、遠慮なく「💡 ヒントをもらう」を押してください。**"
        "回答すると師範（AI）が解説します。"
    )
    if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
        _next_question()
        st.rerun()

# ========== 完了画面 ==========
elif ss.abs_stage == "done":
    st.balloons()
    st.success(f"🏁 全{TOTAL_ABS}問、完了しました！お疲れさまでした。")
    st.write("具体と抽象を行き来する力は、繰り返すほど鋭くなります。")
    if st.button("🔄 もう一度挑戦する", type="primary", use_container_width=True):
        _reset()
        st.rerun()

# ========== 出題中 / 解説 ==========
else:
    st.subheader(f"第 {ss.abs_q} 問 ／ 全 {TOTAL_ABS} 問")
    st.progress(ss.abs_q / TOTAL_ABS)
    st.info(ss.abs_problem)

    # --- 回答入力 ---
    if ss.abs_stage == "answer":
        q = ss.abs_q

        if ss.abs_hint:
            st.warning(f"💡 **ヒント**\n\n{ss.abs_hint}")

        ans = st.text_area("✍️ あなたの回答", key=f"ans_{q}", height=120,
                           placeholder="思いついた共通点や構造を、自由に書いてください。")
        st.caption("わからないときは 💡 ヒント を押すと、答えは言わずに考え方の切り口を教えます。")

        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button("💡 ヒントをもらう", use_container_width=True):
                with st.spinner("師範がヒントを考え中..."):
                    ss.abs_hint = abs_hint(q, ss.abs_problem)
                st.rerun()
        with c2:
            if st.button("回答して解説を見る", type="primary", use_container_width=True):
                ss.abs_ans = ans
                with st.spinner("師範が解説中..."):
                    ss.abs_feedback = abs_feedback(q, ss.abs_problem, ans)
                ss.abs_stage = "feedback"
                ss.abs_play = "success.wav"
                st.rerun()

    # --- 解説表示 ---
    elif ss.abs_stage == "feedback":
        with st.chat_message("user", avatar="🙂"):
            st.markdown(ss.abs_ans or "（未記入）")
        with st.chat_message("assistant", avatar="🔁"):
            st.markdown(ss.abs_feedback)

        if ss.abs_q < TOTAL_ABS:
            if st.button("次の問題へ ➔", type="primary", use_container_width=True):
                _next_question()
                st.rerun()
        else:
            if st.button("🏁 結果を見る", type="primary", use_container_width=True):
                ss.abs_stage = "done"
                ss.abs_play = "result.wav"
                st.rerun()

# ---- サイドバー：やり直し ----
with st.sidebar:
    st.divider()
    if st.button("🔄 最初からやり直す", use_container_width=True, key="abs_reset_btn"):
        _reset()
        st.rerun()
