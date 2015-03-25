# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
import collections
import datetime
import threading

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import arrow


class WVAStreamGrapher(object):
    def __init__(self, wva, items, seconds=300, ylim=1000):
        self.items = items
        self._wva = wva
        self._seconds = seconds
        self._ylim = ylim

        # History is a dictionary of deques where each deque contains a set of
        # ordered samples in descending order (oldest data at the end).  This data is pruned
        # by the graph drawing function so that it only contains information within the
        # moving window we care about.
        self._lock = threading.RLock()
        self._history = {}
        for item in self.items:
            self._history[item] = collections.deque(maxlen=self._seconds * 2)
        self._wva.get_event_stream().add_event_listener(self._event_received)

    def _event_received(self, event):
        with self._lock:
            data = event["data"]
            for item in self.items:
                item_data = data.get(item)
                if item_data:
                    dat = (arrow.get(item_data["timestamp"]).datetime, item_data["value"])
                    self._history[item].append(dat)

    def run(self):
        fig, ax = plt.subplots()
        plt.suptitle("WVA Vehicle Data (Live Graph)")
        x = np.arange(-200, self._seconds, 0.01)
        plot_lines = {}
        plt.xlabel("Seconds from Current Time")
        plt.ylabel("Value")

        ax.set_xlim(left=-10, right=self._seconds)
        ax.set_ylim(top=self._ylim)
        for item in self.items:
            lines_created = ax.plot(x, label=item)
            print lines_created
            plot_lines[item] = lines_created[0]  # only 1 line will ever be created
        plt.legend()

        def animate(_i):
            with self._lock:
                now = arrow.utcnow().datetime
                for item, plot_line in plot_lines.items():
                    history = self._history[item]
                    x = []
                    y = []
                    for dt, value in history:
                        x.append((now - dt).total_seconds())
                        y.append(value)
                    plot_line.set_data(x, y)
                return plot_lines.values()

        # blit is more performant but causes issues with resizing, etc.
        ani = animation.FuncAnimation(fig, animate, interval=250, blit=False)
        plt.show()
