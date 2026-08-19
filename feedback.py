# ==============================================================================
# パフォーマンス自動振り返り ＆ ログ集計スクリプト (feedback.py)
# ==============================================================================
from datetime import datetime
import os
import json
import pandas as pd
import requests
import yfinance as yf

DISCORD_WEBHOOK_URL = os.environ.get(
    "DISCORD_WEBHOOK_URL",
    "https://discord.com/api/webhooks/1530870013467037868/Wegx5aRkM1su7SNlXsvZ0g7DGkg1Ryk9wnGXMkI1o2l71POgI6nh7JiO8Y-WYLJpyLZL",
)

def send_discord_notification(webhook_url, content=None, embeds=None):
    if not webhook_url or "discord.com/api/webhooks" not in webhook_url:
        print("💡 [Discord通知スキップ] Webhook URLが設定されていません。")
        return
    headers = {"Content-Type": "application/json"}
    payload = {}
    if content:
        payload["content"] = content
    if embeds:
        payload["embeds"] = embeds
    try:
        requests.post(webhook_url, data=json.dumps(payload), headers=headers)
    except Exception as e:
        print(f"❌ Discord通信エラー: {e}")

def evaluate_performance():
    history_path = "data/history.csv"
    
    # 1. ファイルが存在するか、または空（サイズが0バイト）でないかチェック
    if not os.path.exists(history_path) or os.path.getsize(history_path) == 0:
        print("⚠️ 蓄積された履歴データ (`data/history.csv`) が存在しないか、空です。評価をスキップします。")
        return

    try:
        # 履歴データの読み込み
        df_history = pd.read_csv(history_path, dtype={"code": str})
    except Exception as e:
        print(f"⚠️ 履歴データの読み込みに失敗しました: {e}")
        return

    if df_history.empty:
        print("⚠️ 履歴データが空です。評価をスキップします。")
        return

    # 2. 必須カラムがすべて揃っているかチェック（KeyError防止）
    required_columns = ["code", "date", "price", "pattern", "name"]
    missing_columns = [col for col in required_columns if col not in df_history.columns]
    if missing_columns:
        print(f"⚠️ 履歴データに必要なカラムが不足しています (不足: {missing_columns})。評価をスキップします。")
        return

    evaluated_records = []
    wins = 0
    total_return = 0.0
    count = 0

    print("=== 📊 過去シグナルのパフォーマンス評価を開始 ===")

    for _, row in df_history.iterrows():
        code = str(row["code"])
        entry_date = row["date"]
        entry_price = float(row["price"])
        pattern = row["pattern"]
        name = row["name"]

        ticker_symbol = f"{code}.T"
        try:
            # エントリー日以降の株価データを取得して最新価格を確認
            df_stock = yf.download(ticker_symbol, start=entry_date, progress=False)
            if isinstance(df_stock.columns, pd.MultiIndex):
                df_stock.columns = df_stock.columns.get_level_values(0)
            
            if df_stock.empty:
                continue

            current_price = float(df_stock["Close"].iloc[-1])
            return_pct = round(((current_price - entry_price) / entry_price) * 100, 2)
            is_win = 1 if return_pct > 0 else 0

            if return_pct > 0:
                wins += 1
            total_return += return_pct
            count += 1

            evaluated_records.append({
                "eval_date": datetime.today().strftime("%Y-%m-%d"),
                "code": code,
                "name": name,
                "pattern": pattern,
                "entry_date": entry_date,
                "entry_price": entry_price,
                "current_price": current_price,
                "return_pct": return_pct,
                "result": "WIN" if is_win else "LOSE"
            })
        except Exception as e:
            print(f"銘柄 {code} の評価中にエラー: {e}")
            continue

    if count == 0:
        print("有効な評価データがありませんでした。")
        return

    win_rate = round((wins / count) * 100, 1)
    avg_return = round(total_return / count, 2)

    # グラフ化・可視化用の蓄積CSVに保存 (data/performance_log.csv)
    os.makedirs("data", exist_ok=True)
    perf_log_path = "data/performance_log.csv"
    df_perf = pd.DataFrame(evaluated_records)
    df_perf.to_csv(perf_log_path, index=False, encoding="utf-8-sig")
    print(f"💾 パフォーマンス評価ログを `{perf_log_path}` に保存しました（スプレッドシートへのインポートに利用可能）。")

    # Discord通知の作成
    embed = {
        "title": "📊 【週次・月次パフォーマンス振り返りレポート】",
        "color": 3447003, # ブルー系
        "fields": [
            {"name": "評価対象シグナル数", "value": f"{count} 件", "inline": True},
            {"name": "勝率", "value": f"**{win_rate}%** ({wins}勝 / {count - wins}敗)", "inline": True},
            {"name": "平均リターン", "value": f"**{avg_return:+.2f}%**", "inline": True},
            {"name": "データ保存先", "value": "`data/performance_log.csv` (スプレッドシート連携用)", "inline": False}
        ],
        "footer": {"text": "AIアナリスト ＆ バックテスト検証システム"}
    }

    send_discord_notification(
        DISCORD_WEBHOOK_URL,
        content="📈 **定期パフォーマンス評価が完了しました！**",
        embeds=[embed]
    )

if __name__ == "__main__":
    evaluate_performance()
