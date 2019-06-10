import click
import subprocess
import sys
import os
from collections import defaultdict
from pathlib import Path

from .options import OptionEatAll


@click.group()
@click.option("-d", "--dbname", default="testdb", show_default=True)
@click.option("-p", "--port", default="8070")
@click.pass_context
def cli(ctx, dbname, port):
    """
    My personal odoo dev commands in the terminal.
    """
    if ctx.obj is None:
        ctx.obj = defaultdict(str)
    ctx.obj["dbname"] = dbname
    ctx.obj["port"] = port


@cli.command("start")
@click.option("-i", "--init", type=list, cls=OptionEatAll)
@click.option("-u", "--update", type=list, cls=OptionEatAll)
@click.option("-w", "--whatever", type=list, cls=OptionEatAll, save_other_options=False)
@click.pass_obj
def start_db(obj, init, update, whatever):
    dbname = obj["dbname"]
    port = obj["port"]
    try:
        command = odoo_run_command(dbname, init, update, port) + list(whatever or [])
        click.echo(f"Running: {' '.join(command)}\n")
        odooproc = subprocess.Popen(command)
        odooproc.communicate()
    except KeyboardInterrupt:
        odooproc.kill()


@cli.command("new")
@click.option("-n", "--no-demo", is_flag=True)
@click.option("-i", "--init", type=list, cls=OptionEatAll)
@click.option("-w", "--whatever", type=list, cls=OptionEatAll, save_other_options=False)
@click.pass_obj
def new_db(obj, no_demo, init, whatever):
    dbname = obj["dbname"]
    port = obj["port"]
    try:
        out, err = subprocess.Popen(
            dropdb_command(dbname), stderr=subprocess.PIPE, stdout=subprocess.PIPE
        ).communicate()
        click.echo((out or err).decode("utf-8") or f"{dbname} dropped.\n")
        command = init_db_command(dbname, init, no_demo, port) + list(whatever or [])
        click.echo(f"Running: {' '.join(command)}\n")
        odooproc = subprocess.Popen(command)
        odooproc.communicate()
    except KeyboardInterrupt:
        odooproc.kill()


@cli.command("shell")
@click.option("-w", "--whatever", type=list, cls=OptionEatAll, save_other_options=False)
@click.pass_obj
def run_odoo_shell(obj, whatever):
    dbname = obj["dbname"]
    try:
        command = odoo_shell_command(dbname) + list(whatever or [])
        click.echo(f"Running: {' '.join(command)}\n")
        odooproc = subprocess.Popen(command)
        odooproc.communicate()
    except KeyboardInterrupt:
        odooproc.kill()


@cli.command("copy")
@click.argument("new-dbname")
@click.pass_obj
def copy_db(obj, new_dbname):
    olddbname = obj["dbname"]
    try:
        out, err = subprocess.Popen(
            dropdb_command(new_dbname), stderr=subprocess.PIPE, stdout=subprocess.PIPE
        ).communicate()
        click.echo((out or err).decode("utf-8") or f"{new_dbname} dropped.")
        out, err = subprocess.Popen(
            copydb_command(olddbname, new_dbname),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        ).communicate()
        click.echo(
            (out or err).decode("utf-8") or f"{olddbname} is copied to {new_dbname}."
        )
    except KeyboardInterrupt:
        odooproc.kill()


## Constants
HOME = Path("~")
DEV = HOME / "Projects" / "odoo-dev"
ODOO = DEV / "src" / "odoo"
THEMES = DEV / "src" / "design-themes"
ENTERPRISE = DEV / "src" / "enterprise"
ODOOBIN = ODOO / "odoo-bin"
PYTHON = HOME / "miniconda3" / "envs" / "master" / "bin" / "python"
ADDONS = [THEMES, ENTERPRISE, ODOO / "addons", ODOO / "odoo" / "addons"]

## UTIL functions
str_path = lambda p: str(p.expanduser())


def init_db_command(dbname, init, no_demo, port):
    command = (
        [str_path(p) for p in [PYTHON, ODOOBIN]]
        + [f"--addons-path={','.join(map(str_path, ADDONS))}"]
        + ["-d", dbname]
        + (["-i", ",".join(init)] if init else [])
        + (["--xmlrpc-port", port] if port else [])
        + (["--without-demo", "ALL"] if no_demo else [])
    )
    return command


def odoo_shell_command(dbname):
    command = (
        [str_path(PYTHON), str_path(ODOOBIN), "shell"]
        + [f"--addons-path={','.join(map(str_path, ADDONS))}"]
        + ["-d", dbname]
    )
    return command


def odoo_run_command(dbname, init, update, port):
    command = (
        [str_path(PYTHON), str_path(ODOOBIN)]
        + [f"--addons-path={','.join(map(str_path, ADDONS))}"]
        + ["-d", dbname]
        + (["-i", ",".join(init)] if init else [])
        + (["-u", ",".join(update)] if update else [])
        + (["--xmlrpc-port", port] if port else [])
    )
    return command


def dropdb_command(dbname):
    command = ["dropdb", dbname]
    return command


def copydb_command(olddbname, newdbname):
    command = ["createdb", "-O", os.environ.get("USER"), "-T", olddbname, newdbname]
    return command
