#!/usr/bin/python

import collections
import les_logger
import json

# JSON layout
#{
#	"Base": 
#	[
# 	{ "Op" : "<operation>", "Pattern" : "<file_pattern>" },
# 	{ "Op" : "<operation>", "Pattern" : "<file_pattern>" },
# 	{ "Op" : "<operation>", "Pattern" : "<file_pattern>", "<optional_tag>" : "<value>" }
#	]
#}

# <operation> : "Valid", "Invalid", "Exists"
# <file_pattern> : ** -means wildcard including directories e.g. recursive, **.* : means everything
# <optional_tag> : one of
#		"MinSizeKB" : "<minimum_size_in_KB>"

# JSON layout
#{
#	"Base": 
#	[
#		{	"Op": "Invalid", "Pattern" : "<file_pattern>"  },
#		{	"Op": "Valid", "Pattern" : "<file_pattern>" },
#		{	"Op": "Exists", "Pattern" : "<file_pattern>", "MinSizeKB" : "<minimum_size_in_KB>" },
#		{	"Op": "Exists", "Pattern" : "<file_pattern>" } # implies MinSizeKB = 0
#	]
#}

RULE_OPERATION_UNKNOWN = 0
RULE_OPERATION_INVALID = 1
RULE_OPERATION_VALID = 2
RULE_OPERATION_EXISTS = 3
RULE_OPERATION_MINSIZE = 4
RULE_OPERATION_JSON_PRIMARY_TAGS = ["Op", "Pattern"]
RULE_OPERATION_JSON_SECONDARY_OPERATIONS = ["MinSizeKB"]

RULE_OPERATION_COMBINED_JSON_TAGS = RULE_OPERATION_JSON_PRIMARY_TAGS + RULE_OPERATION_JSON_SECONDARY_OPERATIONS
RULE_OPERATION_STRINGS = {}
RULE_OPERATION_STRINGS["Invalid"] = RULE_OPERATION_INVALID
RULE_OPERATION_STRINGS["Valid"] = RULE_OPERATION_VALID
RULE_OPERATION_STRINGS["Exists"] = RULE_OPERATION_EXISTS
RULE_OPERATION_STRINGS["MinSizeKB"] = RULE_OPERATION_MINSIZE

RULE_OPERATION_IDS = {}
RULE_OPERATION_IDS[RULE_OPERATION_INVALID] = "Invalid"
RULE_OPERATION_IDS[RULE_OPERATION_VALID] = "Valid"
RULE_OPERATION_IDS[RULE_OPERATION_EXISTS] = "Exists"
RULE_OPERATION_IDS[RULE_OPERATION_MINSIZE] = "MinSizeKB"

class Rule():
	def __init__(self):
		self.__m_operation = RULE_OPERATION_INVALID
		self.__m_pattern = ""
		self.__m_value = 0
		self.__m_usesValue = False

	def ParseRule(self, ruleEntry):
		self.__m_operation = RULE_OPERATION_INVALID
		self.__m_pattern = ""
		self.__m_value = 0
		self.__m_usesValue = False
		#les_logger.Log("%s", ruleEntry)
		keys = ruleEntry.keys()
		MAX_NUM_KEYS = 3
		numKeys = len(keys)
		if numKeys > MAX_NUM_KEYS:
			les_logger.Error("Invalid Rule Format too many tags %d Maximum is %d", numKeys, MAX_NUM_KEYS)
			les_logger.Error("Rule: '%s.", ruleEntry)
			return False

		for k in keys:
			if k not in RULE_OPERATION_COMBINED_JSON_TAGS:
				les_logger.Error("Unknown Rule Operation Tag: '%s'", k)
				les_logger.Error("Rule: '%s.", ruleEntry)
				return False

		OPERATION_TAG = "Op"
		PATTERN_TAG = "Pattern"

		if OPERATION_TAG not in keys:
			les_logger.Error("Invalid Rule 'Op' tag not found")
			les_logger.Error("Rule: '%s.", ruleEntry)
			return False

		if PATTERN_TAG not in keys:
			les_logger.Error("Invalid Rule 'Pattern' tag not found")
			les_logger.Error("Rule: '%s.", ruleEntry)
			return False

		operation = ruleEntry[OPERATION_TAG]
		pattern = ruleEntry[PATTERN_TAG]

		validExtraKeys = []
		MAX_NUM_KEYS = 2
		if operation == "Exists":
			validExtraKeys.append("MinSizeKB")
			MAX_NUM_KEYS = 3

		if numKeys > MAX_NUM_KEYS:
			les_logger.Error("Invalid Rule Format too many tags %d Maximum is %d", numKeys, MAX_NUM_KEYS)
			les_logger.Error("Rule: '%s.", ruleEntry)
			return False

		for k in keys:
			if k not in RULE_OPERATION_JSON_PRIMARY_TAGS:
				if k not in validExtraKeys:
					les_logger.Error("Invalid Rule Operation Tag Found: '%s'", k)
					if k == "MinSizeKB":
						les_logger.Error("'%s' can be only be used with 'Exists' operation", k)
					les_logger.Error("Rule: '%s'", ruleEntry)
					return False

		if operation not in RULE_OPERATION_STRINGS:
			les_logger.Error("Invalid Rule Operation Found: '%s'", operation)
			les_logger.Error("Rule: '%s'", ruleEntry)
			return False

		value = 0
		MINSIZEKB_TAG = "MinSizeKB"
		if MINSIZEKB_TAG in validExtraKeys:
			if MINSIZEKB_TAG in keys:
				operation = MINSIZEKB_TAG
				value = ruleEntry[MINSIZEKB_TAG]
				self.__m_usesValue = True

		self.__m_operation = RULE_OPERATION_STRINGS[operation]
		self.__m_pattern = pattern
		self.__m_value = int(value)

		return True

	def Print(self):
		operation = self.__m_operation
		pattern = self.__m_pattern
		value = self.__m_value
		opString = RULE_OPERATION_IDS[operation]
		msg = "Op:'%s' Pattern:'%s'" % (opString, pattern)
		if self.__m_usesValue:
			msg += " Value:%d" % (value)
		les_logger.Log(msg)

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
		#les_logger.Log("%s", fileDict)
		self.__m_name = rulesName
		self.__m_rules = []
		rules = []
		error = False
		for ruleEntry in fileDict[rulesName]:
			rule = Rule()
			if rule.ParseRule(ruleEntry) == False:
				error = True
				break;
			rules.append(rule)

		if error == False:
			self.__m_rules = rules
		return error

	def Print(self):
		print "Rules:", self.__m_name
		for rule in self.__m_rules:
			rule.Print()

def Init():
	les_logger.Init("log.txt")
	verbose = True
	les_logger.SetConsoleOutput(les_logger.CHANNEL_LOG, verbose)
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_WARNING, "warning.txt")
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_ERROR, "error.txt")
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_LOG, "log.txt")

	rules = Rules("data/ce_base.txt")
	rules.Print()

def runMain():
	Init()

if __name__ == '__main__':
	runMain()
