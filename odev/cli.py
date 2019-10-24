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


def generate_config(branch, enterprise):
    raw_config = ConfigParser()
    conf_path = (
        HOME / ".odev" if (HOME / ".odev").is_file() else (HOME / ".my-odoo-cli")
    )
    raw_config.read(conf_path)

    config = {}
    config["conda-env"] = raw_config["DEFAULT"].get("conda-env")
    config["workspace-dir"] = Path(
        raw_config["DEFAULT"].get("workspace-dir")
    ).expanduser()
    config["kernelspec-dir"] = Path(
        raw_config["DEFAULT"].get("kernelspec-dir")
    ).expanduser()
    config["odoo-src"] = Path(raw_config["DEFAULT"].get("odoo-src")).expanduser()
    config["worktree-src"] = Path(
        raw_config["DEFAULT"].get("worktree-src")
    ).expanduser()
    config["default-dbname"] = branch
    config["default-port"] = raw_config["DEFAULT"].get("default-port")

    src = config["odoo-src"]
    odoo_branch_dir = (
        src / "odoo" if branch == "master" else config["worktree-src"] / branch / "odoo"
    )
    enterprise_branch_dir = (
        src / "enterprise"
        if branch == "master"
        else config["worktree-src"] / branch / "enterprise"
    )
    config["odoo-bin"] = str(
        (src / "odoo" if branch == "master" else odoo_branch_dir) / "odoo-bin"
    )

    enterprise_path = [str(enterprise_branch_dir)] if enterprise else []
    config["addons-path"] = enterprise_path + [
        str(odoo_branch_dir / "addons"),
        str(odoo_branch_dir / "odoo" / "addons"),
    ]
    config["odoo-branch-dir"] = odoo_branch_dir
    config["enterprise-branch-dir"] = enterprise_branch_dir
    config["odoo-master-dir"] = src / "odoo"
    config["enterprise-master-dir"] = src / "enterprise"

    config["branch"] = branch

    return config


@click.group()
@click.option("-d", "--dbname")
@click.option("-p", "--port", default="8070", show_default=True)
@click.option("-b", "--branch", default="master", show_default=True)
@click.option("-e", "--conda-env")
@click.option("--enterprise/--no-enterprise", default=True)
@click.pass_context
def cli(ctx, dbname, port, branch, conda_env, enterprise):
    """
    My personal odoo dev commands in the terminal.
    """
    if ctx.obj is None:
        ctx.obj = defaultdict(str)

    config = generate_config(branch, enterprise)

    ctx.obj["dbname"] = dbname or config.get("default-dbname") or branch
    ctx.obj["port"] = port or config["default-port"]
    ctx.obj["branch"] = branch
    conda_env = conda_env or config["conda-env"]
    python_bin = HOME / "miniconda3" / "envs" / conda_env / "bin" / "python"
    config["python"] = str(
        python_bin if python_bin.is_file() else HOME / "miniconda3" / "bin" / "python"
    )
    ctx.obj["config"] = config


@cli.command("prepare")
@click.pass_obj
def prepare_env(obj):
    """Check out appropriate branch to worktrees (both community and enterprise)."""
    config = obj["config"]
    current_dir = os.getcwd()

    os.chdir(config["odoo-master-dir"])
    if config["branch"] != "master":
        if not try_checkout_odoo_branch(config):
            create_new_odoo_branch(config)

    os.chdir(config["enterprise-master-dir"])
    if config["branch"] != "master":
        if not try_checkout_enterprise_branch(config):
            create_new_enterprise_branch(config)

    create_workspace(config)
    create_launch_json(config)
    os.chdir(current_dir)


def try_checkout_odoo_branch(config):
    command = [
        "git",
        "worktree",
        "add",
        "--checkout",
        str(config["odoo-branch-dir"]),
        config["branch"],
    ]
    out, err = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if "already exists" in err.decode("utf-8"):
        command = [
            "git",
            "worktree",
            "add",
            str(config["odoo-branch-dir"]),
            config["branch"],
        ]
        out, err = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
    return "done" in err.decode("utf-8")


def create_new_odoo_branch(config):
    command = [
        "git",
        "worktree",
        "add",
        "-b",
        config["branch"],
        str(config["odoo-branch-dir"]),
    ]
    out, err = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if out:
        click.echo(out.decode("utf-8"))
    if err:
        click.echo(err.decode("utf-8"))


