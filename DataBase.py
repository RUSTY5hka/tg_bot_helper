import sqlite3
import config


class Data:
    def __init__(self):
        self.db_way = config.db_way
        self.db_name = config.db_name

    def execute_request(self, execute: str, return_value: bool = False, parametrs: list = None):
        con = sqlite3.connect(self.db_way)
        cur = con.cursor()
        if return_value:
            value = cur.execute(execute).fetchall()
        elif parametrs:
            cur.execute(execute, tuple(parametrs))
        else:
            cur.execute(execute)
        con.commit()
        con.close()
        if return_value:
            return value

    def create_table(self, name_column: list, type_column: list):
        execute = ''
        for i in range(0, len(name_column) - 1):
            execute += name_column[i] + ' ' + type_column[i] + ','
        execute += name_column[-1] + ' ' + type_column[-1]
        execute = f'CREATE TABLE IF NOT EXISTS {self.db_name}({execute});'
        Data().execute_request(execute=execute)

    def insert_row(self, name_column: list, value_column: list):
        names = ''
        values = ''
        for i in range(0, len(name_column) - 1):
            names += name_column[i] + ','
            values += '?,'
        names+=name_column[-1]
        values+='?'
        execute = f'''INSERT INTO {self.db_name} ({names}) VALUES ({values})'''
        Data().execute_request(execute=execute, parametrs=value_column)

    def select_from_table(self, select_column: list, elements_conditions: list, elements_values: list):
        execute = ''
        selects = ''
        condition = ''
        for i in range(0, len(select_column) - 1):
            selects += select_column[i] + ','
        selects += select_column[-1]
        for i in range(0, len(elements_conditions) - 1):
            condition += elements_conditions[i] + '=' + elements_values[i] + ','
        condition += elements_conditions[-1] + '=' + elements_values[-1]
        execute = f'SELECT {selects} FROM {self.db_name} WHERE {condition}'
        if Data().execute_request(execute=execute, return_value=True)[0][0] is None:
            return 0
        return Data().execute_request(execute=execute, return_value=True)[0][0]
