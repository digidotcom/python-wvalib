#!/usr/bin/env python
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
import json
import pprint
import time

from core import WVA
import click
import os
from wva.exceptions import WVAError, WVAHttpServiceUnavailableError


def load_config(ctx):
    try:
        with open(os.path.join(ctx.config_dir, "config.json")) as f:
            return json.load(f)
    except (IOError, ValueError):
        return {}


def save_config(ctx):
    if not os.path.exists(ctx.config_dir):
        os.makedirs(ctx.config_dir)

    config = {
        "version": 1,  # may be used for migration purposes
        "hostname": ctx.hostname,
        "username": ctx.username,
        "password": ctx.password,
    }

    # Write config to a file that is restricted to read/write access by current user
    fd = os.open(os.path.join(ctx.config_dir, "config.json"), os.O_WRONLY | os.O_CREAT, 0o0600)
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


def get_root_ctx(ctx):
    while True:
        if hasattr(ctx, 'wva'):
            return ctx
        ctx = ctx.parent


def get_wva(ctx):
    return get_root_ctx(ctx).wva


@click.group()
@click.option('--hostname', default=None, help='Force use of the specified hostname')
@click.option('--username', default=None, help='Force use of the specified username')
@click.option('--password', default=None, help='Force use of the specified password')
@click.option("--config-dir", default="~/.wva", help='Directory containing wva configuration files')
@click.pass_context
def cli(ctx, hostname, username, password, config_dir):
    ctx.user_values_entered = False
    ctx.config_dir = os.path.abspath(os.path.expanduser(config_dir))
    ctx.config = load_config(ctx)
    ctx.hostname = get_hostname(ctx, hostname)
    ctx.username = get_username(ctx, username)
    ctx.password = get_password(ctx, password)
    if ctx.user_values_entered:
        if click.confirm("Save new values to config file?"):
            save_config(ctx)

    ctx.wva = WVA(ctx.hostname, ctx.username, ctx.password)


## Low-Level HTTP Access Commands
@cli.command()
@click.argument('path')
@click.pass_context
def get(ctx, path):
    http_client = get_wva(ctx).get_http_client()
    print(http_client.get(path))


@cli.command()
@click.argument('path')
def delete(ctx, path):
    http_client = get_wva(ctx).get_http_client()
    print(http_client.delete(path))


@cli.command()
@click.argument('path')
@click.argument('input_file', type=click.File())
@click.pass_context
def post(ctx, path, input_file):
    http_client = get_wva(ctx).get_http_client()
    print(http_client.post(path, input_file.read()))


@cli.command()
@click.argument('path')
@click.argument('input_file', type=click.File())
@click.pass_context
def put(ctx, path, input_file):
    http_client = get_wva(ctx).get_http_client()
    print(http_client.put(path, input_file.read()))


## Vehicle Data Command Group (wva vehicle ...)
@cli.group(short_help="Vehicle Data Commands")
@click.pass_context
def vehicle(ctx):
    pass


@vehicle.command(short_help="List available vehicle data items")
@click.option("--value/--no-value", default=False, help="Get the currently value as well")
@click.option('--timestamp/--no-timestamp', default=False, help="Also print the timestamp of the sample")
@click.pass_context
def list(ctx, value, timestamp):
    for name, element in sorted(get_wva(ctx).get_vehicle_data_elements().items(), key=lambda (k, v): k):
        if value:
            try:
                curval = element.sample()
            except WVAHttpServiceUnavailableError:
                print("{} (Unavailable)".format(name))
            except WVAError, e:
                print("{} (Error: {})".format(name, e))
            else:
                if timestamp:
                    print("{} = {} at {}".format(name, curval.value, curval.timestamp.ctime()))
                else:
                    print("{} = {}".format(name, curval.value))
        else:
            print(name)


@vehicle.command(short_help="Get the current value of a vehicle data element")
@click.argument('element')
@click.option('--timestamp/--no-timestamp', default=False, help="Also print the timestamp of the sample")
@click.option('--repeat', default=1, help="How many times to sample")
@click.option('--delay', default=0.5, help="Time to delay between samples in seconds")
@click.pass_context
def sample(ctx, element, timestamp, repeat, delay):
    element = get_wva(ctx).get_vehicle_data_element(element)
    for i in xrange(repeat):
        curval = element.sample()
        if timestamp:
            print("{} at {}".format(curval.value, curval.timestamp.ctime()))
        else:
            print("{}".format(curval.value))

        if i + 1 < repeat:  # do not delay on last iteration
            time.sleep(delay)


def main():
    cli(auto_envvar_prefix="WVA")


if __name__ == "__main__":
    main()
