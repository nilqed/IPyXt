#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#-------------------------------------------------------------------------------
# Copyright 2011 SciOS Scientific Operating Systems GmbH.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted.
#
# THIS SOFTWARE IS PROVIDED BY SciOS GMBH ''AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL SciOS GMBH OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#-------------------------------------------------------------------------------
#BSD(0)
#Rev:
# - TeX2 replaced by the texprt version (pipe to stdin of tex/latex).
#   No temp files anymore, all output to 'texput' which is cleared
#   immediately after read-in of pngfile.
# - Replaced cfg dict by fs class.
# - yaml conversion of docstrings (yaml.load_all)
#

"""
#YAML
---
Usage: load_ext %sympyprt

Description:
  Magic: This defines a magic command %sympyprt to control the TeX rendering.
   Note that we omit the '%' in what follows.
   sympyprt on|off ................... turn rendering on/off
   sympyprt help ..................... show a help text
   sympyprt use simple|mplib|latex ... set the rendering method
   sympyprt <parameter> <value> ...... change a parameter

  Examples:
    sympyprt fontsize 12        ;; set font size to 12 pt
    sympyprt textcolor Red      ;; set text color to red
    sympyprt backcolor Yellow   ;; set background color to yellow
                                   (default is Transparent)
    sympyprt resolution 150     ;; set image resolution to 150 dpi
    sympyprt imagsize bbox      ;; set image size to bbox = bounding box
                                   useful if offset is used
    sympyprt imagesize tight    ;; no border around content (tight). This is
                                   the default.
    sympyprt imagesize 2cm,3cm  ;; set the image size to 2x3 cm. There must
                                   be no whitespace within the dimension pair.
    sympyprt offset -2cm,-1cm   ;; set the offset of the content within the
                                   image.
    sympyprt reset config       ;; reset config to factory settings
    sympyprt reset cache        ;; clear cache and delete all png files from
                                   the temp dir.
    sympyprt matrix v           ;; set matrix border; p,v,b,V,B,small
    sympyprt breqn on           ;; use the breqn package; on/off
    sympyprt mode equation      ;; choose mode; inline, equation, equation*

Advanced usage:
  To access the internals do as follows (for example):
    from sympyprt import *
    fs .................. factory settings (class)
    gcfg ................ global config (instance of fs)
    ObjCache ............ display the object cache (this is a dict)
                          ObjCache[id(<sympy_object>)] -> TeX instance
                          There are also exposed manipulation functions
                          like putObj, getObj, hasObj, getPNG ...
    gcfg = fs() ......... reset the global cfg to factory settings

    TeX0, TeX1, TeX2 .... To test the rendering one can use the different
                          classes as follows, e.g.
                          p = TeX2('$$\hbar^2$$') --> p
                          this should show up the png image by the
                          _repr_png_ method (only in IPy or RTy of course).

Examples:
  - for x in ObjCache.values():
      print x.tex # the TeX code of the object

  - from sympyprt import TeX2 as tex
      tex(r'This text was rendered with \LaTeX')

Magic name:
  If one prefers another name for the %sympyprt magic change the global
  variable fs._magic in the code below.

Note:
  Many (if not most) objects are cached with its 'id'. When typing
  _n ([n] = IPy output number) a cached image will be shown. There
  are several methods to redraw the image;
        1. delete it from the cache
        2. get the instance from the cache and use its render() method
           e.g. x.render(x.cfg) => new x.png (if x.cfg was modified).
        3. delete the original object, so that simpy creates a new one (id)

Credit(s):
  based on ipython/extensions/sympyprinting.py by Brian Granger
"""

__author__ = "Kurt Pagani <pagani@scios.ch>"
__hg_set__ = "1:6926697fdc23"
__loc_id__ = "hg.scios.ch/py_site_scios_tex"

#;;;;;;;;;;;;
# Imports ;;;
#;;;;;;;;;;;;
import os, os.path
import re

from subprocess import Popen, PIPE
from copy import copy

from IPython.lib.latextools import latex_to_png
from matplotlib.mathtext import MathTextParser, MathtextBackendBitmap
from sympy import latex ,pretty
from StringIO import StringIO
from base64 import encodestring


