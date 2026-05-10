# -*- coding: utf-8 -*-
"""Command line tool of scidownl."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Callable, TypedDict, cast

from ..log import get_logger

logger = get_logger()


class DownloadTaskKwargs(TypedDict):
    source_keyword: str | int
    source_type: str
    scihub_url: str | None
    out: Path | None
    proxies: dict[str, str]


def config(location: bool, get: tuple[str, str] | None) -> None:
    """Get global configs."""
    from ..config import get_config, GlobalConfig

    configs = get_config()
    if location:
        logger.info(f"Global config file path: {GlobalConfig.config_fpath}")
        return

    if get:
        sec, key = get
        if sec not in configs.sections():
            logger.warning(f"Section '{sec}' is not found. Valid sections: {configs.sections()}")
            return
        value = configs[sec].get(key, None)
        if value is None:
            logger.warning(f"Key '{key} is not found. Valid keys: {list(dict(configs.items(sec)).keys())}")
            return
        logger.info(f"Value: {configs[sec][key]}")


def update_domains(mode: str) -> None:
    """Update available SciHub domains and save them to local db."""
    from ..core.updater import scihub_domain_updaters

    updater_cls = scihub_domain_updaters.get(mode, None)
    if updater_cls is None:
        logger.error(f"Update mode (-m) must be one of {list(scihub_domain_updaters.keys())}, got '{mode}' instead.")
        return
    updater = updater_cls()
    updater.update_domains()


def list_domains() -> None:
    """List available SciHub domains in local db."""
    from ..db.service import ScihubUrlService

    service = ScihubUrlService()
    urls = service.get_all_urls()
    urls.sort(key=lambda url: url.success_times, reverse=True)
    print(["Url", "SuccessTimes", "FailedTimes"])
    for url in urls:
        print((url.url, url.success_times, url.failed_times))


def download(
    doi: tuple[str, ...],
    pmid: tuple[int, ...],
    title: tuple[str, ...],
    out: Path | None,
    scihub_url: str | None,
    proxy: str | None,
) -> None:
    """Download paper(s) by DOI or PMID."""
    from ..core.task import ScihubTask
    from ..config import get_config

    configs = get_config()

    logger.info("Run scihub tasks. Tasks information: ")
    if len(doi) > 0:
        logger.info("%15s: %s" % ("DOI(s)", list(doi)))
    if len(pmid) > 0:
        logger.info("%15s: %s" % ("PMID(s)", list(pmid)))
    if len(title) > 0:
        logger.info("%15s: %s" % ("TITLE(s)", list(title)))

    if out is None:
        logger.info("%15s: %s" % ("Output", Path("./").resolve().as_posix()))
    else:
        logger.info("%15s: %s" % ("Output", out))

    if scihub_url is None:
        logger.info("%15s: <auto.%s>" % ("SciHub Url", configs["scihub.task"]["scihub_url_chooser_type"]))
    else:
        logger.info("%15s: %s" % ("SciHub Url", scihub_url))

    # Always consider out as a directory if there are multiple DOIs and PMIDs.
    # if len(doi) + len(pmid) + len(title) > 1:
    #     if out is not None and out[-1] != "/":
    #         out = out + '/'

    proxies: dict[str, str] = {}
    # Load proxies configured in global configurations.
    http_proxy = configs["proxy"].get("http")
    if http_proxy is not None:
        proxies["http"] = http_proxy
    https_proxy = configs["proxy"].get("https")
    if https_proxy is not None:
        proxies["https"] = https_proxy

    # Overwrite the proxy with the user specified proxy.
    if proxy is not None and "=" in proxy:
        scheme, proxy_address = proxy.split("=")[:2]
        proxies[scheme] = proxy_address

    if len(proxies) > 0:
        logger.info(f"Proxies: {proxies}")

    tasks: list[DownloadTaskKwargs] = []
    for doi_item in doi:
        tasks.append(
            {
                "source_keyword": doi_item,
                "source_type": "doi",
                "scihub_url": scihub_url,
                "out": out,
                "proxies": proxies,
            }
        )
    for pmid_item in pmid:
        tasks.append(
            {
                "source_keyword": pmid_item,
                "source_type": "pmid",
                "scihub_url": scihub_url,
                "out": out,
                "proxies": proxies,
            }
        )
    for title_item in title:
        tasks.append(
            {
                "source_keyword": title_item,
                "source_type": "title",
                "scihub_url": scihub_url,
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


class ConfigArgs(argparse.Namespace):
    location: bool
    get: list[str] | None


class DomainUpdateArgs(argparse.Namespace):
    mode: str


class DownloadArgs(argparse.Namespace):
    doi: list[str] | None
    pmid: list[int] | None
    title: list[str] | None
    out: Path | None
    scihub_url: str | None
    proxy: str | None


def _run_config(args: argparse.Namespace) -> None:
    typed_args = cast(ConfigArgs, args)
    config_get = (typed_args.get[0], typed_args.get[1]) if typed_args.get is not None else None
    config(location=typed_args.location, get=config_get)


def _run_update_domains(args: argparse.Namespace) -> None:
    typed_args = cast(DomainUpdateArgs, args)
    update_domains(mode=typed_args.mode)


def _run_list_domains(args: argparse.Namespace) -> None:
    list_domains()


def _run_download(args: argparse.Namespace) -> None:
    typed_args = cast(DownloadArgs, args)
    download(
        doi=tuple(typed_args.doi or ()),
        pmid=tuple(typed_args.pmid or ()),
        title=tuple(typed_args.title or ()),
        out=typed_args.out,
        scihub_url=typed_args.scihub_url,
        proxy=typed_args.proxy,
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
        "domain.update",
        help="Update available SciHub domains and save them to local db.",
        description="Update available SciHub domains and save them to local db.",
    )
    update_parser.add_argument(
        "-m",
        "--mode",
        default="crawl",
        help="update mode, could be 'crawl' or 'search', default mode is 'crawl'.",
    )
    update_parser.set_defaults(func=_run_update_domains)

    list_parser = subparsers.add_parser(
        "domain.list",
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
        help="Proxy with the format of SCHEME=PROXY_ADDRESS. e.g., --proxy http=http://127.0.0.1:7890.",
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
