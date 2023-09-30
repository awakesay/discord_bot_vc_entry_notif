# Discord_bot_vc_entry

## 概要
Discordのボットです。
誰かがボイスチャンネルに入ると、テキストチャンネルに投稿します。

## 環境
    - Python3.11^
        - py-cord, json5
    
## 事前準備
    - Discord botのAPIトークンを`./config/discord_bot.json5`の`bot_token`にセット。

## 外部サービス
    - Discord API

## 利用方法
    - /voice_entry_ ... から始まるコマンドを利用して操作する。