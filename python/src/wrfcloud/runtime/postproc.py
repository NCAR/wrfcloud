#!/usr/bin/env python3

"""
Functions for setting up, executing, and monitoring a run of WRF post-processing tasks
"""

# Import our custom modules


def main(runinfo, logger):
    """Main routine that sets up, runs, and monitors post-processing end-to-end"""
    logger.info(f'Setting up post-processing for "{runinfo.name}"')

    logger.critical("This script isn't finished yet!")

if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
