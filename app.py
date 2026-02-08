import streamlit as st
import google.generativeai as genai
import json
import random

# ==========================================
# 1. 接続設定
# ==========================================
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
# 2. 音声再生用の関数 (HTML/JS埋め込み)
# ==========================================
def play_correct_sound():
    # 正解時の「ピンポン」音 (フリー素材のURLを使用)
    sound_url = "https://www.soundjay.com/buttons/sounds/button-09.mp3"
    st.components.v1.html(
        f"""
        <audio autoplay>
            <source src="{sound_url}" type="audio/mp3">
        </audio>
        """,
        height=0,
    )

# ==========================================
# 3. 問題生成 (ランダムシーン & シャッフル)
# ==========================================
def generate_quiz(idx):
    # シーンのバリエーションを定義（ランダムに選ぶ）
    if idx == 0:
        cat, level = "MECE", "初級(日常)"
        scenes = ["冷蔵庫の整理", "旅行のパッキング", "防災リュックの中身", "大掃除の役割分担", "スーパーの買い物リスト"]
    elif idx == 1:
        cat, level = "MECE", "中級(業務)"
        scenes = ["会議のアジェンダ作成", "タスクの優先順位付け", "メールフォルダの整理", "オフィスの備品管理"]
    elif idx == 2:
        cat, level = "MECE", "上級(営業実戦)"
        scenes = ["顧客の潜在ニーズ分析", "提案書の構成要素", "失注理由の分析", "ターゲット顧客のセグメンテーション"]
    elif idx == 3:
        cat, level = "フェルミ推定", "初級"
        scenes = ["日本にある電柱の数", "国内のコンビニ店舗数", "日本にいる猫の数", "1日のスマホ利用時間", "東京ドームの容積"]
    else:
        cat, level = "フェルミ推定", "上級"
        scenes = ["顧客企業の年間IT予算", "新商品の市場規模", "全国の美容室の市場規模", "競合他社の売上推定"]

    # シーンをランダムに決定
    selected_scene = random.choice(scenes)

    prompt = f"""
    あなたは営業マネージャーです。若手向けに「{cat}」の問題を1問作成してください。
    レベル:{level} シーン:{selected_scene}
    指示:
    - 選択肢はA, B, Cの3択。
    - 解説は営業現場での活かし方を含めること。
    - フェルミ推定の場合は、選択肢を「数値」ではなく「計算式（分解の軸）」にすること。
    - 正解の選択肢はランダムに配置してよい。

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
        
        # 選択肢のシャッフル処理 (バイアス除去)
        opts = data['opts']
        correct_text = opts[data['ans_idx']]
        random.shuffle(opts)
        data['opts'] = opts
        data['ans_idx'] = opts.index(correct_text)
        
        return data
    except:
        return {"title": "通信エラー", "q": "再試行してください", "opts": ["A","B","C"], "ans_idx": 0, "exp": "エラー"}

# ==========================================
# 4. アプリ画面
# ==========================================
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False
if 'play_sound' not in st.session_state: st.session_state.play_sound = False

# --- スタート画面 ---
if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    
    # ガイダンスの追加
    st.info("""
    **【修業内容】 全5問**
    - **第1〜3問 (MECE)**: 漏れなくダブりなく構造化する力
    - **第4〜5問 (フェルミ推定)**: 未知の数値を論理的に導く力
    """)
    
    st.markdown("答えの「数字」ではなく、導き出す「ロジック」を鍛える特訓です。")
    
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
    # 音声再生フラグが立っていたら音を鳴らす
    if st.session_state.play_sound:
        play_correct_sound()
        st.session_state.play_sound = False # 一回鳴らしたらオフにする

    # 終了判定
    if st.session_state.idx >= 5:
        st.balloons()
        st.title("🏁 特訓完了")
        score = st.session_state.score
        
        # ランク分けロジック
        st.header(f"戦績: {score} / 5")
        if score == 5:
            st.success("【免許皆伝】 素晴らしい！師範級の論理力です。")
        elif score >= 3:
            st.info("【高弟】 基礎はできています。実戦で磨きをかけましょう。")
        elif score >= 1:
            st.warning("【書生】 まだまだ修行が必要です。ロジックの癖を見直しましょう。")
        else:
            st.error("【入門者】 まずは日常のことから構造化する癖をつけましょう。")

        if st.button("道場の入り口に戻る", use_container_width=True):
            st.session_state.game = False
            st.rerun()
            
    # 問題表示
    else:
        q = st.session_state.q
        labels = ["🟢 MECE(日常)", "🟡 MECE(業務)", "🔴 MECE(営業)", "🟡 フェルミ(日常)", "🔴 フェルミ(営業)"]
        
        st.subheader(f"第{st.session_state.idx + 1}問：{labels[st.session_state.idx]}")
        st.info(f"**{q['title']}**\n\n{q['q']}")
        
        # A. 未回答時
        if st.session_state.ans == False:
            for i, opt in enumerate(q['opts']):
                if st.button(opt, key=f"btn_{st.session_state.idx}_{i}", use_container_width=True):
                    st.session_state.ans = True
                    # 正誤判定
                    if i == q['ans_idx']:
                        st.session_state.last_res = True
                        st.session_state.score += 1
                        st.session_state.play_sound = True # 音を鳴らす予約
                    else:
                        st.session_state.last_res = False
                    st.rerun()
        
        # B. 回答済み時
        else:
            correct_opt = q['opts'][q['ans_idx']]
            
            if st.session_state.last_res:
                st.success("⭕ 正解！その通り！")
            else:
                st.error(f"❌ 不正解... 正しいアプローチは「{correct_opt}」")
            
            st.markdown(f"**【解説】**\n{q['exp']}")
            
            if st.button("次の立ち合いへ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner("師範が次の課題を生成中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()

# === END ===
