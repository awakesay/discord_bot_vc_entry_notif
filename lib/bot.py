
"""
他の関数に切り出してEmbedを返す。
"""

import platform
import random
import discord
from channel import Channel
from discord_util import (
    EmbedSuccess,
    EmbedNotice,
    EmbedFail,
    EmbedChannelList,
    EmbedMessagelList,
    get_channel
)
from discord_util import DeleteButton
from message import Message
from util import get_bot_token

def run_bot():

    # IDテーブル
    db_channel = Channel()
    db_message = Message()

    # ボット権限付与 & ボットオブジェクト生成
    intents = discord.Intents.all()
    intents.message_content = True
    bot = discord.Bot(intents=intents)
    
    # ======================================================================
    # Event functions.
    @bot.event
    async def on_ready():
        """起動イベント"""
        # 起動メッセージ
        print(f'{"-"*30}\non_ready: discord_bot_vc_entry')
        print(f'python_version: {platform.python_version()}')
        print(f'pycord_version: {discord.__version__}')
        # データ初期化
        # TODO: データベース内のしかるべきテーブルを初期化


    @bot.event
    async def on_voice_state_update(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        """ボイスチャンネル入退室イベント"""
        # 入室と移動を処理。
        if after.channel is not None:

            vctc_ids = db_channel.get_channel_list(member)
            post_tc = [id[1] for id in vctc_ids if id[0] == str(after.channel.id)]

            if len(post_tc) == 0:
                return
        
            post_msg: str = db_message.get_random_message(member)
            edit_msg: str = post_msg
            post_msg = post_msg.replace('{name}', member.nick).replace('{vc_name}', after.channel.name)
            edit_msg = edit_msg.replace('{name}', f'<@{member.id}>').replace('{vc_name}', f'<#{after.channel.id}>')
            
            # 
            for tc_id in post_tc:
                post_channel = bot.get_channel(int(tc_id))
                msg = await post_channel.send(embed=EmbedSuccess(post_msg)) # IDのままだと通知が数値の羅列になるので、投稿はベタ書きメッセージ。
                await msg.edit(embed=EmbedSuccess(edit_msg))                # その後、すぐにIDに書き換え。クライアントソフトで見るとエイリアスに入れ替わります。
            
    # ======================================================================
    # Slash command functions.
    
    @bot.slash_command(description='VC入室時のメッセージ一覧を表示します。')
    async def vce_message_list(ctx: discord.ApplicationContext):
        """メッセージ一覧を表示します。"""

        records: list[tuple[str, str]] = db_message.get_message_list(ctx)

        embed = EmbedMessagelList()
        embed.init(ctx, records)
        await ctx.respond(embed=embed, ephemeral=True)


    @bot.slash_command(description='ボイスチャンネル入室時の通知メッセージを追加します。')
    async def vce_add_message(
        ctx: discord.ApplicationContext,
        msg: discord.Option(str, required=True,
            description='キーワード: {name} はユーザー名、 {vc_name} はボイスチャンネル名に置き換えます。')
    ):
        """通知メッセージを追加します。"""

        res = db_message.add_msg(ctx, msg)

        highlight_msg: str = msg.replace('{name}', '{name}').replace('{vc_name}', '{vc_name}')

        match res:
            case True:  # 追加成功
                await ctx.respond(
                    embed=EmbedSuccess(f'[**{highlight_msg}**]\nを通知メッセージリストに追加しました。'),
                    ephemeral=True)
            case False: # 既に登録済み
                await ctx.respond(
                    embed=EmbedNotice(f'[**{highlight_msg}**]\nは既に通知メッセージリストに存在します。'),
                    ephemeral=True)
            case None:  # エラー
                await ctx.respond(
                    embed=EmbedFail(f'[**{highlight_msg}**]\nを通知メッセージリストの追加に失敗しました。'),
                    ephemeral=True)
            

    @bot.slash_command(description='ボイスチャンネル入室時の通知メッセージを削除します。')
    async def vce_del_message(
        ctx: discord.ApplicationContext,
        delete_key: discord.Option(str, required=True, description='削除キー。（ /vce_msg_list コマンドで確認できます。）')
    ):
        
        res, msg = db_message.del_msg(delete_key)

        highlight_msg: str = msg.replace('{name}', '__`{name}`__').replace('{vc_name}', '__`{vc_name}`__')

        match res:
            case True:  # 追加成功
                await ctx.respond(
                    embed=EmbedSuccess(f'[**{highlight_msg}**]\nを通知メッセージリストから削除しました。'),
                    ephemeral=True)
            case False: # 既に登録済み
                await ctx.respond(
                    embed=EmbedNotice(f'[**{highlight_msg}**]\nは既に通知メッセージリストから削除されています。'),
                    ephemeral=True)
            case None:  # エラー
                await ctx.respond(
                    embed=EmbedFail(f'[**{highlight_msg}**]\nを通知メッセージリストからの削除に失敗しました。'),
                    ephemeral=True)


    @bot.slash_command(description='ボイスチャンネルとテキストチャンネルの紐付け一覧を表示します。')
    async def vce_channel_list(ctx: discord.ApplicationContext):
        """ボイスチャンネルとテキストチャンネルの紐付けリストを表示します。（コマンドを実行したサーバー内のみ）"""
        #await ctx.respond(content=f'```cmd: vce_channel_list```', ephemeral=True)
        
        vctc_ids: list[tuple[int, int]] = db_channel.get_channel_list(ctx)

        embed = EmbedChannelList()
        embed.init(ctx, vctc_ids)
        await ctx.respond(embed=embed, ephemeral=True)


    @bot.slash_command(description='ボイスチャンネルとテキストチャンネルを紐付けます。')
    async def vce_add_channel(
        ctx: discord.ApplicationContext,
        vc_id: discord.Option(str, required=True,   
                              description='ボイスチャンネルIDを入力してください。'),
        tc_id: discord.Option(str, required=True,   
                              description='テキストチャンネルIDを入力してください。')
    ):
        # IDチェック（Guild内のチャンネルに引数のIDが存在するか確認します。）
        vc_channel_ids: list[int] = [str(channel.id) for channel in ctx.guild.channels if isinstance(channel, discord.VoiceChannel)]
        tc_channel_ids: list[int] = [str(channel.id) for channel in ctx.guild.channels if isinstance(channel, discord.TextChannel)]
        if vc_id not in vc_channel_ids or tc_id not in tc_channel_ids:
            await ctx.respond(embed=EmbedFail('無効なチャンネルIDです。'),
                              ephemeral=True)   # コマンド利用者だけが見える返信。
            return
        
        # IDをデータベースに追加して、結果を取得する。
        res: bool | None = db_channel.add_channel_ids(guild_id=str(ctx.guild.id), 
                                                      voice_channel_id=vc_id, text_channel_id=tc_id)
        
        # ボイスチャンネルとテキストチャンネルのカテゴリIDを取得
        vc_cat_id: str = get_channel(ctx, vc_id).category.id
        tc_cat_id: str = get_channel(ctx, tc_id).category.id

        # ユーザーへのメッセージ（結果で分岐）
        match res:
            case True:  # 追加成功
                await ctx.respond(
                    embed=EmbedSuccess(f'[<#{vc_cat_id}> / <#{vc_id}>] と [<#{tc_cat_id}> / <#{tc_id}>] を紐付けました。'),
                    ephemeral=True)
            case False: # 既に登録済み
                await ctx.respond(
                    embed=EmbedNotice(f'[<#{vc_cat_id}> / <#{vc_id}>] と [<#{tc_cat_id}> / <#{tc_id}>] は既に紐付いています。'),
                    ephemeral=True)
            case None:  # エラー
                await ctx.respond(
                    embed=EmbedFail(f'[<#{vc_cat_id}> / <#{vc_id}>] と [<#{tc_cat_id}> / <#{tc_id}>] の紐付けに失敗しました。'),
                    ephemeral=True)


    @bot.slash_command(description='ボイスチャンネルとテキストチャンネルの紐付けを解除します。')
    async def vce_del_channel(
        ctx: discord.ApplicationContext,
        delete_key: discord.Option(
            input_type=str, description='削除キー。（ /vce_channel_list コマンドで確認できます。）',
            required=True, min_lengtth=18, max_length=19
        )
    ):
        # 削除キーのレコードをテーブルから削除して、成否とボイスチャンネルとテキストチャンネルを取得する。
        res, vc, tc = db_channel.del_channel_ids(ctx, delete_key)

        match res:
            case True:  # 追加成功
                await ctx.respond(
                    embed=EmbedSuccess(f'[<#{vc.category.id}> / <#{vc.id}>] と [<#{tc.category.id}> / <#{tc.id}>] の紐付けを解除しました。'),
                    ephemeral=True)
            case False: # 既に登録済み
                await ctx.respond(
                    embed=EmbedNotice(f'無効な削除キーです。'),
                    ephemeral=True)
            case None:  # エラー
                await ctx.respond(
                    embed=EmbedFail(f'[<#{vc.category.id}> / <#{vc.id}>] と [<#{tc.category.id}> / <#{tc.id}>] の紐付けに失敗しました。'),
                    ephemeral=True)


    bot.run(get_bot_token())

if __name__ == '__main__':

    run_bot()
