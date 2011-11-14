#
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
import argparse
import os.path
import sys
import lsst.pex.logging as pexLog
import lsst.pex.policy as pexPolicy

__all__ = ["ArgumentParser"]

class ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser is an argparse.ArgumentParser that provides standard arguments for pipe_tasks tasks.

    These are used to populate butler, policy and idList attributes,
    in addition to standard argparse behavior.
    
    @todo: adapt for new butler:
    - Get camera name from data repository
    - Use mapper or camera name to obtain the names of the camera ID elements
    @todo: adapt for new Policy
    """
    def __init__(self, **kwargs):
        argparse.ArgumentParser.__init__(self,
            fromfile_prefix_chars='@',
            epilog="@file reads command-line options from the specified file (one option per line)",
            **kwargs)
        self.add_argument("camera", help="""name of camera (e.g. lsstSim or suprimecam)
(WARNING: this must appear before any options)""")
        self.add_argument("dataPath", help="path to data repository")
        self.add_argument("-p", "--policy", nargs="*", action=PolicyValueAction,
                        help="policy overrides", metavar="NAME=VALUE")
        self.add_argument("-o", "--override", dest="policyPath", nargs="*", action=PolicyFileAction,
                        help="policy override files")
        self.add_argument("--output", dest="outPath", help="output root directory")
        self.add_argument("--calib", dest="calibPath", help="calibration root directory")
        self.add_argument("--debug", action="store_true", help="enable debugging output?")
        self.add_argument("--log", help="logging destination")

    def parse_args(self, policy, argv=None):
        """Parse arguments for a command-line-driven task

        @params policy: default policy
        @params argv: argv to parse; if None then sys.argv[1:] is used
        """
        if argv == None:
            argv = sys.argv[1:]

        if len(sys.argv) < 2:
            sys.stderr.write("Error: must specify camera as first argument\n")
            self.print_usage()
            sys.exit(1)
        try:
            self._handleCamera(sys.argv[1])
        except Exception, e:
            sys.stderr.write("%s\n" % e)
            sys.exit(1)
            
        inNamespace = argparse.Namespace
        inNamespace.policy = policy
        namespace = argparse.ArgumentParser.parse_args(self, args=argv)
        
        if not os.path.isdir(namespace.dataPath):
            sys.stderr.write("Error: dataPath=%r not found\n" % (namespace.dataPath,))
            sys.exit(1)
            
        if namespace.debug:
            try:
                import debug
            except ImportError:
                sys.stderr.write("Warning: no 'debug' module found\n")
                namespace.debug = False

        if namespace.log != None:
            log = pexLog.Log.getDefaultLog()
            log.addDestination(namespace.log)

        return namespace

    def _handleCamera(self, camera):
        """Set attributes based on self._camera
        
        Called by parse_args before the main parser is called
        
        This is a temporary hack; ditch it once we can get this info from a data repository/
        """
        if camera in ("-h", "--help"):
            self.print_help()
            print
            raise RuntimeError("For more complete help, specify camera (e.g. lsstSim or suprimecam) as first argument\n")
        
        lowCamera = camera.lower()
        if lowCamera == "lsstsim":
#            import lsst.obs.lsstSim
#            self._mappers = lsst.obs.lsstSim.LsstSimMapper
            self._idNameCharTypeList = (
                ("visit",  "V", int),
                ("filter", "f", str),
                ("raft",   "r", str),
                ("sensor", "s", str),
            )
            self._extraFileKeys = ["channel"]
        elif lowCamera == "suprimecam":
#            import lsst.obs.suprimecam
#            self._mappers = lsst.obs.suprimecam.SuprimecamMapper
            self._idNameCharTypeList = (
                ("visit",  "V", int),
                ("ccd", "c", str),
            )
            self._extraFileKeys = []
        else:
            raise RuntimeError("Unsupported camera: %s" % camera)

        for idName, idChar, idType in self._idNameCharTypeList:
            argList = []
            if idChar:
                argList.append("-%s" % (idChar,))
            argList.append("--%s" % (idName,))
            self.add_argument(*argList, dest=idName, nargs="*", default=[],
                help="%ss to to process" % (idName,))

        self._camera = camera


# argparse callback to set a configuration value
class PolicyValueAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        """Override one or more policy name value pairs
        """
        policy = pexPolicy.Policy()
        for nameValue in values:
            name, sep, value = nameValue.partition("=")
            if not value:
                raise ValueError("%s value %s must be in form name=value" % (option_string, nameValue))
            policy.set(name, value)
#        namespace.policy.merge(policy)

# argparse callback to override configurations
class PolicyFileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        """Load one or more files of policy overrides
        """
        for policyPath in values:
            policyFile = pexPolicy.Policy(policyPath)
            namespace.policy.merge(overrideFile)
