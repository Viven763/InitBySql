import os
import re
import typer
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from rich.prompt import Prompt

console = Console()

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
        'null': 'None',
        'false': 'False',
        'true': 'True'
    }
    return type_map.get(sql_type, 'str')

def generate_files(tables: List[SQLTable], output_dir: str, include_auth: bool):
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates/')
    env = Environment(loader=FileSystemLoader(templates_dir))
    env.filters['sql_type_to_py'] = sql_type_to_py

    for table in tables:
        dir_path = os.path.join(output_dir, table.name)
        os.makedirs(dir_path, exist_ok=True)
        for file in ['models.py', 'schemas.py', 'crud.py', 'router.py']:
            template = env.get_template(f'{file}.j2')
            content = template.render(table=table)
            content = content.replace("null", "None").replace("false", "False").replace("true", "True")
            with open(os.path.join(dir_path, file), 'w') as f:
                f.write(content)
        with open(os.path.join(dir_path, '__init__.py'), 'w') as f:
            f.write("")

    if include_auth:
        auth_dir = os.path.join(output_dir, 'auth')
        os.makedirs(auth_dir, exist_ok=True)
        for file in ['router.py', 'models.py', 'schemas.py', 'crud.py', 'hashutils.py', 'utils.py']:
            template = env.get_template(f'auth/{file}.j2')
            content = template.render()
            content = content.replace("null", "None").replace("false", "False").replace("true", "True")
            with open(os.path.join(auth_dir, file), 'w') as f:
                f.write(content)
    
    # Генерация app.py
    app_template = env.get_template('app.py.j2')
    app_content = app_template.render(tables=tables)
    with open(os.path.join(output_dir, 'app.py'), 'w') as f:
        f.write(app_content)

def main(sql_file: str, output_dir: str):
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    tables = parse_sql(sql_content)
    
    console.print("\n[bold cyan]Будут созданы следующие роутеры:[/bold cyan]")
    table_view = Table(show_header=True, header_style="bold magenta")
    table_view.add_column("Таблица", style="dim")
    table_view.add_column("Количество полей")
    for table in tables:
        table_view.add_row(table.name, str(len(table.fields)))
    console.print(table_view)
    
    for table in tables:
        console.print(f"\n[bold cyan]Поля таблицы {table.name}:[/bold cyan]")
        field_table = Table(show_header=True, header_style="bold green")
        field_table.add_column("Имя поля")
        field_table.add_column("Тип")
        field_table.add_column("Nullable")
        field_table.add_column("Primary Key")
        for field in table.fields:
            field_table.add_row(field.name, field.type, str(field.nullable), str(field.is_primary))
        console.print(field_table)
    
    include_auth = Confirm.ask("Добавить маршрутизатор аутентификации?")
    generate_files(tables, output_dir, include_auth)
    console.print("\n[bold green]Бэкенд успешно создан![/bold green]")

if __name__ == '__main__':
    typer.run(main)
