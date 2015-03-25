Command Line Interface
======================

The WVA command-line interface seeks to be largely self-documenting.
To see the available top-level commands, run::

    $ wva --help
    wva --help
    Usage: wva [OPTIONS] COMMAND [ARGS]...

      Command-line interface for interacting with a WVA device

    Options:
      --https / --no-https  Use HTTPS instead of HTTP
      --hostname TEXT       Force use of the specified hostname
      --username TEXT       Force use of the specified username
      --password TEXT       Force use of the specified password
      --config-dir TEXT     Directory containing wva configuration files
      --help                Show this message and exit.

    Commands:
      cliconfig      View and clear CLI config
      delete         DELETE the specified URI Example: $ wva get...
      get            Perform an HTTP GET of the provided URI The...
      post           POST file data to a specific URI Note that...
      put            PUT file data to a specific URI Example: $...
      subscriptions  View and Edit subscriptions
      vehicle        Vehicle Data Commands

To receive more information about a specific command, you can add
``--help`` to the end to see its documentation.  For instance::

    $ wva subscriptions --help
    Usage: wva subscriptions [OPTIONS] COMMAND [ARGS]...

      View and Edit subscriptions

    Options:
      --help  Show this message and exit.

    Commands:
      add     Add a subscription with a given short_name...
      clear   Remove all registered subscriptions Example:...
      delete  Delete a specific subscription by short name
      graph   Present a live graph of the incoming...
      list    List short name of all current subscriptions
      listen  Output the contents of the WVA event stream...
      show    Show metadata for a specific subscription...

Managing Subscriptions
----------------------

Most users of the WVA will at some point want to set up subscriptions
to receive information about what vehicle is on the J1939/J1708 bus
attached to the device.

There are two steps required in order to get this information:

1. Create subscriptions for the parameters of interest
2. Receive these events via the event channel

The WVA library and CLI provide methods that make these tasks simple.

To start out, we may want to see what subscriptions are currently already
configured (perhaps by the Android app or previous work)::

    $ wva subscriptions list
    rpm
    speed

To see more information about a subscription, we can do::

    $ wva subscriptions show speed
    {'buffer': 'queue', 'interval': 5, 'uri': 'vehicle/data/VehicleSpeed'}

Let's say we want a clean slate to work from.  In that case, we can remove
all subscriptions by doing::

    $ wva subscriptions clear
    Deleting rpm... Done
    Deleting speed... Done

To view available data items on the vehcle bus, we can use the ``vehicle``
command and use grep to filter out parameters that are unavailable::

    $ wva vehicle list --value | grep -v Unavailable
    AccelPedalLowIdle = 3
    AccelPedalPosition = 38.799999
    BatteryPotential = 14.25
    CruiseControlSetSpeed = 255.0
    CruiseControlStatus = 7
    EngineCoolantTemp = -5.0
    EngineManifoldPressure = 64.0
    EngineOilPressure = 128.0
    EnginePercentLoadAtCurrentSpeed = 16.0
    EngineSpeed = 1044.125
    FuelEconomy = 6.216399
    FuelLevel = 18.0
    FuelRate = 34.049999
    PTOStatus = 31
    ParkingBrake = 0
    Throttle = 102.0
    TotalDistance = 150.0
    TotalEngineHours = 37.5
    TripDistance = 75.0
    VehicleSpeed = 25.09605

Let's say that we want to get TotalDistance and TripDistance every 10 seconds,
EngineSpeed and Throttle every 5 seconds, and VehicleSpeed ever second.  To set
that up, we would do the following from the command-line.  We want to buffer
all of those items except for speed and throttle::

    $ wva subscriptions add distance vehicle/data/TotalDistance --interval=10
    $ wva subscriptions add trip_distance vehicle/data/TripDistance --interval=10
    $ wva subscriptions add rpm vehicle/data/EngineSpeed --interval=5
    $ wva subscriptions add throttle vehicle/data/Throttle --interval=5 --buffer=discard
    $ wva subscriptions add speed vehicle/data/VehicleSpeed --interval=1 --buffer=discard

