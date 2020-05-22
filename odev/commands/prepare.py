import click
import os
import json

from ..utils import return_to_cwd, run
from ..main import main


@main.command("prepare")
@click.argument("new-branch")
@click.option("-p", "--pull", is_flag=True, default=False)
@click.pass_obj
def prepare(obj, new_branch, pull):
    """Check out appropriate branch to worktrees (both community and enterprise).
    
    NEW_BRANCH should have a name prefixed with the name of the base branch.
        e.g. master-new-featuer, 13.0-fix-something
    """
    # compute base branch based on the name of the new branch
    base_branch = new_branch.split("-")[0]

    odoo_dir, odoo_worktree_dir = obj.get_dirs("odoo", new_branch)
    ent_dir, ent_worktree_dir = obj.get_dirs("enterprise", new_branch)
    up_dir, up_worktree_dir = obj.get_dirs("upgrade", new_branch)

    normal_checkout(odoo_dir, base_branch)
    create_worktree(base_branch, new_branch, odoo_dir, odoo_worktree_dir, pull)

    normal_checkout(ent_dir, base_branch)
    create_worktree(base_branch, new_branch, ent_dir, ent_worktree_dir, pull)

    create_upgrade_worktree(new_branch, up_dir, up_worktree_dir, pull)

    create_workspace(
        obj.workspaces, new_branch, odoo_worktree_dir, ent_worktree_dir, up_worktree_dir
    )
    create_launch_json(new_branch, obj.port, odoo_worktree_dir, ent_worktree_dir)

    obj.set_current(new_branch)


@return_to_cwd
def create_worktree(base_branch, new_branch, src_dir, worktree_dir, pull):
    os.chdir(src_dir)
    if pull:
        run(["git", "pull", "origin", base_branch])
    checkout_worktree(worktree_dir, new_branch)


@return_to_cwd
def create_upgrade_worktree(new_branch, src_dir, worktree_dir, pull):
    os.chdir(src_dir)
    if pull:
        run(["git", "pull", "origin", "master"])

    checkout_worktree(worktree_dir, new_branch)

@return_to_cwd
def normal_checkout(src_dir, branch):
    os.chdir(src_dir)
    successful, *_ = run(["git", "checkout", branch])
    if not successful:
        click.echo(f"Failed to checkout base branch: '{branch}'", err=True)
        exit(1)


def checkout_worktree(worktree_dir, new_branch):
    worktree_add = ["git", "worktree", "add"]
    successful, *_ = run([*worktree_add, "--checkout", str(worktree_dir), new_branch])
    if successful:
        return
    successful, *_ = run([*worktree_add, str(worktree_dir), new_branch])
    if successful:
        return
    run([*worktree_add, "-b", new_branch, str(worktree_dir)])


def create_workspace(workspaces, branch_name, odoo_worktree, ent_worktree, up_worktree):
    workspace = {
        "folders": [
            {"path": str(odoo_worktree)},
            {"path": str(ent_worktree)},
            {"path": str(up_worktree)},
        ]
    }
    if not workspaces.exists():
        workspaces.mkdir(parents=True, exist_ok=True)
    with open(workspaces / f"{branch_name}.code-workspace", "w+") as f:
        json.dump(workspace, f, indent=4)


def create_launch_json(new_branch, def_port, odoo_worktree, enterprise_worktree):
    addons = [
        str(enterprise_worktree),
        str(odoo_worktree / "addons"),
        str(odoo_worktree / "odoo" / "addons"),
    ]
    command = (
        [f"--addons-path={','.join(addons)}"]
        + ["-d", new_branch]
        + ["--xmlrpc-port", def_port]
    )
    launch = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "odoo-bin",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/odoo-bin",
                "console": "integratedTerminal",
                "args": command,
            }
        ],
    }
    vscode_dir = odoo_worktree / ".vscode"
    if not vscode_dir.exists():
        vscode_dir.mkdir(parents=True, exist_ok=True)
    with open(vscode_dir / f"launch.json", "w+") as f:
        json.dump(launch, f, indent=4)
