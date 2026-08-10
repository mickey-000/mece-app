# -*- coding: utf-8 -*-
import streamlit as st
from trainers_lib import apply_style

st.set_page_config(page_title="思考道場", page_icon="🥋")
apply_style()

st.title("🥋 思考道場")
st.caption("鍛えたい力を選んでください。左のサイドバーからも切り替えられます。")
st.write("")

# (絵文字, タイトル, 説明, ページのパス)
MENU = [
    ("🥋", "コンサル営業クイズ道場",
     "MECE・フェルミ推定を3択クイズで鍛える（全5問・効果音つき）",
     "pages/3_🥋_コンサル営業クイズ道場.py"),
    ("🏭", "思考構造化トレーニング",
     "製造業の現場発言を 事実・問題・課題・その他 に切り分ける（全3問）",
     "pages/1_🏭_思考構造化トレーニング.py"),
    ("🔁", "具体と抽象の往復トレーニング",
     "バラバラな事象から共通の『構造』を見抜く（全5問・ヒントつき）",
     "pages/2_🔁_具体と抽象トレーニング.py"),
]

for emoji, title, desc, path in MENU:
    with st.container(border=True):
        st.markdown(f"### {emoji} {title}")
        st.write(desc)
        if st.button("▶ はじめる", key=path, type="primary", use_container_width=True):
            st.switch_page(path)
    st.write("")
