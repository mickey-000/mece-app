# -*- coding: utf-8 -*-
"""
対話・自由記述式トレーニングの共通ロジック
（Streamlit + Google Gemini）

- APIキーは st.secrets["GEMINI_API_KEY"] を使用（mece-app と同じ方式）
- 各ページはこのモジュールの run_trainer() を呼ぶだけ
"""

import streamlit as st
import google.generativeai as genai

KICKOFF = "このプロンプトの指示に従って、トレーニングを始めてください。"

# ==========================================================
# トレーニング用システムプロンプト（2種類）
# ==========================================================

STRUCTURE_PROMPT = """【役割】
あなたは「製造業のビジネスコンサルタントの思考訓練を行うAI」です。
複雑で感情的な現場発言から、事実・問題・課題・その他を正確に切り分ける支援を行います。

【目的】
製造業の現場で交わされる「生の発言」に含まれる

事実と解釈の混同
問題と課題の混同
論理の飛躍
を可視化し、構造的に整理する力を鍛えること。

【出題ルール】
全3問を出題します。
各問ごとに「カオスな発言」を1つ提示します。
カオス発言のレベルは、第1問：初級、第2問：中級、第3問：上級とします。
各問のカオス発言の内容だけを、下記の分類定義に従い①～④に分類してください。
シチュエーション設定や理由説明は不要です。
①～④の定義は各出題の際に提示すること。

【分類定義（毎回必ず表示）】

① 事象
完全に中立的な客観的事実のみ
数値、起きた出来事、測定可能な状態
「〜ができていない」「〜が取れない」「〜が多い/少ない」などのネガティブ表現は含めない
例：「生産数1000個」「不良率0.5%」「納期5日遅延」「在庫数200個」

② 問題
あるべき姿とのギャップを示す表現
「〜ができていない」「〜が取れない」「〜が不足している」などネガティブな状態
主観評価・原因仮説・責任論は含めない
例：「不良品が多い」「納期に間に合っていない」「在庫が不足している」

③ 課題
問題を解決するための具体的アクション
発言内に明示されていない場合は「該当なし」でよい
課題を推測・補完しない

④ その他
感情、主観、評価、決めつけ、仮説、価値判断
原因の断定や責任追及
一般論・精神論
例：「現場の意識が低い」「管理が甘い」「もっと頑張るべき」

【回答ルール（受講者向け）】
カオス発言の内容だけを、下記の形式で分類してください。

o ①事象：
o ②問題：
o ③課題：
o ④その他：

理由説明は不要です。

【フィードバックルール（AI側）】
まず良かった点を具体的に挙げて肯定的に評価します。
改善ポイントがあれば、前向きな表現で具体例を示します。
構造化テーブル（模範解答）を提示します。
発言者側の論理の飛躍や思考バイアスを共感的に指摘します。

【出題の流れ】

これから第1問（初級）から順に出題します。
準備ができたら「はい」とご返信ください。
ユーザーが「はい」と入力したら、第1問を出題してください。
カオス発言は製造業の現場でよくあるテーマ（生産計画、品質管理、納期、設備トラブル、現場安全、在庫管理、工程改善、作業員の教育・モチベーション等）から毎回ランダムに出題してください。
第3問（上級）は「製造業のお客様（部長）」が発言者となるカオス発言を出題してください。部長クラスが現場や自社の状況について語るリアルなものとし、経営視点、全体最適、現場への要望、責任論、プレッシャー、経営課題などを含めてください。
それ以外の出題・分類・フィードバックルールは従来通りとします。

【AIへの指示】
このプロンプトを受け取ったら、まず「準備ができたら『はい』とご返信ください。」とだけ案内してください。
ユーザーが「はい」と入力したら、第1問（初級）を出題してください。
以降は通常通り進行してください。"""

