import click

from ..main import main


@main.command("select")
@click.argument("index", type=int)
@click.pass_obj
def select(obj, index):
    worktrees = obj.list_worktrees()
    if index >= len(worktrees):
        click.echo("Invalid index.", err=True)
        exit(1)
    selected = worktrees[index]
    obj.set_current(selected)
