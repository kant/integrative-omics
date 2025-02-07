"""
	Find out which genes are only found when looking at non-coding effects, which are mixed, and which are coding-only. 
	Later also add coding SNVs. 
"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import numpy as np
from six.moves import range


nonCodingRanks = np.loadtxt(sys.argv[1], dtype="object")
mixedRanks = np.loadtxt(sys.argv[2], dtype="object")
geneExpression = np.loadtxt(sys.argv[3],dtype="object") #Which values to use? 

#Readfor each gene if it is linked to an SV. If yes, include it in the results.
effects = dict() #store for every gene what it is affected by

for rank in nonCodingRanks:
	
	gene = rank[0]
	samples = rank[31]
	if samples != "None": #Only if the gene has been linked to at least 1 SV, we include it in the effects table. 
		if gene not in effects:
			effects[gene] = []
		effects[gene].append("Non-coding")
	
for rank in mixedRanks:
	
	gene = rank[0]
	samples = rank[31]
	if samples != "None": #Only if the gene has been linked to at least 1 SV, we include it in the effects table. 
		if gene not in effects:
			effects[gene] = []
		effects[gene].append("Mixed")

for rank in mixedRanks:
	gene = rank[0]
	samples = rank[31]
	if float(rank[3]) > 0:
		if gene not in effects:
			effects[gene] = []
		effects[gene].append("Coding")
	if samples != "None":
		if gene not in effects:
			effects[gene] = []
		effects[gene].append("Non-coding")


mixedOnly = 0
ncOnly = 0
codingOnly = 0

effectsTable = np.empty([len(effects), 3], dtype="object") #Turn dictionary into readable tsv table
effectsTable[:,0] = list(effects.keys())
for geneInd in range(0, len(effects)):
	gene = list(effects.keys())[geneInd]
	if "Non-coding" in effects[gene]:
		effectsTable[geneInd,1] = 1
	else:
		effectsTable[geneInd,1] = 0
	
	if "Coding" in effects[gene]:
		effectsTable[geneInd,2] = 1
	else:
		effectsTable[geneInd,2] = 0
		
	if effectsTable[geneInd,1] == 1 and effectsTable[geneInd,2] == 0: #in non-coding, but not coding
		ncOnly += 1
		
	if effectsTable[geneInd,1] == 0 and effectsTable[geneInd,2] == 1: #in coding, but not in non-coding
		codingOnly += 1

	if effectsTable[geneInd,1] == 1 and effectsTable[geneInd,2] == 1: #in coding, but not in non-coding
		mixedOnly += 1

print(mixedOnly)
print(ncOnly)
print(codingOnly)

effectsTable = effectsTable[effectsTable[:,1].argsort()][::-1]
		
np.savetxt("Output/effectsTable.txt", effectsTable, fmt="%s", delimiter="\t")

#Search through the ranks, if there is a gene that is affected by non-coding SVs only AND has changed expression, we should include this gene.
#If the gene has changed expression and it also has a coding SV, those patients are likely not the ones with expression changes driven by SVs.
#This must be in the same sample, so we are using the results of the mutually exclusive set here. 

nonCodingDrivers = []
for rank in nonCodingRanks:
	
	gene = rank[0]
	samples = rank[31]
	if samples != "None": 
		splitSamples = samples.split(",")
		for sample in splitSamples:
			pair = gene + "_" + sample
			if pair in geneExpression[:,0]:
				expr = float(geneExpression[geneExpression[:,0] == pair,1][0])
				nonCodingDrivers.append([pair, expr])

nonCodingDrivers = np.array(nonCodingDrivers, dtype="object")

nonCodingDrivers = nonCodingDrivers[np.argsort(nonCodingDrivers[:,1])]

print(nonCodingDrivers)
print(len(nonCodingDrivers))
exit()
genes = []			
for pair in nonCodingDrivers:
	
	splitPair = pair.split("_")
	if splitPair[0] not in genes:
		genes.append(splitPair[0])
		print(splitPair[0])

print(len(genes))
		
		
		
	

