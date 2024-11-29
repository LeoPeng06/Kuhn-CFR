from __future__ import annotations

from tabulate import tabulate
import matplotlib.pyplot as plot
import sys


infoSet: dict[str, InfoSetData] = {}
knownInfoSets = []

Cards = ['K', 'Q', 'J']
Actions = ["b", "p"]

finished = {
 "pp",
 "bb",
 "bp",
 "pbb",
 "pbp"
}
#Action Sequences where there is no more action to be taken, ending the round

infoSetSequences = {
    "p",
    "b",
    "pb",
    ""
}
# Action sequences where there is still action to be taken, thus adding it to the infoset

def currentPlayer(infoSetStr: str): #returns current player
    return (len(infoSetStr)-1) % 2

#stores data for each individual dataset
class InfoSetData:
    def __init__(self): #initialize strategy
        self.actions: dict[str, InfoSetActionData] = {
            "b": InfoSetActionData(initStratVal=1/len(Actions)),
            "p": InfoSetActionData(initStratVal=1/len(Actions)),
        }

        self.beliefs: dict[str, float] = {}
        self.expectedUtility: float = None
        self.likelihood: float = None

    @staticmethod
    #creates table for the "Optimal Move" based on previous actions and your card
    def printTable(infoSets: dict[str, InfoSetData]):

        rows = []
        for infoSetStr in knownInfoSets:
            currentInfoSet = infoSet[infoSetStr]
            row= [infoSetStr, *currentInfoSet.getStrategyTableData(), infoSetStr, *currentInfoSet.getBeliefTableData(),infoSetStr,*currentInfoSet.getUtilityTableData, f'{currentInfoSet.expectedUtility:.2f}', f'{currentInfoSet.likelihood:.2f}',infoSetStr,*currentInfoSet.getGainTableData()]
            rows.append(row)
            headers = ["InfoSet","Strat:b", "Strat:p", "---","Belief:H", "Belief:L", "---","Util:b","Util:p","ExpectedUtil","Likelihood","---","TotGain:b","TotGain:p"]


        print(tabulate(rows, headers=headers,tablefmt="pretty",stralign="left"))

    def getStrategyTableData(self):
        return [f'{self.actions[action].strategy:.2f}' for action in Actions]
    
    def getUtilityTableData(self):
        return [f'{self.actions[action].util:.2f}' for action in Actions]
    
    def getGainTableData(self):
        return [f'{self.actions[action].cumulativeGain:.2f}' for action in Actions]
    
    def getBeliefTableData(self):
        return [f'{self.beliefs[oppHole]:.2f}' for oppHole in self.beliefs.keys()]
    
class InfoSetActionData:
    def __init__(self, initStratVal):
        self.strategy = initStratVal
        self.utility = None
        self.cumulativeGain = initStratVal

def getOpponentCards(holeCard):
    return [card for card in Cards if card != holeCard]

def getPreviousInfoSets(infoSetStr) -> list[InfoSetData]:
    if len(infoSetStr) == 1:
        raise ValueError("no previous info in the infoset" + infoSetStr)
    
    possibleOpponentCards = getOpponentCards(infoSetStr[0])
    return [oppHole + infoSetStr[1:-1] for oppHole in possibleOpponentCards ]

def getFutureInfoSets(infoSetStr, action):
    possibleOpponentCards = getOpponentCards(infoSetStr[0])
    actionStr = infoSetStr[1:]+action
    return [oppHole +actionStr for oppHole in possibleOpponentCards]

def Player1Win(hole1, hole2):
    if hole1 == "K":
        return True
    elif hole1 == "J":
        if hole2 == "K":
            return False
        else:
            return True
    else:
        return False
    
def finalUtility(hole1, hole2, actionStr: str):
    if actionStr == "pp":
        if Player1Win(hole1,hole2):
            return 1,-1
        else:
            return -1,1
    elif actionStr == "bb":
        if Player1Win(hole1,hole2):
            return 2,-2
        else:
            return -2,2
    elif actionStr == "pbp":
        return -1, 1
    elif actionStr == "bp":
        return 1, -1
    elif actionStr == "pbb":
        if Player1Win(hole1,hole2):
            return 2, -2
        else:
            return -2, 2
        

