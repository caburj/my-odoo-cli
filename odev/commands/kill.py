import subprocess
import click

from ..utils import run, odoo_bin_proc_ids, identify_current
from ..main import main


@main.command("kill")
@click.argument("name", required=False)
@click.pass_obj
@identify_current
def kill(obj, name):
    for proc_id in odoo_bin_proc_ids(name):
        run(["sudo", "kill", "-9", proc_id])
