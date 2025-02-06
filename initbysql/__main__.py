import os
import re
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Optional
from dataclasses import dataclass
import argparse

@dataclass
class SQLField:
    name: str
    type: str
    nullable: bool
    default: Optional[str]
    is_primary: bool = False
    foreign_key: Optional[str] = None


@dataclass
class SQLTable:
    name: str
    fields: List[SQLField]


# Парсинг SQL файла
def parse_sql(sql_content: str) -> List[SQLTable]:
    tables = []
    sql_content = re.sub(r'--.*', '', sql_content)
    sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
    create_table_regex = re.compile(
        r'create table (?:if not exists )?(\w+)\s*\((.*?)\);',
        re.IGNORECASE | re.DOTALL
    )
    for match in create_table_regex.finditer(sql_content):
        table_name = match.group(1)
        fields_str = match.group(2)
        fields = []
        field_strs = re.split(r',\s*(?![^()]*\))', fields_str)
        for field_str in field_strs:
            field_str = field_str.strip()
            if not field_str:
                continue
            parts = re.split(r'\s+', field_str, maxsplit=2)
            name = parts[0]
            type_ = parts[1].lower()
            modifiers = parts[2].lower() if len(parts) > 2 else ''
            nullable = 'not null' not in modifiers and 'primary key' not in modifiers
            default = re.search(r'default\s+(\S+)', modifiers)
            default = default.group(1) if default else None
            is_primary = 'primary key' in modifiers
            foreign_key = re.search(r'references\s+(\w+)\s*\(\w+\)', modifiers, re.IGNORECASE)
            foreign_key = foreign_key.group(1) if foreign_key else None
            fields.append(SQLField(
                name=name,
                type=type_,
                nullable=nullable,
                default=default,
                is_primary=is_primary,
                foreign_key=foreign_key
            ))
        tables.append(SQLTable(name=table_name, fields=fields))
    return tables


# Маппинг SQL типов на Python
def sql_type_to_py(sql_type: str) -> str:
    type_map = {
        'serial': 'int',
        'integer': 'int',
        'int': 'int',
        'varchar': 'str',
        'text': 'str',
        'boolean': 'bool',
        'float': 'float',
        'timestamp': 'datetime',
    }
    return type_map.get(sql_type, 'str')


# Генерация файлов
def generate_files(tables: List[SQLTable], output_dir: str):
    # Получаем абсолютный путь к папке с шаблонами
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(templates_dir))
    env.filters['sql_type_to_py'] = sql_type_to_py

    # Создаем папки для каждой таблицы
    for table in tables:
        dir_path = os.path.join(output_dir, table.name)
        os.makedirs(dir_path, exist_ok=True)

        # Генерируем models.py
        template = env.get_template('model.py.j2')
        content = template.render(table=table)
        with open(os.path.join(dir_path, 'models.py'), 'w') as f:
            f.write(content)

        # Генерируем schemas.py
        template = env.get_template('schemas.py.j2')
        content = template.render(table=table)
        with open(os.path.join(dir_path, 'schemas.py'), 'w') as f:
            f.write(content)

        # Генерируем crud.py
        template = env.get_template('crud.py.j2')
        content = template.render(table=table)
        with open(os.path.join(dir_path, 'crud.py'), 'w') as f:
            f.write(content)

        # Генерируем router.py
        template = env.get_template('router.py.j2')
        content = template.render(table=table)
        with open(os.path.join(dir_path, 'router.py'), 'w') as f:
            f.write(content)
        with open(os.path.join(dir_path, '__init__.py'), 'w') as f:
            f.write("")

    # Проверяем, есть ли поле password в таблице users
    users_table = next((table for table in tables if table.name == 'users'), None)
    if users_table and any(field.name == 'password' for field in users_table.fields):
        # Генерируем auth
        auth_dir = os.path.join(output_dir, 'auth')
        os.makedirs(auth_dir, exist_ok=True)
        for template_file in ['router.py', 'models.py', 'schemas.py', 'crud.py', 'hashutils.py', 'utils.py']:
            template = env.get_template(f'auth/{template_file}.j2')
            content = template.render()
            with open(os.path.join(auth_dir, template_file), 'w') as f:
                f.write(content)

    # Генерируем app.py
    template = env.get_template('app.py.j2')
    content = template.render(tables=tables)
    with open(os.path.join(output_dir, 'app.py'), 'w') as f:
        f.write(content)


# Основная функция
def main():
    parser = argparse.ArgumentParser(description="Generate Python files from SQL schema.")
    parser.add_argument('sql_file', type=str, help="Path to the SQL file")
    parser.add_argument('output_dir', type=str, help="Path to the output directory")
    args = parser.parse_args()

    with open(args.sql_file, 'r') as f:
        sql_content = f.read()
    tables = parse_sql(sql_content)
    generate_files(tables, args.output_dir)

if __name__ == '__main__':
    main()