"""
File: Graph.py

Author: Matthew Yu, Array Lead (2020).
Contact: matthewjkyu@gmail.com
Created: 11/17/20
Last Modified: 11/24/20

Description: The Graph class is a customizable widget allowing for
displaying series data over an independent axis, like time. Axes properties,
labels, and number of elements displayed at one time is defined at declaration.
"""
# Library Imports.
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

import numpy as np

# Custom Imports.
from ArraySimulation.Controller.View import View


class Graph(View):
    """
    The Graph class is a customizable widget allowing for displaying series data
    over an independent axis, like time. Axes properties, labels, etc is defined
    at initialization.
    """

    SERIES_COLOR_SET = {
        "current": (0, 255, 0),  # Green
        "voltage": (255, 0, 0),  # Red
        "power": (0, 0, 255),  # Blue
        "irradiance": (255, 0, 255),
        "temperature": (255, 255, 0),
        "MPPTVREF": (255, 255, 255),  # White
        "MPPTPower": (0, 255, 0),  # Green
        "maxDiff": (255, 0, 0),  # Red
        "cyclesThreshold": (0, 255, 0),  # Green
        "trackingEff": (0, 0, 255),  # Blue
        "default": (255, 255, 255),
    }

    def __init__(
        self,
        series,
        graphType="Line",
        title="Uninitialized.",
        xAxisLabel="Uninitialized.",
        yAxisLabel="Uninitialized.",
    ):
        """
        Upon initialization, we perform any data and UI setup required to get
        the Graph into a default state.

        Parameters
        ----------
        series: Dict
            A dictionary of data series displayed in the graph. It is in the
            following format:

            {
                "voltage": {
                    "data": {
                        "x": [ 0, 1, 2, ... ],      <-  At initialization,
                        "y": [.6, .6, .6, ... ],        these are empty.
                    },
                    "multiplier": 1,
                    "label": "Voltage (V)",         <-  This label is displayed
                "current": {                            in the legend if not None.
                    "data": {
                        "x": [ 0, 1, 2, ... ],
                        "y": [6, 6, 6, ... ],
                    },
                    "multiplier": .5,               <-  Multipliers adjust the
                    "label": None,                      data scale on the graph.
                },
                ...
                "temperature": {
                    ...
                },
                "list": ("voltage", "current", ..., "temperature"),
            }

            The reference defines how the graph should be formatted and provides
            the storage for adding new data with the update() method.
        graphType: String
            The type of graph. Either a line graph or scatter plot.
        title: String
            Title of the graph.
        xAxisLabel: String
            Label for the X Axis.
        yAxisLabel: String
            Label for the Y Axis.
        framerate: int
            Inherited parameter for View class. Unused here.

        """
        super(Graph, self).__init__()

        self._series = series

        self._graphType = graphType

        # Independent axis label.
        self._xAxisLabel = xAxisLabel

        # Dependent axis label.
        self._yAxisLabel = yAxisLabel

        # Title of graph.
        self._title = title

        # Reference to the graph for easy modification.
        self._graph = {}

        self.updateUI()

    def addPoint(self, series, datapointX, datapointY):
        """
        Adds a new data point to the graph.

        Parameters
        ----------
        series: String
            ID of the series that should exist in self._series where the data
            point should be inserted.
        datapointX: int, float
            X value of the datapoint. Can be either float or integer.
        datapointY: int, float
            Y value of the datapoint. Can be either float or integer.

        Assumptions
        -----------
        Datapoints are inserted IN ORDER. We aren't doing any sorting for you.
        """
        if series in self._series:
            self._series[series]["data"]["x"].append(datapointX)
            self._series[series]["data"]["y"].append(
                datapointY * self._series[series]["multiplier"]
            )

            self._graph[series].setData(
                x=self._series[series]["data"]["x"],
                y=self._series[series]["data"]["y"],
            )

    def addPoints(self, series, datapointsX, datapointsY):
        """
        Adds a new set of data points to the graph.

        Parameters
        ----------
        series: String
            ID of the series that should exist in self._series where the data
            point should be inserted.
        datapointX: int, float
            X value list of datapoints. Can be either floats or integers.
        datapointY: int, float
            Y value list of datapoints. Can be either floats or integers.

        Assumptions
        -----------
        Datapoints are inserted IN ORDER. We aren't doing any sorting for you.
        """
        if series in self._series:
            self._series[series]["data"]["x"] += datapointsX
            modifier = self._series[series]["multiplier"]
            modifiedDatapointsY = [datapointY * modifier for datapointY in datapointsY]
            self._series[series]["data"]["y"] += modifiedDatapointsY

            print(modifiedDatapointsY)
            self._graph[series].setData(
                x=self._series[series]["data"]["x"],
                y=self._series[series]["data"]["y"],
            )

    def setPoint(self, seriesID, idx, datapointX, datapointY):
        """
        Sets a new data point to the graph. Specifically for graphs like MPPT
        V_REF over Source IV/PV Curve, where we're looking at a single point
        move across a curve.

        Parameters
        ----------
        seriesID: String
            ID of the series that should exist in self._series where the data
            point should be inserted.
        idx: int
            Index of the dataset that this point should replace.
        datapointX: int, float
            X value of the datapoint. Can be either float or integer.
        datapointY: int, float
            Y value of the datapoint. Can be either float or integer.

        Assumptions
        -----------
        Datapoints are inserted IN ORDER. We aren't doing any sorting for you.
        """
        if series in self._series:
            self._series[series]["data"]["x"][idx] = datapointX
            self._series[series]["data"]["y"][idx] = datapointY

            self._graph[series].setData(
                x=self._series[series]["data"]["x"],
                y=self._series[series]["data"]["y"],
            )

    def clearPoints(self):
        """
        Erases all data points from all data series.
        """
        for series in self._series["list"]:
            self._series[series]["data"]["x"].clear()
            self._series[series]["data"]["y"].clear()

            self._graph[series].setData(
                x=self._series[series]["data"]["x"],
                y=self._series[series]["data"]["y"],
            )

    def updateUI(self):
        """
        Sets up the UI properties of the Graph. Updates the graph whenever a
        point is added to it. This widget is composed of two layers, a wrapper
        that contains the widget descriptor label ("Flight Altitude Graph") and
        an internal layout that holds the graph itself.

        This method is dependent on the backend used.
        """
        if self._layout is None:
            # Build the widget for the first time.
            # Plot Widget.
            widget = pg.GraphicsLayoutWidget()

            plt = widget.addPlot(title=self._title)
            plt.setLabel("bottom", self._xAxisLabel)
            plt.setLabel("left", self._yAxisLabel)
            plt.addLegend()

            if self._graphType == "Line":
                for series in self._series["list"]:
                    # Apply multiplier to value.
                    for n, y in enumerate(self._series[series]["data"]["y"]):
                        self._series[series]["data"]["y"][n] *= self._series[
                            series
                        ]["multiplier"]

                    # Get pen color.
                    penColor = self.SERIES_COLOR_SET["default"]
                    if series in self.SERIES_COLOR_SET:
                        penColor = self.SERIES_COLOR_SET[series]

                    self._graph[series] = plt.plot(
                        x=self._series[series]["data"]["x"],
                        y=self._series[series]["data"]["y"],
                        pen=pg.mkPen(penColor, width=1),
                        name=self._series[series]["label"],
                    )
            elif self._graphType == "Scatter":
                for series in self._series["list"]:
                    # Apply multiplier to value.
                    for n, y in enumerate(self._series[series]["data"]["y"]):
                        self._series[series]["data"]["y"][n] *= self._series[
                            series
                        ]["multiplier"]

                    # Get pen color.
                    penColor = self.SERIES_COLOR_SET["default"]
                    if series in self.SERIES_COLOR_SET:
                        penColor = self.SERIES_COLOR_SET[series]

                    self._graph[series] = pg.ScatterPlotItem(
                        x=self._series[series]["data"]["x"],
                        y=self._series[series]["data"]["y"],
                        pen=pg.mkPen(penColor, width=1),
                        name=self._series[series]["label"],
                    )
                    plt.addItem(self._graph[series])
            else:
                raise Exception("Invalid graph type:", self._graphType)

            # Internal layout that contains the graph widget.
            graphLayout = QWidget()
            graphLayout.layout = QVBoxLayout(graphLayout)
            graphLayout.setLayout(graphLayout.layout)

            # Add the graph to the internal layout.
            graphLayout.layout.addWidget(widget)

            self._layout = graphLayout