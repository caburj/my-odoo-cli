import click
import subprocess
import sys
import os
from collections import defaultdict
from pathlib import Path
from configparser import ConfigParser
import json

from .options import OptionEatAll

HOME = Path("~").expanduser()


class MyConfig:
    def __init__(self):
        raw_config = ConfigParser()
        conf_path = (
            HOME / ".odev" if (HOME / ".odev").is_file() else (HOME / ".my-odoo-cli")
        )
        raw_config.read(conf_path)

        self.config = {}
        python_bin = (
            HOME
            / "miniconda3"
            / "envs"
            / raw_config["DEFAULT"].get("conda-env")
            / "bin"
            / "python"
        )
        self.config["python"] = (
            python_bin
            if python_bin.is_file()
            else HOME / "miniconda3" / "bin" / "python"
        )
        self.config["workspace-dir"] = Path(
            raw_config["DEFAULT"].get("workspace-dir")
        ).expanduser()
        self.config["odoo-src"] = Path(
            raw_config["DEFAULT"].get("odoo-src")
        ).expanduser()
        self.config["worktree-src"] = Path(
            raw_config["DEFAULT"].get("worktree-src")
        ).expanduser()
        self.config["default-dbname"] = raw_config["DEFAULT"].get("default-dbname")
        self.config["default-port"] = raw_config["DEFAULT"].get("default-port")

    def __getitem__(self, name):
        return self.config.get(name)

    def __setitem__(self, name, value):
        self.config[name] = value


CONFIG = MyConfig()


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

    global CONFIG
    src = CONFIG["odoo-src"]
    worktree_src = CONFIG["worktree-src"]
    odoo_branch_dir = (
        src / "odoo" if odoo_branch == "master" else worktree_src / "odoo" / odoo_branch
    )
    enterprise_branch_dir = (
        src / "enterprise"
        if enterprise_branch == "master"
        else worktree_src / "enterprise" / enterprise_branch
    )
    CONFIG["odoo-bin"] = str(
        (src / "odoo" if odoo_branch == "master" else odoo_branch_dir) / "odoo-bin"
    )

    CONFIG["addons-path"] = [
        str(src / "design-themes"),
        str(enterprise_branch_dir),
        str(odoo_branch_dir / "addons"),
        str(odoo_branch_dir / "odoo" / "addons"),
    ]
    CONFIG["odoo-branch"] = odoo_branch
    CONFIG["enterprise-branch"] = enterprise_branch

    if not odoo_branch_dir.exists():
        create_odoo_worktree()
        create_odoo_workspace()
        create_launch_json()
    if not enterprise_branch_dir.exists():
        create_enterprise_worktree()
        create_enterprise_workspace()
        create_launch_json()

    ctx.obj["dbname"] = CONFIG["default-dbname"] or dbname
    ctx.obj["port"] = CONFIG["default-port"] or port


