#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
import json
import pprint

from core import WVA
import click
import os


CONFIG_DIR = os.path.abspath(os.environ.get('WVA_CONFIGDIR', os.path.expanduser("~/.wva")))


def load_config():
    try:
        with open(os.path.join(CONFIG_DIR, "config.json")) as f:
            return json.load(f)
    except (IOError, ValueError):
        return {}


def save_config(ctx):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    config = {
        "hostname": ctx.hostname,
        "username": ctx.username,
        "password": ctx.password,
    }

    # Write config to a file that is restricted to read/write access by current user
    fd = os.open(os.path.join(CONFIG_DIR, "config.json"), os.O_WRONLY | os.O_CREAT, 0o0600)
    with os.fdopen(fd, 'w') as f:
        f.write(json.dumps(config, indent=2))


def get_config_value(ctx, key, prompt, override_value, password=False):
    if override_value is not None:
        value = override_value
    elif ctx.config.get(key) is not None:
        value = ctx.config[key]
    else:
        value = click.prompt(prompt, hide_input=password)
        ctx.user_values_entered = True

    return value


def get_hostname(ctx, override_hostname=None):
    return get_config_value(ctx, 'hostname', "WVA Hostname", override_hostname)


def get_username(ctx, override_username=None):
    return get_config_value(ctx, 'username', "Username", override_username)


def get_password(ctx, override_password=None):
    return get_config_value(ctx, 'password', 'Password', override_password, password=True)


@click.group()
@click.option('--hostname', default=None, help='Force use of the specified hostname')
@click.option('--username', default=None, help='Force use of the specified username')
@click.option('--password', default=None, help='Force use of the specified password')
@click.pass_context
def cli(ctx, hostname, username, password):
    ctx.config = load_config()
    ctx.user_values_entered = False
    ctx.hostname = get_hostname(ctx, hostname)
    ctx.username = get_username(ctx, username)
    ctx.password = get_password(ctx, password)
    if ctx.user_values_entered:
        if click.confirm("Save new values to config file?"):
            save_config(ctx)

    ctx.wva = WVA(ctx.hostname, ctx.username, ctx.password)


@cli.command()
@click.argument('path')
@click.pass_context
def get(ctx, path):
    pprint.pprint(ctx.parent.wva.get(path))


@cli.command()
@click.argument('path')
def delete(ctx, path):
    pprint.pprint(ctx.parent.wva.delete(path))


@cli.command()
@click.argument('path')
@click.argument('input_file', type=click.File())
@click.pass_context
def post(ctx, path, input_file):
    pprint.pprint(ctx.parent.wva.post(path, input_file.read()))


@cli.command()
@click.argument('path')
@click.argument('input_file', type=click.File())
@click.pass_context
def put(ctx, path, input_file):
    pprint.pprint(ctx.parent.wva.put(path, input_file.read()))


def main():
    cli(auto_envvar_prefix="WVA")


if __name__ == "__main__":
    main()
