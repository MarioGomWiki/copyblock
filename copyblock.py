#!/usr/bin/env python3

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
    ) -> None:
        self.site = Site(lang, site)
        self.meta = Site("meta", "meta")
        self.eswiki = Site("es", "wikipedia")
        self.source_user = source_user
        self.dry_run = dry_run
        self.ranges = ranges
        self.comment_pattern = re.compile(comment_pattern)
        self.verbose = verbose
        self.limit = limit
        self.block_reason = block_reason

    def run(self) -> None:
        if not self.dry_run:
            self.site.login()
            self.meta.login()
            self.eswiki.login()

        bkshow_filter = "range" if self.ranges else "ip"

        print("Preloading local blocks...")
        cur_blocks = ListGenerator(
            site=self.eswiki,
            listaction="blocks",
            bkprop="user|reason|by|expiry|flags",
            bkshow=f"{bkshow_filter}",
            bklimit="max",
        )
        localblocks = {}
        for localblock in cur_blocks:
            if self.verbose and "user" not in localblock:
                print("autoblock", localblock)
                continue
            elif "user" not in localblock:
                continue
            localblocks[localblock["user"]] = localblock
        print(f"Preloaded {len(localblocks)} blocks")

        print("Computing target blocks...")
        target_blocks = []
        blocks_gen = ListGenerator(
            site=self.site,
            listaction="blocks",
            bkprop="user|reason|by|expiry|flags",
            bkshow=f"{bkshow_filter}|temp",
            bklimit="max",
        )
        for log in blocks_gen:
            if self.source_user and log["by"] != self.source_user:
                continue

            if self.verbose and "user" not in log:
                # Yes, this happens, apparently
                print("autoblock", log)
                continue
            elif "user" not in log:
                continue
            user = log["user"]

            anononly = "anononly" in log
            nocreate = "nocreate" in log
            noemail = "noemail" in log
            allowusertalk = "allowusertalk" in log

            expiry = parse_timestamp(log["expiry"])
            if expiry <= datetime.datetime.now():
                if self.verbose:
                    print("ignore (expired)", user)
                continue

            duration_hours = int(
                (expiry - datetime.datetime.now()).total_seconds() // 60 // 60
            )
            if not duration_hours:
                if self.verbose:
                    print("ignore (expiry too near)", user)
                continue

            if not re.search(self.comment_pattern, log["reason"]):
                if self.verbose:
                    # print("ignore (no match)", user)
                    pass
                continue

            if self.ranges:
                if not is_net(user):
                    if self.verbose:
                        print("ignore (not range)", user)
                    continue
            else:
                if not is_ip(user):
                    if self.verbose:
                        print("ignore (not IP)", user)
                    continue

            if user in localblocks:
                if self.verbose:
                    print("ignore (active block)", user)
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
            if anononly:
                target_block["anononly"] = 1
            if nocreate:
                target_block["nocreate"] = 1
            if noemail:
                target_block["noemail"] = 1
            if allowusertalk:
                target_block["allowusertalk"] = 1
            target_blocks.append(target_block)
        print(f"Adding {len(target_blocks)}...")

        if not self.dry_run:
            if len(target_blocks) > 5:
                if self.limit and self.limit > 5:
                    print("Adding flood flag...")
                    print(
                        self.eswiki._simple_request(
                            action="userrights",
                            format="json",
                            user=self.eswiki.username(),
                            add="flood",
                            reason="Bloqueos masivos",  # Add a parameter here?
                            token=self.eswiki.get_tokens(["userrights"])["userrights"],
                        ).submit()
                    )
                elif self.limit and self.limit <= 5:
                    pass
                else:
                    print("Adding flood flag...")
                    print(
                        self.eswiki._simple_request(
                            action="userrights",
                            format="json",
                            user=self.eswiki.username(),
                            add="flood",
                            reason="Bloqueos masivos",  # Add a parameter here?
                            token=self.eswiki.get_tokens(["userrights"])["userrights"],
                        ).submit()
                    )

        for i, target_block in enumerate(target_blocks):
            user = target_block["user"]
            expiry = target_block["expiry"]
            reason = target_block["reason"]
            print(i, "block", user, expiry, reason)
            if not self.dry_run:
                token = self.eswiki.get_tokens(["csrf"])["csrf"]
                target_block = dict(target_block)
                target_block["action"] = "block"
                target_block["token"] = token
                reqblock = self.eswiki._simple_request(**target_block).submit()
                print(reqblock)
                if "error" in reqblock:
                    print("ERROR", reqblock)
                    continue
            if self.limit > 0 and i >= self.limit:
                if self.limit > 5 and not self.dry_run:
                    print(
                        self.eswiki._simple_request(
                            action="userrights",
                            format="json",
                            user=self.site.username(),
                            remove="flood",
                            reason="Done",  # Add a parameter here?
                            token=self.eswiki.get_tokens(["userrights"])["userrights"],
                        ).submit()
                    )
                return

        if not self.dry_run:
            if len(target_blocks) > 5:
                print(
                    self.eswiki._simple_request(
                        action="userrights",
                        format="json",
                        user=self.site.username(),
                        remove="flood",
                        reason="Done",  # Add a parameter here?
                        token=self.eswiki.get_tokens(["userrights"])["userrights"],
                    ).submit()
                )


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
    )
    bot.run()


if __name__ == "__main__":
    run_cli()
