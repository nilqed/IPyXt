#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
#;;;    _____      _ ____  _____    _  _______ ____
#;;;   / ___/_____(_) __ \/ ___/    |/ / ___//  _/
#;;;   \__ \/ ___/ / / / /\__ \    |   /\__ \ / /
#;;;  ___/ / /__/ / /_/ /___/ /   /   |___/ // /
#;;; /____/\___/_/\____//____/   /_/_/____/___/
#;;;
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
#;;; $Id:: ipy_tex.py 5 2011-08-27 17:33:13Z scios                            $
#;;; (C) 1998-2011 SciOS Scientific Operating Systems GmbH
#;;; http://www.scios.ch
#;;; FOR INTERNAL USE ONLY.
#;;; HEAD URL: $HeadURL:: file:///F:/SVN/IPy/ipy_tex.py                       $
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
#;;; PROJECT ...............................: XSI
#;;; SUBPROJECT ............................: IPy
#;;; MODULE ................................: ipy_tex.py
#;;; VERSION ...............................: 0.0.1
#;;; CREATION DATE .........................: 01.01.2000
#;;; MODIFICATION DATE .....................: 16.08.2011
#;;; PROGRAMMING LANGUAGE(S) ...............: Python
#;;; INTERPRETER/COMPILER ..................: Python 2.7 r27:82525
#;;; OPERATING SYSTEM(S) ...................: WIN32 (should be OS independent)
#;;; CREATOR(S) ............................: pagani@scios.ch
#;;; CLIENT(S) .............................: scios
#;;; URL ...................................: research.scios.ch/ipy
#;;; EMAIL .................................: xps@scios.ch
#;;; COPYRIGHT .............................: (C) 2011, SciOS GmbH
#;;; LICENSE ...............................: BSD
#;;; DEPENDENCIES ..........................: IPython, LaTeX (dvipng)
#;;; IMPORTS ...............................: see import list
#;;; EXPORTS ...............................: TeX[0,1,2]
#;;; COMMENTS ..............................: IPython QT console
#;;; SHORT DESCRIPTION .....................: use _repr_png_ to display TeX
#;;; DOCUMENTATION PATH ....................: see XSI/RTy: rty_latex.py
#;;; IDE ...................................: PyScripter V 2.4.2.2
#;;; SVN REVISION ..........................: $Rev:: 5                        $
#;;; REVISION DATE .........................: $Date:: 2011-08-27 19:33:13 +02#$
#;;; REVISED BY ............................: $Author:: scios                 $
#;;; REVISION HISTORY ......................: --
#;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
#
# Copyright (c) 2011, SciOS Scientific Operating Systems GmbH
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of SciOS GmbH nor the
#      names of its contributors may be used to endorse or promote products
#      derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL SciOS GmbH BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ==============================================================================


"""
Doc:
"""

import os, os.path, re, subprocess

from IPython.lib.latextools import latex_to_png
from matplotlib.mathtext import MathTextParser, MathtextBackendBitmap
from tempfile import NamedTemporaryFile

