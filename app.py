import streamlit as st
import google.generativeai as genai
import json

# --- 1. API設定（エラー自動回避機能付き） ---
def init_gemini():
    # Secretsのチェック
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("設定エラー: Secretsに GEMINI_API_KEY がありません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        # 今使えるモデルをリストアップして、最適なものを自動で選ぶ
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順位: 1.5 Flash (高速・安定) -> 1.5 Pro -> Pro (旧型)
        priority = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
        
        target_model = None
        for p in priority:
            if p in available_models:
                target_model = p
                break
        
        # 見つからなければ、とにかく使える最初のモデルを選ぶ
        if not target_model and available_models:
            target_model = available_models[0]
            
        if not target_model:
            st.error("利用可能なAIモデルが見つかりませんでした。APIキーを確認してください。")
            st.stop()
            
        return genai.GenerativeModel(target_model)

    except Exception as e:
        st.error(f"接続エラーが発生しました: {e}")
        st.stop()

# モデルの初期化
model = init_gemini()

# --- 2. 問題生成関数（日常→実戦ルート） ---
def generate_quiz(idx):
    # 難易度とシーンの分岐
    if idx == 0:
        cat, level, scene = "MECE", "初級(日常)", "旅行の準備、冷蔵庫の整理、家事の分担"
    elif idx == 1:
        cat, level, scene = "MECE", "中級(業務)", "会議の準備、タスクの優先順位付け"
    elif idx == 2:
        cat, level, scene = "MECE", "上級(営業実戦)", "顧客の潜在ニーズ分析、提案書の構成"
    elif idx == 3:
        cat, level, scene = "フェルミ推定", "初級(日常)", "日本にある電柱の数、コンビニの売上"
    else:
        cat, level, scene = "フェルミ推定", "上級(営業実戦)", "顧客の年間予算規模、ターゲット市場の規模"

    # AIへの指示（プロンプト）
    prompt = f"""
    あなたは若手営業（1〜3年目）のメンターです。
    以下の条件でクイズを1問作成してください。

    【テーマ】{cat}
    【レベル】{level}
    【シーン】{scene}

    以下のJSON形式(日本語)のみを出力してください:
    {{
        "title": "タイトル",
        "q": "問題文",
        "opts": ["選択肢A", "選択肢B", "選択肢C"],
        "ans_idx": 0,
        "exp": "解説（営業での活かし方）"
    }}
    ※ ans_idx は正解の番号(0, 1, 2)です。
    """

    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        # 万が一のエラー時のバックアップ問題
        return {
            "title": "通信エラー", 
            "q": "問題の生成に失敗しました。再試行してください。", 
            "opts": ["再試行"], 
            "ans
