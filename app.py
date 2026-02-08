import streamlit as st
import google.generativeai as genai
import json
import random
import base64
import os

# ==========================================
# 1. アプリ設定 & API接続
# ==========================================
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets設定エラー: 'GEMINI_API_KEY' がありません。")
        st.stop()
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    try:
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for keyword in ["flash", "1.5-pro"] for m in all_models if keyword in m), all_models[0])
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"接続エラー: {e}")
        st.stop()

model = init_gemini()

# ==========================================
# 2. 音声設定 (サイドバー) & 再生システム
# ==========================================

# サイドバーにスイッチを設置
with st.sidebar:
    st.header("⚙️ 設定")
    is_sound_on = st.toggle("🔊 音声モード (BGM/SE)", value=True)

def play_sound(file_name):
    """ SE再生用（一回だけ鳴らす） """
    # スイッチがOFFなら何もしない
    if not is_sound_on:
        return

    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay="true">
                    <source src="data:audio/wav;base64,{b64}" type="audio/wav">
                </audio>
                """
            st.components.v1.html(md, height=0)

def play_bgm(file_name):
    """ BGM再生用（ループ再生） """
    # スイッチがOFFなら何もしない
    if not is_sound_on:
        return

    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio autoplay="true" loop="true">
                    <source src="data:audio/wav;base64,{b64}" type="audio/wav">
                </audio>
                """
            st.components.v1.html(md, height=0)

# ==========================================
# 3. 問題生成ロジック
# ==========================================
def generate_quiz(idx):
    scenes_list = [
        ["冷蔵庫の整理", "旅行のパッキング", "防災リュック", "大掃除の分担", "買い物リスト"],
        ["会議アジェンダ", "タスク優先順位", "メール整理", "備品管理", "新人研修"],
        ["顧客ニーズ分析", "提案書構成", "失注理由分析", "顧客セグメント", "ボトルネック特定"],
        ["電柱の数", "コンビニ店舗数", "猫の数", "スマホ利用時間", "自販機の数"],
        ["顧客のIT予算", "新商品市場規模", "美容室の市場規模", "競合売上", "LTV算出"]
    ]
    cats = ["MECE", "MECE", "MECE", "フェルミ推定", "フェルミ推定"]
    levels = ["初級(日常)", "中級(業務)", "上級(営業実戦)", "初級", "上級"]
    
    cat, level = cats[idx], levels[idx]
    selected_scene = random.choice(scenes_list[idx])

    prompt = f"""
    あなたは営業マネージャーです。若手向けに「{cat}」の問題を1問作成してください。
    レベル:{level} シーン:{selected_scene}
    指示:
    - 選択肢はA, B, Cの3択。文頭に記号(A.など)は不要。
    - フェルミ推定の場合は、選択肢を「計算式（分解の軸）」にすること。

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
        return {"title": "再試行", "q": "通信エラー", "opts": ["A","B","C"], "ans_idx": 0, "exp": "エラー"}

# ==========================================
# 4. アプリ画面
# ==========================================

# 初期化
if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

# SE再生予約の消化 (スイッチがONの時のみ鳴る)
if 'trigger_sound' in st.session_state:
    play_sound(st.session_state.trigger_sound)
    del st.session_state.trigger_sound

# --- スタート画面 ---
if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.caption("👈 左のサイドバーで「音声のON/OFF」が切り替えられます")
    
    st.info("""
    **【修業内容】 全5問**
    - **第1〜3問 (MECE)**: 漏れなくダブりなく構造化する力
    - **第4〜5問 (フェルミ推定)**: 未知の数値を論理的に導く力
    """)
    if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("師範が課題を生成中..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

# --- クイズ画面 ---
else:
    # 全問終了時
    if st.session_state.idx >= 5:
        if 'played_final' not in st.session_state:
            st.session_state.trigger_sound = "result.wav"
            st.session_state.played_final = True
            st.rerun()

        st.balloons()
        st.title("🏁 特訓完了")
        score = st.session_state.score
        st.header(f"戦績: {score} / 5")
        
        if score == 5: st.success("【免許皆伝】 素晴らしい！師範級の論理力です。")
        elif score >= 3: st.info("【高弟】 基礎はできています。実戦で磨きをかけましょう。")
        elif score >= 1: st.warning("【書生】 まだまだ修行が必要です。")
        else: st.error("【入門者】 まずは日常のことから構造化する癖をつけましょう。")

        if st.button("道場の入り口に戻る", use_container_width=True):
            if 'played_final' in st.session_state: del st.session_state.played_final
            st.session_state.game = False
            st.rerun()

    # 出題中
    else:
        q = st.session_state.q
        labels = ["🟢 MECE(日常)", "🟡 MECE(業務)", "🔴 MECE(営業)", "🟡 フェルミ(日常)", "🔴 フェルミ(営業)"]
        st.subheader(f"第{st.session_state.idx + 1}問：{labels[st.session_state.idx]}")
        st.info(f"**{q['title']}**\n\n{q['q']}")
        
        # A. 未回答（考え中）
        if st.session_state.ans == False:
            
            # BGM再生 (スイッチがONの時のみ)
            play_bgm("thinking.wav")

            for i, opt in enumerate(q['opts']):
                if st.button(opt, key=f"btn_{st.session_state.idx}_{i}", use_container_width=True):
                    st.session_state.ans = True
                    if i == q['ans_idx']:
                        st.session_state.last_res = True
                        st.session_state.score += 1
                        st.session_state.trigger_sound = "success.wav"
                    else:
                        st.session_state.last_res = False
                        st.session_state.trigger_sound = "failure.wav"
                    st.rerun()
        
        # B. 回答済み（解説表示）
        else:
            if st.session_state.last_res: st.success("⭕ 正解！その通り！")
            else: st.error(f"❌ 不正解... 正解は「{q['opts'][q['ans_idx']]}」")
            st.markdown(f"**【解説】**\n{q['exp']}")
            
            if st.button("次の立ち合いへ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner("師範が次の課題を生成中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()