#;;;;;;;;;;;;;;;;;;;;;
# Factory settings ;;;
#;;;;;;;;;;;;;;;;;;;;;
class fs: pass
fs._active = True
fs._magic = 'sympyprt'
fs._loaded = False
fs._methods = ['simple', 'mplib', 'latex']
fs._use = 'latex'
fs._params = ['fontsize', 'resolution', 'imagesize', 'textcolor',
              'backcolor', 'offset', 'reset']

fs.latex = 'latex'
fs.dvipng = 'dvipng'

fs.fontsize = 10
fs.resolution = 140
fs.imagesize = 'tight'
fs.backcolor = 'Transparent'
fs.forecolor = 'Blue'
fs.offset = '0cm,0cm'
fs.mode = 'equation*' #inline|equation|equation*
fs.matrix = 'b'
fs.breqn = False
fs.initrender = True

fs.preamble = r'''\documentclass[%ipt]{article}
\usepackage{amsmath,amssymb}
\usepackage{breqn}
\pagestyle{empty}
\begin{document}
%s
\end{document}'''

fs.latexcmd = r"{0} -halt-on-error"
fs.dvipngcmd = r"{0} -T {1} -D {2:d} -bg {3} -fg {4} -O {5} -o {6} {7}"

fs.jobname = 'texput'
fs.dvifile = fs.jobname + '.dvi'
fs.pngfile = fs.jobname + '.png'

fs.exts = ['dvi','aux','png','log'] # removed

fs.errdvipng = 'Error (dvipng): use the log property for more information.'
fs.errlatex = 'Error (latex): use the log property for more information.'

fs.configscript = None


def paramap(c):
  return {
  'fontsize'   : c.fontsize,
  'resolution' : c.resolution,
  'imagesize'  : c.imagesize,
  'backcolor'  : c.backcolor,
  'textcolor'  : c.forecolor,
  'offset'     : c.offset,
  'mode'       : c.mode,
  'matrix'     : c.matrix,
  'breqn'      : c.breqn,
  'method'     : c._use,
  'preamble'   : c.preamble}


#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
# The factory settings may be overwritten here. ;;;
# Optional configscript: fs.configscript        ;;;
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
try:
  execfile(fs.configscript)
except:
  pass

#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
# Global config obj (instance of fs) ;;;
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
gcfg = fs()


#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
# Cache + manipulation functions ;;;
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
ObjCache = {}
def putObj(x, y): ObjCache[id(x)] = y
def getObj(x): return ObjCache[id(x)]
def hasObj(x): return ObjCache.has_key(id(x))
def getPNG(x): return getObj(x).png
def clearCache(): ObjCache.clear()


#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
# Preps for the magic command ;;;
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

fs.magic_help_text =\
"""Usage: %sympyprt on | off | help | use ?m | ?p ?v
 ?m : method
  simple ...... use IPython's latex_to_png method (no options)
  mplib ....... use matplotlib (options: fontsize, textcolor, resolution)
  latex ....... use LaTeX/dvipng. Options are: fontsize, textcolor,
                resolution, imagesize, backcolor and offset.

 ?p : parameter, ?v : value
  fontsize .... set the fontsize (unit: pt), ?v:Integer (default 11)
  resolution .. set the resolution (unit: dpi), ?v:Integer (default 140)
  imagesize ... set the image size. ?v may be tight, bbox or
                a comma separated dimension pair: e.g. 4cm,2cm
                ** No whitespace between characters! Default is tight.
  textcolor.... set the foreground color. ?v:colorname, e.g. Red, Blue
  backcolor ... set the background color. ?v:colorname, e.g. Yellow
  offset ...... offset for image content. ?v: a comma separated dimension
                pair: e.g. -1cm,-2cm (No whitespace between characters!)
  mode ........ ?v : inline|equation|equation*
  matrix ...... matrix type: ?v : p|v|b|V|B|small (as in LaTeX: ?v-matrix)
  breqn ....... use the breqn package: ?v : on|off
  reset ....... ?v : config|cache;
                config: reset the global cfg (gcfg) to factory settings (fs).
                cache: clear the cache
  show ........ ?v : most ?p above|method|preamble;
                Show current parameter settings; ex. %sympyprt show fontsize
*EOI*
"""

