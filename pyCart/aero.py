"""
Aerodynamic Iterative History: :mod:`pyCart.aero`
=================================================

This module contains functions for reading and processing forces, moments, and
other statistics from a run directory.

:Versions:
    * 2014-11-12 ``@ddalle``: Starter version
"""

# File interface
import os
# Basic numerics
import numpy as np
# Advanced text (regular expressions)
import re


# Aerodynamic history class
class Aero(dict):
    """
    Aerodynamic history class
    =========================
    
    This class provides an interface to important data from a run directory.  It
    reads force and moment histories for named components, if available, and
    other types of data can also be stored
    
    :Call:
        >>> aero = pyCart.aero.Aero(comps=[])
    :Inputs:
        *comps*: :class:`list` (:class:`str`)
            List of components to read; defaults to all components available
    :Outputs:
        *aero*: :class:`pyCart.aero.Aero`
            Instance of the aero history class
        *aero*: :class:`dict` (:class:`numpy.ndarray`)
            Dictionary of force and/or moment histories
    :Versions:
        * 2014-11-12 ``@ddalle``: Starter version
    """
    
    # Initialization method
    def __init__(self, comps=[]):
        """Initialization method
        
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Process the best data folder.
        if os.path.isfile('history.dat'):
            # Use current directory.
            fdir = '.'
        elif os.path.islink('BEST'):
            # There's a BEST/ folder; use it as most recent adaptation cycle.
            fdir = 'BEST'
        elif os.path.isdir('adapt00'):
            # It's an adaptive run, but it hasn't gotten far yet.
            fdir = 'adapt00'
        else:
            # This is not an adaptive cycle; use root folder.
            fdir = '.'
        # Read the loadsCC.dat file to see what components are requested.
        self.ReadLoadsCC()
        # Read the residuals.
        self.Residual = History()
        # Default component list.
        if (type(comps).__name__ in ["str", "unicode", "int"]):
            # Make a singleton list.
            comps = [comps]
        elif len(comps) < 1:
            # Extract keys from dictionary.
            comps = self.Components.keys()
        # Loop through components.
        for comp in comps:
            # Expected name of the history file.
            fname = os.path.join(fdir, comp+'.dat')
            # Check if it exists.
            if not os.path.isfile(fname):
                # Warn and got to the next component.
                print("Warning: Component '%s' was not found." % comp)
                continue
            # Otherwise, read the file.
            lines = open(fname).readlines()
            # Filter comments
            lines = [l for l in lines if not l.startswith('#')]
            # Convert all the values to floats
            # Can't make this an array yet because it's not rectangular.
            V = [[float(v) for v in l.split()] for l in lines]
            # Columns to use: 0 and {-6,-3}:
            n = len(self.Components[comp]['C'])
            # Create an array with the original data.
            A = np.array([v[0:1] + v[-n:] for v in V])
            # Get the number of entries in each row.
            # This will be one larger if a time-accurate iteration.
            # It's a column of zeros, and it's the second column.
            L = np.array([len(v) for v in V])
            # Check for steady-state iterations.
            if np.any(L == n+1):
                # At least one steady-state iteration
                n0 = np.max(A[L==n+1,0])
                # Add that iteration number to the time-accurate steps.
                A[L!=n+1,0] += n0
            # Extract info from components for readability
            d = self.Components[comp]
            # Make the component.
            self[comp] = FM(d['C'], MRP=d['MRP'], A=A)
            
            
    # Function to read 'loadsCC.dat'
    def ReadLoadsCC(self):
        """Read forces and moments from a :file:`loadsCC.dat` file if possible
        
        :Call:
            >> aero.ReadLoadsCC()
        :Inputs:
            *aero*: :class:`pyCart.aero.Aero`
                Instance of the aero history class
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Initialize list of components.
        self.Components = {}
        # Check for the file.
        if os.path.isfile(os.path.join('BEST', 'loadsCC.dat')):
            # Use the most recent file.
            fCC = os.path.join('BEST', 'loadsCC.dat')
        elif os.path.isfile(os.path.join('adapt00', 'loadsCC.dat')):
            # Most recent adaptation currently running; no file in BEST
            fCC = os.path.join('adapt00', 'loadsCC.dat')
        elif os.path.isfile('loadsCC.dat'):
            # Non-adaptive run
            fCC = 'loadsCC.dat'
        else:
            # Nothing to do.
            return None
        # Read the file.
        linesCC = open(fCC).readlines()
        # Loop through the lines.
        for line in linesCC:
            # Strip line.
            line = line.strip()
            # Check for empty line or comment.
            if (not line) or line.startswith('#'): continue
            # Get name of component.
            comp = line.split()[0]
            # Add line to dictionary if necessary.
            if comp not in self.Components:
                self.Components[comp] = {'C':[], 'MRP':None}
            # Try to get the coefficient name.
            try:
                # Find text like '(C_A)' and return 'C_A'.
                c = re.search('\(([A-Za-z_]+)\)', line).group(1)
            except Exception:
                # Failed to find expected text.
                print("Warning: no coefficient name in line:\n  '%s'" % line) 
                continue
            # Filter the coefficient.
            if c == 'C_A':
                # Axial force
                self.Components[comp]['C'].append('CA')
                continue
            elif c == 'C_Y': 
                # Lateral force
                self.Components[comp]['C'].append('CY')
                continue
            elif c == 'C_N':
                # Normal force
                self.Components[comp]['C'].append('CN')
                continue
            elif c == 'C_M_x':
                # Rolling moment
                self.Components[comp]['C'].append('CLL')
            elif c == 'C_M_y':
                # Pitching moment
                self.Components[comp]['C'].append('CLM')
            elif c == 'C_M_z':
                # Yaw moment
                self.Components[comp]['C'].append('CLN')
            else:
                # Extra coefficient such as lift, drag, etc.
                continue
            # Only process reference point once.
            if self.Components[comp]['MRP'] is not None: continue
            # Try to find reference point.
            try:
                # Search for text like '(17.0, 0, 0)'.
                txt = re.search('\(([0-9., -]+)\)', line).group(1)
                # Split into coordinates.
                MRP = np.array([float(v) for v in txt.split(',')])
                # Save it.
                self.Components[comp]['MRP'] = MRP
            except Exception:
                # Failed to find expected text.
                print("Warning: no reference point in line:\n  '%s'" % line)
                
        
