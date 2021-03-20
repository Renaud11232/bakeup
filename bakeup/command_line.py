import argparse
from bakeup import BakeUp


def main():
    parser = argparse.ArgumentParser(description="Starts the backup process")
    parser.add_argument("--config", type=str, required=True)
    args = parser.parse_args()
    bake_up = BakeUp(args.config)
    bake_up.cook()
