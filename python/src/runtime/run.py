#!/usr/bin/env python3

"""
Wrapper script for creating, submitting, and monitoring runs of the wrfcloud framework.
"""

import logging

def setup_logging(logdir=''):
    """
    Sets up logging for a new run. This should be the first action in main() to ensure
    that all actions are properly logged.
    """
    logging.basicConfig(level = logging.DEBUG,
                        format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt = '%m-%d %H:%M',
                        filename = logdir + 'debug.log',
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger().addHandler(console)

def main():
    """Main routine that creates a new run and monitors it through completion"""
    setup_logging()
    logging.info('Starting new run')



    logging.critical("This script isn't finished yet!")

if __name__ == "__main__":
    main()
