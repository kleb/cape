r"""
Databook module for :mod:`cape.pycart`

This module contains functions for reading and processing forces,
moments, and other statistics from cases in a trajectory.

    .. code-block:: python

        # Read Cart3D control instance
        cntl = cape.pycart.cntl.Cntl("pyCart.json")
        # Read the data book
        cntl.ReadDataBook()
        # Get a handle
        db = cntl.DataBook

Data book modules are also invoked during update and reporting
command-line calls.

    .. code-block:: console

        $ pycart --aero
        $ pycart --ll
        $ pycart --report

:See Also:
    * :mod:`cape.cfdx.dataBook`
    * :mod:`cape.cfdx.lineLoad`
    * :mod:`cape.cfdx.pointSensor`
    * :mod:`cape.pycart.lineLoad`
    * :mod:`cape.cfdx.options.databookopts`
    * :mod:`cape.pycart.options.databookopts`
"""

# Standard library
import os

# Third party
import numpy as np

# Local imports
from . import util
from . import case
from . import lineLoad
from . import pointSensor
from ..cfdx import dataBook


# Radian -> degree conversion
deg = np.pi / 180.0


# Aerodynamic history class
class DataBook(dataBook.DataBook):
    r"""Interface to the overall Cart3D run matrix

    :Call:
        >>> DB = pyCart.dataBook.DataBook(x, opts)
    :Inputs:
        *x*: :class:`cape.pycart.runmatrix.RunMatrix`
            The current pyCart trajectory (i.e. run matrix)
        *opts*: :class:`cape.pycart.options.Options`
            Global pyCart options instance
    :Outputs:
        *DB*: :class:`cape.pycart.dataBook.DataBook`
            Instance of the pyCart data book class
    :Versions:
        * 2015-01-03 ``@ddalle``: v1.0
        * 2015-10-16 ``@ddalle``: v1.1: subclass
    """
    # Function to read targets if necessary
    def ReadTarget(self, targ):
        r"""Read a data book target if it is not already present

        :Call:
            >>> DB.ReadTarget(targ)
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of the Cape data book class
            *targ*: :class:`str`
                Target name
        :Versions:
            * 2015-09-16 ``@ddalle``: v1.0
        """
        # Initialize targets if necessary
        try:
            self.Targets
        except AttributeError:
            self.Targets = {}
        # Try to access the target.
        try:
            self.Targets[targ]
        except Exception:
            # Get the target type
            typ = self.opts.get_DataBookTargetType(targ).lower()
            # Check the type
            if typ in ['duplicate', 'cape', 'pycart', 'pyfun', 'pyover']:
                # Read a duplicate data book
                self.Targets[targ] = DataBook(
                    self.x, self.opts, RootDir=self.RootDir, targ=targ)
                # Update the trajectory
                self.Targets[targ].UpdateRunMatrix()
            else:
                # Read the file.
                self.Targets[targ] = DBTarget(
                    targ, self.x, self.opts, self.RootDir)

    # Initialize a DBComp object
    def ReadDBComp(self, comp, check=False, lock=False):
        r"""Initialize data book for one component

        :Call:
            >>> DB.ReadDBComp(comp, check=False, lock=False)
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of the pyCart data book class
            *comp*: :class:`str`
                Name of component
            *check*: ``True`` | {``False``}
                Whether or not to check LOCK status
            *lock*: ``True`` | {``False``}
                If ``True``, wait if the LOCK file exists
        :Versions:
            * 2015-11-10 ``@ddalle``: v1.0
            * 2016-06-27 ``@ddalle``: v1.1; add *targ* keyword
            * 2017-04-13 ``@ddalle``: v2.0; self-contained
        """
        self[comp] = DBComp(
            comp, self.cntl,
            targ=self.targ, check=check, lock=lock)

    # Read line load
    def ReadLineLoad(self, comp, conf=None, targ=None):
        r"""Read a line load data book target if not already present

        :Call:
            >>> DB.ReadLineLoad(comp)
        :Inputs:
            *DB*: :class:`pycart.dataBook.DataBook`
                Instance of the pycart data book class
            *comp*: :class:`str`
                Line load component group
            *conf*: {``"None"``} | :class:`cape.config.Config`
                Surface configuration interface
            *targ*: {``"None"``} | :class:`str`
                Sets alternate directory to read from, defaults to *DB.targ*
        :Versions:
            * 2015-09-16 ``@ddalle``: v1.0
            * 2016-06-27 ``@ddalle``: v1.1; add *targ*
        """
        # Initialize if necessary
        try:
            self.LineLoads
        except Exception:
            self.LineLoads = {}
        if comp is True:
            breakpoint()
        # Try to access the line load
        try:
            if targ is None:
                # Check for the line load data book as is
                self.LineLoads[comp]
            else:
                # Check for the target
                self.ReadTarget(targ)
                # Check for the target line load
                self.Targets[targ].LineLoads[comp]
        except Exception:
            # Safely go to root directory
            fpwd = os.getcwd()
            os.chdir(self.RootDir)
            # Default target name
            if targ is None:
                # Read the file.
                self.LineLoads[comp] = lineLoad.DBLineLoad(
                    comp, self.cntl,
                    conf=conf, RootDir=self.RootDir, targ=self.targ)
            else:
                # Read as a specified target.
                ttl = '%s\\%s' % (targ, comp)
                # Read the file.
                self.LineLoads[ttl] = lineLoad.DBLineLoad(
                    comp, self.cntl,
                    conf=conf, RootDir=self.RootDir, targ=targ)
            # Return to starting location
            os.chdir(fpwd)

    # Read TrqiFM components
    def ReadTriqFM(self, comp, check=False, lock=False):
        r"""Read a TriqFM data book if not already present

        :Call:
            >>> DB.ReadTriqFM(comp, check=False, lock=False)
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of pyCart data book class
            *comp*: :class:`str`
                Name of TriqFM component
            *check*: ``True`` | {``False``}
                Whether or not to check LOCK status
            *lock*: ``True`` | {``False``}
                If ``True``, wait if the LOCK file exists
        :Versions:
            * 2017-03-29 ``@ddalle``: v1.0
        """
        # Initialize if necessary
        try:
            self.TriqFM
        except Exception:
            self.TriqFM = {}
        # Try to access the TriqFM database
        try:
            self.TriqFM[comp]
            # Confirm lock
            if lock:
                self.TriqFM[comp].Lock()
        except Exception:
            # Safely go to root directory
            fpwd = os.getcwd()
            os.chdir(self.RootDir)
            # Read data book
            self.TriqFM[comp] = DBTriqFM(
                self.x, self.opts, comp,
                RootDir=self.RootDir, check=check, lock=lock)
            # Return to starting position
            os.chdir(fpwd)

    # Read point sensor (group)
    def ReadPointSensor(self, name, pts=None):
        r"""Read a point sensor group if it is not already present

        :Call:
            >>> DB.ReadPointSensor(name)
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of the pyCart data book class
            *name*: :class:`str`
                Name of point sensor group
        :Versions:
            * 2015-12-04 ``@ddalle``: v1.0
        """
        # Initialize if necessary.
        try:
            self.PointSensors
        except AttributeError:
            self.PointSensors = {}
        # Initialize the group if necessary
        try:
            # Check for DataBook PointGroup
            self.PointSensors[name]
            # Check for points
            if pts is None:
                pts = self.opts.get_DataBookPoints(name)
            # Check for all the points
            for pt in pts:
                # Check the point
                try:
                    self.PointSensors[name][pt]
                    continue
                except Exception:
                    # Read the new point
                    self.PointSensors[name][pt] = self._DBPointSensor(
                        self.x, self.opts, pt, name)
        except Exception:
            # Safely go to root directory
            fpwd = os.getcwd()
            os.chdir(self.RootDir)
            # Read the point sensor.
            self.PointSensors[name] = self._DBPointSensorGroup(
                self.x, self.opts, name, pts=pts, RootDir=self.RootDir)
            # Return to starting location
            os.chdir(fpwd)

    # Read point sensor (point to correct class)
    def _DBPointSensorGroup(self, *a, **kw):
        r"""Read pyCart data book point sensor group

        :Call:
            >>> DBP = DB._DBPointSensorGroup(*a, **kw)
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of the pyCart data book class
        :Outputs:
            *DBP*: :class:`cape.pycart.pointSensor.DBPointSensorGroup`
                Data book point sensor group
        :Versions:
            * 2016-03-15 ``@ddalle``: v1.0
        """
        return pointSensor.DBPointSensorGroup(*a, **kw)

    # Read point sensor (point to correct class)
    def _DBPointSensor(self, *a, **kw):
        r"""Read pyCart data book point sensor

        :Call:
            >>> DBP = DB._DBPointSensor(*a, **kw)
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of the pyCart data book class
        :Outputs:
            *DBP*: :class:`cape.pycart.pointSensor.DBPointSensor`
                Data book point sensor
        :Versions:
            * 2016-03-15 ``@ddalle``: v1.0
        """
        return pointSensor.DBPointSensor(*a, **kw)

    # Local version of data book
    def _DataBook(self, targ):
        self.Targets[targ] = DataBook(
            self.x, self.opts, RootDir=self.RootDir, targ=targ)

    # Local version of target
    def _DBTarget(self, targ):
        self.Targets[targ] = DBTarget(targ, self.x, self.opts, self.RootDir)

    # Local line load data book read
    def _DBLineLoad(self, comp, conf=None, targ=None):
        r"""Version-specific line load reader

        :Versions:
            * 2017-04-18 ``@ddalle``: v1.0
        """
        # Check for target
        if targ is None:
            self.LineLoads[comp] = lineLoad.DBLineLoad(
                comp, self.cntl,
                conf=conf, RootDir=self.RootDir, targ=self.targ)
        else:
            # Read as a specified target.
            ttl = '%s\\%s' % (targ, comp)
            # Get the keys
            topts = self.opts.get_DataBookTargetByName(targ)
            keys = topts.get("Keys", self.x.cols)
            # Read the file.
            self.LineLoads[ttl] = lineLoad.DBLineLoad(
                comp, self.cntl, keys=keys,
                conf=conf, RootDir=self.RootDir, targ=targ)

    # Update point sensor group
    def UpdatePointSensor(self, name, I=None):
        r"""Update a point sensor group data book for a list of cases

        :Call:
            >>> DB.UpdatePointSensorGroup(name)
            >>> DB.UpdatePointSensorGroup(name, I)
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of the pyCart data book class
            *I*: :class:`list`\ [:class:`int`] or ``None``
                List of trajectory indices or update all cases in trajectory
        :Versions:
            * 2015-10-04 ``@ddalle``: v1.0
        """
        # Default case list
        if I is None:
            # Use all trajectory points
            I = range(self.x.nCase)
        # Read the point sensors if necessary
        self.ReadPointSensor(name)
        # Loop through cases.
        for i in I:
            # Update the point sensors for that case
            self.PointSensors[name].UpdateCase(i)

    # Function to delete entries by index
    def Delete(self, I):
        r"""Delete list of cases from data book

        :Call:
            >>> DB.Delete(I)
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of the pyCart data book class
            *I*: :class:`list`\ [:class:`int`]
                List of trajectory indices or update all cases in trajectory
        :Versions:
            * 2015-03-13 ``@ddalle``: v1.0
        """
        # Get the first data book component.
        DBc = self[self.Components[0]]
        # Number of cases in current data book.
        nCase = DBc.n
        # Initialize data book index array.
        J = []
        # Loop though indices to delete.
        for i in I:
            # Find the match.
            j = DBc.FindMatch(i)
            # Check if one was found.
            if np.isnan(j):
                continue
            # Append to the list of data book indices.
            J.append(j)
        # Initialize mask of cases to keep.
        mask = np.ones(nCase, dtype=bool)
        # Set values equal to false for cases to be deleted.
        mask[J] = False
        # Loop through components.
        for comp in self.Components:
            # Extract data book component.
            DBc = self[comp]
            # Loop through data book columns.
            for c in DBc.keys():
                # Apply the mask
                DBc[c] = DBc[c][mask]
            # Update the number of entries.
            DBc.n = len(DBc['nIter'])

  # ========
  # Case I/O
  # ========
  # <
    # Current iteration status
    def GetCurrentIter(self):
        r"""Determine iteration number of current folder

        :Call:
            >>> n = DB.GetCurrentIter()
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of data book class
        :Outputs:
            *n*: :class:`int` | ``None``
                Iteration number
        :Versions:
            * 2017-04-13 ``@ddalle``: v1.0
        """
        try:
            return case.GetCurrentIter()
        except Exception:
            return None

    # Read case residual
    def ReadCaseResid(self):
        r"""Read a :class:`CaseResid` object

        :Call:
            >>> H = DB.ReadCaseResid()
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of data book class
        :Outputs:
            *H*: :class:`pyFun.dataBook.CaseResid`
                Residual history class
        :Versions:
            * 2017-04-13 ``@ddalle``: First separate version
        """
        # Read CaseResid object from PWD
        return CaseResid()

    # Read case FM history
    def ReadCaseFM(self, comp):
        r"""Read a :class:`CaseFM` object

        :Call:
            >>> FM = DB.ReadCaseFM(comp)
        :Inputs:
            *DB*: :class:`cape.pycart.dataBook.DataBook`
                Instance of data book class
            *comp*: :class:`str`
                Name of component
        :Outputs:
            *FM*: :class:`pyFun.dataBook.CaseFM`
                Residual history class
        :Versions:
            * 2017-04-13 ``@ddalle``: First separate version
        """
        # Read CaseResid object from PWD
        return CaseFM(comp)
  # >