def initDataSets():
    for actionStrs in sorted(Actions, key=lambda x:len(x)):
        for card in Cards:
            infoSetStr = card + actionStrs
            if infoSetStr not in infoSet:
                print(f"Initializing: {infoSetStr}")
            infoSet[infoSetStr] = InfoSetData()
            knownInfoSets.append(infoSetStr)


def updateBeliefs():
    for infoSetStr in knownInfoSets:
        info = infoSet[infoSetStr]
        if len(infoSetStr) == 1:
            oppCards = getOpponentCards(infoSetStr[0])
            for oppCard in oppCards:
                info.beliefs[oppCard] = 1/ len(oppCards)
        else:
            pastInfoSetStrs = getPreviousInfoSets(infoSetStr)
            lastAct = infoSetStr[-1]
            total = 0
            for oppInfoSetStr in pastInfoSetStrs:
                oppInfoSet = infoSet[oppInfoSetStr]
                total += oppInfoSet.actions[lastAct].strategy
            for oppInfoSetStr in pastInfoSetStrs:
                oppInfoSet = infoSet[oppInfoSetStr]
                oppCard = oppInfoSetStr[0]
                info.beliefs[oppCard] = oppInfoSet.actions[lastAct].strategy/total
    return


def updateUtilities(infoSetStr):
    PlayerNum = currentPlayer(infoSetStr)
    info = infoSet[infoSetStr]
    beliefs = info.beliefs
    for action in Actions:
        actionStr=infoSetStr[1:]+action
        futureInfoSetStrs = getFutureInfoSets(infoSetStr, action)
        utilFromInfoSets = 0
        utilFromFinished = 0
        for futureInfoSetStr in futureInfoSetStrs:
            infoSetProb = beliefs[futureInfoSetStr[0]]
            holeCards = [infoSetStr[0],futureInfoSetStr[0]]

            if PlayerNum == 1:
                holeCards = list(reversed(holeCards))
            if actionStr in finished:
                utils = finalUtility(*holeCards, actionStr)
                utilFromFinished+= infoSetProb*utils[PlayerNum]
            else:
                futureInfoSet = infoSet[futureInfoSetStr]
                for oppAction in Actions:
                    probOfOppAction = futureInfoSet.actions[oppAction].strategy
                    destinationInfoSetStr = infoSetStr + action +oppAction
                    destinationActionStr = destinationInfoSetStr[1:]
                    if destinationActionStr in finished:
                        utils = finalUtility(*holeCards, destinationActionStr)
                        utilFromFinished += infoSetProb*probOfOppAction*utils[PlayerNum]
                    else:
                        destinationInfoSet = infoSet[destinationInfoSetStr]
                        utilFromInfoSets+= infoSetProb*probOfOppAction*destinationInfoSet.expectedUtility
        info.actions[action].utility = utilFromInfoSets+utilFromFinished
    info.expectedUtility = 0
    for action in Actions:
        actionData = info.actions[action]
        info.expectedUtility += actionData.strategy*actionData.utility

def calcInfoSetOdds():
    for infoSetStr in knownInfoSets:
        info = infoSet[infoSetStr]
        info.likelihood=0
        possibleOpponentCards = getOpponentCards(infoSetStr[0])
        if len(infoSetStr) == 1:
            info.likelihood = 1/len(Cards)
        elif len(infoSetStr) == 2:
            for opponentCard in possibleOpponentCards:
                oppInfoSet = infoSet[opponentCard+infoSetStr[1:-1]]
                info.likelihood += oppInfoSet.actions[infoSetStr[-1]].strategy/(len(Cards)*len(possibleOpponentCards))
        else:
            for opponentCard in possibleOpponentCards:
                oppInfoSet = infoSet[opponentCard + infoSetStr[1:-1]]
                twoInfoSetsAgo = infoSet[infoSetStr:-2]
                pastOdds = twoInfoSetsAgo.likelihood/len(possibleOpponentCards)
                info.likelihood += pastOdds*oppInfoSet.actions[infoSetStr[-1]].strategy

