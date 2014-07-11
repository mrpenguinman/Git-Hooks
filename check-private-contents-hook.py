#!/usr/bin/env python

#Author: Chris Wallis
#Date: 7-10-2014
#Reads in the PRIVATE_DEFINITIONS_FILE and checks to make sure that any defined variable (that is a string) in that file is only set to the allows phrases. If it finds a variable is improperly set, it will cancel the commit. The comparisons of the variable names are case sensitive and the comparisons of the variables values are not case sensitive.
import sys
import re
import os
import subprocess

#An example file is in the directory.
PRIVATE_DEFINITIONS_FILE = "definitions_file"
REGEX_BASE = "({})\s*=\s*\"(.+)\"" 
tempRegex = re.compile("((?:USERNAME)|(?:PASSWORD))\s*=\s*\"(.*)\"")
tempRegexString = "((?:USERNAME)|(?:PASSWORD))\s*=\s*\"(.+)\""
GIT_STATUS_REGEX = re.compile("^[AM]+\s+(.+)$", re.MULTILINE)

class Definition():
	def __init__(self, varName, allowedOptions=[]):
		self.varName = varName
		self.allowedOptions = allowedOptions
		self.regex = re.compile(REGEX_BASE.format(self.varName))

#A list of all of the defined definitions, each stored as an instance of the Definition class
definitions = {}

def sysCall(args):
    call = subprocess.Popen(args, stdout = subprocess.PIPE)
    details = call.stdout.read()
    details = details.strip()
    return details

def readInPreferences(filePath):
	#TODO: check if file exists
	defFile = open(filePath, 'r')

	#loop over all of the lines in the file
	for line in defFile:
		if not line or line[0] == '#' or line.isspace():
			continue
		parts = line.split("=")
		if len(parts) != 2:
			print "There is a line in the definition file that is improperly formatted:\n\t" +  line + "\nExiting now."
			sys.exit(1)
		varName = parts[0]
		allowedValuesJoined = parts[1]
		allowedValuesRaw = allowedValuesJoined.split(",")

		if len(allowedValuesRaw) == 0:
			print "There are no allowed options for the variable \"" + varName + "\". Exiting now."
			sys.exit(1)

		#go through the allowed values and strip of quotes
		allowedValues = []
		for value in allowedValuesRaw:
			if value[0] == "\"" and value[-1] == "\"":
				allowedValues.append(value[1:-1])
			else:
				allowedValues.append(value)
		definitions[varName] = Definition(varName, allowedValues)
	defFile.close()

def combineDefinitionsIntoRegex():
	combinedDef = ""
	for key, definition in definitions.iteritems():
		combinedDef = combinedDef + "(?:" + definition.varName + ")|"
	combinedDef = combinedDef[0:-1] #strip off the last \
	regexString = REGEX_BASE.format(combinedDef)
	return re.compile(regexString)	

#Expects a file opened in read mode
def checkFileForDefinitions(theFile, regex):
	for line in theFile:
		matches = re.finditer(regex, line)
		for match in matches:
			if not match.group(0):
				continue
			varName = match.group(1)
			value = match.group(2)
			
			if varName in definitions:
				found = False
				for option in definitions[varName].allowedOptions:
					if option.lower() == value.lower():
						found = True
						break
				if not found:
					#This is not an allowed value, throw an error
					print "The only allowed values for " + varName + " are : \n" + ", ".join(definitions[varName].allowedOptions) + "\nBut it was set to the value: \"" + value + "\""
					sys.exit(1)

def main():
	#Set everything up
	readInPreferences(PRIVATE_DEFINITIONS_FILE)
	regex = combineDefinitionsIntoRegex()

	#check all of the files to make sure they are okay.
	status = sysCall(['git','status','--porcelain'])
	fileNames = re.finditer(GIT_STATUS_REGEX, status)
	for fileNameGroup in fileNames:
		name = fileNameGroup.group(1)
		theFile = open(name, 'r')
		checkFileForDefinitions(theFile, regex)

	#If we got to this point, everything is fine and dandy
	return 0

if __name__ == '__main__':
	main()