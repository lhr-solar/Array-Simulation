"""
PVCellNonideal.py

Author: Matthew Yu, Array Lead (2020).
Contact: matthewjkyu@gmail.com
Created: 10/14/20
Last Modified: 10/21/20

Description: Derived class of PVCell that implements an nonideal model tuned to
the Sunpower Maxeon III Bin Le1 solar cells.
"""
# Library Imports.
from math import exp, pow, e
from numpy import log as ln
import numpy as np


# Custom Imports.
from ArraySimulation.PVSource.PVCell.PVCell import PVCell
from ArraySimulation.PVSource.PVCell.Lookup import Lookup


class PVCellNonideal(PVCell):
    """
    Derived class of PVCell that implements an nonideal model tuned to the Sunpower
    Maxeon III Bin Le1 solar cells.
    """

    def __init__(self):
        super(PVCellNonideal, self).__init__()

        # Lookup object for pulling a model from a file.
        self._lookup = Lookup(fileName="NonidealCellLookup.csv")
        self._lookup.readFile()

    def getCurrent(self, voltage=0, irradiance=0.001, temperature=0):
        # Ideal single diode model.
        cellTemperature = (
            temperature + 273.15
        )  # Convert cell temperature into kelvin.

        # Suppres divide by 0s from voltage and irradiance.
        if voltage == 0.0:
            voltage = 0.001
        if irradiance == 0.0:
            irradiance = 0.001

        # Short circuit current.
        SCCurrent = (
            irradiance
            / self.refIrrad
            * self.refSCCurrent
            * (1 + 6e-4 * (cellTemperature - self.refTemp))
        )

        # Open circuit voltage.
        OCVoltage = (
            self.refOCVoltage
            - 2.2e-3 * (cellTemperature - self.refTemp)
            + self.k * cellTemperature / self.q * ln(irradiance / self.refIrrad)
        )

        # Photovoltatic current.
        PVCurrent = SCCurrent

        # Reverse saturation current, or dark saturation current.
        revSatCurrent = exp(
            ln(SCCurrent) - self.q * OCVoltage / (self.k * cellTemperature)
        )

        # Iteratively solve for the implicit parameter.
        currentPrediction = 0
        left = currentPrediction

        # Diode current.
        diodeCurrent = (
            revSatCurrent
            * (
                exp(
                    self.q
                    * (voltage + currentPrediction + self.rSeries)
                    / (self.k * cellTemperature)
                )
                - 1
            )
            - (voltage + currentPrediction * self.rSeries) / self.rShunt
        )
        right = PVCurrent - diodeCurrent

        difference = (left - right) ** 2
        decreasing = True

        while decreasing:
            currentPrediction += 0.001
            left = currentPrediction

            diodeCurrent = (
                revSatCurrent
                * (
                    exp(
                        self.q
                        * (voltage + currentPrediction + self.rSeries)
                        / (self.k * cellTemperature)
                    )
                    - 1
                )
                - (voltage + currentPrediction * self.rSeries) / self.rShunt
            )
            right = PVCurrent - diodeCurrent

            # If my difference change has flipped signs, I'm done.
            if (difference - (left - right) ** 2) <= 0.0:
                decreasing = False
            difference = (left - right) ** 2

        # TODO: for some reason, I'm bloody off by a factor of 10 at all times.
        return currentPrediction * 10

    def getCurrentLookup(self, voltage=0, irradiance=0.001, temperature=0):
        """
        Guaranteed to be at least a dozen times faster than getCurrent. However,
        we need to be able to generate the lookup table from the original, which
        means if you decide to use this method, at some point you'll need to
        spend a cozy 5-10 minutes building the massive lookup table.
        """
        return self._lookup.lookup([voltage, irradiance, temperature])[0]

    def buildCurrentLookup(
        self,
        fileName="NonidealCellLookup2.csv",
        voltageRes=0.01,
        irradianceRes=50,
        temperatureRes=0.5,
    ):
        """
        Using our model and a specified resolution, we'll build up the lookup
        table. Note that the defaults are recommended (<3 min) and shrinking the
        resolutions further nonlinearly increases the process time.

        Also, make sure that the resolutions are in .1, .2, or .5 increments.

        Parameters
        ----------
        voltageRes: float
            Voltage resolution step.
        irradianceRes: float
            Irradiance resolution step.
        temperatureRes: float
            Temperature resolution step.
        """
        lookup = Lookup(fileName=fileName)
        for voltage in np.arange(0, 0.81, voltageRes):
            for irradiance in np.arange(0, 1000.1, irradianceRes):
                for temperature in np.arange(0, 80.1, temperatureRes):
                    current = self.getCurrent(voltage, irradiance, temperature)
                    lookup.addLine(
                        [
                            round(voltage, 3),
                            round(irradiance, 3),
                            round(temperature, 3),
                            round(current, 3),
                        ]
                    )

        lookup.writeFile()
        lookup.readFile()
        self._lookup = lookup

    def getCellIV(self, resolution=0.001, irradiance=0.001, temperature=0):
        """
        Calculates the entire cell model current voltage plot given various
        environmental parameters.

        Parameters
        ----------
        resolution: float
            Voltage stride across the cell. Occurs within the bounds of [0,
            MAX_VOLTAGE], inclusive.
        irradiance: float
            Irradiance on the cell. In W/M^2.
        temperature: float
            Cell surface temperature. In degrees Celsius.

        Returns
        -------
        list: [(voltage:float, current:float), ...]
            A list of paired voltage|current tuples across the cell IV curve.

        Assumptions
        -----------
        The IV curve of the cell has a short circuit current of 0A by MAX_VOLTAGE.
        """
        model = []
        if resolution <= 0:
            resolution = self.MIN_RESOLUTION

        for voltage in np.arange(0.0, self.MAX_VOLTAGE, resolution):
            current = self.getCurrentLookup(voltage, irradiance, temperature)
            if current >= 0.0:
                model.append((voltage, current))

        return model

    def getModelType(self):
        return "Nonideal"
