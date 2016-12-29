"""
Cape utilities: :mod:`cape.util`
================================

This module provides several utilities used throughout the Cape system,
including :func:`SigmaMean` to compute statistical sampling error for iterative
histories and :func:`readline` to process special space-or-comma-separated lines
for run matrix files.
"""

# Numerics
import numpy as np
# File system
import subprocess as sp
# Import path utilities
import os.path, sys
# Text
import re



# cape base folder
capeFolder = os.path.split(os.path.abspath(__file__))[0]
rootFolder = os.path.split(capeFolder)[0]
# Folder containing TecPlot templates
TecFolder = os.path.join(rootFolder, "templates", "tecplot")
# Folder containing Paraview templates
ParaviewFolder = os.path.join(rootFolder, "templates", "paraview")

# Split text by either comma or space
def SplitLineGeneral(line):
    """Split a string in which uses a mix of commas and spaces as delimiters
    
    :Call:
        >>> V = SplitLineGeneral(line)
    :Inputs:
        *line*: :class:`str`
            Text with commas, spaces, or a combination as delimiters
    :Outputs:
        *V*: :class:`list` (:class:`str`)
            List of values split by delimiters
    :Versions:
        * 2016-12-29 ``@ddalle``: First version
    """
    # Split using regular expressions (after stripping white space)
    V = re.split("[\s\,]+", line.strip())
    # Check for empty
    if (len(V) == 1) and (V[0] == ""):
        # Return an empty state instead
        return []
    else:
        # Return the list
        return V

# Convert a list of numbers to a compact string
def RangeString(rng):
    """Convert a list of ascending integers to a string like "1-10,12,14-15"
    
    :Call:
        >>> txt = RangeString(rng)
    :Inputs:
        *rng*: :class:`list` (:class:`int`)
            Range of integers
    :Outputs:
        *txt*: :class:`str`
            Nicely formatted string combining contiguous ranges with ``"-"``
    :Versions:
        * 2016-10-20 ``@ddalle``: First version
    """
    # Number of components
    n = len(rng)
    # Check for single component or no components
    if n == 0:
        return ""
    if n == 1:
        return ("%s" % rng[0])
    # Initialize the string and indices
    txt = []
    ibeg = rng[0]
    iend = rng[0]
    # Loop through the grid numbers, which are ascending and unique.
    for i in range(1,n):
        # Get the compID
        icur = rng[i]
        # Check if this is one greater than the previous one
        if icur == iend + 1:
            # Add to the current list
            iend += 1
        # Write if appropriate
        if i == n-1 or icur > iend+1:
            # Check if single element or list
            if ibeg == iend:
                # Write single
                txt.append("%s" % ibeg)
            else:
                # Write list
                txt.append("%s-%s" % (ibeg, iend))
            # Reset.
            ibeg = icur
            iend = icur
    # Output
    return ",".join(txt)


# Function to get uncertainty in the mean
def SigmaMean(x):
    """Calculate standard deviation of mean of an array of values
    
    Specifically, this returns the standard deviation of an array generated in
    the following way.  If you created 100 sets with the same statistical
    properties as *x* and created an array *X* which contained the means of each
    of those 100 sets, the purpose of this function is to estimate what the
    standard deviation of *X* would be.
    
    :Call:
        >>> sig = cape.util.SigmaMean(x)
    :Inputs:
        *x*: :class:`numpy.ndarray` or :class:`list`
            Array of points
    :Outputs:
        *sig*: :class:`float`
            Estimated standard deviation of the mean
    :Versions:
        * 2015-02-21 ``@ddalle``: First version
    """
    # Length of list
    n = len(x)
    # Best length to break list into
    ni = int(np.sqrt(n))
    # Number of sublists
    mi = n / ni
    # Split into chunks
    X = np.array([np.mean(x[i*ni:(i+1)*ni]) for i in range(mi)])
    # Standard deviation of the sub-means
    si = np.std(X)
    # Output
    return si * np.sqrt(float(ni)/float(n))
    
