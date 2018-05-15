"""
	Script to run after all permutations to compare the scores of the genes with real SVs to the genes with shuffled SVs. The p-values will be computed per layer. The genes with the lowest p-values across all layers will be reported as
	the most intersting genes. 


"""

from os import listdir
from os.path import isfile, join

#1. For each folder in the gene ranking related to this particular run (provide uuid), read the files for the real case and the permutations

dataFolder = sys.argv[1]

#list all files in this data folder

geneScoreFiles = [f for f in listdir(dataFolder) if isfile(join(dataFolder, f))]

print geneScoreFiles

exit()




#2.Prepare a placeholder where all the scores will be stored in one array


#Prepare placeholder for scores
perGeneScores = dict()
for cancerType in uniqueCancerTypes:
	perGeneScores[cancerType] = dict()
	perGeneScores[cancerType]["geneScore"] = np.zeros([len(causalGenes), noOfPermutations])
	perGeneScores[cancerType]["eQTLScore"] = np.zeros([len(causalGenes), noOfPermutations])
	perGeneScores[cancerType]["tadScore"] = np.zeros([len(causalGenes), noOfPermutations])

#Also prepare the order of the genes in the scoring matrix
geneIndices = dict()
geneIndex = 0
for gene in causalGenes[:,3]:
	
	geneName = gene.name
	geneIndices[geneName] = geneIndex
	geneIndex += 1



for permutationRound in range(0, noOfPermutations):

	scores = geneRanking.scores ###Here the right scores need to be read from the pickle
	
	permutationInd = permutationRound
	for cancerType in scores:
		
		cancerTypeScores = scores[cancerType]
		
		
		for row in range(0, cancerTypeScores.shape[0]):
			gene = cancerTypeScores[row][0]
			geneName = gene.name
			
			#make a matrix of genes by permutations
			
			
			
			#Get the right index for this gene
			geneIndex = geneIndices[geneName]
			
	
			perGeneScores[cancerType]["geneScore"][geneIndex, permutationInd] = cancerTypeScores[row, 1]
			perGeneScores[cancerType]["eQTLScore"][geneIndex, permutationInd] = cancerTypeScores[row, 2]
			perGeneScores[cancerType]["tadScore"][geneIndex, permutationInd] = cancerTypeScores[row, 3]
		
		
		print perGeneScores


#3. Compute the p-value for each gene

#Check how many of the permutation scores for this gene are larger than the observed gene score for this gene.
#We can compute this separately per layer, and then rank them based on having the highest score in most columns. 
print "Computing p-values and ranking genes: " 	
for cancerType in realScores:

	cancerTypeScores = realScores[cancerType]
	cancerTypePValues = np.empty([cancerTypeScores.shape[0], 7], dtype="object") #for all genes, store the gene identifier, and 3 columns for the layers.  
	
	#For each cancer type keep an array with the scores in the columns. Then do a sorting where the scores are the highest across all rows for that gene. 
	
	for row in range(0, cancerTypeScores.shape[0]):
	
		#Get the distribution of scores for the permutation for this gene
		gene = cancerTypeScores[row][0]
		geneName = gene.name
		
		geneScore = cancerTypeScores[row,1]
		eQTLScore = cancerTypeScores[row,2]
		tadScore = cancerTypeScores[row,3]
		
		geneIndex = geneIndices[geneName]
		
		permutedGeneScores = perGeneScores[cancerType]["geneScore"][geneIndex]
		permutedEQTLScores = perGeneScores[cancerType]["eQTLScore"][geneIndex]
		permutedTADScores = perGeneScores[cancerType]["tadScore"][geneIndex]
		
		#First compute the p-value for the gene score layer
		proportion = (np.sum((permutedGeneScores >= geneScore).astype(int)) + 1) / float(len(permutedGeneScores) + 1) #I think we need equals, when the sum is the same, the value should be TRUE and receive a lower p-value. 
		
		if proportion < 1:
		
			print "gene: ", geneName
			print "p-value for the gene layer: ", proportion
		
			
		eQTLProportion = (np.sum((permutedEQTLScores >= eQTLScore).astype(int)) + 1) / float(len(permutedEQTLScores) + 1) 
		
		if eQTLProportion < 1:
		
			print "p-value for the eQTL layer: ", eQTLProportion
		
		
		tadProportion = (np.sum((permutedTADScores >= tadScore).astype(int)) + 1) / float(len(permutedTADScores) + 1) 
		
		if tadProportion < 1:
		
			print "p-value for the TAD layer: ", tadProportion
		
		
		cancerTypePValues[row][0] = gene.name
		cancerTypePValues[row][1] = gene.chromosome
		cancerTypePValues[row][2] = gene.start
		cancerTypePValues[row][3] = proportion
		cancerTypePValues[row][4] = eQTLProportion
		cancerTypePValues[row][5] = tadProportion

		#Compute a total score to sort by. 
		totalScore = proportion + eQTLProportion + tadProportion
		cancerTypePValues[row][6] = totalScore


	#Rank by the total score and report the genes.
	np.set_printoptions(threshold=np.nan)
	sortedPValues = cancerTypePValues[cancerTypePValues[:,6].argsort()]
	
	print sortedPValues