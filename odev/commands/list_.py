import click

from ..main import main


@main.command("list")
@click.option("-s", "--search-string")
@click.pass_obj
def list_(obj, search_string):
    worktrees = obj.list_worktrees(search_string)
    current = obj.get_current()
    for i, worktree in enumerate(worktrees):
        marker = "*" if worktree == current else ""
        click.echo(f"{i:<3}{marker}{worktree}{marker}")
