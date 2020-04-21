"""
Utilities for the SH3.
"""

from collections import defaultdict
from datetime import datetime
from types import SimpleNamespace


class DownstreamChannel(SimpleNamespace):
    """
    Container for downstream channel information.
    """
    channel_id = None
    frequency = None
    power = None
    snr = None
    rxmer = None
    post_rs_errors = None
    post_rs_errors = None


class UpstreamChannel(SimpleNamespace):
    """
    Container for upstream channel information.
    """
    channel_id = None
    frequency = None
    power = None
    symbol_rate = None


class LogRecord(SimpleNamespace):
    """
    Container for network log records.
    """
    timestamp = None
    level = None
    message = None

    def __init__(self, timestamp, level, message):
        self.timestamp = timestamp
        self.level = level
        self.message = message


def parse_router_status(struct):
    """
    Parse the output of `getRouterStatus`.
    """
    keys = sorted(struct.keys())  # Access each key in order

    data = {
        "downstream_channels": defaultdict(DownstreamChannel),
        "upstream_channels": defaultdict(UpstreamChannel),
    }

    log_timestamps = []
    log_levels = []
    log_messages = []

    for key in keys:
        value = struct[key]

        # This is going to be mental
        if key.startswith("1.3.6.1.2.1.10.127.1.1.1.1."):  # downstream channel part 1
            key_part = key[27:]
            channel = int(key_part[2:])

            if key_part.startswith("1."):
                data['downstream_channels'][channel].channel_id = int(value)
            if key_part.startswith("2."):
                data['downstream_channels'][channel].frequency = int(value)
            if key_part.startswith("4."):
                data['downstream_channels'][channel].snr = float(value) * 10
            if key_part.startswith("6."):
                data['downstream_channels'][channel].power = int(value) / 10

        if key.startswith("1.3.6.1.2.1.10.127.1.1.4.1."):  # downstream channel part 2
            key_part = key[27:]
            channel = int(key_part[2:])

            if key_part.startswith("3."):
                data['downstream_channels'][channel].pre_rs_errors = int(value)
            if key_part.startswith("4."):
                data['downstream_channels'][channel].post_rs_errors = int(value)
            if key_part.startswith("5."):
                data['downstream_channels'][channel].rxmer = int(value) / 10

        if key.startswith("1.3.6.1.2.1.10.127.1.1.2.1."):  # upstrean channel part 1
            key_part = key[27:]
            if key_part.startswith("15."):
                continue
            channel = int(key_part[2:])

            if key_part.startswith("1."):
                data['upstream_channels'][channel].channel_id = int(value)
            if key_part.startswith("2."):
                data['upstream_channels'][channel].frequency = int(value)

        if key.startswith("1.3.6.1.4.1.4491.2.1.20.1.2.1.1."):  # power
            channel = int(key[32:])
            data['upstream_channels'][channel].power = float(value)

        if key.startswith("1.3.6.1.4.1.4115.1.3.4.1.9.2.1.2."):  # symbol rate
            channel = int(key[33:])
            data['upstream_channels'][channel].symbol_rate = int(value)

        # Log messages
        if key.startswith("1.3.6.1.2.1.69.1.5.8.1.2."):
            log_timestamps.append(datetime.strptime(value, "%d/%m/%Y %H:%M:%S"))
        if key.startswith("1.3.6.1.2.1.69.1.5.8.1.5."):
            log_levels.append(int(value))
        if key.startswith("1.3.6.1.2.1.69.1.5.8.1.7."):
            log_messages.append(value)

    data["network_log"] = [LogRecord(*tup) for tup in zip(log_timestamps, log_levels, log_messages)]
    return data
