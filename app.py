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

with st.sidebar:
    st.header("⚙️ 設定")
    is_sound_on = st.toggle("🔊 音声モード (BGM/SE)", value=True)

def play_sound(file_name):
    """ SE再生用（0.5秒遅延） """
    if not is_sound_on:
        return

    if os.path.exists(file_name):
        with open(file_name, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio id="se_audio">
                    <source src="data:audio/wav;base64,{b64}" type="audio/wav">
                </audio>
                <script>
                    setTimeout(function() {{
                        var audio = document.getElementById('se_audio');
                        if (audio) {{
                            audio.play();
                        }}
                    }}, 500);
                </script>
                """
            st.components.v1.html(md, height=0)

def play_bgm(file_name):
    """ BGM再生用 """
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
    # 若手社員が直面しやすいシーンにアップデート
    scenes_list = [
        ["デスク周りの整理", "出張の持ち物準備", "飲み会の店選び", "共有フォルダの仕分け", "TODOリストの作成"],
        ["日報の書き方", "議事録の項目作成", "先輩への進捗報告", "名刺の管理方法", "備品の補充ルール"],
        ["初めてのテレアポ準備", "担当顧客の業界分析", "商談後の振り返り", "ヒアリング項目の整理", "失注アンケートの集計"],
        ["オフィス街の弁当需要", "通勤電車の混雑数", "近所のコンビニの客数", "1日のメール受信件数", "社内自販機の売上"],
        ["カフェの1日売上", "近隣オフィスのコピー用紙消費量", "同期の年間コーヒー代", "世の中のスマホケース需要", "1時間のテレアポ件数"]
    ]
    cats = ["MECE", "MECE", "MECE", "フェルミ推定", "フェルミ推定"]
    levels = ["初級(日常)", "中級(業務)", "上級(営業実戦)", "初級", "上級"]
    
    cat, level = cats[idx], levels[idx]
    selected_scene = random.choice(scenes_list[idx])

    prompt = f"""
    あなたは若手社員の教育担当（メンター）です。
    入社1〜3年目の若手社員が成長するために必要な「{cat}」の問題を1問作成してください。

    設定:
    - レベル: {level}
    - シーン: {selected_scene}

    指示:
    - 選択肢はA, B, Cの3択。文頭に記号(A.など)は不要。
    - MECEの問題では、「その他」「上記以外」「状況による」といった曖昧な選択肢を**絶対に含めない**でください。
    - 若手社員が「現場でどう考えるべきか」を学べる、具体的で実践的な選択肢にしてください。
    - フェルミ推定の場合は、選択肢を「計算式（分解の軸）」にすること。
    - 語り口は、若手に語りかけるような、丁寧で前向きなトーンにしてください。

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
        return {"title": "再試行", "q": "通信エラーが発生しました。", "opts": ["A","B","C"], "ans_idx": 0, "exp": "エラー"}

# ==========================================
# 4. アプリ画面
# ==========================================

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

if 'trigger_sound' in st.session_state:
    play_sound(st.session_state.trigger_sound)
    del st.session_state.trigger_sound

# --- スタート画面 ---
if not st.session_state.game:
    st.title("🥋 若手営業のための思考道場")
    st.caption("現場で役立つ論理的思考を身につけよう！")
    
    st.info("""
    **【修業内容】 全5問**
    1〜3年目の若手社員が直面する課題をテーマにしています。
    - **第1〜3問 (MECE)**: 情報を整理し、漏れなく考える力
    - **第4〜5問 (フェルミ推定)**: 根拠を持って数字を予測する力
    """)
    if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("先輩が課題を準備しています..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

# --- クイズ画面 ---
else:
    if st.session_state.idx >= 5:
        if 'played_final' not in st.session_state:
            st.session_state.trigger_sound = "result.wav"
            st.session_state.played_final = True
            st.rerun()

        st.balloons()
        st.title("🏁 修業完了")
        score = st.session_state.score
        st.header(f"今回の評価: {score} / 5")
        
        if score == 5: st.success("【完璧】 素晴らしい！即戦力の論理思考の持ち主です。")
        elif score >= 3: st.info("【合格】 基礎は身についています。自信を持って現場へ！")
        elif score >= 1: st.warning("【見習い】 伸びしろがあります。一つずつ整理する癖をつけましょう。")
        else: st.error("【要再試行】 焦らず、まずは身近な物の整理から始めてみましょう。")

        if st.button("道場の入り口に戻る", use_container_width=True):
            if 'played_final' in st.session_state: del st.session_state.played_final
            st.session_state.game = False
            st.rerun()

    else:
        q = st.session_state.q
        labels = ["🟢 MECE(日常)", "🟡 MECE(業務)", "🔴 MECE(営業)", "🟡 フェルミ(日常)", "🔴 フェルミ(営業)"]
        st.subheader(f"第{st.session_state.idx + 1}問：{labels[st.session_state.idx]}")
        st.info(f"**{q['title']}**\n\n{q['q']}")
        
        if st.session_state.ans == False:
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
        
        else:
            if st.session_state.last_res: st.success("⭕ 正解！その調子です！")
            else: st.error(f"❌ 残念... 正解は「{q['opts'][q['ans_idx']]}」")
            st.markdown(f"**【先輩のアドバイス】**\n{q['exp']}")
            
            if st.button("次の課題へ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner("次の課題を準備中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()
