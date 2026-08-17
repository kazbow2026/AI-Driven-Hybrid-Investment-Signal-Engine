import os
import requests
import yfinance as yf
import pandas as pd
from google import genai

# ==========================================
# 1. 設定・環境変数・テストモードの初期化
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# テストモードの判定（環境変数 TEST_MODE="true" または直接 True に指定で有効化）
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# google-genai SDK クライアントの初期化
client = genai.Client(api_key=GEMINI_API_KEY)

# ==========================================
# 2. 監視銘柄リスト（約200銘柄に拡充）
# ==========================================
RAW_DATA = [
    "7203:トヨタ自動車,7201:日産自動車,7267:本田技研工業,7269:スズキ,6902:デンソー",
    "7259:アイシン,7270:SUBARU,5108:ブリヂストン,7261:マツダ,6758:ソニーグループ",
    "6501:日立製作所,6503:三菱電機,6752:パナソニックHD,6645:オムロン,6762:TDK",
    "6506:安川電機,6861:キーエンス,6981:村田製作所,6954:ファナック,8035:東京エレクトロン",
    "6146:ディスコ,6971:京セラ,6857:アドバンテスト,7735:SCREEN_HD,6723:ルネサスエレ",
    "6526:ソシオネクスト,6701:日本電気,6702:富士通,6504:富士電機,6869:シスメックス",
    "6920:レーザーテック,6178:日本郵政,7751:キヤノン,7741:HOYA,6473:ジェイテクト",
    "6471:日本精工,6301:小松製作所,6326:クボタ,6367:ダイキン工業,6141:DMG森精機",
    "6143:ソディック,7011:三菱重工業,7012:川崎重工業,7013:IHI,7272:ヤマハ発動機",
    "6273:SMC,6586:マキタ,6740:JDI,6770:アルプスアルパイン,9432:NTT",
    "9433:KDDI,9984:ソフトバンクG,9434:ソフトバンク,4689:LINEヤフー,4755:楽天グループ",
    "9613:NTTデータ,4307:野村総合研究所,3774:IIJ,9735:セコム,3659:ネクソン",
    "2121:MIXI,2413:エムスリー,4418:JDSC,5253:カバー,130A:VIS,2158:FRONTEO",
    "4385:メルカリ,3923:ラクス,4739:CTC,9684:スクエニHD,9759:NSD,3626:TIS",
    "2317:システナ,3861:王子HD,3915:テラスカイ,4188:三菱ケミカルG,4475:HENNGE",
    "4480:メドレー,4768:大塚商会,6098:リクルートHD,6191:エアトリ,6532:ベイカレント",
    "7309:シマノ,9602:東宝,4816:東映アニメ,9697:カプコン,4661:オリエンタルランド",
    "8306:三菱UFJ,8316:三井住友FG,8411:みずほFG,8308:りそなHD,8309:三井住友トラスト",
    "7182:ゆうちょ銀行,7184:富山第一銀行,8604:野村HD,8630:SOMPO,8725:MS&AD",
    "8766:東京海上HD,8591:オリックス,7167:めぶきFG,8331:千葉銀行,8354:ふくおかFG",
    "8410:セブン銀行,8593:三菱HCキャピタル,8697:日本取引所G,8253:クレディセゾン,7181:かんぽ生命",
    "8001:伊藤忠商事,8031:三井物産,8053:住友商事,8058:三菱商事,8002:丸紅,2768:双日",
    "8015:豊田通商,7459:メディパルHD,9843:ニトリHD,3038:神戸物産,7532:パンパシHD",
    "2670:ABCマート,8267:イオン,8233:高島屋,8252:丸井グループ,3088:マツキヨココカラ",
    "3092:ZOZO,3391:ツルハHD,9983:ファーストリテイリング,3382:セブン&アイHD,4502:武田薬品",
    "4503:アステラス製薬,4507:塩野義製薬,4519:中外製薬,4523:エーザイ,4568:第一三共",
    "4578:大塚HD,4901:富士フイルム,4911:資生堂,4452:花王,3407:旭化成,3402:東レ",
    "4005:住友化学,4183:三井化学,4204:積水化学,4631:DIC,5020:ENEOS,1605:INPEX",
    "9501:東京電力HD,9502:中部電力,9503:関西電力,9531:東京ガス,9532:大阪ガス",
    "5401:日本製鉄,5406:神戸製鋼所,5411:JFE,5713:住友金属鉱山,5714:DOWA,3863:日本製紙",
    "5201:AGC,5333:日本ガイシ,5334:日本特殊陶業,2502:アサヒG,2503:キリンHD",
    "2914:JT,2267:ヤクルト,2269:明治HD,2802:味の素,1801:大成建設,1802:大林組",
    "1803:清水建設,1812:鹿島建設,1925:大和ハウス,1928:積水ハウス,8801:三井不動産",
    "8802:三菱地所,8830:住友不動産,9001:東武鉄道,9005:東急,9020:JR東日本",
    "9021:JR西日本,9022:JR東海,9201:JAL,9202:ANA,9101:日本郵船,9104:商船三井",
    "9107:川崎汽船,9301:三菱倉庫,4614:トウペ,4681:リゾートトラスト,6055:Jマテリアル",
    "7911:凸版印刷,7912:大日本印刷,7951:ヤマハ,7974:任天堂,7832:バンナムHD",
    "9766:コナミG,9962:ミスミG,9064:ヤマトHD,9143:SGホールディングス"
]

TARGET_STOCKS = {}
for line in RAW_DATA:
    for item in line.split(","):
        if ":" in item:
            code, name = item.split(":")
            TARGET_STOCKS[f"{code}.T"] = name

# ==========================================
# 3. テクニカル分析・シグナル検出関数
# ==========================================
def analyze_stock(ticker, name):
    try:
        df = yf.download(ticker, period="6m", interval="1d", progress=False)
        if df.empty or len(df) < 50:
            return None

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
        # 最新の推奨モデル gemini-3.6-flash を指定
        response = client.models.generate_content(
            model="gemini-3.6-flash",
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
    print(f"全 {len(TARGET_STOCKS)} 銘柄のスクリーニングを開始します...")
    detected_stocks = []

    for ticker, name in TARGET_STOCKS.items():
        result = analyze_stock(ticker, name)
        if result:
            detected_stocks.append(result)

    # テストモード有効化時かつ検出0件の場合、検証用ダミーデータを注入
    if TEST_MODE and not detected_stocks:
        print("【TEST MODE】シグナル不検出のため、テスト用ダミーデータを追加して検証を行います。")
        detected_stocks.append({
            "code": "7203",
            "name": "トヨタ自動車 (テスト)",
            "signal": "新高値ブレイクアウト",
            "close": 2850.0
        })

    # シグナル検出が0件かつテストモードオフの場合
    if not detected_stocks:
        print("本日検出された銘柄はありません。定期通知を送信します。")
        no_signal_message = "🚨 **【AIアナリスト：スクリーニング結果報告】**\n\n💤 本日、監視対象銘柄の中でスクリーニング条件を満たす銘柄はありませんでした。"
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": no_signal_message})
        except Exception as e:
            print(f"Failed to send zero-match notification: {e}")
        return

    print(f"{len(detected_stocks)} 件の銘柄を検出しました。レポートを作成します...")

    for i, stock in enumerate(detected_stocks, 1):
        report = generate_report(stock)
        send_discord_notification(i, stock, report)

if __name__ == "__main__":
    main()
