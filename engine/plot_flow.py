from __future__ import print_function
import matplotlib
from matplotlib.patches import Rectangle
matplotlib.rc('font', **{'size': 30})
from matplotlib.dates import DateFormatter, DayLocator
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.dates
import csv
import numpy as np

fname = 'lane_data_3002_3001.csv'
true_x = []
true_y = []
start = datetime(2013, 4, 1)
end = datetime(2013, 6, 15)

with open(fname, 'r') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)
    chunk_size = 12 * 24
    print("Chunk hours:", chunk_size * 5 / 60)
    chunk = []
    for row in reader:

        dt = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if start > dt:
            continue
        if dt >= end:
            break
        if not chunk:
            stime = dt
        chunk.append(sum((float(x) for x in row[1:] if float(x) < 200)))
        if len(chunk) == chunk_size:
            true_x.append(stime)
            true_y.append(np.std(chunk))
            chunk = []

true_x = np.array(true_x)
true_y = np.array(true_y)

title = "Flow"

invalids = true_y > 200
true_y[invalids] = np.nan


class UpdatingRect(Rectangle):
    def __call__(self, ax):
        self.set_bounds(*ax.viewLim.bounds)
        ax.figure.canvas.draw_idle()


def ax_update(ax):
    ax.set_autoscale_on(False)  # Otherwise, infinite loop

    dims = ax.axesPatch.get_window_extent().bounds
    xstart, ystart, xdelta, ydelta = ax.viewLim.bounds
    xend = xstart + xdelta
    yend = int(ystart + ydelta)

    startTime = matplotlib.dates.num2date(xstart).replace(tzinfo=None)
    endTime = matplotlib.dates.num2date(xend).replace(tzinfo=None)
    sIdx = np.searchsorted(true_x, startTime)
    eIdx = np.searchsorted(true_x, endTime, side='right') - 1
    plt.title("3002: Traffic Flow from {} to {}".format(true_x[sIdx].strftime(df), true_x[eIdx].strftime(df)), y=1.03)
    ax.figure.canvas.draw_idle()


fig, ax = plt.subplots()

plt.plot(true_x, true_y, 'b-', label='Daily std. dev')

plt.legend(prop={'size': 23})
plt.grid(b=True, which='major', color='black', linestyle='-')
plt.grid(b=True, which='minor', color='black', linestyle='dotted')
plt.axvline(x=matplotlib.dates.date2num(datetime(2013, 5, 1)), ymax=45, color='r', linewidth=2)
xmajor_fmt = DateFormatter('%a %-d %b')
xmajor_locator = DayLocator(interval=2)
ax.xaxis.set_major_formatter(xmajor_fmt)
ax.xaxis.set_major_locator(xmajor_locator)
fig.subplots_adjust(bottom=0.13)
df = "%A %d %B, %Y"
plt.title("Intersection 3002: Daily Traffic Flow from {} to {}".format(true_x[0].strftime(df), true_x[-1].strftime(df)),
          y=1.03)
# plt.title("3002: Traffic Flow from 10 May 2013 to 11 May 2013", y=1.03)
plt.legend()

plt.ylabel("Standard Deviation of Vehicle Flow Per Day")
plt.xlabel("Time")
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(25)
    tick.label.set_rotation(90)
    # tick.label.set_horizontalalignment('right')
# ax.tick_params(direction='in')
ax.callbacks.connect('xlim_changed', ax_update)
plt.show()
