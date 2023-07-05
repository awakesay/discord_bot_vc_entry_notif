
"""
パス
    ./db/channel.sqlite3

カラム
    GUILD_ID    サーバーID
    VC_ID       ボイスチャンネルID
    TC_ID       テキストチャンネルID
    DEL_KEY     削除キー 時間を利用したランダムSHA256ハッシュ値の先頭4桁。既存の削除キーとの衝突禁止。

SQLITE3
    値の型
        NULL    : NULL値
        INTEGER : 符号付数値
        REAL    : 浮動小数点数
        TEXT    : テキスト（UTF-8、UTF-16LE、UTF-16BE）
        BLOB    : Binary Large Objectの略。バイナリをそのまま格納する。

    カラムの型
        TEXT    : INTEGER型、REAL型の場合、TEXT型に変換する。
        NUMERIC : TEXT型の数値の場合は、INTEGER型かREAL型に変換する。
        INTEGER : TEXT型、REAL型の数値は、INTEGER型に変換する。
        REAL    : INTEGER型の場合、REAL型に変換する。
        NONE    : 変換は行われない。
"""

import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Final
import discord
from discord_util import get_channel

class Channel():

    DATABASE_PATH: Final[Path] = Path(__file__).parents[1].joinpath('db', 'channels.sqlite3')
    TABLE_NAME: str = 'ID_REGISTER'

    def __init__(self):
        
        self._conn = sqlite3.Connection(self.DATABASE_PATH)
        self._cur = self._conn.cursor()

        # テーブル存在確認(なければ追加)
        if not self._exists_table(self.TABLE_NAME):
            self._create_table()

    def __del__(self):
        """Destructor"""
        self._cur.close()
        self._conn.close()

    def add_channel_ids(self,
            guild_id: int,
            voice_channel_id: int,
            text_channel_id: int
        ) -> bool | None:
            """idをテーブルに追加します。すでにある場合は False 、エラーが発生した場合は None を返します。"""
            exists_id_sql: str = f'''
                SELECT 
                    COUNT(*)
                FROM
                    {self.TABLE_NAME}
                WHERE
                    GUILD_ID = '{guild_id}'
                    AND VC_ID = '{voice_channel_id}'
                    AND TC_ID = '{text_channel_id}';
            '''
            self._cur.execute(exists_id_sql)
            record_count = self._cur.fetchall()[0][0]

            if record_count == 0:
                
                delete_key: str = self._get_delete_key()
                add_id_sql: str = f'''
                    INSERT INTO {self.TABLE_NAME} VALUES(
                        '{guild_id}',
                        '{voice_channel_id}',
                        '{text_channel_id}',
                        '{delete_key}'
                    );
                '''
                try:
                    self._cur.execute(add_id_sql)
                    self._conn.commit()
                    return True
                
                except Exception as e:
                    return None
            else:
                return False
        
    def del_channel_ids(self,
        ctx: discord.ApplicationContext,
        delete_key: str
    ) -> list[bool | None, discord.VoiceChannel | None, discord.TextChannel | None]:
        """削除成功 True, 削除するものがない False, エラー None """

        def _get_record_count(delete_key: str) -> int:
            registered_delete_keys_sql: str = f'''
                SELECT
                    VC_ID,
                    TC_ID,
                    DEL_KEY
                FROM
                    {self.TABLE_NAME}
                WHERE
                    DEL_KEY = '{delete_key}';
            '''
            self._cur.execute(registered_delete_keys_sql)
            fetch = self._cur.fetchall()
            return fetch

        before = _get_record_count(delete_key)
        if len(before) == 0:
            return False, None, None

        delete_id_sql: str = f'''
            DELETE FROM {self.TABLE_NAME}
            WHERE
                DEL_KEY = '{delete_key}';
        '''
        try:
            self._cur.execute(delete_id_sql)
            self._conn.commit()

            after = _get_record_count(delete_key)
            if len(after) == 0:
                vc = get_channel(ctx, before[0][0])
                tc = get_channel(ctx, before[0][1])
                return True, vc, tc
            
        except Exception as e:
            return None, None, None

    def get_channel_list(self, ctx: discord.ApplicationContext) -> list[tuple[int, int]]:
        """ギルドIDのボイスチャンネルIDとテキストチャンネルIDを返します。
        Returns [
            (voice channel id, text channel id),
            ...
        ]
        """
        guild_vc_tc_sql: str = f'''
            SELECT
                VC_ID,
                TC_ID,
                DEL_KEY
            FROM
                {self.TABLE_NAME}
            WHERE
                GUILD_ID = '{ctx.guild.id}';
        '''
        self._cur.execute(guild_vc_tc_sql)
        records: list = self._cur.fetchall()
        return records

    def _create_table(self) -> bool:
        """ギルドID・チャンネルIDを格納するテーブルを生成します。"""
        create_table_sql: str = f'''
            CREATE TABLE {self.TABLE_NAME}(
                GUILD_ID TEXT NOT NULL,
                VC_ID TEXT NOT NULL,
                TC_ID TEXT NOT NULL,
                DEL_KEY TEXT NOT NULL
            );
            '''
        try:
            self._cur.execute(create_table_sql)
            return True
        
        except Exception as e:
            return False
        
    def _exists_table(self, table_name: str) -> bool:
        """"""
        table_names = [t['name'] for t in self._get_sqlite_master() if t['type'] == 'table']
        return table_name in table_names
    
    def _get_delete_key(self) -> str:

        registered_delete_keys_sql: str = f'''
            SELECT
                DEL_KEY
            FROM
                {self.TABLE_NAME}
        '''
        
        self._cur.execute(registered_delete_keys_sql)
        registered_delete_keys = [key[0] for key in self._cur.fetchall()]
        
        while True:
            delete_key: str = hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:4]
            if delete_key not in registered_delete_keys:
                return delete_key        

    def _get_sqlite_master(self) -> list[dict[str, str]]:
        """"""
        self._cur.execute('SELECT * FROM sqlite_master')
        column_names = [column[0] for column in self._cur.description]
        sqlite_master = []
        for record in self._cur.fetchall():
            sqlite_master.append({k: v for k, v in zip(column_names, record)})
        return sqlite_master

if __name__ == '__main__':
    """Test code."""
    


