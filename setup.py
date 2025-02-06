import os
from setuptools import setup, find_packages

# Читаем README.md для описания
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="initbysql",
    version="0.3",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Jinja2',
        'typer',
        'rich'
    ],
    package_data={
        'initbysql': ['templates/*', 'templates/auth/*'],
    },
    entry_points={
        'console_scripts': [
            'initbysql=initbysql.__main__:main',  # Исправлено на __main__
        ],
    },
    description="Автоматическая генерация FastAPI-бэкенда по SQL-скрипту.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Viven763/InitBySql",  # Ссылка на репозиторий
    author="@work_george",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
