
import os
import json
import random
from typing import Union
from functools import cache
import discord

def run_bot():

    intents = discord.Intents.default()
    intents.message_content = True
    bot = discord.Bot(intents=intents)
    
    @bot.event
    async def on_ready():
        """起動メッセージ"""
        print('on_ready')
        print(f'version: {discord.__version__}')

    @bot.event
    async def on_voice_state_update(member, before, after):
        """ボイスチャンネル入室通知"""
        rand_msg = get_config_json('rand_msg')  # メッセージリスト取得
        vc_tc = get_config_json('vc_tc')        # チャンネル設定取得
        if before.channel != None:
            return  # イベント前にVCに入ってたときは早期リターン
        elif str(after.channel.id) not in vc_tc.keys():
            return  # vc_tc.jsonに登録されていないチャンネルのときは早期リターン
        elif member.bot:
            return  # イベントを発生させたのがボットのときは早期リターン
        else:
            msg = get_msg(rand_msg, member.name, after.channel.name)                # 表示メッセージ取得
            emb = discord.Embed(title=msg, color=0x2ecc71)      # Embedオブジェクト生成
            channel_id = get_channel(vc_tc, after.channel.id)   # 投稿するテキストチャンネルID取得
            channel = bot.get_channel(channel_id)               # チャンネルIDからチャンネルオブジェクト取得
            await channel.send(embed=emb)                       # 投稿
    
    bot.run(get_config_json('discord_bot')['token'])


def get_msg(rand_msg: list, name: str, vc_name: str) -> str:
    """メッセージをランダムに選択＆名前を置換して返します。"""
    raw_msg = random.sample(rand_msg, 1)[0]
    return raw_msg.replace('{name}', name).replace('{vc_name}', vc_name)


def get_channel(vc_tc: dict, vc: int) -> Union[int, None]:
    """ボイスチャンネルIDに対応したテキストチャンネルIDを返します。"""
    return vc_tc.get(str(vc), None)

@cache  # キャッシュによる高速化
def get_config_json(name: str) -> Union[list, dict]:
    """configフォルダ内の設定を取得して返します。"""
    path = f'{os.path.abspath(os.path.dirname(__file__))}/config/{name}.json'
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


if __name__ == '__main__':
    run_bot()
