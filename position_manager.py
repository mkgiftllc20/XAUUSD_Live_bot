import logging
import config

log = logging.getLogger("position_manager")


async def handle_alert(alert):
    if config.DRY_RUN:
        log.info("DRY_RUN: alert ignored")
        return {"status": "dry_run", "action": alert.action}
    log.info("Alert accepted")
    return {"status": "accepted", "action": alert.action}


async def run_forever():
    while True:
        await handle_alert(None)
