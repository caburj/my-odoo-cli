from setuptools import setup

setup(
    name='odev',
    version='0.1',
    py_modules=['odev'],
    include_package_data=True,
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        odev=odev.cli:cli
    ''',
)