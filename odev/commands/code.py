import click

from ..main import main
from ..utils import run, get_base_branch


@main.command("code")
@click.pass_obj
def code(obj):
    base_branch, _ = get_base_branch(obj.get_current())
    workspace_dir = obj.get_workspace_dir(base_branch)
    run(["code", workspace_dir])
