import click
import os

from ..utils import identify_current, get_base_branch
from ..main import main


@main.command("cd")
@click.argument("name", required=False)
@click.pass_obj
@identify_current
def cd(obj, name):
    base_branch_name, name = get_base_branch(name)
    _, odoo_worktree_dir = obj.get_dirs("odoo", base_branch_name)

    if odoo_worktree_dir.exists():
        if str(odoo_worktree_dir) != os.getcwd():
            os.chdir(str(odoo_worktree_dir))
            os.system("/bin/zsh")
    else:
        click.echo(f"`{base_branch_name}` is not yet checked out.", err=True)
