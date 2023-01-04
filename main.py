
import os
import json
import platform
import random
from typing import Union
import discord

def run_bot():

    intents = discord.Intents.all()
    intents.message_content = True
    bot = discord.Bot(intents=intents)
    
    @bot.event
    async def on_ready():
        """起動メッセージ"""
        print(f'{"-"*30}\non_ready: discord_bot_vc_entry')
        print(f'python_version: {platform.python_version()}')
        print(f'pycord_version: {discord.__version__}')


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
    async def vce_msg_list(ctx):
        """メッセージ一覧を表示します。"""
        await ctx.respond(f'```cmd: vce_list```')
        msg = ''
        for i, message in enumerate(get_config_json('rand_msg')):
            number = str(i).rjust(3, ' ')
            msg += f'\n{number}: {message}'
        await ctx.channel.send(f'```{msg}```')


    @bot.slash_command(description='VC入室時のメッセージを追加します。')
    async def vce_add_msg(
        ctx: discord.ApplicationContext,
        add_msg: discord.Option(str, required=True, description='{name}はユーザー名、{vc_name}はボイスチャンネル名に置換します。')
    ):
        """メッセージを追加します。"""
        await ctx.respond(f'```cmd: vce_add_msg, args: {add_msg}```')
        rand_msg = get_config_json('rand_msg')
        rand_msg.append(add_msg)
        res = set_config_json('rand_msg', rand_msg)
        if res[0]:
            await ctx.channel.send(f'```「{add_msg}」を追加しました。```')
        else:
            await ctx.channel.send(f'```エラーが発生しました。\n{res[1]}```')


    @bot.slash_command(description='VC入室時のメッセージを削除します。')
    async def vce_del_msg(
        ctx: discord.ApplicationContext,
        del_number: discord.Option(int, required=True, description='/vce_list コマンドで表示した番号を選択してください。（注意：最新の番号を確認）')
    ):
        """メッセージを削除します。"""
        await ctx.respond(f'```cmd: vce_del_msg, args: {del_number}```')
        rand_msg = get_config_json('rand_msg')
        try:
            del_msg = rand_msg.pop(del_number)
        except IndexError:
            await ctx.channel.send(f'```有効な番号を入力してください。```')
            return
        res = set_config_json('rand_msg', rand_msg)
        if res[0]:
            await ctx.channel.send(f'```「{del_msg}」を削除しました。```')
        else:
            await ctx.channel.send(f'```エラーが発生しました。\n{res[1]}```')


    @bot.slash_command(description='VCとTCの紐付け一覧を表示します。（コマンド実行サーバーのみ）')
    async def vce_channel_list(ctx: discord.ApplicationContext):
        """ボイスチャンネルとテキストチャンネルの紐付けリストを表示します。（投稿したサーバー内のみ）"""
        await ctx.respond(f'```cmd: vce_channel_list```')
        channels = get_detail_vctc(bot)
        msg = ''
        for i, ch in enumerate(channels):
            sep = f'\n{"-"*30}\n' if msg != '' else ''
            vc = f"vc: {ch['vc'].category.name}/{ch['vc'].name}"    # vcカテゴリー名/チャンネル名
            tc = f"tc: {ch['tc'].category.name}/{ch['tc'].name}"    # tcカテゴリー名/チャンネル名
            msg += f"{sep}{str(i).rjust(3, ' ')}: {vc}\n{str(i).rjust(3, ' ')}: {tc}"
        await ctx.channel.send(f'```{msg}```')


    @bot.slash_command(description='ボイスチャンネルとテキストチャンネルを紐付けます。')
    async def vce_add_channel(
        ctx: discord.ApplicationContext,
        vc_id: discord.Option(
            input_type=str, description='18桁のボイスチャンネルIDを入力してください。',
            required=True, min_length=18, max_length=18
        ),
        tc_id: discord.Option(
            input_type=str,  description='18桁のテキストチャンネルIDを入力してください。',
            required=True, min_length=18, max_length=18
        )
    ):
        """ボイスチャンネルとテキストチャンネルを紐つけます。（コマンド実行サーバーのみ。VCとTCは同一サーバー）"""
        await ctx.respond(f'```cmd: vce_add_channel, vc_id: {vc_id}, tc_id: {tc_id}```')
        res = add_channel(bot, vc_id, tc_id)
        msg = '\n'.join([
            'cmd: vce_add_channel',
            f"vc_id: {vc_id}",
            f"tc_id: {tc_id}",
            f"result: {'失敗' if res['result'] == None else '成功'}",
            f"msg: {res['msg']}"
        ])
        await ctx.channel.send(f'```{msg}```')


    @bot.slash_command(description='ボイスチャンネルとテキストチャンネルの紐付けを解除します。')
    async def vce_del_channel(
        ctx: discord.ApplicationContext,
        vc_id: discord.Option(
            input_type=str, description='18桁のボイスチャンネルIDを入力してください。',
            required=True, min_lengtth=18, max_length=18
        )
    ):
        await ctx.respond(f'```cmd: vce_del_channel, vc_id: {vc_id}```')
        res = del_channel(vc_id)
        msg = '\n'.join([
            'cmd: vce_del_channel',
            f"vc_id: {vc_id}",
            f"result: {'失敗' if res['result'] == None else '成功'}",
            f"msg: {res['msg']}"
        ])
        await ctx.channel.send(f'```{msg}```')


    bot.run(get_config_json('discord_bot')['token'])


