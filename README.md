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
    --ref_host <REF_HOST>               参照数据库地址
    --ref_port <REF_PORT>               参照数据库端口
    --ref_db <REF_DB>                   参照数据库名称
    --ref_username <REF_USERNAME>       参照数据库用户名
    --ref_password >REF_PASSWORD>       参照数据库密码
```