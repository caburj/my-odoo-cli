import click

from ..main import main


@main.command("current")
@click.pass_obj
def current(obj):
    click.echo(f"{obj.get_current()}")
