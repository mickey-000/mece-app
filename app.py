import streamlit as st
import google.generativeai as genai
import json
import time

# ==========================================
# 1. Gemini API設定 (最強の接続ロジック)
# ==========================================
def init_gemini():
    # Secretsのチェック
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("【エラー】Secretsに 'GEMINI_API_KEY' が設定されていません。")
        st.stop()
    
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # 利用可能なモデルを自動探索（Pro版/無料版問わず接続するため）
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 優先順位: Flash(高速) -> Pro(高性能) -> 無印
        target = None
        priority_list = [
            "models/gemini-1.5-flash", 
            "models/gemini-1.5-pro", 
            "models/gemini-1.5-flash-001",
            "models/gemini-pro"
        ]
        
        # 優先リストの中から、実際に使えるものを探す
        for p in priority_list:
            if p in models:
                target = p
                break
        
        # 見つからなければリストの先頭を使う
        if not target and models:
            target = models[0]
            
        if not target:
            raise Exception("利用可能なモデルが見つかりませんでした。")
            
        return genai.GenerativeModel(target), target
    except Exception as e:
        st.error(f"AIモデルの接続に失敗しました: {e}")
        st.stop()

# アプリ起動時にモデルを初期化
model, model_name_used = init_gemini()

# ==========================================
# 2. 問題生成ロジック (AIへの指示)
# ==========================================
def generate_quiz(category_type):
    if category_type == "MECE":
        theme = "ビジネス課題におけるMECE（漏れなくダブりなく）の構造化"
        instruction = "3つの選択肢のうち、1つだけが『完全にMECE』な切り口であること。"
    else:
        theme = "フェルミ推定（未知の数値を論理的に導く計算式）"
        instruction = "3つの選択肢のうち、1つだけが『最も筋の良い因数分解（計算式）』であること。"

    prompt = f"""
    あなたは戦略コンサルタントを育成する『道場の師範』です。
    実務3年目レベルの難易度で、以下のテーマの問題
