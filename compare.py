import re
import argparse
import pymysql

__version__ = "1.0.0"

parser = argparse.ArgumentParser(description='说明：对比mysql数据库结构,生成差异sql, 删表/删字段/索引操作会自动加注释，需要自行判断')
parser.add_argument('-H', '--host', type=str, required=True, help='目标数据库地址')
parser.add_argument('-P', '--port', type=int, default=3306, help='目标数据库端口')
parser.add_argument('-d', '--db', type=str, required=True, help='目标数据库名称')
parser.add_argument('-u', '--username', type=str, required=True, help='目标数据库用户名')
parser.add_argument('-p', '--password', type=str, required=True, help='目标数据库密码')


parser.add_argument('-RH', '--ref-host', type=str, required=True, help='参考数据库地址')
parser.add_argument('-RP', '--ref-port', type=int, default=3306, help='参考数据库端口')
parser.add_argument('-rd', '--ref-db', type=str, required=True, help='参考数据库名称')
parser.add_argument('-ru', '--ref-username', type=str, required=True, help='参考数据库用户名')
parser.add_argument('-rp', '--ref-password', type=str, required=True, help='参考数据库密码')

parser.add_argument('--ignore-comment', action='store_true', help='是否忽略注释，默认不忽略')

args = parser.parse_args()

host=args.host  
port=args.port
database=args.db
username=args.username
password=args.password

reference_host=args.ref_host
reference_port=args.ref_port
reference_database=args.ref_db
reference_username=args.ref_username
reference_password=args.ref_password
ignore_comment=args.ignore_comment


DEFAULT_KEY_WORDS = [
    "CURRENT_TIMESTAMP"
]

def get_tables(cursor):
    '''
        获取指定数据库所有表
    '''
    cursor.execute("show tables")
    tables = cursor.fetchall()
    tables = [d[0] for d in tables]
    return tables

def make_create_table_sql(add_tables, cursor_reference):
    res = []
    pattern = re.compile("AUTO_INCREMENT=\d+ ")
    # 生成建表语句
    for add_table in add_tables:
        cursor_reference.execute("show create table {};".format(add_table))
        data = cursor_reference.fetchone()
        create_table_segment = data[1] + ";"
        res.append(pattern.sub("", create_table_segment))
    return res

def make_drop_table_sql(drop_tables):
    res = []
    for drop_table in drop_tables:
        res.append("-- DROP TABLE `{}`;".format(drop_table))
    return res

def make_add_column_sql(table, reference_columns_dict, add_columns):
    res = []
    for column in add_columns:
        column_detail = reference_columns_dict.get(column)
        if column_detail is not None:
            sql = "ALTER TABLE `{}`.`{}` ADD COLUMN {};".format(database, table, make_sql_from_column_detail(column_detail))
            res.append(sql)
    return res

def make_drop_column_sql(table, drop_columns):
    res = []
    for column in drop_columns:
        sql = "-- ALTER TABLE `{}`.`{}` DROP COLUMN {};".format(database, table, column)
        res.append(sql)
    return res

def make_change_column_sql(table, change_columns, reference_columns_dict, columns_dict):
    res = []
    for column in change_columns:
        column_detail = columns_dict.get(column)
        reference_column_detail = reference_columns_dict.get(column)
        sql = make_sql_from_column_detail(column_detail)
        reference_sql = make_sql_from_column_detail(reference_column_detail)
        if sql != reference_sql:
            full_sql = "ALTER TABLE `{}`.`{}` MODIFY COLUMN {};".format(database, table, reference_sql)
            res.append(full_sql)
    return res


def make_sql_from_column_detail(column_detail):
    '''
        生成字段定义
        `name` varchar(64) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT ''
    '''
    sql_list = []
    sql_list.append(column_detail[0])
    pattern = re.compile("int\(\d+\)")
    sql_list.append(pattern.sub("int", column_detail[1]))
    if column_detail[6] is not None:
        sql_list.append("CHARACTER SET {}".format(column_detail[6]))
    if column_detail[7] is not None:
        sql_list.append("COLLATE {}".format(column_detail[7]))
    if column_detail[2] == "NO":
        sql_list.append("NOT NULL")
    if column_detail[3] is not None and column_detail[3] not in DEFAULT_KEY_WORDS:
        sql_list.append("DEFAULT '{}'".format(column_detail[3]))
    elif column_detail[3] is not None and column_detail[3] in DEFAULT_KEY_WORDS:
        sql_list.append("DEFAULT {}".format(column_detail[3]))
    if column_detail[4] != '':
        # add extra
        sql_list.append(column_detail[4].replace("DEFAULT_GENERATED", ""))
    if column_detail[5] != '':
        # add comment
        if not ignore_comment:
            sql_list.append("COMMENT {}".format(repr(column_detail[5])))
    return " ".join(sql_list)



def get_table_columns(database, table, cursor):
    sql = '''
    select
        COLUMN_NAME,
        COLUMN_TYPE, 
        IS_NULLABLE, 
        COLUMN_DEFAULT, 
        EXTRA,COLUMN_COMMENT, 
        CHARACTER_SET_NAME, 
        COLLATION_NAME
    from information_schema.columns where table_schema='{}' and table_name='{}'
    '''.format(database, table)
    cursor.execute(sql)
    data = cursor.fetchall()
    return data

