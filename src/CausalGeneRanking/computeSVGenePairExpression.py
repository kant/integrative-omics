
from __future__ import absolute_import
from __future__ import print_function
import sys
import numpy as np
import re
from scipy import stats
from os import listdir
from os.path import isfile, join
from six.moves import range

# Get the expression z-scores for every SV. 

nonCodingPairs = np.loadtxt(sys.argv[1], dtype="object")
codingPairs = np.loadtxt(sys.argv[2], dtype="object")

print(codingPairs)

#Get the SNV data for these patients, make sure to map to the same identifiers
snvDir = sys.argv[3]
allFiles = [f for f in listdir(snvDir) if isfile(join(snvDir, f))]

mutations = []
for currentFile in allFiles:
	
	if currentFile == "MANIFEST.txt":
		continue
	splitFileName = currentFile.split(".")
	patientID = splitFileName[0]

	
	#Load the contents of the file
	with open(snvDir + "/" + currentFile, 'r') as inF:
		lineCount = 0
		for line in inF:
			line = line.strip() #remove newlines
			if lineCount < 1: #only read the line if it is not a header line
				lineCount += 1
				continue

			splitLine = line.split("\t")
			geneName = splitLine[0]
			shortPatientID = 'brca' + patientID.split("-")[2]
			mutations.append([geneName, shortPatientID])
		
			

mutations = np.array(mutations, dtype="object")

expressionFile = sys.argv[4]

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

#Get the z-scores for every pair

#For every gene, get a list of all samples in which this gene is affected to exclude these and make a null distribution
geneSampleRef = dict()
for pair in nonCodingPairs[:,0]:
	splitPair = pair.split("_")
	gene = splitPair[0]
	sample = splitPair[7]
	
	if gene not in geneSampleRef:
		geneSampleRef[gene] = []
	geneSampleRef[gene].append(sample)

for pair in codingPairs:
	splitPair = pair.split("_")
	gene = splitPair[0]
	sample = splitPair[7]

	if gene not in geneSampleRef:
		geneSampleRef[gene] = []
	geneSampleRef[gene].append(sample)

for pair in mutations:

	if pair[0] not in geneSampleRef:
		geneSampleRef[pair[0]] = []
	geneSampleRef[pair[0]].append(pair[1])

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



#Also set the negative set for every gene consisting of the expression of all samples wthout any SV
negativeExpr = dict()
for gene in geneSampleExpr:
	matchedFullSampleNames = list(geneSampleExpr[gene].keys())
	
	#Get all the samples without an SV for this gene
	unmatchedSamples = np.setdiff1d(samples[1:len(samples)-1], matchedFullSampleNames) #exclude hybrid ref
	negativeSamples = []
	for sample in unmatchedSamples: #sample tumor samples, exclude normals
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

def getDEPairs(pairs, geneSampleRef, epressionData, perPairDifferentialExpression, geneSampleExpr, negativeExpr):
									
	for pair in pairs:
		splitPair = pair.split("_")
		gene = splitPair[0]
		pairSample = splitPair[7]
		shortPairSampleName = pairSample.split("brca")[1]
		sv = "_".join(splitPair[1:])
		if gene not in expressionData[:,0]:
			continue
		
		if pairSample not in geneSampleExpr[gene]:
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

def getDEPairsSNVs(pairs, geneSampleRef, epressionData, perPairDifferentialExpression, geneSampleExpr, negativeExpr):
									
	for pair in pairs:
		
		gene = pair[0]
		pairSample = pair[1]
		
		if gene not in expressionData[:,0]:
			continue
		
		if pairSample not in geneSampleExpr[gene]: #sometimes there is no expr data for that sample
			continue 
		
		sampleExpressionValue = geneSampleExpr[gene][pairSample] #expression values of this gene in all samples
		matchedFullSampleNames = list(geneSampleExpr[gene].keys())
					
		negativeSampleExpressionValues = negativeExpr[gene]
		
		#Get the expression z-score for this pair
		if np.std(negativeSampleExpressionValues) == 0:
			continue
	
		z = (sampleExpressionValue - np.mean(negativeSampleExpressionValues)) / float(np.std(negativeSampleExpressionValues))
		pValue = stats.norm.sf(abs(z))*2
	
		perPairDifferentialExpression[pair[0] + "_" + pair[1]] = pValue
		
	return perPairDifferentialExpression

