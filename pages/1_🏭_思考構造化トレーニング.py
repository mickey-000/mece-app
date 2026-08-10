# -*- coding: utf-8 -*-
import streamlit as st
from trainers_lib import (
    mece_generate_question,
    mece_feedback,
    apply_style,
    play_se,
    sound_toggle_sidebar,
    DEFINITIONS_MD,
    TOTAL_MECE,
)

st.set_page_config(page_title="思考構造化トレーニング", page_icon="🏭")
apply_style()
st.title("🏭 思考構造化トレーニング")
st.caption(f"製造業の現場発言を ①事象・②問題・③課題・④その他 に切り分ける、全{TOTAL_MECE}問の特訓です。")

sound_toggle_sidebar()

ss = st.session_state

# 効果音の予約再生（送信・完了のタイミングで鳴らす）
if ss.get("mece_play"):
    play_se(ss.mece_play)
    ss.mece_play = None

# ---- 状態の初期化 ----
if "mece_stage" not in ss:
    ss.mece_stage = "intro"   # intro / answer / feedback / done
    ss.mece_q = 0             # 出題済みの問題番号
    ss.mece_problem = ""
    ss.mece_prev = []
    ss.mece_feedback = ""
    ss.mece_ans = ("", "", "", "")


def _reset():
    for k in list(ss.keys()):
        if k.startswith("mece_") or k[:3] in ("a1_", "a2_", "a3_", "a4_"):
            ss.pop(k, None)


def _next_question():
    n = ss.mece_q + 1
    with st.spinner("師範が課題を作成中..."):
        ss.mece_problem = mece_generate_question(n, ss.mece_prev)
    ss.mece_prev.append(ss.mece_problem)
    ss.mece_q = n
    ss.mece_stage = "answer"


# ========== イントロ画面 ==========
if ss.mece_stage == "intro":
    st.info(
        f"**【修業内容】 全{TOTAL_MECE}問**\n\n"
        "現場の「生の発言」を読み、①〜④の枠に切り分けて回答します。\n"
        "各問ごとに師範（AI）が講評と模範解答を返します。"
    )
    with st.expander("🔎 ①②③④の分類定義（迷ったら開いてください）"):
        st.markdown(DEFINITIONS_MD)
    if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
        _next_question()
        st.rerun()

# ========== 完了画面 ==========
elif ss.mece_stage == "done":
    st.balloons()
    st.success(f"🏁 全{TOTAL_MECE}問、完了しました！お疲れさまでした。")
    st.write("切り分けの精度は、繰り返すほど上がっていきます。")
    if st.button("🔄 もう一度挑戦する", type="primary", use_container_width=True):
        _reset()
        st.rerun()

# ========== 出題中 / 講評 ==========
else:
    st.subheader(f"第 {ss.mece_q} 問 ／ 全 {TOTAL_MECE} 問")
    st.progress(ss.mece_q / TOTAL_MECE)
    st.info(f"**🗣️ 現場発言**\n\n{ss.mece_problem}")

    with st.expander("🔎 ①②③④の分類定義（迷ったら開いてください）"):
        st.markdown(DEFINITIONS_MD)

    # --- 回答入力 ---
    if ss.mece_stage == "answer":
        q = ss.mece_q
        st.markdown("##### ✍️ 発言の内容を、下の4つの枠に切り分けて入力してください")
        a1 = st.text_area("① 事象（中立的な事実・数値）", key=f"a1_{q}", height=68,
                          placeholder="例：不良率が3%")
        a2 = st.text_area("② 問題（あるべき姿とのギャップ）", key=f"a2_{q}", height=68,
                          placeholder="例：不良品が多い")
        a3 = st.text_area("③ 課題（解決の具体的アクション。無ければ「該当なし」）", key=f"a3_{q}", height=68,
                          placeholder="例：該当なし")
        a4 = st.text_area("④ その他（感情・主観・評価・決めつけ 等）", key=f"a4_{q}", height=68,
                          placeholder="例：現場のやる気が足りない")

        if st.button("回答を送信して講評を見る", type="primary", use_container_width=True):
            ss.mece_ans = (a1, a2, a3, a4)
            with st.spinner("師範が講評中..."):
                ss.mece_feedback = mece_feedback(ss.mece_problem, a1, a2, a3, a4)
            ss.mece_stage = "feedback"
            ss.mece_play = "success.wav"
            st.rerun()

    # --- 講評表示 ---
    elif ss.mece_stage == "feedback":
        a1, a2, a3, a4 = ss.mece_ans
        with st.chat_message("user", avatar="🙂"):
            st.markdown(
                f"**①事象**：{a1 or '（未記入）'}\n\n"
                f"**②問題**：{a2 or '（未記入）'}\n\n"
                f"**③課題**：{a3 or '（未記入）'}\n\n"
                f"**④その他**：{a4 or '（未記入）'}"
            )
        with st.chat_message("assistant", avatar="🏭"):
            st.markdown(ss.mece_feedback)

        if ss.mece_q < TOTAL_MECE:
            if st.button("次の問題へ ➔", type="primary", use_container_width=True):
                _next_question()
                st.rerun()
        else:
            if st.button("🏁 結果を見る", type="primary", use_container_width=True):
                ss.mece_stage = "done"
                ss.mece_play = "result.wav"
                st.rerun()

# ---- サイドバー：やり直し ----
with st.sidebar:
    st.divider()
    if st.button("🔄 最初からやり直す", use_container_width=True, key="mece_reset_btn"):
        _reset()
        st.rerun()
