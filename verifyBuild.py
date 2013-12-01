#!/usr/bin/python

import les_logger

def runMain():
	les_logger.Init("log.txt")
	verbose = True
	les_logger.SetConsoleOutput(les_logger.CHANNEL_LOG, verbose)
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_WARNING, "warning.txt")
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_ERROR, "error.txt")
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_LOG, "log.txt")

if __name__ == '__main__':
	runMain()
