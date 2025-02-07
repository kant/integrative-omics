"""
	Compute which sv-gene pairs are DEG based on 1 set of input SVs and genes, rather than coding & non-coding
"""


from __future__ import absolute_import
from __future__ import print_function
import sys
import numpy as np
import re
from scipy import stats
from six.moves import range

# Get the expression z-scores for every SV. 

nonCodingPairs = np.loadtxt(sys.argv[1], dtype="object")
codingPairs = np.load(sys.argv[2], allow_pickle=True, encoding='latin1') #include the coding pair to make sure that we compute DEGs compared to samples with NO SV at all, also not coding.

expressionFile = sys.argv[3]
shuffle = sys.argv[4] #pass true or false

expressionData = []
samples = []
with open(expressionFile, 'r') as inF:
	lineCount = 0
	for line in inF:
		line = line.strip()
		if lineCount == 0:
			samples = line.split("\t")
			lineCount += 1
			continue
		if lineCount < 2:
			lineCount += 1
			continue
		splitLine = line.split("\t")
		fullGeneName = splitLine[0]
		geneName = fullGeneName.split("|")[0]

		data = splitLine[1:len(splitLine)-1] 
		fixedData = [geneName]
		fixedData += data
		expressionData.append(fixedData)

expressionData = np.array(expressionData, dtype="object")
print(expressionData)

# if shuffle == "True":
# 	#shuffling across columns
# 	#make sure not to inclue the hybrid ref
# 	cols = list(np.random.permutation(range(1, expressionData.shape[1])))
# 	allCols = np.array([0] + cols)
# 	expressionData = expressionData[:, allCols]
#check if this goes well, also check if the hybrid ref is not in there

#Get the z-scores for every pair

#For every gene, get a list of all samples in which this gene is affected to exclude these and make a null distribution
geneSampleRef = dict()
for pair in nonCodingPairs:
	splitPair = pair.split("_")
	gene = splitPair[0]
	sample = splitPair[len(splitPair)-1]
	
	if gene not in geneSampleRef:
		geneSampleRef[gene] = []
	geneSampleRef[gene].append(sample)

codingSampleRef = dict()
for pair in codingPairs[:,0]:
	splitPair = pair.split("_")
	gene = splitPair[0]
	sample = splitPair[len(splitPair)-1]
	
	if gene not in codingSampleRef:
		codingSampleRef[gene] = []
	codingSampleRef[gene].append(sample)

#Set for every gene the expression values in all possible samples for lookup
geneSampleExpr = dict()
for gene in geneSampleRef:
	
	if gene not in expressionData[:,0]:
		continue
	
	geneSamples = geneSampleRef[gene]
	geneSampleExpr[gene] = dict()
	geneExpression = expressionData[expressionData[:,0] == gene][0]
	for geneSample in geneSamples:
		
		shortSampleName = geneSample.split("brca")[1]
		
		#match the sample name with the expression sample name
		for sampleInd in range(0, len(samples)):
			sample = samples[sampleInd]
			if re.search(shortSampleName, sample, re.IGNORECASE) is not None:
				
				splitSampleName = sample.split("-")
				code = int("".join(list(splitSampleName[3])[0:2]))
				
				if code < 10: #above 9 are the normal samples, which we do not want to include here
					sampleInd = samples.index(sample)
					
					geneSampleExpr[gene][geneSample] = float(geneExpression[sampleInd])
print("done getting expr for samples")

#make a histogram of the expression across all genes and samples (see if there is a skew)
geneSampleExprArr = []
for gene in geneSampleExpr:
	for sample in geneSampleExpr[gene]:
		geneSampleExprArr.append(geneSampleExpr[gene][sample])

import matplotlib.pyplot as plt
plt.hist(geneSampleExprArr)
plt.savefig(sys.argv[1] + "_geneSampleExpr.svg")
plt.clf()

