import os
import sys
import json  # ★ Discord送信で必須のライブラリを追加
import time
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from google import genai

# ==========================================
# ⚙️ 設定情報（環境変数より取得）
# ==========================================
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not WEBHOOK_URL or not GEMINI_API_KEY:
    print("❌ エラー: 環境変数 DISCORD_WEBHOOK_URL または GEMINI_API_KEY が設定されていません。")
    sys.exit(1)

# Gemini クライアントの初期化
client = genai.Client(api_key=GEMINI_API_KEY)

# テストモードの切り替え (True: テスト実行 / False: 通常運用)
TEST_MODE = True

# ==========================================
# 📦 対象銘柄リスト
# ==========================================
TICKER_LIST = [
    "7203.T", "6758.T", "6501.T", "6861.T", "8035.T", "6920.T", "9984.T", "8306.T",
    "8058.T", "9983.T", "7974.T", "9101.T", "3382.T", "4502.T", "9432.T"
]

COMPANY_NAMES = {
    "7203.T": "トヨタ自動車", "6758.T": "ソニーグループ", "6501.T": "日立製作所", "6861.T": "キーエンス",
    "8035.T": "東京エレクトロン", "6920.T": "レーザーテック", "9984.T": "ソフトバンクG", "8306.T": "三菱UFJ",
    "8058.T": "三菱商事", "9983.T": "ファーストリテイリング", "7974.T": "任天堂", "9101.T": "日本郵船",
    "3382.T": "セブン&アイHD", "4502.T": "武田薬品", "9432.T": "NTT"
}

def get_company_name(code):
    return COMPANY_NAMES.get(code, code.replace(".T", ""))

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==========================================
# 🔍 1次スクリーニング
# ==========================================
def run_screening():
    print("📈 株価データを取得中...")
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.Timedelta(days=150)
    
    try:
        data = yf.download(TICKER_LIST, start=start_date, end=end_date, progress=False)
        close_df = data['Close']
        volume_df = data['Volume']
    except Exception as e:
        print(f"❌ 株価データ取得エラー: {e}")
        return pd.DataFrame()

    candidates = []

    for code in TICKER_LIST:
        if code not in close_df.columns:
            continue
            
        prices = close_df[code].dropna()
        volumes = volume_df[code].dropna()
        
        if len(prices) < 60:
            continue

        latest_price = prices.iloc[-1]
        rsi = calculate_rsi(prices, 14).iloc[-1]
        sma20 = prices.rolling(20).mean().iloc[-1]
        sma50 = prices.rolling(50).mean().iloc[-1]
        vol_ratio = volumes.iloc[-1] / volumes.rolling(20).mean().iloc[-1]

        detected_system = None

        if TEST_MODE:
            # テストモード判定
            if latest_price >= prices.iloc[-10:].max():
                detected_system = "🚀 新高値ブレイクアウト(テスト)"
            elif rsi <= 55:
                detected_system = "🛡️ 攻めの押し目買い(テスト)"
            else:
                detected_system = "📊 モメンタム判定(テスト)"
        else:
            # 本番用スクリーニング判定
            if latest_price >= prices.iloc[-50:].max() and vol_ratio >= 1.2:
                detected_system = "🚀 新高値ブレイクアウト"
            elif rsi <= 35:
                detected_system = "📉 大暴落パニック検知"
            elif latest_price > sma50 and latest_price <= sma20 and rsi < 55:
                detected_system = "🛡️ 攻めの押し目買い"

        if detected_system:
            volatility = prices.pct_change().std() * np.sqrt(252)
            candidates.append({
                "code": code,
                "name": get_company_name(code),
                "system": detected_system,
                "score": round(100 - (volatility * 100), 2)
            })

    return pd.DataFrame(candidates)

# ==========================================
# 🧠 Gemini API による個別解説
# ==========================================
def fetch_gemini_analysis(code, name, system):
    clean_code = code.replace(".T", "")

    prompt = f"""あなたはプロの証券アナリストです。
以下の日本株銘柄について、テクニカル指標「以外」の観点から、株価が動いている背景をプロの視点で分析してください。

【対象銘柄】
銘柄コード: {clean_code}
企業名: {name}
今回検知されたシグナル: {system}

【出力フォーマット】
以下の3つの項目について、それぞれ1〜2文（簡潔かつ具体的）で記述してください。
■ 企業の特徴と独自の強み:
■ 最近の関連ニュース・市場の流れ（なぜ今お金が集まっているか）:
■ 今後の注目カタリスト（材料・決算期などのリスク）:
"""

    for attempt in range(1, 4):
        try:
            # ★ 安定している gemini-2.5-flash（または gemini-1.5-flash）に変更
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            if response.text:
                return response.text
            else:
                return "⚠️ AIからの回答テキストが空でした。"
        except Exception as e:
            err_str = str(e)
            print(f"⚠️ Gemini API エラー (試行 {attempt}/3): {err_str}")
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                time.sleep(20 * attempt)
            else:
                time.sleep(5)
            
            if attempt == 3:
                return f"⚠️ Gemini API呼び出し失敗 (詳細: {err_str[:150]})"

# ==========================================
# 🕊️ Discord Webhook 送信
# ==========================================
def send_discord_message(content):
    headers = {"Content-Type": "application/json"}
    payload = {"content": content}
    try:
        requests.post(WEBHOOK_URL, data=json.dumps(payload), headers=headers, timeout=10)
    except Exception as e:
        print(f"❌ Discord送信エラー: {e}")

# ==========================================
# 🚀 メイン実行処理
# ==========================================
def main():
    print("🤖 株式自動スクリーニング処理を開始します...")
    df_candidates = run_screening()

    if df_candidates.empty:
        print("ℹ️ 本日基準を満たす銘柄はありませんでした。Discordに通知を送信します。")
        no_signal_msg = (
            "🧭 **【AIアナリスト：日次パトロール報告】**\n\n"
            "💤 本日、スクリーニング条件（新高値ブレイクアウト／大暴落パニック／攻めの押し目買い）を満たす注目銘柄は検出されませんでした。\n"
            "市場の動きを見守り、じっくりチャンスを待ちましょう。"
        )
        send_discord_message(no_signal_msg)
        return

    df_ranked = df_candidates.sort_values(by="score", ascending=False)
    df_top = df_ranked.head(5)

    print(f"🎯 選定されたトップ{len(df_top)}銘柄のAI背景解析を開始します...")

    for rank, (_, row) in enumerate(df_top.iterrows(), 1):
        clean_code = row["code"].replace(".T", "")
        company_name = row["name"]
        detected_system = row["system"]

        if rank > 1:
            time.sleep(12)

        ai_analysis = fetch_gemini_analysis(row["code"], company_name, detected_system)

        report_message = (
            f"🧭 **【AIアナリスト：銘柄深掘りレポート (第{rank}位)】**\n"
            f"📊 **{company_name}** ({clean_code}) ｜ 検出網: {detected_system}\n"
            f"ーーーーーーーーーーーーーーーーーー\n"
            f"{ai_analysis}\n"
            f"ーーーーーーーーーーーーーーーーーー"
        )

        send_discord_message(report_message)
        print(f"✅ 第{rank}位: {company_name} のレポートを送信しました。")

    print("🎉 すべての処理が完了しました！")

if __name__ == "__main__":
    main()
