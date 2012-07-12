# -*- coding: UTF-8 -*-
#!/usr/bin/env python

__author__ = "Kurt Pagani <pagani@scios.ch>"
__svn_id__ = "$Id:$"
__rev_id__ = "Rev. 24.06.2012 11:39:03"

"""
--- #YAML
Axiom0:
  - Low level class: with an instance of this class one can already
    communicate with Axiom on a send input string get output string
    basis.
Axiom1:
  - Input class
Axiom2:
    Output class
Axiom3:
    System commands

"""

import re
import sys
import time
import tempfile
import os, os.path

if os.name == 'nt':
  import winpexpect as xp
  spawn = xp.winspawn
else:
  import pexpect as xp
  spawn = xp.spawn

from IPython.core.magic import Magics, magics_class, line_magic
from IPython.core.magic import cell_magic, line_cell_magic
from IPython.core.magic_arguments import argument, magic_arguments
from IPython.core.magic_arguments import parse_argstring
from IPython.core.display import Latex, Image, display_latex, display
from termcolor import colored, cprint
from texprt import TeX

# ----------------------
# fs ; factory settings
# ----------------------
class fs:
  """
  --- #YAML: yaml.load(fs.__doc__.strip())
  Factory settings: >
    An instance of this (dummy) class is given as an argument to the
    init method of the base class and may be created e.g. internally
    or by a config file.
  """
  pass

# The name of the Axiom executable (eg. axiom, fricas, openaxiom)
# if the file is not in the system path then the full path is rquired.
# Use only forward slashes.
fs.appname = "openaxiom"

# The Axiom prompt has usually the form '(n) ->' (n an integer), so that
# the regexp pattern below should match.
fs.prompt_re = "\([0-9]+\) ->"

# Read quiet command (read in a file)
fs.cmd_read_quiet = ')read "{}" )quiet'

# Tempfile generation template (used by NamedTemporaryFile)
fs.tmpfile_kw = {'prefix':'ax$', 'suffix':'.input', 'delete':False}


# ------------------------
# Axiom ; axiom sys class
# ------------------------

class Axiom():
  """
  Axiom base class. Handle the interaction with the console
  window and provide all low level routines for a device and
  os independent subclass.
    - start, stop
    - read header/banner
    - expect prompt
    - handle i/o (send input, read output)
    - detect/manage errors
    - store history
  Note: originally this was Axiom0 now renamed and extended for this IPy
  magic. In ordinary Python use: from scios.axiom.axiomsys import ...
  """

  def __init__(self, cfg = fs()):
    """
    The argument cfg has to be an instance of the factory settings.
    E.g. cfg = mycfg, then mycfg is expected to have all porperties
    of fs.
    """

    # Publish the cfg instance
    self.cfg = cfg

    # Define the axiom process
    self.axp = None

    # The header/banner read when started
    self.banner = None

    # The current prompt
    self.prompt = None

    # Output caught after a command has been sent (always unmodified)
    self.output = None

    # Last error enountered (0: OK, 1: EOF, 2: TIMEOUT)
    self.error = None

    # Log file ([win]spawn)
    self.logfile = None


  def _axp_expect(self):
    """
    Return True if the prompt was matched otherwise return False and
    set the error=1 if EOF or error=2 if Timeout.
    """
    self.error = self.axp.expect([self.cfg.prompt_re, xp.EOF, xp.TIMEOUT])
    if self.error == 0:
      self.error = None
      return True
    else:
      return False


  def _axp_sendline(self, txt):
     """
     Send the text+os.linesep to Axiom and expect the prompt. Moreover
     reset the error state. Return is as in _axp_expect.
     """
     self.error = None
     n = self.axp.sendline(txt) #chk n>=len(txt) ?
     return self._axp_expect()


  def start(self, **kwargs):
    """
    --- #YAML
    Action: Start (spawning) Axiom.
    Return: True or False
    The following keywords (kwargs) may be used:
      args=[], timeout=30, maxread=2000, searchwindowsize=None
      logfile=None, cwd=None, env=None, username=None, domain=None
      password=None
    For details consult the pexpect manual as this parameters are the same
    as in the spawn/winspawn function respectively.
    Note: after started one may access the values as follows:
      <axiom_instance>.axp.<keyword>, e.g. a.axp.timeout -> 30.
    """
    if self.axp is None:
      self.axp = spawn(self.cfg.appname, **kwargs)
      if self._axp_expect():
        self.banner = self.axp.before
        self.prompt = self.axp.after
        return True
      else:
        return False


  def stop(self):
    """
    Stop Axiom (the hard way). One may also send the command ')quit'
    to Axiom using writeln for example.
    The return value is that of the isalive() function.
    """
    if self.axp is not None:
      self.axp.close()
      self.axp = None
    return not self.isalive()


  def isalive(self):
    """
    Check if Axiom is running.
    """
    if self.axp is not None:
      return self.axp.isalive()
    else:
      return False


  def haserror(self):
    """
    True if there was an error.
    """
    return self.error is not None


  def hasoutput(self):
    """
    True if there is output.
    """
    return self.output is not None


  def writeln(self, src):
    """
    Write a line to Axiom, i.e. as if it were entered into the interactive
    console. Output - if any - is (unmodified) stored in 'output'.
    Note: src should not contain any control characters; a newline (in fact
    os.linesep) will be added automatically. Axiom's continuation character,
    however, is no problem.
    """

    if self._axp_sendline(src):
      self.output = self.axp.before
      self.prompt = self.axp.after
      return True
    else:
      self.output = None
      return False


  def writef(self, filename):
    """
    Write the content of the file to Axiom, i.e. urge Axiom to read it in
    by itself.
    """

    if os.path.isfile(filename):
      return self.writeln(self.cfg.cmd_read_quiet.format(filename))
    else:
      return False


  def write(self, src):
    """
    Place the string src into a temp file and call writef, that is command
    Axiom to read in the temp file. Note: the temp file will be deleted
    after having been read into Axiom.
    This command allows multiline input in SPAD/Aldor form.
    """

    tmpf = tempfile.NamedTemporaryFile(**self.cfg.tmpfile_kw)
    tmpf.write(src)
    tmpf.close()
    rc = self.writef(tmpf.name)
    os.unlink(tmpf.name)
    return rc

  #+ Axiom0 ends here ; some special methods for the use of the magic %axsys.

  def get_index(self, prompt):
    """
    Return the number N in the input prompt (N) ->.
    """
    m = re.match("\(([0-9]+)\)", prompt)
    if m is not None  and len(m.groups()) == 1:
      return int(m.group(1))
    else:
      return False


  def get_type_and_value(self, output = None):
    """
    Get index, type and value in the 'output'. Default is the current output.
    """
    if output is None: output = self.output

    r = output.strip(" \n").split("Type:")
    ri = re.match("^\(([0-9]+)\)", r[0]).group(1)
    rv = re.split("^\([0-9]+\)",r[0])[1].strip(" \n")
    rv = re.sub("_\n","", rv)
    rt = r[1].strip()
    return ri, rt, rv


  def extract_types(self, data):
    """
    Extract the type(s) returned (if any).
    """
    ty = re.findall('Type:[a-zA-Z0-9_. ]*', data)
    ty = map(lambda x: x.replace('Type:',''), ty)
    return map(lambda x: x.strip(), ty)


  def extract_tex(self, data):
    """
    Extract TeX code from data.
    """
    tex = re.findall('\$\$[^\$]*\$\$', data)
    return tex


  def remove_tex(self, data, tex = []):
    """
    Remove TeX code from data.
    """
    for s in tex:
      data = data.replace(s,'')
    return data


  def split_tex(self, data):
    """
    Split the output by TeX code into text substrings .
    """
    return re.split('\$\$[^\$]*\$\$', data)


  def tex_breqn(self, tex):
    """
    Transform TeX code for using the breqn package.
    """
    # remove leqno's
    tex = re.sub(r"\\leqno\(\d*\)", "%", tex)
    tex = r"\begin{dmath*}" + "\n" + tex + "\n" + r"\end{dmath*}"
    return tex