# Individual component data book
class DBComp(dataBook.DBComp):
    pass


# Data book target instance
class DBTarget(dataBook.DBTarget):
    pass


# TriqFM data book
class DBTriqFM(dataBook.DBTriqFM):
    r"""Force and moment component extracted from surface triangulation

    :Call:
        >>> DBF = DBTriqFM(x, opts, comp, RootDir=None)
    :Inputs:
        *x*: :class:`cape.runmatrix.RunMatrix`
            RunMatrix/run matrix interface
        *opts*: :class:`cape.options.Options`
            Options interface
        *comp*: :class:`str`
            Name of TriqFM component
        *RootDir*: {``None``} | :class:`st`
            Root directory for the configuration
    :Outputs:
        *DBF*: :class:`cape.pycart.dataBook.DBTriqFM`
            Instance of TriqFM data book
    :Versions:
        * 2017-03-29 ``@ddalle``: v1.0
    """
    # Get file
    def GetTriqFile(self):
        r"""Get most recent ``triq`` file and its associated iterations

        :Call:
            >>> qtriq, ftriq, n, i0, i1 = DBF.GetTriqFile()
        :Inputs:
            *DBF*: :class:`cape.pycart.dataBook.DBTriqFM`
                Instance of TriqFM data book
        :Outputs:
            *qtriq*: {``False``}
                Whether or not to convert file from other format
            *ftriq*: :class:`str`
                Name of ``triq`` file
            *n*: :class:`int`
                Number of iterations included
            *i0*: :class:`int`
                First iteration in the averaging
            *i1*: :class:`int`
                Last iteration in the averaging
        :Versions:
            * 2016-12-19 ``@ddalle``: v1.0
        """
        # Get properties of triq file
        ftriq, n, i0, i1 = case.GetTriqFile()
        # Output
        return False, ftriq, n, i0, i1


