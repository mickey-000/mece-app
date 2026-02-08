import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 全モデル検索 & 接続ロジック
# ==========================================
def init_gemini():
    # APIキーの確認
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("エラー: Secretsに GEMINI_API_KEY がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # 【重要】アカウントで使えるモデルを全てリストアップする
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not all_models:
            st.error("利用可能なモデルが1つも見つかりませんでした。APIキーまたはプランを確認してください。")
            st.stop()

        # 優先順位: Flash -> Pro -> その他
        # ※名前が少し違っても部分一致でヒットさせる
        target_model = None
        for keyword in ["flash", "1.5-pro", "gemini-pro"]:
            for m in all_models:
                if keyword in m:
                    target_model = m
                    break
            if target_model: break
        
        # 優先モデルがなければ、リストの先頭（どれでもいいから動くやつ）を使う
        if not target_model:
            target_model = all_models[0]
            
        return genai.GenerativeModel(target_model), target_model, all_models

    except Exception as e:
        st.error(f"API接続時の致命的エラー: {e}")
        st.stop()

# モデル初期化
model, model_name_used, available_list = init_gemini()

# ==========================================
# 2. 問題生成 (エラーを隠さず表示する)
# ==========================================
def generate_quiz(idx):
    scenes = [
        ("MECE", "初級(日常)", "旅行の準備、冷蔵庫の整理"),
        ("MECE", "中級(業務)", "会議アジェンダ、タスク整理"),
        ("MECE", "上級(営業)", "顧客ヒアリング整理、提案構成"),
        ("フェルミ", "初級", "コンビニの売上、電柱の数"),
        ("フェルミ", "上級", "市場規模算出、顧客予算")
    ]
    cat, level, scene = scenes[idx]

    prompt = f"""
    あなたは営業マネージャーです。若手向けに「{cat}」の問題を1問作成せよ。
    レベル:{level} シーン:{scene}
    出力は以下のJSON形式(日本語)のみ:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["A", "B", "C"],
        "ans_idx": 0,
        "exp": "解説"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        # 【ここが修正点】エラーを隠さず、そのまま画面に出す
        error_msg = str(e)
        return {
            "title": "⚠️ エラー発生", 
            "q": f"システムエラーが発生しました。\n以下の英語メッセージを確認してください:\n\n{error_msg}", 
            "opts": ["再試行"], 
            "ans_idx": 0, 
            "exp": "APIキーの制限、またはモデルのアクセス権限に問題がある可能性があります。"
        }

# ==========================================
# 3. アプリ画面
# ==========================================
st.set_page_config(page_title="営業思考道場", page_icon="🥋")

if 'game' not in st.session_state: st.session_state.game = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'ans' not in st.session_state: st.session_state.ans = False

if not st.session_state.game:
    st.title("🥋 営業×コンサル思考道場")
    
    # デバッグ情報：どのモデルにつながったか表示
    st.success(f"接続成功: {model_name_used.replace('models/', '')}")
    with st.expander("詳細: 検出された全モデルリスト"):
        st.write(available_list)
        
    st.info("日常の整理から営業実戦まで。全5問の特訓。")
    
    if st.button("▶ 特訓を開始する", type="primary", use_container_width=True):
        st.session_state.game = True
        st.session_state.score = 0
        st.session_state.idx = 0
        st.session_state.ans = False
        with st.spinner("課題を作成中..."):
            st.session_state.q = generate_quiz(0)
        st.rerun()

else:
    if st.session_state.idx >= 5:
        st.balloons()
        st.title("🏁 特訓完了")
        st.header(f"結果: {st.session_state.score} / 5")
        if st.button("戻る", use_container_width=True):
            st.session_state.game = False
            st.rerun()
    else:
        q = st.session_state.q
        
        # エラー時は赤く表示
        if "エラー" in q['title']:
            st.error(q['title'])
            st.warning(q['q']) # エラー詳細を表示
        else:
            labels = ["🟢 初級", "🟡 中級", "🔴 上級", "🟡 推定", "🔴 推定(実戦)"]
            st.subheader(f"第{st.session_state.idx + 1}問：{labels[st.session_state.idx]}")
            st.info(f"**{q['title']}**\n\n{q['q']}")
        
        if not st.session_state.ans:
            for i, opt in enumerate(q['opts']):
                if st.button(opt, key=f"btn_{st.session_state.idx}_{i}", use_container_width=True):
                    st.session_state.ans = True
                    if i == q['ans_idx']:
                        st.session_state.last_res = True
                        st.session_state.score += 1
                    else:
                        st.session_state.last_res = False
                    st.rerun()
        else:
            if st.session_state.last_res: st.success("⭕ 正解")
            else: st.error(f"❌ 不正解... 正解: {q['opts'][q['ans_idx']]}")
            st.markdown(f"**【解説】**\n{q['exp']}")
            if st.button("次へ ➔", type="primary", use_container_width=True):
                st.session_state.idx += 1
                st.session_state.ans = False
                if st.session_state.idx < 5:
                    with st.spinner("生成中..."):
                        st.session_state.q = generate_quiz(st.session_state.idx)
                st.rerun()
# === コピー終了 ===
