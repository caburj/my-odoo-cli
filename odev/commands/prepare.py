import click
import os
import json

from ..utils import return_to_cwd, run, get_base_branch
from ..persist import add_to_list
from ..main import main

# TODO: add a way to prepare from odoo-dev remote (useful for failed forward port)
@main.command("prepare")
@click.argument("new-branch")
@click.option("-p", "--pull", is_flag=True, default=False)
@click.option("-r", "--from-remote", is_flag=True, default=False)
@click.option("-o", "--open-workspace", is_flag=True, default=True)
@click.pass_obj
def prepare(obj, new_branch, pull, from_remote, open_workspace):
    """Check out appropriate branch to worktrees (both community and enterprise).

    NEW_BRANCH should have a name prefixed with the name of the base branch
    separated by hyphen. e.g. master-new-feature, 13.0-fix-something,
    saas-13.4-change-tour-message
    """
    original_name = new_branch
    base_branch, new_branch = get_base_branch(new_branch)

    _, odoo_base_worktree_dir = obj.get_dirs("odoo", base_branch)
    _, ent_base_worktree_dir = obj.get_dirs("enterprise", base_branch)
    up_dir, _ = obj.get_dirs("upgrade", base_branch)

    create_branch(base_branch, new_branch, odoo_base_worktree_dir, pull, from_remote)
    create_branch(base_branch, new_branch, ent_base_worktree_dir, pull, from_remote)
    create_upgrade_branch(new_branch, up_dir, pull, from_remote)

    add_to_list("all", original_name)
    obj.set_current(original_name)

    if open_workspace:
        run(["odev", "code"])


@return_to_cwd
def create_branch(base_branch, new_branch, worktree_dir, pull, from_remote):
    os.chdir(worktree_dir)
    run(["git", "checkout", base_branch])
    if pull:
        run(["git", "pull", "origin", base_branch])
    checkout_new_branch(worktree_dir, new_branch, from_remote)


@return_to_cwd
def create_upgrade_branch(new_branch, src_dir, pull, from_remote):
    os.chdir(src_dir)
    run(["git", "checkout", "master"])
    if pull:
        run(["git", "pull", "origin", "master"])
    checkout_new_branch(src_dir, new_branch, from_remote)


def checkout_new_branch(worktree_dir, new_branch, from_remote):
    if from_remote:
        run(["git", "fetch", "odoo-dev", new_branch])
        run(["git", "checkout", "-t", f"odoo-dev/{new_branch}"])
    else:
        run(["git", "checkout", "-b", new_branch])