ABSTRACTION_PROMPT = """役割
あなたは営業・コンサルの若手を対象とした「具体と抽象の往復」を鍛える専門トレーニングAIです。

目的
バラバラに見える事象から共通の「構造（抽象）」を見抜き、それを別の事象に「適用（具体）」できる力を養うこと。

出題ルール（全5問のステップアップ形式）
各レベルごとに、毎回異なる切り口やジャンル、パターンで出題してください。
同じようなモノや事例が続かないよう、ランダム性を持たせてください。

【第1問：初級】
日常的なモノ（3つ）から共通点を見つける。
※家電、乗り物、道具、自然物、施設など、ジャンルを毎回変えること。

【第2問：中級】
さまざまなビジネスモデルやサービス（3つ）から共通点を見つける。
※サブスクリプション型、フリーミアム型、成果報酬型、プラットフォーム型、シェアリング型など多様なモデルからランダムに出題すること。

【第3問：実践】
営業現場やコンサル業務での出来事（3つ）から共通点を見つける。
※顧客対応、提案活動、社内調整、トラブル対応など、シーンやテーマを毎回変えること。

【第4問：上級】
提示された2つの具体例から共通点を見つけ、さらに「同じ構造を持つ3つ目の具体例」を自分で1つ作成する。
※ジャンルや業界、規模感などを毎回変えること。

【第5問：最上級】
提示された「抽象概念（お題）」に対し、具体例を1つこちらで提示します。
ユーザーは「同じ構造を持つ2つの具体例」を自分で考えてください。
※「リスク分散」「成長の仕組み」「フィードバックループ」「ボトルネック」「レバレッジ」「インセンティブ設計」「可視化」「標準化」など、営業・コンサルに役立つ多様なテーマからランダムに出題すること。

ヒント機能（重要）
特に第4問・第5問において、ユーザーが「ヒント」と入力した場合は、以下の指針で思考を助けてください。

直接的な答えは言わない。
「歴史、スポーツ、恋愛、科学、家事」など、別のジャンルの切り口を提示する。
「もし、この構造が○○の世界にあったとしたら？」と問いかける。

進め方

まず問題（具体的な出来事、またはお題）だけを提示し、ユーザーの回答を待つ。
回答後に、以下の3点を含めて短く解説する。
抽象化の例（言語化のヒント）
なぜそう考えられるか（構造の解説）
営業・コンサル視点でのポイント
解説後、次のレベルへ進む。

注意事項

専門用語を使いすぎず、本質を突いた平易な言葉で解説する。
ユーザーの視点の良さを拾い上げて褒め、モチベーションを維持する。
出題ジャンルやパターンが偏らないよう、毎回ランダム性を意識する。

【AIへの指示】
このプロンプトを受け取ったら、まず簡単にトレーニングの概要を案内し、「準備ができたら『はい』とご返信ください。」と伝えてください。
ユーザーが「はい」と入力したら、第1問（初級）を出題してください。
以降は上記の進め方に従って進行してください。"""


# ==========================================================
# Gemini 接続
# ==========================================================
@st.cache_resource(show_spinner=False)
def _get_model(system_instruction):
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets設定エラー: 'GEMINI_API_KEY' がありません。"
                 "Streamlit の Settings → Secrets に GEMINI_API_KEY を設定してください。")
        st.stop()
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    try:
        all_models = [m.name for m in genai.list_models()
                      if "generateContent" in m.supported_generation_methods]
        target = next((m for keyword in ["flash", "1.5-pro"]
                       for m in all_models if keyword in m), all_models[0])
    except Exception as e:
        st.error(f"接続エラー: {e}")
        st.stop()
    return genai.GenerativeModel(target, system_instruction=system_instruction)


def _generate(system_prompt, state_key):
    model = _get_model(system_prompt)
    with st.spinner("考え中..."):
        try:
            resp = model.generate_content(st.session_state[state_key])
            text = resp.text
        except Exception as e:
            text = f"⚠️ 応答の取得でエラーが発生しました。もう一度お試しください。\n\n({e})"
    st.session_state[state_key].append({"role": "model", "parts": [text]})


