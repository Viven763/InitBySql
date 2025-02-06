from setuptools import setup, find_packages

setup(
    name="initbysql",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Jinja2',
    ],
    entry_points={
        'console_scripts': [
            'initbysql=initbysql.generate_api:main',
        ],
    },
)