from StringIO import StringIO
from base64 import encodestring



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
  @texstr ........ TeX code as string
  @color ......... Font color
  @dpi ........... Resolution (dots per inch)
  @fontsize ...... Font size
  @enocde ........ Enocde base64
  @init_render ... Render the PNG image when creating an instance.
                   If 'False' one has to call the render method explicitly.
  """
  def __init__(self, texstr, color = 'black', dpi = 120, fontsize = 12,
    encode=False, init_render = True):

    self.texstr = texstr
    self.color = color
    self.dpi = dpi
    self.fontsize = fontsize
    self.encode = encode
    self.init_render = init_render
    self.png = None

    if self.init_render:
      self.render()

  def render(self):
    self.mtp = MathTextParser('bitmap')
    f = StringIO()
    self.mtp.to_png(f, self.texstr, self.color, self.dpi, self.fontsize)
    bin_data = f.getvalue()
    if self.encode:
      bin_data = encodestring(bin_data)
    self.png = bin_data
    f.close()

  def set_texstr(self, texstr):
    self.texstr = texstr
    self.render()

  def set_color(self, color):
    self.color = color
    self.render()

  def set_dpi(self, dpi):
    self.dpi = dpi
    self.render()

  def set_fontsize(self, fontsize):
    self.fontsize = fontsize
    self.render()

  def set_encode(self, encode):
    self.encode = encode
    self.render()

  def _repr_png_(self):
    return self.png


#;;;;;;;;;;;;;;;
# Class TeX2 ;;;
#;;;;;;;;;;;;;;;
class TeX2():
  """
  Converts TeX code to a PNG image via dvi using 'dvipng'
  Credit: dvipng 1.XX Copyright 2002-2008 Jan-Ake Larsson
  Details: http://www.nongnu.org/dvipng/dvipng_4.html

    D = #         Output resolution
    O = c         Image offset
    T = c         Image size (also accepts '-T bbox' and '-T tight')

    bg = s        Background color (TeX-style color or 'Transparent')
    fg = s        Foreground color (TeX-style color)
    bd = #        Transparent border width in dots
    bd = s        Transparent border fallback color (TeX-style color)

    pt = #        Font size set in \documentstyle[#pt]

    cleanup = True | False ... removes .aux, .tex, .log and .dvi files.
    latex_template = Tex preambel + begin/end{document}

     # = number   f = file   s = string  * = suffix, '0' to turn off
     c = comma-separated dimension pair (e.g., 3.2in,-32.1cm)
     color-spec: ex. rgb 1.0 0.0 0.0 , 'White', 'transparent' ...

    Return value: 'False' if an error occurs (check the variables
      latex_log, dvipng_log respectively).

    It is up to the user to delete/copy/move the PNG file from its
    temporary location.
  """

  def __init__(self, tex, pt = 12, D = 150, T = 'tight', bg = 'White',
    fg = 'Blue', O = '0cm, 0cm', bd = '0', cleanup = True, init_render = True):

    self.tex = tex
    self.pt = pt
    self.D = D
    self.T = T
    self.bg = bg
    self.fg =fg
    self.O = O
    self.bd = bd
    self.cleanup = cleanup
    self.init_render = init_render


    self.latex_exe = 'latex'
    self.dvipng_exe = 'dvipng'

    self.default_template = r'''\documentclass[%ipt]{article}
\usepackage{amssymb,amsmath,bm,color}
\usepackage[latin1]{inputenc}
\usepackage{flexisym}
\usepackage{breqn}
\pagestyle{empty}
\begin{document}
%s
\end{document}'''

    self.dvipng_opt_template = "-T %s -D %i -bg %s -fg %s -O %s -bd %s"

    self.latex_template = self.default_template
    self.pngfile = None
    self.png = None

    if self.init_render:
      self.render()

  def render(self):

    # Create a named temporary file for the TeX source code
    tex_file = NamedTemporaryFile(suffix = ".tex", delete = False)
    tex_file_name = tex_file.name
    tmp_file_base = tex_file_name[:-4]

    # Create the TeX source (template % (font_size, tex_string)
    tex_input = self.latex_template % (self.pt, self.tex)

    # Write TeX input to temp file and close it
    tex_file.write(tex_input)
    tex_file.close()

    # LaTeX process
    opt = "-output-directory=" + os.path.dirname(tex_file_name)
    cmd = ('%s ' + opt + " -halt-on-error " + '%s') %  (self.latex_exe, tex_file_name)
    latex = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)


    # Read stdout/stderr
    latex_log = latex.communicate()

    if  latex.returncode != 0:
      print latex_log, cmd, opt
      return False

    # Run conversion
    pngfile = tmp_file_base + ".png"
    dvifile = tmp_file_base + ".dvi"
    opt = self.dvipng_opt_template % (self.T, self.D, self.bg, self.fg,
      self.O, self.bd)
    cmd = ('%s ' + opt + " -o %s %s") % (self.dvipng_exe, pngfile, dvifile)
    dvipng = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE)

    # Read stdout/stderr
    dvipng_log = dvipng.communicate()

    if dvipng.returncode != 0:
      print dvipng_log, cmd, opt
      return False

    # Cleanup
    if self.cleanup:
      to_remove = [tmp_file_base + ".dvi", tmp_file_base + ".aux", \
                   tmp_file_base + ".log", tmp_file_base  + ".tex"]

      for item in to_remove:
        os.remove(item)

    # Set png image path
    self.pngfile = pngfile

    # Read the image
    f = open(self.pngfile,'rb') # b may be important here
    self.png = f.read()
    f.close()

  def remove_pngfile(self):
    os.remove(self.pngfile)

  def _repr_png_(self):
    return self.png


#;;;;;;;;;;;;;;;;;;;;;;;;;
# DISPLAY TeX Function ;;;
#;;;;;;;;;;;;;;;;;;;;;;;;;
def dt(arg, m = 1):
 """
 Create a TeX instance. Try the matplotlib version first (quite fast) otherwise
 try the dvipng version (may be a little slower).
 Note: the instance is available with _n, where n is the ipy output number.
 The available attributes depend on the class used.
 """

 if m == 2: return TeX2(arg)

 try:
   return TeX1(arg)
 except:
   return TeX2(arg)


##try:
##  __IPy__ =  __IPYTHON__active
##
##except:
##  __IPy__ = None
##
##
##if __IPy__ is not None:
##  ip = get_ipython()
##
##  def _tex(self, arg):
##    #ip.ex('')
##    try:
##      return TeX1(arg)
##    except:
##      return TeX2(arg)
##
##  ip.define_magic('tex', _tex)

#;;;;;;;;;
# MAIN ;;;
#;;;;;;;;;

def main():
  X=TeX1(r"$\sum_{n=0}^\infty A_n \forall x \in \Lambda$", 'blue', 120, 10)

if __name__ == '__main__':
  main()

