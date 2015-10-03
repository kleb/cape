"""
Data Book Module: :mod:`pyCart.dataBook`
========================================

This module contains functions for reading and processing forces, moments, and
other statistics from cases in a trajectory.

:Versions:
    * 2014-12-20 ``@ddalle``: Started
    * 2015-01-01 ``@ddalle``: First version
"""

# File interface
import os
# Basic numerics
import numpy as np
# Advanced text (regular expressions)
import re
# Date processing
from datetime import datetime

# Use this to only update entries with newer iterations.
from .case import GetCurrentIter, GetWorkingFolder
# Finer control of dicts
from .options import odict
# Utilities or advanced statistics
from . import util
# Line loads
from . import lineLoad

# Template module
import cape.dataBook

#<!--
# ---------------------------------
# I consider this portion temporary

# Get the umask value.
umask = 0027
# Get the folder permissions.
fmask = 0777 - umask
dmask = 0777 - umask

# ---------------------------------
#-->

# Placeholder variables for plotting functions.
plt = 0

# Radian -> degree conversion
deg = np.pi / 180.0

# Dedicated function to load Matplotlib only when needed.
def ImportPyPlot():
    """Import :mod:`matplotlib.pyplot` if not loaded
    
    :Call:
        >>> pyCart.dataBook.ImportPyPlot()
    :Versions:
        * 2014-12-27 ``@ddalle``: First version
    """
    # Make global variables
    global plt
    global tform
    global Text
    # Check for PyPlot.
    try:
        plt.gcf
    except AttributeError:
        # Load the modules.
        import matplotlib.pyplot as plt
        import matplotlib.transforms as tform
        from matplotlib.text import Text