def calcWinnings():
    totalGain = 0.0
    for infoSetStr in finished:
        info = infoSet[infoSetStr]
        for action in Actions:
            utilForAction = info.actions[action].utility
            gain = max(0, utilForAction-info.expectedUtility)
            totalGain += gain
            info.actions[action].cumulativeGain+= gain * info.likelihood
    return totalGain

def updateStrategy():
    for infoSetStr in finished:
        info =  infoSet[infoSetStr]
        gains = [info.actions[action].cumulativeGain for action in Actions]
        totalGains = sum(gains)
        for action in Actions:
            gain = info.actions[action].cumulativeGain
            info.actions[action].strategy = gain/totalGains


def setInitialStrategy():
#player 1
    infoSet["K"].actions["b"].strategy = 2/3
    infoSet["K"].actions["p"].strategy = 1/3

    infoSet["Q"].actions["b"].strategy = 1/2
    infoSet["Q"].actions["p"].strategy = 1/2

    infoSet["J"].actions["b"].strategy = 1/3
    infoSet["J"].actions["p"].strategy = 2/3

    infoSet["Kpb"].actions["b"].strategy = 1
    infoSet["Kpb"].actions["p"].strategy = 0

    infoSet["Qpb"].actions["b"].strategy = 1/2
    infoSet["Qpb"].actions["p"].strategy = 1/2

    infoSet["Jpb"].actions["b"].strategy = 0
    infoSet["Jpb"].actions["p"].strategy = 1

#player 2

    infoSet["Kb"].actions["b"].strategy = 1
    infoSet["Kb"].actions["p"].strategy = 0
    infoSet["Kp"].actions["b"].strategy = 1
    infoSet["Kp"].actions["p"].strategy = 0

    infoSet["Qb"].actions["b"].strategy = 1/2
    infoSet["Qb"].actions["p"].strategy = 1/2
    infoSet["Qp"].actions["b"].strategy = 2/3
    infoSet["Qp"].actions["p"].strategy = 1/3

    infoSet["Jb"].actions["b"].strategy = 0
    infoSet["Jb"].actions["p"].strategy = 1
    infoSet["Jp"].actions["b"].strategy = 1/3
    infoSet["Jp"].actions["p"].strategy = 2/3


if __name__ == "__main__":
    initDataSets()
    # setInitialStrategiesToSpecificValues() # uncomment in order to get the values in professor bryce's youtube video: https://www.youtube.com/watch?v=ygDt_AumPr0&t=668s: Counterfactual Regret Minimization (AGT 26)

    numIterations=300000 # best numIterations for closest convergence
    # numIterations=3000 # best numIterations for plotting the convergence
    # numIterations=1 # best to checking that the output values match professor bryce's youtube video: https://www.youtube.com/watch?v=ygDt_AumPr0&t=668s: Counterfactual Regret Minimization (AGT 26)
    totGains = []

    # only plot the gain from every xth iteration (in order to lessen the amount of data that needs to be plotted)
    numGainsToPlot=100 
    gainGrpSize = numIterations//numGainsToPlot 
    if gainGrpSize==0:
       gainGrpSize=1

    for i in range(numIterations):
        updateBeliefs()

        for infoSetStr in reversed(finished):
            updateUtilities(infoSetStr)

        calcInfoSetOdds()
        totGain = calcWinnings()
        if i%gainGrpSize==0: # every 10 or 100 or x rounds, save off the gain so we can plot it afterwards and visually see convergence
            totGains.append(totGain)
            print(f'TOT_GAIN {totGain: .3f}')
        updateStrategy()

    InfoSetData.printInfoSetDataTable(infoSet)

    print(f'Plotting {len(totGains)} totGains')
    # Generate random x, y coordinates
    x = [x*gainGrpSize for x in range(len(totGains))]
    y = totGains

    # Create scatter plot
    plt.scatter(x, y)

    # Set title and labels
    plt.title('Total Gain per iteration')
    plt.xlabel(f'Iteration # ')
    plt.ylabel('Total Gain In Round')

    # Display the plot
    plt.show()








    
