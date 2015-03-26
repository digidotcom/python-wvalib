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
import sys

from core import WVA
import click
import os
from wva.exceptions import WVAError, WVAHttpServiceUnavailableError, WVAHttpNotFoundError


def load_config(ctx):
    try:
        with open(os.path.join(ctx.config_dir, "config.json")) as f:
            return json.load(f)
    except (OSError, IOError, ValueError):
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


def clear_config(ctx):
    config_json = os.path.join(ctx.config_dir, "config.json")
    if os.path.exists(config_json):
        try:
            os.remove(config_json)
        except (IOError, OSError):
            print("Failed to remove config.json")


def get_config_value(ctx, key, prompt, current_value, password=False):
    if current_value is not None:
        value = current_value
    elif ctx.config.get(key) is not None:
        value = ctx.config[key]
    else:
        value = click.prompt(prompt, hide_input=password)
        ctx.user_values_entered = True

    return value


def get_hostname(ctx):
    return get_config_value(ctx, 'hostname', "WVA Hostname", ctx.hostname)


def get_username(ctx):
    return get_config_value(ctx, 'username', "Username", ctx.username)


def get_password(ctx):
    return get_config_value(ctx, 'password', 'Password', ctx.password, password=True)


def get_root_ctx(ctx):
    while not getattr(ctx, 'is_root', False):
        ctx = ctx.parent
    return ctx


def get_wva(ctx):
    root_ctx = get_root_ctx(ctx)
    if root_ctx.wva is None:
        root_ctx.hostname = get_hostname(root_ctx)
        root_ctx.username = get_username(root_ctx)
        root_ctx.password = get_password(root_ctx)
        root_ctx.wva = WVA(root_ctx.hostname, root_ctx.username, root_ctx.password, root_ctx.https)
        if root_ctx.user_values_entered:
            if click.confirm("Save new values to config file?", default=True):
                save_config(root_ctx)

    return root_ctx.wva


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
    """Command-line interface for interacting with a WVA device"""
    ctx.is_root = True
    ctx.user_values_entered = False
    ctx.config_dir = os.path.abspath(os.path.expanduser(config_dir))
    ctx.config = load_config(ctx)
    ctx.hostname = hostname
    ctx.username = username
    ctx.password = password
    ctx.https = https

    # Creating the WVA object is deferred as some commands like clearconfig
    # should not require a username/password to perform them
    ctx.wva = None


#
# Plumbing
#
@cli.group()
@click.pass_context
def cliconfig(ctx):
    """View and clear CLI config"""


@cliconfig.command()
@click.pass_context
def show(ctx):
    """Show the current configuration"""
    cli_pprint(get_root_ctx(ctx).config)


@cliconfig.command()
@click.pass_context
def clear(ctx):
    """Clear the local WVA configuration

Note that this command does not impact any settings on any WVA device and
only impacts that locally stored settings used by the tool.  This configuration
is usually stored in ~/.wva/config.json and includes the WVA hostname, username,
and password settings.
"""
    clear_config(get_root_ctx(ctx))


#
# Low-Level HTTP Access Commands
#
@cli.command()
@click.argument('uri')
@click.pass_context
def get(ctx, uri):
    """Perform an HTTP GET of the provided URI

The URI provided is relative to the /ws base to allow for easy navigation of
the resources exposed by the WVA.  Example Usage::

\b
    $ wva get /
    {'ws': ['vehicle',
             'hw',
             'config',
             'state',
             'files',
             'alarms',
             'subscriptions',
             'password']}
    $ wva get /vehicle
    {'vehicle': ['vehicle/ecus', 'vehicle/data', 'vehicle/dtc']}
    $ wva get /vehicle/ecus
    {'ecus': ['vehicle/ecus/can0ecu0', 'vehicle/ecus/can0ecu251']}
    $ wva get /vehicle/ecus/can0ecu0
    {'can0ecu0': ['vehicle/ecus/can0ecu0/name',
           'vehicle/ecus/can0ecu0/address',
           'vehicle/ecus/can0ecu0/function',
           'vehicle/ecus/can0ecu0/bus',
           'vehicle/ecus/can0ecu0/channel',
           'vehicle/ecus/can0ecu0/make',
           'vehicle/ecus/can0ecu0/model',
           'vehicle/ecus/can0ecu0/serial_number',
           'vehicle/ecus/can0ecu0/unit_number',
           'vehicle/ecus/can0ecu0/VIN']}
    $ wva get /vehicle/ecus/can0ecu0/bus
    {'bus': 'J1939'}
    """
    http_client = get_wva(ctx).get_http_client()
    cli_pprint(http_client.get(uri))


@cli.command()
@click.argument('uri')
@click.pass_context
def delete(ctx, uri):
    """DELETE the specified URI

Example:

\b
    $ wva get files/userfs/WEB/python
    {'file_list': ['files/userfs/WEB/python/.ssh',
                    'files/userfs/WEB/python/README.md']}
    $ wva delete files/userfs/WEB/python/README.md
    ''
    $ wva get files/userfs/WEB/python
    {'file_list': ['files/userfs/WEB/python/.ssh']}
    """
    http_client = get_wva(ctx).get_http_client()
    cli_pprint(http_client.delete(uri))


@cli.command()
@click.argument('uri')
@click.argument('input_file', type=click.File())
@click.pass_context
def post(ctx, uri, input_file):
    """POST file data to a specific URI

Note that POST is not used for most web services URIs.  Instead,
PUT is used for creating resources.
    """
    http_client = get_wva(ctx).get_http_client()
    cli_pprint(http_client.post(uri, input_file.read()))


