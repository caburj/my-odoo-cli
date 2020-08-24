import click
import os

from ..utils import identify_current
from ..main import main


@main.command("cd")
@click.argument("name", required=False)
@click.pass_obj
@identify_current
def cd(obj, name):
    odoo_dir, odoo_worktree_dir = obj.get_dirs("odoo", name)

    if name == "src":
        if str(odoo_dir) != os.getcwd():
            os.chdir(str(odoo_dir))
            os.system("/bin/zsh")
            return

    if odoo_worktree_dir.exists():
        if str(odoo_worktree_dir) != os.getcwd():
            os.chdir(str(odoo_worktree_dir))
            os.system("/bin/zsh")
    else:
        click.echo(f"`{name}` is not yet checked out.", err=True)
