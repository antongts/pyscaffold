#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Setup file for PyScaffold.

    This file was generated with PyScaffold, a tool that easily
    puts up a scaffold for your new Python project. Learn more under:
    http://pyscaffold.readthedocs.org/
"""

import inspect
import os
import re
import subprocess
import sys
from distutils.cmd import Command
from distutils.command.build import build as _build
from distutils.command.sdist import sdist as _sdist

import setuptools
from setuptools import setup
from setuptools.command.test import test as TestCommand

# For Python 2/3 compatibility, pity we can't use six.moves here
try:  # try Python 3 imports first
    import configparser
    from io import StringIO
except ImportError:  # then fall back to Python 2
    import ConfigParser as configparser
    from StringIO import StringIO

__location__ = os.path.join(os.getcwd(), os.path.dirname(
    inspect.getfile(inspect.currentframe())))

package = "pyscaffold"


class PyTest(TestCommand):
    user_options = [("cov=", None, "Run coverage"),
                    ("cov-report=", None, "Generate a coverage report"),
                    ("junitxml=", None, "Generate xml of test results")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.cov = None
        self.cov_report = None
        self.junitxml = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        if self.cov:
            self.cov = ["--cov", self.cov, "--cov-report", "term-missing"]
            if self.cov_report:
                self.cov.extend(["--cov-report", self.cov_report])
        if self.junitxml:
            self.junitxml = ["--junitxml", self.junitxml]

    def run_tests(self):
        try:
            import pytest
        except:
            raise RuntimeError("py.test is not installed, "
                               "run: pip install pytest")
        params = {"args": self.test_args}
        if self.cov:
            params["args"] += self.cov
            params["plugins"] = ["cov"]
        if self.junitxml:
            params["args"] += self.junitxml
        errno = pytest.main(**params)
        sys.exit(errno)


def sphinx_builder():
    try:
        from sphinx.setup_command import BuildDoc
    except ImportError:
        class NoSphinx(Command):
            user_options = []

            def initialize_options(self):
                raise RuntimeError("Sphinx documentation is not installed, "
                                   "run: pip install sphinx")

        return NoSphinx

    class BuildSphinxDocs(BuildDoc):

        def run(self):
            if self.builder == "doctest":
                import sphinx.ext.doctest as doctest
                # Capture the DocTestBuilder class in order to return the total
                # number of failures when exiting
                ref = capture_objs(doctest.DocTestBuilder)
                BuildDoc.run(self)
                errno = ref[-1].total_failures
                sys.exit(errno)
            else:
                BuildDoc.run(self)

    return BuildSphinxDocs


class ObjKeeper(type):
    instances = {}

    def __init__(cls, name, bases, dct):
        cls.instances[cls] = []

    def __call__(cls, *args, **kwargs):
        cls.instances[cls].append(super(ObjKeeper, cls).__call__(*args,
                                                                 **kwargs))
        return cls.instances[cls][-1]


def capture_objs(cls):
    from six import add_metaclass
    module = inspect.getmodule(cls)
    name = cls.__name__
    keeper_class = add_metaclass(ObjKeeper)(cls)
    setattr(module, name, keeper_class)
    cls = getattr(module, name)
    return keeper_class.instances[cls]


def get_install_requirements(path):
    content = open(os.path.join(__location__, path)).read()
    return [req for req in content.splitlines() if req != '']


def read(fname):
    return open(os.path.join(__location__, fname)).read()


def read_setup_cfg():
    config = configparser.SafeConfigParser(allow_no_value=True)
    config_file = StringIO(read(os.path.join(__location__, 'setup.cfg')))
    config.readfp(config_file)
    metadata = dict(config.items('metadata'))
    metadata['classifiers'] = [item.strip() for item
                               in metadata['classifiers'].split(',')]
    console_scripts = dict(config.items('console_scripts'))
    console_scripts = prepare_console_scripts(console_scripts)
    return metadata, console_scripts


def prepare_console_scripts(dct):
    return ['{cmd} = {func}'.format(cmd=k, func=v) for k, v in dct.items()]


def setup_package():
    # Assemble additional setup commands
    cmdclass = get_cmdclass()
    cmdclass['docs'] = sphinx_builder()
    cmdclass['doctest'] = sphinx_builder()
    cmdclass['test'] = PyTest

    # Some helper variables
    version = get_version()
    docs_path = os.path.join(__location__, "docs")
    docs_build_path = os.path.join(docs_path, "_build")
    install_reqs = get_install_requirements("requirements.txt")
    metadata, console_scripts = read_setup_cfg()

    command_options = {
        'docs': {'project': ('setup.py', package),
                 'version': ('setup.py', version.split('-', 1)[0]),
                 'release': ('setup.py', version),
                 'build_dir': ('setup.py', docs_build_path),
                 'config_dir': ('setup.py', docs_path),
                 'source_dir': ('setup.py', docs_path)},
        'doctest': {'project': ('setup.py', package),
                    'version': ('setup.py', version.split('-', 1)[0]),
                    'release': ('setup.py', version),
                    'build_dir': ('setup.py', docs_build_path),
                    'config_dir': ('setup.py', docs_path),
                    'source_dir': ('setup.py', docs_path),
                    'builder': ('setup.py', 'doctest')},
        'test': {'test_suite': ('setup.py', 'tests'),
                 'cov': ('setup.py', package)}}

    setup(name=package,
          version=version,
          url=metadata['url'],
          description=metadata['description'],
          author=metadata['author'],
          author_email=metadata['author_email'],
          license=metadata['license'],
          long_description=read('README.rst'),
          classifiers=metadata['classifiers'],
          test_suite='tests',
          packages=setuptools.find_packages(exclude=['tests', 'tests.*']),
          install_requires=install_reqs,
          setup_requires=['six'],
          cmdclass=cmdclass,
          tests_require=['pytest-cov', 'pytest'],
          include_package_data=True,
          package_data={package: ['data/*']},
          command_options=command_options,
          entry_points={'console_scripts': console_scripts})


# gist of Versioneer 0.12 by Brain Warner
# https://github.com/warner/python-versioneer
# License is public domain

# Versioneer configuration
VCS = 'git'
versionfile_source = os.path.join(package, '_version.py')
versionfile_build = os.path.join(package, '_version.py')
tag_prefix = 'v'  # tags are like v1.2.0
parentdir_prefix = package + '-'
DEFAULT = {"version": "unknown", "full": "unknown"}
SHORT_VERSION_PY = """
# This file was generated by 'versioneer.py' (0.12) from
# revision-control system data, or from the parent directory name of an
# unpacked source archive. Distribution tarballs contain a pre-generated copy
# of this file.