@cli.command()
@click.argument('uri')
@click.argument('input_file', type=click.File())
@click.pass_context
def put(ctx, uri, input_file):
    """PUT file data to a specific URI

Example:

\b
    $ wva get /files/userfs/WEB/python
    {'file_list': ['files/userfs/WEB/python/.ssh']}
    $ wva put /files/userfs/WEB/python/README.md README.md
    ''
    $ wva get /files/userfs/WEB/python
    {'file_list': ['files/userfs/WEB/python/.ssh',
                'files/userfs/WEB/python/README.md']}
    """
    http_client = get_wva(ctx).get_http_client()
    cli_pprint(http_client.put(uri, input_file.read()))


#
# Vehicle Data Command Group (wva vehicle ...)
#
@cli.group()
@click.pass_context
def vehicle(ctx):
    """Vehicle Data Commands"""


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
    """Sample the value of a vehicle data element

This command allows for the current value of a vehicle data element
to be sampled:

\b
    $ wva vehicle sample VehicleSpeed
    168.15329

Optionally, the value may be samples multiple times:

\b
    $ wva vehicle sample VehicleSpeed --repeat 10 --delay 1 --timestamp
    148.076462 at Tue Mar 24 23:52:56 2015
    145.564896 at Tue Mar 24 23:52:57 2015
    143.057251 at Tue Mar 24 23:52:58 2015
    138.03804 at Tue Mar 24 23:52:59 2015
    135.526474 at Tue Mar 24 23:53:00 2015
    133.018829 at Tue Mar 24 23:53:01 2015
    130.507263 at Tue Mar 24 23:53:02 2015
    127.999619 at Tue Mar 24 23:53:03 2015
    125.48806 at Tue Mar 24 23:53:04 2015
    122.976501 at Tue Mar 24 23:53:05 2015

For receiving large amounts of data on a periodic basis, use of subscriptions
and streams is enocuraged as it will be significantly more efficient.
"""
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
    """View and Edit subscriptions"""


@subscriptions.command()
@click.pass_context
def list(ctx):
    """List short name of all current subscriptions"""
    wva = get_wva(ctx)
    for subscription in wva.get_subscriptions():
        print(subscription.short_name)


@subscriptions.command()
@click.argument("short_name")
@click.pass_context
def delete(ctx, short_name):
    """Delete a specific subscription by short name"""
    wva = get_wva(ctx)
    subscription = wva.get_subscription(short_name)
    subscription.delete()


@subscriptions.command()
@click.pass_context
def clear(ctx):
    """Remove all registered subscriptions

Example:

\b
    $ wva subscriptions clear
    Deleting engineload... Done
    Deleting fuelrate... Done
    Deleting throttle... Done
    Deleting rpm... Done
    Deleting speedy... Done

To remove a specific subscription, use 'wva subscription remove <name>' instead.
"""
    wva = get_wva(ctx)
    for subscription in wva.get_subscriptions():
        sys.stdout.write("Deleting {}... ".format(subscription.short_name))
        sys.stdout.flush()
        subscription.delete()
        print("Done")


@subscriptions.command()
@click.argument("short_name")
@click.pass_context
def show(ctx, short_name):
    """Show metadata for a specific subscription

Example:

\b
    $ wva subscriptions show speed
    {'buffer': 'queue', 'interval': 5, 'uri': 'vehicle/data/VehicleSpeed'}
"""
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
    """Add a subscription with a given short_name for a given uri

This command can be used to create subscriptions to receive new pieces
of vehicle data on the stream channel on a periodic basis.  By default,
subscriptions are buffered and have a 5 second interval:

\b
    $ wva subscriptions add speed vehicle/data/VehicleSpeed
    $ wva subscriptions show speed
    {'buffer': 'queue', 'interval': 5, 'uri': 'vehicle/data/VehicleSpeed'}

These parameters can be modified by the use of optional arguments:

    $ wva subscriptions add rpm vehicle/data/EngineSpeed --interval 1 --buffer discard
    $ wva subscriptions show rpm
    {'buffer': 'discard', 'interval': 1, 'uri': 'vehicle/data/EngineSpeed'}

To view the data coming in as a result of these subscriptions, one can use
either 'wva subscriptions listen' or 'wva subscriptions graph <name>'.
"""
    wva = get_wva(ctx)
    subscription = wva.get_subscription(short_name)
    subscription.create(uri, buffer, interval)


@subscriptions.command()
@click.pass_context
def listen(ctx):
    """Output the contents of the WVA event stream

This command shows the data being received from the WVA event stream based on
the subscriptions that have been set up and the data on the WVA vehicle bus.

\b
    $ wva subscriptions listen
    {'data': {'VehicleSpeed': {'timestamp': '2015-03-25T00:11:53Z',
                                 'value': 198.272461},
               'sequence': 124,
               'short_name': 'speed',
               'timestamp': '2015-03-25T00:11:53Z',
               'uri': 'vehicle/data/VehicleSpeed'}}
    {'data': {'EngineSpeed': {'timestamp': '2015-03-25T00:11:54Z',
                                'value': 6425.5},
               'sequence': 274,
               'short_name': 'rpm',
               'timestamp': '2015-03-25T00:11:54Z',
               'uri': 'vehicle/data/EngineSpeed'}}
    ...
    ^C
    Aborted!

This command can be useful for debugging subscriptions or getting a quick
glimpse at what data is coming in to a WVA device.
"""
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
    """Present a live graph of the incoming streaming data

This command requires that matplotlib be installed and accessible
to the application in order to work.  The application reads
data from the WVA event stream and plots all data for specified
parameters within some time window.  Subscriptions must be
set up prior to running this command for it to work.

As an example, let's say that I want to show the last 3 minutes (180 seconds)
of speed and rpm data for my device.  In that case, I work set up my
subscriptions and execute the following...

\b
    $ wva subscriptions graph --seconds=180 VehicleSpeed EngineSpeed
"""
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