# Individual component force and moment
class CaseFM(dataBook.CaseFM):
    r"""Cart3D iterative force & moment class

    This class contains methods for reading data about an the history of
    an individual component for a single case.  It reads the file
    ``{comp}.dat`` where *comp* is the name of the component. From this
    file it determines which coefficients are recorded automatically.
    If some of the comment lines from the Cart3D output file have been
    deleted, it guesses at the column definitions based on the number of
    columns.

    :Call:
        >>> FM = CaseFM(comp)
    :Inputs:
        *comp*: :class:`str`
            Name of component to process
    :Outputs:
        *FM*: :class:`cape.pycart.dataBook.CaseFM`
            Instance of the force and moment class
        *FM.coeffs*: :class:`list`\ [:class:`str`]
            List of coefficients
    :Versions:
        * 2014-11-12 ``@ddalle``: v1.0 (``aero.FM``)
        * 2014-12-21 ``@ddalle``: v1.0
        * 2015-10-16 ``@ddalle``: v2.0; self-contained
    """
    # Initialization method
    def __init__(self, comp):
        r"""Initialization method

        :Versions:
            * 2014-11-12 ``@ddalle``: v1.0
            * 2015-10-16 ``@ddalle``: v2.0; single arg
        """
        # Save component name
        self.comp = comp
        self.cols = []
        # Get the working folder.
        fdir = util.GetWorkingFolder()
        # Expected name of the component history file
        fname = os.path.join(fdir, comp+'.dat')
        # Check if it exists.
        if not os.path.isfile(fname):
            # Make an empty CaseFM
            self.init_empty()
            return
        # Otherwise, read the file.
        lines = open(fname).readlines()
        # Process the column meanings.
        self.ProcessColumnNames(lines)
        # Filter comments
        lines = [l for l in lines if not l.startswith('#')]
        # Convert all values to floats
        # (This is not guaranteed to be rectangular yet.)
        V = [[float(v) for v in l.split()] for l in lines]
        # Number of coefficients.
        n = len(self.coeffs)
        # Create an array with the original data
        A = np.array([v[0:1] + v[-n:] for v in V])
        # Get number of values in each raw data row.
        L = np.array([len(v) for v in V])
        # Check for columns without an extra column.
        if np.any(L == n+1):
            # At least one steady-state iteration.
            n0 = np.max(A[L == n + 1, 0])
            # Add that iteration number to the time-accurate steps.
            A[L != n + 1, 0] += n0
        # Save the values.
        for k, col in enumerate(list(self.cols)):
            # Set the values from column *k* of the data
            self.save_col(col, A[:, k])

    # Process the column names
    def ProcessColumnNames(self, lines):
        r"""Determine column names

        :Call:
            >>> FM.ProcessColumnNames(lines)
        :Inputs:
            *FM*: :class:`cape.pycart.dataBook.CaseFM`
                Case force/moment history
            *lines*: :class:`list`\ [:class:`str`]
                List of lines from the data file
        :Versions:
            * 2015-10-16 ``@ddalle``: v1.0
        """
        # Get the lines from the file that explain the contents.
        lines = [l for l in lines if l.startswith('# cycle')]
        # Check for lines
        if len(lines) == 0:
            # Alert to the status of this file.
            print("Warning: no header found for component '%s'" % self.comp)
            # Use a data line.
            lines = [l for l in lines if not l.startswith('#')]
            # Check for lines.
            if len(lines) == 0:
                print("Warning: no data found for component '%s'" % self.comp)
                # Empty
                self.init_empty()
                return
            # Split into values
            vals = lines[0].split()
            # Guess at the uses from contents.
            if len(vals) > 6:
                # Full force-moment
                self.C = ['CA', 'CY', 'CN', 'CLL', 'CLM', 'CLN']
                self.txt = ['Fx', 'Fy', 'Fz', 'Mx', 'My', 'Mz']
            elif len(vals) in [4, 5]:
                # Force only (ambiguous with 2D F&M
                self.C = ['CA', 'CY', 'CN']
                self.txt = ['Fx', 'Fy', 'Fz']
            else:
                # Guess at 2D force
                self.C = ['CA', 'CN']
                self.txt = ['Fx', 'Fz']
            # Add iteration to column list.
            self.cols = ['i'] + self.C
            self.txt.prepend('cycle')
            return
        # Read the contents
        self.txt = lines[0].lstrip('#').strip().split()
        self.cols = []
        self.coeffs = []
        # Loop through columns.
        for i in range(len(self.txt)):
            # Get the raw column name.
            col = self.txt[i]
            # Filter its name
            if col == 'cycle':
                # Iteration number
                self.cols.append('i')
            elif col == 'i':
                # Iteration number
                self.cols.append('i')
            elif col == 'Fx':
                # Axial force coefficient
                self.cols.append('CA')
                self.coeffs.append('CA')
            elif col == 'Fy':
                # Side force coefficient
                self.cols.append('CY')
                self.coeffs.append('CY')
            elif col == 'Fz':
                # Normal force coefficient
                self.cols.append('CN')
                self.coeffs.append('CN')
            elif col == 'Mx':
                # Rolling moment
                self.cols.append('CLL')
                self.coeffs.append('CLL')
            elif col == 'My':
                # Pitching moment
                self.cols.append('CLM')
                self.coeffs.append('CLM')
            elif col == 'Mz':
                # Yawing moment
                self.cols.append('CLN')
                self.coeffs.append('CLN')
            else:
                # Something else
                self.cols.append(col)
                self.coeffs.append(col)

    # Write a pure file
    def Write(self, fname):
        r"""Write contents to force/moment file

        :Call:
            >>> FM.Write(fname)
        :Inputs:
            *FM*: :class:`cape.pycart.dataBook.CaseFM`
                Instance of the force and moment class
            *fname*: :class:`str`
                Name of file to write.
        :Versions:
            * 2015-03-02 ``@ddalle``: v1.0
        """
        # Open the file for writing.
        f = open(fname, 'w')
        # Start the header.
        f.write('# ')
        # Write the raw column titles
        f.write(' '.join(self.txt))
        # End the header.
        f.write('\n')
        # Initialize the data
        A = np.array([self.get_values("i")])
        # Loop through coefficients.
        for c in self.coeffs:
            # Append the data.
            A = np.vstack((A, [self.get_values(c)]))
        # Transpose.
        A = A.transpose()
        # Form the string flag.
        flg = '%i' + (' %s'*len(self.coeffs)) + '\n'
        # Loop through iterations.
        for v in A:
            # Write the line.
            f.write(flg % tuple(v))
        # Close the file.
        f.close()


