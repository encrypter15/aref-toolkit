#!/usr/bin/env python3
import argparse
import sys
import json
import threading
import os
import re
import logging
from queue import Queue
from modules import passive_recon, active_recon, ml_analyzer, report_generator, cloud_recon
from plugins import load_plugins
from src.encrypt_creds import decrypt_file

logging.basicConfig(filename="logs/aref.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def setup_parser():
    parser = argparse.ArgumentParser(description="AREF-Toolkit Prometheus: Adaptive Recon and Exploitation")
    subparsers = parser.add_subparsers(dest="command")
    
    recon = subparsers.add_parser("recon", help="Run reconnaissance")
    recon.add_argument("--target", required=True, help="Target domain or IP")
    recon.add_argument("--passive", action="store_true", help="Run passive recon")
    recon.add_argument("--active", action="store_true", help="Run active recon")
    recon.add_argument("--cloud", action="store_true", help="Run cloud recon")
    recon.add_argument("--ml", action="store_true", help="Run ML analysis")
    recon.add_argument("--report", action="store_true", help="Generate report")
    recon.add_argument("--profile", default="default", help="Config profile")
    recon.add_argument("--plugin", help="Run specific plugin")
    recon.add_argument("--verbose", action="store_true", help="Verbose output")
    recon.add_argument("--quiet", action="store_true", help="Minimal output")
    
    return parser

def worker(queue, results, func, profile):
    while not queue.empty():
        target = queue.get()
        try:
            results[target] = func(target, profile)
        except Exception as e:
            logging.error(f"Worker failed on {target}: {e}")
        queue.task_done()

def run_parallel(targets, func, profile):
    queue = Queue()
    results = {}
    for t in targets: queue.put(t)
    threads = min(profile["threads"], len(targets))
    for _ in range(threads):
        t = threading.Thread(target=worker, args=(queue, results, func, profile))
        t.start()
    queue.join()
    return results

def validate_target(target):
    domain_pattern = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"
    ip_pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    if not (re.match(domain_pattern, target) or re.match(ip_pattern, target)):
        logging.error(f"Invalid target: {target}")
        print(f"[-] Invalid target: {target}")
        sys.exit(1)
    return target

def validate_credentials(creds):
    required = {"aws": ["access_key", "secret_key"], "gcp": ["project_id"], "azure": ["subscription_id"]}
    for provider, fields in required.items():
        if provider in creds:
            for field in fields:
                if not creds[provider].get(field):
                    logging.error(f"Missing {field} in {provider} creds")
                    print(f"[-] Missing {field} in {provider} creds")
                    sys.exit(1)
    return creds

def log_print(message, args):
    if args.verbose:
        print(f"[*] {message}")
    elif not args.quiet:
        print(f"[+] {message}")
    logging.info(message)

def main():
    parser = setup_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    target = validate_target(args.target)
    with open("config/profiles.json", "r") as f:
        profiles = json.load(f)
    profile = profiles.get(args.profile, profiles["default"])
    
    passphrase = os.getenv("CREDS_PASSPHRASE")
    if not passphrase:
        log_print("CREDS_PASSPHRASE env var required.", args)
        sys.exit(1)
    creds = validate_credentials(decrypt_file(passphrase))
    profile["credentials"] = creds

    if not os.getenv("SHODAN_API_KEY"):
        log_print("SHODAN_API_KEY env var required.", args)
        sys.exit(1)

    results = {}
    plugins = load_plugins() if args.plugin else {}

    if args.passive or not (args.active or args.cloud or args.ml or args.report):
        log_print("Running passive recon...", args)
        results["passive"] = run_parallel([target], passive_recon.run, profile)[target]

    if args.active:
        log_print("Running active recon...", args)
        results["active"] = run_parallel([target], active_recon.run, profile)[target]

    if args.cloud:
        log_print("Running cloud recon...", args)
        results["cloud"] = run_parallel([target], cloud_recon.run, profile)[target]

    if args.ml and "passive" in results:
        log_print("Analyzing with ML...", args)
        results["ml"] = ml_analyzer.analyze(results["passive"], profile)

    if args.plugin and args.plugin in plugins:
        log_print(f"Running plugin: {args.plugin}", args)
        results["plugin"] = plugins[args.plugin](target, profile)

    if args.report and results:
        log_print("Generating report...", args)
        report_generator.generate(target, results, args)

    if not results:
        log_print("Nothing to do. Use --help for options.", args)
        sys.exit(1)

if __name__ == "__main__":
    main()