# Aerodynamic history class
class DataBook(cape.dataBook.DataBook):
    """
    This class provides an interface to the data book for a given CFD run
    matrix.
    
    :Call:
        >>> DB = pyCart.dataBook.DataBook(x, opts)
    :Inputs:
        *x*: :class:`pyCart.trajectory.Trajectory`
            The current pyCart trajectory (i.e. run matrix)
        *opts*: :class:`pyCart.options.Options`
            Global pyCart options instance
    :Outputs:
        *DB*: :class:`pyCart.dataBook.DataBook`
            Instance of the pyCart data book class
    :Versions:
        * 2014-12-20 ``@ddalle``: Started
    """
    
    # Read line load
    def ReadLineLoad(self, comp):
        """Read a line load data book target if it is not already present
        
        :Call:
            >>> DB.ReadLineLoad(comp)
        :Inputs:
            *DB*: :class:`pycart.dataBook.DataBook`
                Instance of the pycart data book class
            *comp*: :class:`str`
                Line load component group
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Try to access the line load
        try:
            self.LineLoads[comp]
        except Exception:
            # Read the file.
            self.LineLoads.append(
                lineLoad.DBLineLoad(self.cart3d, comp))
    
    
            
    
    # Update data book
    def UpdateDataBook(self, I=None):
        """Update the data book for a list of cases from the run matrix
        
        :Call:
            >>> DB.UpdateDataBook()
            >>> DB.UpdateDataBook(I)
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *I*: :class:`list` (:class:`int`) or ``None``
                List of trajectory indices or update all cases in trajectory
        :Versions:
            * 2014-12-22 ``@ddalle``: First version
        """
        # Default.
        if I is None:
            # Use all trajectory points.
            I = range(self.x.nCase)
        # Loop through indices.
        for i in I:
            self.UpdateCase(i)
            
    # Update line load data book
    def UpdateLineLoadDataBook(self, comp, I=None):
        """Update a line load data book for a list of cases
        
        :Call:
            >>> DB.UpdateLineLoadDataBook(comp)
            >>> DB.UpdateLineLoadDataBook(comp, I)
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *I*: :class:`list` (:class:`int`) or ``None``
                List of trajectory indices or update all cases in trajectory
        :Versions:
            * 2015-09-17 ``@ddalle``: First version
        """
        # Default case list
        if I is None:
            # Use all trajectory points
            I = range(self.x.nCase)
        # Loop through indices.
        for i in I:
            self.UpdateLineLoadCase(comp, i)
        
    # Function to delete entries by index
    def Delete(self, I):
        """Delete list of cases from data book
        
        :Call:
            >>> DB.Delete(I)
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *I*: :class:`list` (:class:`int`)
                List of trajectory indices or update all cases in trajectory
        :Versions:
            * 2015-03-13 ``@ddalle``: First version
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
            if np.isnan(j): continue
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
        
            
    # Update one line load case
    def UpdateLineLoadCase(self, comp, i):
        """Update one line load case if necessary
        
        :Call:
            >>> DB.UpdateLineLoadCase(comp, i)
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *comp*: :class:`str`
                Name of line load group
            *i*: :class:`int`
                Case number
        :Versions:
            * 2015-09-17 ``@ddalle``: First version
        """
        # Read the line loads if necessary
        self.ReadLineLoad(comp)
        # Data book directory
        fdat = self.cart3d.opts.get_DataBookDir()
        flls = 'lineloads-%s' % comp
        fldb = os.path.join(fdat, flls)
        # Expected seam cut file
        fsmy = os.path.join(self.cart3d.Rootdir, fldb, '%s.smy'%comp)
        fsmz = os.path.join(self.cart3d.Rootdir, fldb, '%s.smz'%comp)
        # Extract line load
        DBL = self.LineLoad[comp]
        # Try to find a match existing in the data book.
        j = DBL.FindMatch(i)
        # Get the name of the folder.
        frun = self.cart3d.x.GetFullFolderNames(i)
        # Status update.
        print(frun)
        # Go home
        fpwd = os.getcwd()
        os.chdir(self.RootDir)
        # Check if the folder exists.
        if not os.path.join(fldb):
            os.mkdir(flds, 0027)
        # Check if the folder exists.
        if not os.path.isdir(frun):
            os.chdir(fpwd)
            return
        # Go to the folder.
        os.chdir(frun)
        # Determine minimum number of iterations required.
        nAvg = self.opts.get_nStats()
        nMin = self.opts.get_nMin()
        # Get the number of iterations
        ftriq, nStats, n0, nIter = lineLoad.GetTriqFile()
        # Process whether or not to update.
        if (not nIter) or (nIter < nMin + nStats):
            # Not enough iterations (or zero iterations)
            print("  Not enough iterations (%s) for analysis." % nIter)
            q = False
        elif np.isnan(j):
            # No current entry.
            print("  Adding new databook entry at iteration %i." % nIter)
            q = True
        elif DBL['nIter'][j] < nIter:
            # Update
            print("  Updating from iteration %i to %i."
                % (self[c0]['nIter'][j], nIter))
            q = True
        elif DBL['nStats'][j] < nStats:
            # Change statistics
            print("  Recomputing statistics using %i iterations." % nStats)
            q = True
        else:
            # Up-to-date
            print("  Databook up to date.")
            q = False
        # Check for an update
        if (not q): return
        # Read the new line load
        LL = lineLoad.CaseLL(self.cart3d, i, comp)
        # Calculate it.
        LL.CalculateLineLoads()
        # Check if the seam cut file exists.
        if not os.path.isfile(fsmy):
            # Collect seam cuts.
            q_seam = True
            # Read the seam curves.
            LL.ReadSeamCurves()
        else:
            # Seam cuts already present.
            q_seam = False
        # Save the data.
        if np.isnan(j):
            # Add the the number of cases.
            DBL.n += 1
            # Append trajectory values.
            for k in self.x.keys:
                # I found a better way to append in NumPy.
                DBL[k] = np.append(DBL[k], getattr(self.cart3d.x,k)[i])
            # Save parameters.
            DBL['Mach'] = np.append(DBL['Mach'], LL.Mach)
            DBL['Re']   = np.append(DBL['Re'],   LL.Re)
            DBL['XMRP'] = np.append(DBL['XMRP'], LL.MRP[0])
            DBL['YMRP'] = np.append(DBL['YMRP'], LL.MRP[1])
            DBL['ZMRP'] = np.append(DBL['ZMRP'], LL.MRP[2])
            # Append iteration counts.
            DBL['nIter']  = np.append(DBL['nIter'],  nIter)
            DBL['nStats'] = np.append(DBL['nStats'], nStats)
        else:
            # No need to update trajectory values.
            # Update the other statistics.
            DBL['nIter'][j]   = nIter
            DBL['nStats'][j]  = nStats
        # Go into the databook folder
        os.chdir(self.cart3d.RootDir)
        os.chdir(fldb)
        # Lineloads file name
        flds = frun.replace(os.sep, '-')
        # Write the loads
        lineload.WriteLDS(flds)
        # Write the seam curves if appropriate
        if q_seam:
            # Write both
            lineLoad.WriteSeam(fsmy, LL.smy)
            lineLoad.WriteSeam(fsmz, LL.smz)
        # Go back.
        os.chdir(fpwd)
    
    # Update or add an entry.
    def UpdateCase(self, i):
        """Update or add a trajectory to a data book
        
        The history of a run directory is processed if either one of three
        criteria are met.
        
            1. The case is not already in the data book
            2. The most recent iteration is greater than the data book value
            3. The number of iterations used to create statistics has changed
        
        :Call:
            >>> DB.UpdateCase(i)
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *i*: :class:`int`
                Trajectory index
        :Versions:
            * 2014-12-22 ``@ddalle``: First version
        """
        # Get the first data book component.
        c0 = self.Components[0]
        # Try to find a match existing in the data book.
        j = self[c0].FindMatch(i)
        # Get the name of the folder.
        frun = self.x.GetFullFolderNames(i)
        # Status update.
        print(frun)
        # Go home.
        os.chdir(self.RootDir)
        # Check if the folder exists.
        if not os.path.isdir(frun):
            # Nothing to do.
            return
        # Go to the folder.
        os.chdir(frun)
        # Get the current iteration number.
        nIter = int(GetCurrentIter())
        # Get the number of iterations used for stats.
        nStats = self.opts.get_nStats()
        # Get the iteration at which statistics can begin.
        nMin = self.opts.get_nMin()
        # Process whether or not to update.
        if (not nIter) or (nIter < nMin + nStats):
            # Not enough iterations (or zero iterations)
            print("  Not enough iterations (%s) for analysis." % nIter)
            q = False
        elif np.isnan(j):
            # No current entry.
            print("  Adding new databook entry at iteration %i." % nIter)
            q = True
        elif self[c0]['nIter'][j] < nIter:
            # Update
            print("  Updating from iteration %i to %i."
                % (self[c0]['nIter'][j], nIter))
            q = True
        elif self[c0]['nStats'][j] < nStats:
            # Change statistics
            print("  Recomputing statistics using %i iterations." % nStats)
            q = True
        else:
            # Up-to-date
            print("  Databook up to date.")
            q = False
        # Check for an update
        if (not q): return
        # Read the history.
        A = Aero(self.Components)
        # Maximum number of iterations allowed.
        nMax = min(nIter-nMin, self.opts.get_nMaxStats())
        # Loop through components.
        for comp in self.Components:
            # Extract the component history and component databook.
            FM = A[comp]
            DC = self[comp]
            # Loop through the transformations.
            for topts in self.opts.get_DataBookTransformations(comp):
                # Apply the transformation.
                FM.TransformFM(topts, self.x, i)
                
            # Process the statistics.
            s = FM.GetStats(nStats, nMax)
            # Get the corresponding residual drop
            nOrders = A.Residual.GetNOrders(s['nStats'])
            
            # Save the data.
            if np.isnan(j):
                # Add the the number of cases.
                DC.n += 1
                # Append trajectory values.
                for k in self.x.keys:
                    # I hate the way NumPy does appending.
                    DC[k] = np.hstack((DC[k], [getattr(self.x,k)[i]]))
                # Append values.
                for c in DC.DataCols:
                    DC[c] = np.hstack((DC[c], [s[c]]))
                # Append residual drop.
                DC['nOrders'] = np.hstack((DC['nOrders'], [nOrders]))
                # Append iteration counts.
                DC['nIter']  = np.hstack((DC['nIter'], [nIter]))
                DC['nStats'] = np.hstack((DC['nStats'], [s['nStats']]))
            else:
                # No need to update trajectory values.
                # Update data values.
                for c in DC.DataCols:
                    DC[c][j] = s[c]
                # Update the other statistics.
                DC['nOrders'][j] = nOrders
                DC['nIter'][j]   = nIter
                DC['nStats'][j]  = s['nStats']
        # Go back.
        os.chdir(self.RootDir)
                    
    # Get target to use based on target name
    def GetTargetByName(self, targ):
        """Get a target handle by name of the target
        
        :Call:
            >>> DBT = DB.GetTargetByName(targ)
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *targ*: :class:`str`
                Name of target to find
        :Outputs:
            *DBT*: :class:`pyCart.dataBook.DBTarget`
                Instance of the pyCart data book target class
        :Versions:
            * 2015-06-04 ``@ddalle``: First version
        """
        # List of target names.
        targs = [DBT.Name for DBT in self.Targets]
        # Check for the target.
        if targ not in targs:
            # Target not found.
            raise ValueError("Target named '%s' not in data book." % targ)
        # Return the target handle.
        return self.Targets[targs.index(targ)]
    
    # Get index of target to use based on coefficient name
    def GetTargetIndex(self, ftarg):
        """Get the index of the target to use based on a name
        
        For example, if "UPWT/CAFC" will use the target "UPWT" and the column
        named "CAFC".  If there is no "/" character in the name, the first
        available target is used.
        
        :Call:
            >>> i, c = self.GetTargetIndex(ftarg)
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *ftarg*: :class:`str`
                Name of the target and column
        :Outputs:
            *i*: :class:`int`
                Index of the target to use
            *c*: :class:`str`
                Name of the column to use from that target
        :Versions:
            * 2014-12-22 ``@ddalle``: First version
        """
        # Check if there's a slash
        if "/" in ftarg:
            # List of target names.
            TNames = [DBT.Name for DBT in self.Targets]
            # Split.
            ctarg = ftarg.split("/")
            # Find the name,
            i = TNames.index(ctarg[0])
            # Column name
            c = ctarg[1]
        else:
            # Use the first target.
            i = 0
            c = ftarg
        # Output
        return i, c
        
    # Get lists of indices of matches
    def GetTargetMatches(self, ftarg, tol=0.0, tols={}):
        """Get vectors of indices matching targets
        
        :Call:
            >>> I, J = DB.GetTargetMatches(ftarg, tol=0.0, tols={})
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *ftarg*: :class:`str`
                Name of the target and column
            *tol*: :class:`float`
                Tolerance for matching all keys (``0.0`` enforces equality)
            *tols*: :class:`dict`
                Dictionary of specific tolerances for each key
        :Outputs:
            *I*: :class:`numpy.ndarray`
                Array of data book indices with matches
            *J*: :class:`numpy.ndarray`
                Array of target indices for each data book index
        :Versions:
            * 2015-08-30 ``@ddalle``: First version
        """
        # First component.
        DBC = self[self.Components[0]]
        # Initialize indices of targets *J*
        I = []
        J = []
        # Loop through cases.
        for i in np.arange(DBC.n):
            # Get the match.
            j = self.GetTargetMatch(i, ftarg, tol=tol, tols=tols)
            # Check it.
            if np.isnan(j): continue
            # Append it.
            I.append(i)
            J.append(j)
        # Convert to array.
        I = np.array(I)
        J = np.array(J)
        # Output
        return I, J
    
    # Get match for a single index
    def GetTargetMatch(self, i, ftarg, tol=0.0, tols={}):
        """Get index of a target match (if any) for one data book entry
        
        :Call:
            >>> j = DB.GetTargetMatch(i, ftarg, tol=0.0, tols={})
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *i*: :class:`int`
                Data book index
            *ftarg*: :class:`str`
                Name of the target and column
            *tol*: :class:`float`
                Tolerance for matching all keys (``0.0`` enforces equality)
            *tols*: :class:`dict`
                Dictionary of specific tolerances for each key
        :Outputs:
            *j*: :class:`int` or ``np.nan``
                Data book target index
        :Versions:
            * 2015-08-30 ``@ddalle``: First version
        """
        # Check inputs.
        if type(tols).__name__ not in ['dict']:
            raise IOError("Keyword argument *tols* to " +
                ":func:`GetTargetMatches` must be a :class:`dict`.") 
        # First component.
        DBC = self[self.Components[0]]
        # Get the target.
        DBT = self.GetTargetByName(ftarg)
        # Get trajectory keys.
        tkeys = DBT.topts.get_Trajectory()
        # Initialize constraints.
        cons = {}
        # Loop through trajectory keys
        for k in self.x.keys:
            # Get the column name.
            col = tkeys.get(k, k)
            # Continue if column not present.
            if col is None or col not in DBT: continue
            # Get the constraint
            cons[k] = tols.get(k, tol)
            # Set the key.
            tkeys.setdefault(k, col)
        # Initialize match indices
        m = np.arange(DBT.nCase)
        # Loop through tkeys
        for k in tkeys:
            # Get the trajectory key.
            tk = tkeys[k]
            # Make sure there's a key.
            if tk is None: continue
            # Check type.
            if self.x.defns[k]['Value'].startswith('float'):
                # Apply the constraint.
                m = np.intersect1d(m, np.where(
                    np.abs(DBC[k][i] - DBT[tk]) <= cons[k])[0])
            else:
                # Apply equality constraint.
                m = np.intersect1d(m, np.where(DBC[k][i]==DBT[tk])[0])
            # Check if empty; if so exit with no match.
            if len(m) == 0: return np.nan
        # Return the first match.
        return m[0]
    
    # Get match for a single index
    def GetDBMatch(self, h, ftarg, tol=0.0, tols={}):
        """Get index of a target match (if any) for one data book entry
        
        :Call:
            >>> i = DB.GetDBMatch(j, ftarg, tol=0.0, tols={})
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *j*: :class:`int` or ``np.nan``
                Data book target index
            *ftarg*: :class:`str`
                Name of the target and column
            *tol*: :class:`float`
                Tolerance for matching all keys (``0.0`` enforces equality)
            *tols*: :class:`dict`
                Dictionary of specific tolerances for each key
        :Outputs:
            *i*: :class:`int`
                Data book index
        :Versions:
            * 2015-08-30 ``@ddalle``: First version
        """
        # Check inputs.
        if type(tols).__name__ not in ['dict']:
            raise IOError("Keyword argument *tols* to " +
                ":func:`GetTargetMatches` must be a :class:`dict`.") 
        # First component.
        DBC = self[self.Components[0]]
        # Get the target.
        DBT = self.GetTargetByName(ftarg)
        # Get trajectory keys.
        tkeys = DBT.topts.get_Trajectory()
        # Initialize constraints.
        cons = {}
        # Loop through trajectory keys
        for k in self.x.keys:
            # Get the column name.
            col = tkeys.get(k, k)
            # Continue if column not present.
            if col is None or col not in DBT: continue
            # Get the constraint
            cons[k] = tols.get(k, tol)
            # Set the key.
            tkeys.setdefault(k, col)
        # Initialize match indices
        m = np.arange(DBC.n)
        # Loop through tkeys
        for k in tkeys:
            # Get the trajectory key.
            tk = tkeys[k]
            # Make sure there's a key.
            if tk is None: continue
            # Check type.
            if self.x.defns[k]['Value'].startswith('float'):
                # Apply the constraint.
                m = np.intersect1d(m, np.where(
                    np.abs(DBC[k] - DBT[tk][j]) <= cons[k])[0])
            else:
                # Apply equality constraint.
                m = np.intersect1d(m, np.where(DBC[k]==DBT[tk][j])[0])
            # Check if empty; if so exit with no match.
            if len(m) == 0: return np.nan
        # Return the first match.
        return m[0]
            
        
    # Plot a sweep of one or more coefficients
    def PlotCoeff(self, comp, coeff, I, **kw):
        """Plot a sweep of one coefficients over several cases
        
        :Call:
            >>> h = DB.PlotCoeff(comp, coeff, I, **kw)
        :Inputs:
            *DB*: :class:`pyCart.dataBook.DataBook`
                Instance of the pyCart data book class
            *comp*: :class:`str`
                Component whose coefficient is being plotted
            *coeff*: :class:`str`
                Coefficient being plotted
            *I*: :class:`numpy.ndarray` (:class:`int`)
                List of indexes of cases to include in sweep
        :Keyword Arguments:
            *x*: [ {None} | :class:`str` ]
                Trajectory key for *x* axis (or plot against index if ``None``)
            *Label*: [ {*comp*} | :class:`str` ]
                Manually specified label
            *Legend*: [ {True} | False ]
                Whether or not to use a legend
            *StDev*: [ {None} | :class:`float` ]
                Multiple of iterative history standard deviation to plot
            *MinMax*: [ {False} | True ]
                Whether to plot minimum and maximum over iterative history
            *LineOptionss*: :class:`dict`
                Plot options for the primary line(s)
            *StDevOptions*: :class:`dict`
                Dictionary of plot options for the standard deviation plot
            *MinMaxOptions*: :class:`dict`
                Dictionary of plot options for the min/max plot
            *FigWidth*: :class:`float`
                Width of figure in inches
            *FigHeight*: :class:`float`
                Height of figure in inches
        :Outputs:
            *h*: :class:`dict`
                Dictionary of plot handles
        :Versions:
            * 2015-05-30 ``@ddalle``: First version
        """
        # Make sure the plotting modules are present.
        ImportPyPlot()
        # Extract the component.
        DBc = self[comp]
        # Get horizontal key.
        xk = kw.get('x')
        # Figure dimensions
        fw = kw.get('FigWidth', 6)
        fh = kw.get('FigHeight', 4.5)
        # Iterative uncertainty options
        qmmx = kw.get('MinMax', 0)
        ksig = kw.get('StDev')
        # Initialize output
        h = {}
        # Extract the values for the x-axis.
        if xk is None or xk == 'Index':
            # Use the indices as the x-axis
            xv = I
            # Label
            xk = 'Index'
        else:
            # Extract the values.
            xv = DBc[xk][I]
        # Extract the mean values.
        yv = DBc[coeff][I]
        # Initialize label.
        lbl = kw.get('Label', comp)
        # -----------------------
        # Standard Deviation Plot
        # -----------------------
        # Initialize plot options for standard deviation
        kw_s = odict(color='b', lw=0.0,
            facecolor='b', alpha=0.35, zorder=1)
        # Show iterative standard deviation.
        if ksig:
            # Add standard deviation to label.
            lbl = u'%s (\u00B1%s\u03C3)' % (lbl, ksig)
            # Extract plot options from keyword arguments.
            for k in util.denone(kw.get("StDevOptions")):
                # Option.
                o_k = kw["StDevOptions"][k]
                # Override the default option.
                if o_k is not None: kw_s[k] = o_k
            # Get the standard deviation value.
            sv = DBc[coeff+"_std"][I]
            # Plot it.
            h['std'] = plt.fill_between(xv, yv-ksig*sv, yv+ksig*sv, **kw_s)
        # ------------
        # Min/Max Plot
        # ------------
        # Initialize plot options for min/max
        kw_m = odict(color='g', lw=0.0,
            facecolor='g', alpha=0.35, zorder=2)
        # Show min/max options
        if qmmx:
            # Add min/max to label.
            lbl = u'%s (min/max)' % (lbl)
            # Extract plot options from keyword arguments.
            for k in util.denone(kw.get("MinMaxOptions")):
                # Option
                o_k = kw["MinMaxOptions"][k]
                # Override the default option.
                if o_k is not None: kw_m[k] = o_k
            # Get the min and max values.
            ymin = DBc[coeff+"_min"][I]
            ymax = DBc[coeff+"_max"][I]
            # Plot it.
            h['max'] = plt.fill_between(xv, ymin, ymax, **kw_m)
        # ------------
        # Primary Plot
        # ------------
        # Initialize plot options for primary plot
        kw_p = odict(color='k', marker='^', zorder=8, ls='-')
        # Plot options
        for k in util.denone(kw.get("LineOptions")):
            # Option
            o_k = kw["LineOptions"][k]
            # Override the default option.
            if o_k is not None: kw_p[k] = o_k
        # Label
        kw_p.setdefault('label', lbl)
        # Plot it.
        h['line'] = plt.plot(xv, yv, **kw_p)
        # ----------
        # Formatting
        # ----------
        # Get the figure and axes.
        h['fig'] = plt.gcf()
        h['ax'] = plt.gca()
        # Check for an existing ylabel
        ly = h['ax'].get_ylabel()
        # Compare to requested ylabel
        if ly and ly != coeff:
            # Combine labels.
            ly = ly + '/' + coeff
        else:
            # Use the coefficient.
            ly = coeff
        # Labels.
        h['x'] = plt.xlabel(xk)
        h['y'] = plt.ylabel(ly)
        # Get limits that include all data (and not extra).
        xmin, xmax = get_xlim(h['ax'], pad=0.05)
        ymin, ymax = get_ylim(h['ax'], pad=0.05)
        # Make sure data is included.
        h['ax'].set_xlim(xmin, xmax)
        h['ax'].set_ylim(ymin, ymax)
        # Legend.
        if kw.get('Legend', True):
            # Get current limits.
            ymin, ymax = get_ylim(h['ax'], pad=0.05)
            # Add extra room for the legend.
            h['ax'].set_ylim((ymin, 1.2*ymax-0.2*ymin))
            # Font size checks.
            if len(h['ax'].get_lines()) > 5:
                # Very small
                fsize = 7
            else:
                # Just small
                fsize = 9
            # Activate the legend.
            try:
                # Use a font that has the proper symbols.
                h['legend'] = h['ax'].legend(loc='upper center',
                    prop=dict(size=fsize, family="DejaVu Sans"),
                    bbox_to_anchor=(0.5,1.05), labelspacing=0.5)
            except Exception:
                # Default font.
                h['legend'] = h['ax'].legend(loc='upper center',
                    prop=dict(size=fsize),
                    bbox_to_anchor=(0.5,1.05), labelspacing=0.5)
        # Figure dimensions.
        if fh: h['fig'].set_figheight(fh)
        if fw: h['fig'].set_figwidth(fw)
        # Attempt to apply tight axes.
        try: plt.tight_layout()
        except Exception: pass
        # Output
        return h
