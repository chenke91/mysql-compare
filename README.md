# mysql-compare
```
对比mysql数据库结构,生成差异sql

usage: 

> docker run --rm chenke91/mysql-compare:0.0.1 \
    --host <HOST>                       目标数据库地址
    --port <PORT>                       目标数据库端口
    --db <DB>                           目标数据库名称
    --username <USERNAME>               目标数据库用户名
    --password <PASSWORD>               目标数据库密码
    --ref-host <REF-HOST>               参照数据库地址
    --ref-port <REF-PORT>               参照数据库端口
    --ref-db <REF-DB>                   参照数据库名称
    --ref-username <REF-USERNAME>       参照数据库用户名
    --ref-password <REF-PASSWORD>       参照数据库密码
    --ignore-comment <IGNORE-COMMENT>   是否忽略注释
```