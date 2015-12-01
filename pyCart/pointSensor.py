"""
Point Sensors Module: :mod:`pyCart.pointSensor`
===============================================

This module contains a class for reading and averaging point sensors.  It is not
included in the :mod:`pyCart.dataBook` module in order to give finer import
control when used in other modules

:Versions:
    * 2015-11-30 ``@ddalle``: First version
"""

# File interface
import os, glob
# Basic numerics
import numpy as np
# Special read line ignoring comments
from .util import readline
from .bin  import tail


# Check iteration number
def get_iter(fname):
    """Get iteration number from a point sensor single-iteration file
    
    :Call:
        >>> i = get_iter(fname)
    :Inputs:
        *fname*: :class:`str`
            Point sensor file name
    :Outputs:
        *i*: :class:`float`
            Iteration number or time
    :Versions:
        * 2015-11-30 ``@ddalle``: First version
    """
    # Safely check the last line of the file.
    try:
        # Get the last line.
        line = tail(fname, n=1)
        # Read the time step/iteration
        return float(line.split()[-1])
    except Exception:
        # No iterations
        return 0


# Data book of point sensors
class DBPointSensor(object):
    
    pass





# Individual point sensor
class CasePointSensor(object):
    
    # Initialization method
    def __init__(self):
        """Initialization method"""
        # Check for history file
        if os.path.isfile('pointSensors.hist.dat'):
            # Read the file
            self.ReadHist()
        else:
            # Initialize empty data
            self.nPoint = None
            self.nIter = 0
            self.nd = None
            self.data = np.zeros((0,0,12))
        # Read iterations if necessary.
        self.UpdateIterations()
        
    
    # Read the steady-state output file
    def UpdateIterations(self):
        """Read any Cart3D point sensor output files and save them
        
        :Call:
            >>> P.UpdateIterations()
        :Inputs:
            *P*: :class:`pyCart.pointSensor.CasePointSensor`
                Iterative point sensor history
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
        """
        # Extract iterative history
        i = self.data[0,:,-1]
        # Get last iteration
        if len(i) > 0: imax = max(i)
        else: imax = 0
        # Check for steady-state iteration.
        if get_iter('pointSensors.dat') > imax
            # Read the file.
            PS = PointSensor('pointSensor.dat')
            # Save the iterations
            self.AppendIteration(PS)
            # Extract iterative history
            i = self.data[0,:,-1]
            # Get last iteration
            if len(i) > 0: imax = max(i)
            else: imax = 0
        # Check for time-accurate iterations.
        fglob = glob.glob('pointSensors.[0-9][0-9]*.dat')
        iglob = np.array([int(f) for f in fglob])
        iglob.sort()
        # Check scenario
        if os.path.isfile('pointSensors.dat'):
            # Check for reset.
            if len(i) > 1 and np.any(i[1:] < i[:-1]):
                # At least one time-accurate data point included
                iglob = iglob[iglob > imax]
        else:
            # Time-accurate results only; filter on *imax*
            iglob = iglob[iglob > imax]
        # Read the time-accurate iterations
        for i in iglob:
            # File name
            fi = "pointSensors.%05i.dat" % i
            # Read the file.
            PS = PointSensor(fi)
            # Save the data.
            self.AppendIteration(PS)
        
        
    # Read history file
    def ReadHist(self, fname='pointSensors.hist.dat'):
        """Read point sensor iterative history file
        
        :Call:
            >>> P.ReadHist(fname='pointSensors.hist.dat')
        :Inputs:
            *fname*: :class:`str`
                Name of point sensor history file
        :Outputs:
            *P*: :class:`pyCart.pointSensor.CasePointSensor`
                Iterative point sensor history
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
        """
        # Check for the file
        if not os.path.isfile(fname):
            raise SystemError("File '%s' does not exist." % fname)
        # Open the file.
        f = open(fname, 'r')
        # Read the first line, which contains identifiers.
        line = readline(f)
        # Get the values
        nPoint, nIter, nd = [int(v) for v in line.split()]
        # Save
        self.nPoint = nPoint
        self.nIter  = nIter
        self.nd     = nd
        # Number of data columns
        if nd == 2:
            # Two-dimensional data
            nCol = 10
        else:
            # Three-dimensional data
            nCol = 12
        # Read data lines
        A = np.fromfile(f, dtype=float, count=nPoint*nIter*nCol, sep=" ")
        # Reshape
        self.data = A.reshape((nPoint, nIter, nCol))
        
    # Add another point sensor
    def AppendIteration(self, PS):
        """Add a single-iteration of point sensor data to the history
        
        :Call:
            >>> P.AppendIteration(PS)
        :Inputs:
            *P*: :class:`pyCart.pointSensor.CasePointSensor`
                Iterative point sensor history
            *PS*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
        """
        # Check compatibility
        if self.nPoint is None:
            # Use the point count from the individual file.
            self.nPoint = PS.nPoint
            self.nd = PS.nd
            self.nIter = 0
            # Initialize
            if self.nd == 2:
                self.data = np.zeros((self.nPoint, 0, 10))
            else:
                self.data = np.zeros((self.nPoint, 0, 12))
        elif self.nPoint != PS.nPoint:
            # Wrong number of points
            raise IndexError(
                "History has %i points; point sensor has %i points."
                % (self.nPoint, PS.nPoint))
        elif self.nd != PS.nd:
            # Wrong number of dimensions
            raise IndexError(
                "History is %-D; point sensor is %i-D." % (self.nd, PS.nd))
        # Get data from point sensor and add point number
        A = np.hstack((np.array([range(self.nPoint)]).transpose(), PS.data))
        # Append to history.
        self.data = np.hstack(
            (self.data, A.reshape((self.nPoint,1,self.nCol))))
        
