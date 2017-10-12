# -*- coding: utf-8 -*-
"""
Shell commands like git, django-admin.py etc.
"""

from __future__ import absolute_import, division, print_function

import functools
import subprocess
import sys

from six import raise_from

from .log import logger
from .exceptions import ShellCommandException

__author__ = "Florian Wilhelm"
__copyright__ = "Blue Yonder"
__license__ = "new BSD"


class ShellCommand(object):
    """Shell command that can be called with flags like git('add', 'file')

    Args:
        command (str): command to handle
        shell (bool): run the command in the shell
        cwd (str): current working dir to run the command

    The produced command can be called with the following keyword arguments:

        - **log** (*bool*): log activity when true. ``False`` by default.
        - **pretend** (*bool*): skip execution (but log) when pretending.
          ``False`` by default.

    The positional arguments are passed to the underlying shell command.
    """
    def __init__(self, command, shell=True, cwd=None):
        self._command = command
        self._shell = shell
        self._cwd = cwd

    def __call__(self, *args, **kwargs):
        """Execute command with the given arguments."""
        command = "{cmd} {args}".format(cmd=self._command,
                                        args=subprocess.list2cmdline(args))

        should_pretend = kwargs.get('pretend')
        should_log = kwargs.get('log', should_pretend)
        # ^ When pretending, automatically output logs
        #   (after all, this is the primary purpose of pretending)

        if should_log:
            logger.report('run', command, context=self._cwd)

        if should_pretend:
            output = ''
        else:
            try:
                output = subprocess.check_output(command,
                                                 shell=self._shell,
                                                 cwd=self._cwd,
                                                 stderr=subprocess.STDOUT,
                                                 universal_newlines=True)
            except subprocess.CalledProcessError as e:
                raise_from(ShellCommandException(e.output), e)

        return (line for line in output.splitlines())


def called_process_error2exit_decorator(func):
    """Decorator to convert given CalledProcessError to an exit message

    This avoids displaying nasty stack traces to end-users
    """
    @functools.wraps(func)
    def func_wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except ShellCommandException as e:
            e = e.__cause__
            print("{err}:\n{msg}".format(err=str(e), msg=e.output))
            sys.exit(1)
    return func_wrapper


def get_git_cmd(**args):
    """Retrieve the git shell command depending on the current platform

    Args:
        **args: additional keyword arguments to :obj:`~.ShellCommand`
    """
    if sys.platform == "win32":
        for cmd in ["git.cmd", "git.exe"]:
            git = ShellCommand(cmd, **args)
            try:
                git("--version")
            except ShellCommandException:
                continue
            return git
        return None
    else:
        git = ShellCommand("git", **args)
        try:
            git("--version")
        except ShellCommandException:
            return None
        return git


def command_exists(cmd):
    """Check check if command exists

    Args:
        cmd: executable name
    """
    checker = ShellCommand("command -v")
    try:
        checker(cmd)
        return True
    except ShellCommandException:
        return False


#: Command for git
git = get_git_cmd()

#: Command for django-admin.py
django_admin = ShellCommand("django-admin.py")
