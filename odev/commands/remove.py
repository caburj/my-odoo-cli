import click
import os

from ..utils import run, HOME, identify_current
from ..main import main


@main.command("remove")
@click.argument("name", required=False)
@click.option("-d", "--drop-dbs", is_flag=True, default=False)
@click.pass_obj
@identify_current
def remove(obj, name, drop_dbs):
    odoo_dir, _ = obj.get_dirs("odoo", name)
    enterprise_dir, _ = obj.get_dirs("enterprise", name)
    upgrade_dir, _ = obj.get_dirs("upgrade", name)

    delete_worktrees(name, obj.workspaces, obj.worktrees)
    delete_branch(name, odoo_dir)
    delete_branch(name, enterprise_dir)
    delete_branch(name, upgrade_dir)
    if drop_dbs:
        run(["odev", "drop", name, "--all"])
    obj.remove_current()


def delete_worktrees(name, workspaces, worktrees):
    os.chdir(str(HOME))
    run(["rm", "-rf", str(worktrees / name)])
    run(["rm", str(workspaces / f"{name}.code-workspace")])


def delete_branch(name, repo_dir):
    os.chdir(repo_dir)
    run(["git", "worktree", "prune"])
    run(["git", "branch", "-D", name])