def get_table_indexes(change_table, cursor):
    '''
        返回格式：
        {
            'PRIMARY': 'ALTER TABLE device_damage ADD PRIMARY KEY (id, user_id);', 
            'user_id': 'ALTER TABLE device_damage ADD INDEX user_id (user_id, device_id);', 
            'user_id_2': 'ALTER TABLE device_damage ADD INDEX user_id_2 (user_id);', 
            'library_id': 'ALTER TABLE device_damage ADD INDEX library_id (library_id);', 
            'created_at': 'ALTER TABLE device_damage ADD INDEX created_at (created_at);', 
            'content': 'ALTER TABLE device_damage ADD INDEX content (content);'
        }
    '''
    sql = 'show index from {}'.format(change_table)
    cursor.execute(sql)
    data = cursor.fetchall()
    keys_map = {}
    for item in data:
        index_name = item[2]
        is_unique = item[1] == 0
        column = item[4]
        is_fulltext = item[10] == 'FULLTEXT'
        index = {
            'index_name': index_name,
            'is_unique': is_unique,
            'column': column,
            'is_fulltext': is_fulltext
        }
        keys_map.setdefault(index_name, []).append(index)
    res = {}
    for key in keys_map.keys():
        sql = get_index_segment(keys_map.get(key))
        res[key] = sql
    return res

def get_index_segment(index_columns):
    data = index_columns[0]
    columns = ', '.join([ '`{}`'.format(d['column']) for d in index_columns])
    if data.get('index_name') == 'PRIMARY':
        return "ADD PRIMARY KEY ({});".format(columns)
    if data.get('is_unique'):
        return "ADD UNIQUE KEY {} ({});".format(data['index_name'], columns)
    if data.get('is_fulltext'):
        return "ADD FULLTEXT INDEX {} ({});".format(data['index_name'], columns)
    return "ADD INDEX {} ({});".format(data['index_name'], columns)

def make_add_index_sql(add_indexes, indexes):
    res = []
    for key in add_indexes:
        res.append("-- " + indexes.get(key))
    return res

def make_drop_index_sql(change_table, drop_indexes):
    res = []
    for key in drop_indexes:
        res.append(get_drop_sql_by_key(change_table, key))
    return res

def make_change_index_sql(change_table, change_indexes, indexes, reference_indexes):
    res = []
    for key in change_indexes:
        if indexes.get(key) != reference_indexes.get(key):
            res.append('-- ALTER TABLE `{}`.`{}` DROP INDEX `{}`, {}'.format(database, change_table, key, reference_indexes.get(key)))
    return res     

def get_drop_sql_by_key(change_table, key):
    if key == 'PRIMARY':
        return "-- ALTER TABLE `{}`.`{}` DROP PRIMARY KEY;".format(database, change_table)
    return "-- ALTER TABLE `{}`.`{}` DROP INDEX {};".format(database, change_table, key)

db = pymysql.connect(host=host,
                     port=port,
                     user=username,
                     password=password,
                     database=database)

db_reference = pymysql.connect(host=reference_host,
                     port=reference_port,
                     user=reference_username,
                     password=reference_password,
                     database=reference_database)
# 使用 cursor() 方法创建一个游标对象 cursor
cursor = db.cursor()
cursor_reference = db_reference.cursor()

# 生成建表语句，删表语句
tables = get_tables(cursor)
reference_tables = get_tables(cursor_reference)
add_tables = [t for t in reference_tables if t not in tables]
drop_tables = [t for t in tables if t not in reference_tables]
change_tables = [t for t in tables if t in reference_tables]

# 生成建表语句

create_table_sqls = make_create_table_sql(add_tables, cursor_reference)
if len(create_table_sqls) > 0:
    print("-- ----------create tables-------------")
    print('\n'.join(create_table_sqls))
    print("-- ------------------------------------")

# 生成删表语句

drop_table_sqls = make_drop_table_sql(drop_tables)
if len(drop_table_sqls) > 0:
    print("-- -----------drop tables-- -----------")
    print('\n'.join(drop_table_sqls))
    print("-- ------------------------------------")


print("-- ----------modify tables-------------")
for change_table in change_tables:
    columns = get_table_columns(database, change_table, cursor)
    reference_columns = get_table_columns(reference_database, change_table, cursor_reference)
    columns_dict = {d[0]: d for d in columns}
    reference_columns_dict = {d[0]: d for d in reference_columns}
    
    add_columns = [d for d in reference_columns_dict.keys() if d not in columns_dict.keys()]
    drop_columns = [d for d in columns_dict.keys() if d not in reference_columns_dict.keys()]
    change_columns = [d for d in columns_dict.keys() if d in reference_columns_dict.keys()]
    # 生成字段新增语句
    add_column_sqls = make_add_column_sql(change_table, reference_columns_dict, add_columns)
    # 生成字段删除语句
    drop_column_sqls = make_drop_column_sql(change_table, drop_columns)
    # 生成字段变更语句
    change_column_sqls = make_change_column_sql(change_table, change_columns, reference_columns_dict, columns_dict)

    # 获取表索引列表
    indexes = get_table_indexes(change_table, cursor)
    reference_indexes = get_table_indexes(change_table, cursor_reference)

    add_indexes = [d for d in reference_indexes.keys() if d not in indexes.keys()]
    drop_indexes = [d for d in indexes.keys() if d not in reference_indexes.keys()]
    change_indexes = [d for d in indexes.keys() if d in reference_indexes.keys()]
    # 生成索引新增语句
    add_index_sqls = make_add_index_sql(add_indexes, reference_indexes)
    # 生成索引删除语句
    drop_index_sqls = make_drop_index_sql(change_table, drop_indexes)
    # 索引变更
    change_index_sqls = make_change_index_sql(change_table, change_indexes, indexes, reference_indexes)

    sql_list = add_column_sqls + drop_column_sqls + change_column_sqls + add_index_sqls + drop_index_sqls + change_index_sqls
    if len(sql_list) > 0:
        print("-- ----------modify table {}-------------".format(change_table))
        print('\n'.join(sql_list))
        print("-- ------------------------------------")

print("-- ------------------------------------")
 
# 关闭数据库连接
db.close()
db_reference.close()
