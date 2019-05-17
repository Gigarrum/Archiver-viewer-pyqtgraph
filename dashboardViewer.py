#!/usr/bin/env python

#Adapted from https://gist.github.com/cpascual/cdcead6c166e63de2981bc23f5840a98

#------------------------------------------------------------------------------

#Developer: Paulo Baraldi Mausbach
#LNLS - Brazilian Synchrotron Light Source Laboratory

"""
This module provides date-time aware axis
"""

__all__ = ["DateAxisItem"]

import numpy as np
from pyqtgraph import AxisItem
from datetime import datetime, timedelta
from time import mktime

class DateAxisItem(AxisItem):
    """
    A tool that provides a date-time aware axis. It is implemented as an
    AxisItem that interpretes positions as unix timestamps (i.e. seconds
    since 1970).
    The labels and the tick positions are dynamically adjusted depending
    on the range.
    It provides a  :meth:`attachToPlotItem` method to add it to a given
    PlotItem
    """

    # Max width in pixels reserved for each label in axis
    _pxLabelWidth = 80

    def __init__(self, *args, **kwargs):
        AxisItem.__init__(self, *args, **kwargs)
        self._oldAxis = None

    def tickValues(self, minVal, maxVal, size):
        """
        Reimplemented from PlotItem to adjust to the range and to force
        the ticks at "round" positions in the context of time units instead of
        rounding in a decimal base
        """

        maxMajSteps = int(size/self._pxLabelWidth)

        dt1 = datetime.fromtimestamp(minVal)
        dt2 = datetime.fromtimestamp(maxVal)

        dx = maxVal - minVal
        majticks = []

        if dx > 63072001:  # 3600s*24*(365+366) = 2 years (count leap year)
            d = timedelta(days=366)
            for y in range(dt1.year + 1, dt2.year):
                dt = datetime(year=y, month=1, day=1)
                majticks.append(mktime(dt.timetuple()))

        elif dx > 5270400:  # 3600s*24*61 = 61 days
            d = timedelta(days=31)
            dt = dt1.replace(day=1, hour=0, minute=0,
                             second=0, microsecond=0) + d
            while dt < dt2:
                # make sure that we are on day 1 (even if always sum 31 days)
                dt = dt.replace(day=1)
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 172800:  # 3600s24*2 = 2 days
            d = timedelta(days=1)
            dt = dt1.replace(hour=0, minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 7200:  # 3600s*2 = 2hours
            d = timedelta(hours=1)
            dt = dt1.replace(minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 1200:  # 60s*20 = 20 minutes
            d = timedelta(minutes=10)
            dt = dt1.replace(minute=(dt1.minute // 10) * 10,
                             second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 120:  # 60s*2 = 2 minutes
            d = timedelta(minutes=1)
            dt = dt1.replace(second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 20:  # 20s
            d = timedelta(seconds=10)
            dt = dt1.replace(second=(dt1.second // 10) * 10, microsecond=0) + d
            while dt < dt2:
                majticks.append(mktime(dt.timetuple()))
                dt += d

        elif dx > 2:  # 2s
            d = timedelta(seconds=1)
            majticks = range(int(minVal), int(maxVal))

        else:  # <2s , use standard implementation from parent
            return AxisItem.tickValues(self, minVal, maxVal, size)

        L = len(majticks)
        if L > maxMajSteps:
            majticks = majticks[::int(np.ceil(float(L) / maxMajSteps))]

        return [(d.total_seconds(), majticks)]

    def tickStrings(self, values, scale, spacing):
        """Reimplemented from PlotItem to adjust to the range"""
        ret = []
        if not values:
            return []

        if spacing >= 31622400:  # 366 days
            fmt = "%Y"

        elif spacing >= 2678400:  # 31 days
            fmt = "%Y %b"

        elif spacing >= 86400:  # = 1 day
            fmt = "%b/%d"

        elif spacing >= 3600:  # 1 h
            fmt = "%b/%d-%Hh"

        elif spacing >= 60:  # 1 m
            fmt = "%H:%M"

        elif spacing >= 1:  # 1s
            fmt = "%H:%M:%S"

        else:
            # less than 2s (show microseconds)
            # fmt = '%S.%f"'
            fmt = '[+%fms]'  # explicitly relative to last second

        for x in values:
            try:
                t = datetime.fromtimestamp(x)
                ret.append(t.strftime(fmt))
            except ValueError:  # Windows can't handle dates before 1970
                ret.append('')

        return ret

    def attachToPlotItem(self, plotItem):
        """Add this axis to the given PlotItem
        :param plotItem: (PlotItem)
        """
        self.setParentItem(plotItem)
        viewBox = plotItem.getViewBox()
        self.linkToView(viewBox)
        self._oldAxis = plotItem.axes[self.orientation]['item']
        self._oldAxis.hide()
        plotItem.axes[self.orientation]['item'] = self
        pos = plotItem.axes[self.orientation]['pos']
        plotItem.layout.addItem(self, *pos)
        self.setZValue(-1000)

    def detachFromPlotItem(self):
        """Remove this axis from its attached PlotItem
        (not yet implemented)
        """
        raise NotImplementedError()  # TODO

#[DEBUG]

if __name__ == '__main__':

    import time
    import sys
    import pyqtgraph as pg
    from PyQt5 import QtGui
    import epics
    from ArchiverRequester import ArchiverRequester

    class UpdateSignalizer(pg.QtCore.QObject):

        updateSignal = pg.QtCore.Signal(object)

    def updateData(**kwargs):
        global valuesArray,timestamps,updateSignalizer

        print(kwargs) #[DEBUG]

         # shift data in the array one sample left
        valuesArray[:-1] = valuesArray[1:]
        timestamps[:-1] = timestamps[1:]

        #insert new value
        valuesArray[-1] = kwargs['value']
        timestamps[-1] = kwargs['timestamp']

        updateSignalizer.updateSignal.emit((timestamps,valuesArray))

    def updatePlot(plotData):
        global valueArray,curve,timestamps
        w.plot(x=plotData[0], y=plotData[1])

    app = QtGui.QApplication([])

    w = pg.PlotWidget()

    # Add the Date-time axis
    axis = DateAxisItem(orientation='bottom')
    axis.attachToPlotItem(w.getPlotItem())

    #Request historical data to EPICS Archivers
    requester = ArchiverRequester('http','10.0.38.59','11998')
    r = requester.requestHistoricalData('LNLS:ANEL:corrente',datetime(2019,5,17))

    #Transform data received
    dataArray = np.array(r[0]['data'])
    valuesArray = np.array([])

    for data in dataArray:
        valuesArray = np.append(valuesArray,data['val'])

    # Create time axis
    now = time.time()
    timestamps = np.linspace(now - 3600, now,len(valuesArray))

    # Plot historical data
    curve = w.plot(x=timestamps, y=valuesArray)
    w.show()

    #Start monitoring PV value
    epics.camonitor('LNLS:ANEL:corrente',callback = updateData)

    updateSignalizer = UpdateSignalizer()
    updateSignalizer.updateSignal.connect(updatePlot)

    sys.exit(app.exec_())
