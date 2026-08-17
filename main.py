import os
import requests
import yfinance as yf
import pandas as pd
from google import genai

# ==========================================
# 1. 環境変数の取得
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Gemini Client の初期化
client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. 監視銘柄リスト
# ==========================================
TARGET_STOCKS = {
    "7203.T": "トヨタ自動車",
    "9984.T": "ソフトバンクグループ",
    "6758.T": "ソニーグループ",
    "7974.T": "任天堂",
    "3382.T": "セブン&アイHD",
    "8306.T": "三菱UFJフィナンシャル・グループ",
    "6857.T": "アドバンテスト",
    "8035.T": "東京エレクトロン",
    "9432.T": "NTT",
    "6920.T": "レーザーテック"
}

# ==========================================
# 3. テクニカル分析・シグナル検出関数
# ==========================================
def analyze_stock(ticker, name):
    try:
        df = yf.download(ticker, period="6m", interval="1d")
        if df.empty or len(df) < 50:
            return None

        # 終値・出来高の取得
        close = df['Close'].iloc[-1]
        if isinstance(close, pd.Series):
            close = close.item()
            
        high_20 = df['High'].iloc[-21:-1].max()
        if isinstance(high_20, pd.Series):
            high_20 = high_20.item()

        sma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        if isinstance(sma20, pd.Series):
            sma20 = sma20.item()

        sma50 = df['Close'].rolling(window=50).mean().iloc[-1]
        if isinstance(sma50, pd.Series):
            sma50 = sma50.item()

        # シグナル判定
        signal = None
        if close > high_20:
            signal = "新高値ブレイクアウト"
        elif close > sma50 and close <= sma20:
            signal = "攻めの押し目買い"

        if signal:
            code = ticker.replace(".T", "")
            return {
                "code": code,
                "name": name,
                "signal": signal,
                "close": round(close, 1)
            }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
    return None

# ==========================================
# 4. Gemini API によるレポート生成関数
# ==========================================
def generate_report(stock_info):
    prompt = f"""
以下の銘柄について、投資アナリストとして簡潔な銘柄深掘りレポートを作成してください。

【対象銘柄】
・銘柄名: {stock_info['name']} ({stock_info['code']})
・検出シグナル: {stock_info['signal']}
・直近株価: {stock_info['close']}円

【出力フォーマット】
1. シグナルの背景と現状分析（2〜3文）
2. 今後の注目ポイント・リスク要因（2〜3文）
3. 短期的な売買方針（1文）
※文字数は全体で250文字程度、箇条書きを活用して読みやすく作成してください。
"""
    try:
        # SDK最新仕様: client.models.generate_content & gemini-2.0-flash を使用
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Gemini API呼び出し失敗 (詳細: {e})"

# ==========================================
# 5. Discord Webhook 送信関数
# ==========================================
def send_discord_notification(rank, stock_info, report_text):
    message = f"""
【AIアナリスト：銘柄深掘りレポート (第{rank}位)】
{stock_info['name']} ({stock_info['code']}) ｜ 検出網: {stock_info['signal']}
ーーーーーーーーーーーーーーーーーー
{report_text}
ーーーーーーーーーーーーーーーーーー
"""
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"Discord sent successfully for {stock_info['name']}")
    except Exception as e:
        print(f"Failed to send Discord message: {e}")

# ==========================================
# 6. メイン実行処理
# ==========================================
def main():
    print("スクリーニングを開始します...")
    detected_stocks = []

    for ticker, name in TARGET_STOCKS.items():
        result = analyze_stock(ticker, name)
        if result:
            detected_stocks.append(result)

    if not detected_stocks:
        print("本日検出された銘柄はありません。定期通知を送信します。")
        no_signal_message = """
🚨 **【AIアナリスト：スクリーニング結果報告】**

💤 本日、監視対象銘柄の中でスクリーニング条件（新高値ブレイクアウト／攻めの押し目買い）を満たす銘柄はありませんでした。
"""
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": no_signal_message})
        except Exception as e:
            print(f"Failed to send zero-match notification: {e}")
        return
