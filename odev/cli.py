import click
import subprocess
import sys
import os
from collections import defaultdict
from pathlib import Path
from configparser import ConfigParser

from .options import OptionEatAll

HOME = Path("~").expanduser()


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

    raw_config = ConfigParser()
    conf_path = (
        HOME / ".odev" if (HOME / ".odev").is_file() else (HOME / ".my-odoo-cli")
    )
    raw_config.read(conf_path)

    config = {}
    env_python_exe = (
        HOME
        / "miniconda3"
        / "envs"
        / raw_config["DEFAULT"].get("conda-env")
        / "bin"
        / "python"
    )
    config["python"] = str(
        env_python_exe
        if env_python_exe.is_file()
        else HOME / "miniconda3" / "bin" / "python"
    )
    config["odoo-src"] = Path(raw_config["DEFAULT"].get("odoo-src")).expanduser()
    config["worktree-src"] = Path(
        raw_config["DEFAULT"].get("worktree-src")
    ).expanduser()
    config["odoo-bin"] = str(config["odoo-src"] / "odoo" / "odoo-bin")
    src = config["odoo-src"]
    config["addons-path"] = [
        str(src / "design-themes"),
        str(src / "enterprise"),
        str(src / "odoo" / "addons"),
        str(src / "odoo" / "odoo" / "addons"),
    ]

    ctx.obj["dbname"] = raw_config["DEFAULT"].get("default-dbname", dbname)
    ctx.obj["port"] = raw_config["DEFAULT"].get("default-port", port)
    ctx.obj["config"] = config


@cli.command("start")
@click.option("-i", "--init", type=list, cls=OptionEatAll)
@click.option("-u", "--update", type=list, cls=OptionEatAll)
@click.option("-w", "--whatever", type=list, cls=OptionEatAll, save_other_options=False)
@click.pass_obj
def start_db(obj, init, update, whatever):
    dbname = obj["dbname"]
    port = obj["port"]
    try:
        command = odoo_run_command(obj["config"], dbname, init, update, port) + list(
            whatever or []
        )
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
        command = init_db_command(obj["config"], dbname, init, no_demo, port) + list(
            whatever or []
        )
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
        command = odoo_shell_command(obj["config"], dbname) + list(whatever or [])
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


def init_db_command(config, dbname, init, no_demo, port):
    python = config["python"]
    odoobin = config["odoo-bin"]
    addons = config["addons-path"]
    command = (
        [python, odoobin]
        + [f"--addons-path={','.join(addons)}"]
        + ["-d", dbname]
        + (["-i", ",".join(init)] if init else [])
        + (["--xmlrpc-port", port] if port else [])
        + (["--without-demo", "ALL"] if no_demo else [])
    )
    return command


def odoo_shell_command(config, dbname):
    python = config["python"]
    odoobin = config["odoo-bin"]
    addons = config["addons-path"]
    command = (
        [python, odoobin, "shell"]
        + [f"--addons-path={','.join(addons)}"]
        + ["-d", dbname]
    )
    return command


def odoo_run_command(config, dbname, init, update, port):
    python = config["python"]
    odoobin = config["odoo-bin"]
    addons = config["addons-path"]
    command = (
        [python, odoobin]
        + [f"--addons-path={','.join(addons)}"]
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