def try_checkout_enterprise_branch(config):
    command = [
        "git",
        "worktree",
        "add",
        "--checkout",
        str(config["enterprise-branch-dir"]),
        config["branch"],
    ]
    out, err = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if "already exists" in err.decode("utf-8"):
        command = [
            "git",
            "worktree",
            "add",
            str(config["odoo-branch-dir"]),
            config["branch"],
        ]
        out, err = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
    return "done" in err.decode("utf-8")


def create_new_enterprise_branch(config):
    command = [
        "git",
        "worktree",
        "add",
        "-b",
        config["branch"],
        str(config["enterprise-branch-dir"]),
    ]
    out, err = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if out:
        click.echo(out.decode("utf-8"))
    if err:
        click.echo(err.decode("utf-8"))


def create_workspace(config):
    branch = config["branch"]
    if branch == "master":
        return

    workspace = {
        "folders": [
            {"path": str(config["odoo-branch-dir"])},
            {"path": str(config["enterprise-branch-dir"])},
            # {"path": "/home/joseph/Projects/odoo-dev/src/design-themes"},
        ]
    }
    workspace_dir = config["workspace-dir"]
    if not workspace_dir.exists():
        workspace_dir.mkdir(parents=True, exist_ok=True)
    with open(workspace_dir / f"{branch}.code-workspace", "w+") as f:
        json.dump(workspace, f, indent=4)


def create_launch_json(config):
    addons = config["addons-path"]
    command = (
        [f"--addons-path={','.join(addons)}"]
        + ["-d", config["default-dbname"]]
        + ["--xmlrpc-port", config["default-port"]]
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
    vscode_dir = config["odoo-branch-dir"] / ".vscode"
    if not vscode_dir.exists():
        vscode_dir.mkdir(parents=True, exist_ok=True)
    with open(vscode_dir / f"launch.json", "w+") as f:
        json.dump(launch, f, indent=4)


@cli.command("init")
@click.option("-n", "--no-demo", is_flag=True)
@click.option("-i", "--init", type=list, cls=OptionEatAll)
@click.option(
    "-w",
    "--whatever",
    type=list,
    cls=OptionEatAll,
    save_other_options=False,
    help="Other options that can be passed to odoo-cli",
)
@click.pass_obj
def init_db(obj, no_demo, init, whatever):
    """Once worktrees are available, start new instance."""
    config = obj["config"]
    dbname = obj["dbname"]
    port = obj["port"]
    try:
        out, err = subprocess.Popen(
            dropdb_command(dbname), stderr=subprocess.PIPE, stdout=subprocess.PIPE
        ).communicate()
        click.echo((out or err).decode("utf-8") or f"{dbname} dropped.\n")
        command = init_db_command(config, dbname, init, no_demo, port) + list(
            whatever or []
        )
        click.echo(f"Running: {' '.join(command)}\n")
        odooproc = subprocess.Popen(command)
        odooproc.communicate()
    except KeyboardInterrupt:
        odooproc.kill()


@cli.command("start")
@click.option("-i", "--init", type=list, cls=OptionEatAll)
@click.option("-u", "--update", type=list, cls=OptionEatAll)
@click.option(
    "-w",
    "--whatever",
    type=list,
    cls=OptionEatAll,
    save_other_options=False,
    help="Other options that can be passed to odoo-cli",
)
@click.pass_obj
def start_db(obj, init, update, whatever):
    """Start an existing instance."""
    dbname = obj["dbname"]
    port = obj["port"]
    config = obj["config"]
    try:
        command = odoo_run_command(config, dbname, init, update, port) + list(
            whatever or []
        )
        click.echo(f"Running: {' '.join(command)}\n")
        odooproc = subprocess.Popen(command)
        odooproc.communicate()
    except KeyboardInterrupt:
        odooproc.kill()


@cli.command("shell")
@click.option(
    "-w",
    "--whatever",
    type=list,
    cls=OptionEatAll,
    save_other_options=False,
    help="Other options that can be passed to odoo-cli.",
)
@click.pass_obj
def run_odoo_shell(obj, whatever):
    """Start a shell instance."""
    dbname = obj["dbname"]
    config = obj["config"]
    try:
        command = odoo_shell_command(config, dbname) + list(whatever or [])
        click.echo(f"Running: {' '.join(command)}\n")
        odooproc = subprocess.Popen(command)
        odooproc.communicate()
    except KeyboardInterrupt:
        odooproc.kill()


@cli.command("gen-kernelspec")
@click.option(
    "-w",
    "--whatever",
    type=list,
    cls=OptionEatAll,
    save_other_options=False,
    help="Other options that can be passed to odoo-cli.",
)
@click.pass_obj
def generate_kernelspec(obj, whatever):
    """Start a shell instance."""
    dbname = obj["dbname"]
    config = obj["config"]
    branch = obj["branch"]
    try:
        shell_command = odoo_shell_command(config, dbname, is_for_jupyter=True) + list(
            whatever or []
        )
        kernelspec_dict = {
            "argv": shell_command,
            "display_name": f"Odoo - {branch} - {dbname}",
            "language": "Python",
        }
        kernel_spec_to_install_dir = config["kernelspec-dir"] / branch / dbname
        kernel_spec_to_install_dir.mkdir(parents=True, exist_ok=True)
        with open(kernel_spec_to_install_dir / "kernel.json", "w+") as outfile:
            json.dump(kernelspec_dict, outfile, indent=2)

        install_kernelspec_command = [
            "jupyter",
            "kernelspec",
            "install",
            str(kernel_spec_to_install_dir),
            "--user",
        ]
        proc = subprocess.Popen(install_kernelspec_command)
        proc.communicate()
    except KeyboardInterrupt:
        proc.kill()


@cli.command("copy-db")
@click.argument("new-dbname")
@click.pass_obj
def copy_db(obj, new_dbname):
    """Duplicate an existing database."""
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


## REMOVE


@cli.command("remove")
@click.pass_obj
def delete_branch(obj):
    """Remove `prepared` branch (workstrees and workspace)."""
    config = obj["config"]
    if config["branch"] == "master":
        return
    delete_odoo_worktree_and_branch(config)
    delete_enterprise_worktree_and_branch(config)
    delete_branch_dir(config)


def delete_odoo_worktree_and_branch(config):
    branch = config["branch"]
    current_dir = os.getcwd()
    os.chdir(config["odoo-master-dir"])

    remove_dir_command = ["rm", "-rf", str(config["odoo-branch-dir"])]
    prune_worktree_command = ["git", "worktree", "prune"]
    delete_branch_command = ["git", "branch", "-D", branch]
    delete_workspace_command = [
        "rm",
        str(config["workspace-dir"] / f"{branch}.code-workspace"),
    ]

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


def delete_enterprise_worktree_and_branch(config):
    branch = config["branch"]
    current_dir = os.getcwd()
    os.chdir(config["enterprise-master-dir"])

    remove_dir_command = ["rm", "-rf", str(config["enterprise-branch-dir"])]
    prune_worktree_command = ["git", "worktree", "prune"]
    delete_branch_command = ["git", "branch", "-D", branch]
    for command in [remove_dir_command, prune_worktree_command, delete_branch_command]:
        out, err = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        ).communicate()
        if out:
            click.echo(out.decode("utf-8"))
        if err:
            click.echo(err.decode("utf-8"), err=True)
    os.chdir(current_dir)


