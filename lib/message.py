

"""
パス
    ./db/message.sqlite3

カラム
    GUILD_ID    サーバーID
    MSG         通知メッセージ（{name} | {vcname}
    DEL_KEY     削除キー  時間を利用したランダムSHA256ハッシュ値の先頭4桁。既存の削除キーとの衝突禁止。
"""

import hashlib
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Final
import discord

class Message():

    DATABASE_PATH: Final[Path] = Path(__file__).parents[1].joinpath('db', 'message.sqlite3')
    TABLE_NAME: str = 'MSG_REGISTER'
    DEFAULT_MSG: str = '{name} が {vc_name} に入室しました。'

    def __init__(self):

        self._conn = sqlite3.Connection(self.DATABASE_PATH)
        self._cur = self._conn.cursor()

        # テーブル存在確認（なければ追加）
        if not self._exists_table(self.TABLE_NAME):
            self._create_table()

    def __del__(self):
        """Destructor"""
        self._cur.close()
        self._conn.close()

    def add_msg(self,
        ctx: discord.ApplicationContext,
        msg: str
    ) -> bool:
        """idをテーブルに追加します。すでにある場合は False 、エラーが発生した場合は None を返します。
        bool: {name}, bool: {vc_name} の存在有無"""
        
        exists_msg_sql: str = f'''
            SELECT 
                COUNT(*)
            FROM
                {self.TABLE_NAME}
            WHERE
                GUILD_ID = '{ctx.guild.id}'
                AND MSG = '{msg}';
        '''
        self._cur.execute(exists_msg_sql)
        count = self._cur.fetchall()[0][0]
        if count != 0:
            return False

        delete_key: str = self._get_delete_key()
        add_msg_sql: str = f'''
            INSERT INTO {self.TABLE_NAME} VALUES(
                '{ctx.guild.id}',
                '{msg}',
                '{delete_key}'
            );
        '''
        try:
            self._cur.execute(add_msg_sql)
            self._conn.commit()
            return True
    
        except Exception as e:
            return None
    
    def del_msg(self,
        delete_key: str
    ) -> list[bool, str]:
        """削除成功 True, 削除するものがない False, エラー None """

        def _get_record_count(delete_key: str) -> list[str, str]:
            registered_delete_keys_sql: str = f'''
                SELECT
                    MSG,
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
            return False, ''

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
                return True, before[0][0]
            
        except Exception as e:
            return None, before[0][0]
        
    def get_message_list(self, ctx: discord.ApplicationContext) -> list[tuple[int, int]]:
        """ギルドIDのボイスチャンネルIDとテキストチャンネルIDを返します。
        Returns [
            (guild id, message),
            ...
        ]
        """
        guild_msg_sql: str = f'''
            SELECT
                MSG,
                DEL_KEY
            FROM
                {self.TABLE_NAME}
            WHERE
                GUILD_ID = '{ctx.guild.id}';
        '''
        self._cur.execute(guild_msg_sql)
        records: list = self._cur.fetchall()
        return records

    def get_random_message(self, member: discord.Member) -> str:

        guild_msg_sql: str = f'''
            SELECT
                MSG
            FROM
                {self.TABLE_NAME}
            WHERE
                GUILD_ID = '{member.guild.id}';
        '''
        self._cur.execute(guild_msg_sql)
        msgs: list = [record[0] for record in self._cur.fetchall()]
        if len(msgs) == 0:
            return self.DEFAULT_MSG
        else:
            return random.choice(msgs)

    def _create_table(self) -> bool:
        """ギルドID・チャンネルIDを格納するテーブルを生成します。"""
        create_table_sql: str = f'''
            CREATE TABLE {self.TABLE_NAME}(
                GUILD_ID TEXT NOT NULL,
                MSG TEXT NOT NULL,
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
    




