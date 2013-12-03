#!/usr/bin/python

import collections
import les_logger
import json
import os

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
# <file_pattern> : 
#			* - means non-recursive wildcard e.g. just matches the dirname or filename or extension
#			** -means wildcard including directories e.g. recursive, 
#			**.* : means everything
#			The character after ** must be / or . - can't do **level.pak
#
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
		self.__m_patternObj = None
		self.__m_value = 0
		self.__m_usesValue = False

	def __ParsePattern(self, pattern):
		dirPart = ""
		filePart = ""
		extPart = ""

		tempStr = pattern

		extInd = tempStr.find(".")
		if extInd != -1:
			extPart = tempStr[extInd+1:]
			tempStr = tempStr[0:extInd]

		dirInd = tempStr.rfind("/")
		if dirInd == 0:
			filePart = tempStr
		elif dirInd > 0:
			dirPart = tempStr[0:dirInd]
			tempStr = tempStr[dirInd+1:]
			filePart = tempStr
		else:
			filePart = tempStr

		wildInd = filePart.rfind("**")
		if wildInd != -1:
			if len(dirPart) > 0:
				dirPart += "/"
			dirPart += "**"
			filePart = filePart[wildInd:].replace("**", "*", 1)

		if extPart.find("**") != -1:
			les_logger.Error("Illegal extension '%s' can't contain '**'", extPart);
			return None;

		if 0:
			les_logger.Log("dirPart: '%s'", dirPart)
			les_logger.Log("filePart: '%s'", filePart)
			les_logger.Log("extPart: '%s'", extPart)

		return (dirPart, filePart, extPart)

	def ParseRule(self, ruleEntry):
		self.__m_operation = RULE_OPERATION_INVALID
		self.__m_patternObj = None
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
		operation = operation.strip()
		pattern = pattern.strip()

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
				value = value.strip()
				self.__m_usesValue = True

		pattern = pattern.strip()
		pattern = pattern.replace("\\", "/")
		while (pattern.find("//") != -1):
		 pattern = pattern.replace("//", "/")

		patternObj = self.__ParsePattern(pattern)
		if patternObj == None:
			les_logger.Error("Invalid pattern found: '%s'", pattern)
			les_logger.Error("Rule: '%s'", ruleEntry)
			return False

		self.__m_operation = RULE_OPERATION_STRINGS[operation]
		self.__m_pattern = pattern
		self.__m_patternObj = patternObj
		self.__m_value = int(value)

		return True

	def ToString(self):
		operation = self.__m_operation
		pattern = self.__m_pattern
		patternObj = self.__m_patternObj
		dirPart = ""
		filePart = ""
		extPart = ""
		if patternObj != None:
			(dirPart, filePart, extPart) = patternObj

		value = self.__m_value
		opString = RULE_OPERATION_IDS[operation]
		msg = "Op:'%s' Pattern:'%s' Dir:'%s' File:'%s' Ext:'%s'" % (opString, pattern, dirPart, filePart, extPart)
		if self.__m_usesValue:
			msg += " Value:%d" % (value)
		return msg

	def Print(self):
		les_logger.Log(self.ToString())

	def Validate(self, d, f, e):
		return False

class Rules():
	def __init__(self, fileName):
		self.__m_sourceFile = fileName
		self.__m_name = ""
		self.__m_rules = []
		self.__Load__()

	def GetName(self):
		return self.__m_name

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
		les_logger.Log("Rules: '%s'", self.__m_name)
		for rule in self.__m_rules:
			msg = rule.Print()
			less_logger.Log(msg)

		return False

	def Validate(self, d, f, e):
		for rule in self.__m_rules:
			if rule.Validate(d, f, e) == False:
				filename = os.path.join(d, f)
				if len(e) > 0:
					filename += "." + e
				les_logger.Error("Validation Failed")
				les_logger.Error("File:'%s'", filename)
				les_logger.Error("Rule '%s'", rule.ToString())
				return False
		return True

def GetFileList(root):
	filenames = []
	for root, dirs, files in os.walk(root):
		for name in files:
			filename = os.path.join(root, name)
			if filename.find("./") == 0:
				filename = filename[2:]
	 		filenames.append(filename)

	for root, dirs, files in os.walk(root):
		for name in dirs:
 			dirname = os.path.join(root, name)
			filenames.append(GetFileList(dirname))

	return filenames

def Init():
	les_logger.Init("log.txt")
	verbose = True
	les_logger.SetConsoleOutput(les_logger.CHANNEL_LOG, verbose)
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_WARNING, "warning.txt")
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_ERROR, "error.txt")
	les_logger.SetChannelOutputFileName(les_logger.CHANNEL_LOG, "log.txt")

def LoadRules():
	ruleSets = []
	rules = Rules("data/ce_base.txt")
	ruleSets.append(rules)
	return ruleSets

def GetFiles():
	fileList = GetFileList(".")
	if 0:
		for f in fileList:
			les_logger.Log(f)
	
	files = []
	for f in fileList:
		(dirname, file_ext_name) = os.path.split(f)
		extIndex = file_ext_name.rfind(".")
		if extIndex == 0:
			filename = ""
			extension = file_ext_name[1:]
		elif extIndex > 0:
			filename = file_ext_name[0:extIndex]
			extension = file_ext_name[extIndex+1:]
		else:
			filename = file_ext_name
			extension = ""

		fileEntry = (dirname, filename, extension)
		files.append(fileEntry)

	return files

def Validate(files, ruleSets):
	for (d, f, e) in files:
		for ruleSet in ruleSets:
			if ruleSet.Validate(d, f, e) == False:
				les_logger.Error("Validation Failed: RuleSet: '%s'", ruleSet.GetName())
				return False
	return true

def runMain():
	Init()
	rules = LoadRules()
	files = GetFiles()

	if 0:
		for (d, f, e) in files:
			les_logger.Log("d:'%s' f:'%s' e:'%s'", d, f, e)

	if Validate(files, rules) == False:
		return False

	return True

if __name__ == '__main__':
	if runMain() == False:
		exit(-1)
	exit(0)
