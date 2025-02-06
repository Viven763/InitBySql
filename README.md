# InitBySql

InitBySql — это инструмент для автоматической генерации FastAPI-бэкенда по SQL-скрипту создания таблиц.

## Установка

```sh
pip3 install initbysql
```

## Использование
```sh
python3 -m initbysql schema.sql output_directory
```
## Где:

**schema.sql** — файл с SQL-скриптом создания таблиц
**output_directory** — папка, в которую будет сгенерирован код