Now, to view the data we can do the following::

    $ wva subscriptions listen
    {'data': {'EngineSpeed': {'timestamp': '2015-03-25T04:22:24Z',
                                'value': 7148.25},
               'sequence': 17,
               'short_name': 'rpm',
               'timestamp': '2015-03-25T04:22:24Z',
               'uri': 'vehicle/data/EngineSpeed'}}
    {'data': {'TotalDistance': {'timestamp': '2015-03-25T04:22:17Z',
                                  'value': 850599.125},
               'sequence': 10,
               'short_name': 'distance',
               'timestamp': '2015-03-25T04:22:24Z',
               'uri': 'vehicle/data/TotalDistance'}}
    {'data': {'VehicleSpeed': {'timestamp': '2015-03-25T04:22:25Z',
                                 'value': 220.860855},
               'sequence': 67,
               'short_name': 'speed',
               'timestamp': '2015-03-25T04:22:25Z',
               'uri': 'vehicle/data/VehicleSpeed'}}
    {'data': {'VehicleSpeed': {'timestamp': '2015-03-25T04:22:26Z',
                                 'value': 218.349304},
               'sequence': 68,
               'short_name': 'speed',
               'timestamp': '2015-03-25T04:22:26Z',
               'uri': 'vehicle/data/VehicleSpeed'}}
    {'data': {'Throttle': {'timestamp': '2015-03-25T04:22:26Z',
                             'value': 102.0},
               'sequence': 15,
               'short_name': 'throttle',
               'timestamp': '2015-03-25T04:22:26Z',
               'uri': 'vehicle/data/Throttle'}}

This is just a short snippet.  The listen command will run indefinitely.  You
can kill the command with Ctrl-C at any time to stop it.

WVA Configuration Management
----------------------------

The WVA CLI will offer to store information about the WVA IP address/host, username,
and password as these can be annoying to type in each time the 'wva' command is
executed.

By default, settings that are saved are written to ~/.wva/config.json.

You can view the current config by doing::

    $ wva cliconfig show
    {'hostname': '10.35.1.165',
     'password': 'admin',
     'username': 'admin',
     'version': 1}

To clear the stored configuration, you can do::

    $ wva cliconfig clear

See the CLI help for options on overriding the username, password, config directory
and other settings.


Low-Level Web Services Interface
--------------------------------

The library and CLI do not have custom commands for accessing all
of the WVA functionality.  The CLI does, however, provide a set
of methods that allow users to explore the web services API
generically.  The commands that may be used for exploring the
web services API match the basic HTTP verbs:

 - get
 - put
 - post
 - delete

As an example, see how these methods can be used to navigate through
the WVA web services to get information about `Diagnostic Trouble Codes
<http://ftp1.digi.com/support/documentation/html/90001930/90001930_D/Files/webservices.html#dtc>`_
as there is no first-class support for querying these in the rest of the
CLI.

First, we can explore to find where functionality is in the web services
API::

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

Here we see that there is a URI that seems like it may be related, ``/vehicle/dtc``.  Let's
get that and see what we can find::

    $ wva get /vehicle/dtc
    {'dtc': ['vehicle/dtc/can0_active',
          'vehicle/dtc/can0_inactive',
          'vehicle/dtc/can1_active',
          'vehicle/dtc/can1_inactive']}
    $ wva get /vehicle/dtc/can0_inactive
    {'can0_inactive': []}
    $ wva get /vehicle/dtc/can0_active
    {'can0_active': []}

It appears that there are no active DTCs on my bus right now.  If there were
active diagnostic codes, I would get an ecu reference which I could then ``get`` which
would lead me to a DTC value.

Use of the ``PUT``, ``POST``, and ``DELETE`` commands are similarly easy.
Currently, the ``PUT`` and ``POST`` commands require a path to a file
to be specified for the request body.

Bash Completion
---------------

Bash completion for the wva command-line utility may be enabled by
adding the following to your ~/.bashrc or similar::

    eval "$(_WVA_COMPLETE=source wva)"

This functionality uses the bash completion functionality from the
Python Click library.  The `Click Documentation <http://click.pocoo.org/3/bashcomplete/>`_
has additional details if you are running into performance issues or other problems.
