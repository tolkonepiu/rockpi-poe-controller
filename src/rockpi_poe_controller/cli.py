"""Command-line interface for ROCK Pi PoE HAT controller."""

import argparse
import logging
import sys

from .config import Config
from .controller import FanController

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ROCK Pi 23W PoE HAT Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start                    # Start fan controller
  %(prog)s stop                     # Stop fan controller
        """
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands")

    # Start command
    subparsers.add_parser("start", help="Start fan controller")

    # Stop command
    subparsers.add_parser("stop", help="Stop fan controller")

    return parser


def start_controller() -> None:
    try:
        config = Config()
        setup_logging(config.log_level)

        controller = FanController(config)
        logger.info("Starting fan controller")
        controller.start()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error("Failed to start controller: %s", str(e))
        sys.exit(1)


def stop_controller() -> None:
    try:
        config = Config()
        setup_logging(config.log_level)

        controller = FanController(config)
        controller.stop()
        logger.info("Fan controller stopped")

    except Exception as e:
        logger.error("Failed to stop controller: %s", str(e))
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "start":
            start_controller()
        elif args.command == "stop":
            stop_controller()
        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
