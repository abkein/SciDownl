# -*- coding: utf-8 -*-
"""Command line tool of scidownl."""

import re
import sys
import argparse
from dataclasses import dataclass
from collections.abc import Sequence
from pathlib import Path
from typing import Callable, Literal, TypedDict, cast

from ..log import get_logger
from ..core.proxyspec import ProxySpec

logger = get_logger()


class DownloadTaskKwargs(TypedDict):
    source_keyword: str | int
    source_type: str
    scihub_url: str | None
    out: Path | None
    proxies: ProxySpec | None


@dataclass
class ConfigArgs:
    location: bool
    get: tuple[str, str] | None


def config(args: ConfigArgs) -> None:
    """Get global configs."""
    from ..config import get_config, GlobalConfig

    configs = get_config()
    if args.location:
        logger.info(f"Global config file path: {GlobalConfig.config_fpath}")
        return

    if args.get is not None:
        sec, key = args.get
        if sec not in configs.sections():
            logger.warning(f"Section '{sec}' is not found. Valid sections: {configs.sections()}")
            return
        value = configs[sec].get(key, None)
        if value is None:
            logger.warning(f"Key '{key} is not found. Valid keys: {list(dict(configs.items(sec)).keys())}")
            return
        logger.info(f"Value: {configs[sec][key]}")


def _run_config(args: argparse.Namespace) -> None:
    location: bool = bool(args.location)
    config_get: tuple[str, str] | None = (str(args.get[0]), str(args.get[1])) if args.get is not None else None
    config(
        ConfigArgs(
            location=location,
            get=config_get,
        )
    )


@dataclass
class DomainUpdateArgs:
    mode: str


def update_domains(args: DomainUpdateArgs) -> None:
    """Update available SciHub domains and save them to local db."""
    from ..core.updater import scihub_domain_updaters

    updater_cls = scihub_domain_updaters.get(args.mode, None)
    if updater_cls is None:
        logger.error(f"Update mode (-m) must be one of {list(scihub_domain_updaters.keys())}, got '{args.mode}' instead.")
        return
    updater = updater_cls()
    updater.update_domains()


def _run_update_domains(args: argparse.Namespace) -> None:
    update_domains(DomainUpdateArgs(mode=str(args.mode)))


def list_domains() -> None:
    """List available SciHub domains in local db."""
    from ..db.service import ScihubUrlService

    service = ScihubUrlService()
    urls = service.get_all_urls()
    urls.sort(key=lambda url: url.success_times, reverse=True)
    print(["Url", "SuccessTimes", "FailedTimes"])
    for url in urls:
        print((url.url, url.success_times, url.failed_times))


def _run_list_domains(args: argparse.Namespace) -> None:
    list_domains()


@dataclass
class DownloadArgs:
    doi: list[str]
    pmid: list[int]
    title: list[str]
    out: Path | None
    scihub_url: str | None
    proxies: list[str]


def download(args: DownloadArgs) -> None:
    """Download paper(s) by DOI or PMID."""
    from ..core.task import ScihubTask
    from ..config import get_config

    configs = get_config()

    logger.info("Run scihub tasks. Tasks information: ")
    if len(args.doi) > 0:
        logger.info("%15s: %s" % ("DOI(s)", list(args.doi)))
    if len(args.pmid) > 0:
        logger.info("%15s: %s" % ("PMID(s)", list(args.pmid)))
    if len(args.title) > 0:
        logger.info("%15s: %s" % ("TITLE(s)", list(args.title)))

    out: Path
    if args.out is None:
        out = Path("./").resolve()
        logger.info("%15s: %s" % ("Output", out.as_posix()))
    else:
        out = args.out
        logger.info("%15s: %s" % ("Output", out.as_posix()))

    if args.scihub_url is None:
        logger.info("%15s: <auto.%s>" % ("SciHub Url", configs["scihub.task"]["scihub_url_chooser_type"]))
    else:
        logger.info("%15s: %s" % ("SciHub Url", args.scihub_url))

    # Always consider out as a directory if there are multiple DOIs and PMIDs.
    # if len(doi) + len(pmid) + len(title) > 1:
    #     if out is not None and out[-1] != "/":
    #         out = out + '/'

    proxies: ProxySpec = {}
    # Load proxies configured in global configurations.
    http_proxy = configs["proxy"].get("http", None)
    if http_proxy is not None:
        proxies["http"] = http_proxy
    https_proxy = configs["proxy"].get("https", None)
    if https_proxy is not None:
        proxies["https"] = https_proxy

    # Overwrite the proxy with the user specified proxy.
    for proxy in args.proxies:
        match = re.match(r"^(\w+):\/\/([\w\.]+(?:\:\d+)?)$", proxy)
        if match is not None:
            schema: str = match.group(1)
            address: str = match.group(2)
            if schema in ProxySpec.__mutable_keys__:
                proxies[cast(Literal["all", "http", "https", "ws", "wss"], schema)] = address
            else:
                msg = f"Proxy schema must be one of {list(ProxySpec.__mutable_keys__)}, got: '{schema}'. Skipping."
                logger.error(msg)
                # raise RuntimeError(msg)
        else:
            msg = f"Invalid proxy specification. Proxy should be in form 'SCHEMA://ADDRESS[:PORT]', got: '{proxy}'. Skipping."
            logger.error(msg)
            # raise RuntimeError(msg)

    if len(proxies) > 0:
        logger.info(f"Following proxies were successfully configured: {proxies}")

    tasks: list[DownloadTaskKwargs] = []
    for doi_item in args.doi:
        tasks.append(
            {
                "source_keyword": doi_item,
                "source_type": "doi",
                "scihub_url": args.scihub_url,
                "out": out,
                "proxies": proxies,
            }
        )
    for pmid_item in args.pmid:
        tasks.append(
            {
                "source_keyword": pmid_item,
                "source_type": "pmid",
                "scihub_url": args.scihub_url,
                "out": out,
                "proxies": proxies,
            }
        )
    for title_item in args.title:
        tasks.append(
            {
                "source_keyword": title_item,
                "source_type": "title",
                "scihub_url": args.scihub_url,
                "out": out,
                "proxies": proxies,
            }
        )
    for task_kwargs in tasks:
        task = ScihubTask(**task_kwargs)
        try:
            task.run()
        except Exception:
            logger.error(f"final status: {task.context['status']}, error: {task.context['error']}")


