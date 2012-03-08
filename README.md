IP[y] Extensions (IPyXt)
========================
Some extensions for the [IPython](http://ipython.org/ "IPython") interactive
computing environment (especially for `qtconsole` and  `notebook` mode).


sympyprt
--------
This is a single file (sympyprt.py) extension for 
[SymPy](http://sympy.org/en/index.html "SymPy") - the *Python* library for
symbolic mathematics. 

## Purpose
`sympyprt` is a SymPy printer extension which renders the output (provided
that you are using `ipython qtconsole` or `ipython notebook`) of SymPy to
a LaTeX compiled inline image.

## Prerequisites
A complete IPython installation (details @ ipython.org):

* IPython 0.11+ (with PyQT4, ZMQ)
* tornado (IPython 0.12+, for notebook)
* LaTeX distribution with `latex` and `dvipng` commands (in the system path!)
* Several addtional LaTeX packages: 
  * breqn
  * amssymb
  * amsmath
  * bm
  * color
  * flexisym

Some are not really necessary and can be removed by editing the code (TeX2).

The `breqn` package is used to split very long output.

## Installation
Copy the file `sympyprt.py` (possibly after editing) into the IPython 
`extension` directory. 

Usually: `site-packages/IPython/extensions`.

## Usage
Load the extension with the IPython magic:

    %load_ext sympyprt
    
This defines also a magic command `%sympyprt` to control the TeX rendering: 

    %sympyprt on|off ................... turn rendering on/off
    %sympyprt help ..................... show a help text
    %sympyprt use simple|mplib|latex ... set the rendering method
    %sympyprt <parameter> <value> ...... change a parameter


*Some examples*:
    
    %sympyprt fontsize 12        ;; set font size to 12 pt
    %sympyprt textcolor Red      ;; set text color to red
    %sympyprt backcolor Yellow   ;; set background color to yellow
                                    (default is Transparent)
    %sympyprt resolution 150     ;; set image resolution to 150 dpi
    %sympyprt imagsize bbox      ;; set image size to bbox = bounding box
                                    useful if offset is used
    %sympyprt imagesize tight    ;; no border around content (tight). This is
                                    the default.
    %sympyprt imagesize 2cm,3cm  ;; set the image size to 2x3 cm. There must
                                    be no whitespace within the dimension pair.
    %sympyprt offset -2cm,-1cm   ;; set the offset of the content within the
                                    image.
    %sympyprt reset config       ;; reset config to factory settings
    %sympyprt reset cache        ;; clear cache and delete all png files from
                                    the temp dir.
    %sympyprt matrix v           ;; set matrix border: p,v,b,V,B,small
    %sympyprt breqn on           ;; use the breqn package: on/off
    @sympyprt mode equation      ;; choose mode: inline, equation, equation*   


## Advanced usage
There is a picture cache avoiding rendering the same output again and again 
(i.e inspecting the history).

To access the internals do as follows (for example):

    from sympyprt import *
    cfg ...................... show configuration dictionary
                               values may be changed directly or with
                               the set_<parameter> functions.
    ObjCache ................. display the object cache (this is a dict)
                               full access
                               ObjCache[id(<sympy_object>)] -> TeX instance
                               -> can be re-rendered with different parameters
                               or deleted ....
                               There are also exposed manipulation functions
                               like putObj, getObj, hasObj, getPNG ...
    cfg_reset ................ reset the cfg dict to factory settings

    TeX0, TeX1, TeX2 ......... To test the rendering one can use the different
                               classes as follows, e.g.:
                               p = TeX2('$$\hbar^2$$') --> p

    Example:

    for x in ObjCache.values():
      print x.tex # the TeX code of the object

    for x in ObjCache.values():
      print x.pngfile # the png file names in the temp dir

    from sympyprt import TeX2 as tex
    tex(r'This text was rendered with \LaTeX')


## Notes
Magic name:

If one prefers another name for the `%sympyprt magic`, change the global
variable `_magic` in the code below.

if the `latex` method is used all the png images are stored in the
user's temp directory. The LaTeX source and aux files will be cleared
(provided that cleanup is True) but not the images. Either use the 
`remove_pngfile` method of the TeX2 class or clear the temp directory manually.

    NT: !dir %temp% -> show the content of the temp dir
    
Many (if not most) objects are cached with its 'id'. When typing

    _n ([n] = IPy output number) a cached image will be shown. There
    are several methods to redraw the image:
    
     1. delete it from the cache
     2. get the instance from the cache and use its render() method
     3. delete the original object, so that simpy creates a new one (id)


## Sample output
[QT sample (HTML](http://edu.scios.ch/sympy/qt_sample_sympy.html)

[Notebook sample (ipynb)](http://edu.scios.ch/sympy/nb_sample_sympy.ipynb) 


## Credits
based on ipython/extensions/sympyprinting.py by Brian Granger

dvipng 1.XX Copyright 2002-2008 Jan-Ake Larsson

