# mysql-compare
```
对比mysql数据库结构,生成差异sql
安全起见，生成语句中删表/删字段/索引操作会自动加注释，需要自行判断是否打开注释

usage: 

> docker run --rm chenke91/mysql-compare:1.0.0 \
    -H --host <HOST>                        目标数据库地址
    -P --port <PORT>                        目标数据库端口
    -d --db <DB>                            目标数据库名称
    -u --username <USERNAME>                目标数据库用户名
    -p --password <PASSWORD>                目标数据库密码
    -RH --ref-host <REF-HOST>               参照数据库地址
    -RP --ref-port <REF-PORT>               参照数据库端口
    -rd --ref-db <REF-DB>                   参照数据库名称
    -ru --ref-username <REF-USERNAME>       参照数据库用户名
    -rp --ref-password <REF-PASSWORD>       参照数据库密码
    --ignore-comment <IGNORE-COMMENT>       是否忽略注释
```