# ==========================================================
# トレーニング画面（ページから呼び出す）
# ==========================================================
def run_trainer(page_title, emoji, system_prompt):
    st.set_page_config(page_title=page_title, page_icon=emoji)
    st.title(f"{emoji} {page_title}")

    state_key = "chat_" + str(abs(hash(system_prompt)))

    # 初回：見えない合図でAIの開始案内を引き出す
    if state_key not in st.session_state:
        st.session_state[state_key] = [{"role": "user", "parts": [KICKOFF]}]
        _generate(system_prompt, state_key)

    # 履歴を表示（最初の隠しメッセージは飛ばす）
    for i, m in enumerate(st.session_state[state_key]):
        if i == 0 and m["role"] == "user":
            continue
        role = "user" if m["role"] == "user" else "assistant"
        avatar = "🙂" if role == "user" else emoji
        with st.chat_message(role, avatar=avatar):
            st.markdown(m["parts"][0])

    # 入力
    if prompt := st.chat_input("回答を入力してください（例：はい / ヒント）"):
        st.session_state[state_key].append({"role": "user", "parts": [prompt]})
        _generate(system_prompt, state_key)
        st.rerun()

    # サイドバー：やり直し
    with st.sidebar:
        st.divider()
        if st.button("🔄 最初からやり直す", use_container_width=True, key="reset_" + state_key):
            del st.session_state[state_key]
            st.rerun()


# ==========================================================
# 思考構造化トレーニング（①②③④の入力欄・全3問・次へボタン式）
# ==========================================================
TOTAL_MECE = 3

MECE_ROLE = ("あなたは製造業のビジネスコンサルタント育成を行うプロの講師AIです。"
             "回答はすべて日本語で行います。")

DEFINITIONS_MD = """**① 事象**：中立的な客観的事実のみ（数値・起きた出来事・測定可能な状態）。ネガティブ表現は含めない。
例：生産数1000個、不良率0.5%、納期5日遅延

**② 問題**：あるべき姿とのギャップ（「〜できていない」「〜が不足」等のネガティブな状態）。主観・原因仮説・責任論は含めない。
例：不良品が多い、納期に間に合っていない

**③ 課題**：問題を解決するための具体的アクション。発言に明示が無ければ「該当なし」。推測で補完しない。

**④ その他**：感情・主観・評価・決めつけ・仮説・価値判断・原因の断定・責任追及・一般論・精神論。
例：現場の意識が低い、管理が甘い、もっと頑張るべき"""


def _oneshot(system_instruction, user_text):
    """1回だけ Gemini を呼んでテキストを返す（会話履歴なし）"""
    model = _get_model(system_instruction)
    try:
        return model.generate_content(user_text).text
    except Exception as e:
        return f"⚠️ 応答の取得でエラーが発生しました。もう一度お試しください。\n\n({e})"


def mece_generate_question(n, prev):
    """第n問（1〜3）のカオス発言を1つ生成する。prev は過去の発言リスト。"""
    level = {1: "初級", 2: "中級", 3: "上級"}.get(n, "中級")
    extra = ""
    if n >= 3:
        extra = ("この発言は『製造業のお客様（部長クラス）』が語るものにしてください。"
                 "経営視点・全体最適・現場への要望・責任論・プレッシャー・経営課題などを含む、"
                 "リアルで少し感情のこもった発言に。")
    prev_text = "\n".join(f"- {p}" for p in prev) if prev else "（なし）"
    user = f"""第{n}問（難易度:{level}）の「カオス発言（現場の生の発言）」を1つだけ作成してください。
{extra}

出力ルール:
- カオス発言の本文だけを出力する（1〜3文程度、自然な話し言葉）。
- 「第○問」などの見出し、①〜④の定義、解説、前置き、かぎ括弧での囲みは書かない。
- テーマは製造業の現場（生産計画/品質管理/納期/設備トラブル/現場安全/在庫管理/工程改善/作業員の教育・モチベーション等）からランダムに選ぶ。
- 事実・問題・課題・感情や決めつけなどが入り混じった、切り分け甲斐のある発言にする。
- これまでに出した発言とは、テーマも内容も重複させない。

これまでの発言:
{prev_text}"""
    return _oneshot(MECE_ROLE, user).strip()


