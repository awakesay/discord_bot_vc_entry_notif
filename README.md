# Discord_bot_vc_entry

## 概要
    - Discordのボイスチャンネルに誰かが入ると、テキストチャンネルに通知してくれるボットです。

## 動作環境
    - PC: Raspberry Pi 4
    - OS: Raspberry Pi OS
    - Lang: Python 3.9.2
        - Package: pycord

## 事前準備
    - Discord bot APIキー（/config/discord_bot.jsonにセット)
        - ボットの導入方法は省略

## 外部サービス
    - Discord API

## 利用方法
    - /vce_add_channelコマンドでボイスチャンネルとテキストチャンネルを紐付けする。