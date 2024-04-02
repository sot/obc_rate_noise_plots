#!/usr/bin/env python
import os
import numpy as np
import matplotlib
if __name__ == '__main__':
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from Chandra.Time import DateTime
from Ska.Matplotlib import plot_cxctime
import Ska.engarchive.fetch as fetch
from kadi import events
from pathlib import Path
import shutil


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
    parser.add_option("--outdir",
                      default=".")
    parser.add_option("--root",
                      default='recent',
                      help="Root file name")
    (opt, args) = parser.parse_args()
    return (opt, args)


def main():
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
            plt.hist(rates, bins=bins, log=True, color='blue')
            plt.title(label.capitalize() + ' rates {0}'.format(time_range))
            plt.xlabel('Rate (arcsec/sec)')
            plt.ylabel('Frequency')
            plt.tight_layout()
            #plt.subplots_adjust(left=0.16, bottom=0.14)
            plt.grid(linestyle='--')
            plt.show()
            plt.savefig(os.path.join(opt.outdir, label + '_hist_%s.png' % opt.root))

    if 1:
        plt.figure(2, figsize=(8, 2.75))
        for label, rates in (('roll', roll_rates),
                            ('pitch', pitch_rates),
                            ('yaw', yaw_rates)):
            print('Making', label, 'time plots')
            plt.clf()
            plot_cxctime(times, rates, '.', markersize=2, mew=0, color='blue', alpha=.20)
            plt.ylim(-4, 4)
            plt.yticks(np.arange(-4, 5))
            plt.title(label.capitalize() + ' rates {0}'.format(time_range))
            plt.ylabel('Rate (arcsec/sec)')
            ax = plt.gca()
            ax.set_axisbelow(False)
            plt.grid(linestyle='--')
            plt.show()
            plt.savefig(os.path.join(opt.outdir, label + '_time_%s.png' % opt.root))

    index = Path(__file__).parent / "files" / "index.html"
    shutil.copy(index, opt.outdir)


if __name__ == '__main__':
    main()