# Individual component force and moment
class FM(object):
    """
    Individual force and moment class
    =================================
    
    This class contains methods for reading data about an individual component. 
    The list of available components comes from a :file:`loadsCC.dat` file if
    one exists.
    
    :Call:
        >>> FM = pyCart.aero.FM(C, MRP=None, A=None)
    :Inputs:
        *aero*: :class:`pyCart.aero.Aero`
            Instance of the aero history class
        *C*: :class:`list` (:class:`str`)
            List of coefficients to initialize
        *MRP*: :class:`numpy.ndarray` (:class:`float`) shape=(3,)
            Moment reference point
        *A*: :class:`numpy.ndarray` shape=(*N*,4) or shape=(*N*,7)
            Matrix of forces and/or moments at *N* iterations
    :Outputs:
        *FM*: :class:`pyCart.aero.FM`
            Instance of the force and moment class
        *FM.C*: :class:`list` (:class:`str`)
            List of coefficients
        *FM.MRP*: :class:`numpy.ndarray` (:class:`float`) shape=(3,)
            Moment reference point
        *FM.i*: :class:`numpy.ndarray` shape=(0,)
            List of iteration numbers
        *FM.CA*: :class:`numpy.ndarray` shape=(0,)
            Axial force coefficient at each iteration
        *FM.CY*: :class:`numpy.ndarray` shape=(0,)
            Lateral force coefficient at each iteration
        *FM.CN*: :class:`numpy.ndarray` shape=(0,)
            Normal force coefficient at each iteration
        *FM.CLL*: :class:`numpy.ndarray` shape=(0,)
            Rolling moment coefficient at each iteration
        *FM.CLM*: :class:`numpy.ndarray` shape=(0,)
            Pitching moment coefficient at each iteration
        *FM.CLN*: :class:`numpy.ndarray` shape=(0,)
            Yaw moment coefficient at each iteration
    :Versions:
        * 2014-11-12 ``@ddalle``: Starter version
    """
    # Initialization method
    def __init__(self, C, MRP=None, A=None):
        """Initialization method
        
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Save component list.
        self.C = C
        # Initialize iteration list.
        self.i = np.array([])
        # Loop through components.
        for c in C:
            setattr(self, c, np.array([]))
        # Save the MRP.
        self.MRP = np.array(MRP)
        # Check for data.
        if A is not None:
            # Use method to parse.
            self.AddData(A)
            
    # Function to display contents
    def __repr__(self):
        """Representation method
        
        Returns one of the following:
        
            * ``'<aero.FM Force, i=100>'``
            * ``'<aero.FM Moment, i=100, MRP=(0.00, 1.00, 2.00)>'``
            * ``'<aero.FM FM, i=100, MRP=(0.00, 1.00, 2.00)>'``
        
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Initialize the string.
        txt = '<aero.FM '
        # Check for a moment.
        if ('CA' in self.C) and ('CLL' in self.C):
            # Force and moment.
            txt += 'FM'
        elif ('CA' in self.C):
            # Force only
            txt += 'Force'
        elif ('CLL' in self.C):
            # Moment only
            txt += 'Moment'
        # Add number of iterations.
        txt += (', i=%i' % self.i.size)
        # Add MRP if possible.
        if (self.MRP.size == 3):
            txt += (', MRP=(%.2f, %.2f, %.2f)' % tuple(self.MRP))
        # Finish the string and return it.
        return txt + '>'
        
    # String method
    def __str__(self):
        """String method
        
        Returns one of the following:
        
            * ``'<aero.FM Force, i=100>'``
            * ``'<aero.FM Moment, i=100, MRP=(0.00, 1.00, 2.00)>'``
            * ``'<aero.FM FM, i=100, MRP=(0.00, 1.00, 2.00)>'``
        
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        return self.__repr__()
        
            
    # Method to add data to instance
    def AddData(self, A):
        """Add iterative force and/or moment history for a component
        
        :Call:
            >>> FM.AddData(A)
        :Inputs:
            *FM*: :class:`pyCart.aero.FM`
                Instance of the force and moment class
            *A*: :class:`numpy.ndarray` shape=(*N*,4) or shape=(*N*,7)
                Matrix of forces and/or moments at *N* iterations
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Get size of A.
        n, m = A.shape
        # Save the iterations.
        self.i = A[:,0]
        # Check size.
        if m == 7:
            # Save all fields.
            self.CA = A[:,1]
            self.CY = A[:,2]
            self.CN = A[:,3]
            self.CLL = A[:,4]
            self.CLM = A[:,5]
            self.CLN = A[:,6]
        elif (self.MRP.size==3) and (m == 4):
            # Save only moments.
            self.CLL = A[:,1]
            self.CLM = A[:,2]
            self.CLN = A[:,3]
        elif (m == 4):
            # Save only forces.
            self.CA = A[:,1]
            self.CY = A[:,2]
            self.CN = A[:,3]

    

