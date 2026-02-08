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
# 2. 音声再生 (公式機能 st.audio を使用)
# ==========================================
def play_correct_sound():
    # プレイヤーを画面から隠すCSS
    st.markdown(
        """
        <style>
            /* オーディオプレイヤーを非表示にする */
            audio { display: none; }
        </style>
        """,
        unsafe_allow_html=True
    )
    # Streamlitの公式機能で自動再生 (SoundJayの無料素材)
    try:
        st.audio("https://www.soundjay.com/buttons/sounds/button-09.mp3", format="audio/mp3", autoplay=True)
    except:
        pass # 音が出なくてもエラーにはしない

# ==========================================
# 3. 問題生成 (ABC問題の修正)
# ==========================================
def generate_quiz(idx):
    # シーン設定
    if idx == 0:
        cat, level = "MECE", "初級(日常)"
        scenes = ["冷蔵庫の整理", "旅行のパッキング", "防災リュック", "大掃除の分担", "買い物リスト"]
    elif idx == 1:
        cat, level = "MECE", "中級(業務)"
        scenes = ["会議アジェンダ", "タスク優先順位", "メール整理", "備品管理", "新人研修"]
    elif idx == 2:
        cat, level = "MECE", "上級(営業実戦)"
        scenes = ["顧客ニーズ分析", "提案書構成", "失注理由分析", "顧客セグメント", "ボトルネック特定"]
    elif idx == 3:
        cat, level = "フェルミ推定", "初級"
        scenes = ["電柱の数", "コンビニ店舗数", "猫の数", "スマホ利用時間", "自販機の数"]
    else:
        cat, level = "フェルミ推定", "上級"
        scenes = ["顧客のIT予算", "新商品市場規模", "美容室の市場規模", "競合売上", "LTV算出"]

    selected_scene = random.choice(scenes)

    # ★修正点：AIに「A. B. C. を書くな」と指示
    prompt = f"""
    営業マネージャーとして、若手向けに「{cat}」の問題を1問作成せよ。
    レベル:{level} シーン:{selected_scene}
    
    【重要指示】
    - 選択肢の文頭に「A.」「1.」などの記号は絶対に付けないこと。内容のみ記述せよ。
    - フェルミ推定の選択肢は「計算式（分解の軸）」にすること。
    
    出力はJSONのみ:
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
        
        # シャッフル処理
        opts = data['opts']
        
        # 万が一AIが記号をつけてしまった場合のためのクリーニング処理
        clean_opts = []
        for opt in opts:
            # "A. " や "1. " を削除して綺麗にする
            cleaned = opt.replace("A.", "").replace("B.", "").replace("C.", "").replace("1.", "").replace("2.", "").replace("3.", "").strip()
            clean_opts.append(cleaned)
            
        correct_text = clean_opts[data['ans_idx']] # 正解のテキストを保持
        
        random.shuffle(clean_opts) # 選択肢を混ぜる
        
        data['opts'] = clean_opts
        data['ans_idx'] = clean_opts.index(correct_text) # 新しい正解位置を特定
        
        return data
    except:
        return {
            "title": "通信エラー", "q": "再試行してください", 
            "opts": ["再試行"], "ans_idx": 0, "exp": "エラー"
        }

# ==========================================
# 4. アプリ画面
# ==========================================
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False
if 'play_sound' not in st.session_state: st.session_state.play_sound = False

if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
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

else:
    # 音声再生 (HTML埋め込みではなくst.audioを使用)
    if st.session_state.play_sound:
        play_correct_sound()
        st.session_state.play_sound = False 

    if st.session_state.idx >= 5:
        st.balloons()
        st.title("🏁 特訓完了")
        score = st.session_state.score
        st.header(f"戦績: {score} / 5")
        
        if score == 5: st.success("【免許皆伝】 素晴らしい！師範級の論理力です。")
        elif score >= 3: st.info("【高弟】 基礎はできています。実戦で磨きをかけましょう。")
        elif score >= 1: st.warning("【書生】 まだまだ修行が必要です。")
        else: st.error("【入門者】 まずは日常のことから構造化する癖をつけましょう。")

        if st.button("道場の入り口に戻る", use_container_width=True):
            st.session_state.game = False
            st.rerun()
    else:
        q = st.session_state.q
        labels = ["🟢 MECE(日常)", "🟡 MECE(業務)", "🔴 MECE(営業)", "🟡 フェルミ(日常)", "🔴 フェルミ(営業)"]
        
        st.subheader(f"第{st.session_state.idx + 1}問：{labels[st.session_state.idx]}")
        st.info(f"**{q['title']}**\n\n{q['q']}")
        
        if st.session_state.ans == False:
            # 選択肢ボタン (A, B, C のラベルは付けず、ボタンの位置で判断させる)
            for i, opt in enumerate(q['opts']):
                if st.button(opt, key=f"btn_{st.session_state.idx}_{i}", use_container_width=True):
                    st.session_state.ans = True
                    if i == q['ans_idx']:
                        st.session_state.last_res = True
                        st.session_state.score += 1
                        st.session_state.play_sound = True
                    else:
                        st.session_state.last_res = False
                    st.rerun()
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