# class DataBook
        
            
# Function to automatically get inclusive data limits.
def get_ylim(ha, pad=0.05):
    """Calculate appropriate *y*-limits to include all lines in a plot
    
    Plotted objects in the classes :class:`matplotlib.lines.Lines2D` and
    :class:`matplotlib.collections.PolyCollection` are checked.
    
    :Call:
        >>> ymin, ymax = get_ylim(ha, pad=0.05)
    :Inputs:
        *ha*: :class:`matplotlib.axes.AxesSubplot`
            Axis handle
        *pad*: :class:`float`
            Extra padding to min and max values to plot.
    :Outputs:
        *ymin*: :class:`float`
            Minimum *y* coordinate including padding
        *ymax*: :class:`float`
            Maximum *y* coordinate including padding
    :Versions:
        * 2015-07-06 ``@ddalle``: First version
    """
    return cape.get_ylim(ha, pad=pad)
    
# Function to automatically get inclusive data limits.
def get_xlim(ha, pad=0.05):
    """Calculate appropriate *x*-limits to include all lines in a plot
    
    Plotted objects in the classes :class:`matplotlib.lines.Lines2D` are
    checked.
    
    :Call:
        >>> xmin, xmax = get_xlim(ha, pad=0.05)
    :Inputs:
        *ha*: :class:`matplotlib.axes.AxesSubplot`
            Axis handle
        *pad*: :class:`float`
            Extra padding to min and max values to plot.
    :Outputs:
        *xmin*: :class:`float`
            Minimum *x* coordinate including padding
        *xmax*: :class:`float`
            Maximum *x* coordinate including padding
    :Versions:
        * 2015-07-06 ``@ddalle``: First version
    """
    return cape.get_xlim(ha, pad=pad)
# DataBook Plot functions

                
# Individual component data book
class DBComp(cape.dataBook.DBComp):
    """
    Individual component data book
    
    :Call:
        >>> DBi = DBComp(comp, x, opts)
    :Inputs:
        *comp*: :class:`str`
            Name of the component
        *x*: :class:`pyCart.trajectory.Trajectory`
            Trajectory for processing variable types
        *opts*: :class:`pyCart.options.Options`
            Global pyCart options instance
    :Outputs:
        *DBi*: :class:`pyCart.dataBook.DBComp`
            An individual component data book
    :Versions:
        * 2014-12-20 ``@ddalle``: Started
    """
        
    pass
# class DBComp
        
        
# Data book target instance
class DBTarget(cape.dataBook.DBTarget):
    """
    Class to handle data from data book target files.  There are more
    constraints on target files than the files that data book creates, and raw
    data books created by pyCart are not valid target files.
    
    :Call:
        >>> DBT = pyCart.dataBook.DBTarget(targ, x, opts)
    :Inputs:
        *targ*: :class:`pyCart.options.DataBook.DBTarget`
            Instance of a target source options interface
        *x*: :class:`pyCart.trajectory.Trajectory`
            Run matrix interface
        *opts*: :class:`pyCart.options.Options`
            Global pyCart options instance to determine which fields are useful
    :Outputs:
        *DBT*: :class:`pyCart.dataBook.DBTarget`
            Instance of the pyCart data book target data carrier
    :Versions:
        * 2014-12-20 ``@ddalle``: Started
    """
    
    pass
