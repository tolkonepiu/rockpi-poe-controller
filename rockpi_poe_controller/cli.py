"""Command-line interface for ROCK Pi PoE HAT controller."""

import argparse
import sys

import structlog

from .config import Config
from .controller import FanController

logger = structlog.get_logger(__name__)


def setup_logging(log_level: str = "INFO", log_format: str = "text") -> None:
    """Setup structured logging.

    Args:
        log_level: Logging level
        log_format: Log format (json or text)
    """
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
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
    start_parser = subparsers.add_parser("start", help="Start fan controller")
    start_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level"
    )
    start_parser.add_argument(
        "--log-format",
        choices=["text", "json"],
        default="text",
        help="Log format"
    )

    # Stop command
    subparsers.add_parser("stop", help="Stop fan controller")

    return parser


def start_controller(args: argparse.Namespace) -> None:
    """Start the fan controller.

    Args:
        args: Command line arguments
    """
    try:
        config = Config.from_env()
        setup_logging(args.log_level, args.log_format)

        controller = FanController(config)
        logger.info("Starting fan controller")
        controller.start()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error("Failed to start controller", error=str(e))
        sys.exit(1)


def stop_controller(args: argparse.Namespace) -> None:
    """Stop the fan controller.

    Args:
        args: Command line arguments
    """
    try:
        config = Config.from_env()
        controller = FanController(config)
        controller.stop()
        logger.info("Fan controller stopped")

    except Exception as e:
        logger.error("Failed to stop controller", error=str(e))
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
            start_controller(args)
        elif args.command == "stop":
            stop_controller(args)
        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
