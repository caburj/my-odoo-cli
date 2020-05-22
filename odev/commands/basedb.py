import click

from ..utils import run, identify_current
from ..main import main


@main.command("basedb")
@click.argument("name", required=False)
@click.option("-a", "--alias")
@click.option("-i", "--install-modules")
@click.option("-l", "--list", default=False, is_flag=True)
@click.option("-n", "--no-demo", default=False, is_flag=True)
@click.pass_obj
@identify_current
def basedb(obj, name, alias, install_modules, list, no_demo):
    dbname = f"{name}-{alias if alias else 'basedb'}"
    run(obj.dropdb(dbname))
    run(obj.drop_filestore(dbname))
    run(obj.init_db(name, dbname, install_modules, no_demo), verbose=True)
