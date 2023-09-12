#!/usr/bin/env python3

import logging

logging.basicConfig(format="[%(asctime)s][%(name)s][%(levelname)s] %(message)s")
logging.getLogger("pywiki").disabled = True
logger = logging.getLogger("copyblock")

import datetime
import ipaddress
import re

import click
import dateutil.parser
import dateutil.tz

from pywikibot import Site, User  # type: ignore
from pywikibot.data.api import ListGenerator  # type: ignore


def parse_timestamp(s: str):
    return dateutil.parser.isoparse(s).replace(tzinfo=None)


def is_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_net(ip):
    try:
        ipaddress.ip_network(ip)
        return True
    except ValueError:
        return False


class CopyBlock:
    def __init__(
        self,
        source_user: str,
        lang: str = "en",
        site: str = "wikipedia",
        dry_run: bool = True,
        ranges: bool = False,
        comment_pattern: str = ".*",
        verbose: bool = False,
        limit: int = 0,
        block_reason: str = "",
        anon_only: bool = False,
    ) -> None:
        self.source_site = Site(lang, site)
        self.target_site = Site("es", "wikipedia")
        self.source_user = source_user
        self.dry_run = dry_run
        self.ranges = ranges
        self.comment_pattern = re.compile(comment_pattern)
        self.verbose = verbose
        self.limit = limit
        self.block_reason = block_reason
        self.anon_only = anon_only

    def run(self) -> None:

        if self.verbose:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        if not self.dry_run:
            self.target_site.login()

        bkshow_filter = "range" if self.ranges else "ip"

        logger.info("Preloading local blocks")
        cur_blocks = ListGenerator(
            site=self.target_site,
            listaction="blocks",
            bkprop="user|reason|by|expiry|flags",
            bkshow=f"{bkshow_filter}",
            bklimit="max",
        )
        localblocks = {}
        for localblock in cur_blocks:
            if "user" not in localblock:
                logger.debug(f"autoblock: {localblock}")
                continue
            localblocks[localblock["user"]] = localblock
        logger.info(f"Preloaded {len(localblocks)} blocks")

        logger.info("Computing target blocks")
        target_blocks = []
        blocks_gen = ListGenerator(
            site=self.source_site,
            listaction="blocks",
            bkprop="user|reason|by|expiry|flags",
            bkshow=f"{bkshow_filter}|temp",
            bklimit="max",
        )
        for log in blocks_gen:
            if self.source_user and log["by"] != self.source_user:
                continue

            if "user" not in log:
                # Yes, this happens, apparently
                logger.debug(f"autoblock: {log}")
                continue
            user = log["user"]

            anononly = "anononly" in log
            nocreate = "nocreate" in log
            noemail = "noemail" in log
            allowusertalk = "allowusertalk" in log

            expiry = parse_timestamp(log["expiry"])
            if expiry <= datetime.datetime.now():
                logger.debug(f"ignore (expired): {user}")
                continue

            duration_hours = int(
                (expiry - datetime.datetime.now()).total_seconds() // 60 // 60
            )
            if not duration_hours:
                logger.debug(f"ignore (expiry too near): {user}")
                continue

            if not re.search(self.comment_pattern, log["reason"]):
                # logger.debug(f"ignore (no match): {user}")
                continue

            if self.ranges:
                if not is_net(user):
                    logger.debug(f"ignore (not range): {user}")
                    continue
            else:
                if not is_ip(user):
                    logger.debug(f"ignore (not IP): {user}")
                    continue

            if user in localblocks:
                logger.debug(f"ignore (active block): {user}")
                continue

            expiry = f"{duration_hours} hours"
            if self.block_reason:
                reason = self.block_reason
            else:
                reason = log["reason"]

            target_block = {
                "user": user,
                "expiry": expiry,
                "reason": reason,
            }
            if anononly or self.anon_only:
                target_block["anononly"] = 1
            if nocreate:
                target_block["nocreate"] = 1
            # XXX: Disable for safety
            # if noemail:
            #    target_block["noemail"] = 1
            # if allowusertalk:
            #    target_block["allowusertalk"] = 1
            target_blocks.append(target_block)
        logger.info(f"Adding {len(target_blocks)}")

        for i, target_block in enumerate(target_blocks):
            user = target_block["user"]
            expiry = target_block["expiry"]
            reason = target_block["reason"]
            logger.info(f"{i} block {user} {expiry} {reason}")
            if not self.dry_run:
                token = self.target_site.get_tokens(["csrf"])["csrf"]
                target_block = dict(target_block)
                target_block["action"] = "block"
                target_block["token"] = token
                reqblock = self.target_site._simple_request(**target_block).submit()
                logger.info(f"request: {reqblock}")
                if "error" in reqblock:
                    logger.error(f"Error in block request: {reqblock}")
                    continue
            if self.limit > 0 and i >= self.limit:
                break
        logger.info(f"Imported {i} blocks")


@click.command()
@click.option(
    "--lang",
    default="en",
    help='Language that the blocks should be imported from. Default: "en"',
)
@click.option(
    "--site",
    default="wikipedia",
    help='Domain that the blocks should be imported from. Default: "wikipedia"',
)
@click.option(
    "--dry-run/--really-run",
    required=True,
    help="Whether or not to actually execute the blocks or make a dry run.",
)
@click.option(
    "--source-user",
    required=False,
    default=None,
    help="User whose blocks should be imported. Required parameter.",
)
@click.option(
    "--ranges/--ips",
    required=False,
    default=False,
    type=bool,
    help="Copy rangeblocks instead of IP blocks",
)
@click.option(
    "--comment-pattern",
    default=".*",
    help='Regex to select only blocks containing certain strings in the block summary. Default: Import all blocks. Default: ".*".',
)
@click.option(
    "--verbose",
    is_flag=True,
    help="If specified, the script prints more verbose log messages.",
)
@click.option(
    "--limit",
    type=click.INT,
    default=0,
    help="Maximum number of blocks to make. Default: No limit.",
)
@click.option(
    "--block-reason",
    help="Block reason to use. Default: The existing local block reason.",
)
@click.option(
    "--anon-only",
    is_flag=True,
    type=bool,
    help="Always add anon. only flag to blocks.",
)
def run_cli(
    lang,
    site,
    dry_run,
    source_user,
    ranges,
    comment_pattern,
    verbose,
    limit,
    block_reason,
    anon_only,
):
    bot = CopyBlock(
        lang=lang,
        site=site,
        source_user=source_user,
        dry_run=dry_run,
        ranges=ranges,
        comment_pattern=comment_pattern,
        verbose=verbose,
        limit=limit,
        block_reason=block_reason,
        anon_only=anon_only,
    )
    bot.run()


if __name__ == "__main__":
    run_cli()
