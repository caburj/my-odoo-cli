import os
import re
import click
import subprocess
from configparser import ConfigParser

from pathlib import Path

from . import persist

HOME = Path("~").expanduser()


class OdevContextObject:
    def __init__(self):
        config = ConfigParser()
        config.read(HOME / ".odev")
        self.src = Path(config["DEFAULT"].get("src")).expanduser()
        self.worktrees = Path(config["DEFAULT"].get("worktrees")).expanduser()
        self.workspaces = Path(config["DEFAULT"].get("workspaces")).expanduser()
        self.filestore = Path(config["DEFAULT"].get("filestore")).expanduser()
        self.port = config["DEFAULT"].get("port")

    def set_current(self, name):
        persist.save("current", name)

    def remove_current(self):
        persist.remove("current")

    def get_current(self):
        return persist.get("current")

    def get_dirs(self, repo, branch):
        return (self.src / repo, self.worktrees / branch / repo)

    def identify_name(self):
        cwd = os.getcwd()
        try:
            return re.match(
                f"({str(self.worktrees)})/(.*)/((odoo|enterprise).*)", cwd
            ).group(2)
        except Exception:
            return self.get_current()

    def get_addons(self, name, no_enterprise=False, from_src=False):
        enterprise_worktree = (
            self.worktrees / name / "enterprise"
            if not from_src
            else self.src / "enterprise"
        )
        odoo_worktree = (
            self.worktrees / name / "odoo" if not from_src else self.src / "odoo"
        )
        enterprise = [] if no_enterprise else [str(enterprise_worktree)]
        return ",".join(
            [
                *enterprise,
                str(odoo_worktree / "addons"),
                str(odoo_worktree / "odoo" / "addons"),
            ]
        )

    def get_python(self):
        _, out, _ = run(["which", "python"])
        return out.decode("utf-8").strip()

    def get_odoo_bin(self, name, from_src=False):
        if from_src:
            return str(self.src / "odoo" / "odoo-bin")
        return str(self.worktrees / name / "odoo" / "odoo-bin")

    def init_db(self, name, dbname, modules=None, no_demo=None):
        python = self.get_python()
        odoobin = self.get_odoo_bin(name)
        command = (
            [python, odoobin]
            + ["--addons-path", self.get_addons(name)]
            + ["-d", dbname]
            + (["-i", modules] if modules else [])
            + (["--without-demo", "ALL"] if no_demo else [])
            + (["--stop-after-init"])
        )
        return command

    def list_worktrees(self, search_string=False):
        return [
            dI
            for dI in os.listdir(str(self.worktrees))
            if os.path.isdir(os.path.join(str(self.worktrees), dI))
            if (search_string or "") in dI
        ]

    def dropdb(self, dbname):
        return ["dropdb", dbname]

    def copydb(self, olddbname, newdbname):
        return ["createdb", "-O", os.environ.get("USER"), "-T", olddbname, newdbname]

    def drop_filestore(self, name):
        return ["rm", "-rf", str(self.filestore / name)]

    def copy_filestore(self, olddbname, newdbname):
        return [
            "cp",
            "-r",
            str(self.filestore / olddbname),
            str(self.filestore / newdbname),
        ]


def run(command, verbose=False):
    str_command = f"{' '.join(command)}"
    if verbose:
        try:
            click.echo(str_command)
            process = subprocess.Popen(command)
            out, err = process.communicate()
            return process.returncode == 0, out, err
        except KeyboardInterrupt:
            process.kill()
            return exit(1)

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    click.echo(f"{str_command} : {process.returncode}")
    return process.returncode == 0, out, err


def return_to_cwd(func):
    def wrapped(*args, **kwargs):
        current_dir = os.getcwd()
        result = func(*args, **kwargs)
        new_current_dir = os.getcwd()
        if current_dir != new_current_dir:
            os.chdir(current_dir)
        return result

    return wrapped


def get_dbs(subname):
    command = f"psql -l|awk '{{print $1}}'|grep -w {subname}"
    ps = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return ps.communicate()[0].decode("utf-8").strip().split("\n")


def db_exists(name):
    return name in get_dbs(name)


def odoo_bin_proc_ids(name=False):
    if not name:
        command = f"ps aux|grep odoo-bin|grep python|awk '{{print $2}}'"
    else:
        regex = f"{name}.*odoo-bin"
        command = f"ps aux|grep {regex}|grep python|awk '{{print $2}}'"
    ps = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    return ps.communicate()[0].decode("utf-8").strip().split("\n")[:-1]


def identify_current(func):
    def wrapped(obj, name, *args, **kwargs):
        if not name:
            name = obj.identify_name()
        if not name:
            click.echo("Please select a dev env name.\ntry: $ odev list")
            exit(1)
        result = func(obj, name, *args, **kwargs)
        return result

    return wrapped
