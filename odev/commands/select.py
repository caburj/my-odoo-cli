import click

from ..main import main


@main.command("select")
@click.option("-s", "--search-string")
@click.option("-i", "--index", default=0)
@click.pass_obj
def select(obj, search_string, index=0):
    worktrees = obj.list_worktrees(search_string)
    if len(worktrees) == 0:
        click.echo(f"No result for '{search_string}'.")
        exit(1)
    if len(worktrees) == 1:
        index = 0
    if index >= len(worktrees):
        click.echo("Invalid index.", err=True)
        exit(1)
    selected = worktrees[index]
    obj.set_current(selected)
    click.echo(f"{selected} is selected.")
