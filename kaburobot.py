import yfinance as yf
import requests
import json
import math
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# 秘密のDiscord Webhook URL
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1521247684739072010/9Co7qc8fdlT8xHtErA-AOaobZTp0phucFiOcEdDfk1G1nsNsbhYVhIYEjuf8D0iEC81C"

print("=== 🚨 【株ロボ1】大本命：200銘柄・メガ二刀流パトロール開始 🚨 ===")

# 200銘柄のデータリスト
raw_data = [
    "7203.T:トヨタ自動車,7201.T:日産自動車,7267.T:本田技研工業,7269.T:スズキ,6902.T:デンソー",
    "7259.T:アイシン,7270.T:SUBARU,5108.T:ブリヂストン,7261.T:マツダ,6758.T:ソニーグループ",
    "6501.T:日立製作所,6503.T:三菱電機,6752.T:パナソニックHD,6645.T:オムロン,6762.T:TDK",
    "6506.T:安川電機,6861.T:キーエンス,6981.T:村田製作所,6954.T:ファナック,8035.T:東京エレクトロン",
    "6146.T:ディスコ,6971.T:京セラ,6857.T:アドバンテスト,7735.T:SCREEN_HD,6723.T:ルネサスエレ",
    "6526.T:ソシオネクスト,6701.T:日本電気,6702.T:富士通,6504.T:富士電機,6869.T:シスメックス",
    "6920.T:レーザーテック,6178.T:日本郵政,7751.T:キヤノン,7741.T:HOYA,6473.T:ジェイテクト",
    "6471.T:日本精工,6301.T:小松製作所,6326.T:クボタ,6367.T:ダイキン工業,6141.T:DMG森精機",
    "6143.T:ソディック,7011.T:三菱重工業,7012.T:川崎重工業,7013.T:IHI,7272.T:ヤマハ発動機",
    "6273.T:SMC,6586.T:マキタ,6740.T:JDI,6770.T:アルプスアルパイン,9432.T:NTT",
    "9433.T:KDDI,9984.T:ソフトバンクG,9434.T:ソフトバンク,4689.T:LINEヤフー,4755.T:楽天グループ",
    "9613.T:NTTデータ,4307.T:野村総合研究所,3774.T:IIJ,9735.T:セコム,3659.T:ネクソン",
    "2121.T:MIXI,2413.T:エムスリー,4418.T:JDSC,5253.T:カバー,130A.T:VIS,2158.T:FRONTEO",
    "4385.T:メルカリ,3923.T:ラクス,4739.T:CTC,9684.T:スクエニHD,9759.T:NSD,3626.T:TIS",
    "2317.T:システナ,3861.T:王子HD,3915.T:テラスカイ,4188.T:三菱ケミカルG,4475.T:HENNGE",
    "4480.T:メドレー,4768.T:大塚商会,6098.T:リクルートHD,6191.T:エアトリ,6532.T:ベイカレント",
    "7309.T:シマノ,9602.T:東宝,4816.T:東映アニメ,9697.T:カプコン,4661.T:オリエンタルランド",
    "8306.T:三菱UFJ,8316.T:三井住友FG,8411.T:みずほFG,8308.T:りそなHD,8309.T:三井住友トラスト",
    "7182.T:ゆうちょ銀行,7184.T:富山第一銀行,8604.T:野村HD,8630.T:SOMPO,8725.T:MS&AD",
    "8766.T:東京海上HD,8591.T:オリックス,7167.T:めぶきFG,8331.T:千葉銀行,8354.T:ふくおかFG",
    "8410.T:セブン銀行,8593.T:三菱HCキャピタル,8697.T:日本取引所G,8253.T:クレディセゾン,7181.T:かんぽ生命",
    "8001.T:伊藤忠商事,8031.T:三井物産,8053.T:住友商事,8058.T:三菱商事,8002.T:丸紅,2768.T:双日",
    "8015.T:豊田通商,7459.T:メディパルHD,9843.T:ニトリHD,3038.T:神戸物産,7532.T:パンパシHD",
    "2670.T:ABCマート,8267.T:イオン,8233.T:高島屋,8252.T:丸井グループ,3088.T:マツキヨココカラ",
    "3092.T:ZOZO,3391.T:ツルハHD,9983.T:ファーストリテイリング,3382.T:セブン&アイHD,4502.T:武田薬品",
    "4503.T:アステラス製薬,4507.T:塩野義製薬,4519.T:中外製薬,4523.T:エーザイ,4568.T:第一三共",
    "4578.T:大塚HD,4901.T:富士フイルム,4911.T:資生堂,4452.T:花王,3407.T:旭化成,3402.T:東レ",
    "4005.T:住友化学,4183.T:三井化学,4204.T:積水化学,4631.T:DIC,5020.T:ENEOS,1605.T:INPEX",
    "9501.T:東京電力HD,9502.T:中部電力,9503.T:関西電力,9531.T:東京ガス,9532.T:大阪ガス",
    "5401.T:日本製鉄,5406.T:神戸製鋼所,5411.T:JFE,5713.T:住友金属鉱山,5714.T:DOWA,3863.T:日本製紙",
    "5201.T:AGC,5333.T:日本ガイシ,5334.T:日本特殊陶業,2502.T:アサヒG,2503.T:キリンHD",
    "2914.T:JT,2267.T:ヤクルト,2269.T:明治HD,2802.T:味の素,1801.T:大成建設,1802.T:大林組",
    "1803.T:清水建設,1812.T:鹿島建設,1925.T:大和ハウス,1928.T:積水ハウス,8801.T:三井不動産",
    "8802.T:三菱地所,8830.T:住友不動産,9001.T:東武鉄道,9005.T:東急,9020.T:JR東日本",
    "9021.T:JR西日本,9022.T:JR東海,9201.T:JAL,9202.T:ANA,9101.T:日本郵船,9104.T:商船三井",
    "9107.T:川崎汽船,9301.T:三菱倉庫,4614.T:トウペ,4681.T:リゾートトラスト,6055.T:Jマテリアル",
    "7911.T:凸版印刷,7912.T:大日本印刷,7951.T:ヤマハ,7974.T:任天堂,7832.T:バンナムHD",
    "9766.T:コナミG,9962.T:ミスミG,9064.T:ヤマトHD,9143.T:SGホールディングス"
]

