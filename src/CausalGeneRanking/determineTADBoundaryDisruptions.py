"""
	For every TAD, count how many patients have an SV overlapping that TAD boundary

"""

from __future__ import absolute_import
from __future__ import print_function
from inputParser import InputParser
from genomicShuffler import GenomicShuffler
import sys
import numpy as np
import matplotlib.pyplot as plt
from six.moves import range
import settings


excludedSVs = np.loadtxt(settings.files['excludedSVs'], dtype='object')
somaticSVs = InputParser().getSVsFromFile(sys.argv[1], "all", excludedSVs)

filteredSomaticSVs = [] #first filter the SVs to remove the translocations, there are not relevant here
for somaticSV in somaticSVs:
	if somaticSV[0] == somaticSV[3]:
		filteredSomaticSVs.append(somaticSV)
filteredSomaticSVs = np.array(filteredSomaticSVs, dtype="object")


filteredSVs = []
for sv in filteredSomaticSVs:
	svEntry = sv[0] + "_" + str(sv[1]) + "_" + str(sv[2]) + "_" + sv[3] + "_" + str(sv[4]) + "_" + str(sv[5]) + "_" + sv[8].sampleName
	if svEntry not in excludedSVs:
		filteredSVs.append(sv)

filteredSVs = np.array(filteredSVs, dtype='object')

# # Shuffling SVs randomly
print("Shuffling variants")
genomicShuffler = GenomicShuffler()
#Shuffle the variants, provide the mode such that the function knows how to permute
filteredSVs = genomicShuffler.shuffleSVs(filteredSVs)

tads = InputParser().getTADsFromFile(sys.argv[2])

tadDisruptions = [] #keep the number of samples across each TAD.
tadDisruptionsDict = dict()

for i in range(0,28):
	tadDisruptionsDict[i] = 0

for tad in tads:
	
	#check if there is any SV overlapping this boundary
	#we can exclude translocations here, so no need to look at chr2
	#if the same SV overlaps both the start and the end, count it only once

	svChrSubset = filteredSVs[filteredSVs[:,0] == tad[0],:]
	
	startMatches = (tad[1] >= svChrSubset[:,1]) * (tad[1] <= svChrSubset[:,5])
	endMatches = (tad[2] >= svChrSubset[:,1]) * (tad[2] <= svChrSubset[:,5])
	
	#Use sum to include either, and both only once
	matches = startMatches + endMatches
	
	matchingSVs = svChrSubset[matches]
	
	if len(matchingSVs) > 0:
		#Count only 1 SV per sample
		samples = np.unique(matchingSVs[:,7])
		svTypes = dict()
		for sv in matchingSVs:
			if sv[8].svType not in svTypes:
				svTypes[sv[8].svType] = 0
			svTypes[sv[8].svType] += 1	

		tadDisruptionsDict[len(samples)] += 1
		tadDisruptions.append(len(samples))
	else:
		tadDisruptionsDict[0] += 1
		tadDisruptions.append(0)

print(np.sum(list(tadDisruptionsDict.values())))
		
#plt.hist(tadDisruptions)
plt.bar(list(tadDisruptionsDict.keys()), list(tadDisruptionsDict.values()))
plt.ylim(0,3300)
plt.xlim(-1,28)
plt.show()


	
	
	
	
	

