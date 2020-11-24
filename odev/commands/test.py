import click
import os

from ..utils import run, db_exists, identify_current
from ..main import main
from odev.options import OptionEatAll


@main.command("test")
@click.argument("name", required=False)
@click.option("-f", "--test-file")
@click.option("-t", "--test-tags")
@click.option("-i", "--install-modules")
@click.option("-u", "--update-modules")
@click.option("-s", "--suffix")
@click.option("-b", "--basedb")
@click.option("-ne", "--no-enterprise", is_flag=True, default=False)
@click.option("--debug", is_flag=True, default=False)
@click.option("--fresh", is_flag=True, default=False)
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
def test(
    obj,
    name,
    test_file,
    test_tags,
    install_modules,
    update_modules,
    suffix,
    basedb,
    no_enterprise,
    debug,
    fresh,
    whatever,
):
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
    odoobin = obj.get_odoo_bin(name)
    addons = obj.get_addons(name, no_enterprise)
    command = [
        python,
        odoobin,
        "--addons-path",
        addons,
        "-d",
        suffix,
        "--stop-after-init",
    ]

    if install_modules:
        command += ["-i", install_modules]
    if update_modules:
        command += ["-u", update_modules]
    if debug:
        command += ["--limit-time-real", "3600"]
    if test_file:
        command += ["--test-file", test_file]
    if test_tags and not test_file:
        command += ["--test-enable", "--test-tags", test_tags]

    command += whatever

    run(command, verbose=True)