#
# Function to switch the sympyprt_active variable True/False and printing a
# help text.
#
def _fswitch(arg):
  d = {True : 'on', False : 'off'}
  if arg == 'on':
    gcfg._active = True
  elif arg == 'off':
    gcfg._active = False
  elif arg == 'help':
    print fs.magic_help_text
  else:
    print 'Usage: %s on|off|help|use ?m|?p ?v' % ('%' + gcfg._magic)
    print 'Current state: %s' % d[gcfg._active]

#
# Function  to set the render method
#
def _fmethod(arg):
  if arg in fs._methods:
    gcfg._use = arg
  else:
    print 'Usage: %s use %s' % (('%' + gcfg._magic), '|'.join(gcfg._methods))
    print 'Current method: %s' % gcfg._use

#
# Function to set parameters
#
def _fparams(p, v):
  global ObjCache
  if p == 'fontsize':
    gcfg.fontsize = int(v)
  elif p == 'resolution':
    gcfg.resolution = int(v)
  elif p == 'imagesize':
    gcfg.imagesize = v
  elif p == 'textcolor':
    gcfg.forecolor = v.capitalize()
  elif p == 'backcolor':
    gcfg.backcolor = v.capitalize()
  elif p == 'offset':
    gcfg.offset = v
  elif p == 'matrix':
    gcfg.matrix = v
  elif p == 'mode':
    gcfg.mode = v
  elif p == 'breqn':
    d = {'on':True, 'off':False}
    if v  in d.keys():
      gcfg.breqn = d[v]
  elif p == 'show':
    if v in paramap(gcfg).keys():
      print paramap(gcfg)[v]
    elif v == 'all':
      for s in paramap(gcfg).keys():
        print "{:<12} ....... {}".format(s, paramap(gcfg)[s])
    else:
      print fs.magic_help_text
  elif p == 'reset':
    if v == 'config':
      gfcg = fs()
    elif v == 'cache':
      clearCache()
  else:
    print 'Usage: %s %s ?value' % (('%' + gcfg._magic), '|'.join(gcfg._params))


def _fmagic(self, *args):
  a = args[0].split()
  l = len(a)
  if l == 0:
    _fswitch('none')
  elif l == 1:
    _fswitch(a[0])
  elif l == 2:
    if a[0] == 'use':
      _fmethod(a[1])
    else:
      _fparams(a[0], a[1])


#;;;;;;;;;;;;;;;
# IPy magics ;;;
#;;;;;;;;;;;;;;;

#
# Define an IPython magic command: %sympyprt on|off ...
#
try:
  ip = get_ipython()
  ip.define_magic(gcfg._magic, _fmagic)
except:
  pass


#;;;;;;;;;;;;;;;
# Class TeX0 ;;;
#;;;;;;;;;;;;;;;
class TeX0():
  """
  Render TeX code with IPython lib latextools (not many options here ;)
  """
  def __init__(self, s, encode = False):
    self.png = latex_to_png(s, encode)
  def _repr_png_(self):
    return self.png


#;;;;;;;;;;;;;;;
# Class TeX1 ;;;
#;;;;;;;;;;;;;;;
class TeX1():
  """
  Render TeX code with matplotlib mathtext. Doesn't need a LaTeX installation.
  @enocde ........ Enocde base64
  @init_render ... Render the PNG image when creating an instance.
  """
  def __init__(self, src, encode = False, cfg = fs()):

    self.cfg = copy(cfg)
    self.src = src
    self.encode = encode
    self.png = None

    if self.cfg.initrender:
      self.render(self.cfg)

  def render(self, cfg):
    self.mtp = MathTextParser('bitmap')
    f = StringIO()
    self.mtp.to_png(f, self.src, cfg.forecolor, cfg.resolution, cfg.fontsize)
    bin_data = f.getvalue()
    if self.encode:
      bin_data = encodestring(bin_data)
    self.png = bin_data
    f.close()

  def _repr_png_(self):
    return self.png


