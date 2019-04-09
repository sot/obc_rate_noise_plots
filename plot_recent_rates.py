import numpy as np
import tables
from Chandra.Time import DateTime
import Ska.DBI

import matplotlib
if __name__ == '__main__':
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
from Ska.Matplotlib import plot_cxctime

import Ska.engarchive.fetch as fetch

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
    msids = fetch.MSIDset(['aorate1', 'aorate2', 'aorate3', 'aounload'], tstart, tstop)

    # Relabel data to match an earlier implementation done without 'fetch'
    r1_data = msids['aorate1'].vals
    r1_qual = msids['aorate1'].bads
    r2_data = msids['aorate2'].vals
    r2_qual = msids['aorate2'].bads
    r3_data = msids['aorate3'].vals
    r3_qual = msids['aorate3'].bads
    dump_data = msids['aounload'].vals
    dump_qual = msids['aounload'].bads
    time_data = msids['aorate2'].times

    print 'Filtering'
    qual = ~(r1_qual | r2_qual | r3_qual | dump_qual)
    r1_data_q = r1_data[qual]
    r2_data_q = r2_data[qual]
    r3_data_q = r3_data[qual]
    time_data_q = time_data[qual]
    dump_data_q = dump_data[qual]

# Filter to times within Kalman interval with no momentum dumps or SIM moves nearby
if 'times' not in globals():
    db = Ska.DBI.DBI(dbi='sybase', server='sybase', user='aca_read', database='aca')
    print 'Getting kalmans'
    
    kalmans = db.fetchall('select kalman_tstart as tstart, kalman_tstop as tstop from obs_kalman '
                          'where kalman_tstop > {0} and kalman_tstart < {1}'.format(tstart, tstop))
    print 'Getting cmd_states'
    cmd_states = db.fetchall('select tstart, tstop, simpos from cmd_states '
                             'where tstop > {0} and tstart < {1}'.format(tstart, tstop))
    db.conn.close()

    print 'Filtering kalman'
    ok = np.zeros(len(time_data_q), dtype=bool)
    for kalman in kalmans:
        row0, row1 = np.searchsorted(time_data_q, [kalman.tstart+1000, kalman.tstop-1000])
        ok[row0:row1] = True

    print 'Making sim_moving filters'
    sim_moving = cmd_states.simpos[1:] - cmd_states.simpos[:-1] > 3
    for sim_moving_time in cmd_states.tstart[1:][sim_moving]:
        row0, row1 = np.searchsorted(time_data_q, [sim_moving_time-1000, sim_moving_time+1000])
        ok[row0:row1] = False

    print 'Making mom_dump filters'
    mom_dumps = dump_data_q[1:] != dump_data_q[:-1]
    for mom_dump_time in time_data_q[1:][mom_dumps]:
        row0, row1 = np.searchsorted(time_data_q, [mom_dump_time-1000, mom_dump_time+1000])
        ok[row0:row1] = False

    print 'Calculating and final filtering'
    roll_rates = r1_data_q[ok] * 206264.
    pitch_rates = r2_data_q[ok] * 206264.
    yaw_rates = r3_data_q[ok] * 206264.
    times = time_data_q[ok]

time_range = DateTime(tstart).date[:8] + ' to ' + DateTime(tstop).date[:8]
if 1:
    plt.figure(1, figsize=(4,2.75))
    bins = np.linspace(-4, 4, 60)
    for label, rates in (('roll', roll_rates),
                         ('pitch', pitch_rates),
                         ('yaw', yaw_rates)):
        print 'Making', label, 'histograms'
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
    plt.figure(2, figsize=(8,2.75))
    for label, rates in (('roll', roll_rates),
                         ('pitch', pitch_rates),
                         ('yaw', yaw_rates)):
        print 'Making', label, 'time plots'
        plt.clf()
        plot_cxctime(times, rates, '.', markersize=1, mew=0)
        plt.ylim(-4, 4)
        plt.title(label.capitalize() + ' rates {0}'.format(time_range))
        plt.ylabel('Rate (arcsec/sec)')
        plt.grid()
        plt.show()
        plt.savefig(label + '_time_%s.png' % opt.root)
