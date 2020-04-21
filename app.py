"""
Monitor a Virgin SuperHub 3.0
"""
import asyncio
import logging
import os
import time
from datetime import datetime

import aiohttp
import aiosqlite
import configargparse
import yaml

from logger import start_logger
from sh3 import parse_router_status

ENDPOINT_URL = "http://192.168.100.1/getRouterStatus"


async def amain():
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
    args = parser.parse_args()

    db_path = os.path.expanduser(args.db_path)

    sql3 = aiosqlite.connect(db_path, isolation_level=None)
    session = aiohttp.ClientSession()

    async with session, sql3:
        # Look to see if our database is initialised
        cursor = await sql3.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table';
        """)
        if not await cursor.fetchall():
            # No rows, initialise the database
            await initialise_db(sql3)

        while True:
            start = time.time()
            async with session.get(args.url) as response:
                content = await response.read()
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


if __name__ == "__main__":
    asyncio.run(amain())