#;;;;;;;;;;;;;;;
# Class TeX2 ;;;
#;;;;;;;;;;;;;;;
class TeX2():
  """
  Convert TeX code to a PNG image via dvi using the 'dvipng' command.
  Credit: dvipng 1.XX Copyright 2002-2008 Jan-Ake Larsson
  Details: http://www.nongnu.org/dvipng/dvipng_4.html
  -- This is by far the shortest and fastest version (compared to older TeX2).
  """

  def __init__(self, src, cfg = gcfg):
    """
    The parameter src should be TeX code without preamble and without begin/end
    document commands. The optional parameter cfg can be a modified instance
    of the factory settings class fs.
    """

    # Copy cfg (otherwise changes to cfg affect the whole class)
    self.cfg = copy(cfg)
    self.src = src

    # Log (subprocess/communicate output in case of errors)
    self.log = None

    # The PNG file
    self.pngfile = None

    # The PNG image (string/x89PNG)
    self.png = None

    # Render now or later?
    if cfg.initrender:
      self.render(self.cfg)


  def render(self, cfg):
    """
    Run latex then convert the dvi output to png. The mandatory cfg
    has to be an instance of fs (usually self.cfg).
    """
    # Default template
    self.preamble = cfg.preamble % (cfg.fontsize, self.src)

    # LaTeX command
    self.latex = cfg.latexcmd.format(cfg.latex)

    # Dvipng command
    self.dvipng = cfg.dvipngcmd.format(cfg.dvipng, cfg.imagesize,
      cfg.resolution, cfg.backcolor, cfg.forecolor, cfg.offset,
      cfg.pngfile, cfg.dvifile)

    # Note: going to write to latex's stdin => needs to be piped
    p = Popen(self.latex, shell = True, stdin = PIPE, stdout = PIPE)

    # Send input & read stdout/stderr
    log = p.communicate(cfg.preamble % (cfg.fontsize, self.src))

    # Check for errors (<>0)
    if  p.returncode != 0:
      print cfg.errlatex
      self.log = log
      self.cleanup()
      return

    # Run the dvi to png conversion
    p = Popen(self.dvipng, shell = True, stdout = PIPE)

    # Read stdout/stderr
    log = p.communicate()

    # Check for errors (<>0)
    if p.returncode != 0:
      print cfg.errdvipng
      self.log = log
      self.cleanup()
      return

    # Set the png image path
    self.pngfile = cfg.pngfile

    # Read and store the PNG image (use binary read)
    f = open(self.pngfile, 'rb')
    self.png = f.read()
    f.close()

    # Remove all output files
    self.cleanup()


  def cleanup(self):
    """
    Remove all fs.jobname{fs.exts} files and reset pngfile to None.
    """
    try:
      for f in map(lambda x: self.cfg.jobname + '.' + x, self.cfg.exts):
        os.remove(f)
    except:
      pass
    self.pngfile = None


  def save_src(self, filename):
    """
    Save the TeX source to filename.
    """
    try:
      f = open(filename,'w')
      f.write(self.src)
      f.close()
      return True
    except:
      return False


  def save_png(self, filename):
    """
    Save the PNG image to filename.
    """
    try:
      f = open(filename, 'wb')
      f.write(self.png)
      f.close()
      return True
    except:
      return False


  def change_src(self, src, redraw = False):
    """
    Change the src input string (use raw string).
    If redraw = True then the image will be re-rendered. On the other
    hand you can do this manually by x.render(x.cfg), where x is the
    instance name (e.g. if you want to change several parameters).
    """
    self.src = src
    if redraw: self.render(self.cfg)


  def change_colors(self, forecolor, backcolor, redraw = False):
    """
    Change fore/back color. E.g. 'Transparent', 'Blue', 'Green' ...
    If redraw = True then the image will be re-rendered. On the other
    hand you can do this manually by x.render(x.cfg), where x is the
    instance name (e.g. if you want to change several parameters).
    """
    self.cfg.forecolor = forecolor
    self.cfg.backcolor = backcolor
    if redraw: self.render(self.cfg)


  def change_fontsize(self, dpi, pt, redraw = False):
    """
    The displayed fontsize depends on the resolution (dpi) and the
    pointsize in the latex preamble (pt). Usually the values range
    in: dpi = 100 ... 150, pt = 10,11,12.
    If redraw = True then the image will be re-rendered. On the other
    hand you can do this manually by x.render(x.cfg), where x is the
    instance name (e.g. if you want to change several parameters).
    """
    self.cfg.fontsize = pt
    self.cfg.resolution = dpi
    if redraw: self.render(self.cfg)


  def change_imagesize(self, imagesize, redraw = False):
    """
    Change image size (dimension pair like '2cm,3cm' or 'bbox' or 'tight')
    If redraw = True then the image will be re-rendered. On the other
    hand you can do this manually by x.render(x.cfg), where x is the
    instance name (e.g. if you want to change several parameters).
    """
    self.cfg.imagesize = imagesize
    if redraw: self.render(self.cfg)


  def _repr_png_(self):
    """
    Representation as png image (returns the image code).
    """
    return self.png