# Aerodynamic history class
class CaseResid(dataBook.CaseResid):
    r"""Iterative history class

    This class provides an interface to residuals, CPU time, and similar
    data for a given run directory

    :Call:
        >>> hist = CaseResid()
    :Outputs:
        *hist*: :class:`cape.pycart.dataBook.CaseResid`
            Instance of the run history class
    :Versions:
        * 2014-11-12 ``@ddalle``: v1.0
    """
    # Initialization method
    def __init__(self):
        r"""Initialization method

        :Versions:
            * 2014-11-12 ``@ddalle``: v1.0
            * 2024-01-11 ``@ddalle``: v1.1; DataKit updates
        """
        # Initialize attributes
        self.cols = []
        # Process the best data folder
        fdir = util.GetWorkingFolder()
        # History file name
        fhist = os.path.join(fdir, 'history.dat')
        # Read the file
        lines = open(fhist).readlines()
        # Filter comments
        lines = [l for l in lines if not l.startswith('#')]
        # Convert all the values to floats.
        A = np.array([[float(v) for v in l.split()] for l in lines])
        # Get the indices of steady-state iterations.
        # (Time-accurate iterations are marked with decimal step numbers.)
        i = np.array(['.' not in l.split()[0] for l in lines])
        # Check for steady-state iterations.
        if np.any(i):
            # Get the last steady-state iteration.
            n0 = np.max(A[i, 0])
            # Add this to the time-accurate iteration numbers.
            A[np.logical_not(i), 0] += n0
            # Index of first unsteady iteration
            in0 = np.where(i)[0][-1]+1
        else:
            # No steady-state iterations.
            n0 = 0
            in0 = 0
        # Process unsteady iterations if any.
        if A[-1, 0] > n0:
            # Get the integer values of the iteration indices.
            # For example, both 2000.100 and 2001.00 are part of 2001
            nii = np.ceil(A[in0:, 0])
            # Get indices of lines in which the iteration changes
            ii = np.where(nii[1:] != nii[:-1])[0]
            # Index of first line for each iteration
            i0 = np.insert(ii+1, 0, 0) + in0
            # Index of last line for each iteration
            i1 = np.append(ii, len(nii)-1) + in0
        else:
            # No unsteady iterations.
            i0 = np.array([], dtype=int)
            i1 = np.array([], dtype=int)
        # Indices of steady-state iterations
        if n0 > 0:
            # Get the steady-state iterations from the '.' test above.
            i2 = np.where(i)[0]
        else:
            # No steady-state iterations
            i2 = np.arange(0)
        # Prepend the steady-state iterations.
        i0 = np.hstack((i2, i0))
        i1 = np.hstack((i2, i1))
        # Make sure these stupid things are ints.
        i0 = np.array(i0, dtype=int)
        i1 = np.array(i1, dtype=int)
        # Save the initial residuals
        self.save_col("L1Resid0", A[i0, 3])
        # Rewrite the history.dat file without middle subiterations.
        if not os.path.isfile('RUNNING'):
            # Iterations to keep.
            i = np.union1d(i0, i1)
            # Write the integer iterations and the first subiterations.
            open(fhist, 'w').writelines(np.array(lines)[i])
        # Eliminate subiterations.
        A = A[i1]
        # Save the number of iterations.
        self.nIter = int(A[-1, 0])
        # Save data
        for j, col in enumerate(("i", "CPUtime", "maxResid", "L1Resid")):
            self.save_col(col, A[:, j])
        # Process the CPUtime used for steady cycles
        if n0 > 0:
            # At least one steady-state cycle
            # Find the index of the last steady-state iter
            i0 = np.where(self["i"] == n0)[0] + 1
            # Get the CPU time used up to that point
            t = self.get_values("CPUtime", i0 - 1)
        else:
            # No steady state cycles.
            i0 = 0
            t = 0.0
        # Process the unsteady cycles.
        if self.nIter > n0:
            # Add up total CPU time for unsteady cycles.
            t += np.sum(self["CPUtime"][i0:])
        # Check for a 'user_time.dat' file.
        if os.path.isfile('user_time.dat'):
            # Loop through lines.
            for line in open('user_time.dat').readlines():
                # Check comment.
                if line.startswith('#'):
                    continue
                # Add to the time everything except flowCart time.
                t += np.sum([float(v) for v in line.split()[2:]])
        # Save the time
        self.CPUhours = t / 3600.

