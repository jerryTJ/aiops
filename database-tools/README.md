
# create environment

## install hatch

 pip install hatch -i <https://pypi.tuna.tsinghua.edu.cn/simple>

## install python

pyenv  install/uninstall  3.13.2
pyenv global  3.13.2
pyenv local  3.13.2
python   versions

## create env

python -m venv ./env-name

sourece .python-env/bin/activate

# database-tools

[![PyPI - Version](https://img.shields.io/pypi/v/database-tools.svg)](https://pypi.org/project/database-tools)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/database-tools.svg)](https://pypi.org/project/database-tools)

-----

## Table of Contents

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install database-tools
```

## License

`database-tools` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

# launch mcp inspector

npx @modelcontextprotocol/inspector
<http://localhost:6274>

sql_config
{"sql":"update histories set created_at = now();","user":"jerry","id":"2025-11-24","attributes":"labels:example-label context:example-context","rollback":"update histories set created_at = now();","comment":"test mcp"}

db_config
{"url":"jdbc:mysql://localhost:3306/applier","username":"root","pwd":"Admin@123"}

 liquibase --driver=com.mysql.cj.jdbc.Driver  --changeLogFile=/tmp/chanageSet_2025-11-24.sql
 --url=jdbc:mysql://localhost:3306/applier --username=root --password=Admin@123 update

liquibase --driver=com.mysql.cj.jdbc.Driver --changeLogFile=chanageSet_2025-11-24.sql --url=jdbc:mysql://localhost:3306/applier --username=root --password=Admin@123 update

liquibase --driver=com.mysql.cj.jdbc.Driver --changeLogFile=chanageSet_2025-11-24.sql --url=jdbc:mysql://localhost:3306/applier --username=root --password=Admin@123 update

--liquibase formatted sql
--changeset zhangsan:T1-20251125-001 context:prod
--comment: 更新用户昵称
UPDATE t_users SET nick_name="Tom", open_id=1 WHERE id=1;
--rollback UPDATE t_users SET nick_name="Jerry", open_id=2 WHERE id=1

{"db_url":"localhost:3306","db_name":"applier","username":"root", "pwd":"Admin@123"}
