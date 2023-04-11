"""Call to main to be containerized."""

from fantasy_footballer import run_app


def main():
    """Docker image's top level method."""
    run_app()


if __name__ == "__main__":
    main()
