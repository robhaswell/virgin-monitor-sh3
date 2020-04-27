"""
Monitor a Virgin SuperHub 3.0

Development:

1. pip install aiohttp-devtools
2. adev runserver app.py
"""
import asyncio
import logging
import os
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta

import aiohttp
import aiosqlite
import configargparse
import yaml
from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from logger import start_logger
from sh3 import parse_router_status

ENDPOINT_URL = "http://192.168.100.1/getRouterStatus"


async def start_monitor(app):
    """ Start background tasks. """
    # Look to see if our database is initialised
    async with app['sql3_connect']() as sql3:
        cursor = await sql3.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table';
        """)
        if not await cursor.fetchall():
            # No rows, initialise the database
            await initialise_db(sql3)

    # Start the task
    app['monitor'] = asyncio.create_task(monitor_sh3(app))


async def cleanup(app):
    """ Cleanup. """
    app['monitor'].cancel()
    await app['monitor']


def create_app(main=False):
    """
    Main asynchronous program.
    """
    start_logger()
    log = logging.getLogger(__name__)

    parser = configargparse.ArgParser(default_config_files=["~/.virgin-monitor"])
    parser.add("-c", "--my-config", is_config_file=True, help="config file path")
    parser.add("-p", "--db-path", env_var="DB_PATH", default="~/virgin-monitor.sqlite",
               help="database file path")
    parser.add("-i", "--interval", env_var="POLL_INTERVAL", default=10,
               help="poll interval (seconds)", type=int)
    parser.add("-u", "--url", env_var="URL", default=ENDPOINT_URL, help="Endpoint URL")

    if main:
        argv = sys.argv[1:]
    else:
        # Run with adev or something
        argv = sys.argv[2:]
    args = parser.parse_args(argv)

    db_path = os.path.expanduser(args.db_path)

    http = aiohttp.ClientSession()

    app = web.Application()
    app.update(
        args=args,
        http=http,
        sql3_connect=lambda: aiosqlite.connect(db_path, isolation_level=None),
        log=log
    )

    app.on_startup.append(start_monitor)
    app.on_cleanup.append(cleanup)

    # Web routes
    app.add_routes([web.static('/js', "web/js")])
    app.add_routes([web.static('/css', "web/css")])
    app.router.add_get('/', index)
    app.router.add_get('/data', data)
    return app


async def index(_: Request):
    """
    Web root page.
    """
    output = open("web/index.html").read()
    return Response(text=output, content_type="text/html")


async def data(request: Request):
    """
    Get chart data.
    """
    start = datetime.utcnow() - timedelta(days=1)
    data = {
        "downstream_power": defaultdict(list),
        "downstream_snr": defaultdict(list),
        "downstream_rxmer": defaultdict(list),
        "upstream_power": defaultdict(list),
        "network_log_events": list,
    }

    async with request.app['sql3_connect']() as sql3:
        sql3.row_factory = sqlite3.Row

        # Fetch downstream statistics
        cursor = await sql3.execute("""
            SELECT timestamp, channel, power, snr, rxmer FROM downstream_channels
            WHERE timestamp > ?
        """, (start,))
        rows = await cursor.fetchall()
        for row in rows:
            timestamp = datetime.fromisoformat(row['timestamp']).replace(microsecond=0)
            data['downstream_power'][row['channel']].append(
                dict(x=timestamp.isoformat(), y=row['power']))
            data['downstream_snr'][row['channel']].append(
                dict(x=timestamp.isoformat(), y=row['snr']))
            data['downstream_rxmer'][row['channel']].append(
                dict(x=timestamp.isoformat(), y=row['rxmer']))

        # Fetch upstream statistics
        cursor = await sql3.execute("""
            SELECT timestamp, channel, power FROM upstream_channels
            WHERE timestamp > ?
        """, (start,))
        rows = await cursor.fetchall()
        for row in rows:
            timestamp = datetime.fromisoformat(row['timestamp']).replace(microsecond=0)
            data['upstream_power'][row['channel']].append(
                dict(x=timestamp.isoformat(), y=row['power']))

        # Get the count of network log critical events
        log_events = defaultdict(int)
        cursor = await sql3.execute("""
            SELECT timestamp FROM network_log
            WHERE timestamp > ?
                AND level >= 3
        """, (start,))
        rows = await cursor.fetchall()
        for row in rows:
            timestamp = datetime.fromisoformat(row['timestamp'])
            timestamp = timestamp.replace(second=0, microsecond=0)
            log_events[timestamp.isoformat()] += 1

        data['network_log_events'] = [{"x": timestamp, "y": value}
                                      for timestamp, value in log_events.items()]

    return web.json_response(data)


async def monitor_sh3(app):
    """
    Background task to collect telemetry on the SH3.
    """
    args = app['args']
    log = app['log']

    async with app['http'] as http, app['sql3_connect']() as sql3:
        while True:
            start = time.time()
            try:
                async with http.get(args.url) as response:
                    content = await response.read()
            except (aiohttp.client_exceptions.ClientError, asyncio.TimeoutError):
                log.exception("client error")
                # Retry immediately
                continue
            end = time.time()
            log.info("got router status", extra=dict(request_time=end-start))

            stats = parse_router_status(yaml.load(content, Loader=yaml.SafeLoader))

            now = datetime.utcnow()

            # Now store the data
            for channel, row in stats['downstream_channels'].items():
                await sql3.execute("""
                    INSERT INTO downstream_channels (timestamp, channel, channel_id, frequency,
                        power, snr, rxmer, pre_rs_errors, post_rs_errors)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (now, channel, row.channel_id, row.frequency,
                      row.power, row.snr, row.rxmer, row.pre_rs_errors, row.post_rs_errors))

            for channel, row in stats['upstream_channels'].items():
                await sql3.execute("""
                    INSERT INTO upstream_channels (timestamp, channel, channel_id, frequency,
                        power, symbol_rate)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (now, channel, row.channel_id, row.frequency,
                      row.power, row.symbol_rate))

            for log_record in stats['network_log']:
                await sql3.execute("""
                    INSERT OR IGNORE INTO network_log (timestamp, level, message)
                    VALUES (?, ?, ?)
                """, (log_record.timestamp, log_record.level, log_record.message))

            await asyncio.sleep(10)


async def initialise_db(sql3):
    """
    Create sqlite schema.
    """
    await sql3.execute("""
        CREATE TABLE network_log (
            timestamp timestamp,
            level int,
            message text,

            PRIMARY KEY (timestamp, message)
        )
    """)

    await sql3.execute("""
        CREATE TABLE downstream_channels (
            timestamp timestamp,
            channel int,
            channel_id int,
            frequency int,
            pre_rs_errors int,
            post_rs_errors int,
            power float,
            snr float,
            rxmer float,

            PRIMARY KEY (timestamp, channel)
        )
    """)

    await sql3.execute("""
        CREATE TABLE upstream_channels (
            timestamp timestamp,
            channel int,
            channel_id int,
            frequency int,
            power float,
            symbol_rate int,

            PRIMARY KEY (timestamp, channel)
        )
    """)


def main():
    """
    Start the application.
    """
    app = create_app(True)
    web.run_app(app, port=8080, print=app['log'].info)


if __name__ == "__main__":
    main()