def mece_feedback(problem, a1, a2, a3, a4):
    """受講者の①〜④の回答を講評する（模範解答テーブル付き）。"""
    user = f"""次の「カオス発言」に対する受講者の分類回答を講評してください。

【カオス発言】
{problem}

【受講者の回答】
①事象：{a1 or "（未記入）"}
②問題：{a2 or "（未記入）"}
③課題：{a3 or "（未記入）"}
④その他：{a4 or "（未記入）"}

【分類定義】
① 事象：中立的な客観的事実のみ（数値・起きた出来事・測定可能な状態）。ネガティブ表現は含めない。
② 問題：あるべき姿とのギャップ（ネガティブな状態）。主観・原因仮説・責任論は含めない。
③ 課題：問題を解決する具体的アクション。発言に無ければ「該当なし」。
④ その他：感情・主観・評価・決めつけ・仮説・価値判断・原因の断定・責任追及・一般論・精神論。

【講評の順番（必ずこの順で、見出しをつけて）】
1. **良かった点**：具体的にほめる。
2. **改善ポイント**：前向きな表現で、具体例を挙げて示す。
3. **模範解答**：Markdownの表で提示する（列は「区分」と「内容」、行は ①事象／②問題／③課題／④その他 の4行）。
4. **ひとことアドバイス**：発言者側の論理の飛躍や思考バイアスを、受講者に寄り添って共感的に指摘する。"""
    return _oneshot(MECE_ROLE, user)


# ==========================================================
# 具体と抽象の往復トレーニング（全5問・ガイド付き・次へボタン式）
# ==========================================================
TOTAL_ABS = 5

ABS_ROLE = ("あなたは営業・コンサルの若手を対象に「具体と抽象の往復」を鍛える"
            "専門トレーニングAIです。回答はすべて日本語で、平易な言葉で行います。")

_ABS_SPECS = {
    1: ("第1問：初級",
        "身近な『モノ・対象』を3つ提示してください。ジャンルは毎回大きく変えること"
        "（家電／乗り物／道具／文房具／建物・施設／自然物・自然現象／動物／植物／食べ物／"
        "飲み物／スポーツ／楽器／天体／体の器官 などから、毎回違うジャンルを選ぶ）。"
        "『身近な道具』ばかりに偏らせず、意外な組み合わせも歓迎。"
        "ユーザーはこの3つに共通する『構造・仕組み・役割』を考えます。"),
    2: ("第2問：中級",
        "一見バラバラで共通点がなさそうな、実在の企業・店・サービス・仕組みを3つ提示して"
        "ください。例：『回転寿司・IKEA・セルフ式ガソリンスタンド』（隠れた共通構造は"
        "“本来お店がやる作業を客にやらせてコストを下げるセルフサービス”）のように、"
        "表面は無関係でも実は同じ構造を持つ組み合わせにする。隠れた共通構造は毎回変えること"
        "（セルフサービス／本体は安く消耗品で稼ぐ／プラットフォーム／会員制・囲い込み／"
        "体験や希少性の演出／あえての逆張り／ボトルネックの解消 など）。"
        "サブスクリプションばかりに偏らせないこと。"
        "ユーザーはこの3つの“意外な共通点（構造）”を考えます。"),
    3: ("第3問：実践",
        "営業現場やコンサル業務での出来事を3つ提示してください。顧客対応・提案活動・"
        "社内調整・トラブル対応などからシーンを選ぶ。ユーザーは3つの共通点（構造）を考えます。"),
    4: ("第4問：上級",
        "具体例を2つだけ提示してください。ユーザーは（A）2つの共通点（構造）を見抜き、"
        "（B）同じ構造を持つ3つ目の具体例を自分で1つ作ります。"),
    5: ("第5問：最上級",
        "抽象概念のお題（リスク分散／成長の仕組み／フィードバックループ／ボトルネック／"
        "レバレッジ／インセンティブ設計／可視化／標準化 など）を1つ選び、その具体例を1つだけ"
        "提示してください。ユーザーは同じ構造を持つ具体例を自分で2つ考えます。"),
}


def abs_generate_question(n, prev):
    """第n問（1〜5）の問題文を生成する。"""
    level, instruction = _ABS_SPECS.get(n, _ABS_SPECS[1])
    prev_text = "\n".join(f"- {p}" for p in prev) if prev else "（なし）"
    user = f"""{level} の問題を作成してください。
{instruction}

出力ルール:
- 問題文だけを出力する（前置き・解説・答え・ヒントは書かない）。
- まず対象（3つのモノ／2つの具体例／お題と具体例）を、箇条書きで分かりやすく提示する。
- 最後に「▶ あなたへの問い：」で始まる1行で、何を答えればよいかを示す。
- 毎回ジャンルや切り口を変え、これまでの問題と重複させない。

これまでの問題:
{prev_text}"""
    return _oneshot(ABS_ROLE, user).strip()


