import subprocess
import click

from ..utils import run, identify_current
from ..main import main


@main.command("listdb")
@click.argument("name", required=False)
@click.pass_obj
@identify_current
def listdb(obj, name):
    proc = subprocess.Popen(f"psql -l|awk '{{print $1}}'|grep -w {name}", shell=True)
    proc.communicate()
    return proc.returncode
