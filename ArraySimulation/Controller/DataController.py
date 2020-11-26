"""
DataController.py

Author: Matthew Yu, Array Lead (2020).
Contact: matthewjkyu@gmail.com
Created: 11/19/20
Last Modified: 11/24/20

Description: The DataController class manages the data passed throughout the
program. It exposes objects that represent the state of the application (what
models are running, what data is being captured, commands being executed, etc)
and an API for running the models in the data pipeline.


For now, we only have two types of simulations that we want to simulate.
1. Source Simulation.

    In the source simulation, we want to get the I-V and P-V curves of a
    given irradiance, temperature, and model. (Whether to use lookup to
    speed up the process is optional)

    As such, the user should be able to do the basic calls:

    - Set the PVEnvironment to a specific irradiance and temperature.
    - Set the PVSource to a specific model.

    Using the PVEnvironment and PVSource, extract the IV curve.
    This IV curve is stored in the datastore to be retrieved by the
    UIController.

    Since each set of curves should be a separate series (and therefore
    distinguishable by color), the UIController has the responsibility
    to make repeated calls to the DataController to build the SourceModel
    of the appropriate resolution (Lower, Upper, Step values of the
    irradiance and temperature). This involves resetting the DataController
    per pass.

    TODO: Eventually, we want to enable multi-module support for this.
    This means that we should be able to load a file into this method
    to generate the appropriate irradiance and temperature profile
    across a set of modules.

2. MPPT Simulation.

    In the MPPT simulation, we want to get the I-V and P-V curves of both
    the source and MPPT, and then see how the MPPT varies its reference
    voltage over time and affects the source output. We should also be able
    to see the efficiency calculations over time.

    As such, the user should be able to do the basic calls:

    - Set the PVEnvironment to a specific irradiance and temperature.
    - Set the PVSource to a specific model.
    - Set the MPPT to use a specific algorithm and stride algorithm.

    Using the PVEnvironment and PVSource, provide the input for the
    the MPPT to generate a reverence voltage. Calculate the appropriate
    statistics.

    In the next cycle, use the generated VREF to adjust the source
    output and feed back into the MPPT and so on.

    Since all of the data required for the UI is generated cumulatively
    across cycles, we can just cycle through the simulation until the
    end cycle.

    TODO: Eventually, we want to enable multi-module support for this.
    This means that we should be able to load a file into this method
    to generate the appropriate irradiance and temperature profile
    across a set of modules.
"""
# Library Imports.

# Custom Imports.
from ArraySimulation.DCDCConverter.DCDCConverter import DCDCConverter
from ArraySimulation.MPPT.MPPT import MPPT
from ArraySimulation.PVEnvironment.PVEnvironment import PVEnvironment
from ArraySimulation.PVSource.PVSource import PVSource