def delete_branch_dir(config):
    branch = config["branch"]
    command = ["rm", "-rf", str(config["worktree-src"] / branch)]
    out, err = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).communicate()
    if out:
        click.echo(out.decode("utf-8"))
    if err:
        click.echo(err.decode("utf-8"), err=True)


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


def odoo_shell_command(config, dbname, is_for_jupyter=False):
    python = config["python"]
    odoobin = config["odoo-bin"]
    addons = config["addons-path"]
    command = (
        [python, odoobin, "shell"]
        + [f"--addons-path={','.join(addons)}"]
        + ["-d", dbname]
        + (["-f", "{connection_file}"] if is_for_jupyter else [])
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


@cli.command("cd")
@click.argument("repo")
@click.pass_obj
def change_dir(obj, repo):
    config = obj["config"]
    branch = obj["branch"]
    try_change = repo in ["odoo", "o", "enterprise", "e"]
    if branch == "master":
        if repo in ["odoo", "o"]:
            directory = config["odoo-master-dir"]
        elif repo in ["enterprise", "e"]:
            directory = config["enterprise-master-dir"]
    else:
        if repo in ["odoo", "o"]:
            directory = config["odoo-branch-dir"]
        elif repo in ["enterprise", "e"]:
            directory = config["enterprise-branch-dir"]
    if try_change:
        if directory.exists():
            if str(directory) != os.getcwd():
                os.chdir(str(directory))
                os.system("/bin/zsh")
        else:
            click.echo(f"`{branch}` is not yet checked out.", err=True)
    else:
        click.echo("repo can only be `odoo` or `enterprise`.", err=True)
