import click
import os

from ..main import main
from ..utils import run, get_base_branch, return_to_cwd


@main.command("select")
@click.option("-s", "--search-string")
@click.option("-i", "--index", default=0)
@click.option("-o", "--open-workspace", is_flag=True, default=True)
@click.pass_obj
def select(obj, search_string, index, open_workspace):
    branches = obj.list_branches(search_string)
    if len(branches) == 0:
        click.echo(f"No result for '{search_string}'.")
        exit(1)
    if len(branches) == 1:
        index = 0
    if index >= len(branches):
        click.echo("Invalid index.", err=True)
        exit(1)
    selected = branches[index]
    obj.set_current(selected)
    click.echo(f"{selected} is selected.")

    base_branch, selected = get_base_branch(selected)
    _, odoo_worktree_dir = obj.get_dirs("odoo", base_branch)
    _, ent_worktree_dir = obj.get_dirs("enterprise", base_branch)
    upgrade_dir, _ = obj.get_dirs("upgrade", base_branch)

    normal_checkout(odoo_worktree_dir, selected)
    normal_checkout(ent_worktree_dir, selected)
    normal_checkout(upgrade_dir, selected)

    if open_workspace:
        run(["odev", "code"])


@return_to_cwd
def normal_checkout(src_dir, branch):
    os.chdir(src_dir)
    run(["git", "checkout", branch])