# class DBTarget
        
        
# Aerodynamic history class
class Aero(dict):
    """
    This class provides an interface to important data from a run directory.  It
    reads force and moment histories for named components, if available, and
    other types of data can also be stored
    
    :Call:
        >>> aero = pyCart.dataBook.Aero(comps=[])
    :Inputs:
        *comps*: :class:`list` (:class:`str`)
            List of components to read; defaults to all components available
    :Outputs:
        *aero*: :class:`pyCart.aero.Aero`
            Instance of the aero history class, similar to dictionary of force
            and/or moment histories
    :Versions:
        * 2014-11-12 ``@ddalle``: Starter version
        * 2014-12-21 ``@ddalle``: Copied from previous `aero.Aero`
    """
    
    # Initialization method
    def __init__(self, comps=[]):
        """Initialization method
        
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Process the best data folder.
        fdir = GetWorkingFolder()
        # Read the loadsCC.dat file to see what components are requested.
        self.ReadLoadsCC()
        # Read the residuals.
        self.Residual = CaseResid()
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
            self[comp] = CaseFM(d['C'], MRP=d['MRP'], A=A)
            
    # Function to calculate statistics and select ideal nStats
    def GetStats(self, nStats=0, nMax=0, nLast=None):
        """
        Get statistics for all components and decide how many iterations to use
        for calculating statistics.
        
        The number of iterations to use is selected such that the sum of squares
        of all errors (all coefficients of each component) is minimized.  Only
        *nStats*, *nMax*, and integer multiples of *nStats* are considered as
        candidates for the number of iterations to use.
        
        :Call:
            >>> S = A.GetStats(nStats, nMax=0, nLast=None)
        :Inputs:
            *nStats*: :class:`int`
                Nominal number of iterations to use in statistics
            *nMax*: :class:`int`
                Maximum number of iterations to use for statistics
            *nLast*: :class:`int`
                Specific iteration at which to get statistics
        :Outputs:
            *S*: :class:`dict` (:class:`dict` (:class:`float`))
                Dictionary of statistics for each component
        :See also:
            :func:`pyCart.dataBook.CaseFM.GetStats`
        :Versions:
            * 2015-02-28 ``@ddalle``: First version
        """
        # Initialize statistics for this count.
        S = {}
        # Loop through components.
        for comp in self:
            # Get the statistics.
            S[comp] = self[comp].GetStats(nStats, nMax=nMax, nLast=nLast)
        # Output
        return S
    
    # Function to read 'loadsCC.dat'
    def ReadLoadsCC(self):
        """Read forces and moments from a :file:`loadsCC.dat` file if possible
        
        :Call:
            >> A.ReadLoadsCC()
        :Inputs:
            *A*: :class:`pyCart.aero.Aero`
                Instance of the aero history class
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Initialize list of components.
        self.Components = {}
        # Get working directory.
        fdir = GetWorkingFolder()
        # Path to the file.
        fCC = os.path.join(fdir, 'loadsCC.dat')
        # Check for the file.
        if not os.path.isfile(fCC):
            # Change the loadsTRI.dat
            fCC = os.path.join(fdir, 'loadsTRI.dat')
        # Try again.
        if not os.path.isfile(fCC):
            # Change to common directory.
            fCC = os.path.join('..', '..', 'inputs', 'loadsCC.dat')
        # Check for the last time.
        if not os.path.isfile(fCC):
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
                txt = re.search('\(([0-9EeDd., +-]+)\)', line).group(1)
                # Split into coordinates.
                MRP = np.array([float(v) for v in txt.split(',')])
                # Save it.
                self.Components[comp]['MRP'] = MRP
            except Exception:
                # Failed to find expected text.
                print("Warning: no reference point in line:\n  '%s'" % line)
                # Function to plot a single coefficient.
    
    # Plot coefficient iterative history
    def PlotCoeff(self, comp, c, n=None, nAvg=100, d=0.01, **kw):
        """Plot a single coefficient history
        
        :Call:
            >>> h = A.PlotCoeff(comp, c, n=1000, nAvg=100, **kw)
        :Inputs:
            *A*: :class:`pyCart.dataBook.Aero`
                Instance of the force history class
            *comp*: :class:`str`
                Name of component to plot
            *c*: :class:`str`
                Name of coefficient to plot, e.g. ``'CA'``
            *n*: :class:`int`
                Only show the last *n* iterations
            *nAvg*: :class:`int`
                Use the last *nAvg* iterations to compute an average
            *d*: :class:`float`
                Delta in the coefficient to show expected range
            *nLast*: :class:`int`
                Last iteration to use (defaults to last iteration available)
            *nFirst*: :class:`int`
                First iteration to plot
        :Outputs:
            *h*: :class:`dict`
                Dictionary of figure/plot handles
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
            * 2014-12-09 ``@ddalle``: Transferred to :class:`AeroPlot`
            * 2015-02-15 ``@ddalle``: Transferred to :class:`dataBook.Aero`
            * 2015-03-04 ``@ddalle``: Added *nStart* and *nLast*
        """
        # Extract the component.
        FM = self[comp]
        # Create the plot.
        h = FM.PlotCoeff(c, n=n, nAvg=nAvg, d=d, **kw)
        # Output.
        return h
    
    # Plot coefficient histogram
    def PlotCoeffHist(self, comp, c, nAvg=100, nBin=20, nLast=None, **kw):
        """Plot a single coefficient histogram
        
        :Call:
            >>> h = A.PlotCoeffHist(comp, c, n=1000, nAvg=100, **kw)
        :Inputs:
            *A*: :class:`pyCart.dataBook.Aero`
                Instance of the force history class
            *comp*: :class:`str`
                Name of component to plot
            *c*: :class:`str`
                Name of coefficient to plot, e.g. ``'CA'``
            *nAvg*: :class:`int`
                Use the last *nAvg* iterations to compute an average
            *nBin*: :class:`int`
                Number of bins to plot
            *nLast*: :class:`int`
                Last iteration to use (defaults to last iteration available)
            *FigWidth*: :class:`float`
                Figure width
            *FigHeight*: :class:`float`
                Figure height
        :Outputs:
            *h*: :class:`dict`
                Dictionary of figure/plot handles
        :Versions:
            * 2015-02-15 ``@ddalle``: First version
            * 2015-03-06 ``@ddalle``: Added *nLast* and fixed documentation
        """
        # Extract the component.
        FM = self[comp]
        # Create the plot.
        h = FM.PlotCoeffHist(c, nAvg=nAvg, nBin=nBin, nLast=nLast, **kw)
        # Output.
        return h
        
        
    # Plot function
    def PlotL1(self, n=None, nFirst=None, nLast=None, **kw):
        """Plot the L1 residual
        
        :Call:
            >>> h = A.PlotL1(n=None, nFirst=None, nLast=None)
        :Inputs:
            *A*: :class:`pyCart.dataBook.Aero`
                Instance of the force history class
            *n*: :class:`int`
                Only show the last *n* iterations
            *nFirst*: :class:`int`
                Plot starting at iteration *nStart*
            *nLast*: :class:`int`
                Plot up to iteration *nLast*
        :Outputs:
            *h*: :class:`dict`
                Dictionary of figure/plot handles
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
            * 2014-12-09 ``@ddalle``: Moved to :class:`AeroPlot`
            * 2015-02-15 ``@ddalle``: Transferred to :class:`dataBook.Aero`
            * 2015-03-04 ``@ddalle``: Added *nStart* and *nLast*
        """
        # Make sure plotting modules are present.
        ImportPyPlot()
        # Create the plot.
        h = self.Residual.PlotL1(n=n, nFirst=nFirst, nLast=nLast, **kw)
        # Output.
        return h
            
    # Function to plot several coefficients.
    def Plot(self, comp, C, d={}, **kw):
        """Plot one or several component histories
        
        :Call:
            >>> h = AP.Plot(comp, C, d={}, n=1000, nAvg=100, **kw)
        :Inputs:
            *AP*: :class:`pyCart.aero.Plot`
                Instance of the force history plotting class
            *comp*: :class:`str`
                Name of component to plot
            *nRow*: :class:`int`
                Number of rows of subplots to make
            *nCol*: :class:`int`
                Number of columns of subplots to make
            *C*: :class:`list` (:class:`str`)
                List of coefficients or ``'L1'`` to plot
            *n*: :class:`int`
                Only show the last *n* iterations
            *nFirst*: :class:`int`
                First iteration to plot
            *nLast*: :class:`int`
                Last iteration to plot
            *nAvg*: :class:`int`
                Use the last *nAvg* iterations to compute an average
            *d0*: :class:`float`
                Default delta to use
            *d*: :class:`dict`
                Dictionary of deltas for each component
            *tag*: :class:`str` 
                Tag to put in upper corner, for instance case number and name
            *restriction*: :class:`str`
                Type of data, e.g. ``"SBU - ITAR"`` or ``"U/FOUO"``
            *FigWidth*: :class:`float`
                Figure width
            *FigHeight*: :class:`float`
                Figure height
        :Outputs:
            *h*: :class:`dict`
                Dictionary of figure/plot handles
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
            * 2014-12-09 ``@ddalle``: Moved to :class:`AeroPlot`
            * 2015-02-15 ``@ddalle``: Transferred to :class:`dataBook.Aero`
            * 2015-03-04 ``@ddalle``: Added *nFirst* and *nLast*
        """
        # Make sure plotting modules are present.
        ImportPyPlot()
        # Read inputs
        nRow = kw.get('nRow', 2)
        nCol = kw.get('nCol', 2)
        n    = kw.get('n', 1000)
        nAvg = kw.get('nAvg', 100)
        nBin = kw.get('nBin', 20)
        d0   = kw.get('d0', 0.01)
        # Window control
        nFirst = kw.get('nFirst')
        nLast  = kw.get('nLast')
        # Check for single input.
        if type(C).__name__ == "str": C = [C]
        # Number of components
        nC = len(C)
        # Check inputs.
        if nC > nRow*nCol:
            raise IOError("Too many components for %i rows and %i columns" 
                % (nRow, nCol))
        # Initialize handles.
        h = CasePlot()
        # Loop through components.
        for i in range(nC):
            # Get coefficient.
            c = C[i]
            # Pull up the subplot.
            plt.subplot(nRow, nCol, i+1)
            # Check if residual was requested.
            if c == 'L1':
                # Plot it.
                h[c] = self.PlotL1(n=n, nFirst=nFirst, nLast=nLast)
            elif c.endswith('hist'):
                # Get the coeff name.
                ci = c[:-4]
                # Plot histogram
                h[c] = self.PlotCoeffHist(comp, ci, nAvg=nAvg, nBin=nBin, 
                    nLast=nLast)
            else:
                # Get the delta
                di = d.get(c, d0)
                # Plot
                h[c] = self.PlotCoeff(comp, c, n=n, nAvg=nAvg, d=di,
                    nFirst=nFirst, nLast=nLast)
            # Turn off overlapping xlabels for condensed plots.
            if (nCol==1 or nRow>2) and (i+nCol<nC):
                # Kill the xlabel and xticklabels.
                h[c]['ax'].set_xticklabels(())
                h[c]['ax'].set_xlabel('')
        # Max of number 
        n0 = max(nCol, nRow)
        # Determine target font size.
        if n0 == 1:
            # Font size (default)
            fsize = 12
        elif n0 == 2:
            # Smaller
            fsize = 9
        else:
            # Really small
            fsize = 8
        # Loop through the text labels.
        for h_t in plt.gcf().findobj(Text):
            # Apply the target font size.
            h_t.set_fontsize(fsize)
        # Add tag.
        tag = kw.get('tag', '')
        h['tag'] = plt.figtext(0.015, 0.985, tag, verticalalignment='top')
        # Add restriction.
        txt = kw.get('restriction', '')
        h['restriction'] = plt.figtext(0.5, 0.01, txt,
            horizontalalignment='center')
        # Add PASS label (empty but handle is useful)
        h['pass'] = plt.figtext(0.99, 0.97, "", color="#00E500",
            horizontalalignment='right')
        # Add iteration label
        h['iter'] = plt.figtext(0.99, 0.94, "%i/" % self[comp].i[-1],
            horizontalalignment='right', size=9)
        # Attempt to use the tight_layout() utility.
        try:
            # Add room for labels with *rect*, and tighten up other margins.
            plt.gcf().tight_layout(pad=0.2, w_pad=0.5, h_pad=0.7,
                rect=(0.01,0.015,0.99,0.91))
        except Exception:
            pass
        # Save the figure.
        h['fig'] = plt.gcf()
        # Output
        return h
        
    # Function to add plot restriction label
    
            
    # Function to plot force coeffs and residual (resid is only a blank)
    def Plot4(self, comp, **kw):
        """Initialize a plot for three force coefficients and L1 residual
        
        :Call:
            >>> h = AP.Plot4(comp, **kw)
        :Inputs:
            *AP*: :class:`pyCart.aero.Plot`
                Instance of the force history plotting class
            *comp*: :class:`str`
                Name of component to plot
            *n*: :class:`int`
                Only show the last *n* iterations
            *nAvg*: :class:`int`
                Use the last *nAvg* iterations to compute an average
            *d0*: :class:`float`
                Default delta to use
            *kw*: :class:`dict`
                Keyword arguments passed to :func:`pyCart.aero.Aero.plot`
        :Outputs:
            *h*: :class:`dict`
                Dictionary of figure/plot handles
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Plot the forces and residual.
        h = self.Plot(comp, ['CA', 'CY', 'CN', 'L1'], nRow=2, nCol=2, **kw)
        # Output
        return h
        
    # Function to plot force coefficients only
    def PlotForce(self, comp, **kw):
        """Initialize a plot for three force coefficients
        
        :Call:
            >>> h = AP.PlotForce(comp, **kw)
        :Inputs:
            *AP*: :class:`pyCart.aero.Plot`
                Instance of the force history plotting class
            *comp*: :class:`str`
                Name of component to plot
            *n*: :class:`int`
                Only show the last *n* iterations
            *nAvg*: :class:`int`
                Use the last *nAvg* iterations to compute an average
            *d0*: :class:`float`
                Default delta to use
            *kw*: :class:`dict`
                Keyword arguments passed to :func:`pyCart.aero.Aero.plot`
        :Outputs:
            *h*: :class:`dict`
                Dictionary of figure/plot handles
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Plot the forces, but leave a spot for residual.
        h = self.Plot(comp, ['CA', 'CY', 'CN'], nRow=3, nCol=1, **kw)
        # Output
        return h