# Function to get a non comment line
def readline(f, comment='#'):
    """Read line that is nonempty and not a comment
    
    :Call:
        >>> line = readline(f, comment='#')
    :Inputs:
        *f*: :class:`file`
            File instance
        *comment*: :class:`str`
            Character(s) that begins a comment
    :Outputs:
        *line*: :class:`str`
            Nontrivial line or `''` if at end of file
    :Versions:
        * 2015-11-19 ``@ddalle``: First version
    """
    # Read a line.
    line = f.readline()
    # Check for empty line (EOF)
    if line == '': return line
    # Process stripped line
    lstrp = line.strip()
    # Check if otherwise empty or a comment
    while (lstrp=='') or lstrp.startswith(comment):
        # Read the next line.
        line = f.readline()
        # Check for empty line (EOF)
        if line == '': return line
        # Process stripped line
        lstrp = line.strip()
    # Return the line.
    return line
    
# Function to get Tecplot command
def GetTecplotCommand():
    """Return the Tecplot 360 command on the current system
    
    The preference is 'tec360EX', 'tec360', 'tecplot'.  An exception is raised
    if none of these commands can be found.
    
    :Call:
        >>> cmd = cape.util.GetTecplotCommand()
    :Outputs:
        *cmd*: :class:`str`
            Name of the command to the current 'tec360' command
    :Versions:
        * 2015-03-02 ``@ddalle``: First version
    """
    # Shut up about output.
    f = open('/dev/null', 'w')
    # Loop through list of possible commands
    for cmd in ['tec360EX', 'tec360', 'tecplot']:
        # Use `which` to see where the command might be.
        ierr = sp.call(['which', cmd], stdout=f, stderr=f)
        # Check.
        if ierr: continue
        # If this point is reached, we found the command.
        return cmd
    # If this point is reached, no command was found.
    raise SystemError('No Tecplot360 command found')

# Function to fix "NoneType is not iterable" nonsense
def denone(x):
    """Replace ``None`` with ``[]`` to avoid iterative problems
    
    :Call:
        >>> y = cape.util.denone(x)
    :Inputs:
        *x*: any
            Any variable
    :Outputs:
        *y*: any
            Same as *x* unless *x* is ``None``, then ``[]``
    :Versions:
        * 2015-03-09 ``@ddalle``: First version
    """
    if x is None:
        return []
    else:
        return x
        
# Check if an object is a list.
def islist(x):
    """Check if an object is a list or not
    
    :Call:
        >>> q = cape.util.islist(x)
    :Inputs:
        *x*: any
            Any variable
    :Outputs:
        *q*: :class:`bool`
            Whether or not *x* is in [:class:`list` or :class:`numpy.ndarray`]
    :Versions:
        * 2015-06-01 ``@ddalle``: First version
    """
    return type(x).__name__ in ['list', 'ndarray']

# Function to automatically get inclusive data limits.
def get_ylim(ha, ypad=0.05, **kw):
    """Calculate appropriate *y*-limits to include all lines in a plot
    
    Plotted objects in the classes :class:`matplotlib.lines.Lines2D` and
    :class:`matplotlib.collections.PolyCollection` are checked.
    
    :Call:
        >>> ymin, ymax = get_ylim(ha, ypad=0.05, ym=None, yp=None)
    :Inputs:
        *ha*: :class:`matplotlib.axes.AxesSubplot`
            Axis handle
        *ypad*: {``0.05``} | :class:`float`
            Extra padding to min and max values to plot
        *ym*: :class:`float`
            Padding on minimum side
        *yp*: :class:`float`
            Padding on maximum side
    :Outputs:
        *ymin*: :class:`float`
            Minimum *y* coordinate including padding
        *ymax*: :class:`float`
            Maximum *y* coordinate including padding
    :Versions:
        * 2015-07-06 ``@ddalle``: First version
        * 2016-06-10 ``@ddalle``: Moved to :mod:`cape.util`
    """
    # Initialize limits.
    ymin = np.inf
    ymax = -np.inf
    # Loop through all children of the input axes.
    for h in ha.get_children():
        # Get the type.
        t = type(h).__name__
        # Check the class.
        if t == 'Line2D':
            # Check for empty
            if len(h.get_xdata()) == 0: continue
            # Check the min and max data
            ymin = min(ymin, min(h.get_ydata()))
            ymax = max(ymax, max(h.get_ydata()))
        elif t == 'PolyCollection':
            # Get the path.
            P = h.get_paths()[0]
            # Get the coordinates.
            ymin = min(ymin, min(P.vertices[:,1]))
            ymax = max(ymax, max(P.vertices[:,1]))
    # Process margins
    ym = kw.get('ym', ypad)
    yp = kw.get('yp', ypad)
    # Check for identical values
    if ymax - ymin <= 0.05*(ym+yp):
        # Expand by manual amount.
        ymax += yp*ymax
        ymin -= ym*ymin
    # Add padding.
    yminv = (1+ym)*ymin - ym*ymax
    ymaxv = (1+yp)*ymax - yp*ymin
    # Output
    return yminv, ymaxv
    
