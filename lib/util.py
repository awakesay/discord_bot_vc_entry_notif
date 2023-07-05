



from pathlib import Path
import json5

def get_bot_token() -> str:
    """./Config/discord.json5 からボットのトークンを読み出して返します。"""
    path = Path(__file__).parents[1].joinpath('config', 'discord.json5')
    with open(path, 'r', encoding='utf-8') as f:
        return json5.load(f)['bot_token']

if __name__ == '__main__':

    bot_token = get_bot_token()
    print(bot_token)
