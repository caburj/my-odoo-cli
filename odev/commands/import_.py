import os
import tempfile
from pathlib import Path

import click

from ..utils import run, identify_current
from ..main import main


@main.command("import")
@click.argument("name", required=False)
@click.option("-z", "--zipfile", type=click.Path(exists=True))
@click.option("-s", "--suffix")
@click.pass_obj
@identify_current
def import_(obj, name, zipfile, suffix):
    dbname = f"{name}{f'-{suffix}' if suffix else ''}"

    with tempfile.TemporaryDirectory() as tempdir:
        temppath = Path(tempdir)
        run(["unzip", zipfile, "-d", tempdir])
        dumpfile = temppath / "dump.sql"
        filestore = temppath / "filestore"
        if (obj.filestore / dbname).exists():
            run(["rm", "-rf", str(obj.filestore / dbname)])
        run(["cp", "-r", str(filestore), str(obj.filestore / dbname)])
        run(["createdb", dbname])
        run(["psql", "-U", os.getlogin(), "-d", dbname, "-f", str(dumpfile)])

    return 0
