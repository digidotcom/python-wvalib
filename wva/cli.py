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
from wva.exceptions import WVAError, WVAHttpServiceUnavailableError, WVAHttpNotFoundError


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


def cli_pprint(data):
    # replace the unicode prefix for python 2.7
    output = pprint.pformat(data)
    print(output.replace("u'", "'"))


@click.group()
@click.option('--https/--no-https', default=True, help="Use HTTPS instead of HTTP")
@click.option('--hostname', default=None, help='Force use of the specified hostname')
@click.option('--username', default=None, help='Force use of the specified username')
@click.option('--password', default=None, help='Force use of the specified password')
@click.option("--config-dir", default="~/.wva", help='Directory containing wva configuration files')
@click.pass_context
def cli(ctx, hostname, username, password, config_dir, https):
    ctx.user_values_entered = False
    ctx.config_dir = os.path.abspath(os.path.expanduser(config_dir))
    ctx.config = load_config(ctx)
    ctx.hostname = get_hostname(ctx, hostname)
    ctx.username = get_username(ctx, username)
    ctx.password = get_password(ctx, password)
    if ctx.user_values_entered:
        if click.confirm("Save new values to config file?"):
            save_config(ctx)

    ctx.wva = WVA(ctx.hostname, ctx.username, ctx.password, https)


#
# Low-Level HTTP Access Commands
#
@cli.command()
@click.argument('path')
@click.pass_context
def get(ctx, path):
    http_client = get_wva(ctx).get_http_client()
    cli_pprint(http_client.get(path))


@cli.command()
@click.argument('path')
@click.pass_context
def delete(ctx, path):
    http_client = get_wva(ctx).get_http_client()
    cli_pprint(http_client.delete(path))


@cli.command()
@click.argument('path')
@click.argument('input_file', type=click.File())
@click.pass_context
def post(ctx, path, input_file):
    http_client = get_wva(ctx).get_http_client()
    cli_pprint(http_client.post(path, input_file.read()))


@cli.command()
@click.argument('path')
@click.argument('input_file', type=click.File())
@click.pass_context
def put(ctx, path, input_file):
    http_client = get_wva(ctx).get_http_client()
    cli_pprint(http_client.put(path, input_file.read()))


#
# Vehicle Data Command Group (wva vehicle ...)
#
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


#
# Subscription/Event Commands
#
@cli.group()
@click.pass_context
def subscriptions(ctx):
    pass


@subscriptions.command()
@click.pass_context
def list(ctx):
    wva = get_wva(ctx)
    for subscription in wva.get_subscriptions():
        print(subscription.short_name)


@subscriptions.command()
@click.argument("short_name")
@click.pass_context
def delete(ctx, short_name):
    wva = get_wva(ctx)
    subscription = wva.get_subscription(short_name)
    subscription.delete()


@subscriptions.command()
@click.argument("short_name")
@click.pass_context
def show(ctx, short_name):
    wva = get_wva(ctx)
    subscription = wva.get_subscription(short_name)
    cli_pprint(subscription.get_metadata())


@subscriptions.command()
@click.argument("short_name", "The short name of the subscription")
@click.argument("uri", "The URI for which the subscription should be created")
@click.option("--interval", default=5.0, help="How often should we receive updates for this URI")
@click.option("--buffer", default="queue")
@click.pass_context
def add(ctx, short_name, uri, interval, buffer):
    wva = get_wva(ctx)
    subscription = wva.get_subscription(short_name)
    subscription.create(uri, buffer, interval)


@subscriptions.command()
@click.pass_context
def listen(ctx):
    wva = get_wva(ctx)
    es = wva.get_event_stream()

    def cb(event):
        cli_pprint(event)

    es.add_event_listener(cb)
    es.enable()
    while True:
        time.sleep(5)


@subscriptions.command()
@click.argument("items", nargs=-1)
@click.option("--seconds", default=300, help="The number of seconds of history to graph")
@click.option("--ylim", default=1000, help="The Y Limit for the graph view area")
@click.pass_context
def graph(ctx, items, seconds, ylim):
    wva = get_wva(ctx)
    es = wva.get_event_stream()

    try:
        from wva import grapher
    except ImportError:
        print("Unable to graph... you must have matplotlib installed")
    else:
        stream_grapher = grapher.WVAStreamGrapher(wva, items, seconds=seconds, ylim=ylim)
        es.enable()
        stream_grapher.run()

#
# SSH
#
@cli.group()
@click.pass_context
def ssh(ctx):
    """Enable SSH access to a device"""


@ssh.command()
@click.option("--public-key", type=click.File(),
              default=os.path.expanduser("~/.ssh/id_rsa.pub"), help="The public key to use")
@click.option("--append/--no-append", default=False, help="Append to the authorized_keys")
@click.pass_context
def authorize(ctx, public_key, append):
    """Enable ssh login as the Python user for the current user

This command will create an authorized_keys file on the target device
containing the current users public key.  This will allow ssh to
the WVA from this machine.
"""
    wva = get_wva(ctx)

    http_client = wva.get_http_client()
    authorized_keys_uri = "/files/userfs/WEB/python/.ssh/authorized_keys"
    authorized_key_contents = public_key
    if append:
        try:
            existing_contents = http_client.get(authorized_keys_uri)
            authorized_key_contents = "{}\n{}".format(existing_contents, public_key)
        except WVAHttpNotFoundError:
            pass  # file doesn't exist, just write the public key
    http_client.put(authorized_keys_uri, authorized_key_contents)

    print("Public key written to authorized_keys for python user.")
    print("You should now be able to ssh to the device by doing the following:")
    print("")
    print("  $ ssh python@{}".format(get_root_ctx(ctx).hostname))


def main():
    import logging
    logging.basicConfig()
    cli(auto_envvar_prefix="WVA")


if __name__ == "__main__":
    main()
