"""Run queue resync for a specific counter from terminal.

Usage:
	python -m scripts.resync_queue --counter-id 1
"""

import argparse

from app.core.database import SessionLocal
from app.services.queue_service import QueueService


def main() -> None:
	parser = argparse.ArgumentParser(description="Resync queue estimates for a counter")
	parser.add_argument("--counter-id", type=int, required=True, help="Counter ID to resync")
	args = parser.parse_args()

	db = SessionLocal()
	try:
		QueueService(db).resync_queue_for_counter(args.counter_id)
		print(f"Queue resync completed for counter_id={args.counter_id}")
	finally:
		db.close()


if __name__ == "__main__":
	main()


