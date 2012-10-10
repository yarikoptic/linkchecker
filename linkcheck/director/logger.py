# -*- coding: iso-8859-1 -*-
# Copyright (C) 2006-2012 Bastian Kleineidam
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""Logger for aggregator instances"""
import threading
import thread
from ..decorators import synchronized
_lock = threading.Lock()


class Logger (object):
    """Thread safe multi-logger class used by aggregator instances."""

    def __init__ (self, config):
        """Initialize basic logging variables."""
        self.loggers = [config['logger']]
        self.loggers.extend(config['fileoutput'])
        self.verbose = config["verbose"]
        self.complete = config["complete"]
        self.warnings = config["warnings"]

    def start_log_output (self):
        """
        Start output of all configured loggers.
        """
        for logger in self.loggers:
            logger.start_output()

    def end_log_output (self):
        """
        End output of all configured loggers.
        """
        for logger in self.loggers:
            logger.end_output()

    def add_statistics(self, robots_txt_stats, download_stats):
        """Add statistics to logger."""
        for logger in self.loggers:
            logger.add_statistics(robots_txt_stats, download_stats)

    def do_print (self, url_data):
        """Determine if URL entry should be logged or not."""
        if self.complete:
            return True
        if url_data.cached and url_data.valid:
            return False
        if self.verbose:
            return True
        if self.warnings and url_data.warnings:
            return True
        return not url_data.valid

    @synchronized(_lock)
    def log_url (self, url_data):
        """Send new url to all configured loggers."""
        self.check_active_loggers()
        do_print = self.do_print(url_data)
        # Only send a transport object to the loggers, not the complete
        # object instance.
        transport = url_data.to_wire()
        for log in self.loggers:
            log.log_filter_url(transport, do_print)

    @synchronized(_lock)
    def log_internal_error (self):
        """Document that an internal error occurred."""
        for logger in self.loggers:
            logger.log_internal_error()

    def check_active_loggers(self):
        """Check if all loggers are deactivated due to I/O errors."""
        for logger in self.loggers:
            if logger.is_active:
                break
        else:
            thread.interrupt_main()