version_version = '%(version)s'
version_full = '%(full)s'
def get_versions(default={}, verbose=False):
    return {'version': version_version, 'full': version_full}

"""
LONG_VERSION_PY = dict()
LONG_VERSION_PY['git'] = '''
# This file helps to compute a version number in source trees obtained from
# git-archive tarball (such as those provided by githubs download-from-tag
# feature). Distribution tarballs (built by setup.py sdist) and build
# directories (produced by setup.py build) will contain a much shorter file
# that just contains the computed version number.

# This file is released into the public domain. Generated by
# versioneer-0.12 (https://github.com/warner/python-versioneer)

# these strings will be replaced by git during git-archive
git_refnames = "%(DOLLAR)sFormat:%%d%(DOLLAR)s"
git_full = "%(DOLLAR)sFormat:%%H%(DOLLAR)s"

# these strings are filled in when 'setup.py versioneer' creates _version.py
tag_prefix = "%(TAG_PREFIX)s"
parentdir_prefix = "%(PARENTDIR_PREFIX)s"
versionfile_source = "%(VERSIONFILE_SOURCE)s"

import os, sys, re, subprocess, errno

def run_command(commands, args, cwd=None, verbose=False, hide_stderr=False):
    assert isinstance(commands, list)
    p = None
    for c in commands:
        try:
            # remember shell=False, so use git.cmd on windows, not just git
            p = subprocess.Popen([c] + args, cwd=cwd, stdout=subprocess.PIPE,
                                 stderr=(subprocess.PIPE if hide_stderr
                                         else None))
            break
        except EnvironmentError:
            e = sys.exc_info()[1]
            if e.errno == errno.ENOENT:
                continue
            if verbose:
                print("unable to run %%s" %% args[0])
                print(e)
            return None
    else:
        if verbose:
            print("unable to find command, tried %%s" %% (commands,))
        return None
    stdout = p.communicate()[0].strip()
    if sys.version >= '3':
        stdout = stdout.decode()
    if p.returncode != 0:
        if verbose:
            print("unable to run %%s (error)" %% args[0])
        return None
    return stdout


def versions_from_parentdir(parentdir_prefix, root, verbose=False):
    # Source tarballs conventionally unpack into a directory that includes
    # both the project name and a version string.
    dirname = os.path.basename(root)
    if not dirname.startswith(parentdir_prefix):
        if verbose:
            print("guessing rootdir is '%%s', but '%%s' doesn't start with prefix '%%s'" %%
                  (root, dirname, parentdir_prefix))
        return None
    return {"version": dirname[len(parentdir_prefix):], "full": ""}

def git_get_keywords(versionfile_abs):
    # the code embedded in _version.py can just fetch the value of these
    # keywords. When used from setup.py, we don't want to import _version.py,
    # so we do it with a regexp instead. This function is not used from
    # _version.py.
    keywords = {}
    try:
        f = open(versionfile_abs,"r")
        for line in f.readlines():
            if line.strip().startswith("git_refnames ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    keywords["refnames"] = mo.group(1)
            if line.strip().startswith("git_full ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    keywords["full"] = mo.group(1)
        f.close()
    except EnvironmentError:
        pass
    return keywords

def git_versions_from_keywords(keywords, tag_prefix, verbose=False):
    if not keywords:
        return {} # keyword-finding function failed to find keywords
    refnames = keywords["refnames"].strip()
    if refnames.startswith("$Format"):
        if verbose:
            print("keywords are unexpanded, not using")
        return {} # unexpanded, so not in an unpacked git-archive tarball
    refs = set([r.strip() for r in refnames.strip("()").split(",")])
    # starting in git-1.8.3, tags are listed as "tag: foo-1.0" instead of
    # just "foo-1.0". If we see a "tag: " prefix, prefer those.
    TAG = "tag: "
    tags = set([r[len(TAG):] for r in refs if r.startswith(TAG)])
    if not tags:
        # Either we're using git < 1.8.3, or there really are no tags. We use
        # a heuristic: assume all version tags have a digit. The old git %%d
        # expansion behaves like git log --decorate=short and strips out the
        # refs/heads/ and refs/tags/ prefixes that would let us distinguish
        # between branches and tags. By ignoring refnames without digits, we
        # filter out many common branch names like "release" and
        # "stabilization", as well as "HEAD" and "master".
        tags = set([r for r in refs if re.search(r'\d', r)])
        if verbose:
            print("discarding '%%s', no digits" %% ",".join(refs-tags))
    if verbose:
        print("likely tags: %%s" %% ",".join(sorted(tags)))
    for ref in sorted(tags):
        # sorting will prefer e.g. "2.0" over "2.0rc1"
        if ref.startswith(tag_prefix):
            r = ref[len(tag_prefix):]
            if verbose:
                print("picking %%s" %% r)
            return { "version": r,
                     "full": keywords["full"].strip() }
    # no suitable tags, so we use the full revision id
    if verbose:
        print("no suitable tags, using full revision id")
    return { "version": keywords["full"].strip(),
             "full": keywords["full"].strip() }


def git_versions_from_vcs(tag_prefix, root, verbose=False):
    # this runs 'git' from the root of the source tree. This only gets called
    # if the git-archive 'subst' keywords were *not* expanded, and
    # _version.py hasn't already been rewritten with a short version string,
    # meaning we're inside a checked out source tree.

    if not os.path.exists(os.path.join(root, ".git")):
        if verbose:
            print("no .git in %%s" %% root)
        return {}

    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]
    stdout = run_command(GITS, ["describe", "--tags", "--dirty", "--always"],
                         cwd=root)
    if stdout is None:
        return {}
    if not stdout.startswith(tag_prefix):
        if verbose:
            print("tag '%%s' doesn't start with prefix '%%s'" %% (stdout, tag_prefix))
        return {}
    tag = stdout[len(tag_prefix):]
    stdout = run_command(GITS, ["rev-parse", "HEAD"], cwd=root)
    if stdout is None:
        return {}
    full = stdout.strip()
    if tag.endswith("-dirty"):
        full += "-dirty"
    return {"version": tag, "full": full}


def get_versions(default={"version": "unknown", "full": ""}, verbose=False):
    # I am in _version.py, which lives at ROOT/VERSIONFILE_SOURCE. If we have
    # __file__, we can work backwards from there to the root. Some
    # py2exe/bbfreeze/non-CPython implementations don't do __file__, in which
    # case we can only use expanded keywords.

    keywords = { "refnames": git_refnames, "full": git_full }
    ver = git_versions_from_keywords(keywords, tag_prefix, verbose)
    if ver:
        return rep_by_pep440(ver)

    try:
        root = os.path.abspath(__file__)
        # versionfile_source is the relative path from the top of the source
        # tree (where the .git directory might live) to this file. Invert
        # this to find the root from __file__.
        for i in range(len(versionfile_source.split('/'))):
            root = os.path.dirname(root)
    except NameError:
        return default

    return rep_by_pep440(
        git_versions_from_vcs(tag_prefix, root, verbose)
        or versions_from_parentdir(parentdir_prefix, root, verbose)
        or default)


def git2pep440(ver_str):
    dash_count = ver_str.count('-')
    if dash_count == 0:
        return ver_str
    elif dash_count == 1:
        return ver_str.split('-')[0] + "+dirty"
    elif dash_count == 2:
        tag, commits, sha1 = ver_str.split('-')
        return "{}.post0.dev{}+{}".format(tag, commits, sha1)
    elif dash_count == 3:
        tag, commits, sha1, _ = ver_str.split('-')
        commits = str(int(commits) + 1)
        return "{}.post0.dev{}+{}.dirty".format(tag, commits, sha1)
    else:
        raise RuntimeError("Invalid version string")


def rep_by_pep440(ver):
    if ver["full"]:  # only if versions_from_parentdir was not used
        ver["version"] = git2pep440(ver["version"])
    else:
        ver["version"] = ver["version"].split('-')[0]
    return ver
'''


def run_command(commands, args, cwd=None, verbose=False, hide_stderr=False):
    assert isinstance(commands, list)
    p = None
    for c in commands:
        try:
            # remember shell=False, so use git.cmd on windows, not just git
            p = subprocess.Popen([c] + args, cwd=cwd, stdout=subprocess.PIPE,
                                 stderr=(subprocess.PIPE if hide_stderr
                                         else None))
            break
        except EnvironmentError:
            e = sys.exc_info()[1]
            if e.errno == errno.ENOENT:
                continue
            if verbose:
                print("unable to run %s" % args[0])
                print(e)
            return None
    else:
        if verbose:
            print("unable to find command, tried %s" % (commands,))
        return None
    stdout = p.communicate()[0].strip()
    if sys.version >= '3':
        stdout = stdout.decode()
    if p.returncode != 0:
        if verbose:
            print("unable to run %s (error)" % args[0])
        return None
    return stdout


def get_root():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.dirname(os.path.abspath(sys.argv[0]))


def git_get_keywords(versionfile_abs):
    # the code embedded in _version.py can just fetch the value of these
    # keywords. When used from setup.py, we don't want to import _version.py,
    # so we do it with a regexp instead. This function is not used from
    # _version.py.
    keywords = {}
    try:
        f = open(versionfile_abs,"r")
        for line in f.readlines():
            if line.strip().startswith("git_refnames ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    keywords["refnames"] = mo.group(1)
            if line.strip().startswith("git_full ="):
                mo = re.search(r'=\s*"(.*)"', line)
                if mo:
                    keywords["full"] = mo.group(1)
        f.close()
    except EnvironmentError:
        pass
    return keywords


def git_versions_from_keywords(keywords, tag_prefix, verbose=False):
    if not keywords:
        return {} # keyword-finding function failed to find keywords
    refnames = keywords["refnames"].strip()
    if refnames.startswith("$Format"):
        if verbose:
            print("keywords are unexpanded, not using")
        return {} # unexpanded, so not in an unpacked git-archive tarball
    refs = set([r.strip() for r in refnames.strip("()").split(",")])
    # starting in git-1.8.3, tags are listed as "tag: foo-1.0" instead of
    # just "foo-1.0". If we see a "tag: " prefix, prefer those.
    TAG = "tag: "
    tags = set([r[len(TAG):] for r in refs if r.startswith(TAG)])
    if not tags:
        # Either we're using git < 1.8.3, or there really are no tags. We use
        # a heuristic: assume all version tags have a digit. The old git %d
        # expansion behaves like git log --decorate=short and strips out the
        # refs/heads/ and refs/tags/ prefixes that would let us distinguish
        # between branches and tags. By ignoring refnames without digits, we
        # filter out many common branch names like "release" and
        # "stabilization", as well as "HEAD" and "master".
        tags = set([r for r in refs if re.search(r'\d', r)])
        if verbose:
            print("discarding '%s', no digits" % ",".join(refs-tags))
    if verbose:
        print("likely tags: %s" % ",".join(sorted(tags)))
    for ref in sorted(tags):
        # sorting will prefer e.g. "2.0" over "2.0rc1"
        if ref.startswith(tag_prefix):
            r = ref[len(tag_prefix):]
            if verbose:
                print("picking %s" % r)
            return { "version": r,
                     "full": keywords["full"].strip() }
    # no suitable tags, so we use the full revision id
    if verbose:
        print("no suitable tags, using full revision id")
    return { "version": keywords["full"].strip(),
             "full": keywords["full"].strip() }


def git_versions_from_vcs(tag_prefix, root, verbose=False):
    # this runs 'git' from the root of the source tree. This only gets called
    # if the git-archive 'subst' keywords were *not* expanded, and
    # _version.py hasn't already been rewritten with a short version string,
    # meaning we're inside a checked out source tree.

    if not os.path.exists(os.path.join(root, ".git")):
        if verbose:
            print("no .git in %s" % root)
        return {}

    GITS = ["git"]
    if sys.platform == "win32":
        GITS = ["git.cmd", "git.exe"]
    stdout = run_command(GITS, ["describe", "--tags", "--dirty", "--always"],
                         cwd=root)
    if stdout is None:
        return {}
    if not stdout.startswith(tag_prefix):
        if verbose:
            print("tag '%s' doesn't start with prefix '%s'" % (stdout, tag_prefix))
        return {}
    tag = stdout[len(tag_prefix):]
    stdout = run_command(GITS, ["rev-parse", "HEAD"], cwd=root)
    if stdout is None:
        return {}
    full = stdout.strip()
    if tag.endswith("-dirty"):
        full += "-dirty"
    return {"version": tag, "full": full}


def versions_from_file(filename):
    versions = {}
    try:
        with open(filename) as f:
            for line in f.readlines():
                mo = re.match("version_version = '([^']+)'", line)
                if mo:
                    versions["version"] = mo.group(1)
                mo = re.match("version_full = '([^']+)'", line)
                if mo:
                    versions["full"] = mo.group(1)
    except EnvironmentError:
        return {}

    return versions


def versions_from_parentdir(parentdir_prefix, root, verbose=False):
    # Source tarballs conventionally unpack into a directory that includes
    # both the project name and a version string.
    dirname = os.path.basename(root)
    if not dirname.startswith(parentdir_prefix):
        if verbose:
            print("guessing rootdir is '%s', but '%s' doesn't start with prefix '%s'" %
                  (root, dirname, parentdir_prefix))
        return None
    return {"version": dirname[len(parentdir_prefix):], "full": ""}


def get_versions(default=DEFAULT, verbose=False):
    # returns dict with two keys: 'version' and 'full'
    assert versionfile_source is not None, "please set versioneer.versionfile_source"
    assert tag_prefix is not None, "please set versioneer.tag_prefix"
    assert parentdir_prefix is not None, "please set versioneer.parentdir_prefix"
    assert VCS is not None, "please set versioneer.VCS"

    # I am in versioneer.py, which must live at the top of the source tree,
    # which we use to compute the root directory. py2exe/bbfreeze/non-CPython
    # don't have __file__, in which case we fall back to sys.argv[0] (which
    # ought to be the setup.py script). We prefer __file__ since that's more
    # robust in cases where setup.py was invoked in some weird way (e.g. pip)
    root = get_root()
    versionfile_abs = os.path.join(root, versionfile_source)

    # extract version from first of _version.py, VCS command (e.g. 'git
    # describe'), parentdir. This is meant to work for developers using a
    # source checkout, for users of a tarball created by 'setup.py sdist',
    # and for users of a tarball/zipball created by 'git archive' or github's
    # download-from-tag feature or the equivalent in other VCSes.

    get_keywords_f = git_get_keywords
    versions_from_keywords_f = git_versions_from_keywords
    if get_keywords_f and versions_from_keywords_f:
        vcs_keywords = get_keywords_f(versionfile_abs)
        ver = versions_from_keywords_f(vcs_keywords, tag_prefix)
        if ver:
            if verbose: print("got version from expanded keyword %s" % ver)
            return rep_by_pep440(ver)

    ver = versions_from_file(versionfile_abs)
    if ver:
        if verbose: print("got version from file %s %s" % (versionfile_abs,ver))
        return rep_by_pep440(ver)

    versions_from_vcs_f = git_versions_from_vcs
    if versions_from_vcs_f:
        ver = versions_from_vcs_f(tag_prefix, root, verbose)
        if ver:
            if verbose: print("got version from VCS %s" % ver)
            return rep_by_pep440(ver)

    ver = versions_from_parentdir(parentdir_prefix, root, verbose)
    if ver:
        if verbose: print("got version from parentdir %s" % ver)
        return rep_by_pep440(ver)

    if verbose: print("got version from default %s" % default)
    return rep_by_pep440(default)


def get_version(verbose=False):
    return get_versions(verbose=verbose)["version"]


class cmd_version(Command):
    description = "report generated version string"
    user_options = []
    boolean_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        ver = get_version(verbose=True)
        print("Version is currently: %s" % ver)


class cmd_build(_build):
    def run(self):
        versions = get_versions(verbose=True)
        _build.run(self)
        # now locate _version.py in the new build/ directory and replace it
        # with an updated value
        if versionfile_build:
            target_versionfile = os.path.join(self.build_lib, versionfile_build)
            print("UPDATING %s" % target_versionfile)
            os.unlink(target_versionfile)
            with open(target_versionfile, "w") as f:
                f.write(SHORT_VERSION_PY % versions)

if 'cx_Freeze' in sys.modules:  # cx_freeze enabled?
    from cx_Freeze.dist import build_exe as _build_exe

    class cmd_build_exe(_build_exe):
        def run(self):
            versions = get_versions(verbose=True)
            target_versionfile = versionfile_source
            print("UPDATING %s" % target_versionfile)
            os.unlink(target_versionfile)
            with open(target_versionfile, "w") as f:
                f.write(SHORT_VERSION_PY % versions)

            _build_exe.run(self)
            os.unlink(target_versionfile)
            with open(versionfile_source, "w") as f:
                assert VCS is not None, "please set versioneer.VCS"
                LONG = LONG_VERSION_PY[VCS]
                f.write(LONG % {"DOLLAR": "$",
                                "TAG_PREFIX": tag_prefix,
                                "PARENTDIR_PREFIX": parentdir_prefix,
                                "VERSIONFILE_SOURCE": versionfile_source,
                                })


class cmd_sdist(_sdist):
    def run(self):
        versions = get_versions(verbose=True)
        self._versioneer_generated_versions = versions
        # unless we update this, the command will keep using the old version
        self.distribution.metadata.version = versions["version"]
        return _sdist.run(self)

    def make_release_tree(self, base_dir, files):
        _sdist.make_release_tree(self, base_dir, files)
        # now locate _version.py in the new base_dir directory (remembering
        # that it may be a hardlink) and replace it with an updated value
        target_versionfile = os.path.join(base_dir, versionfile_source)
        print("UPDATING %s" % target_versionfile)
        os.unlink(target_versionfile)
        with open(target_versionfile, "w") as f:
            f.write(SHORT_VERSION_PY % self._versioneer_generated_versions)


def get_cmdclass():
    cmds = {'version': cmd_version,
            'build': cmd_build,
            'sdist': cmd_sdist,
            }
    if 'cx_Freeze' in sys.modules:  # cx_freeze enabled?
        cmds['build_exe'] = cmd_build_exe
        del cmds['build']

    return cmds
# End gist of Versioneer 0.12


def git2pep440(ver_str):
    dash_count = ver_str.count('-')
    if dash_count == 0:
        return ver_str
    elif dash_count == 1:
        return ver_str.split('-')[0] + "+dirty"
    elif dash_count == 2:
        tag, commits, sha1 = ver_str.split('-')
        return "{}.post0.dev{}+{}".format(tag, commits, sha1)
    elif dash_count == 3:
        tag, commits, sha1, _ = ver_str.split('-')
        commits = str(int(commits) + 1)
        return "{}.post0.dev{}+{}.dirty".format(tag, commits, sha1)
    else:
        raise RuntimeError("Invalid version string")


def rep_by_pep440(ver):
    if ver["full"]:  # only if versions_from_parentdir was not used
        ver["version"] = git2pep440(ver["version"])
    else:
        ver["version"] = ver["version"].split('-')[0]
    return ver

if __name__ == "__main__":
    setup_package()
