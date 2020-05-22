import click

from ..utils import run, db_exists, identify_current
from ..main import main
from odev.options import OptionEatAll


@main.command("start")
@click.argument("name", required=False)
@click.option("-i", "--install-modules")
@click.option("-u", "--update-modules")
@click.option("-p", "--port")
@click.option("-d", "--dbsuffix")
@click.option("-b", "--basedb")
@click.option("-ne", "--no-enterprise", is_flag=True, default=False)
@click.option("-nd", "--no-demo", is_flag=True, default=False)
@click.option("--debug", is_flag=True, default=False)
@click.option("--fresh", is_flag=True, default=False)
@click.option("--shell", is_flag=True, default=False)
@click.option(
    "-w",
    "--whatever",
    type=list,
    cls=OptionEatAll,
    save_other_options=False,
    default=list,
    help="Other options that can be passed to odoo-cli",
)
@click.pass_obj
@identify_current
def start(
    obj,
    name,
    install_modules,
    update_modules,
    port,
    dbsuffix,
    basedb,
    no_enterprise,
    no_demo,
    debug,
    fresh,
    shell,
    whatever,
):
    dbsuffix = f"{name}{f'-{dbsuffix}' if dbsuffix else ''}"
    basedb = f"{name}-{basedb if basedb else 'basedb'}"

    if fresh:
        run(obj.dropdb(dbsuffix))
        run(obj.drop_filestore(dbsuffix))
        run(obj.copydb(basedb, dbsuffix))
        run(obj.copy_filestore(basedb, dbsuffix))
    elif not db_exists(dbsuffix):
        run(obj.copydb(basedb, dbsuffix))
        run(obj.copy_filestore(basedb, dbsuffix))

    python = obj.get_python()
    odoobin = obj.get_odoo_bin(name)
    addons = obj.get_addons(name, no_enterprise)
    command = [python, odoobin]

    if shell:
        command += ["shell"]

    command += ["--addons-path", addons, "-d", dbsuffix, "-p", port or obj.port]

    if install_modules:
        command += ["-i", install_modules]
    if update_modules:
        command += ["-u", update_modules]
    if no_demo:
        command += ["--without-demo", "ALL"]
    if debug:
        command += ["--limit-time-real", "3600"]
    
    command += whatever

    run(command, verbose=True)
