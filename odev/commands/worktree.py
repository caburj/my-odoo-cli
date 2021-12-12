import click
import os

from ..utils import run
from ..main import main


@main.command("worktree")
@click.argument("branch")
@click.option("--remove", is_flag=True, default=False)
@click.pass_obj
def worktree(obj, branch, remove):
    branch_worktree_dir = obj.worktrees / branch
    odoo_dir = branch_worktree_dir / "odoo"
    ent_dir = branch_worktree_dir / "enterprise"

    for _dir in [branch_worktree_dir, odoo_dir, ent_dir]:
        if not os.path.isdir(_dir):
            os.mkdir(_dir)
            click.echo(f"{_dir} created.")
        else:
            click.echo(f"{_dir} already exist.")

    odoo_src = obj.src / "odoo"
    ent_src = obj.src / "enterprise"

    for [wt_dir, src] in [[odoo_dir, odoo_src], [ent_dir, ent_src]]:
        os.chdir(src)
        click.echo(f"cd {src}")
        run(f"git worktree add {wt_dir} {branch}".split(" "))