def _run_download(args: argparse.Namespace) -> None:
    _doi: list[str] = list(args.doi) if args.doi is not None else list()
    doi: list[str] = [str(e) for e in _doi]
    _pmid: list[str] = list(args.pmid) if args.pmid is not None else list()
    pmid: list[int] = [int(e) for e in _pmid]
    _title: list[str] = list(args.title) if args.title is not None else list()
    title: list[str] = [str(e) for e in _title]
    out: Path | None = Path(args.out) if args.out is not None else None
    scihub_url: str | None = str(args.scihub_url) if args.scihub_url is not None else None
    _proxies: list[str] = list(args.proxy) if args.proxy is not None else list()
    proxies: list[str] = [str(e) for e in _proxies]
    download(
        DownloadArgs(
            doi=doi,
            pmid=pmid,
            title=title,
            out=out,
            scihub_url=scihub_url,
            proxies=proxies,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the scidownl command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="scidownl",
        description="Command line tool to download pdfs from Scihub.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    config_parser = subparsers.add_parser("config", help="Get global configs.", description="Get global configs.")
    config_parser.add_argument("-l", "--location", action="store_true", help="Show the location of global config file.")
    config_parser.add_argument(
        "-g",
        "--get",
        nargs=2,
        metavar=("section", "key"),
        help="Get config by section and key, usage: --get <section> <key>.",
    )
    config_parser.set_defaults(func=_run_config)

    update_parser = subparsers.add_parser(
        "update",
        help="Update available SciHub domains and save them to local db.",
        description="Update available SciHub domains and save them to local db.",
    )
    update_parser.add_argument(
        "-m",
        "--mode",
        choices=["crawl", "search"],
        default="crawl",
        help="update mode, could be 'crawl' or 'search', default mode is 'crawl'.",
    )
    update_parser.set_defaults(func=_run_update_domains)

    list_parser = subparsers.add_parser(
        "list",
        help="List available SciHub domains in local db.",
        description="List available SciHub domains in local db.",
    )
    list_parser.set_defaults(func=_run_list_domains)

    download_parser = subparsers.add_parser(
        "download",
        help="Download paper(s) by DOI or PMID.",
        description="Download paper(s) by DOI or PMID.",
    )
    download_parser.add_argument(
        "-d",
        "--doi",
        action="append",
        help="DOI string. Specifying multiple DOIs is supported, e.g., --doi FIRST_DOI --doi SECOND_DOI ... ",
    )
    download_parser.add_argument(
        "-p",
        "--pmid",
        action="append",
        type=int,
        help="PMID numbers. Specifying multiple PMIDs is supported, e.g., --pmid FIRST_PMID --pmid SECOND_PMID ...",
    )
    download_parser.add_argument(
        "-t",
        "--title",
        action="append",
        help="Title string. Specifying multiple titles is supported, e.g., --title FIRST_TITLE --title SECOND_TITLE ...",
    )
    download_parser.add_argument(
        "-o",
        "--out",
        type=Path,
        help="Output directory or file path, which could be an absolute path "
        "or a relative path. "
        "Output directory examples: /absolute/path/to/download/, ./relative/path/to/download/, "
        "Output file examples: /absolute/dir/paper.pdf, ../relative/dir/paper.pdf. "
        "If --out is not specified, paper will be downloaded to the current directory "
        "with the file name of the paper's title. "
        "If multiple DOIs or multiple PMIDs are provided, the --out option is always considered "
        "as the output directory, rather than the output file path.",
    )
    download_parser.add_argument(
        "-u",
        "--scihub-url",
        help="Scihub domain url. If not specified, automatically choose one from local saved domains. It's recommended to leave this option empty.",
    )
    download_parser.add_argument(
        "-x",
        "--proxy",
        action="append",
        help="Proxy with the format of SCHEMA://ADDRESS[:PORT]. e.g., --proxy http://127.0.0.1:7890.",
        default=[],
    )
    download_parser.set_defaults(func=_run_download)

    return parser


def cli(argv: Sequence[str] | None = None) -> None:
    """Command line tool to download pdfs from Scihub."""
    parser = build_parser()
    args_list = list(sys.argv[1:] if argv is None else argv)
    if not args_list:
        parser.print_help()
        return
    args = parser.parse_args(args_list)
    handler = cast(Callable[[argparse.Namespace], None], args.func)
    handler(args)


if __name__ == "__main__":
    cli()
