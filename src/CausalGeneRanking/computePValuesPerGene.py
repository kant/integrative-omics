"""
	Script to run after all permutations to compare the scores of the genes with real SVs to the genes with shuffled SVs. The p-values will be computed per layer. The genes with the lowest p-values across all layers will be reported as
	the most intersting genes. 

	Step 1: read all the permutation scores for the genes and for the original round, store the scores per gene.
	Step 2: compute the p-values
	
	This script now runs for each data folder/cancer type individually. 

"""

from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from os import listdir

from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as plt
from six.moves import range

#1. For each folder in the gene ranking related to this particular run (provide uuid), read the files for the real case and the permutations

dataFolder = sys.argv[1] #provide the folder which contains the output of all permutation runs. 
noOfPermutations = int(sys.argv[2]) #provide how many permutations we expected. I can probably get that from the data folder as well, but that is more risky. 

#first read the non-permuted scores

nonPermutedScoresFile = dataFolder + "/realSVs_geneScores_chr.txt"
nonPermutedScores = np.loadtxt(nonPermutedScoresFile, dtype="object")

noOfCausalGenes = len(nonPermutedScores[:,0])	

perGeneScores = dict()
perGeneScores["totalScore"] = np.zeros([noOfCausalGenes, noOfPermutations+1])


#Make an index for the positions of the genes in the final scoring matrix
geneIndex = 0
geneIndexDict = dict()
for row in range(0, nonPermutedScores.shape[0]):
	
	gene = nonPermutedScores[row][0]
	geneIndexDict[gene] = geneIndex
	geneIndex += 1
	


#list all files in this data folder

np.set_printoptions(threshold=np.nan)

geneScoreFiles = [f for f in listdir(dataFolder) if isfile(join(dataFolder, f))]

for geneScoreFile in geneScoreFiles:
	
	#For each of these files, convert the file back to a numpy array
	#Then we make the per gene score arrays, keep the score separate per permutation round
	
	#separate the permutation round number from the file name
	
	if geneScoreFile == "realSVs_geneScores_chr.txt": #skip the non-permutation file
		continue
	
	permutationRound = int(geneScoreFile.split("_")[1])
	
	geneScores = np.loadtxt(dataFolder + "/" + geneScoreFile, dtype="object")
	
	for row in range(0, geneScores.shape[0]):
	
		#get the right index of the gene
		currentGeneIndex = geneIndexDict[geneScores[row,0]]
		
		
		
		perGeneScores["totalScore"][currentGeneIndex, permutationRound] = geneScores[row][30]
		


# geneInd = geneIndexDict['ZFP57']
# print perGeneScores["interactionScore"][geneInd, :]

#Extra step:

#Show the distribution of the permutation scores for each gene

#Normalize this, use a pdf for plotting


#3. Compute the p-value for each gene

#Check how many of the permutation scores for this gene are larger than the observed gene score for this gene.
#We can compute this separately per layer, and then rank them based on having the highest score in most columns. 
print("Computing p-values and ranking genes: ") 	


cancerTypePValues = np.empty(nonPermutedScores.shape, dtype="object") #for all genes, store the gene identifier, and 3 columns for the layers.  

#For each cancer type keep an array with the scores in the columns. Then do a sorting where the scores are the highest across all rows for that gene. 

for row in range(0, nonPermutedScores.shape[0]):
	#Get the distribution of scores for the permutation for this gene
	geneName = nonPermutedScores[row][0]
	
	total = float(nonPermutedScores[row,30])
	
	geneIndex = geneIndexDict[geneName]
	
	permutedTotalScores = np.array(perGeneScores["totalScore"][geneIndex])

	#First compute the p-value for the gene score layer
	proportion = (np.sum((permutedTotalScores >= total).astype(int)) + 1) / float(len(permutedTotalScores) + 1) #I think we need equals, when the sum is the same, the value should be TRUE and receive a lower p-value. 
	
	cancerTypePValues[row][0] = geneName
	#cancerTypePValues[row][1] = gene.chromosome
	#cancerTypePValues[row][2] = gene.start
	cancerTypePValues[row][1] = proportion
	#cancerTypePValues[row][2] = proportion

	#Compute a total score to sort by. 
	#totalScore = proportion + eQTLProportion + tadProportion
	#cancerTypePValues[row][6] = totalScore
	
	cutoff = 0.05
	totalCutoffMatches = 0
	
	# if proportion < cutoff:
	# 	totalCutoffMatches += 1
	if proportion < cutoff: #I want to rank only by eQTL scores
		totalCutoffMatches += 1	
	# if tadProportion < cutoff:
	# 	totalCutoffMatches += 1

		
	#cancerTypePValues[row][3] = totalCutoffMatches	

#Rank by the total score and report the genes.
np.set_printoptions(threshold=np.nan)
sortedPValues = cancerTypePValues[cancerTypePValues[:,1].argsort()] #[::-1]

outFile = "rankedGenes_test.txt"

with open(outFile, 'w') as out:
	
	for gene in sortedPValues:
		
		#0 is the gene name, 3 is the gene score, 4 is the eqtl score, 5 is the tad score, 7 the total.
		newLine = gene[0] + "\t" + str(gene[1]) + "\n"
		out.write(newLine)
	