# Function to automatically get inclusive data limits.
def get_xlim(ha, xpad=0.05, **kw):
    """Calculate appropriate *x*-limits to include all lines in a plot
    
    Plotted objects in the classes :class:`matplotlib.lines.Lines2D` are
    checked.
    
    :Call:
        >>> xmin, xmax = get_xlim(ha, pad=0.05)
    :Inputs:
        *ha*: :class:`matplotlib.axes.AxesSubplot`
            Axis handle
        *xpad*: :class:`float`
            Extra padding to min and max values to plot.
        *xm*: :class:`float`
            Padding on minimum side
        *xp*: :class:`float`
            Padding on maximum side
    :Outputs:
        *xmin*: :class:`float`
            Minimum *x* coordinate including padding
        *xmax*: :class:`float`
            Maximum *x* coordinate including padding
    :Versions:
        * 2015-07-06 ``@ddalle``: First version
    """
    # Initialize limits.
    xmin = np.inf
    xmax = -np.inf
    # Loop through all children of the input axes.
    for h in ha.get_children():
        # Get the type.
        t = type(h).__name__
        # Check the class.
        if t == 'Line2D':
            # Check for empty
            if len(h.get_xdata()) == 0: continue
            # Check the min and max data
            xmin = min(xmin, min(h.get_xdata()))
            xmax = max(xmax, max(h.get_xdata()))
        elif t == 'PolyCollection':
            # Get the path.
            P = h.get_paths()[0]
            # Get the coordinates.
            xmin = min(xmin, min(P.vertices[:,0]))
            xmax = max(xmax, max(P.vertices[:,0]))
    # Process margins
    xm = kw.get('xm', xpad)
    xp = kw.get('xp', xpad)
    # Check for identical values
    if xmax - xmin <= 0.05*(xm+xp):
        # Expand by manual amount.
        xmax += xp*xmax
        xmin -= xm*xmin
    # Add padding.
    xminv = (1+xm)*xmin - xm*xmax
    xmaxv = (1+xp)*xmax - xp*xmin
    # Output
    return xminv, xmaxv
    
