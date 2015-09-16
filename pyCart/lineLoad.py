"""
Sectional Loads Module: :mod:`pyCart.lineLoad`
==============================================

This module contains functions for reading and processing sectional loads.  It
is a submodule of :mod:`pyCart.dataBook`.

:Versions:
    * 2015-09-15 ``@ddalle``: Started
"""

# File interface
import os, glob
# Basic numerics
import numpy as np
# Date processing
from datetime import datetime

# Utilities or advanced statistics
from . import util
from . import case
from . import tar


# Data book of line loads
class DBLineLoad(object):
    """Line load (sectional load) data book for one group
    
    :Call:
        >>> DBL = DBLineLoad(cart3d, comp)
    :Inputs:
        *cart3d*: :class:`pyCart.cart3d.Cart3d`
            Master pyCart interface
        *i*: :class:`int`
            Case index
        *comp*: :class:`str`
            Name of line load group
    :Outputs:
        *DBL*: :class:`pyCart.lineLoad.DBLineLoad`
            Instance of line load data book
        *DBL.nCut*: :class:`int`
            Number of *x*-cuts to make, based on options in *cart3d*
        *DBL.RefL*: :class:`float`
            Reference length
        *DBL.MRP*: :class:`numpy.ndarray` shape=(3,)
            Moment reference center
        *DBL.x*: :class:`numpy.ndarray` shape=(*nCut*,)
            Locations of *x*-cuts
        *DBL.CA*: :class:`numpy.ndarray` shape=(*nCut*,)
            Axial force sectional load, d(CA)/d(x/RefL))
    :Versions:
        * 2015-09-16 ``@ddalle``: First version
    """
    def __init__(self, cart3d, comp):
        """Initialization method
        
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Get the data book directory.
        fdir = opts.get_DataBookDir()
        # Compatibility
        fdir = fdir.repalce("/", os.sep)
        
        # Construct the file name.
        fcomp = 'll_%s.csv' % comp
        # Full file name
        fname = os.apth.join(fdir, fcomp)
        
        # Save the Cart3D run info
        self.cart3d = cart3d
        # Save the file name.
        self.fname = fname
        
        # Reference areas
        self.RefA = cart3d.opts.get_RefArea(self.RefComp)
        self.RefL = cart3d.opts.get_RefLength(self.RefComp)
        # Moment reference point
        self.MRP = np.array(cart3d.opts.get_RefPoint(self.RefComp))
        
        # Read the file or initialize empty arrays.
        self.Read(fname)
        
    # Representation method
    def __repr__(self):
        """Representation method
        
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Initialize string
        lbl = "<DBLineLoad %s, " % self.comp
        # Number of cases in book
        lbl += "nCase=%i>" % self.n
        # Output
        return lbl
        
    # function to read line load data book summary
    def Read(self, fname=None):
        """Read a data book summary file for a single line load group
        
        :Call:
            >>> DBL.Read()
            >>> DBL.Read(fname)
        :Inputs:
            *DBL*: :class:`pyCart.lineLoad.DBLineLoad`
                Instance of line load data book
            *fname*: :class:`str`
                Name of summary file
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Check for default file name
        if fname is None: fname = self.fname
        # Try to read the file.
        try:
            # Data book delimiter
            delim = self.opts.get_Delimiter()
            # Initialize column number.
            nCol = 0
            # Loop through the trajectory keys.
            for k in self.cart3d.x.keys:
                # Get the type.
                t = self.cart3d.x.defns[k].get('Value', 'float')
                # Convert type.
                if t in ['hex', 'oct', 'octal', 'bin']: t = 'int'
                # Read the column
                self[k] = np.loadtxt(fname,
                    delimiter=delim, dtype=str(t), usecols=[nCol])
                # Increase the column number.
                nCol += 1
            # Mach number and Reynolds number
            self['Mach'] = np.loadtxt(fname,
                delimiter=delim, dtype=float, usecols=[nCol])
            self['Re'] = np.loadtxt(fname,
                delimiter=delim, dtype=float, usecols=[nCol+1])
            # MRP
            nCol += 2
            self['XMRP'] = np.loadtxt(fname,
                delimiter=delim, dtype=float, usecols=[nCol])
            self['YRMP'] = np.loadtxt(fname,
                delimiter=delim, dtype=float, usecols=[nCol+1])
            self['ZMRP'] = np.loadtxt(fname,
                delimiter=delim, dtype=float, usecols=[nCol+2])
            # Iteration number
            nCol += 3
            self['nIter'] = np.loadtxt(fname,
                delimiter=delim, dtype=int, usecols=[nCol])
            # Stats
            nCol += 1
            self['nStats'] = np.loadtxt(fname,
                delimiter=delim, dtype=int, usecols=[nCol])
        except Exception:
            # Initialize empty trajectory arrays
            for k in self.cart3d.x.keys:
                # get the type.
                t = self.cart3d.x.defns[k].get('Value', 'float')
                # convert type
                if t in ['hex', 'oct', 'octal', 'bin']: t = 'int'
                # Initialize an empty array.
                self[k] = np.array([], dtype=str(t))
            # Initialize Other parameters.
            self['Mach'] = np.array([], dtype=float)
            self['Re']   = np.array([], dtype=float)
            self['XMRP'] = np.array([], dtype=float)
            self['YRMP'] = np.array([], dtype=float)
            self['ZMRP'] = np.array([], dtype=float)
            self['nIter'] = np.array([], dtype=int)
            self['nStats'] = np.array([], dtype=int)
        # Save the number of cases analyzed.
        self.n = len(self[k])
    
    # Function to write line load data book summary file
    def Write(self, fname=None):
        """Wrie a single line load data book summary file
        
        :Call:
            >>> DBL.Write()
            >>> DBL.Write(fname)
        :Inputs:
            *DBL*: :class:`pycart.lineLoad.DBLineLoad`
                Instance of line load data book
            *fname*: :class:`str`
                Name of summary file
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Check for default file name
        if fname is None: fname = self.fname
        # check for a previous old file.
        if os.path.isfile(fname+".old"):
            # Remove it.
            os.remove(fname+".old")
        # Check for an existing data file.
        if os.path.isfile(fname):
            # Move it to ".old"
            os.rename(fname, fname+".old")
        # DataBook delimiter
        delim = self.cart3d.opts.get_Delimiter()
        # Open the file.
        f = open(fname, 'w')
        # Write the header
        f.write("# Line load summary for '%s' extracted on %s\n" %
            (self.comp, datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')))
        # Empty line.
        f.write('#\n')
        # Reference quantities
        f.write('# Reference Area = %.6E\n' % self.RefA)
        f.write('# Reference Length = %.6E\n' % self.RefL)
        # Moment reference point
        f.write('# Nominal moment reference point:\n')
        f.write('# XMRP = %.6E\n' % self.MRP[0])
        f.write('# YMRP = %.6E\n' % self.MRP[1])
        f.write('# ZMRP = %.6E\n' % self.MRP[2])
        # Empty line and start of variable list
        f.write('#\n# ')
        # Write the name of each trajectory key.
        for k in self.cart3d.x.keys:
            f.write(k + delim)
        # Write the extra column titles.
        f.write('Mach%sRe%sXMRP%sYMRP%sZMRP%snIter%snStats\n' %
            tuple([delim]*6))
        # Loop through database entries.
        for i in np.arange(self.n):
            # Write the trajectory values.
            for k in self.cart3d.x.keys:
                f.write('%s%s' % (self[k][i], delim))
            # Write data values
            f.write('%s%s' % (self['Mach'][i], delim))
            f.write('%s%s' % (self['Re'][i], delim))
            f.write('%s%s' % (self['XMRP'][i], delim))
            f.write('%s%s' % (self['YMRP'][i], delim))
            f.write('%s%s' % (self['ZMRP'][i], delim))
            # Iteration counts
            f.write('%i%s' % (self['nIter'][i], delim))
            f.write('%i%s' % (self['nStats'][i], delim))
        # Close the file.
        f.close()
    

# Line loads
class CaseLL(object):
    """Individual class line load class
    
    :Call:
        >>> LL = CaseLL(cart3d, i, comp)
    :Inputs:
        *cart3d*: :class:`pyCart.cart3d.Cart3d`
            Master pyCart interface
        *i*: :class:`int`
            Case index
        *comp*: :class:`str`
            Name of line load group
    :Outputs:
        *LL*: :class:`pyCart.lineLoad.CaseLL`
            Instance of individual case line load interface
        *LL.nCut*: :class:`int`
            Number of *x*-cuts to make, based on options in *cart3d*
        *LL.nIter*: :class:`int`
            Last iteration in line load file
        *LL.nStats*: :class:`int`
            Number of iterations in line load file
        *LL.RefL*: :class:`float`
            Reference length
        *LL.MRP*: :class:`numpy.ndarray` shape=(3,)
            Moment reference center
        *LL.x*: :class:`numpy.ndarray` shape=(*nCut*,)
            Locations of *x*-cuts
        *LL.CA*: :class:`numpy.ndarray` shape=(*nCut*,)
            Axial force sectional load, d(CA)/d(x/RefL))
    :Versions:
        * 2015-09-16 ``@ddalle``: First version
    """
    # Initialization method
    def __init__(self, cart3d, i, comp):
        """Initialization method"""
        # Save options
        self.cart3d = cart3d
        self.i = i
        self.comp = comp
        # Number of cuts
        self.nCut = cart3d.opts.get_LineLoad_nCut(comp)
        # Ensure triangulation is present
        cart3d.ReadTri()
        # Lead component
        o_comp = cart3d.opts.get_LineLoadComponents(comp)
        # Components
        self.CompID = cart3d.tri.config.GetCompID(o_comp)
        # Get Mach number and Reynolds number options
        o_mach = cart3d.opts.get_ComponentMach(comp)
        o_gam  = cart3d.opts.get_ComponentGamma(comp)
        o_re   = cart3d.opts.get_ComponentReynoldsNumber(comp)
        # Process "primary" component
        if type(o_comp).__name__ == 'list':
            # Use the first component
            self.RefComp = o_comp[0]
        else:
            # Use as is
            self.RefComp = o_comp
        # Process Mach number
        if type(o_mach).__name__ in ['str', 'unicode']:
            # Trajectory key
            self.Mach = getattr(cart3d.x,o_mach)[i]
        elif o_mach is None:
            # Default
            self.Mach = 1.0
        else:
            # Specified value
            self.Mach = o_mach
        # Process Reynolds number per inch
        if type(o_gam).__name__ in ['str', 'unicode']:
            # Trajectory key
            self.Gamma = getattr(cart3d.x,o_gam)[i]
        elif o_gam is None:
            # Default
            self.Gamma = 1.4
        else:
            # Specified value
            self.Gamma = o_gam
        # Process Reynolds number per inch
        if type(o_re).__name__ in ['str', 'unicode']:
            # Trajectory key
            self.Re = getattr(cart3d.x,o_re)[i]
        elif o_re is None:
            # Default
            self.Re = 1.0
        else:
            # Specified value
            self.Re = o_re
        # Reference areas
        self.RefA = cart3d.opts.get_RefArea(self.RefComp)
        self.RefL = cart3d.opts.get_RefLength(self.RefComp)
        # Moment reference point
        self.MRP = np.array(cart3d.opts.get_RefPoint(self.RefComp))
        # Containing BBox
        self.BBox = cart3d.tri.GetCompBBox(self.CompID)
        ## Min and max *x*-coordinates
        self.xmin = self.BBox[0]
        self.xmax = self.BBox[1]
    
    # Function to display contents
    def __repr__(self):
        """Representation method
        
        Returns the following format:
        
            * ``<CaseLL nCut=200>``
        
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        return "<CaseLL nCut=%i>" % self.nCut
    
    # Write line loads file
    def WriteTriloadInput(self):
        """Write :file:`triload.i` input file to `triloadCmd`
        
        :Call:
            >>> LL.WriteTriloadInput()
        :Inputs:
            *LL*: :class:`pyCart.lineLoad.CaseLL`
                Instance of data book line load interface
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Open the file.
        f = open('triload.i', 'w')
        # Write the name of the triq file
        f.write('Components.i.triq\n')
        f.write('LineLoad\n')
        # Write Mach number, Reynolds number, 
        f.write('%s %s %s\n' % (self.Mach, self.Re, self.Gamma))
        # Write moment reference point
        f.write('%s %s %s\n' % tuple(self.MRP))
        # Settings about units
        f.write('0 0\n')
        # Reference length and area
        f.write('%s %s\n' % (self.RefL, self.RefA))
        # Do not include momentum in line loads
        f.write('n\n')
        # Name and component IDs
        f.write('%s %s\n' % (self.comp, ",".join([str(c) for c in self.CompID])))
        # Number of cuts
        f.write('%i\n' % self.nCut)
        # Min and max coordinates
        f.write('%f, %f\n' % (self.xmin, self.xmax))
        # Type and cleanup
        f.write('const x\n')
        f.write('n\n')
        # Close the file.
        f.close()
        
    # Execute triload system command
    def RunTriload(self):
        """Run `triloadCmd` using the appropriate input file
        
        :Call:
            >>> LL.RunTriload()
        :Inputs:
            *LL*: :class:`pyCart.lineLoad.CaseLL`
                Instance of data book line load interface
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Write the input file.
        self.WriteTriloadInput()
        # Run triload without some of the interface
        ierr = os.system('triloadCmd < triload.i > triload.out')
        # Check status
        if ierr:
            raise SystemError("Running 'triloadCmd' failed.")
            
    # Calculate triloads
    def CalculateLineLoads(self):
        """Set up inputs for a sectional loads case and compute them
        
        :Call:
            >>> LL.CalculateLineLoads()
        :Inputs:
            *LL*: :class:`pyCart.lineLoad.CaseLL`
                Instance of data book line load interface
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Initialize line load
        self.LL = None
        # Change to root directory.
        fpwd = os.getcwd()
        os.chdir(self.cart3d.RootDir)
        # Name of triload folder
        ftri = 'fomo-lineload'
        # Name of output files.
        flds = 'LineLoad_%s.dlds' % self.comp
        # Get working directory
        fdir = self.cart3d.x.GetFullFolderNames(i)
        # Check folder.
        if not os.path.isdir(fdir):
            os.chdir(fpwd)
            return
        # Enter
        os.chdir(frun)
        # Check for lineload folder.
        if not os.path.isdir(ftri): os.mkdir(ftri, 0027)
        # Get working folder.
        fwrk = os.path.abspath(case.GetWorkingFolder())
        # Get triangulation file
        ftrq, nStats, i0, i1 = self.GetTriqFile()
        # Full path to triangulation
        ftriq = os.path.join(fwrk, ftrq)
        # Check for ``triq`` file
        if not os.path.isfile(ftriq):
            # Save non iteration numbers
            self.nIter = np.nan
            self.nStats = np.nan
            # Exit
            os.chdir(fpwd)
            return
        # Enter the lineload folder.
        os.chdir(ftri)
        # Create symbolic link
        os.symlink(ftriq, 'Components.i.triq')
        # Execute triload
        self.RunTriload()
        # Read the data.
        self.ReadLDS(flds)
        # Statistics
        self.nIter = i1
        self.nStats = nStats
        self.i0 = i0
        # Clean up.
        tar.chdir_up()
        os.chdir(fpwd)
        
    # Function to determine newest triangulation file
    def GetTriqFile(self):
        """Get most recent ``triq`` file and its associated iterations
        
        :Call:
            >>> ftriq, n, i0, i1 = LL.GetTriqFile()
        :Inputs:
            *LL*: :class:`pyCart.lineLoad.CaseLL`
                Instance of data book line load interface
        :Outputs:
            *ftriq*: :class:`str`
                Name of ``triq`` file
            *n*: :class:`int`
                Number of iterations included
            *i0*: :class:`int`
                First iteration in the averaging
            *i1*: :class:`int`
                Last iteration in the averaging
        :Versions:
            * 2015-09-16 ``@ddalle``: First version
        """
        # Get the working directory.
        fwrk = case.GetWorkingFolder()
        # Go there.
        fpwd = os.getcwd()
        os.chdir(fwrk)
        # Get the glob of numbered files.
        fglob3 = glob.glob('Components.*.*.*.triq')
        fglob2 = glob.glob('Components.*.*.triq')
        fglob1 = glob.glob('Components.[0-9]*.triq')
        # Check it.
        if len(fglob3) > 0:
            # Get last iterations
            I0 = [int(f.split('.')[3]) for f in fglob3]
            # Index of best iteration
            j = np.argmax(I0)
            # Iterations there.
            i1 = I0[j]
            i0 = int(fglob3[j].split('.')[2])
            # Count
            n = int(fglob3[j].split('.')[1])
            # File name
            ftriq = fglob3[j]
        if len(fglob2) > 0:
            # Get last iterations
            I0 = [int(f.split('.')[2]) for f in fglob2]
            # Index of best iteration
            j = np.argmax(I0)
            # Iterations there.
            i1 = I0[j]
            i0 = int(fglob2[j].split('.')[1])
            # File name
            ftriq = fglob2[j]
        # Check it.
        elif len(fglob1) > 0:
            # Get last iterations
            I0 = [int(f.split('.')[1]) for f in fglob1]
            # Index of best iteration
            j = np.argmax(I0)
            # Iterations there.
            i1 = I0[j]
            i0 = I0[j]
            # Count
            n = i1 - i0 + 1
            # File name
            ftriq = fglob1[j]
        # Plain file
        elif os.path.isfile('Components.i.triq'):
            # Iteration counts: assume it's most recent iteration
            i1 = self.cart3d.CheckCase(self.i)
            i0 = i1
            # Count
            n = 1
            # file name
            ftriq = 'Components.i.triq'
        else:
            # No iterations
            i1 = None
            i0 = None
            n = None
            ftriq = None
        # Output
        os.chdir(fpwd)
        return ftriq, n, i0, i1
        
    
    # Function to read a file
    def ReadLDS(fname):
        """Read a sectional loads ``*.?lds`` from `triloadCmd`
        
        :Call:
            >>> d = ReadLDS(fname)
        :Inputs:
            *fname*: :class:`str`
                Name of file to read
        :Outputs:
            *d*: :class:`dict` (:class:`numpy.ndarray`)
                Dictionary of each line load coefficient
            *d['x']*: :class:`numpy.ndarray`
                Vector of cut coordinates
            *d['CA']*: :class:`numpy.ndarray`
                Axial force contribution
        :Versions:
            * 2015-09-15 ``@ddalle``: First version
        """
        # Open the file.
        f = open(fname, 'r')
        # Read lines until it is not a comment.
        line = '#'
        while (not line.lstrip().startswith('#')) and (len(line)>0):
            # Read the next line.
            line = f.readline()
        # Exit if empty.
        if len(line) == 0:
            return {}
        # Number of columns
        nCol = len(line.split())
        # Go backwards one line from current position.
        f.seek(-len(line), 1)
        # Read the rest of the file.
        D = np.fromfile(f, count=-1, sep=' ')
        # Reshape to a matrix
        D = D.reshape((D.size/nCol, nCol))
        # Save the keys.
        self.x   = D[:,0]
        self.CA  = D[:,1]
        self.CY  = D[:,2]
        self.CN  = D[:,3]
        self.CLL = D[:,4]
        self.CLM = D[:,5]
        self.CLN = D[:,6]
# class CaseLL

        
            
