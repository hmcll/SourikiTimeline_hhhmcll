@hhhmcll Contribution:
Improved reaction speed of the masking operation


# 総力戦タイムラインメーカー

[![Test](https://github.com/kidonaru/SourikiTimeline/actions/workflows/test.yml/badge.svg)](https://github.com/kidonaru/SourikiTimeline/actions/workflows/test.yml)

総力戦のプレイ動画からタイムラインを作成するアプリケーション


## 概要

このアプリケーションでは、プレイ動画からOCRで情報を読み取り、スキル実行順のタイムラインをTSVとして生成することができます。


### TSVサンプル

| 発動時コスト | キャラ名
| -- | --
| 3.1 | ウイ
| 6.5 | ユウカ（体操服）
| 8.5 | ウイ（水着）
| 9.1 | ミカ
|  | 
|  | アコ
|  | ヒマリ
| 3.4 | ウイ
| 3.0 | ミカ


**表示可能なカラム**
- 発動時コスト
- 残コスト
- キャラ名
- 短縮キャラ名
- スキル名
- 経過時間
- 残り時間
- 動画再生位置


## インストール方法


### Windows

1. [Python 3.10.6](https://www.python.org/downloads/release/python-3106/)をインストールしてください。
   - "Windows installer (64-bit)"からインストーラーをダウンロードします。
   - インストール時に "Add Python to PATH" にチェックを入れます。
2. [このページ](https://github.com/kidonaru/SourikiTimeline/releases) から最新バージョンの`Source code (zip)`をダウンロードします。
3. zipを解凍し、適当なディレクトリに配置します。例えば、`C:\tools`などがおすすめです。
   - 全角文字やスペースが含まれていると動作しないことがあります。
4. `setup.bat`を実行してセットアップを行います。
   - `All complete!!! Please press any key...`と表示されれば成功です。適当なキーを押してください。


## アプリの起動方法

1. `run.bat`を実行します。
   - 成功すると自動的にブラウザが立ち上がり、アプリ画面が表示されます。


## 更新手順

[このページ](https://github.com/kidonaru/SourikiTimeline/releases) から最新のzipをダウンロードして、解凍した中身を上書きしてください。


## 使い方

各作業フローごとにタブが分かれています。

"動画一覧"タブから、右のタブへ順次作業を進めていくとタイムラインの出力ができます。

使い方の参考動画: https://www.youtube.com/watch?v=y1Ss26u0PH0


1. **プロジェクトの作成**
   - "動画一覧"タブを開きます。
   - "新規作成"ボタンを押して、新規作成モーダルを開きます。
   - "タイムライン出力する動画のURL"にYouTube動画のURLを入力して、"作成"ボタンを押します。

2. **動画ファイルのダウンロード**
   - "ダウンロード"タブを開きます。
   - "動画ダウンロード"ボタンを押して、動画をダウンロードします。
   - ダウンロードに失敗する場合、"ダウンローダー"や"フォーマット"を変更すると成功する可能性があります。

3. **マスクの調整**
   - "マスク調整"タブを開きます。
   - 右下の"Download Video"を再生して、適当なスキルの発動時間を調べます。
   - "プレビュー時間"に発動時間を入力して、"プレビュー更新"ボタンを押します。
   - "Preview Image"にキャラ名、コスト、残り時間の読み取り結果が表示されるので、正しく読み取れているか確認します。
       - 正しく読み取れている場合は、4.に進みます。
   - 正しく読み取れていない場合、"動画のクロップ設定"や、"マスク設定"タブでマスク範囲を調整し、"プレビュー更新"ボタンを押して確認、調整をしてください。
   - "マスクのロード"ボタンから、基本的なマスク設定を適用することもできます。
     - `mask_default.png`: 通常の解像度用マスク
     - `mask_iphone.png`: iPhone Xなどの解像度用マスク

4. **タイムラインの生成**
   - "タイムライン生成"タブを開きます。
   - "タイムライン生成"ボタンを押して、タイムラインを生成します。
       - 数分かかるのでしばらく待ちます。
   - 必要に応じて"表示設定"タブで、出力データを調整します。


## 注意事項

このアプリケーションは、趣味の範囲での使用目的で作成されており、商用利用は禁止しています。

また、このアプリケーションを使用したことによるいかなる損害に対しても責任を負いません。

生成したタイムラインは自由に利用してもらって構いませんが、元動画の投稿者ではない場合は個人の使用範囲での利用をお願いします。


## 補足


### マスク画像の作成

OCR用のマスクは、基本的にはアプリケーション内の微調整で済みますが、特殊な解像度の場合は大幅な修正が必要になることもあります。

アプリケーション内で範囲を調整し、保存することもできますが、Photoshopなどで直接マスク画像を作成することもできます。

`resources/mask/mask_default.psd`を開いて、任意のスクリーンショットに合わせてマスクを作成し、pngで保存することでアプリケーションからロードすることができます。

- 赤枠: スキル名の範囲
- 青枠: コストバーの範囲
- 緑枠: 残り時間の範囲


## 質問など

@kidonaruまでDMしてください
可能な範囲で答えます

https://twitter.com/kidonaru


## Credits

- ブルーアーカイブ (Blue Archive) - https://bluearchive.jp/
   - ゲームの情報を参照しています
- ブルーアーカイブ(ブルアカ)攻略Wiki - https://gamerch.com/bluearchive/
  - スキル一覧の情報を参照しています
