import sys
from pathlib import Path


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

    from chiron_backend.agents.worker import main as worker_main

    worker_main()


if __name__ == "__main__":
    main()