# Aerodynamic history class
class History(object):
    """
    Iterative history class
    
    This class provides an interface to residuals, CPU time, and similar data
    for a given run directory
    
    :Call:
        >>> hist = pyCart.history.History()
    :Outputs:
        *hist*: :class:`pyCart.history.History`
            Instance of the run history class
    :Versions:
        * 2014-11-12 ``@ddalle``: Starter version
    """
    
    # Initialization method
    def __init__(self):
        """Initialization method
        
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        
        # Process the best data folder.
        if os.path.isfile('history.dat'):
            # Subsequent non-adaptive runs
            fdir = '.'
        elif os.path.islink('BEST'):
            # There's a BEST/ folder; use it as most recent adaptation cycle.
            fdir = 'BEST'
        elif os.path.isdir('adapt00'):
            # It's an adaptive run, but it hasn't gotten far yet.
            fdir = 'adapt00'
        else:
            # This is not an adaptive cycle; use root folder.
            fdir = '.'
        # History file name.
        fhist = os.path.join(fdir, 'history.dat')
        # Read the file.
        lines = open(fhist).readlines()
        # Filter comments.
        lines = [l for l in lines if not l.startswith('#')]
        # Convert all the values to floats.
        A = np.array([[float(v) for v in l.split()] for l in lines])
        # Get the indices of steady-state iterations.
        # (Time-accurate iterations are marked with decimal step numbers.)
        i = np.array(['.' not in l.split()[0] for l in lines])
        # Check for steady-state iterations.
        if np.any(i):
            # Get the last steady-state iteration.
            n0 = np.max(A[i,0])
            # Add this to the time-accurate iteration numbers.
            A[np.logical_not(i),0] += n0
        # Eliminate subiterations.
        A = A[np.mod(A[:,0], 1.0) == 0.0]
        # Save the number of iterations.
        self.nIter = A.shape[0]
        # Save the iteration numbers.
        self.i = np.arange(self.nIter) + 1
        # Save the CPU time per processor.
        self.CPUtime = A[:,1]
        # Save the maximum residual.
        self.maxResid = A[:,2]
        # Save the global residual.
        self.L1Resid = A[:,3]
        # Check for a 'user_time.dat' file.
        if os.path.isfile('user_time.dat'):
            # Initialize time
            t = 0.0
            # Loop through lines.
            for line in open('user_time.dat').readlines():
                # Check comment.
                if line.startswith('#'): continue
                # Add to the time.
                t += np.sum([float(v) for v in line.split()[1:]])
        else:
            # Find the indices of run break points.
            i = np.where(self.CPUtime[1:] < self.CPUtime[:-1])[0]
            # Sum the end times.
            t = np.sum(self.CPUtime[i]) + self.CPUtime[-1]
        # Save the time.
        self.CPUhours = t / 3600.
        
