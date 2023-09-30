
"""
パス
    ../database/channel.sqlite3

テーブル名
    REGISTER_CHANNEL

カラム
    GUILD_ID          : サーバーID
    VOICE_CHANNEL_ID  : ボイスチャンネルID
    TEXT_CHANNEL_ID   : テキストチャンネルID
    DELETE_KEY        : 削除キー 時間を利用したランダムSHA256ハッシュ値の先頭4桁。既存の削除キーとの衝突禁止。

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
from typing import Final, Union
from utils import app_root

SQLITE3_DIR: Final[Path] = app_root('database')

class ReturnStatus(): ...
class Successfully(ReturnStatus): ...
class AlreadyAdded(ReturnStatus): ...

class Channel():

    DATABASE_PATH: Final[Path] = SQLITE3_DIR.joinpath('channel.sqlite3')
    TABLE_NAME: Final[str] = 'REGISTER_CHANNEL'
    CREATE_TABLE_STATEMENT: Final[str] = f'''
        CREATE TABLE {TABLE_NAME}(
            GUILD_ID TEXT NOT NULL,
            VOICE_CHANNEL_ID TEXT NOT NULL,
            TEXT_CHANNEL_ID TEXT NOT NULL,
            DELETE_KEY TEXT NOT NULL
        );
    '''
    INSERT_STATEMENT: Final[str] = f'''
        INSERT INTO {TABLE_NAME} VALUES(
            :guild_id, 
            :voice_channel_id, 
            :text_channel_id, 
            :delete_key
        );
    '''
    SELECT_STATEMENT: Final[str] = f'''
        SELECT 
            *
        FROM {TABLE_NAME}
        <placeholder>;
    '''# `<placeholder>`はコード内で動的に生成します。
    DELETE_STATEMENT: Final[str] = f'''
        DELETE FROM {TABLE_NAME}
        WHERE DELETE_KEY = :delete_key;
    '''
    SQLITE_MASTER_STATEMENT: Final[str] = f'''
        SELECT * FROM sqlite_master;
    '''

    def __init__(self):
        """Constructor"""
        self.connection = sqlite3.connect(self.DATABASE_PATH)
        self.cursor = self.connection.cursor()
        self.cursor.row_factory = self._dict_factory
        self._create_table()

    def __del__(self):
        """Destructor"""
        self.cursor.close()
        self.connection.close()

    def add_channel_id(self, guild_id: Union[int, str], 
                       voice_channel_id: Union[int, str], text_channel_id: Union[int, str]) -> ReturnStatus:
        """ギルトID、ボイスチャンネルID、テキストチャンネルIDを登録します。
        ここで削除キーを付与します。重複登録は無視されます。"""
        statement: str = self.SELECT_STATEMENT.replace(
            '<placeholder>', 
            '''WHERE GUILD_ID = :guild_id
            AND VOICE_CHANNEL_ID = :voice_channel_id
            AND TEXT_CHANNEL_ID = :text_channel_id'''
        )
        parameters: dict = {
            'guild_id': str(guild_id),
            'voice_channel_id': str(voice_channel_id),
            'text_channel_id': str(text_channel_id)
        }
        try:
            self.cursor.execute(statement, parameters)
            if len(self.cursor.fetchall()) == 0:
                parameters['delete_key'] = self._generate_delete_key()
                self.cursor.execute(self.INSERT_STATEMENT, parameters)
                self.connection.commit()
                return Successfully()
            else:
                return AlreadyAdded()
        except Exception as e:
            return Exception('function failed: `Channel.add_channel`')
    
    def del_channel_id(self, delete_key: str) -> list:
        """削除キーをキーにレコードを削除して、削除したレコードを返します。"""
        # DELETE文では削除したレコードを取得できないので、予め取得しておく。
        statement: str = self.SELECT_STATEMENT.replace(
                                '<placeholder>', 'WHERE DELETE_KEY = :delete_key')
        self.cursor.execute(statement, {'delete_key': delete_key})    
        delete_records: list = self.cursor.fetchall()
        self.cursor.execute(self.DELETE_STATEMENT, {'delete_key': delete_key})
        self.connection.commit()
        return delete_records

    def get_records_by_guild_id(self, guild_id: Union[int, str]) -> list:
        """ギルドIDから登録されているレコードを返します。"""        
        statement: str = self.SELECT_STATEMENT.replace(
                         '<placeholder>', 'WHERE GUILD_ID = :guild_id')
        self.cursor.execute(statement, {'guild_id': str(guild_id)})
        return self.cursor.fetchall()
    
    def get_records_by_voice_channel_id(self, voice_channel_id: Union[int, str]) -> list:
        """ボイスチャンネルIDから登録されているレコードを返します。"""
        statement: str = self.SELECT_STATEMENT.replace(
                         '<placeholder>', 'WHERE VOICE_CHANNEL_ID = :voice_channel_id')
        self.cursor.execute(statement, {'voice_channel_id': str(voice_channel_id)})
        return self.cursor.fetchall()

    def get_records_by_delete_key(self, delete_key: str) -> list:
        """削除キーから登録されているレコードを返します。"""
        statement: str = self.SELECT_STATEMENT.replace(
                         '<placeholder>', 'WHERE DELETE_KEY = :delete_key')
        self.cursor.execute(statement, {'delete_key': delete_key})
        return self.cursor.fetchall()

    def get_records_by_guild_id_and_delete_key(self, guild_id: Union[int, str], delete_key: str) -> list:
        """ギルドIDと削除キーから登録されているレコードを返します。"""        
        statement: str = self.SELECT_STATEMENT.replace(
                         '<placeholder>', 'WHERE GUILD_ID = :guild_id AND DELETE_KEY = :delete_key')
        self.cursor.execute(statement, {'guild_id': str(guild_id), 'delete_key': delete_key})
        return self.cursor.fetchall()
    
    def _create_table(self):
        """テーブルが無ければ生成します。"""
        self.cursor.execute(self.SQLITE_MASTER_STATEMENT)
        tables: dict = [record['name'] for record in self.cursor.fetchall() if record['type'] == 'table']
        if not self.TABLE_NAME in tables:
            self.cursor.execute(self.CREATE_TABLE_STATEMENT)

    def _generate_delete_key(self) -> str:
        """テーブルにない削除キーを生成して返します。"""
        statement: str = f'SELECT DELETE_KEY FROM {self.TABLE_NAME} WHERE DELETE_KEY = :delete_key'
        while True:
            generate_delete_key: str = hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:4]
            self.cursor.execute(statement, {'delete_key': generate_delete_key})
            if len(self.cursor.fetchall()) == 0:
                return generate_delete_key
            
    def _dict_factory(self, cursor: sqlite3.Cursor, record: tuple) -> dict:
        """"""
        dict_record: dict = {}
        column_names = [c[0] for c in cursor.description]
        for column_name, value in zip(column_names, record):
            dict_record[column_name] = value
        return dict_record
    
if __name__ == '__main__':
    """Test code."""

    # channel = Channel()
    # channel.add_channel_id('guild', 'voice', 'text')
    # print(channel.get_register_channel('guild'))
    # channel.del_channel_id('7680')
