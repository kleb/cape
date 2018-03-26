"""
:mod:`pyOver.tecplot`: Interface to OVERFLOW Tecplot scripts 
============================================================

This is a module built off of the :mod:`cape.fileCntl` module customized for
manipulating Tecplot layout files and macros.  The OVERFLOW version of this
module is based off of the generic version :mod:`cape.tecplot` with minimal
modifications.

The module allows users to edit quantities of any layout command in addition to
declaring and adding layout variables. In addition, the :func:`ExportLayout`
function provides a utility to open a layout using Tecplot in batch mode to
export an image.

The class provides two classes, the first of which is the generic version
typically used for layout files.  The second class has a few extra methods for
handling Tecplot macros specifically.

    * :class:`pyOver.tecplot.Tecsript`
    * :class:`pyOver.tecplot.TecMacro`

:See also:
    * :mod:`cape.fileCntl`
    * :mod:`cape.report`
"""

# Import the base file control class.
import cape.tecplot


# Stand-alone function to run a Tecplot layout file
def ExportLayout(lay="layout.lay", fname="export.png", fmt="PNG", w=None):
    """Stand-alone function to open a layout and export an image
    
    :Call:
        >>> ExportLayout(lay="layout.lay", fname="export.png", fmt="PNG", w=None)
    :Inputs:
        *lay*: {``"layout.lay"``} | :class:`str`
            Name of Tecplot layout file
        *fname*: {``"export.png"``} | :class:`str`
            Name of image file to export
        *fmt*: {``"PNG"``} | ``"JPG"`` | :class:`str`
            Valid image format for Tecplot export
        *w*: {``None``} | :class:`float`
            Image width in pixels
    :Versions:
        * 2015-03-10 ``@ddalle``: First version
    """
    cape.tecplot.ExportLayout(lay=lay, fname=fname, fmt=fmt, w=w)
    
# Aerodynamic history class
class Tecscript(cape.tecplot.Tecscript):
    """
    File control class for Tecplot script files
    
    :Call:
        >>> tec = pyOver.tecplot.Tecscript()
        >>> tec = pyOver.tecplot.Tecscript(fname="layout.lay")
    :Inputs:
        *fname*: :class:`str`
            Name of Tecplot script to read
    :Outputs:
        *tec*: :class:`pyOver.tecplot.Tecscript` or derivative
            Instance of Tecplot script base class
    :Versions:
        * 2015-02-26 ``@ddalle``: Started
        * 2015-03-10 ``@ddalle``: First version
    """
    pass

# class Tecscript


# Tecplot macro
class TecMacro(cape.tecplot.TecMacro):
    """
    File control class for Tecplot macr files
    
    :Call:
        >>> tec = pyOver.tecplot.TecMacro()
        >>> tec = pyOver.tecplot.TecMacro(fname="export.mcr")
    :Inputs:
        *fname*: :class:`str`
            Name of Tecplot script to read
    :Outputs:
        *tec*: :class:`pyOver.tecplot.TecMacro`
            Instance of Tecplot macro interface
    :Versions:
        * 2015-03-10 ``@ddalle``: First version
    """
    pass

# class TecMacro

