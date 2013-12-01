#!/usr/bin/python

import les_logger
import json

class Rules():
	def __init__(self, fileName):
		self.__m_sourceFile = fileName
		self.__m_name = ""
		self.__m_rules = []
		self.__Load__()

	def __Load__(self):
		fh = open(self.__m_sourceFile, "r")
		if fh != None:
			fileDict = json.load(fh)
		fh.close()
		rulesName = fileDict.keys()[0]
		self.__m_name = rulesName
		for rule in fileDict[rulesName]:
			for operation, value in rule.items():
				ruleEntry = (operation, value)
				self.__m_rules.append(ruleEntry)

	def Print(self):
		print "Rules:", self.__m_name
		for rule in self.__m_rules:
			(operation, value) = rule
			print operation, ":", value

def Init():
	les_logger.Init("log.txt")
	verbose = True
	les_logger.SetConsoleOutput(les_logger.CHANNEL_LOG, verbose)
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_WARNING, "warning.txt")
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_ERROR, "error.txt")
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_LOG, "log.txt")

	rules = Rules("ce_base.txt")
	rules.Print()

def runMain():
	Init()

if __name__ == '__main__':
	runMain()
