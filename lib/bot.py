


import platform
from typing import Any, Final, Union
import discord
from channel import Channel, ReturnStatus, Successfully, AlreadyAdded
from utils import get_bot_token

VC_ENTRY_POST_TEXT: Final[str] = f'<username> has joined \
                                  the <voice_channel> voice channel.'

def run_bot():

    db_channel = Channel()

    # 面倒なので権限関係は調べてません。とりあえず全権を与えといてください。
    # ボットには`Intents`を付与しておいてください。
    intents = discord.Intents.all()
    intents.message_content = True
    bot = discord.Bot(intents=intents)
    
    # Event functions =========================================================

    @bot.event
    async def on_ready():
        """起動イベント"""
        # 起動メッセージ表示
        launch_message: list[str] = [
            'discord_bot_vc_entry_notif',
            f'python_version: {platform.python_version()}',
            f'pycord_version: {discord.__version__}'
        ]
        max_length: int = max(len(s) for s in launch_message)
        sep: str = '-' * max_length + '\n'
        print(sep + '\n'.join(launch_message) + '\n' + sep)

    @bot.event
    async def on_voice_state_update(member: discord.Member, 
                                    before: discord.VoiceState,
                                    after: discord.VoiceState):
        """ボイスチャンネル状態変化イベント"""
        if after.channel is None:   # 退出
            return          
        elif member.bot:            # ボット
            return
        register_records: list = db_channel.get_records_by_voice_channel_id(str(after.channel.id))
        if len(register_records) == 0:
            return
        
        post_description: str = VC_ENTRY_POST_TEXT.replace('<username>', member.nick) \
                                                  .replace('<voice_channel>', after.channel.name)
        edit_description: str = VC_ENTRY_POST_TEXT.replace('<username>', discord_notation(member, True)) \
                                                  .replace('<voice_channel>', discord_notation(after.channel))
        post_embed = discord.Embed(colour=discord.Color.green(), description=post_description)
        edit_embed = discord.Embed(colour=discord.Color.green(), description=edit_description)
        for text_channel_id in [int(record['TEXT_CHANNEL_ID']) for record in register_records]:
            post_channel: discord.TextChannel = bot.get_channel(text_channel_id)
            post_message = await post_channel.send(embed=post_embed)
            await post_message.edit(embed=edit_embed)
    
    # Slash command functions =================================================

    @bot.slash_command(description='Add voice and text channel.')
    async def voice_entry_add_channel(ctx: discord.ApplicationContext,
                                      voice_channel_id: discord.Option(
                                          str, required=True, description='Enter voice channel id.'),
                                      text_channel_id: discord.Option(
                                          str, required=True, description='Enter text channel id.')):
        voice_channel_ids: list[str] = [str(ch.id) for ch in ctx.guild.channels if isinstance(ch, discord.VoiceChannel)]
        text_channel_ids: list[str] = [str(ch.id) for ch in ctx.guild.channels if isinstance(ch, discord.TextChannel)]
        is_valid_voice_channel: bool = voice_channel_id in voice_channel_ids
        is_valid_text_channel: bool = text_channel_id in text_channel_ids
        if not all((is_valid_voice_channel, is_valid_text_channel)):
            failed_embed = discord.Embed(colour=discord.Colour.red(), description='Invalid channel id.')
            await ctx.respond(embed=failed_embed, ephemeral=True)
            return
        
        response: ReturnStatus = db_channel.add_channel_id(ctx.guild.id, voice_channel_id, text_channel_id)
        if isinstance(response, Successfully):
            response_embed = discord.Embed(colour=discord.Colour.green(), description='Added channel.')
        elif isinstance(response, AlreadyAdded):
            response_embed = discord.Embed(colour=discord.Colour.yellow(), description='Channel has already been added.')
        await ctx.respond(embed=response_embed, ephemeral=True)
    
    @bot.slash_command(description='remove voice and text channel.')
    async def voice_entry_remove_channel(ctx: discord.ApplicationContext,
                                         delete_key: discord.Option(str, required=True, 
                                                                         description='Enter delete key. Check list.')):
        records: list = db_channel.get_records_by_guild_id_and_delete_key(ctx.guild.id, delete_key)
        if len(records) == 0:
            post_embed = discord.Embed(colour=discord.Colour.yellow(), description='Not found delete key.')
            await ctx.respond(embed=post_embed, ephemeral=True)
            return
        elif len(records) == 1:
            record = db_channel.del_channel_id(delete_key)[0]
            voice_channel: discord.VoiceChannel = bot.get_channel(int(record['VOICE_CHANNEL_ID']))
            text_channel: discord.TextChannel = bot.get_channel(int(record['TEXT_CHANNEL_ID']))
            post_embed = discord.Embed(colour=discord.Colour.yellow(), description='Channel deleted.')
            post_embed.add_field(name='Voice channel', value=discord_notation(voice_channel), inline=False)
            post_embed.add_field(name='Text channel', value=discord_notation(text_channel), inline=False)
            await ctx.respond(embed=post_embed, ephemeral=True)

    @bot.slash_command(description='Display channel list.')
    async def voice_entry_channel_list(ctx: discord.ApplicationContext):
        """ボイスチャンネルとテキストチャンネルの紐付けリストを表示します。（コマンドを実行したサーバー内のみ）"""
        records = db_channel.get_records_by_guild_id(ctx.guild.id)
        post_embed = discord.Embed(colour=discord.Colour.green(), description='Channel list.')
        for record in records:
            voice_channel = bot.get_channel(int(record['VOICE_CHANNEL_ID']))
            text_channel = bot.get_channel(int(record['TEXT_CHANNEL_ID']))
            post_embed.add_field(name=f'{discord_notation(voice_channel.category)}.{discord_notation(voice_channel)}' \
                                    + f'\t->\t{discord_notation(text_channel.category)}.{discord_notation(text_channel)}',
                                 value=f'\tDelete_key: {record["DELETE_KEY"]}')
        await ctx.respond(embed=post_embed, ephemeral=True)

    bot.run(get_bot_token())


# Common funcions =============================================================

def discord_notation(obj: Union[Any, None] = None, is_member: bool = False) -> str:
    """Discordの表記に変更します。"""
    if obj is None or not hasattr(obj, 'id'):
        if is_member:
            return '<@0>'
        else:
            return '<#0>'
    
    if isinstance(obj, discord.Member):
        prefix = '@'
    else:
        prefix = '#'

    return f'<{prefix}{obj.id}>'
    
if __name__ == '__main__':

    run_bot()
