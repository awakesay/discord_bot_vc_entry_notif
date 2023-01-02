
import os
import json
import random
from typing import Union
from functools import cache
import discord

def run_bot():

    intents = discord.Intents.all()
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
            msg = get_msg(rand_msg, member.name, after.channel.name)# 表示メッセージ取得
            emb = discord.Embed(title=msg, color=0x2ecc71)          # Embedオブジェクト生成
            channel_id = get_channel_id(vc_tc, after.channel.id)    # 投稿するテキストチャンネルID取得
            channel = bot.get_channel(channel_id)                   # チャンネルIDからチャンネルオブジェクト取得
            await channel.send(embed=emb)                           # 投稿
    

    @bot.slash_command(description='VC入室時のメッセージ一覧を表示します。')
    async def vce_list(ctx):
        """メッセージ一覧を表示します。"""
        await ctx.respond(f'```\ncmd: vce_list\n```')
        msg = ''
        for i, message in enumerate(get_config_json('rand_msg')):
            number = str(i).rjust(3, ' ')
            msg += f'\n{number}: {message}'
        await ctx.channel.send(f'```\n{msg}\n```')


    @bot.slash_command(description='VC入室時のメッセージを追加します。')
    async def vce_add_msg(
        ctx: discord.ApplicationContext,
        add_msg: discord.Option(str, required=True, description='{name}はユーザー名、{vc_name}はボイスチャンネル名に置換します。')
    ):
        """メッセージを追加します。"""
        await ctx.respond(f'```\ncmd: vce_add_msg, args: {add_msg}\n```')
        rand_msg = get_config_json('rand_msg')
        rand_msg.append(add_msg)
        res = set_config_json('rand_msg', rand_msg)
        if res[0]:
            await ctx.channel.send(f'{add_msg}\nを追加しました。')
        else:
            await ctx.channel.send(f'エラーが発生しました。\n{res[1]}')


    @bot.slash_command(description='VC入室時のメッセージを削除します。')
    async def vce_del_msg(
        ctx: discord.ApplicationContext,
        del_number: discord.Option(str, required=True, description='{name}はユーザー名、{vc_name}はボイスチャンネル名に置換します。')
    ):
        """メッセージを削除します。"""
        await ctx.respond(f'```\ncmd: vce_del_msg, args: {del_number}\n```')
        rand_msg = get_config_json('rand_msg')
        del_msg = rand_msg.pop(del_number)
        res = set_config_json('rand_msg', rand_msg)
        if res[0]:
            await ctx.channel.send(f'{del_msg}\nを削除しました。')
        else:
            await ctx.channel.send(f'エラーが発生しました。\n{res[1]}')


    bot.run(get_config_json('discord_bot')['token'])


def get_msg(rand_msg: list, name: str, vc_name: str) -> str:
    """メッセージをランダムに選択＆名前とVC名を置換して返します。"""
    raw_msg = random.sample(rand_msg, 1)[0]
    return raw_msg.replace('{name}', name).replace('{vc_name}', vc_name)


def get_channel_id(vc_tc: dict, vc: int) -> Union[int, None]:
    """ボイスチャンネルIDに対応したテキストチャンネルIDを返します。"""
    return vc_tc.get(str(vc), None)

#@cache  # キャッシュによる高速化
def get_config_json(name: str) -> Union[list, dict]:
    """configフォルダ内の設定を取得して返します。"""
    path = f'{os.path.abspath(os.path.dirname(__file__))}/config/{name}.json'
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def set_config_json(name: str, set_obj: Union[list, dict]) -> list[bool, str]:
    """configフォルダ内に設定を書き込みます。"""
    try:
        path = f'{os.path.abspath(os.path.dirname(__file__))}/config/{name}.json'
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(set_obj, f)
            return True, ''
    except Exception as e:
            return False, str(e)


if __name__ == '__main__':
    run_bot()