# ------------------------------
# AxiomMagics ; cell/line magic
# ------------------------------

@magics_class
class AxiomMagics(Magics):

  def __init__(self, shell):
    super(AxiomMagics,self).__init__(shell)

    self.ax = Axiom()
    self.ax.start()
    if not self.ax.isalive:
      print "Could not start axiom"
    else:
      print self.ax.banner

    self.render = 'mathjax'


  @magic_arguments()
  @argument(
    '-h', '--help', action='append', default=[],
      help="Axiom help.")
  @argument(
    '-r', '--render', action ='store', default=[],
      help="TeX render method to use.")

  @line_magic
  def axsys(self, line):
    args = parse_argstring(self.axsys, line)

    if args.help:
      print "axiom help coming ..."

    if args.render is not None:
      self.render = args.render

  @line_magic
  def axloop(self, line):
    print 'use quit. to exit.'
    try:
      while True:
        s = raw_input(colored(self.ax.prompt, 'green')+colored(" ",'blue'))
        if s.startswith('quit.'): break
        self.ax.writeln(s)
        if self.ax.hasoutput:
          print colored(self.ax.output, 'red')
    except:
      pass


  @line_cell_magic
  def axiom(self, line, cell = None):
    if cell is None:
      self.ax.writeln(line)
    else:
      if not cell.endswith('\n'): cell += '\n'
      self.ax.write(cell)

    if self.ax.hasoutput:
      try:
        #print colored(self.ax.output, 'red')
        tex = self.ax.extract_tex(self.ax.output)
        txt = self.ax.remove_tex(self.ax.output,tex)
        typ = self.ax.extract_types(self.ax.output)
        for s in tex:
          if self.render == 'mathjax':
            #display_latex(s, True)
            s =  r"$\def\sp{^}\def\sb{_}\def\leqno(#1){}$" + s
            display(Latex(s))
          elif self.render == 'tex':
            display(TeX(s))
          elif self.render == 'raw':
            print s
          else:
            pass
        print colored(txt, 'red')
      except:
        print 'exception?'


# ---------------------------------------------
# ax_completer ; command completion for %axiom
# ---------------------------------------------
def ax_completer(self, evt):
  return [')help', ')system', ')set', ')credits']

import IPython.core.ipapi
ip = IPython.core.ipapi.get()
ip.set_hook('complete_command', ax_completer, str_key = '%axiom')


# ----------
# _loaded ?
# ----------
_loaded = False



# -----------------------
# load/unload_ipython_extension
# -----------------------
def load_ipython_extension(ip):
  """Load the extension in IPython."""
  global _loaded
  if not _loaded:
    ip.register_magics(AxiomMagics)
    _loaded = True


def unload_ipython_extension(ip):
  """Unload the extension in IPython."""
  global _loaded
  if _loaded:
    #AxiomMagics.ax.stop()
    _loaded = False