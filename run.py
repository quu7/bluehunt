#!/usr/bin/env python3

import subprocess
import argparse
from bluehunt import settings


parser = argparse.ArgumentParser(
    description="Start Bluehunt.",
    epilog="You can exit the program by pressing CONTROL-C on your keyboard.",
)
parser.add_argument(
    "--reset",
    help="Delete all user data from this installation.",
    action="store_true",
)
args = parser.parse_args()


def main(args):
    BASE_DIR = settings.BASE_DIR
    MEDIA_ROOT = settings.MEDIA_ROOT
    db = settings.DATABASES["default"]["NAME"]

    if db.exists() and args.reset:
        db.unlink(missing_ok=True)

    if not db.exists():
        print("\n\tMigrating database...\n")
        migration = subprocess.run(
            ["pipenv", "run", "python", "manage.py", "migrate"],
            cwd=BASE_DIR,
        )

    print("\n\tStarting server...\n")
    runserver = subprocess.run(
        ["pipenv", "run", "python", "manage.py", "runserver"],
        cwd=BASE_DIR,
    )


if __name__ == "__main__":
    # execute only if run as a script
    main(args)
