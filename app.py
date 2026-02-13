import streamlit as st
import google.generativeai as genai
import json
import random
import base64
import os
import time

# ==========================================
# 1. アプリ設定 & API接続
# ==========================================
st.set_page_config(page_title="営業思考道場", page_icon="🥋", layout="centered")

def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets設定に 'GEMINI_API_KEY' が必要です。")
        st.stop()
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # 高速レスポンスの1.5-flashを使用
    return genai.GenerativeModel('gemini-1.5-flash')

model = init_gemini()

# ==========================================
# 2. 音響システム (Base64再生)
# ==========================================
def play_sound(file_name):
    if st.session_state.get("is_sound_on", True) and os.path.exists(file_name):
        with open(file_name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            md = f'<audio autoplay="true"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>'
            st.components.v1.html(md, height=0)

def play_bgm(file_name):
    if st.session_state.get("is_sound_on", True) and os.path.exists(file_name):
        with open(file_name, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
            md = f'<audio autoplay="true" loop="true"><source src="data:audio/wav;base64,{b64}" type="audio/wav"></audio>'
            st.components.v1.html(md, height=0)

# ==========================================
# 3. サイドバー設定
# ==========================================
with st.sidebar:
    st.header("⚙️ 設定")
    mode = st.radio("修行モード", ["🧠 論理思考 (MECE/フェルミ)", "⏱️ 30秒音声ピッチ"])
    st.divider()
    st.session_state.is_sound_on = st.toggle("🔊 音声モード (BGM/SE)", value=True)
    st.divider()
    user_product = st.text_input("あなたの担当商材", "ビジネスコンサルティング")

# ==========================================
# 4. 【モードA】論理思考クイズ (修正済み)
# ==========================================
def generate_quiz(idx):
    scenes_list = [
        ["冷蔵庫の整理", "旅行のパッキング", "防災リュック"],
        ["会議アジェンダ", "タスク優先順位", "メール整理"],
        ["顧客ニーズ分析", "提案書構成", "失注理由分析"],
        ["電柱の数", "コンビニ店舗数", "猫の数"],
        ["顧客のIT予算", "新商品市場規模", "競合売上"]
    ]
    cats = ["MECE", "MECE", "MECE", "フェルミ推定", "フェルミ推定"]
    levels = ["初級(日常)", "中級(業務)", "上級(営業実戦)", "初級", "上級"]
    
    cat, level = cats[idx], levels[idx]
    selected_scene = random.choice(scenes_list[idx])

    # 1. MECEの選択肢で「その他」を入れないようプロンプトを強化
    prompt = f"""
    あなたは営業マネージャーです。若手向けに「{cat}」の問題を1問作成してください。
    レベル:{level} シーン:{selected_scene}
    指示:
    - 選択肢はA, B, Cの3択。
    - ★重要: 「その他」「どれでもない」「上記すべて」といった逃げの選択肢は絶対に含めないこと。
    - フェルミ推定の場合は、選択肢を具体的な「計算式（分解の軸）」にすること。

    JSON形式のみ出力:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["選択肢1", "選択肢2", "選択肢3"],
        "ans_idx": 0,
        "exp": "解説"
    }}
    """
    try:
        res = model.generate_content(prompt)
        text = res.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(text)
        
        opts = data['opts']
        correct_text = opts[data['ans_idx']]
        random.shuffle(opts)
        data['opts'] = opts
        data['ans_idx'] = opts.index(correct_text)
        return data
    except:
        return {"title": "エラー", "q": "再試行してください", "opts": ["A","B","C"], "ans_idx": 0, "exp": "エラー"}

def run_logic_dojo():
    if 'idx' not in st.session_state: st.session_state.idx = 0
    if 'score' not in st.session_state: st.session_state.score = 0
    if 'game_active' not in st.session_state: st.session_state.game_active = False
    if 'ans_revealed' not in st.session_state: st.session_state.ans_revealed = False

    if not st.session_state.game_active:
        st.title("🥋 営業×コンサル思考道場")
        st.info("第1〜3問: MECE / 第4〜5問: フェルミ推定")
        if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
            st.session_state.game_active = True
            st.session_state.score = 0
            st.session_state.idx = 0
            st.session_state.ans_revealed = False
            with st.spinner("課題を生成中..."):
                st.session_state.current_q = generate_quiz(0)
            st.rerun()
    else:
        if st.session_state.idx >= 5:
            st.balloons()
            st.title("🏁 特訓完了")
            st.header(f"戦績: {st.session_state.score} / 5")
            play_sound("result.wav")
            if st.button("道場の入り口に戻る", use_container_width=True):
                st.session_state.game_active = False
                st.rerun()
        else:
            q = st.session_state.current_q
            st.subheader(f"第{st.session_state.idx + 1}問")
            st.info(f"**{q['title']}**\n\n{q['q']}")

            if not st.session_state.ans_revealed:
                play_bgm("thinking.wav")
                for i, opt in enumerate(q['opts']):
                    if st.button(opt, key=f"ans_{st.session_state.idx}_{i}", use_container_width=True):
                        # 2. 回答ボタン押下後に0.5秒のタメを作る
                        time.sleep(0.5)
                        
                        st.session_state.ans_revealed = True
                        if i == q['ans_idx']:
                            st.session_state.is_correct = True
                            st.session_state.score += 1
                            st.session_state.sound_trigger = "success.wav"
                        else:
                            st.session_state.is_correct = False
                            st.session_state.sound_trigger = "failure.wav"
                        st.rerun()
            else:
                play_sound(st.session_state.get("sound_trigger", ""))
                if st.session_state.is_correct: st.success("⭕ 正解！")
                else: st.error(f"❌ 不正解... 正解は「{q['opts'][q['ans_idx']]}」")
                st.markdown(f"**【解説】**\n{q['exp']}")
                
                if st.button("次の立ち合いへ ➔", type="primary", use_container_width=True):
                    st.session_state.idx += 1
                    st.session_state.ans_revealed = False
                    if st.session_state.idx < 5:
                        with st.spinner("生成中..."):
                            st.session_state.current_q = generate_quiz(st.session_state.idx)
                    st.rerun()

# ==========================================
# 5. 【モードB】30秒ピッチ道場
# ==========================================
def run_pitch_dojo():
    st.title("⏱️ 30秒音声ピッチ道場")
    st.write(f"現在の修行商材: **{user_product}**")
    
    # 詳細は省略（以前のコードの音声ピッチ部分をここに統合）
    st.warning("音声ピッチ機能はマイクとGemini API（有料枠）が必要です。")
    # ...（音声ピッチのロジック）...
    if st.button("お題を生成（仮）"):
        st.write("リモート研修用に、スマホでの実施を推奨します。")

# ==========================================
# 6. メイン制御
# ==========================================
if mode == "🧠 論理思考 (MECE/フェルミ)":
    run_logic_dojo()
else:
    run_pitch_dojo()
