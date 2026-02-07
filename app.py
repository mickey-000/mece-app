import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="API接続テスト", page_icon="🔧")

st.title("🔧 APIキー診断モード")

# 1. Secretsの読み込み確認
if "GEMINI_API_KEY" not in st.secrets:
    st.error("❌ 【原因1】Secretsの設定が見つかりません。")
    st.info("StreamlitのSettings > Secrets に `GEMINI_API_KEY = ...` があるか確認してください。")
    st.stop()

api_key = st.secrets["GEMINI_API_KEY"]

# キーの長さをチェック（極端に短い場合はコピペミスの可能性）
if len(api_key) < 30:
    st.error(f"❌ 【原因2】APIキーが短すぎます（現在{len(api_key)}文字）。")
    st.write(f"読み込んでいるキー: `{api_key}`")
    st.info("コピーする際に、文字列が途切れていないか確認してください。")
    st.stop()

# キーの前後に余計な空白がないかチェック
if api_key.strip() != api_key:
    st.warning("⚠️ キーの前後に「スペース」や「改行」が含まれています。自動で削除して接続を試みます...")
    api_key = api_key.strip()

st.success(f"✅ Secretsの読み込み成功（キーの末尾: ...{api_key[-5:]}）")

# 2. 実際の接続テスト
st.write("---")
st.write("📡 Googleへの接続テスト中...")

genai.configure(api_key=api_key)

# 最も安定しているモデルでテスト
target_model = "gemini-1.5-flash"

try:
    model = genai.GenerativeModel(target_model)
    response = model.generate_content("Hello, can you hear me?", request_options={"timeout": 10})
    
    st.balloons()
    st.success("🎉 【接続成功】おめでとうございます！APIは正常です。")
    st.write(f"**AIからの返事:** {response.text}")
    st.write("---")
    st.info("この画面が出たら、コードを元の「ゲーム用コード」に戻してOKです！")

except Exception as e:
    st.error("❌ 【接続失敗】Googleからエラーが返ってきました。")
    st.write("以下のエラーメッセージを確認してください：")
    
    # エラー内容を詳しく表示
    error_msg = str(e)
    st.code(error_msg, language="text")

    st.write("---")
    st.subheader("考えられる原因と対策")
    
    if "403" in error_msg or "API key not valid" in error_msg:
        st.write("🔴 **原因：APIキーが無効です**")
        st.write("対策：Google AI Studioで新しいキーを発行し、Secretsに貼り直してください。")
    elif "404" in error_msg:
        st.write("🔴 **原因：モデルが見つかりません**")
        st.write("対策：使用するモデル名が変更された可能性があります。")
    elif "User location is not supported" in error_msg:
        st.write("🔴 **原因：地域制限**")
        st.write("対策：現在接続しているネットワークの場所（VPNなど）が制限対象かもしれません。")
    else:
        st.write("🔴 **原因：その他**")
        st.write("対策：上記のエラーメッセージをコピーして、Gemini（チャット）に相談してください。")
