import streamlit as st
import google.generativeai as genai
import json

# --- 1. API設定 ---
def init_gemini():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets設定エラー: 'GEMINI_API_KEY' がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 最も安定している Flash モデルを優先的に使用
    try:
        return genai.GenerativeModel("gemini-1.5-flash")
    except:
        # FlashがだめならPro、それもだめなら自動探索
        try:
            return genai.GenerativeModel("gemini-1.5-pro")
        except:
            models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = models[0] if models else None
            return genai.GenerativeModel(target)

model = init_gemini()

# --- 2. 問題生成関数（日常→実戦ルート） ---
def generate_quiz(idx):
    # 段階的な難易度設定
    if idx == 0:
        cat, level, scene = "MECE", "初級(日常)", "日常生活（旅行の準備、冷蔵庫の整理、家事など）"
    elif idx == 1:
        cat, level, scene = "MECE", "中級(業務)", "一般的なオフィス業務（会議準備、タスク整理）"
    elif idx == 2:
        cat, level, scene = "MECE", "上級(営業実戦)", "営業現場（顧客の潜在ニーズ分析、提案書の構成）"
    elif idx == 3:
        cat, level, scene = "フェルミ推定", "初級(日常)", "身近な数字（コンビニの売上、日本にある電柱の数など）"
    else:
        cat, level, scene = "フェルミ推定", "上級(営業実戦)", "B2B営業（顧客の年間予算、ターゲット市場規模の算出）"

    # シンプルで頑丈なプロンプト
    prompt = f"""
    あなたは若手営業（1〜3年目）のメンターです。
    以下の条件でクイズを1問作成してください。

    【テーマ】{cat}
    【レベル】{level}
    【シーン】{scene}

    指示:
    - 3択問題。
    - 解説は「営業現場での活かし方」を含めること。
    - 以下のJSON形式(日本語)のみを出力すること。

    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "ans_idx": 0,
        "exp": "解説"
    }}
    ※ ans_idx は正解の配列インデックス(0, 1, 2 の数値)
    """

    try:
        # 余計な設定を排除し、シンプルに投げる
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        # エラー時は詳細を表示してデバッグしやすくする
        return {
            "title": "通信エラー", 
            "q": f"エラーが発生しました: {str(e)}", 
            "opts": ["再試行"], 
            "ans_idx": 0, 
            "exp": "「再試行」ボタンを押してください。"
        }

# --- 3. メイン画面 ---
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    st.markdown("### 日常から実戦へ。論理の「型」を習得せよ。")
    st.info("""
    **【特訓カリキュラム】**
    1. **日常MECE**: 身近な事象を構造化
    2. **業務MECE**: 仕事のタスクを整理
    3. **営業MECE**: 顧客課題を深掘り
    4. **日常フェルミ**: 身近な数値を推計
    5. **営業フェルミ**: 市場・予算を試算
    """)
    
    if st.button("▶ 入門する（特訓開始）", type="primary", use_container_width=True):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("第一の課題を作成中..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

else:
