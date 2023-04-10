"""Call to main to be containerized."""

import click

from fantasy_footballer import run_app

@click.command()
def main():
    run_app()

if __name__ == "__main__":
    main()
