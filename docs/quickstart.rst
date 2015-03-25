Quickstart
==========

You can install the library direclty from PyPI using pip::

    pip install wva

The installation into a `virtualenv <https://virtualenv.pypa.io/en/latest/>_`
is recommended but not required.

With the appliation installed (and when working in the correct environment
if using virtualenv), you should have access to both the library and to
the CLI application.  To test that you have access to the CLI program,
you can run the following::

    wva --help

To verify that the python library is accessible you can do the following::

    $ python
    >>> import wva
    >>> print wva.__version__
    0.1

Using the CLI
-------------

A detailed tutorial describing how to use the CLI can be found on the
:doc:`cli` page.  Most of the CLI is self-documenting.  To explore the
capabilities of the CLI, you can start by running::

    $ wva --help
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

To receive even more help on any given command, you can specify that
command, followed by ``--help`` to get more details.  For instance::

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

Using the Library
-----------------

The WVA object is the center of any use of the library.  Creating
a WVA object can be done by doing the following::

    from wva import WVA
    wva = WVA('<wva-host-or-ip>', 'user', 'password')

By default, the WVA object will be set-up to use HTTPS.  To change this
to HTTP, you can either change it by doing ``wva.use_https = False`` or
specify ``use_https=False`` when constructing the WVA object.

The :doc:`api` documentation describes all of the library methods in
greater detail, including the methods available on the WVA object.

