files = dict(
	
	eQTLFile = '../../data/eQTLs/breast_eQTLs.bed', #File with eQTLs specific for breast tissue
	enhancerFile = '../../../data/enhancers/enhancer_gene_GM12878.txt', #File with enhancers specific for normal cell lines
	promoterFile = '../../../data/promoters/epdnew_hg38ToHg19_9vC8m.bed', #File with promoters in human, not cell-specific
	cpgFile = '../../../data/cpg/cpgIslandExt.txt', #All human CpG sites
	tfFile = '../../../data/tf/tf_experimentallyValidated.bed', #All validated human TFs
	h3k9me3 = '../../../data/histones/ENCFF065FJK_H3K9me3.bed',
	h3k4me3 = '../../../data/histones/ENCFF065TIH_H3K4me3.bed',
	h3k27ac = '../../../data/histones/ENCFF154XFN_H3K27ac.bed',
	h3k27me3 = '../../../data/histones/ENCFF291WFP_H3K27me3.bed',
	h3k4me1 = '../../../data/histones/ENCFF336DDM_H3K4me1.bed',
	h3k36me3 = '../../../data/histones/ENCFF906MJM_H3K36me3.bed',
	dnaseIFile = '../../../data/dnase/ENCFF301VRH.bed',
	hicFile = '../../../data/hic/HMEC_groupedTADInteractions.txt',
	tadFile = "../../../data/tads/HMEC_Lieberman-raw_TADs.bed", #File with TADs specific for breast tissue
	rankedGeneScoreDir = "Output/RankedGenes", #File that the output scores will be written to. The output will be in a folder with the provided UUID under this main results folder
	hg19CoordinatesFile = "../../data/chromosomes/hg19Coordinates.txt",
	causalGenesFile = '../../../data/genes/CCGC.tsv', #file with all causal genes from cosmic. 
	nonCausalGenesFile = '../../../data/genes/hg19_proteinCodingGenes.bed' #file with all protein-coding genes.
)

general = dict(
	
	mode = 'SV', #Options are: SV, SNV or SV+SNV
	cancerType = 'BRCA', #Use to specify which cancer type the data should be filtered by
	nonCoding = True, #Should we count gains/losses for genes that are affected by non-coding SVS?
	coding = False, #Should we include gains and losses of non-coding elements, or only genes that are directly affected by SVs? 
	gains = True, #Enable looking at gains of features
	losses = True, #enable looking at losses of features
	tads = True, #Include TADs in the ranking yes/no, only to rank by how often TAD boundaries themselves are disrupted by SVs. (we are getting very dependent on TADs, so perhaps force this as always required)
	eQTLs = False, #Include eQTLs in the ranking yes/no
	enhancers = True, #Include enhancers in the ranking yes/no
	promoters = True, #Include promoters in the ranking yes/no
	cpgIslands = True, #Include CpG islands in the ranking yes/no
	transcriptionFactors = True, #Include TFs in the ranking yes/no
	hiC = True, #Include HiC interactions in the ranking yes/no
	histones = True, #Include the histone marks in the ranking yes/no (maybe these need to be split later)
	dnaseI = True, #Include DNAse I hypersensitivity sites yes/no
	genes = True
)

interactions = dict( #settings specific for Hi-C interaction data
	binSize = 5000 
	
	
)