#Get the p-value for each pair in coding & non-coding
# perPairDifferentialExpression = getDEPairs(nonCodingPairs[:,0], geneSampleRef, expressionData, dict(), geneSampleExpr, negativeExpr)
# print("done")
# perPairDifferentialExpression = getDEPairs(codingPairs, geneSampleRef, expressionData, perPairDifferentialExpression, geneSampleExpr, negativeExpr)
# print("coding done")
# #Do multiple testing correction
# #print perPairDifferentialExpression
# 
# perPairDifferentialExpressionArray = np.empty([len(perPairDifferentialExpression), 2], dtype="object")
# perPairDifferentialExpressionArray[:,0] = list(perPairDifferentialExpression.keys())
# perPairDifferentialExpressionArray[:,1] = list(perPairDifferentialExpression.values())
# 
# 
# from statsmodels.sandbox.stats.multicomp import multipletests
# reject, pAdjusted, _, _ = multipletests(perPairDifferentialExpressionArray[:,1], method='bonferroni')
# 
# perPairDifferentialExpressionArrayFiltered = perPairDifferentialExpressionArray[reject]
# 
# #np.save('codingNonCodingPairDEGs.npy', perPairDifferentialExpressionArrayFiltered)
# 
# #instead of writing the whole array to a file, write per SV which DEGs these are linked to
# svsAndDegsNonCoding = dict()
# svsAndDegsCoding = dict()
# for pair in perPairDifferentialExpressionArrayFiltered[:,0]:
# 	splitPair = pair.split("_")
# 	svEntries = splitPair[1:]
# 	sv = "_".join(svEntries)
# 	
# 	if sv not in svsAndDegsNonCoding:
# 		svsAndDegsNonCoding[sv] = 0
# 	if sv not in svsAndDegsCoding:
# 		svsAndDegsCoding[sv] = 0
# 		
# 	if pair in nonCodingPairs[:,0]:
# 		svsAndDegsNonCoding[sv] += 1
# 	if pair in codingPairs:
# 		svsAndDegsCoding[sv] += 1
# 
# pairs = np.empty([len(svsAndDegsNonCoding), 2], dtype="object")	
# for svInd in range(0, len(svsAndDegsNonCoding)):
# 	pairs[svInd, 0] = list(svsAndDegsNonCoding.keys())[svInd]
# 	pairs[svInd,1] = svsAndDegsNonCoding[list(svsAndDegsNonCoding.keys())[svInd]]
# 
# np.savetxt(sys.argv[1] + "_degPairsNonCoding.txt", pairs, delimiter="\t", fmt="%s")
# 
# #repeat for coding
# pairs = np.empty([len(svsAndDegsCoding), 2], dtype="object")	
# for svInd in range(0, len(svsAndDegsCoding)):
# 	pairs[svInd, 0] = list(svsAndDegsCoding.keys())[svInd]
# 	pairs[svInd,1] = svsAndDegsCoding[list(svsAndDegsCoding.keys())[svInd]]
# 
# np.savetxt(sys.argv[1] + "_degPairsCoding.txt", pairs, delimiter="\t", fmt="%s")

# Output DEG pairs for non-coding only
from statsmodels.sandbox.stats.multicomp import multipletests
perPairDifferentialExpression = getDEPairs(nonCodingPairs[:,0], geneSampleRef, expressionData, dict(), geneSampleExpr, negativeExpr)
print("done")

perPairDifferentialExpressionArray = np.empty([len(perPairDifferentialExpression), 2], dtype="object")
perPairDifferentialExpressionArray[:,0] = list(perPairDifferentialExpression.keys())
perPairDifferentialExpressionArray[:,1] = list(perPairDifferentialExpression.values())

from statsmodels.sandbox.stats.multicomp import multipletests
reject, pAdjusted, _, _ = multipletests(perPairDifferentialExpressionArray[:,1], method='bonferroni')

perPairDifferentialExpressionArrayFiltered = perPairDifferentialExpressionArray[reject]

np.save(sys.argv[1] + '_nonCodingPairDEGs.npy', perPairDifferentialExpressionArrayFiltered)

perPairDifferentialExpression = getDEPairs(codingPairs, geneSampleRef, expressionData, dict(), geneSampleExpr, negativeExpr)
print("done")

perPairDifferentialExpressionArray = np.empty([len(perPairDifferentialExpression), 2], dtype="object")
perPairDifferentialExpressionArray[:,0] = list(perPairDifferentialExpression.keys())
perPairDifferentialExpressionArray[:,1] = list(perPairDifferentialExpression.values())

from statsmodels.sandbox.stats.multicomp import multipletests
reject, pAdjusted, _, _ = multipletests(perPairDifferentialExpressionArray[:,1], method='bonferroni')

perPairDifferentialExpressionArrayFiltered = perPairDifferentialExpressionArray[reject]

np.save(sys.argv[1] + '_codingPairDEGs.npy', perPairDifferentialExpressionArrayFiltered)

#finally repeat for SNVs as well

perPairDifferentialExpression = getDEPairsSNVs(mutations, geneSampleRef, expressionData, dict(), geneSampleExpr, negativeExpr)
print("done")

perPairDifferentialExpressionArray = np.empty([len(perPairDifferentialExpression), 2], dtype="object")
perPairDifferentialExpressionArray[:,0] = list(perPairDifferentialExpression.keys())
perPairDifferentialExpressionArray[:,1] = list(perPairDifferentialExpression.values())

from statsmodels.sandbox.stats.multicomp import multipletests
reject, pAdjusted, _, _ = multipletests(perPairDifferentialExpressionArray[:,1], method='bonferroni')

perPairDifferentialExpressionArrayFiltered = perPairDifferentialExpressionArray[reject]

np.save(sys.argv[1] + '_codingSNVDEGs.npy', perPairDifferentialExpressionArrayFiltered)
