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
@click.option("-ob", "--odoo-branch", default="master")
@click.option("-eb", "--enterprise-branch", default="master")
@click.pass_context
def cli(ctx, dbname, port, odoo_branch, enterprise_branch):
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
    config["odoo-branch"] = odoo_branch
    config["enterprise-branch"] = enterprise_branch
    src = config["odoo-src"]
    worktree_src = config["worktree-src"]
    odoo_dir = (
        src / "odoo" if odoo_branch == "master" else worktree_src / "odoo" / odoo_branch
    )
    enterprise_dir = (
        src / "enterprise"
        if enterprise_branch == "master"
        else worktree_src / "enterprise" / enterprise_branch
    )

    if not odoo_dir.exists():
        create_odoo_worktree(config, odoo_branch, odoo_dir)
    if not enterprise_dir.exists():
        create_enterprise_worktree(config, enterprise_branch, enterprise_dir)

    config["addons-path"] = [
        str(src / "design-themes"),
        str(enterprise_dir),
        str(odoo_dir / "addons"),
        str(odoo_dir / "odoo" / "addons"),
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


@cli.command("delete-branch")
@click.option("-b", "--branches", type=list, cls=OptionEatAll)
@click.pass_obj
def delete_branch(obj, branches):
    """ branches = list "odoo/<branch_name>" or "enterprise/<branch_name>"
    """
    if branches:
        branches = [b.split("/") for b in branches]
        odoo_branches = [b for a, b in branches if a == "odoo"]
        enterprise_branches = [b for a, b in branches if a == "enterprise"]
    else:
        branches = []
        odoo_branches = []
        enterprise_branches = []
    if obj["config"].get("odoo-branch") != "master":
        odoo_branches.append(obj["config"].get("odoo-branch"))
    if obj["config"].get("enterprise-branch") != "master":
        enterprise_branches.append(obj["config"].get("enterprise-branch"))

    for branch in odoo_branches:
        delete_odoo_worktree_and_branch(obj["config"], branch)

    for branch in enterprise_branches:
        delete_enterprise_worktree_and_branch(obj["config"], branch)


# UTILITY FUNCTIONS


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


def create_odoo_worktree(config, branch_name, directory):
    odoo_dir = config["odoo-src"] / "odoo"
    worktree_src = config["worktree-src"]
    current_dir = os.getcwd()
    os.chdir(odoo_dir.expanduser())
    create_worktree_command = [
        "git",
        "worktree",
        "add",
        "-b",
        branch_name,
        str(worktree_src / "odoo" / branch_name),
    ]
    out, err = subprocess.Popen(
        create_worktree_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if out:
        click.echo(out.decode("utf-8"))
    if err:
        click.echo(err.decode("utf-8"), err=True)
    os.chdir(current_dir)


def create_enterprise_worktree(config, branch_name, directory):
    enterprise_dir = config["odoo-src"] / "enterprise"
    worktree_src = config["worktree-src"]
    current_dir = os.getcwd()
    os.chdir(enterprise_dir.expanduser())
    create_worktree_command = [
        "git",
        "worktree",
        "add",
        "-b",
        branch_name,
        str(worktree_src / "enterprise" / branch_name),
    ]
    out, err = subprocess.Popen(
        create_worktree_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if out:
        click.echo(out.decode("utf-8"))
    if err:
        click.echo(err.decode("utf-8"), err=True)
    os.chdir(current_dir)


def delete_odoo_worktree_and_branch(config, branch):
    odoo_dir = config["odoo-src"] / "odoo"
    worktree_src = config["worktree-src"]
    current_dir = os.getcwd()
    remove_dir_command = ["rm", "-rf", str(worktree_src / "odoo" / branch)]
    delete_branch_command = ["git", "branch", "-d", branch]
    prune_worktree_command = ["git", "worktree", "prune"]
    os.chdir(odoo_dir)
    for command in [remove_dir_command, delete_branch_command, prune_worktree_command]:
        out, err = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        if out:
            click.echo(out.decode("utf-8"))
        if err:
            click.echo(err.decode("utf-8"), err=True)
    os.chdir(current_dir)

def delete_enterprise_worktree_and_branch(config, branch):
    enterprise_dir = config["odoo-src"] / "enterprise"
    worktree_src = config["worktree-src"]
    current_dir = os.getcwd()
    remove_dir_command = ["rm", "-rf", str(worktree_src / "enterprise" / branch)]
    delete_branch_command = ["git", "branch", "-d", branch]
    prune_worktree_command = ["git", "worktree", "prune"]
    os.chdir(enterprise_dir)
    for command in [remove_dir_command, delete_branch_command, prune_worktree_command]:
        out, err = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        if out:
            click.echo(out.decode("utf-8"))
        if err:
            click.echo(err.decode("utf-8"), err=True)
    os.chdir(current_dir)