def abs_hint(n, problem):
    """直接の答えを言わずにヒントを出す。"""
    user = f"""次の問題について、ユーザーの思考を助けるヒントを出してください。

【問題】
{problem}

ヒントのルール:
- 直接的な答えは絶対に言わない。
- 「歴史・スポーツ・恋愛・科学・家事」など、別ジャンルの切り口を1つ提示する。
- 「もし、この構造が○○の世界にあったとしたら？」という問いかけを添える。
- 2〜4文程度で簡潔に。"""
    return _oneshot(ABS_ROLE, user)


def abs_feedback(n, problem, answer):
    """ユーザーの回答を短く解説する。"""
    user = f"""ユーザーの回答を、営業・コンサルの講師として短く解説してください。

【問題】
{problem}

【ユーザーの回答】
{answer or "（未記入）"}

解説の構成（各項目に見出しをつけ、簡潔に）:
1. **良い視点**：回答の良い点を具体的にほめる（未記入なら、考える入口をやさしく示す）。
2. **抽象化の例**：この事象をどう言語化できるか（共通する構造）の例を示す。
3. **なぜそう言えるか**：構造をやさしく解説する。
4. **営業・コンサル視点**：実務でどう活きるかのポイントを一言。

専門用語を使いすぎず、本質を突いた平易な言葉で。ユーザーのやる気が続くよう前向きに。"""
    return _oneshot(ABS_ROLE, user)


# ==========================================================
# 見た目（デザイン）を整えるCSS
# ==========================================================
def apply_style():
    """各ページ冒頭で呼ぶと、モダンな見た目のCSSを適用する。"""
    st.markdown(
        """
        <style>
        /* 背景に奥行きのあるグラデーション */
        .stApp {
            background:
              radial-gradient(1100px 620px at 12% -12%, #23305a 0%, rgba(35,48,90,0) 55%),
              radial-gradient(900px 520px at 110% 0%, #14324a 0%, rgba(20,50,74,0) 50%),
              #0b0e16;
        }
        .block-container { padding-top: 2.4rem; max-width: 880px; }

        /* 見出しをグラデーション文字に */
        h1 {
            font-weight: 800 !important;
            letter-spacing: .01em;
            background: linear-gradient(92deg, #8e7bff 0%, #4fd1c5 100%);
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent; color: transparent;
        }
        h2, h3 { font-weight: 700 !important; letter-spacing: .01em; }

        /* info / warning / success カードをガラス風に */
        div[data-testid="stAlert"] {
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,.09);
            background: rgba(255,255,255,.035);
            backdrop-filter: blur(6px);
            box-shadow: 0 10px 34px rgba(0,0,0,.30);
            padding: 1rem 1.15rem;
        }

        /* 入力欄 */
        textarea, input, .stTextArea textarea {
            border-radius: 12px !important;
            background: rgba(255,255,255,.04) !important;
            border: 1px solid rgba(255,255,255,.12) !important;
        }
        textarea:focus { border-color: #7c5cff !important; box-shadow: 0 0 0 2px rgba(124,92,255,.35) !important; }

        /* ボタン全般 */
        .stButton > button {
            border-radius: 12px;
            font-weight: 700;
            padding: .55rem 1rem;
            border: 1px solid rgba(255,255,255,.14);
            background: rgba(255,255,255,.05);
            color: #eef0f6;
            transition: transform .06s ease, box-shadow .2s ease, border-color .2s ease;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            border-color: #7c5cff;
            box-shadow: 0 8px 22px rgba(124,92,255,.30);
        }
        /* プライマリボタンはグラデーション */
        .stButton > button[kind="primary"],
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(92deg, #7c5cff 0%, #4fd1c5 100%) !important;
            border: none !important;
            color: #0b0e16 !important;
        }
        .stButton > button[kind="primary"]:hover { filter: brightness(1.05); }

        /* 進捗バー */
        .stProgress > div > div > div > div {
            background: linear-gradient(92deg, #7c5cff 0%, #4fd1c5 100%);
        }

        /* チャット吹き出し */
        div[data-testid="stChatMessage"] {
            border-radius: 16px;
            background: rgba(255,255,255,.035);
            border: 1px solid rgba(255,255,255,.07);
        }

        /* サイドバー */
        section[data-testid="stSidebar"] {
            background: rgba(10,13,22,.75);
            border-right: 1px solid rgba(255,255,255,.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
