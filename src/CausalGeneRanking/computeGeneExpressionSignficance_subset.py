"""
	Compute the differential expression difference between genes with SVs and genes without SVs. 

"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import numpy as np
import matplotlib.pyplot as plt
import re
from scipy import stats
from six.moves import range

#Plot the number of samples that every gene has in a histogram
geneScoreFile = sys.argv[1]
geneScores = np.loadtxt(geneScoreFile, dtype="object")

#Make the gene subsets given a threshold of number of samples
threshold = 5
filteredGenes = []
for gene in geneScores:
	samples = gene[31].split(",")
	if len(samples) > threshold:
		
		filteredGenes.append(gene)
		
filteredGenes = np.array(filteredGenes, dtype="object")
print(filteredGenes.shape)

#Write to outfile to check cosmic overlap etc
header = "geneName\tgeneScore\teQTLGains\teQTLLosses\tenhancerGains\tenhancerLosses\tpromoterGains\tpromoterLosses\tcpgGains\tcpgLosses\ttfGains\ttfLosses\thicGains\thicLosses\th3k9me3Gains\th3k9me3Losses\th3k4me3Gains\th3k4me3Losses\th3k27acGains\th3k27acLosses\th3k27me3Gains\th3k27me3Losses\th3k4me1Gains\th3k4me1Losses\th3k36me3Gains\th3k36me3Losses\tdnaseIGains\tdnaseILosses\ttotal\tsamples"
				
#Write to numpy output file	
np.savetxt(geneScoreFile + "_filtered.txt", filteredGenes, delimiter='\t', fmt='%s', header=header)

#Get the expression values for the samples in the positive subset
expressionFile = sys.argv[2]

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

pValues = []
excludedSamples = dict()
for gene in filteredGenes:
	if gene[0] not in expressionData[:,0]:
		continue
	geneExpression = expressionData[expressionData[:,0] == gene[0]][0]
	sampleExpressionValues = [] #expression values of this gene in all samples
	
	geneSamples = gene[31].split(",")
	excludedSampleCount = int(round(len(geneSamples) / 2))
	
	matchedFullSampleNames = []
	sampleCount = 0
	for geneSample in geneSamples:
		if sampleCount > excludedSampleCount:
			if gene[0] not in excludedSamples:
				excludedSamples[gene[0]] = []
			excludedSamples[gene[0]].append(geneSample)
			continue

		shortSampleName = geneSample.split("brca")[1]
		
		#match the sample name with the expression sample name
		for sampleInd in range(0, len(samples)):
			sample = samples[sampleInd]
			if re.search(shortSampleName, sample, re.IGNORECASE) is not None:
				matchedFullSampleNames.append(sample) #keep this to check later for the negative set
				#Get the last 2 numbers
				splitSample = sample.split("-")
				code = int(splitSample[len(splitSample)-1])
				
				if code < 10: #above 9 are the normal samples, which we do not want to include here
					sampleInd = samples.index(sample)
					
					sampleExpressionValues.append(float(geneExpression[sampleInd]))
		sampleCount += 1
		
			
				
	#Get 5 random samples that are not affecting this gene
	unmatchedSamples = np.setdiff1d(samples[1:len(samples)-1], matchedFullSampleNames) #exclude hybrid ref
	negativeSamples = []
	for sample in unmatchedSamples: #sample tumor samples, exclude normals
		splitSample = sample.split("-")
		code = int(splitSample[len(splitSample)-1])
		
		if code < 10: 
			negativeSamples.append(sample)
		# if len(negativeSamples) == len(matchedFullSampleNames):
		# 	break
	
	#Get the expression of these samples
	negativeSampleExpressionValues = []
	for sample in negativeSamples:
		sampleInd = samples.index(sample)				
		negativeSampleExpressionValues.append(float(geneExpression[sampleInd]))
	
	
	#Do a t-test and compute the p-value for this gene
	posMean = np.mean(sampleExpressionValues)
	posStd = np.std(sampleExpressionValues)
	negMean = np.mean(negativeSampleExpressionValues)
	negStd = np.std(negativeSampleExpressionValues)
	
	pValue = stats.ttest_ind_from_stats(posMean, posStd, len(sampleExpressionValues), negMean, negStd, len(negativeSampleExpressionValues))[1]
	pValues.append([gene[0], pValue])
	

pValues = np.array(pValues, dtype="object")

pValues = pValues[pValues[:,1].argsort()] 
print(pValues.shape)
signGenes = []
signCount = 0
for pValue in pValues:
	if pValue[1] < 0.05:
		
		gene = filteredGenes[filteredGenes[:,0] == pValue[0]][0]
		signGenes.append(gene)
		
		print(pValue)
		signCount += 1
print("Number of significant genes: ", signCount)

signGenes = np.array(signGenes)
#Write to outfile to check cosmic overlap etc
header = "geneName\tgeneScore\teQTLGains\teQTLLosses\tenhancerGains\tenhancerLosses\tpromoterGains\tpromoterLosses\tcpgGains\tcpgLosses\ttfGains\ttfLosses\thicGains\thicLosses\th3k9me3Gains\th3k9me3Losses\th3k4me3Gains\th3k4me3Losses\th3k27acGains\th3k27acLosses\th3k27me3Gains\th3k27me3Losses\th3k4me1Gains\th3k4me1Losses\th3k36me3Gains\th3k36me3Losses\tdnaseIGains\tdnaseILosses\ttotal\tsamples"
				
#Write to numpy output file	
np.savetxt(geneScoreFile + "_signgt5.txt", signGenes, delimiter='\t', fmt='%s', header=header)

#Make a file with the excluded samples
with open(sys.argv[3], 'w') as outF:
	for gene in excludedSamples:
		outF.write(gene + "\t" + ",".join(excludedSamples[gene]) + "\n")
		


#Get the expression values for the sample sin the negative subset