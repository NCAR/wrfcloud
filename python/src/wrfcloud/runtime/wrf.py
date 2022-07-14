#!/usr/bin/env python3

"""
Functions for setting up, executing, and monitoring a run of the WRF model
"""

# Import our custom modules


def main(runinfo, logger):
    """Main routine that sets up, runs, and monitors WRF end-to-end"""
    logger.info(f'Setting up WRF for "{runinfo.name}"')

    logger.warning(f"{__name__} isn't fully implemented yet!")

if __name__ == "__main__":
    print('Script not yet set up for standalone run, exiting...')
