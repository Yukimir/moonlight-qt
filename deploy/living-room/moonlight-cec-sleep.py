#!/usr/bin/env python3
"""Suspend the living-room Moonlight client when its TV broadcasts standby."""

import logging
import re
import subprocess
import time


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
TV_STANDBY = re.compile(r"^Received from TV to all .*: STANDBY \(0x36\)")


def monitor():
    subprocess.run(
        ["cec-ctl", "-d0", "--playback"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
        timeout=10,
        check=True,
    )
    logging.info("Watching TV standby on /dev/cec0")
    with subprocess.Popen(
        ["stdbuf", "-oL", "cec-ctl", "-d0", "-M", "-w", "--monitor-time", "86400"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    ) as process:
        for line in process.stdout:
            if not TV_STANDBY.match(line):
                continue
            logging.info("TV sent STANDBY; ending the stream and suspending")
            process.terminate()
            try:
                subprocess.run(["/usr/local/sbin/moonlight-suspend"], check=True)
            except subprocess.CalledProcessError as exc:
                logging.error("Suspend command failed: %s", exc)
            time.sleep(15)
            return
        logging.warning("CEC monitor exited with status %s; retrying", process.wait())


while True:
    try:
        monitor()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logging.error("CEC monitor unavailable: %s", exc)
    time.sleep(5)
