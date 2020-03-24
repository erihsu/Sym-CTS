import os
import numpy as np, random,operator,pandas as pd
from fitness import Fitness
# the code below is partially editted from another repository 
# https://github.com/ezstoltz/genetic-algorithm

#create buffer insertion strategy 
#创建一个缓冲器插入策略，一个插入策略对应一种染色体编码。染色体上的基因代表不同尺寸buffer的编号，0代表不差buffer，数字越大，buffer尺寸越大
def createStrategy(buffer_lib_size,branch_level):
	solution = []
	for _ in range(branch_level):
		solution.append(random.randint(0, buffer_lib_size))
	return solution

# create first population (list of strategies)
# 初始化种群
def initialPopulation(popSize, buffer_lib_size, branch_level):
	population = []

	for _ in range(0, popSize):
		population.append(createStrategy(buffer_lib_size, branch_level))
	return population

# rank individuals (strategies) in a population
# 对种群内的个体按照适应度进行排序
def rankStrategies(population):
	fitnessResults = {}
	u = Fitness()
	for i in range(0, len(population)):
		fitnessResults[i] = u.objFitness(population[i])
	return sorted(fitnessResults.items(),key = operator.itemgetter(1), reverse = True)

# selection function that will be used to make the list of parent strategies
# 采用精英策略来选择个体来作为父体
def selection(popRanked, eliteSize):
	selectionResults = []
	df = pd.DataFrame(np.array(popRanked), columns=["Index","Fitness"])
	df["cum_sum"] = df.Fitness.cumsum()
	df["cum_perc"] = 100*df.cum_sum/df.Fitness.sum()

	for i in range(0, eliteSize):
		selectionResults.append(popRanked[i][0])

	for i in range(0, len(popRanked)-eliteSize):
		pick = 100*random.random()
		for j in range(0, len(popRanked)):
			if pick <= df.iat[j,3]:
				selectionResults.append(popRanked[i][0])
				break 
	return selectionResults

# create mating pool
# 创建交配池
def matingPool(population, selectionResults):
	matingpool = []
	for i in range(0, len(selectionResults)):
		index = selectionResults[i]
		matingpool.append(population[index])
	return matingpool

# crossover function for two parents to create one child
# 父本之间交配
def breed(parent1, parent2):
	child = []
	childP1 = []
	childP2 = []

	random_index = random.sample(range(1,len(parent1)-1), 2)
	startGene = min(random_index)
	endGene   = max(random_index)

	childP1  = parent1[startGene:endGene]

	childP2 = parent2[:startGene] + parent2[endGene:]

	child = childP1 + childP2

	return child 

# crossover over full mating pool
# 在交配池内对所有对偶进行交配
def breedPopulation(matingpool, eliteSize):
	children = []
	length = len(matingpool) - eliteSize
	pool = random.sample(matingpool, len(matingpool))
	for i in range(0,eliteSize):
		children.append(matingpool[i])
	for i in range(0, length):
		child = breed(pool[i], pool[len(matingpool)-i-1])
		children.append(child)
	return children

# function to mutate a single strategy
# 个体变异	
def mutate(individual, mutationRate):
	for swapped in range(len(individual)):
		if (random.random() < mutationRate):
			swapWith = int(random.random()*len(individual))

			strategy1 = individual[swapped]
			strategy2 = individual[swapWith]

			individual[swapped] = strategy2
			individual[swapWith] = strategy1
	return individual

# function to run mutation over entire population
# 在整个种群内进行变异
def mutatePopulation(population, mutationRate):
	mutatedPop = []
	for ind in range(0, len(population)):
		mutatedInd = mutate(population[ind], mutationRate)
		mutatedPop.append(mutatedInd)
	return mutatedPop

# combine all steps to create the next generation
# 建立产生下一代个体的过程
def nextGeneration(currentGen, eliteSize, mutationRate):
	popRanked = rankStrategies(currentGen)
	selectionResults = selection(popRanked, eliteSize)
	matingpool = matingPool(currentGen, selectionResults)
	children = breedPopulation(matingpool, eliteSize)
	nextGeneration = mutatePopulation(children, mutationRate)
	return nextGeneration

# main genetic algorithm
# 完整的遗传算法
def geneticAlgorithm(buffer_lib_size, branch_level, popSize, eliteSize, mutationRate, generations):
	pop = initialPopulation(popSize, buffer_lib_size, branch_level)
	print("Initial objvalue: " + str(rankStrategies(pop)[0][1]))
	for i in range(0, generations):
		pop = nextGeneration(pop, eliteSize, mutationRate)
		if i % 5 == 0:
			print("{}th generations:{};objvalue:{}".format(i,pop[0],str(rankStrategies(pop)[0][1])))

	print("Final objvalue: " + str(rankStrategies(pop)[0][1]))
	bestStrategyIndex = rankStrategies(pop)[0][0]
	bestStrategy = pop[bestStrategyIndex]

	# export best solution
	with open("{}/symcts/solution.txt".format(os.getenv('SYMCTS')),'w') as f:
		for buffer_size in bestStrategy:
			f.write(str(buffer_size)+"\n")

def main():
	pass 

if __name__ == '__main__':
	main()