# class CasePointSensor


# Individual file point sensor
class PointSensor(object):
    """Class for individual point sensor
    
    :Call:
        >>> PS = PointSensor(fname="pointSensors.dat", data=None)
    :Inputs:
        *fname*: :class:`str`
            Name of Cart3D output point sensors file
        *data*: :class:`np.ndarray` (:class:`float`)
            Data array with either 9 (2-D) or 11 (3-D) columns
    :Outputs:
        *PS*: :class:`pyCart.pointSensor.PointSensor`
            Point sensor
        *PS.data*: :class:`np.ndarray` (:class:`float`)
            Data array with either 9 (2-D) or 11 (3-D) columns
        *PS.nd*: ``2`` | ``3``
            Number of dimensions of the data
        *PS.nPoint*: :class:`int`
            Number of points in the file
        *PS.nIter*: :class:`int`
            Number of iterations used to calculate the average
    :Versions:
        * 2015-11-30 ``@ddalle``: First version
    """
    
    # Initialization method
    def __init__(self, fname="pointSensors.dat", data=None):
        """Initialization method"""
        # Check for data
        if data is None:
            # Read the file.
            self.data = np.loadtxt(fname, comments='#')
        else:
            # Save the input data.
            self.data = data
        # Check the dimensionality.
        if self.data.shape[1] == 9:
            # Two-dimensional data
            self.nd = 2
            self.X = self.data[:,0]
            self.Y = self.data[:,1]
            self.p   = self.data[:,2]
            self.rho = self.data[:,3]
            self.U   = self.data[:,4]
            self.V   = self.data[:,5]
            self.P   = self.data[:,6]
            self.RefLev = self.data[:,7]
            self.i      = self.data[:,8]
        else:
            # Three-dimensional data
            self.nd = 3
            self.X = self.data[:,0]
            self.Y = self.data[:,1]
            self.Z = self.data[:,2]
            self.p   = self.data[:,3]
            self.rho = self.data[:,4]
            self.U   = self.data[:,5]
            self.V   = self.data[:,6]
            self.W   = self.data[:,7]
            self.P   = self.data[:,8]
            self.RefLev = self.data[:,9]
            self.i      = self.data[:,10]
        # Save number of points
        self.nPoint = self.data.shape[0]
        # Number of averaged iterations
        self.nIter = 1
        
    # Representation method
    def __repr__(self):
        """Representation method
        
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
        """
        # Check dimensionality
        return "<PointSensor(nd=%i, nPoint=%i)>" % (self.nd, self.nPoint)
        
    # Copy a point sensor
    def copy(self):
        """Copy a point sensor
        
        :Call:
            >>> P2 = PS.copy()
        :Inputs:
            *PS*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor
        :Outputs:
            *P2*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor copied
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
        """
        return PointSensor(data=self.data)
        
    # Write to file
    def Write(self, fname):
        """Write single-iteration point sensor file
        
        :Call:
            >>> PS.Write(fname):
        :Inputs:
            *PS*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor
            *fname*: :class:`str`
                Name of Cart3D output point sensors file
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
        """
        # Open the file for writing.
        f = open(fname, 'w')
        # Write header
        if self.nd == 2:
            # Two-dimensional data
            f.write("VARIABLES = X Y (P-Pinf)/Pinf RHO U V P ")
            f.write("RefLev mgCycle/Time\n")
            # Format string
            fpr = (7*' %15.8e' + ' %i %7.3f\n')
        else:
            # Three-dimensional data
            f.write("VARIABLES = X Y Z (P-Pinf)/Pinf RHO U V W P ")
            f.write("RefLev mgCycle/Time\n")
            # Format string
            fpr = (9*' %15.8e' + ' %i %7.3f\n')
        # Write the points
        for i in range(self.nPoint):
            f.write(fpr % tuple(self.data[i,:]))
        # Close the file.
        f.close()
    
        
    # Multiplication
    def __mul__(self, c):
        """Multiplication method
        
        :Call:
            >>> P2 = PS.__mul__(c)
            >>> P2 = PS * c
        :Inputs:
            *PS*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor
            *c*: :class:`int` | :class:`float`
                Number by which to multiply
        :Outputs:
            *P2*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor copied
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
        """
        # Check the input
        t = type(c).__name__
        if not (tc.startswith('int') or tc.startswith('float')):
            return TypeError("Point sensors can only be multiplied by scalars.")
        # Create a copy
        P2 = self.copy()
        # Multiply
        if self.nd == 2:
            # Two-dimensional data
            P2.data[:,2:7] *= c
        else:
            # Two-dimensional data
            P2.data[:,3:9] *= c
        # If integer, multiply number of iiterations included
        if type(c).startswith('int'): P2.nIter*=c
        # Output
        return P2
    
    # Multiplication, other side
    __rmul__ = __mul__
    __rmul__.__doc__ = """Right-hand multiplication method
    
        :Call:
            >>> P2 = PS.__rmul__(c)
            >>> P2 = c * PS
        :Inputs:
            *PS*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor
            *c*: :class:`int` | :class:`float`
                Number by which to multiply
        :Outputs:
            *P2*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor copied
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
    """
    
    # Multiplication
    def __div__(self, c):
        """Multiplication method
        
        :Call:
            >>> P2 = PS.__div__(c)
            >>> P2 = PS / c
        :Inputs:
            *PS*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor
            *c*: :class:`int` | :class:`float`
                Number by which to divide
        :Outputs:
            *P2*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor copied
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
        """
        # Check the input
        t = type(c).__name__
        if not (tc.startswith('int') or tc.startswith('float')):
            return TypeError("Point sensors can only be multiplied by scalars.")
        # Create a copy
        P2 = self.copy()
        # Multiply
        if self.nd == 2:
            # Two-dimensional data
            P2.data[:,2:7] /= c
        else:
            # Two-dimensional data
            P2.data[:,3:9] /= c
        # Output
        return P2
    
    # Addition method
    def __add__(self, P1):
        """Addition method
        
        :Call:
            >>> P2 = PS.__add__(P1)
        :Inputs:
            *PS*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor
            *P2*: :class:`pyCart.pointSensor.PointSensor`
                Point sensor to add
        :Outputs:
            *P2*: :class:`pyCart.pointSensor.PointSensor`
                Point sensors added
        :Versions:
            * 2015-11-30 ``@ddalle``: First version
        """
        # Check compatibility
        if type(P1).__name__ != 'PointSensor':
            # One addend is not a point sensor
            return TypeError(
                "Only point sensors can be added to point sensors.")
        elif self.nd != P1.nd:
            # Incompatible dimension
            return IndexError("Cannot add 2D and 3D point sensors together.")
        elif self.nPoint != P1.nPoint:
            # Mismatching number of points
            return IndexError(
                "Sensor 1 has %i points, and sensor 2 has %i points." 
                % (self.nPoint, P1.nPoint))
        # Create a copy.
        P2 = self.copy()
        # Add
        if self.nd == 2:
            # Two-dimensional data
            P2.data[:,2:7] = self.data[:,2:7] + P1.data[:,2:7]
        else:
            # Two-dimensional data
            P2.data[:,3:9] = self.data[:,3:9] + P1.data[:,3:9]
        # Number of iterations
        P2.nIter = self.nIter + P1.nIter
        # Output
        return P2
# class PointSensor

