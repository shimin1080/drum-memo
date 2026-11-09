# Drum memo — 開発の引き継ぎ

スマートフォンでドラムパターンをすばやくメモするアプリ。Web 版（PWA）と、同じコードを Capacitor で包んだ iPhone / Android アプリがある。
オーナーは日本語で指示する。返答・コメント・コミットメッセージは日本語で書く。

## 作業ルール（オーナーの希望）

- **コミット・プッシュは頼まれたときだけ**行う（「コミットしてプッシュ」と言われることが多い）。
- 音（`VOICES`、RD/CR/RS の合成）を大きく変える提案は何度も却下されている。音は頼まれない限り触らない。
- 振動（Haptics）は不要と言われて削除済み。入れない。
- UI の変更は小さな動きのなめらかさまで気にする（ガクッと動く・一瞬飛ぶ、などは不具合として扱う）。

## 構成

| パス | 内容 |
|---|---|
| `index.html` | アプリ本体（HTML・CSS・JS がすべてこの1ファイル、約1600行） |
| `sw.js` | Service Worker。**index.html を変えたら `CACHE` の番号を上げる**（今は `drum-memo-v39`） |
| `manifest.webmanifest`, `icon-*.png` | PWA 用 |
| `scripts/build-www.mjs` | アプリに入れるファイルを `www/` に書き出す（`npm run build`） |
| `scripts/android-assets.py` | Android のアイコン・起動画面を生成（Pillow が必要） |
| `capacitor.config.json` | appId `jp.shimin.drummemo`、webDir `www` |
| `ios/` | Xcode プロジェクト（Capacitor 8、SPM。CocoaPods なし） |
| `android/` | Android Studio プロジェクト |

- Web 版は GitHub Pages でリポジトリ直下をそのまま公開: https://shimin1080.github.io/drum-memo/ （リポジトリ `shimin1080/drum-memo`、public、ブランチ `main`）
- `www/`, `node_modules/` は git 管理外。

## index.html の要点

- **データ**: `p.tracks` の値は 0〜3（ベロシティ 1/2/3 = 小/中/大）、`DATA_VER=2`。`p.divs` は拍ごとの分割（3 = 三連）。楽器ごとに `p.volumes` / `p.swings` / `p.muted`、`p.swing8`（8分スウィング）。保存は `Store`（IndexedDB）。
- **音**: Web Audio で合成（`VOICES`、`hit(id,t,vol)` → `bus`）。RD/CR/RS は Web Worker で事前レンダリング（`prerender`、`PRE_SR=48000`）。AudioContext は最初に音を出すときに作る（起動を速くするため）。
- **再生**: 先読みスケジューラ。Worker の `clock` で回し、通常 0.12 秒・`document.hidden` 時 1.5 秒先まで予約。光るマスは `audibleTime()` + `VISUAL_LEAD`(0.05) で音に合わせる。
- **ハイハット**: CH が OH を止める処理は `chokeOpenHat()`（`cancelAndHoldAtTime`）。単純な `cancelScheduledValues` に戻すとバックグラウンドで音が乱れる。
- **アプリ判定**: `IS_APP`（Capacitor ネイティブ）で `html.is-app`、Android は加えて `html.is-android`。
- **起動アニメーション**: `#intro`（起動画面と同じ 4x4 のマスの絵）を `playIntro()` で動かし、そこで SplashScreen を隠す。大きさは iOS が `max(100vw,100vh)*172/1366`、Android が `116px`（Android 12+ の起動画面アイコンの実測値。`android-assets.py` の `GRID_SPLASH` と揃える）。
- **タグ**: パターン名の右に右寄せ。追加・削除時は `slideFrom()` で「+」と他のタグをすべらせる。日本語入力の確定 Enter をタグにしない対策あり（`tagComposing` 等）。
- 上部バーは `setTbar()` で折りたたみ（状態は localStorage `drum-memo-tbar`）。楽器の並べ替えは長押しドラッグ（`DRAG_HOLD=350`）。

## ビルドと確認

```bash
npm run build                 # www/ を作る
npx cap sync                  # iOS・Android に反映
```

- **iOS**: `npx cap open ios` → Xcode で ▶。シミュレーター確認例: `xcodebuild -project ios/App/App.xcodeproj -scheme App -destination 'id=<SIM_ID>' -derivedDataPath <tmp>/dd build` → `xcrun simctl install/launch`。
  - AppDelegate で AVAudioSession を `.playback` + `.mixWithOthers`、Info.plist に `UIBackgroundModes: audio`。WebView 側は `navigator.audioSession.type='playback'`（消音スイッチ対策）。
- **Android**: Java は Android Studio 付属のものを使う。
  ```bash
  cd android && JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew assembleDebug
  ~/Library/Android/sdk/platform-tools/adb install -r app/build.nosync/outputs/apk/debug/app-debug.apk
  ```
  - 付属 Java が 25 のため Gradle wrapper を **9.1.0** に上げてある（8.14 では動かない）。
  - デスクトップが iCloud 同期されていて、ビルド中に「〜 2.png」等の複製ができてビルドが壊れるため、**ビルド出力先を `build.nosync`** にしている（`android/build.gradle` の `layout.buildDirectory`）。
  - エミュレーター `Pixel_10a`（arm64、GPU は host、RAM 4GB）。WebView のデバッグは `adb forward tcp:9333 localabstract:webview_devtools_remote_<pid>` → `http://localhost:9333/json`。
  - バックグラウンド再生: 再生中だけフォアグラウンドサービス（`PlaybackService`、type `mediaPlayback`）を起動。JS の `bgPlayback()` から `BackgroundPlaybackPlugin`（`MainActivity` で登録）を呼ぶ。`setRendererPriorityPolicy(IMPORTANT, false)` で WebView を後回しにさせない。
  - Edge-to-edge: `capacitor.config.json` の `SystemBars.initialViewportFitValueHint: "cover"` で WebView を全画面にし、余白は CSS の `env(safe-area-inset-*)` で取る。

## 現在の状態（2026-11 時点）

- 最終コミット `46e696d`（iOS・Android アプリ化の設定）。それ以降の次の変更は **未コミット**:
  - Android のアイコン・起動画面（`scripts/android-assets.py` で生成）
  - 起動画面と起動アニメーションの位置・大きさ合わせ（edge-to-edge 化を含む）
  - Android のバックグラウンド再生（フォアグラウンドサービス）
  - `build.nosync` への出力先変更、`sw.js` v39
- これらはエミュレーターで確認済み。**実機では未確認**（特に画面オフ時の音の途切れ、音と光のタイミング）。

## 残っていること

1. 上記の未コミット変更のコミット（オーナーの指示待ち）。
2. Android 実機での確認（バックグラウンド再生、タイミング、動きの軽さ）。
3. Android 13+ で「再生中」通知を見せたければ `POST_NOTIFICATIONS` の許可を求める（今は求めていないので通知は非表示、再生は続く）。
4. 配信準備
   - iOS: バージョン 1.0.0 (build 1)、`ITSAppUsesNonExemptEncryption=false` の追加、TestFlight → App Store（有料販売予定）。
   - Android: Google Play Console 登録、署名付き AAB、個人アカウントは 12 人以上 × 14 日のクローズドテストが必要。
5. プライバシーポリシー（データは端末内のみ・収集なし）。