ticker_dict = {}
for line in raw_data:
    for item in line.split(","):
        code, name = item.split(":")
        ticker_dict[code] = name

ticker_list = list(ticker_dict.keys())
print(f"📊 対象銘柄数: {len(ticker_list)} 銘柄 の巡回を開始します...")

# データ一括取得（8ヶ月分）
try:
    all_data = yf.download(ticker_list, period="8mo", progress=False)
    close_df = all_data["Close"] if "Close" in all_data.columns.levels[0] else all_data
except Exception as e:
    print(f"❌ データ一括取得でエラーが発生しました: {e}")
    close_df = pd.DataFrame()

signal_detected = False

# 各シグナルの計算と審査
for ticker in ticker_list:
    try:
        if ticker not in close_df.columns: continue
        prices = close_df[ticker].dropna()
        if len(prices) < 35: continue
        
        # 移動平均線 (5日, 25日)
        sma_5 = prices.rolling(window=5).mean()
        sma_25 = prices.rolling(window=25).mean()
        
        # RSI (14日)
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi_series = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        
        # ボリンジャーバンド (-1σ)
        std_25 = prices.rolling(window=25).std()
        bb_minus1 = sma_25 - std_25
        
        # 値の抽出
        kinou_kabu = prices.iloc[-2]
        kinou_heikin = sma_5.iloc[-2]
        
        kyou_kabu = prices.iloc[-1]
        kyou_heikin = sma_5.iloc[-1]
        kyou_heikin_25 = sma_25.iloc[-1]
        kyou_rsi = rsi_series.iloc[-1]
        kyou_macd = macd_line.iloc[-1]
        kyou_macd_sig = signal_line.iloc[-1]
        kyou_bb = bb_minus1.iloc[-1]
        
        if any(math.isnan(x) for x in [kyou_rsi, kinou_heikin, kyou_heikin_25, kyou_macd, kyou_macd_sig, kyou_bb]):
            continue
            
        name = ticker_dict[ticker]
        
        # 🛡️ 【システムA：五重鉄壁フィルター】
        if (kyou_rsi <= 42 and 
            (kinou_kabu <= kinou_heikin) and (kyou_kabu > kyou_heikin) and 
            (kyou_kabu > kyou_heikin_25) and 
            (kyou_kabu >= kyou_bb) and 
            (kyou_macd > kyou_macd_sig)):
            
            message = f"🌌 **【株ロボ1：A：五重鉄壁シグナル！】**\n滅多に出ない超安全な買いチャンス！\n会社名: {ticker} {name}\n株価: {round(kyou_kabu)}円"
            requests.post(WEBHOOK_URL, data=json.dumps({"content": message}), headers={"Content-Type": "application/json"})
            print(f"🌟 【{name}】でシステムAが発動！")
            signal_detected = True

        # 🎯 【システムB：攻めの押し目買いフィルター】
        elif (kyou_heikin > kyou_heikin_25 and 
              kyou_rsi <= 45 and 
              kyou_kabu > kinou_kabu):
            
            message = f"🚀 **【株ロボ1：B：攻めの押し目買いシグナル！】**\n上昇トレンド中の『今だけ一時値下げ』を検知！\n会社名: {ticker} {name}\n株価: {round(kyou_kabu)}円\nRSI: {round(kyou_rsi)}"
            requests.post(WEBHOOK_URL, data=json.dumps({"content": message}), headers={"Content-Type": "application/json"})
            print(f"🔥 【{name}】でシステムBが発動！")
            signal_detected = True
            
    except:
        pass

print(f"=== {len(ticker_list)}銘柄すべてのパトロールが完了しました ===")

# === 🚀 チャンスが何もなかった時の安心定期報告 ===
if not signal_detected:
    try:
        no_signal_message = "🚨 **【株ロボ1：二刀流パトロール報告】**\n\n💤 **本日、200銘柄の中にシステムA（五重鉄壁）およびシステムB（押し目買い）の条件を満たす極上銘柄はありません。じっくり力を蓄えましょう。**"
        requests.post(WEBHOOK_URL, data=json.dumps({"content": no_signal_message}), headers={"Content-Type": "application/json"})
        print("🕊️ Discordに『対象なし』の定期報告を送信しました！")
    except Exception as e:
        print(f"⚠️ Discordへの定期報告中にエラーが発生しました: {e}")