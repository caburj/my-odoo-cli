import click
import os

from ..utils import run, HOME, identify_current, get_base_branch
from ..main import main


@main.command("remove")
@click.argument("name", required=False)
@click.option("-d", "--drop-dbs", is_flag=True, default=False)
@click.pass_obj
@identify_current
def remove(obj, name, drop_dbs):
    base_branch, name = get_base_branch(name)
    _, odoo_base_worktree_dir = obj.get_dirs("odoo", base_branch)
    _, ent_base_worktree_dir = obj.get_dirs("enterprise", base_branch)
    upgrade_dir, _ = obj.get_dirs("upgrade", base_branch)

    delete_branch(name, odoo_base_worktree_dir, base_branch)
    delete_branch(name, ent_base_worktree_dir, base_branch)
    delete_branch(name, upgrade_dir, base_branch="master")
    if drop_dbs:
        run(["odev", "drop", name, "--all"])
    obj.remove_current()


def delete_branch(name, repo_dir, base_branch):
    os.chdir(repo_dir)
    run(["git", "checkout", base_branch])
    run(["git", "branch", "-D", name])