# class Aero
    
    
# Individual component force and moment
class CaseFM(object):
    """
    This class contains methods for reading data about an the histroy of an
    individual component for a single case.  The list of available components
    comes from a :file:`loadsCC.dat` file if one exists.
    
    :Call:
        >>> FM = pyCart.dataBook.CaseFM(C, MRP=None, A=None)
    :Inputs:
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
        * 2014-12-21 ``@ddalle``: Copied from previous `aero.FM`
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
        
            * ``'<dataBook.CaseFM Force, i=100>'``
            * ``'<dataBook.CaseFM Moment, i=100, MRP=(0.00, 1.00, 2.00)>'``
            * ``'<dataBook.CaseFM FM, i=100, MRP=(0.00, 1.00, 2.00)>'``
        
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
        """
        # Initialize the string.
        txt = '<dataBook.CaseFM '
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
        
            * ``'<dataBook.CaseFM Force, i=100>'``
            * ``'<dataBook.CaseFM Moment, i=100, MRP=(0.00, 1.00, 2.00)>'``
            * ``'<dataBook.CaseFM FM, i=100, MRP=(0.00, 1.00, 2.00)>'``
        
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
            *FM*: :class:`pyCart.dataBook.CaseFM`
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
            # Save list of coefficients.
            self.coeffs = ['CA', 'CY', 'CN', 'CLL', 'CLM', 'CLN']
        elif (self.MRP.size==3) and (m == 4):
            # Save only moments.
            self.CLL = A[:,1]
            self.CLM = A[:,2]
            self.CLN = A[:,3]
            # Save list of coefficients.
            self.coeffs = ['CLL', 'CLM', 'CLN']
        elif (m == 4):
            # Save only forces.
            self.CA = A[:,1]
            self.CY = A[:,2]
            self.CN = A[:,3]
            # Save list of coefficients.
            self.coeffs = ['CA', 'CY', 'CN']
        
    # Transform force or moment reference frame
    def TransformFM(self, topts, x, i):
        """Transform a force and moment history
        
        Available transformations and their required parameters are listed
        below.
        
            * "Euler321": "psi", "theta", "phi"
            
        Trajectory variables are used to specify values to use for the
        transformation variables.  For example,
        
            .. code-block:: python
            
                topts = {"Type": "Euler321",
                    "psi": "Psi", "theta": "Theta", "phi": "Phi"}
        
        will cause this function to perform a reverse Euler 3-2-1 transformation
        using *x.Psi[i]*, *x.Theta[i]*, and *x.Phi[i]* as the angles.
        
        :Call:
            >>> FM.TransformFM(topts, x, i)
        :Inputs:
            *FM*: :class:`pyCart.dataBook.CaseFM`
                Instance of the force and moment class
            *topts*: :class:`dict`
                Dictionary of options for the transformation
            *x*: :class:`pyCart.trajectory.Trajectory`
                The run matrix used for this analysis
            *i*: :class:`int`
                The index of the case to transform in the current run matrix
        :Versions:
            * 2014-12-22 ``@ddalle``: First version
        """
        # Get the transformation type.
        ttype = topts.get("Type", "")
        # Check it.
        if ttype in ["Euler321"]:
            # Get the angle variable names.
            # Use same as default in case it's obvious what they should be.
            kph = topts.get('phi', 'phi')
            kth = topts.get('theta', 'theta')
            kps = topts.get('psi', 'psi')
            # Extract roll
            if kph.startswith('-'):
                # Negative roll angle.
                phi = -getattr(x,kph[1:])[i]*deg
            else:
                # Positive roll
                phi = getattr(x,kph)[i]*deg
            # Extract pitch
            if kth.startswith('-'):
                # Negative pitch
                theta = -getattr(x,kth[1:])[i]*deg
            else:
                # Positive pitch
                theta = getattr(x,kth)[i]*deg
            # Extract yaw
            if kps.startswith('-'):
                # Negative yaw
                psi = -getattr(x,kps[1:])[i]*deg
            else:
                # Positive pitch
                psi = getattr(x,kps)[i]*deg
            # Sines and cosines
            cph = np.cos(phi); cth = np.cos(theta); cps = np.cos(psi)
            sph = np.sin(phi); sth = np.sin(theta); sps = np.sin(psi)
            # Make the matrices.
            # Roll matrix
            R1 = np.array([[1, 0, 0], [0, cph, -sph], [0, sph, cph]])
            # Pitch matrix
            R2 = np.array([[cth, 0, -sth], [0, 1, 0], [sth, 0, cth]])
            # Yaw matrix
            R3 = np.array([[cps, -sps, 0], [sps, cps, 0], [0, 0, 1]])
            # Combined transformation matrix.
            # Remember, these are applied backwards in order to undo the
            # original Euler transformation that got the component here.
            R = np.dot(R1, np.dot(R2, R3))
            # Force transformations
            if 'CY' in self.coeffs:
                # Assemble forces.
                Fc = np.vstack((self.CA, self.CY, self.CN))
                # Transform.
                Fb = np.dot(R, Fc)
                # Extract (is this necessary?)
                self.CA = Fb[0]
                self.CY = Fb[1]
                self.CN = Fb[2]
            elif 'CN' in self.coeffs:
                # Use zeros for side force.
                CY = np.zeros_like(self.CN)
                # Assemble forces.
                Fc = np.vstack((self.CA, CY, self.CN))
                # Transform.
                Fb = np.dot(R, Fc)
                # Extract
                self.CA = Fb[0]
                self.CN = Fb[2]
            # Moment transformations
            if 'CLN' in self.coeffs:
                # Assemble moment vector.
                Mc = np.vstack((self.CLL, self.CLM, self.CLN))
                # Transform.
                Mb = np.dot(R, Mc)
                # Extract.
                self.CLL = Mb[0]
                self.CLM = Mb[1]
                self.CLN = Mb[2]
            elif 'CLM' in self.coeffs:
                # Use zeros for roll and yaw moment.
                CLL = np.zeros_like(self.CLM)
                CLN = np.zeros_like(self.CLN)
                # Assemble moment vector.
                Mc = np.vstack((CLL, self.CLM, CLN))
                # Transform.
                Mb = np.dot(R, Mc)
                # Extract.
                self.CLM = Mb[1]
                
        elif ttype in ["ScaleCoeffs"]:
            # Loop through coefficients.
            for c in topts:
                # Check if it's an available coefficient.
                if c not in self.coeffs: continue
                # Get the value.
                k = topts[c]
                # Check if it's a number.
                if type(k).__name__ not in ["float", "int"]:
                    # Assume they meant to flip it.
                    k = -1.0
                # Scale.
                setattr(self,c, k*getattr(self,c))
            
        else:
            raise IOError(
                "Transformation type '%s' is not recognized." % ttype)
        
    # Method to shift the MRC
    def ShiftMRP(self, Lref, x, xi=None):
        """Shift the moment reference point
        
        :Call:
            >>> FM.ShiftMRP(Lref, x, xi=None)
        :Inputs:
            *FM*: :class:`pyCart.dataBook.CaseFM`
                Instance of the force and moment class
            *Lref*: :class:`float`
                Reference length
            *x*: :class:`list` (:class:`float`)
                Target moment reference point
            *xi*: :class:`list` (:class:`float`)
                Current moment reference point (default: *self.MRP*)
        :Versions:
            * 2015-03-02 ``@ddalle``: First version
        """
        # Check for moments.
        if ('CA' not in self.coeffs) or ('CLM' not in self.coeffs):
            # Not a force/moment history
            return
        # Rolling moment: side force
        if ('CLL' in self.coeffs) and ('CY' in self.coeffs):
            self.CLL -= (xi[2]-x[2])/Lref*self.CY
        # Rolling moment: normal force
        if ('CLL' in self.coeffs) and ('CN' in self.coeffs):
            self.CLL += (xi[1]-x[1])/Lref*self.CN
        # Pitching moment: normal force
        if ('CLM' in self.coeffs) and ('CN' in self.coeffs):
            self.CLM -= (xi[0]-x[0])/Lref*self.CN
        # Pitching moment: axial force
        if ('CLM' in self.coeffs) and ('CA' in self.coeffs):
            self.CLM += (xi[2]-x[2])/Lref*self.CA
        # Yawing moment: axial force
        if ('CLN' in self.coeffs) and ('CA' in self.coeffs):
            self.CLN += (x[1]-xi[1])/Lref*self.CA
        # Yawing moment: axial force
        if ('CLN' in self.coeffs) and ('CY' in self.coeffs):
            self.CLN += (x[0]-xi[0])/Lref*self.CY
            
    # Write a pure file.
    def Write(self, fname):
        """Write contents to force/moment file
        
        :Call:
            >>> FM.Write(fname)
        :Inputs:
            *FM*: :class:`pyCart.dataBook.CaseFM`
                Instance of the force and moment class
            *fname*: :class:`str`
                Name of file to write.
        :Versions:
            * 2015-03-02 ``@ddalle``: First version
        """
        # Open the file for writing.
        f = open(fname, 'w')
        # Start the header.
        f.write('# cycle')
        # Check for basic force coefficients.
        if 'CA' in self.coeffs:
            f.write(' Fx Fy')
        # Check for side force.
        if 'CY' in self.coeffs:
            f.write(' Fz')
        # Check for 3D moments.
        if 'CLN' in self.coeffs:
            # 3D moments
            f.write(' CLL CLM CLN')
        elif 'CLM' in self.coeffs:
            # 2D, only pitching moment
            f.write(' CLM')
        # End the header.
        f.write('\n')
        # Initialize the data.
        A = np.array([self.i])
        # Loop through coefficients.
        for c in self.coeffs:
            # Append the data.
            A = np.vstack((A, [getattr(self,c)]))
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
        
        
    # Function to get index of a certain iteration number
    def GetIterationIndex(self, i):
        """Return index of a particular iteration in *FM.i*
        
        If the iteration *i* is not present in the history, the index of the
        last available iteration less than or equal to *i* is returned.
        
        :Call:
            >>> j = FM.GetIterationIndex(i)
        :Inputs:
            *FM*: :class:`pyCart.dataBook.CaseFM`
                Instance of the force and moment class
            *i*: :class:`int`
                Iteration number
        :Outputs:
            *j*: :class:`int`
                Index of last iteration in *FM.i* less than or equal to *i*
        :Versions:
            * 2015-03-06 ``@ddalle``: First version
        """
        # Check for *i* less than first iteration.
        if i < self.i[0]: return 0
        # Find the index.
        j = np.where(self.i <= i)[0][-1]
        # Output
        return j
        
        
    # Method to get averages and standard deviations
    def GetStatsN(self, nStats=100, nLast=None):
        """Get mean, min, max, and standard deviation for all coefficients
        
        :Call:
            >>> s = FM.GetStatsN(nStats, nFirst=None, nLast=None)
        :Inputs:
            *FM*: :class:`pyCart.dataBook.CaseFM`
                Instance of the force and moment class
            *nStats*: :class:`int`
                Number of iterations in window to use for statistics
            *nLast*: :class:`int`
                Last iteration to use for statistics
        :Outputs:
            *s*: :class:`dict` (:class:`float`)
                Dictionary of mean, min, max, std for each coefficient
        :Versions:
            * 2014-12-09 ``@ddalle``: First version
            * 2015-02-28 ``@ddalle``: Renamed from :func:`GetStats`
            * 2015-03-04 ``@ddalle``: Added last iteration capability
        """
        # Last iteration to use.
        if nLast:
            # Attempt to use requested iter.
            if nLast < self.i.size:
                # Using an earlier iter; make sure to use one in the hist.
                jLast = self.GetIterationIndex(nLast)
                # Find the iterations that are less than i.
                iLast = self.i[jLast]
            else:
                # Use the last iteration.
                iLast = self.i.size
        else:
            # Just use the last iteration
            iLast = self.i.size
        # Default values.
        if (nStats is None) or (nStats < 2):
            # Use last iteration
            i0 = iLast - 1
        else:
           # Process min indices for plotting and averaging.
            i0 = max(0, iLast-nStats)
        # Initialize output.
        s = {}
        # Loop through coefficients.
        for c in self.coeffs:
            # Get the values
            F = getattr(self, c)
            # Save the mean value.
            s[c] = np.mean(F[i0:])
            # Check for statistics.
            if (nStats is not None) or (nStats < 2):
                # Save the statistics.
                s[c+'_min'] = np.min(F[i0:iLast])
                s[c+'_max'] = np.max(F[i0:iLast])
                s[c+'_std'] = np.std(F[i0:iLast])
                s[c+'_err'] = util.SigmaMean(F[i0:iLast])
        # Output
        return s
            
    # Method to get averages and standard deviations
    def GetStats(self, nStats=100, nMax=None, nLast=None):
        """Get mean, min, max, and standard deviation for all coefficients
        
        :Call:
            >>> s = FM.GetStats(nStats, nMax=None, nLast=None)
        :Inputs:
            *FM*: :class:`pyCart.dataBook.CaseFM`
                Instance of the force and moment class
            *nStats*: :class:`int`
                Minimum number of iterations in window to use for statistics
            *nMax*: :class:`int`
                Maximum number of iterations to use for statistics
            *nLast*: :class:`int`
                Last iteration to use for statistics
        :Outputs:
            *s*: :class:`dict` (:class:`float`)
                Dictionary of mean, min, max, std for each coefficient
        :Versions:
            * 2015-02-28 ``@ddalle``: First version
            * 2015-03-04 ``@ddalle``: Added last iteration capability
        """
        # Make sure the number of iterations used is an integer.
        if not nStats: nStats = 1
        # Process list of candidate numbers of iterations for statistics.
        if nMax and (nStats > 1) and (nMax >= 1.5*nStats):
            # Nontrivial list of candidates
            # Multiples of *nStats*
            N = [k*nStats for k in range(1, int(nMax/nStats)+1)]
            # Check if *nMax* should also be considered.
            if nMax >= 1.5*N[-1]:
                # Add *nMax*
                N.append(nMax)
        else:
            # Only one candidate.
            N = [nStats]
        # Initialize error as infinity.
        e = np.inf;
        # Loop through list of candidate iteration counts
        for n in N:
            # Get the statistics.
            sn = self.GetStatsN(n, nLast=nLast)
            # Save the number of iterations used.
            sn['nStats'] = n
            # If there is only one candidate, return it.
            if len(N) == 1: return sn
            # Calculate the composite error.
            en = np.sqrt(np.sum([sn[c+'_err']**2 for c in self.coeffs]))
            # Calibrate to slightly favor less iterations
            en = en * (0.75 + 0.25*np.sqrt(n)/np.sqrt(N[0]))
            # Check if this error is an improvement.
            if en < e:
                # Select these statistics, and update the best scaled error.
                s = sn
                e = en
        # Output.
        return s
    
    # Plot iterative force/moment history
    def PlotCoeff(self, c, n=None, nAvg=100, **kw):
        """Plot a single coefficient history
        
        :Call:
            >>> h = FM.PlotCoeff(comp, c, n=1000, nAvg=100, **kw)
        :Inputs:
            *FM*: :class:`pyCart.dataBook.CaseFM`
                Instance of the component force history class
            *c*: :class:`str`
                Name of coefficient to plot, e.g. ``'CA'``
            *n*: :class:`int`
                Only show the last *n* iterations
            *nAvg*: :class:`int`
                Use the last *nAvg* iterations to compute an average
            *d*: :class:`float`
                Delta in the coefficient to show expected range
            *nLast*: :class:`int`
                Last iteration to use (defaults to last iteration available)
            *nFirst*: :class:`int`
                First iteration to plot
            *FigWidth*: :class:`float`
                Figure width
            *FigHeight*: :class:`float`
                Figure height
        :Outputs:
            *h*: :class:`dict`
                Dictionary of figure/plot handles
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
            * 2014-12-09 ``@ddalle``: Transferred to :class:`AeroPlot`
            * 2015-02-15 ``@ddalle``: Transferred to :class:`dataBook.Aero`
            * 2015-03-04 ``@ddalle``: Added *nStart* and *nLast*
        """
        # Make sure plotting modules are present.
        ImportPyPlot()
        # Extract the data.
        C = getattr(self, c)
        # Process inputs.
        nLast = kw.get('nLast')
        nFirst = kw.get('nFirst')
        # Iterative uncertainty options
        dc = kw.get("d", 0.0)
        ksig = kw.get("k", 0.0)
        uerr = kw.get("u", 0.0)
        # Other plot options
        fw = kw.get('FigWidth')
        fh = kw.get('FigHeight')
        # Get statistics
        s = self.GetStatsN(nAvg, nLast=nLast) 
        # ---------
        # Last Iter 
        # ---------
        # Most likely last iteration
        iB = self.i[-1]
        # Check for an input last iter
        if nLast is not None:
            # Attempt to use requested iter.
            if nLast < iB:
                # Using an earlier iter; make sure to use one in the hist.
                # Find the iterations that are less than i.
                jB = self.GetIterationIndex(nLast)
                iB = self.i[jB]
        # Get the index of *iB* in *self.i*.
        jB = self.GetIterationIndex(iB)
        # ----------
        # First Iter
        # ----------
        # Default number of iterations: all
        if n is None: n = len(self.i)
        # Get the starting iteration number to use.
        i0 = max(0, iB-n, nFirst) + 1
        # Make sure *iA* is in *self.i* and get the index.
        j0 = self.GetIterationIndex(i0)
        # Reselect *iA* in case initial value was not in *self.i*.
        i0 = self.i[j0]
        # --------------
        # Averaging Iter
        # --------------
        # Get the first iteration to use in averaging.
        iA = max(0, iB-nAvg) + 1
        # Make sure *iV* is in *self.i* and get the index.
        jA = self.GetIterationIndex(iA)
        # Reselect *iV* in case initial value was not in *self.i*.
        iA = self.i[jA]
        # -----------------------
        # Standard deviation plot
        # -----------------------
        # Initialize dictionary of handles.
        h = {}
        # Shortcut for the mean
        cAvg = s[c]
        # Initialize plot options for standard deviation
        kw_s = odict(color='b', lw=0.0,
            facecolor="b", alpha=0.35, zorder=1)
        # Show iterative n*standard deviation
        if ksig and nAvg>2:
            # Extract plot options from kwargs
            for k in util.denone(kw.get("StDevOptions", {})):
                # Ignore linestyle and ls
                if k in ['ls', 'linestyle']: continue
                # Override the default option.
                if kw["StDevOptions"][k] is not None:
                    kw_s[k] = kw["StDevOptions"][k]
            # Limits
            cMin = cAvg - ksig*s[c+"_std"]
            cMax = cAvg + ksig*s[c+"_std"]
            # Plot the target window boundaries.
            h['std'] = plt.fill_between([iA,iB], [cMin]*2, [cMax]*2, **kw_s)
        # --------------------------
        # Iterative uncertainty plot
        # --------------------------
        kw_u = odict(color='g', ls="none",
            facecolor="g", alpha=0.4, zorder=2)
        # Show iterative n*standard deviation
        if uerr and nAvg>2:
            # Extract plot options from kwargs
            for k in util.denone(kw.get("ErrPltOptions", {})):
                # Ignore linestyle and ls
                if k in ['ls', 'linestyle']: continue
                # Override the default option.
                if kw["ErrPltOptions"][k] is not None:
                    kw_u[k] = kw["ErrPltOptions"][k]
            # Limits
            cMin = cAvg - uerr*s[c+"_err"]
            cMax = cAvg + uerr*s[c+"_err"]
            # Plot the target window boundaries.
            h['err'] = plt.fill_between([iA,iB], [cMin]*2, [cMax]*2, **kw_u)
        # ---------
        # Mean plot
        # ---------
        # Initialize plot options for mean.
        kw_m = odict(color=kw.get("color", "0.1"),
            ls=[":", "-"], lw=1.0, zorder=8)
        # Extract plot options from kwargs
        for k in util.denone(kw.get("MeanOptions", {})):
            # Override the default option.
            if kw["MeanOptions"][k] is not None:
                kw_m[k] = kw["MeanOptions"][k]
        # Turn into two groups.
        kw0 = {}; kw1 = {}
        for k in kw_m:
            kw0[k] = kw_m.get_key(k, 0)
            kw1[k] = kw_m.get_key(k, 1)
        # Plot the mean.
        h['mean'] = (
            plt.plot([i0,iA], [cAvg, cAvg], **kw0) + 
            plt.plot([iA,iB], [cAvg, cAvg], **kw1))
        # ----------
        # Delta plot
        # ----------
        # Initialize options for delta.
        kw_d = odict(color="r", ls="--", lw=0.8, zorder=4)
        # Calculate range of interest.
        if dc:
            # Extract plot options from kwargs
            for k in util.denone(kw.get("DeltaOptions", {})):
                # Override the default option.
                if kw["DeltaOptions"][k] is not None:
                    kw_d[k] = kw["DeltaOptions"][k]
            # Turn into two groups.
            kw0 = {}; kw1 = {}
            for k in kw_m:
                kw0[k] = kw_d.get_key(k, 0)
                kw1[k] = kw_d.get_key(k, 1)
            # Limits
            cMin = cAvg-dc
            cMax = cAvg+dc
            # Plot the target window boundaries.
            h['min'] = (
                plt.plot([i0,iA], [cMin,cMin], **kw0) +
                plt.plot([iA,iB], [cMin,cMin], **kw1))
            h['max'] = (
                plt.plot([i0,iA], [cMax,cMax], **kw0) +
                plt.plot([iA,iB], [cMax,cMax], **kw1))
        # ------------
        # Primary plot
        # ------------
        # Initialize primary plot options.
        kw_p = odict(color=kw.get("color","k"), ls="-", lw=1.5, zorder=7)
        # Extract plot options from kwargs
        for k in util.denone(kw.get("LineOptions", {})):
            # Override the default option.
            if kw["LineOptions"][k] is not None:
                kw_p[k] = kw["LineOptions"][k]
        # Plot the coefficient.
        h[c] = plt.plot(self.i[j0:], C[j0:], **kw_p)
        # Get the figure and axes.
        h['fig'] = plt.gcf()
        h['ax'] = plt.gca()
        # Check for an existing ylabel
        ly = h['ax'].get_ylabel()
        # Compare to the requested ylabel
        if ly and ly != c:
            # Combine labels
            ly = ly + '/' + c
        else:
            # Use the coefficient
            ly = c
        # Labels.
        h['x'] = plt.xlabel('Iteration Number')
        h['y'] = plt.ylabel(ly)
        # Set the xlimits.
        h['ax'].set_xlim((i0, iB+25))
        # Set figure dimensions
        if fh: h['fig'].set_figheight(fh)
        if fw: h['fig'].set_figwidth(fw)
        # Attempt to apply tight axes.
        try: plt.tight_layout()
        except Exception: pass
        # ------
        # Labels
        # ------
        # y-coordinates of the current axes w.r.t. figure scale
        ya = h['ax'].get_position().get_points()
        ha = ya[1,1] - ya[0,1]
        # y-coordinates above and below the box
        yf = 2.5 / ha / h['fig'].get_figheight()
        yu = 1.0 + 0.065*yf
        yl = 1.0 - 0.04*yf
        # Make a label for the mean value.
        if kw.get("ShowMu", True):
            # Form: CA = 0.0204
            lbl = u'%s = %.4f' % (c, cAvg)
            # Create the handle.
            h['mu'] = plt.text(0.99, yu, lbl, color=kw_p['color'],
                horizontalalignment='right', verticalalignment='top',
                transform=h['ax'].transAxes)
            # Correct the font.
            try: h['mu'].set_family("DejaVu Sans")
            except Exception: pass
        # Make a label for the deviation.
        if dc and kw.get("ShowDelta", True):
            # Form: \DeltaCA = 0.0050
            lbl = u'\u0394%s = %.4f' % (c, dc)
            # Create the handle.
            h['d'] = plt.text(0.99, yl, lbl, color=kw_d.get_key('color',1),
                horizontalalignment='right', verticalalignment='top',
                transform=h['ax'].transAxes)
            # Correct the font.
            try: h['d'].set_family("DejaVu Sans")
            except Exception: pass
        # Make a label for the standard deviation.
        if ksig and nAvg>2 and kw.get("ShowSigma", True):
            # Form \sigma(CA) = 0.0032
            lbl = u'\u03C3(%s) = %.4f' % (c, ksig*s[c+'_std'])
            # Create the handle.
            h['sig'] = plt.text(0.01, yu, lbl, color=kw_s.get_key('color',1),
                horizontalalignment='left', verticalalignment='top',
                transform=h['ax'].transAxes)
            # Correct the font.
            try: h['sig'].set_family("DejaVu Sans")
            except Exception: pass
        # Make a label for the iterative uncertainty.
        if uerr and nAvg>2 and kw.get("ShowEpsilon", True):
            # Form \sigma(CA) = 0.0032
            lbl = u'\u0395(%s) = %.4f' % (c, ueps*s[c+'_err'])
            # Create the handle.
            h['eps'] = plt.text(0.01, yl, lbl, color=kw_u.get_key('color',1),
                horizontalalignment='left', verticalalignment='top',
                transform=h['ax'].transAxes)
            # Correct the font.
            try: h['sig'].set_family("DejaVu Sans")
            except Exception: pass
        # Output.
        return h
    
    # Plot coefficient histogram
    def PlotCoeffHist(self, c, nAvg=100, nBin=20, nLast=None, **kw):
        """Plot a single coefficient histogram
        
        :Call:
            >>> h = FM.PlotCoeffHist(comp, c, n=1000, nAvg=100, **kw)
        :Inputs:
            *FM*: :class:`pyCart.dataBook.CaseFM`
                Instance of the component force history class
            *comp*: :class:`str`
                Name of component to plot
            *c*: :class:`str`
                Name of coefficient to plot, e.g. ``'CA'``
            *nAvg*: :class:`int`
                Use the last *nAvg* iterations to compute an average
            *nBin*: :class:`int`
                Number of bins to plot
            *nLast*: :class:`int`
                Last iteration to use (defaults to last iteration available)
            *FigWidth*: :class:`float`
                Figure width
            *FigHeight*: :class:`float`
                Figure height
        :Outputs:
            *h*: :class:`dict`
                Dictionary of figure/plot handles
        :Versions:
            * 2015-02-15 ``@ddalle``: First version
            * 2015-03-06 ``@ddalle``: Added *nLast* and fixed documentation
            * 2015-03-06 ``@ddalle``: Copied to :class:`CaseFM`
        """
        # Make sure plotting modules are present.
        ImportPyPlot()
        # Extract the data.
        C = getattr(self, c)
        # Process other options
        fw = kw.get('FigWidth')
        fh = kw.get('FigHeight')
        # ---------
        # Last Iter 
        # ---------
        # Most likely last iteration
        iB = self.i[-1]
        # Check for an input last iter
        if nLast is not None:
            # Attempt to use requested iter.
            if nLast < iB:
                # Using an earlier iter; make sure to use one in the hist.
                # Find the iterations that are less than i.
                jB = self.GetIterationIndex(nLast)
                iB = self.i[jB]
        # Get the index of *iB* in *FM.i*.
        jB = self.GetIterationIndex(iB)
        # --------------
        # Averaging Iter
        # --------------
        # Get the first iteration to use in averaging.
        iA = max(0, iB-nAvg) + 1
        # Make sure *iV* is in *FM.i* and get the index.
        jA = self.GetIterationIndex(iA)
        # Reselect *iV* in case initial value was not in *FM.i*.
        iA = self.i[jA]
        # --------
        # Plotting
        # --------
        # Calculate statistics.
        cAvg = np.mean(C[jA:jB+1])
        cStd = np.std(C[jA:jB+1])
        cErr = util.SigmaMean(C[jA:jB+1])
        # Calculate # of independent samples
        # Number of available samples
        nStat = jB - jA + 1
        # Initialize dictionary of handles.
        h = {}
        # Plot the histogram.
        h[c] = plt.hist(C[jA:jB+1], nBin,
            normed=1, histtype='bar', rwidth=0.85, color='#2020ff')
        # Labels.
        h['x'] = plt.xlabel(c)
        h['y'] = plt.ylabel('PDF')
        # Get the figure and axes.
        h['fig'] = plt.gcf()
        h['ax'] = plt.gca()
        # Set figure dimensions
        if fh: h['fig'].set_figheight(fh)
        if fw: h['fig'].set_figwidth(fw)
        # Attempt to apply tight axes.
        try:
            plt.tight_layout()
        except Exception:
            pass
        # Make a label for the mean value.
        lbl = u'\u03BC(%s) = %.4f' % (c, cAvg)
        h['mu'] = plt.text(1.0, 1.06, lbl, horizontalalignment='right',
            verticalalignment='top', transform=h['ax'].transAxes)
        # Make a label for the standard deviation.
        lbl = u'\u03C3(%s) = %.4f' % (c, cStd)
        h['sigma'] = plt.text(0.02, 1.06, lbl, horizontalalignment='left',
            verticalalignment='top', transform=h['ax'].transAxes)
        # Make a label for the uncertainty.
        lbl = u'\u03C3(\u03BC) = %.4f' % cErr
        h['err'] = plt.text(0.02, 0.98, lbl, horizontalalignment='left',
            verticalalignment='top', transform=h['ax'].transAxes)
        # Attempt to set font to one with Greek symbols.
        try:
            # Set the fonts.
            h['mu'].set_family("DejaVu Sans")
            h['sigma'].set_family("DejaVu Sans")
            h['err'].set_family("DejaVu Sans")
        except Exception:
            pass
        # Output.
        return h
