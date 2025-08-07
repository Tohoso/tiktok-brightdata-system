# Bright Data APIキー取得・設定ガイド

## 🎯 **APIキー取得手順**

### **ステップ1: アカウント作成**

1. **Bright Data公式サイトにアクセス**
   - URL: https://brightdata.com/products/web-scraper/tiktok
   - 25%割引コード: `APIS25` (6ヶ月間有効)

2. **無料トライアル開始**
   - 「Start free trial」をクリック
   - メールアドレスで登録 または Google/GitHub連携
   - 認証完了後、ダッシュボードにアクセス

### **ステップ2: TikTokスクレイパー設定**

1. **ダッシュボードにログイン**
   - URL: https://brightdata.com/cp
   - 左メニューから「Web Scrapers」を選択

2. **TikTokスクレイパーを有効化**
   - 「TikTok - Posts」または「TikTok - Profiles」を選択
   - 「Start free trial」をクリック
   - 設定を完了

### **ステップ3: APIキー取得**

1. **データセット設定**
   - ダッシュボードで「Datasets」セクションに移動
   - TikTokスクレイパーのデータセットを確認
   - **Dataset ID**をコピー（例: `gd_l7q7dkf244hwjntr0`）

2. **APIキー生成**
   - 「API Access」または「Settings」セクションに移動
   - 「Generate API Key」をクリック
   - **API Key**をコピー（例: `e6bcf62b20...`）

3. **Collector ID確認**
   - スクレイパー設定ページで**Collector ID**を確認
   - または「API Documentation」で確認

---

## 🔧 **設定ファイル更新**

### **config.json更新**

```json
{
  "bright_data": {
    "api_key": "YOUR_ACTUAL_API_KEY",
    "dataset_id": "YOUR_DATASET_ID",
    "collector_id": "YOUR_COLLECTOR_ID",
    "timeout": 300,
    "max_retries": 3
  },
  "google_sheets": {
    "credentials_file": "credentials.json",
    "spreadsheet_name": "tiktok",
    "worksheet_name": "tiktok"
  }
}
```

### **実際の値の例**

```json
{
  "bright_data": {
    "api_key": "e6bcf62b20a1b2c3d4e5f6g7h8i9j0k1",
    "dataset_id": "gd_l7q7dkf244hwjntr0",
    "collector_id": "c_l7q7dkf244hwjntr0",
    "timeout": 300,
    "max_retries": 3
  }
}
```

---

## 🧪 **設定テスト**

### **APIキー動作確認**

```bash
cd tiktok-brightdata-system
python test_brightdata_only.py
```

### **期待される結果**

```
✅ Bright Data API接続成功
✅ データセット確認完了
✅ Collector設定正常
```

---

## 🚨 **よくある問題と解決策**

### **問題1: Collector not found (404エラー)**

**原因**: Collector IDが間違っているか、スクレイパーが有効化されていない

**解決策**:
1. ダッシュボードでTikTokスクレイパーが有効化されているか確認
2. 正しいCollector IDをコピー
3. Dataset IDとCollector IDの整合性を確認

### **問題2: 認証エラー (401/403エラー)**

**原因**: APIキーが無効または期限切れ

**解決策**:
1. ダッシュボードで新しいAPIキーを生成
2. config.jsonを更新
3. アカウントの課金状況を確認

### **問題3: データが取得できない**

**原因**: スクレイパーの設定やパラメータが不正

**解決策**:
1. ダッシュボードでスクレイパーの動作状況を確認
2. APIドキュメントで正しいパラメータを確認
3. 小さなテストリクエストから開始

---

## 💰 **料金プラン推奨**

### **テスト・開発用**
- **Pay as you go**: $1.50/1K requests
- **無料クレジット**: $5-10
- **推奨**: 初期テスト用

### **本格運用用**
- **Growth**: $502/月 (25%割引適用後)
- **Business**: $1,012/月 (25%割引適用後)
- **推奨**: 月間300-500件収集用

---

## 📞 **サポート情報**

### **Bright Dataサポート**
- **チャット**: ダッシュボード右下のチャットアイコン
- **メール**: support@brightdata.com
- **ドキュメント**: https://docs.brightdata.com/

### **24/7サポート**
- 平均応答時間: 10分以内
- 日本語サポート: 利用可能
- 技術サポート: 無料

---

## 🎉 **設定完了後の次のステップ**

### **1. システムテスト**
```bash
python test_api_connection.py
```

### **2. 実際のデータ収集**
```bash
python main.py --method discover --test
```

### **3. Google Sheets確認**
- スプレッドシート「tiktok」を確認
- データが正常に書き込まれているか確認

### **4. 本格運用開始**
```bash
python main.py --method hybrid
```

---

## 🏆 **成功の指標**

### **技術的成功**
- ✅ API接続成功率: 95%以上
- ✅ データ取得成功率: 90%以上
- ✅ Google Sheets書き込み成功率: 100%

### **ビジネス成功**
- 🎯 24時間以内動画発見率: 85%以上
- 🎯 50万再生以上動画発見率: 95%以上
- 🎯 日本動画精度: 90%以上

**Bright Data APIキーの正しい設定により、TikTok Bright Data Systemが完全に稼働し、24時間以内・50万再生以上のバイラル動画を自動収集できるようになります！** 🚀

