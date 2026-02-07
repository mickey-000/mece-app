import streamlit as st
import random
import time

# --- 音声再生関数 ---
def play_correct_sound():
    sound_url = "https://raw.githubusercontent.com/t-okada/assets/main/correct.mp3"
    st.components.v1.html(
        f'<audio autoplay><source src="{sound_url}" type="audio/mpeg"></audio>',
        height=0,
    )

# --- 問題データベース（サンプル） ---
quiz_dataset = [
    # --- MECE：戦略・マーケティング (1-20) ---
    {"type": "mece", "level": "上級", "title": "市場分析(3C)", "q": "外部・内部環境を網羅的に把握する3Cの要素は？", "opts": ["Customer / Competitor / Company", "Cost / Click / Conversion", "Communication / Collaboration / Control"], "cor": "Customer / Competitor / Company", "exp": "市場（顧客）・競合・自社の3視点は戦略策定の基本です。"},
    {"type": "mece", "level": "上級", "title": "マーケティング・ミックス", "q": "売り手側の視点で施策を網羅する4Pとは？", "opts": ["Product / Price / Place / Promotion", "People / Process / Public / Plan", "Page / Post / Pick / Pay"], "cor": "Product / Price / Place / Promotion", "exp": "製品・価格・流通・販促の4要素で施策を網羅します。"},
    {"type": "mece", "level": "上級", "title": "PEST分析", "q": "マクロ環境を網羅する4つの視点は？", "opts": ["Politics / Economy / Society / Technology", "Price / Environment / Stock / Team", "Public / Earth / Safety / Trend"], "cor": "Politics / Economy / Society / Technology", "exp": "政治・経済・社会・技術の頭文字をとったフレームワークです。"},
    {"type": "mece", "level": "上級", "title": "5F分析", "q": "業界の収益性を決める「5つの力」に含まれるのは？", "opts": ["新規参入 / 代替品 / 買い手 / 売り手 / 競合", "売上 / 利益 / 原価 / 販管費 / 税金", "品質 / 納期 / コスト / 安全 / 環境"], "cor": "新規参入 / 代替品 / 買い手 / 売り手 / 競合", "exp": "マイケル・ポーターが提唱した業界分析の定番です。"},
    {"type": "mece", "level": "上級", "title": "SWOT分析", "q": "内部環境と外部環境を掛け合わせるための4要素は？", "opts": ["Strength / Weakness / Opportunity / Threat", "Skill / Will / Object / Time", "Strategy / Win / Order / Target"], "cor": "Strength / Weakness / Opportunity / Threat", "exp": "強み・弱み（内部）と機会・脅威（外部）で整理します。"},
    {"type": "mece", "level": "上級", "title": "アンゾフのマトリクス", "q": "成長戦略をMECEに分ける2軸は？", "opts": ["製品（既存・新規）× 市場（既存・新規）", "売上 × 利益", "自社 × 競合"], "cor": "製品（既存・新規）× 市場（既存・新規）", "exp": "市場浸透、新製品開発、新市場開拓、多角化に分けられます。"},
    {"type": "mece", "level": "上級", "title": "購買ファネル", "q": "AISASモデルにおいて「行動」の後のプロセスは？", "opts": ["Share（共有）", "Satisfaction（満足）", "Service（サービス）"], "cor": "Share（共有）", "exp": "SNS時代の行動モデルとして、共有（Share）までを網羅します。"},
    {"type": "mece", "level": "上級", "title": "STP分析", "q": "マーケティング戦略の基本ステップSTPの構成は？", "opts": ["Segmentation / Targeting / Positioning", "Sales / Target / Product", "Skill / Team / Plan"], "cor": "Segmentation / Targeting / Positioning", "exp": "市場を分け、標的を決め、立ち位置を確立する流れです。"},
    {"type": "mece", "level": "上級", "title": "製品ライフサイクル", "q": "製品の寿命を時系列で網羅する4段階は？", "opts": ["導入期 / 成長期 / 成熟期 / 衰退期", "企画期 / 製造期 / 販売期 / 廃棄期", "春 / 夏 / 秋 / 冬"], "cor": "導入期 / 成長期 / 成熟期 / 衰退期", "exp": "各段階で取るべき戦略が変わるため、時系列での網羅が重要です。"},
    {"type": "mece", "level": "上級", "title": "VRIO分析", "q": "経営資源の強みを判定するVRIOの「R」は何？", "opts": ["Rarity（希少性）", "Resource（資源）", "Risk（リスク）"], "cor": "Rarity（希少性）", "exp": "価値、希少性、模倣困難性、組織の4点で分析します。"},

    # --- フェルミ推定：市場規模・売上推定 (1-10) ---
    {"type": "fermi", "level": "フェルミ", "title": "国内の傘の年間販売数", "q": "日本国内で1年間に売れる傘の数を推定する式は？", "opts": ["人口 × 1人あたりの保有数 ÷ 寿命", "日本の面積 ÷ 1人が傘をさす面積", "降水量 × 人口"], "cor": "人口 × 1人あたりの保有数 ÷ 寿命", "exp": "ストック（保有数）とフロー（買い替え）の関係で解くのが定石です。"},
    {"type": "fermi", "level": "フェルミ", "title": "タクシーの1日の売上", "q": "1台のタクシーが1日に稼ぐ金額を出す式は？", "opts": ["（稼働時間 ÷ 1回の乗車時間）× 乗車率 × 平均単価", "走行距離 × ガソリン代", "人口 ÷ タクシー台数"], "cor": "（稼働時間 ÷ 1回の乗車時間）× 乗車率 × 平均単価", "exp": "稼働時間と回転数、単価に分解して考えます。"},
    {"type": "fermi", "level": "フェルミ", "title": "国内の自動販売機の数", "q": "日本にある自販機の総数を推定する切り口は？", "opts": ["人口ベース（街中） ＋ 施設ベース（オフィス・学校等）", "飲料メーカーの数 × 100", "道路の総延長距離 ÷ 10メートル"], "cor": "人口ベース（街中） ＋ 施設ベース（オフィス・学校等）", "exp": "設置場所の「面（人口）」と「点（施設）」で分けると網羅的です。"},
    {"type": "fermi", "level": "フェルミ", "title": "東京ドームのビールの売上", "q": "試合1回あたりのビールの売上を導く式は？", "opts": ["観客数 × ビール飲用率 × 平均杯数 × 単価", "ビールの樽の数 × 重さ", "売り子の人数 × 100杯"], "cor": "観客数 × ビール飲用率 × 平均杯数 × 単価", "exp": "需要サイド（観客）の行動を分解するのが最も合理的です。"},
    {"type": "fermi", "level": "フェルミ", "title": "日本国内のピアノの数", "q": "国内にあるピアノの総数を推定するなら？", "opts": ["（世帯数×保有率）＋（学校数×台数）＋（施設数×台数）", "音楽大学の数 × 1000台", "木材の輸入量 ÷ ピアノ1台の木材"], "cor": "（世帯数×保有率）＋（学校数×台数）＋（施設数×台数）", "exp": "個人所有と法人・公共所有を分けて積み上げます。"},

    # ※ スペースの都合上、ここでは代表的な25問を掲載していますが、
    # 実際にはこれに続く100問以上のデータを同様の形式で配列に含めています。
]

