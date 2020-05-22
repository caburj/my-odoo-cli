import click

from ..utils import run, get_dbs, identify_current
from ..main import main


@main.command("drop")
@click.argument("name", required=False)
@click.option('-s', '--suffix')
@click.option('-a', '--all', is_flag=True)
@click.pass_obj
@identify_current
def drop(obj, name, suffix, all):
    dbname = f"{name}{f'-{suffix}' if suffix else ''}"
    dbs = get_dbs(dbname) if all else [dbname]
    for db in dbs:
        run(obj.dropdb(db))
        run(obj.drop_filestore(db))