class DataController:
    """
    The DataController class manages the data passed throughout the
    program. It exposes objects that represent the state of the application
    (what models are running, what data is being captured, commands being
    executed, etc) and an API for running the models in the data pipeline.
    """

    def __init__(self):
        """
        Generates objects for the pipeline and initializes a data store that
        records data and prepares it for feeding into the UIController.

        The datastore is in the following format:
        {
            "cycle": [],        # List of integers
            "sourceDef": [],    # List of source environment definitions
            "sourceOutput: [],  # List of dicts in the following format:
                                    {
                                        "current": float,
                                        "IV": list of voltage/current tuples,
                                        "edge": tuple (V_OC, I_SC, (V_MPP, I_MPP))
                                    }
            "mpptOutput": [],   # List of reference voltages
            "dcdcOutput": [],   # List of output Pulse Widths
        }

        Based on what is requested, not all of these parameters will have to be
        filled in.
        """
        # Objects in the pipeline.
        self._PVEnv = PVEnvironment()
        self._PVSource = PVSource()
        self._MPPT = MPPT()
        self._DCDCConverter = DCDCConverter()

        # Data storage.
        self.datastore = {
            "cycle": [],
            "sourceDef": [],
            "sourceOutput": [],
            "mpptOutput": [],
            "dcdcOutput": [],
        }

        # The reference voltage applied at the start of every cycle.
        self._vREF = 0.0

    # def setSimTime(self, targetCycle):
    #     """
    #     Time travel to the specified cycle.

    #     Parameters
    #     ----------
    #     targetCycle: int
    #         The cycle the simulation should jump to.
    #     """
    #     self._environment.setCycle(targetCycle)

    # # Source management.
    # def setupSimSource(self, modelType, useLookup):
    #     """
    #     Sets up the PVSource object for the simulation.

    #     Parameters
    #     ----------
    #     modelType: String
    #         Specifies the PVCell model used for modeling all photovoltaics.
    #     useLookup: Bool
    #         Enables the use of lookup tables, if they exist for the model. If it
    #         doesn't, we default to the getCurrent function that doesn't use
    #         lookups.
    #     """

    # # MPPT management.
    # def setupSimMPPT(self, numCells, modelType, strideType):
    #     """
    #     Sets up the MPPT object for the simulation.

    #     Parameters
    #     ----------
    #     numCells: int
    #         Number of cells expected by the MPPT model.
    #     modelType: String
    #         Specifier for the type of model to be used in the MPPT.
    #     strideType: String
    #         Specifier for the type of stride model to be used in the MPPT.
    #     """
    #     self._MPPT.setupModel(numCells, modelType, strideType)

    # # DC-DC Converter management.
    # def setupSimDCDCConverter(self, arrayVoltage, loadVoltage):
    #     """
    #     Sets up the DC-DC Converter object for the simulation.

    #     Parameters
    #     ----------
    #     arrayVoltage: float
    #         Expected array output voltage.
    #     loadVoltage: float
    #         Initial load voltage. This is the battery in the case of the solar
    #         array.
    #     """
    #     self._DCDCConverter.setup(arrayVoltage, loadVoltage)

    # # Simulation pipeline management.
    # def resetPipeline(self, voltage=0.0):
    #     """
    #     Resets components within the pipeline to the default state.
    #     By default, voltage applied across the source is 0V, and the cycle is 0.

    #     Parameters
    #     ----------
    #     voltage: float
    #         Initial VREF of the simulation.
    #     """
    #     self._PVEnv.setCycle(0)
    #     self._MPPT.reset()
    #     self._DCDCConverter.reset()
    #     self.datastore = None

    #     self._vREF = voltage

    # def iteratePipelineCycleSource(self):
    #     """
    #     Runs an entire cycle through the pipeline, using components required for
    #     a Source Simulation.
    #     """
    #     # Get the current simulation cycle.
    #     cycle = self._PVEnv.getCycle()

    #     # Retrieve the source definition for the current simulation cycle.
    #     modulesDef = self._PVEnv.getSourceDefinition(0)
    #     envDef = self._PVEnv.getAgglomeratedEnvironmentDefinition()

    #     # Retrieve the source characteristics given the source definition.
    #     sourceIV = self._PVSource.getIV(modulesDef)
    #     sourceEdgeChar = self._PVSource.getEdgeCharacteristics(modulesDef)

    #     # Store our output into our datastore.
    #     self.datastore["cycle"].append(cycle)
    #     self.datastore["sourceDef"].append(modulesDef)
    #     self.datastore["sourceOutput"].append(
    #         {"current": 0, "IV": sourceIV, "edge": sourceEdgeChar}
    #     )
    #     self.datastore["mpptOutput"].append(0)
    #     self.datastore["dcdcOutput"].append(0)

    #     # Increment the current simulation cycle.
    #     self._PVEnv.cycle()

    # def iteratePipelineCycleMPPT(self):
    #     """
    #     Runs an entire cycle through the pipeline, using components required for
    #     a MPPT Simulation.
    #     """
    #     # Get the current simulation cycle.
    #     cycle = self._PVEnv.getCycle()

    #     # Retrieve the source definition for the current simulation cycle.
    #     modulesDef = self._PVEnv.getSourceDefinition(self._vREF)
    #     envDef = self._PVEnv.getAgglomeratedEnvironmentDefinition()

    #     # Retrieve the source characteristics given the source definition.
    #     sourceCurrent = self._PVSource.getSourceCurrent(modulesDef)
    #     sourceIV = self._PVSource.getIV(modulesDef)
    #     sourceEdgeChar = self._PVSource.getEdgeCharacteristics(modulesDef)

    #     # Retrieve the MPPT VREF guess given the source output current.
    #     vRef = self._MPPT.getReferenceVoltage(
    #         self._vREF,
    #         sourceCurrent,
    #         envDef["irradiance"],
    #         envDef["temperature"],
    #     )

    #     # Generate the pulsewidth of the DC-DC Converter and spit it back out.
    #     self._DCDCConverter.setPulseWidth(vRef)
    #     pulseWidth = self._DCDCConverter.getPulseWidth()

    #     # Store our output into our datastore.
    #     self.datastore["cycle"].append(cycle)
    #     self.datastore["sourceDef"].append(modulesDef)
    #     self.datastore["sourceOutput"].append(
    #         {"current": sourceCurrent, "IV": sourceIV, "edge": sourceEdgeChar}
    #     )
    #     self.datastore["mpptOutput"].append(vRef)
    #     self.datastore["dcdcOutput"].append(pulseWidth)

    #     # Assign the VREF to apply across the source in the next simulation cycle.
    #     self._vREF = vRef

    #     # Increment the current simulation cycle.
    #     self._PVEnv.cycle()

    def generateSourceCurve(
        self, irradiance, temperature, voltageResolution, modelType, useLookup
    ):
        """
        Generates a source curve for the given parameters.

        Parameters
        ----------
        irradiance: float
            PVEnvironment irradiance.
        temperature: float
            PVEnvironment temperature.
        voltageResolution: float
            Voltage resolution step for the I-V curve (controls how many points
            will be plotted).
        modelType: String
            Selects what the cell model type is.
        useLookup: bool
            Indicates whether to use a lookup table if there are any.

        Returns
        -------
        A tuple of x and y coordinate attributes, corresponding to the voltage
        and current pairs of the I-V curve.
        """
        # Setup the PVEnvironment.
        # We don't care about the max cycles in this case.
        self._PVEnv.setupModel((irradiance, temperature), 0)

        # Setup the PVSource.
        self._PVSource.setupModel(modelType, useLookup)

        # Extract the I-V and P-V curve from the source.
        # We don't care about the voltage input in this case (since we grab the
        # entire I-V curve, which iterates over all voltages).
        modulesDef = self._PVEnv.getSourceDefinition(0.0)
        IVCoordinates = self._PVSource.getIV(modulesDef, voltageResolution)

        # Parse it into a format directly ingestable by the UIController.
        xVals = []
        yVals = []
        for coordinate in IVCoordinates:
            xVals.append(coordinate[0])
            yVals.append(coordinate[1])

        return (xVals, yVals)