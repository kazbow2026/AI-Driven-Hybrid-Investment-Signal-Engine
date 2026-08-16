import os
import sys
import json
import time
import requests
import numpy as np
import pandas as pd
import yfinance as yf

# ==========================================
# ⚙️ 設定情報（環境変数より取得）
# ==========================================
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not WEBHOOK_URL or not GEMINI_API_KEY:
    print("❌ エラー: 環境変数 DISCORD_WEBHOOK_URL または GEMINI_API_KEY が設定されていません。")
    sys.exit(1)

# ==========================================
# 📦 対象銘柄リスト
# ==========================================
TICKER_LIST = [
    "7203.T", "7201.T", "7267.T", "7269.T", "6902.T", "7259.T", "7270.T", "5108.T", "7261.T", "6758.T",
    "6501.T", "6503.T", "6752.T", "6645.T", "6762.T", "6506.T", "6861.T", "6981.T", "6954.T", "8035.T",
    "6146.T", "6971.T", "6857.T", "7735.T", "6723.T", "6526.T", "6701.T", "6702.T", "6504.T", "6869.T",
    "6920.T", "6178.T", "7751.T", "7741.T", "6473.T", "6471.T", "6301.T", "6326.T", "6367.T", "6141.T",
    "7011.T", "7012.T", "7013.T", "7272.T", "6273.T", "6586.T", "9432.T", "9433.T", "9984.T", "9434.T",
    "4689.T", "4755.T", "9613.T", "4307.T", "9735.T", "3659.T", "2413.T", "4385.T", "3923.T", "6098.T",
    "8306.T", "8316.T", "8411.T", "8308.T", "8766.T", "8591.T", "8001.T", "8031.T", "8053.T", "8058.T",
    "8002.T", "2768.T", "8015.T", "9843.T", "3038.T", "7532.T", "8267.T", "9983.T", "3382.T", "4502.T",
    "4503.T", "4507.T", "4519.T", "4523.T", "4568.T", "4578.T", "4901.T", "4911.T", "4452.T", "5020.T",
    "1605.T", "9501.T", "9502.T", "9503.T", "5401.T", "5411.T", "5713.T", "2502.T", "2503.T", "2914.T",
    "1801.T", "1802.T", "1803.T", "1812.T", "1925.T", "1928.T", "8801.T", "8802.T", "8830.T", "9020.T",
    "9022.T", "9201.T", "9202.T", "9101.T", "9104.T", "9107.T", "7974.T", "7832.T", "9766.T", "9962.T"
]

COMPANY_NAMES = {
    "7203.T": "トヨタ自動車", "6758.T": "ソニーグループ", "6501.T": "日立製作所", "6861.T": "キーエンス",
    "8035.T": "東京エレクトロン", "6920.T": "レーザーテック", "9984.T": "ソフトバンクG", "8306.T": "三菱UFJ",
    "8058.T": "三菱商事", "9983.T": "ファーストリテイリング", "7974.T": "任天堂", "9101.T": "日本郵船"
}

def get_company_name(code):
    return COMPANY_NAMES.get(code, code.replace(".T", ""))

# ==========================================
# 📊 テクニカル指標計算ヘルパー
# ==========================================
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
    print("📈 株価データを一括取得中...")
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

        # 1. 新高値ブレイクアウト
        if latest_price >= prices.iloc[-50:].max() and vol_ratio >= 1.3:
            detected_system = "🚀 新高値ブレイクアウト"
        # 2. パニック逆張り
        elif rsi <= 32:
            detected_system = "📉 大暴落パニック検知"
        # 3. 押し目買い
        elif latest_price > sma50 and latest_price <= sma20 and rsi < 50:
            detected_system = "🛡️ 攻めの押し目買い"

        if detected_system:
            # 簡略スコア算出 (ボラティリティ調整)
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
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-lite:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}

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

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        res_json = response.json()
        if "candidates" in res_json and len(res_json["candidates"]) > 0:
            return res_json["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "⚠️ Gemini APIからの回答生成に失敗しました。"
    except Exception as e:
        return f"⚠️ 通信エラーが発生しました: {e}"

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
        print("ℹ️ 本日基準を満たす銘柄はありませんでした。")
        send_discord_message("🧭 **【AIアナリスト】** 本日基準を満たす注目銘柄は検出されませんでした。")
        return

    df_ranked = df_candidates.sort_values(by="score", ascending=False)
    df_top = df_ranked.head(5)

    print(f"🎯 選定されたトップ{len(df_top)}銘柄のAI背景解析を開始します...")

    for rank, (_, row) in enumerate(df_top.iterrows(), 1):
        clean_code = row["code"].replace(".T", "")
        company_name = row["name"]
        detected_system = row["system"]

        # API制限(RPM)を抑えるため12秒待機
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
