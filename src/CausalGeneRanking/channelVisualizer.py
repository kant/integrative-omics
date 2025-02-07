"""
	The main goal of this class is to take the genes (with neighborhood and dertivative neighborhoods mapped) and visualize the distributions (later to be used as channels) of the regulatory data within
	the nearest TAD boundaries. 

"""
from __future__ import absolute_import
from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np
import math

import settings
from six.moves import range

class ChannelVisualizer:
	
	
	
	def __init__(self, genes, mode, genome):
		
		#Load the list of known cancer genes
		#Then determine if the known cancer genes have losses/gains
		#how do the counts compare to the other random genes?
		#for the genes that have losses/gains in the causal gene set, visualize the channels
		#Does that look different from a random gene?
		
		print("loading genes")
		knownBcGenes = self.loadBCGenes("../../data/Genes/breastCancerCausalGenes.txt")
		causalGenes = self.loadCausalGenes('../../data/Genes/Census_allTue Apr 10 14_56_44 2018.tsv')
		
		#self.reportEQTLChanges(genes, knownBcGenes)
		#self.reportEQTLChanges(genes, causalGenes)
		#self.reportSVOverlap(genes, causalGenes)
		#self.reportSNVOverlap(genes, causalGenes)
		#self.visualizeReference(genes)
		#self.visualizeDerivative(genes)
		
		[channels, labels] = self.makeFeatureMatrix(genes, causalGenes, genome)
		self.clusterGenes(channels, labels)
		
	def loadCausalGenes(self, causalGeneFile):
		
		genes = []
		
		with open(causalGeneFile, 'r') as f:
			lineCount = 0
			for line in f:
				if lineCount < 1:
					lineCount += 1
					continue
				
				line = line.strip()
				splitLine = line.split("\t")
				
				genes.append(splitLine[0])	
		
		return genes
			
	def loadBCGenes(self, causalGeneFile):

		genes = []
		
		with open(causalGeneFile, 'r') as f:
			
			for line in f:
				
				line = line.strip()
				
				genes.append(line)

		return genes
	
	def makeFeatureMatrix(self, genes, causalGenes, genome):
		
		print("defining the feature matrix")
		
		#For the genes, make the channels with gains. But instead, make 200 bins across which the values are distributed.
		#As labels, each gene in the COSMIC dataset is positive. Every sample that has gains from this set is also positive.
		#I think I will limit the negative set to the same size of the positive set. Although that may mean that both sets will be very small and difficult to compare. 
		
		noOfBins = 200
		#noOfBins = 200*2
		windowSize = 40000 #Size of the TADs
		#Make a map with the indices from the start of the TAD to determine which bin the gains should be stored in.
		binRange = windowSize / noOfBins #how many positions of the TAD should be in each bin?
		#binRange = windowSize*2 / noOfBins #how many positions of the TAD should be in each bin?
		
		positionMap = dict()
		currentBin = 0
		for pos in range(1, windowSize+1):
		#for pos in range(0, windowSize*2):	
			
			if pos % binRange == 0:
				currentBin += 1
			
			positionMap[pos] = currentBin
		
		
		
		
		#loss of eQTLs. For each gene, first determine what the nearest TAD from the left is. From there, we count a 40 kb window. We count all TAD losses within this TAD. 
		
		channels = []
		gainChannels = [] #Make sure that these have the same number of genes and bins
		lossChannels = []
		labels = []
		posCount = 0
		negCount = 0
		skippedGenes = 0
		samples = []
		noSamples = 0
		noTad = 0
		noOfSamples = []
		for gene in genes:

			if len(list(gene.lostEQTLs.keys())) < 1 and len(list(gene.gainedEQTLs.keys())) > 0:
				samples = list(gene.gainedEQTLs.keys()) 
			elif len(list(gene.gainedEQTLs.keys())) < 1 and len(list(gene.lostEQTLs.keys())) > 0:
				samples = list(gene.lostEQTLs.keys())
			else: #combine the samples
				samples = list(gene.lostEQTLs.keys()) + list(gene.gainedEQTLs.keys())

			if len(samples) < 1:
				gainChannel = np.zeros(noOfBins+1)
				lossChannel = np.zeros(noOfBins+1)
				lossChannels.append(lossChannel)
				gainChannels.append(gainChannel)
				
				if gene.name in causalGenes:
					noSamples += 1
					posCount += 1
					labels.append(1)	
				elif gene.SNVs is not None and len(gene.SNVs) > 0:
					posCount += 1
					labels.append(1)
				else:
					#negCount += 1
					labels.append(0)	
				
				
				continue


			if gene.leftTAD is None:
				
				
				#In this case, the gene will not have gains and losses, so a feature vector of 0.
				gainChannel = np.zeros(noOfBins+1)
				lossChannel = np.zeros(noOfBins+1)
				lossChannels.append(lossChannel)
				gainChannels.append(gainChannel)
				
				if gene.name in causalGenes:
					noTad += 1
					posCount += 1
					labels.append(1)	
				elif gene.SNVs is not None and len(gene.SNVs) > 0:
					posCount += 1
					labels.append(1)
				else:
					#negCount += 1
					labels.append(0)	
				
				continue
			leftTAD = gene.leftTAD
			
			if leftTAD.end < gene.start:
				tadStart = leftTAD.end
				tadEnd = tadStart + 40000
			else:
				tadStart = leftTAD.start
				tadEnd = leftTAD.end
				
			
			
			
			#Each sample is a separate feature. 
			totalGains = []
			included = False
			gainIncluded = False
			lossIncluded = False
			for sample in samples:
				
				channel = np.zeros(noOfBins+1) #will hold a value of 1 if there is an eQTL in that bin. Gains will be after the losses. 
				gainChannel = np.zeros(noOfBins+1)
				lossChannel = np.zeros(noOfBins+1)
								
				#if sample in gene.gainedEQTLs:
				if sample in gene.lostEQTLs:
					included = True
					lossIncluded = True
					
					losses = gene.lostEQTLs[sample]
					
					for loss in losses:
						
						if loss.start >= tadStart and loss.start <= tadEnd:
							inTadPos = loss.start - tadStart
							
							binPosition = positionMap[inTadPos]
							#channel[binPosition] = 1
							lossChannel[binPosition] = 1
							
				
				if sample in gene.gainedEQTLs:
					
					included = True
					gainIncluded = True
					
					gains = gene.gainedEQTLs[sample] #the actual gained eQTLs are in the first array entry, second is the TAD
					
					#If we use genome, we can get the bin that the gain is from.
					#If this is another TAD, we can use the positions in that TAD.
					#If this is a genomic bin, then we should limit it to the 40kb around the eQTL. But starting from which place?
					
					
					
					#tad = gene.gainedEQTLs[sample] #how to get this info? 
					
					#Represent the gains as bins
					for gain in gains:
						
						#Get the bin in which this
						genomicBin = genome.collectGenomicBin(gain.chromosome, gain.start, gain.end)
						
						if genomicBin == None:
							continue #skip the eQTL if it does not fit in any genomic bin. 
						
						#Check the size of the bin. If it is a TAD, no problem
						
						#####This is a bug, the position is not correct. We need the right TAD pos
						
						if genomicBin[2] - genomicBin[1] == windowSize:
							inTadPos = gain.start - genomicBin[1]
							
						else:
							
							#Divide the bin up in bins of 40 KB.
							boundaries = []
							bins = (genomicBin[2] - genomicBin[1]) / windowSize
							genomicInd = genomicBin[1]
							for binInd in range(0, bins):
								boundaries.append(genomicInd)
								genomicInd += windowSize
							
							closestPos = boundaries[0]
							currentClosest = abs(gain.start - boundaries[0])
							for boundary in boundaries:
								if abs(gain.start - boundary) < currentClosest:
									
									closestPos = boundary
									currentClosest = abs(gain.start - boundary)
							
							if gain.start > closestPos:
								inTadPos = gain.start - closestPos
							else:
								inTadPos = gain.start - (closestPos - windowSize)
							
						#inTadPos = (gain.start - tad.start) + windowSize #this will be in the second TAD
						#inTadPos = gain.start - tad.start
						binPosition = positionMap[inTadPos]
						#channel[binPosition] = 1
						gainChannel[binPosition] = 1
					
				
				lossChannels.append(lossChannel)
				gainChannels.append(gainChannel)
			
				if gene.name in causalGenes:
					noOfSamples.append(len(samples))
					posCount += 1
					labels.append(1)	
				elif gene.SNVs is not None and len(gene.SNVs) > 0:
					posCount += 1
					labels.append(1)
				else:
					negCount += 1
					labels.append(0)	
			
			
				# if included == True:
				# 	
				# 	channels.append(channel)
				# 	
				# 	if gene.name in causalGenes:
				# 		posCount += 1
				# 		labels.append(1)	
				# 	elif gene.SNVs is not None and len(gene.SNVs) > 0:
				# 		posCount += 1
				# 		labels.append(1)
				# 	else:
				# 		#if negCount > 200: #skip all negative genes if we have 500, otherwise there will be too many. 
				# 		#	continue
				# 		negCount += 1
				# 		labels.append(0)
		
		print("no samples: ", noSamples)
		print("no tad: ", noTad)
		print("no of samples: ", noOfSamples)
		print("neg count with gains/losses: ", negCount)
		exit()
		
		print(posCount)
		print(negCount)
		print(len(labels))
		
		lossChannels = np.array(lossChannels)
		gainChannels = np.array(gainChannels)
		
		#Deep learning
		stackedChannels = np.dstack((lossChannels, gainChannels))
		#Simple classifiers
		#stackedChannels = np.concatenate((lossChannels, gainChannels), axis=1)
		
		print(stackedChannels)
		print(labels)
		
		print("data shapes: ")
		print(stackedChannels.shape)
		print(len(labels))
		
				
		# exit()			
		# channels = np.array(channels)
		# print channels.shape
		
		#Combine into a 3D matrix
		
		
		
		# print channels
		# print labels
		# print posCount
		# print negCount
		# exit()
		
		print("Number of positive genes: ", posCount)
		return stackedChannels, labels

	def clusterGenes(self, channels, labelList):
		
		#cluster the channels. 
		
		# from scipy.cluster.hierarchy import dendrogram, linkage  
		# from matplotlib import pyplot as plt
		# 
		# print labelList
		# 
		# 
		# 
		# from sklearn.decomposition import PCA
		# 
		# pca = PCA(n_components=2)
		# 
		# projected = pca.fit_transform(channels)
		# 
		# colorLabels = []
		# for label in labelList:
		# 	if label == 1:
		# 		colorLabels.append('r')
		# 	else:
		# 		colorLabels.append('b')
		# 
		# plt.scatter(projected[:, 0], projected[:, 1], c=colorLabels)
		# plt.show()
		# # 
		# # plt.scatter(projected[:, 0], projected[:, 1], c=colorLabels, edgecolor='none', alpha=1, cmap=plt.cm.get_cmap('jet', 2))
		# # plt.xlabel('component 1')
		# # plt.ylabel('component 2')
		# # plt.colorbar()
		# # plt.show()
		# 
		# # 
		# from tsne import bh_sne
		# 
		# vis_data = bh_sne(channels)
		# # plot the result
		# vis_x = vis_data[:, 0]
		# vis_y = vis_data[:, 1]
		# plt.scatter(vis_x, vis_y, c=colorLabels)
		# plt.show()
		# exit()
		
		# print labelList
		# exit()
		# 
		# plt.scatter(vis_x, vis_y, c=labelList, edgecolor = 'none', alpha = 0.5, cmap=plt.cm.get_cmap("jet", 2))
		# plt.colorbar()
		# plt.show()
		# 
		# exit()
		# 
		
		# Try some simple classifiers, is there any that can obtain reasonable performance with the current features?
		
		from sklearn.model_selection import train_test_split
		# from sklearn.preprocessing import StandardScaler
		# from sklearn.datasets import make_moons, make_circles, make_classification
		# from sklearn.neural_network import MLPClassifier
		# from sklearn.neighbors import KNeighborsClassifier
		# from sklearn.svm import SVC
		# from sklearn.gaussian_process import GaussianProcessClassifier
		# from sklearn.gaussian_process.kernels import RBF
		# from sklearn.tree import DecisionTreeClassifier
		# from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
		# from sklearn.naive_bayes import GaussianNB
		# from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
		# from sklearn.model_selection import cross_val_score
		# 
		# 
		# names = ["Nearest Neighbors", "Linear SVM", "RBF SVM", "Gaussian Process",
		# 		 "Decision Tree", "Random Forest", "Neural Net", "AdaBoost",
		# 		 "Naive Bayes", "QDA"]
		# 
		# classifiers = [
		# 	KNeighborsClassifier(3),
		# 	SVC(kernel="linear", C=0.025),
		# 	SVC(gamma=2, C=1),
		# 	#GaussianProcessClassifier(1.0 * RBF(1.0)),
		# 	DecisionTreeClassifier(max_depth=5),
		# 	RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
		# 	MLPClassifier(alpha=1),
		# 	AdaBoostClassifier(),
		# 	GaussianNB(),
		# 	QuadraticDiscriminantAnalysis()]
		# 
		# 	
		# X_train, X_test, y_train, y_test = train_test_split(channels, labelList, test_size=.4, random_state=42)
		# 
		# #Combine this with cross validation!
		# 
		# # iterate over classifiers
		# for name, clf in zip(names, classifiers):
		# 	
		# 	scores = cross_val_score(clf, channels, labelList, cv=10)
		# 	#clf.fit(X_train, y_train)
		# 	#score = clf.score(X_test, y_test)
		# 	
		# 	print "classifier ", name, ": ", scores.mean()
		# 
		# exit()
	
		#Try a CNN
		from mcfly import modelgen, find_architecture, storage
		from keras.models import load_model
		import os
		
		#use just 1 channel for now, later split into 2 and see if it makes a difference
		X_train, X_test, y_train_list, y_test_list = train_test_split(channels, labelList, test_size=.4, random_state=42)
		
		#the training labels need to be a vector as well. For each gene we have a 1 or 0 for each class. We have 2 classes, so this will be genes * 2
		
		y_train = np.zeros([len(y_train_list), 2])
		for labelInd in range(0, len(y_train_list)):
			
			label = y_train_list[labelInd]
			
			if label == 1:
				y_train[labelInd, 0] = 0
				y_train[labelInd, 1] = 1
			if label == 0:
				y_train[labelInd, 0] = 1
				y_train[labelInd, 1] = 0
		
		y_test = np.zeros([len(y_test_list), 2])
		for labelInd in range(0, len(y_test_list)):
			
			label = y_test_list[labelInd]
			
			if label == 1:
				y_test[labelInd, 0] = 0
				y_test[labelInd, 1] = 1
			if label == 0:
				y_test[labelInd, 0] = 1
				y_test[labelInd, 1] = 0
			
		
		
		num_classes = y_train.shape[1]
		X_train = np.array(X_train)
		
		X_test = np.array(X_test)
		
		
		models = modelgen.generate_models(X_train.shape,
										  number_of_classes=num_classes,
										  number_of_models = 2)
		

		models_to_print = list(range(len(models)))
		for i, item in enumerate(models):
			if i in models_to_print:
				model, params, model_types = item
				print("-------------------------------------------------------------------------------------------------------")
				print(("Model " + str(i)))
				print(" ")
				print("Hyperparameters:")
				print(params)
				print(" ")
				print("Model description:")
				model.summary()
				print(" ")
				print("Model type:")
				print(model_types)
				print(" ")

		# Define directory where the results, e.g. json file, will be stored
		resultpath = os.path.join('.', 'models')
		if not os.path.exists(resultpath):
				os.makedirs(resultpath)
				
		outputfile = os.path.join(resultpath, 'modelcomparison.json')
		histories, val_accuracies, val_losses = find_architecture.train_models_on_samples(X_train, y_train,
																				   X_test, y_test,
																				   models,nr_epochs=5,
																				   subset_size=300,
																				   verbose=True,
																				   outputfile=outputfile)
		print(('Details of the training process were stored in ',outputfile))

		
		
		
		return 0

	def reportSVOverlap(self, genes, knownBcGenes):
		
		bcGenesWithOverlap = 0
		otherGenesWithOverlap = 0
		bcGenesWithSNVSVOverlap = 0
		otherGenesWithSNVSVOverlap = 0
		for gene in genes:
			
			if gene.SVs is not None:
				if len(gene.SVs) > 0:	
					if gene.name in knownBcGenes:
						
						bcGenesWithOverlap += 1
					else:
						otherGenesWithOverlap += 1	
			
			if (gene.SVs is not None and len(gene.SVs) > 0) or (gene.SNVs is not None and len(gene.SNVs) > 0): 
					if gene.name in knownBcGenes:
						bcGenesWithSNVSVOverlap += 1
					else:
						otherGenesWithSNVSVOverlap += 1
			
		print(bcGenesWithOverlap)
		print(otherGenesWithOverlap)
		
		print("bc with both overlap: ", bcGenesWithSNVSVOverlap)
		print("other with both overlap: ", otherGenesWithSNVSVOverlap)
				
		
		return

	def reportSNVOverlap(self, genes, knownBcGenes):
		
		bcGenesWithOverlap = 0
		otherGenesWithOverlap = 0
		for gene in genes:
			
			if gene.SNVs is not None:
				if len(gene.SNVs) > 0:	
					if gene.name in knownBcGenes:
						
						bcGenesWithOverlap += 1
					else:
						otherGenesWithOverlap += 1	
			
		print(bcGenesWithOverlap)
		print(otherGenesWithOverlap)
				
		exit()
		return

	
	
	def reportEQTLChanges(self, genes, knownBcGenes):
		
		#1. Determine the number of lost and gained eQTLs for the known BC genes compared to all other genes
		
		bcLossCount = 0
		bcGainCount = 0
		otherLossCount = 0
		otherGainCount = 0
		for gene in genes:
			# 
			# if gene.name == "APOBEC3B":
			# 	print gene.lostEQTLs
			# 	print gene.gainedEQTLs
			# 	exit()
			
			#The losses and gains are per sample. Do we average across the samples?
			if len(list(gene.lostEQTLs.keys())) < 1 and len(list(gene.gainedEQTLs.keys())) > 0:
				samples = list(gene.gainedEQTLs.keys()) 
			elif len(list(gene.gainedEQTLs.keys())) < 1 and len(list(gene.lostEQTLs.keys())) > 0:
				samples = list(gene.lostEQTLs.keys())
			else: #combine the samples
				samples = list(gene.lostEQTLs.keys()) + list(gene.gainedEQTLs.keys())
			
			#First aggregate across the samples? Count how often we see a gain or loss in total across all samples.
			
			totalLosses = []
			totalGains = []
			for sample in samples:
				
				if sample in gene.lostEQTLs:
					losses = len(gene.lostEQTLs[sample])
					totalLosses.append(losses)
				
				if sample in gene.gainedEQTLs:
					gains = len(gene.gainedEQTLs[sample])
					totalGains.append(gains)
			
			if len(totalLosses) > 0:
				if gene.name in knownBcGenes:
					print("gene ", gene.name, " loses eQTLs")
					bcLossCount += 1 
				else:
					otherLossCount += 1
				
			if len(totalGains) > 0:
				if gene.name in knownBcGenes:
					print("gene ", gene.name, " gains eQTLs")
					bcGainCount += 1
				else:
					otherGainCount += 1
				
		
		#Show the distribution
		
		print("bc loss: ", bcLossCount)
		print("bc gain: ", bcGainCount)
		print("other loss: ", otherLossCount)
		print("other gain: ", otherGainCount)
		
		
		print(len(genes))
		print(len(knownBcGenes))
		
		# 
		
		return
		
		
		
	def visualizeReference(self, genes):
		"""
			For every gene, if there are lost or gained eQTLs for the derivative, show where all the eQTLs normally are within the nearest TAD boundaries
		"""
		distances = []
		for gene in genes:
			
			if len(gene.gainedEQTLs) < 1 and len(gene.lostEQTLs) < 1:
				
				continue
			
			#Check if the total distance is something that we can easily plot or if we need to make bins
			
			if gene.leftTAD == None or gene.rightTAD == None: #Also skip if there is no TAD on the left/right for now
				continue
			
			distance = abs(gene.leftTAD.end - gene.rightTAD.start) #left comes before right
			#at each eQTL position, add a +1.
			tadRange = list(range(gene.leftTAD.end, gene.rightTAD.start))
			plotRange = list(range(0, distance))
			
			eQTLPositions = np.zeros([distance,1])
			for eQTL in gene.eQTLs:
				eQTLPos = eQTL.start
				if eQTLPos < gene.leftTAD.end or eQTLPos > gene.rightTAD.start: #skip the eQTL if it is outside of the TAD boundary
					continue
				
				#The position in the array depends on the positions within the actual tad
				tadInd = tadRange.index(eQTLPos)	
				eQTLPositions[tadInd] = 1
			
			plt.plot(plotRange, eQTLPositions)
			plt.ylim(-1,2)
			plt.show()
				
			return	
			
			#distances.append(distance)
		
		#plt.boxplot(distances)
		#plt.show()
	
		
		
		1+1
		
	def visualizeDerivative(self, genes):
		"""
			For each of the genes, determine if there are lost or gained eQTLs (these should already have been limited to within the nearest TAD boundaries)
		"""
		distances = []
		gainedEQTLs = []
		lostEQTLs = []
		for gene in genes:
			#print gene.name
			if gene.name != "CNTRL":
				continue
			else:
				print(gene.name)
			
			print(gene.gainedEQTLs)
			print(gene.lostEQTLs)
			
			if len(gene.gainedEQTLs) < 1 and len(gene.lostEQTLs) < 1:
				
				continue
			
			# if len(gene.lostEQTLs) > 0:
			# 	print gene.name
			# 	continue

			#Check if the total distance is something that we can easily plot or if we need to make bins
			
			if gene.leftTAD == None or gene.rightTAD == None: #Also skip if there is no TAD on the left/right for now
				continue
			
			#If the gene is within a TAD, the lost eQTLs are between the left tad end, and right tad end.
			#If the gene is not within TADs, the lost eQTLs are between the end of the left tad, and start of the right tad. 
			
			distance = abs(gene.leftTAD.end - gene.rightTAD.start) #left comes before right
			#at each eQTL position, add a +1.
			
			if gene.rightTAD.end != gene.leftTAD.end:
				tadRange = list(range(gene.leftTAD.end, gene.rightTAD.end))
				distance = abs(gene.leftTAD.end - gene.rightTAD.end)
			else:
				tadRange = list(range(gene.leftTAD.end, gene.rightTAD.start))
				distance = abs(gene.leftTAD.end - gene.rightTAD.start)
			
			plotRange = list(range(0, distance))
			
			
			
			geneGainedEQTLs = 0
			geneLostEQTLs = 0
			
			
			#Cover for the case when there are no gains, but losses and vv
			if len(list(gene.lostEQTLs.keys())) < 1 and len(list(gene.gainedEQTLs.keys())) > 0:
				samples = list(gene.gainedEQTLs.keys()) 
			elif len(list(gene.gainedEQTLs.keys())) < 1 and len(list(gene.lostEQTLs.keys())) > 0:
				samples = list(gene.lostEQTLs.keys())
			else: #combine the samples
				samples = list(gene.lostEQTLs.keys()) + list(gene.gainedEQTLs.keys())
			
			if len(samples) > 1 and len(samples) < 10:
				
				startPlot = int(str(int(math.ceil(len(samples) / 2.0))) + "21")
				print(startPlot)
			elif len(samples) > 9:
				startPlot = int(str(int(math.ceil(len(samples) / 2.0))) + "31")
				print(startPlot)
				
			else:
				startPlot = int(str(int(math.ceil(len(samples) / 2.0))) + "11")
			
			# if len(gene.lostEQTLs.keys()) > 7: #look for interesting genes with recurrent mutations
			# 	print gene.name
			# 	
			# else:
			# 	continue
			
			for sample in samples:
				
				
				
				if sample in gene.lostEQTLs:
					
					print("sample ", sample, "lost: ", len(gene.lostEQTLs[sample]))
				if sample in gene.gainedEQTLs:
					
				
					print("sample ", sample, "gained: ", len(gene.gainedEQTLs[sample]))
					
					#Get the TAD that the SV ends in. 
					otherTAD = gene.gainedEQTLs[sample][1]
					#The TAD range is the entire length of the TAD for now, but eventually we also need to take into account that inside this TAD some eQTLs are also deleted and are thus probably not gained. 
					
					print(otherTAD)
					gainedTadRange = list(range(otherTAD.start, otherTAD.end))
					gainedTadDistance = abs(otherTAD.start - otherTAD.end)
				
					gainedPlotRange = list(range(0, gainedTadDistance))
					gainedEQTLPositions = np.zeros(gainedTadDistance)
				
					for eQTL in gene.gainedEQTLs[sample][0]: #The TAD is the last element
				
						eQTLPos = eQTL.start
						
						geneGainedEQTLs += 1
						
						#The position in the array depends on the positions within the actual tad
						tadInd = gainedTadRange.index(eQTLPos)	
						gainedEQTLPositions[tadInd] = 1
				
					#Plot the gains per sample per gene
					print("Plotting gains for sample ", sample, " and gene ", gene.name)
					plt.subplot(startPlot)
					plt.subplots_adjust(hspace=2)
					startPlot += 1
					plt.title(sample)
					plt.plot(gainedPlotRange, gainedEQTLPositions)
					plt.ylim(-2,2)
					label = str(otherTAD.start) + "-" + str(otherTAD.end)
					plt.xlabel(label)
					
					#plt.show()
				
				# if sample in gene.lostEQTLs:
				# 	eQTLPositions = np.zeros(distance)
				# 
				# 	geneStartPos = tadRange.index(gene.start)
				# 	geneEndPos = tadRange.index(gene.end)
				# 	eQTLPositions[geneStartPos:geneEndPos] = 1
				# 	print eQTLPositions
				# 	
				# 	for eQTL in gene.lostEQTLs[sample]:
				# 		
				# 		eQTLPos = eQTL.start
				# 		
				# 		if eQTLPos < gene.leftTAD.end or eQTLPos > gene.rightTAD.start: #skip the eQTL if it is outside of the TAD boundary
				# 			continue
				# 		
				# 		geneLostEQTLs += 1
				# 		
				# 		#The position in the array depends on the positions within the actual tad
				# 		tadInd = tadRange.index(eQTLPos)
				# 		
				# 		eQTLPositions[tadInd] = -1
				# 
				# 	 
				# 	
				# 
				# 	#Plot the gains and losses for each gene per sample
				# 	print "Plotting losses for sample ", sample, " and gene ", gene.name
				# 	print startPlot
				# 	plt.subplot(startPlot)
				# 	plt.subplots_adjust(hspace=2)
				# 	startPlot += 1
				# 	
				# 	if startPlot % 10 == 0:
				# 		startPlot += 1
				# 	
				# 	plt.title(sample)
				# 	plt.plot(plotRange, eQTLPositions)
				# 	plt.ylim(-2,2)
				# 	label = str(tadRange[0]) + "-" + str(tadRange[len(tadRange)-1])
				# 	plt.xlabel(label)
				# 	plt.show()
				# 	exit()
				
			plt.show()
			exit()
			# plt.plot(plotRange, eQTLPositions)
			# plt.ylim(-2,2)
			# plt.show()
			# 	
			#return
		# print "plotting"
		# plt.boxplot(gainedEQTLs)
		# plt.show()
		# plt.boxplot(lostEQTLs)
		# plt.show()
		#return
		
		
		
	def visualizeDelta(self, genes):
		
		1+1
	
	