def get_msg(rand_msg: list, name: str, vc_name: str) -> str:
    """メッセージをランダムに選択し、名前とVC名を置換して返します。"""
    raw_msg = random.sample(rand_msg, 1)[0]
    return raw_msg.replace('{name}', name).replace('{vc_name}', vc_name)


def get_channel_id(vc_tc: dict, vc: int) -> Union[int, None]:
    """ボイスチャンネルIDに対応したテキストチャンネルIDを返します。"""
    return vc_tc.get(str(vc), None)


def get_detail_vctc(bot: discord.Bot) -> list[dict]:
    """サーバーで利用しているVCとTCのチャンネルオブジェクトを返します。"""
    vc_tc = get_config_json('vc_tc')
    del vc_tc['str: voice_channel']
    channels = []
    for vc_str, tc_int in vc_tc.items():
        vc = bot.get_channel(int(vc_str))
        tc = bot.get_channel(tc_int)
        if not (vc == None or tc == None):
            channels.append({'vc': vc, 'tc': tc})
    return channels


def add_channel(bot: discord.Bot, vc_id: str, tc_id: str) -> dict:
    """VCとTCの紐付けを追加して、結果を返します。"""
    vc_tc = get_config_json('vc_tc')
    vc = bot.get_channel(int(vc_id))    # voice_channelオブジェクト取得
    tc = bot.get_channel(int(tc_id))    # text_channelオブジェクト取得
    if vc == None:
        return {'result': False, 'vc': vc, 'tc': tc,
                'msg': 'vc_idからチャンネルを取得できません。無効な値です。'}
    elif vc.type.name != 'voice':
        return {'result': False, 'vc': vc, 'tc': tc,
                'msg': 'vc_idはボイスチャンネルではありません。'}
    elif tc == None:
        return {'result': False, 'vc': vc, 'tc': tc,
                'msg': 'tc_idからチャンネルを取得できません。無効な値です。'}
    elif tc.type.name != 'text':
        return {'result': False, 'vc': vc, 'tc': tc,
                'msg': 'tc_idはテキストチャンネルではありません。'}
    
    vc_tc[vc_id] = int(tc_id)
    res = set_config_json('vc_tc', vc_tc)
    if res[0]:
        return {'result': True, 'vc': vc, 'tc': tc,
                'msg': 'vc_idとtc_idを紐付けしました。'}
    else:
        return {'result': False, 'vc': vc, 'tc': tc,
                'msg': '書き込み中にエラーが発生しました。'}


def del_channel(vc_id: str) -> dict:
    """VCとTCの紐付けを解除して、結果を返します。"""
    vc_tc = get_config_json('vc_tc')
    try:
        del vc_tc[vc_id]
    except KeyError as e:
        return {'result': False, 'msg': 'vc_idの値が見つかりません。'}
    
    res = set_config_json('vc_tc', vc_tc)
    if res[0]:
        return {'result': True, 'msg': 'vc_idの紐付けを解除しました。'}
    else:
        return {'result': True, 'msg': '書き込み中にエラーが発生しました。'}


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
            json.dump(set_obj, f, indent=4, ensure_ascii=False)
            return True, ''
    except Exception as e:
            return False, str(e)


if __name__ == '__main__':
    run_bot()
