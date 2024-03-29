import click
import os

from ..utils import run, db_exists, identify_current
from ..main import main
from odev.options import OptionEatAll


@main.command("start")
@click.argument("name", required=False)
@click.option("-i", "--install-modules")
@click.option("-u", "--update-modules")
@click.option("-p", "--port")
@click.option("-s", "--suffix")
@click.option("-b", "--basedb")
@click.option("-W", "--base-worktree")
@click.option("-ne", "--no-enterprise", is_flag=True, default=False)
@click.option("-nd", "--no-demo", is_flag=True, default=False)
@click.option("--debug", is_flag=True, default=False)
@click.option("--fresh", is_flag=True, default=False)
@click.option("--shell", is_flag=True, default=False)
@click.option("--populate", is_flag=True, default=False)
@click.option("-d", "--db")
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
    suffix,
    basedb,
    base_worktree,
    no_enterprise,
    no_demo,
    debug,
    fresh,
    shell,
    populate,
    db,
    whatever,
):
    name = base_worktree if base_worktree else name
    suffix = f"{name}{f'-{suffix}' if suffix else ''}"
    basedb = f"{name}-{basedb if basedb else 'basedb'}"

    if fresh:
        run(obj.dropdb(suffix))
        run(obj.drop_filestore(suffix))
        run(obj.copydb(basedb, suffix))
        run(obj.copy_filestore(basedb, suffix))
    elif not db_exists(suffix):
        run(obj.copydb(basedb, suffix))
        run(obj.copy_filestore(basedb, suffix))

    python = obj.get_python()
    odoobin = obj.get_odoo_bin(name, base_worktree)
    addons = obj.get_addons(name, no_enterprise, base_worktree)
    command = [python]

    if debug:
        command.extend(['-m', 'debugpy', '--listen', '5678'])

    command.append(odoobin)

    if shell:
        command += ["shell"]
    if populate:
        command += ["populate"]

    command += ["--addons-path", addons, "-d", db or suffix, "-p", port or obj.port]

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
