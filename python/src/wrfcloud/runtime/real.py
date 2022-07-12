#!/usr/bin/env python3

"""
Functions for setting up, executing, and monitoring a run of the 'real.exe' WRF pre-processing program
"""

# Import our custom modules


def main(runinfo, logger):
    """Main routine that sets up, runs, and monitors real.exe end-to-end"""
    logger.info(f'Setting up real.exe for "{runinfo.name}"')

    logger.warning("This script isn't finished yet!")

if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