#Also set the negative set for every gene consisting of the expression of all samples wthout any SV
negativeExpr = dict()
for gene in geneSampleExpr:
	matchedFullSampleNames = list(geneSampleExpr[gene].keys())
	
	#Get all the samples without an SV for this gene
	unmatchedNonCodingSamples = list(np.setdiff1d(samples[1:len(samples)-1], matchedFullSampleNames)) #exclude hybrid ref
	unmatchedSamples = []
	for sample in unmatchedNonCodingSamples:
		if gene in codingSampleRef:
			if sample not in codingSampleRef[gene]: #only samples that are not in the set with non-coding SVs, and also do not have coding SVs.
				unmatchedSamples.append(sample)
		else: #if the gene does not have coding SV pairs, add it to the negative set.
			unmatchedSamples.append(sample)
	negativeSamples = []
	for sample in unmatchedSamples: 
		splitSampleName = sample.split("-")
		code = int("".join(list(splitSampleName[3])[0:2]))
		
		if code < 10: 
			negativeSamples.append(sample)
		
	#Get the expression of these samples
	negativeSampleExpressionValues = []
	for sample in negativeSamples:
		sampleInd = samples.index(sample)				
		negativeSampleExpressionValues.append(float(geneExpression[sampleInd]))
	
	negativeExpr[gene] = negativeSampleExpressionValues
print("negative expr done")

negativeSampleExprArr = []
for gene in negativeExpr:
	negativeSampleExprArr += negativeExpr[gene]

import matplotlib.pyplot as plt
plt.hist(negativeSampleExprArr)
plt.savefig(sys.argv[1] + "_negativeSampleExpr.svg")
plt.clf()

#alternative shuffling after pre-removing coding samples
#here we go through the positive & negative set and do a random sampling without replacement from either until we have enough values.
import random
if shuffle == "True":
	
	#This is the case where we shuffle differently per gene
	for gene in geneSampleExpr:
		allExpr = negativeExpr[gene]
		for sample in geneSampleExpr[gene]:
			allExpr.append(geneSampleExpr[gene][sample])
		
		#For each positive sample, get a random expression value.
		for sample in geneSampleExpr[gene]:
			randInd = random.randint(0,len(allExpr)-1)
			geneSampleExpr[gene][sample] = allExpr[randInd]
			del allExpr[randInd]
		negativeExpr[gene] = allExpr #remaining will be the negative set. 

	#An alternative case where we shuffle the same across all samples


def getDEPairs(pairs, geneSampleRef, epressionData, perPairDifferentialExpression, geneSampleExpr, negativeExpr):
									
	for pair in pairs:
		splitPair = pair.split("_")
		gene = splitPair[0]
		pairSample = splitPair[len(splitPair)-1]
		shortPairSampleName = pairSample.split("brca")[1]
		sv = "_".join(splitPair[1:])
		if gene not in expressionData[:,0]:
			continue
		
		
		sampleExpressionValue = geneSampleExpr[gene][pairSample] #expression values of this gene in all samples
		matchedFullSampleNames = list(geneSampleExpr[gene].keys())
					
		
		negativeSampleExpressionValues = negativeExpr[gene]
		
		#Get the expression z-score for this pair
		if np.std(negativeSampleExpressionValues) == 0:
			continue
	
		z = (sampleExpressionValue - np.mean(negativeSampleExpressionValues)) / float(np.std(negativeSampleExpressionValues))
		pValue = stats.norm.sf(abs(z))*2
	
		perPairDifferentialExpression[pair] = pValue
		
	return perPairDifferentialExpression

#Get the p-value for each pair in coding & non-coding
perPairDifferentialExpression = getDEPairs(nonCodingPairs, geneSampleRef, expressionData, dict(), geneSampleExpr, negativeExpr)
print("done")

perPairDifferentialExpressionArray = np.empty([len(perPairDifferentialExpression), 2], dtype="object")
perPairDifferentialExpressionArray[:,0] = list(perPairDifferentialExpression.keys())
perPairDifferentialExpressionArray[:,1] = list(perPairDifferentialExpression.values())

from statsmodels.sandbox.stats.multicomp import multipletests
reject, pAdjusted, _, _ = multipletests(perPairDifferentialExpressionArray[:,1], method='bonferroni')

perPairDifferentialExpressionArrayFiltered = perPairDifferentialExpressionArray[reject]

np.save(sys.argv[1] + '_degPairs.npy', perPairDifferentialExpressionArrayFiltered)
