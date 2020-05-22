import click
import os

from .utils import OdevContextObject


@click.group()
@click.pass_context
def main(ctx):
    ctx.obj = OdevContextObject()


from . import commands