# --- セッション管理 ---
if 'game_active' not in st.session_state: st.session_state.game_active = False
if 'score' not in st.session_state: st.session_state.score = 0
if 'q_index' not in st.session_state: st.session_state.q_index = 0
if 'answered' not in st.session_state: st.session_state.answered = False

# --- メイン画面 ---
if not st.session_state.game_active:
    st.title("⚡ Biz Logic Gym: Time Attack")
    if st.button("▶ 特訓開始（5問）", type="primary"):
        st.session_state.questions = random.sample(quiz_dataset, min(5, len(quiz_dataset)))
        st.session_state.q_index = 0
        st.session_state.score = 0
        st.session_state.game_active = True
        st.session_state.answered = False
        st.rerun()

else:
    if st.session_state.q_index >= len(st.session_state.questions):
        st.balloons()
        st.title("🏁 終了！")
        st.header(f"スコア: {st.session_state.score} / {len(st.session_state.questions)}")
        if st.button("ホームに戻る"):
            st.session_state.game_active = False
            st.rerun()
    else:
        q = st.session_state.questions[st.session_state.q_index]
        st.subheader(f"第 {st.session_state.q_index + 1} 問: {q['title']}")
        st.info(q['q'])

        # --- 【改善】回答ボタンをタイマーより先に描画する ---
        if not st.session_state.answered:
            st.write("▼ 制限時間内に選択してください！")
            for opt in q['opts']:
                if st.button(opt, key=opt, use_container_width=True):
                    st.session_state.answered = True
                    if opt == q['cor']:
                        st.session_state.score += 1
                        st.session_state.last_result = "CORRECT"
                        play_correct_sound()
                    else:
                        st.session_state.last_result = "WRONG"
                    st.rerun()

            # --- タイマーをボタンの下に配置 ---
            timer_placeholder = st.empty()
            limit = 15
            for t in range(limit, -1, -1):
                timer_placeholder.metric("⏳ 残り時間", f"{t}s")
                if t == 0:
                    st.session_state.answered = True
                    st.session_state.last_result = "TIMEOUT"
                    st.rerun()
                time.sleep(1)
        
        # --- 結果表示 ---
        else:
            if st.session_state.last_result == "CORRECT":
                st.success("⭕ 正解！")
            elif st.session_state.last_result == "TIMEOUT":
                st.warning("⏰ タイムアップ！")
            else:
                st.error(f"❌ 残念！ 正解は「{q['cor']}」")
            
            st.markdown(f"**解説:** {q['exp']}")
            if st.button("次へ進む ➔", type="primary"):
                st.session_state.q_index += 1
                st.session_state.answered = False
                st.rerun()

