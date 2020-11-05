# genkai-bot for Heroku
## genkai-bot for Herokuとは
Genkai-bot for Herokuは、某身内discord鯖で利用していたbotから汎用的に利用できる（であろう機能）を抽出したプログラムです。

## 動作
1. 特定のテキストチャンネルの権限を管理し、特定のボイスチャンネルにインしている場合のみ閲覧権限が与えられるようにします
1. 通話に参加していない人はそのテキストチャンネルが見れないため、通知が抑制されます
1. ボイスチャンネルに人が誰も居なくなったらそのチャンネルと関連付けられたテキストチャンネルの内容を全て消去します
1. 10分に1回程度ボイスチャンネルをチェックし、権限の付与漏れ及びテキストチャンネルの削除漏れを確認します
1. WebカメラのON検知 / GoLiveの開始検知に対応し、(設定に応じて)任意のチャンネルで通知することができます

## セットアップ
必要なランタイムを入れさえすればどこでもで動きはしますが、一応何も考えずにHerokuで動作出来るように作ってます
### Herokuのアカウントを作成
https://jp.heroku.com/

新規登録からアカウント登録ができます

アカウント登録後、以下からHeroku-CLIをインストールしてください

https://devcenter.heroku.com/articles/heroku-cli

### Gitをインストール
Windows: https://gitforwindows.org/

### Discordのトークンを取得
とってください

### botのダウンロードと設定
事前にテキストチャンネルとボイスチャンネルを作成し、チャンネルIDを取得する。
次に、以下の書式でテキストファイルを作成する。
```
対象ボイスチャンネルID,対象テキストチャンネルID,カメラON通知を出すチャンネルID
```
要するにCSV形式です。ファイルそのものは```chlist.txt```で同じ階層で保存してください。

同じ要領でログを出力するテキストチャンネルIDを記載した```chlog.txt```を必要に応じて作成してください。

```
git init
git add .
git commit -m "Genkai Commit"
heroku create genkai-bot
heroku config:set ENV_TOKEN=XXXXXXXXXXXXXXXXX
git push heroku master
```