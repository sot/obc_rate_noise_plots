#!/usr/bin/env python
import numpy as np
import matplotlib
if __name__ == '__main__':
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from Chandra.Time import DateTime
from Ska.Matplotlib import plot_cxctime
import Ska.engarchive.fetch as fetch
from kadi import events


def get_options():
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults()
    parser.add_option("--start",
                      help="Start time")
    parser.add_option("--stop",
                      help="Stop time")
    parser.add_option("--duration",
                      type='float',
                      default=1.6e7,
                      help="Plot duration (seconds)")
    parser.add_option("--root",
                      default='recent',
                      help="Root file name")
    (opt, args) = parser.parse_args()
    return (opt, args)

opt, args = get_options()


tstop = DateTime(opt.stop).secs  # if opt.stop is None then this returns current time
if opt.start is None:
    tstart = tstop - opt.duration
else:
    tstart = DateTime(opt.start).secs

if 'msids' not in globals():
    dwells = events.dwells.filter(tstart, tstop)
    tstop = np.min([dwells[len(dwells) - 1].tstop, tstop])
    msids = fetch.MSIDset(['aorate1', 'aorate2', 'aorate3'],
                          tstart, tstop, filter_bad=True)

# Filter to times within Kalman interval with no momentum dumps or SIM moves nearby
if 'times' not in globals():
    print('Calculating and final filtering')
    events.dwells.interval_pad = (-1000, -1000)
    events.tsc_moves.interval_pad = (1000, 1000)
    events.dumps.interval_pad = (1000, 1000)
    for msid in msids:
        msids[msid].select_intervals(events.dwells)
        msids[msid].remove_intervals(events.tsc_moves)
        msids[msid].remove_intervals(events.dumps)
    roll_rates = msids['aorate1'].vals * 206264
    pitch_rates = msids['aorate2'].vals * 206264
    yaw_rates = msids['aorate3'].vals * 206264
    times = msids['aorate1'].times

time_range = DateTime(tstart).date[:8] + ' to ' + DateTime(tstop).date[:8]
if 1:
    plt.figure(1, figsize=(4, 2.75))
    bins = np.linspace(-4, 4, 60)
    for label, rates in (('roll', roll_rates),
                         ('pitch', pitch_rates),
                         ('yaw', yaw_rates)):
        print('Making', label, 'histograms')
        plt.clf()
        plt.hist(rates, bins=bins, log=True)
        plt.title(label.capitalize() + ' rates {0}'.format(time_range))
        plt.xlabel('Rate (arcsec/sec)')
        plt.ylabel('Frequency')
        plt.subplots_adjust(left=0.16, bottom=0.14)
        plt.grid()
        plt.show()
        plt.savefig(label + '_hist_%s.png' % opt.root)

if 1:
    plt.figure(2, figsize=(8, 2.75))
    for label, rates in (('roll', roll_rates),
                         ('pitch', pitch_rates),
                         ('yaw', yaw_rates)):
        print('Making', label, 'time plots')
        plt.clf()
        plot_cxctime(times, rates, '.', markersize=1, mew=0)
        plt.ylim(-4, 4)
        plt.title(label.capitalize() + ' rates {0}'.format(time_range))
        plt.ylabel('Rate (arcsec/sec)')
        plt.grid()
        plt.show()
        plt.savefig(label + '_time_%s.png' % opt.root)