@cli.command("start")
@click.option("-i", "--init", type=list, cls=OptionEatAll)
@click.option("-u", "--update", type=list, cls=OptionEatAll)
@click.option("-w", "--whatever", type=list, cls=OptionEatAll, save_other_options=False)
@click.pass_obj
def start_db(obj, init, update, whatever):
    dbname = obj["dbname"]
    port = obj["port"]
    try:
        command = odoo_run_command(CONFIG, dbname, init, update, port) + list(
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
        command = init_db_command(CONFIG, dbname, init, no_demo, port) + list(
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
        command = odoo_shell_command(CONFIG, dbname) + list(whatever or [])
        click.echo(f"Running: {' '.join(command)}\n")
        odooproc = subprocess.Popen(command)
        odooproc.communicate()
    except KeyboardInterrupt:
        odooproc.kill()


@cli.command("copy-db")
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
@click.option(
    "-b",
    "--branches",
    type=list,
    cls=OptionEatAll,
    help='branches = list "odoo/<branch_name>" or "enterprise/<branch_name>"',
)
@click.pass_obj
def delete_branch(obj, branches):
    # branches = list "odoo/<branch_name>" or "enterprise/<branch_name>"
    if branches:
        branches = [b.split("/") for b in branches]
        odoo_branches = [b for a, b in branches if a == "odoo"]
        enterprise_branches = [b for a, b in branches if a == "enterprise"]
    else:
        branches = []
        odoo_branches = []
        enterprise_branches = []
    if CONFIG["odoo-branch"] != "master":
        odoo_branches.append(CONFIG["odoo-branch"])
    if CONFIG["enterprise-branch"] != "master":
        enterprise_branches.append(CONFIG["enterprise-branch"])
    for branch in odoo_branches:
        delete_odoo_worktree_and_branch(branch)

    for branch in enterprise_branches:
        delete_enterprise_worktree_and_branch(branch)


# UTILITY FUNCTIONS


def init_db_command(config, dbname, init, no_demo, port):
    python = str(config["python"])
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
    python = str(config["python"])
    odoobin = config["odoo-bin"]
    addons = config["addons-path"]
    command = (
        [python, odoobin, "shell"]
        + [f"--addons-path={','.join(addons)}"]
        + ["-d", dbname]
    )
    return command


def odoo_run_command(config, dbname, init, update, port):
    python = str(config["python"])
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


def create_odoo_worktree():
    branch_name = CONFIG["odoo-branch"]
    odoo_dir = CONFIG["odoo-src"] / "odoo"
    worktree_src = CONFIG["worktree-src"]
    current_dir = os.getcwd()
    os.chdir(odoo_dir.expanduser())
    command1 = [
        "git",
        "worktree",
        "add",
        "--checkout",
        str(worktree_src / "odoo" / branch_name),
        branch_name,
    ]
    command2 = [
        "git",
        "worktree",
        "add",
        "-b",
        branch_name,
        str(worktree_src / "odoo" / branch_name),
    ]
    out, err = subprocess.Popen(
        command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if 'fatal: invalid reference' in err.decode("utf-8"):
        click.echo(
            f"Unable to checkout remote branch: `{branch_name}`. Creating a new branch now for the worktree...",
            err=True,
        )
        out, err = subprocess.Popen(
            command2, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
    if out:
        click.echo(out.decode("utf-8"))
    if err:
        click.echo(err.decode("utf-8"), err=True)
    os.chdir(current_dir)


def create_enterprise_worktree():
    branch_name = CONFIG["enterprise-branch"]
    enterprise_dir = CONFIG["odoo-src"] / "enterprise"
    worktree_src = CONFIG["worktree-src"]
    current_dir = os.getcwd()
    os.chdir(enterprise_dir.expanduser())
    command1 = [
        "git",
        "worktree",
        "add",
        "--checkout",
        str(worktree_src / "enterprise" / branch_name),
        branch_name,
    ]
    command2 = [
        "git",
        "worktree",
        "add",
        "-b",
        branch_name,
        str(worktree_src / "enterprise" / branch_name),
    ]
    out, err = subprocess.Popen(
        command1, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if 'fatal: invalid reference' in err.decode("utf-8"):
        click.echo(
            f"Unable to checkout remote branch: `{branch_name}`. Creating a new branch now for the worktree...",
            err=True,
        )
        out, err = subprocess.Popen(
            command2, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
    if out:
        click.echo(out.decode("utf-8"))
    if err:
        click.echo(err.decode("utf-8"), err=True)
    os.chdir(current_dir)


def delete_odoo_worktree_and_branch(branch):
    odoo_dir = CONFIG["odoo-src"] / "odoo"
    worktree_src = CONFIG["worktree-src"]
    current_dir = os.getcwd()
    remove_dir_command = ["rm", "-rf", str(worktree_src / "odoo" / branch)]
    delete_branch_command = ["git", "branch", "-d", branch]
    prune_worktree_command = ["git", "worktree", "prune"]
    delete_workspace_command = [
        "rm",
        str(CONFIG["workspace-dir"] / f"odoo-{branch}.code-workspace"),
    ]
    os.chdir(odoo_dir)
    for command in [
        remove_dir_command,
        prune_worktree_command,
        delete_branch_command,
        delete_workspace_command,
    ]:
        out, err = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        if out:
            click.echo(out.decode("utf-8"))
        if err:
            click.echo(err.decode("utf-8"), err=True)
    os.chdir(current_dir)


def delete_enterprise_worktree_and_branch(branch):
    enterprise_dir = CONFIG["odoo-src"] / "enterprise"
    worktree_src = CONFIG["worktree-src"]
    current_dir = os.getcwd()
    remove_dir_command = ["rm", "-rf", str(worktree_src / "enterprise" / branch)]
    delete_branch_command = ["git", "branch", "-d", branch]
    prune_worktree_command = ["git", "worktree", "prune"]
    delete_workspace_command = [
        "rm",
        str(CONFIG["workspace-dir"] / f"enterprise-{branch}.code-workspace"),
    ]
    os.chdir(enterprise_dir)
    for command in [
        remove_dir_command,
        prune_worktree_command,
        delete_branch_command,
        delete_workspace_command,
    ]:
        out, err = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        if out:
            click.echo(out.decode("utf-8"))
        if err:
            click.echo(err.decode("utf-8"), err=True)
    os.chdir(current_dir)


def create_odoo_workspace():
    branch = CONFIG["odoo-branch"]
    workspace = {
        "folders": [
            {"path": str(CONFIG["worktree-src"] / "odoo" / branch)},
            {"path": "/home/joseph/Projects/odoo-dev/src/enterprise"},
            {"path": "/home/joseph/Projects/odoo-dev/src/design-themes"},
        ]
    }
    workspace_dir = CONFIG["workspace-dir"]
    if not workspace_dir.exists():
        workspace_dir.mkdir(parents=True, exist_ok=True)
    with open(workspace_dir / f"odoo-{branch}.code-workspace", "w+") as f:
        json.dump(workspace, f, indent=4)


def create_enterprise_workspace():
    branch = CONFIG["enterprise-branch"]
    workspace = {
        "folders": [
            {"path": "/home/joseph/Projects/odoo-dev/src/odoo"},
            {"path": str(CONFIG["worktree-src"] / "enterprise" / branch)},
            {"path": "/home/joseph/Projects/odoo-dev/src/design-themes"},
        ]
    }
    workspace_dir = CONFIG["workspace-dir"]
    if not workspace_dir.exists():
        workspace_dir.mkdir(parents=True, exist_ok=True)
    with open(workspace_dir / f"enterprise-{branch}.code-workspace", "w+") as f:
        json.dump(workspace, f)


def create_launch_json():
    branch = CONFIG["odoo-branch"]
    python = CONFIG["python"]
    odoobin = CONFIG["odoo-bin"]
    addons = CONFIG["addons-path"]
    command = (
        [f"--addons-path={','.join(addons)}"]
        + ["-d", "testdb"]
        + ["--xmlrpc-port", "8070"]
    )
    launch = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "odoo-bin",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/odoo-bin",
                "console": "integratedTerminal",
                "args": command,
            }
        ],
    }

    vscode_dir = CONFIG["worktree-src"] / "odoo" / branch / ".vscode"
    if not vscode_dir.exists():
        vscode_dir.mkdir(parents=True, exist_ok=True)

    with open(vscode_dir / f"launch.json", "w+") as f:
        json.dump(launch, f, indent=4)
