# ruff: disable[N802,N806]
"""基于时间的日志轮转处理器模块。"""

import logging.handlers
import os
import time

from ..files import ensure_str_path


class TimeLoggerRolloverHandler(logging.handlers.TimedRotatingFileHandler):
    """Custom timed rotating file handler for log files with custom naming format.

    This handler extends Python's TimedRotatingFileHandler to provide a customized
    log file rotation mechanism with a specific naming pattern: {basename}.{timestamp}.log

    Attributes:
        Inherits all attributes from TimedRotatingFileHandler
    """

    def __init__(
        self,
        filename,
        when="h",
        interval=1,
        backupCount=0,  # noqa: N803
        encoding=None,
        delay=False,
        utc=False,
        atTime=None,  # noqa: N803
        errors=None,
    ):
        """Initialize the handler with a custom log file path, fixing the problem of path format and extending rotation.

        Args:
            filename: Path to the log file
            when: Rotation interval type ('S'=Seconds, 'M'=Minutes, 'H'=Hours, 'D'=Days, etc.)
            interval: Rotation interval count (default: 1)
            backupCount: Number of backup files to keep (0 = keep all)
            encoding: File encoding (default: None = system default)
            delay: If True, file opening is deferred until the first emit()
            utc: If True, use UTC time; otherwise use local time
            atTime: Specific time of day for rotation (when='midnight' or 'H'|'M')
            errors: Error handling scheme for encoding errors
        """
        # Initialize and normalize the folder path to ensure proper file path format
        filename = ensure_str_path(filename, folder=False)
        super().__init__(filename, when, interval, backupCount, encoding, delay, utc, atTime, errors)

    def doRollover(self):
        """Perform log file rotation with a custom timestamp-based naming scheme.

        This method is called when it's time to rotate the log file. It creates a new
        log file with a timestamp suffix based on the START of the rotation interval,
        not the current time. This ensures files are named according to the time period
        they cover (e.g., app.20250118.10.log covers the hour 10:00-11:00).

        Rotation Logic:
        1. Calculate the start time of the current logging interval
        2. Handle daylight saving time (DST) transitions if using local time
        3. Generate the new filename with timestamp suffix
        4. Close the current log file stream
        5. Rename/move the current log file to the timestamped backup name
        6. Delete old backup files if backupCount is exceeded
        7. Open a new log file for continued writing
        8. Calculate the next rotation time

        Example:
            If rotating hourly at 11:00, the file covering 10:00-11:00 will be
            named as 'app.20250118.10.log' (not 'app.20250118.11.log')
        """
        # Get the current timestamp as integer seconds since epoch
        currentTime = int(time.time())

        # Calculate the start time of the current logging interval
        # (e.g., if rotating hourly at 11:00, this gives 10:00)
        t = self.rolloverAt - self.interval

        # Convert the interval start time to a time tuple
        if self.utc:
            # Use UTC time if utc flag is set
            timeTuple = time.gmtime(t)
        else:
            # Use local time and handle daylight saving time (DST) transitions
            timeTuple = time.localtime(t)

            # Check if DST status has changed between interval start and now
            dstNow = time.localtime(currentTime)[-1]  # Current DST status (0 or 1)
            dstThen = timeTuple[-1]  # Interval start DST status (0 or 1)

            if dstNow != dstThen:
                # DST transition occurred: adjust time by +/- 1 hour
                addend = 3600 if dstNow else -3600
                timeTuple = time.localtime(t + addend)

        # Construct the destination filename for the rotated log file (different from the original doRollover)
        # Format: {baseFilename}.{timestamp_suffix}.log
        # Example: /var/log/app.2025011810.log
        # if baseFilename ends with .log, it becomes .2025011810.log
        if self.baseFilename.endswith(".log"):
            dfn = self.rotation_filename(f"{self.baseFilename[:-4]}.{time.strftime(self.suffix, timeTuple)}.log")
        else:
            dfn = self.rotation_filename(f"{self.baseFilename}.{time.strftime(self.suffix, timeTuple)}.log")

        # Check if the rotated file already exists (prevents duplicate rotation)
        if os.path.exists(dfn):
            # File already rolled over, skip rotation to prevent data loss
            return

        # Close the current log file stream if it's open
        if self.stream:
            self.stream.close()
            # Clear the stream reference
            self.stream = None

        # Perform the actual file rotation (rename current file to timestamped name)
        self.rotate(self.baseFilename, dfn)

        # Clean up old backup files if backup count limit is set
        if self.backupCount > 0:
            # Get list of files to delete based on backupCount limit
            for s in self.getFilesToDelete():
                os.remove(s)

        # Open a new log file for continued logging (unless delay is set)
        if not self.delay:
            self.stream = self._open()

        # Calculate and set the next rotation time
        self.rolloverAt = self.computeRollover(currentTime)


__all__ = ["TimeLoggerRolloverHandler"]

# ruff: enable[N802,N806]