#;;;;;;;;;;;;;;;;;;;;;;;
# Printing functions ;;;
#;;;;;;;;;;;;;;;;;;;;;;;

def print_basic_unicode(o, p, cycle):
  """
  A function to pretty print sympy Basic objects.
  """
  if cycle:
    return p.text('Basic(...)')
  out = pretty(o, use_unicode = True)
  if '\n' in out:
    p.text(u'\n')
  p.text(out)


def print_png0(obj):
  """
  Display sympy expression using TeX0.
  """
  if not gcfg._active: return None
  s = latex(obj, mode = 'inline')
  s = s.replace('\\operatorname','')
  s = s.replace('\\overline', '\\bar')
  png = TeX0(s).png
  return png


def print_png1(obj):
  """
  Display sympy expression using TeX1.
  """
  if not gcfg._active: return None
  s = latex(obj, mode = 'inline')
  s = s.replace('\\operatorname','')
  s = s.replace('\\overline', '\\bar')
  png = TeX1(s).png
  return png


def print_png2(self):
  """
  Display sympy expression using TeX2.
  """
  if not gcfg._active: return None
  if hasObj(self):
    return getPNG(self) #cached img
  else:
    try:
      s = latex(self, mode = '%s' % gcfg.mode)
      #s = s.replace('smallmatrix','bmatrix') #v, V, b, B, p
      s = s.replace('\\left(\\begin{smallmatrix}',
                    '\\begin{%smatrix}' % gcfg.matrix)
      s = s.replace('\\end{smallmatrix}\\right)',
                    '\\end{%smatrix}' % gcfg.matrix)
      # breqn
      if gcfg.breqn:
        s = s.replace('{equation*}', '{dmath*}')

      repr_obj = TeX2(s)
      putObj(self, repr_obj)
      return repr_obj.png
    except:
      return None


def print_png(obj):
  """
  Depending on method (_use) activate the corresponding function.
  """
  if gcfg._use == 'simple':
    return print_png0(obj)
  elif gcfg._use == 'mplib':
    return print_png1(obj)
  elif gcfg._use == 'latex':
    return print_png2(obj)
  else:
    return None

#;;;;;;;;;;;;;;;;;
# IPy Extension;;;
#;;;;;;;;;;;;;;;;;

def load_ipython_extension(ip):
  """
  Load the extension in IPython.
  """
  if not gcfg._loaded:
    plaintext_formatter = ip.display_formatter.formatters['text/plain']

    for cls in (object, tuple, list, set, frozenset, dict, str):
        plaintext_formatter.for_type(cls, print_basic_unicode)

    plaintext_formatter.for_type_by_name('sympy.core.basic', 'Basic',
      print_basic_unicode)
    plaintext_formatter.for_type_by_name('sympy.matrices.matrices',
      'Matrix', print_basic_unicode)

    png_formatter = ip.display_formatter.formatters['image/png']
    png_formatter.for_type_by_name('sympy.matrices.matrices','Matrix', print_png)
    png_formatter.for_type_by_name('sympy.core.basic', 'Basic', print_png)

    gcfg._loaded = True


def main():
    pass

if __name__ == '__main__':
    main()