# Function to automatically get inclusive data limits.
def get_ylim_ax(ha, ypad=0.05, **kw):
    """Calculate appropriate *y*-limits to include all lines in a plot
    
    Plotted objects in the classes :class:`matplotlib.lines.Lines2D` and
    :class:`matplotlib.collections.PolyCollection` are checked.
    
    This version is specialized for equal-aspect ratio axes.
    
    :Call:
        >>> ymin, ymax = get_ylim_ax(ha, ypad=0.05, ym=None, yp=None)
    :Inputs:
        *ha*: :class:`matplotlib.axes.AxesSubplot`
            Axis handle
        *ypad*: {``0.05``} | :class:`float`
            Extra padding to min and max values to plot
        *ym*: :class:`float`
            Padding on minimum side
        *yp*: :class:`float`
            Padding on maximum side
    :Outputs:
        *ymin*: :class:`float`
            Minimum *y* coordinate including padding
        *ymax*: :class:`float`
            Maximum *y* coordinate including padding
    :Versions:
        * 2015-07-06 ``@ddalle``: First version
        * 2016-06-10 ``@ddalle``: Moved to :mod:`cape.util`
    """
    # Initialize limits.
    xmin = np.inf
    xmax = -np.inf
    ymin = np.inf
    ymax = -np.inf
    # Loop through all children of the input axes.
    for h in ha.get_children():
        # Get the type.
        t = type(h).__name__
        # Check the class.
        if t == 'Line2D':
            # Check for empty
            if len(h.get_xdata()) == 0: continue
            # Check the min and max data
            xmin = min(xmin, min(h.get_xdata()))
            xmax = max(xmax, max(h.get_xdata()))
            ymin = min(ymin, min(h.get_ydata()))
            ymax = max(ymax, max(h.get_ydata()))
        elif t == 'PolyCollection':
            # Get the path.
            P = h.get_paths()[0]
            # Get the coordinates.
            xmin = min(xmin, min(P.vertices[:,0]))
            xmax = max(xmax, max(P.vertices[:,0]))
            ymin = min(ymin, min(P.vertices[:,1]))
            ymax = max(ymax, max(P.vertices[:,1]))
    # Process margins
    ym = kw.get('ym', ypad)
    yp = kw.get('yp', ypad)
    # Check for identical values
    if ymax - ymin <= 0.05*(ym+yp):
        # Expand by manual amount.
        ymax += yp*ymax
        ymin -= ym*ymin
    # Add padding.
    yminv = ymin - ym*max(xmax-xmin, ymax-ymin)
    ymaxv = ymax + yp*max(xmax-xmin, ymax-ymin)
    # Output
    return yminv, ymaxv
    
# Function to automatically get inclusive data limits.
def get_xlim_ax(ha, xpad=0.05, **kw):
    """Calculate appropriate *x*-limits to include all lines in a plot
    
    Plotted objects in the classes :class:`matplotlib.lines.Lines2D` are
    checked.
    
    This version is specialized for equal-aspect ratio axes.
    
    :Call:
        >>> xmin, xmax = get_xlim_ax(ha, pad=0.05)
    :Inputs:
        *ha*: :class:`matplotlib.axes.AxesSubplot`
            Axis handle
        *xpad*: :class:`float`
            Extra padding to min and max values to plot.
        *xm*: :class:`float`
            Padding on minimum side
        *xp*: :class:`float`
            Padding on maximum side
    :Outputs:
        *xmin*: :class:`float`
            Minimum *x* coordinate including padding
        *xmax*: :class:`float`
            Maximum *x* coordinate including padding
    :Versions:
        * 2015-07-06 ``@ddalle``: First version
    """
    # Initialize limits.
    xmin = np.inf
    xmax = -np.inf
    ymin = np.inf
    ymax = -np.inf
    # Loop through all children of the input axes.
    for h in ha.get_children():
        # Get the type.
        t = type(h).__name__
        # Check the class.
        if t == 'Line2D':
            # Check for empty
            if len(h.get_xdata()) == 0: continue
            # Check the min and max data
            xmin = min(xmin, min(h.get_xdata()))
            xmax = max(xmax, max(h.get_xdata()))
            ymin = min(ymin, min(h.get_ydata()))
            ymax = max(ymax, max(h.get_ydata()))
        elif t == 'PolyCollection':
            # Get the path.
            P = h.get_paths()[0]
            # Get the coordinates.
            xmin = min(xmin, min(P.vertices[:,0]))
            xmax = max(xmax, max(P.vertices[:,0]))
            ymin = min(ymin, min(P.vertices[:,1]))
            ymax = max(ymax, max(P.vertices[:,1]))
    # Process margins
    xm = kw.get('xm', xpad)
    xp = kw.get('xp', xpad)
    # Check for identical values
    if xmax - xmin <= 0.05*(xm+xp):
        # Expand by manual amount.
        xmax += xp*xmax
        xmin -= xm*xmin
    # Add padding.
    xminv = xmin - xm*max(xmax-xmin, ymax-ymin)
    xmaxv = xmax + xp*max(xmax-xmin, ymax-ymin)
    # Output
    return xminv, xmaxv

