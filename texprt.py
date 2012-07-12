# -*- coding: UTF-8 -*-
#!/usr/bin/env python

#Todo: src decoration/pre processing
#Todo: modes: equation, ....
#Todo: doku/beamer/pager/online/link ....
#Todo: caching for ipy_print ext

__author__ = "Kurt Pagani <pagani@scios.ch>"
__svn_id__ = "$Id:$"
__hg_set__ = "1:6926697fdc23"
__rev_id__ = "Rev. Fri Jun 08 09:11:49 2012 +0200"
__loc_id__ = "hg.scios.ch/py_site_scios_tex"

#;;;;;;;;;;;;
# Imports ;;;
#;;;;;;;;;;;;
import os, os.path
import re

from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from copy import copy


#;;;;;;;;;;;;;;;;;;;;;
# Factory settings ;;;
#;;;;;;;;;;;;;;;;;;;;;
class fs: pass
fs._active = True
fs._magic = 'texprt'
fs._loaded = False
fs._params = []

fs.latex = 'latex'
fs.dvipng = 'dvipng'

fs.fontsize = 12
fs.resolution = 150
fs.imagesize = 'tight'
fs.backcolor = 'Transparent'
fs.forecolor = 'Blue'
fs.offset = '0cm,0cm'
fs.mode = 'equation'
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

#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
# Cache + manipulation functions ;;;
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
ObjCache = {}
def putObj(x, y): ObjCache[id(x)] = y
def getObj(x): return ObjCache[id(x)]
def hasObj(x): return ObjCache.has_key(id(x))
def getPNG(x): return getObj(x).png
def clearCache(): ObjCache.clear()


#;;;;;;;;;;;;;;
# Class TeX ;;;
#;;;;;;;;;;;;;;
class TeX():
  """
  Convert TeX code to a PNG image via dvi using the 'dvipng' command.
  Credit: dvipng 1.XX Copyright 2002-2008 Jan-Ake Larsson
  Details: http://www.nongnu.org/dvipng/dvipng_4.html
  -- This is by far the shortest and fastest version (compared to TeX2).
  """

  def __init__(self, src, cfg = fs()):
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





def main():
  pass

if __name__ == '__main__':
  main()
