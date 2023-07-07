"""
ユーザー
    <@{USER_ID}>

テキストチャンネル・ボイスチャンネル
    <#{CHANNEL_ID}>

"""

from discord import Color, Embed
import discord

class EmbedSuccess(Embed):
    def __init__(self, description: str, **kwargs):
        dict_drops(kwargs, ['color', 'colour', 'description'])
        super().__init__(color=Color.green(), description=description, **kwargs)

class EmbedNotice(Embed):
    def __init__(self, description: str, **kwargs):
        dict_drops(kwargs, ['color', 'colour', 'description'])
        super().__init__(color=Color.yellow(), description=description, **kwargs)

class EmbedFail(Embed):
    def __init__(self, description: str, **kwargs):
        dict_drops(kwargs, ['color', 'colour', 'description'])
        super().__init__(color=Color.red(), description=description, **kwargs)

class EmbedChannelList(Embed):
    def init(self,
        ctx: discord.ApplicationContext,
        vctc_ids: list[tuple[int, int]]
    ):
        """"""
        self.description = 'ボイスチャンネルとテキストチャンネルの紐付け一覧を表示します。'
        for i, ids in enumerate(vctc_ids, 1):
            vc: discord.VoiceChannel = get_channel(ctx, ids[0])
            tc: discord.TextChannel = get_channel(ctx, ids[1])
            msg_str = f'{i}\t: [<#{vc.category.id}>/<#{vc.id}>]\t>>>\t[<#{tc.category.id}>/<#{tc.id}>]'
            del_cmd: str = f'`削除コマンド -> /vce_del_channel delete_key:{ids[2]}`'
            self.add_field(name=msg_str, value=del_cmd, inline=False)

class EmbedMessagelList(Embed):
    def init(self,
        ctx: discord.ApplicationContext,
        records: list[tuple[str, str]]
    ):
        """"""
        self.description = ' 通知メッセージの一覧を表示します。'
        for i, record in enumerate(records, 1):
            highlight_msg: str = record[0].replace('{name}', '{name}').replace('{vc_name}', '{vc_name}')
            msg_str = f'{i}\t: **{highlight_msg}**'
            del_cmd: str = f'`削除コマンド -> /vce_del_message delete_key:{record[1]}`'
            self.add_field(name=msg_str, value=del_cmd, inline=False)

class EmbedVCEntryMsg(Embed):
    def __init__(self, **kwargs):

        dict_drops(kwargs, ['color', 'colour'])

        entry_msg = ''

        super().__init__(
            color=Color.green()
            **kwargs
        )

class DeleteButton(discord.ui.View):
    @discord.ui.button(label='削除', style=discord.ButtonStyle.red)
    async def button_callback(
        self,
        button: discord.Button,
        interaction: discord.interactions.Interaction
    ):
        await interaction.message.delete()


def get_channel(
    ctx: discord.ApplicationContext,
    channel_id: str
) -> discord.CategoryChannel | discord.TextChannel | discord.VoiceChannel | None:
    """IDからチャンネルオブジェクトを返します。見つからないときは None を返します。"""
    for channel in ctx.guild.channels:
        if str(channel.id) == channel_id:
            return channel
    return None

def dict_drops(dict: dict, keys: str | list[str]):
    """辞書のキーを指定して要素を削除します。"""
    _keys = [keys] if isinstance(keys, str) else keys
    for _key in _keys:
        if _key in dict:
            dict.pop(_key)

if __name__ == '__main__':
    """Test code."""
  