# class CaseFM
    

# Aerodynamic history class
class CaseResid(object):
    """
    Iterative history class
    
    This class provides an interface to residuals, CPU time, and similar data
    for a given run directory
    
    :Call:
        >>> hist = pyCart.dataBook.CaseResid()
    :Outputs:
        *hist*: :class:`pyCart.dataBook.CaseResid`
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
        fdir = GetWorkingFolder()
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
        else:
            # No steady-state iterations.
            n0 = 0
        # Process unsteady iterations if any.
        if A[-1,0] > n0:
            # Get the integer values of the iteration indices.
            # For *ni0*, 2000.000 --> 1999; 2000.100 --> 2000
            ni0 = np.array(A[n0:,0]-1e-4, dtype=int)
            # For *ni0*, 2000.000 --> 2000; 1999.900 --> 1999
            ni1 = np.array(A[n0:,0], dtype=int)
            # Look for iterations where the index crosses an integer.
            i0 = np.insert(np.where(ni0[1:] > ni0[:-1])[0]+1, 0, 0) + n0
            i1 = np.where(ni1[1:] > ni1[:-1])[0] + 1 + n0
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
        # Save the initial residuals.
        self.L1Resid0 = A[i0, 3]
        # Rewrite the history.dat file without middle subiterations.
        if not os.path.isfile('RUNNING'):
            # Iterations to keep.
            i = np.union1d(i0, i1)
            # Write the integer iterations and the first subiterations.
            open(fhist, 'w').writelines(np.array(lines)[i])
        # Eliminate subiterations.
        A = A[i1]
        # Save the number of iterations.
        self.nIter = int(A[-1,0])
        # Save the iteration numbers.
        self.i = A[:,0]
        # Save the CPU time per processor.
        self.CPUtime = A[:,1]
        # Save the maximum residual.
        self.maxResid = A[:,2]
        # Save the global residual.
        self.L1Resid = A[:,3]
        # Process the CPUtime used for steady cycles.
        if n0 > 0:
            # At least one steady-state cycle.
            # Find the index of the last steady-state iter.
            i0 = np.where(self.i==n0)[0] + 1
            # Get the CPU time used up to that point.
            t = self.CPUtime[i0-1]
        else:
            # No steady state cycles.
            i0 = 0
            t = 0.0
        # Process the unsteady cycles.
        if self.nIter > n0:
            # Add up total CPU time for unsteady cycles.
            t += np.sum(self.CPUtime[i0:])
        # Check for a 'user_time.dat' file.
        if os.path.isfile('user_time.dat'):
            # Loop through lines.
            for line in open('user_time.dat').readlines():
                # Check comment.
                if line.startswith('#'): continue
                # Add to the time everything except flowCart time.
                t += np.sum([float(v) for v in line.split()[2:]])
        # Save the time.
        self.CPUhours = t / 3600.
        
    # Number of orders of magnitude of residual drop
    def GetNOrders(self, nStats=1):
        """Get the number of orders of magnitude of residual drop
        
        :Call:
            >>> nOrders = hist.GetNOrders(nStats=1)
        :Inputs:
            *hist*: :class:`pyCart.dataBook.CaseResid`
                Instance of the DataBook residual history
            *nStats*: :class:`int`
                Number of iterations to use for averaging the final residual
        :Outputs:
            *nOrders*: :class:`float`
                Number of orders of magnitude of residual drop
        :Versions:
            * 2015-01-01 ``@ddalle``: First versoin
        """
        # Process the number of usable iterations available.
        i = max(self.nIter-nStats, 0)
        # Get the maximum residual.
        L1Max = np.log10(np.max(self.L1Resid))
        # Get the average terminal residual.
        L1End = np.log10(np.mean(self.L1Resid[i:]))
        # Return the drop
        return L1Max - L1End
        
    # Number of orders of unsteady residual drop
    def GetNOrdersUnsteady(self, n=1):
        """
        Get the number of orders of magnitude of unsteady residual drop for each
        of the last *n* unsteady iteration cycles.
        
        :Call:
            >>> nOrders = hist.GetNOrders(n=1)
        :Inputs:
            *hist*: :class:`pyCart.dataBook.CaseResid`
                Instance of the DataBook residual history
            *n*: :class:`int`
                Number of iterations to analyze
        :Outputs:
            *nOrders*: :class:`numpy.ndarray` (:class:`float`), shape=(n,)
                Number of orders of magnitude of unsteady residual drop
        :Versions:
            * 2015-01-01 ``@ddalle``: First versoin
        """
        # Process the number of usable iterations available.
        i = max(self.nIter-n, 0)
        # Get the initial residuals
        L1Init = np.log10(self.L1Resid0[i:])
        # Get the terminal residuals.
        L1End = np.log10(self.L1Resid[i:])
        # Return the drop
        return L1Init - L1End
        
    # Plot function
    def PlotL1(self, n=None, nFirst=None, nLast=None, **kw):
        """Plot the L1 residual
        
        :Call:
            >>> h = hist.PlotL1(n=None, nFirst=None, nLast=None, **kw)
        :Inputs:
            *hist*: :class:`pyCart.dataBook.CaseResid`
                Instance of the DataBook residual history
            *n*: :class:`int`
                Only show the last *n* iterations
            *nFirst*: :class:`int`
                Plot starting at iteration *nStart*
            *nLast*: :class:`int`
                Plot up to iteration *nLast*
            *FigWidth*: :class:`float`
                Figure width
            *FigHeight*: :class:`float`
                Figure height
        :Outputs:
            *h*: :class:`dict`
                Dictionary of figure/plot handles
        :Versions:
            * 2014-11-12 ``@ddalle``: First version
            * 2014-12-09 ``@ddalle``: Moved to :class:`AeroPlot`
            * 2015-02-15 ``@ddalle``: Transferred to :class:`dataBook.Aero`
            * 2015-03-04 ``@ddalle``: Added *nStart* and *nLast*
        """
        # Make sure plotting modules are present.
        ImportPyPlot()
        # Initialize dictionary.
        h = {}
        # Get iteration numbers.
        if n is None:
            # Use all iterations
            n = self.i[-1]
        # Process other options
        fw = kw.get('FigWidth')
        fh = kw.get('FigHeight')
        # ---------
        # Last Iter 
        # ---------
        # Most likely last iteration
        iB = self.i[-1]
        # Check for an input last iter
        if nLast is not None:
            # Attempt to use requested iter.
            if nLast < iB:
                # Using an earlier iter; make sure to use one in the hist.
                jB = self.GetIterationIndex(nLast)
                # Find the iterations that are less than i.
                iB = self.i[jB]
        # Get the index of *iB* in *FM.i*.
        jB = np.where(self.i == iB)[0][-1]
        # ----------
        # First Iter
        # ----------
        # Get the starting iteration number to use.
        i0 = max(0, iB-n, nFirst) + 1
        # Make sure *iA* is in *FM.i* and get the index.
        j0 = self.GetIterationIndex(i0)
        # Reselect *iA* in case initial value was not in *FM.i*.
        i0 = self.i[j0]
        # --------
        # Plotting
        # --------
        # Extract iteration numbers and residuals.
        i  = self.i[i0:]
        L1 = self.L1Resid[i0:]
        L0 = self.L1Resid0[i0:]
        # Check if L0 is too long.
        if len(L0) > len(i):
            # Trim it.
            L0 = L0[:len(i)]
        # Plot the initial residual if there are any unsteady iterations.
        if L0[-1] > L1[-1]:
            h['L0'] = plt.semilogy(i, L0, 'b-', lw=1.2)
        # Plot the residual.
        h['L1'] = plt.semilogy(i, L1, 'k-', lw=1.5)
        # Labels
        h['x'] = plt.xlabel('Iteration Number')
        h['y'] = plt.ylabel('L1 Residual')
        # Get the figures and axes.
        h['ax'] = plt.gca()
        h['fig'] = plt.gcf()
        # Set figure dimensions
        if fh: h['fig'].set_figheight(fh)
        if fw: h['fig'].set_figwidth(fw)
        # Attempt to apply tight axes.
        try:
            plt.tight_layout()
        except Exception:
            pass
        # Set the xlimits.
        h['ax'].set_xlim((i0, iB+25))
        # Output.
        return h
        
        
    # Function to get index of a certain iteration number
    def GetIterationIndex(self, i):
        """Return index of a particular iteration in *hist.i*
        
        If the iteration *i* is not present in the history, the index of the
        last available iteration less than or equal to *i* is returned.
        
        :Call:
            >>> j = hist.GetIterationIndex(i)
        :Inputs:
            *hist*: :class:`pyCart.dataBook.CaseResid`
                Instance of the residual history class
            *i*: :class:`int`
                Iteration number
        :Outputs:
            *j*: :class:`int`
                Index of last iteration in *FM.i* less than or equal to *i*
        :Versions:
            * 2015-03-06 ``@ddalle``: First version
        """
        # Check for *i* less than first iteration.
        if i < self.i[0]: return 0
        # Find the index.
        j = np.where(self.i <= i)[0][-1]
        # Output
        return j
# class CaseResid
        
