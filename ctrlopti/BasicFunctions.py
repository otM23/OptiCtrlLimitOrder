# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 20:15:20 2016

@author: Otm
"""


##############################################################################################################
##############################################################################################################
############################################# Basic Functions  ##################################################
##############################################################################################################
##############################################################################################################

def ProbTrans(lambdaInserSame,lambdaCancelSame,lambdaInserOpp,lambdaCancelOpp,TimeStep):
    """ lambdaInserSame = insertion intensity Bid """
    """ lambdaCancelSame = cancellation intensity Bid """
    """ lambdaInserOpp = insertion intensity Ask """
    """ lambdaCancelOpp = cancellation intensity Ask """
    """ TimeStep = Basic time step"""
    # Unit quantity inserted in the ask side
    q1=lambdaInserOpp*TimeStep*(1-lambdaCancelOpp*TimeStep)*(1-lambdaInserSame*TimeStep)*(1-lambdaCancelSame*TimeStep)
    # Unit quantity consumed in the ask side
    q2=lambdaCancelOpp*TimeStep*(1-lambdaInserOpp*TimeStep)*(1-lambdaInserSame*TimeStep)*(1-lambdaCancelSame*TimeStep)
    # Unit quantity inserted in the bid side
    q3=lambdaInserSame*TimeStep*(1-lambdaInserOpp*TimeStep)*(1-lambdaCancelOpp*TimeStep)*(1-lambdaCancelSame*TimeStep)
    # Unit quantity consumed in the bid side
    q4=lambdaCancelSame*TimeStep*(1-lambdaInserOpp*TimeStep)*(1-lambdaCancelOpp*TimeStep)*(1-lambdaInserSame*TimeStep)
    # Nothing happens
    q5=1-(q1+q2+q3+q4)
    return [q1,q2,q3,q4,q5]


## Compute Imbalance
def ImbalanceI(QSame,Qopp):
    ''' QSame =  quantity in the same side'''
    ''' Qopp =  quantity in the opposite side'''
    return float(QSame-Qopp)/(QSame+Qopp)

## Compute Mean Imbalance of the Sons 
## This can be forgotten for a first reading
def ImbalanceS(Sons,StatesIndex,ProbaTransI):
    ''' Sons =  Sons of an element'''
    ''' StatesIndex =  State of all visited states'''
    ''' ProbaTransI =  array containing the probabilities of transition'''
    NbSons = len(Sons)
    MeanImbalance = 0
    if (NbSons) :
        for IndexSon in range(NbSons):
            Son = Sons[IndexSon]
            QSame = StatesIndex[Son][0]+StatesIndex[Son][1]
            Qopp = StatesIndex[Son][2]
            ImbalanceSon = ImbalanceI(QSame,Qopp)
            MeanImbalance += ImbalanceSon
        return float(MeanImbalance/NbSons)
    if not (NbSons) : 
        return(-1) # Final State with no sons
    
# Create New graph element
def CreateElmt1(QBefI,QAftI,QOppI,ExecI=0,ChangePrice=0,typeExec='s'):
    """ QBefI = quantity before the unit order """
    """ QAftI = quantity after the unit order """
    """ QOppI = quantity in the opposite side """
    """ ExecI = 0 when the order isn't executed, 1 when the order is executed, -1 when it has been executed"""
    """ ChangePrice = 0 if the price doesn't change, 1 when the price moves up and -1 when the price moves down"""
    return [QBefI,QAftI,QOppI,ExecI,ChangePrice,typeExec]
    
def CreateGraphElmt(Sons=list(),NbPassingTime=list(),ProbState=list()):
    """ Sons = Son's Index """
    """ NbPassingTime = Nb of Times passing by state at step n """
    """ MeanPriceVariation = Mean Price Variation at step n"""
    return [Sons,NbPassingTime,ProbState]
       
## The Id associated to a state to find it easier using a set and not a list
def IdStates(State):
    return (str(State)[1:-1].replace(" ",""))
    

# The following function updates the transition proba and the mean price move in the stay limit order algorithm
def UpdateProbTransPriceMoveStay(FatherIndex,graph,StatesIndex,OldProbaTrans,NbPassingTime,ProbTransI,PriceJump,UnitQuant):
    NbTrans = 5  # Nb sons.
    sumProbUnExec = 0 
    sumProbExec = 0 
    pricemove = 0
    for IndexTransition in range(NbTrans-2):
        ProbTrans0 = OldProbaTrans*ProbTransI[IndexTransition] 
        SonIndex = graph[FatherIndex][0][IndexTransition] # the first son (under control s) index has an even index
        graph[SonIndex][1][-1]+= NbPassingTime
        graph[SonIndex][2][-1]+= ProbTrans0
        sumProbUnExec += ProbTrans0
        pricemove += PriceJump*StatesIndex[SonIndex][4]*ProbTrans0
        
    IndexTransition = 3
    SonIndex = graph[FatherIndex][0][IndexTransition]
    QBefSon = StatesIndex[SonIndex][0]
    if (QBefSon >= 2*UnitQuant):
        ProbTrans0 = OldProbaTrans*ProbTransI[IndexTransition] 
        graph[SonIndex][1][-1]+= NbPassingTime
        graph[SonIndex][2][-1]+= ProbTrans0
        pricemove += PriceJump*StatesIndex[SonIndex][4]*ProbTrans0
        sumProbUnExec += ProbTrans0
    if (QBefSon < 2*UnitQuant):
        ProbTrans0 = OldProbaTrans*ProbTransI[IndexTransition]
        graph[SonIndex][1][-1]+= NbPassingTime
        graph[SonIndex][2][-1]+= ProbTrans0
        pricemove += PriceJump*StatesIndex[SonIndex][4]*ProbTrans0
        sumProbExec += ProbTrans0
        
    return [sumProbExec,sumProbUnExec,pricemove]
    
def ComputeLatencyUtility(ProbFatherState,FatherState,ctrl,UtilityAfter,bsgraph,StatesIndex,LatencyFactor,IntensFunc,TimeStep):
    Utility = 0
    SonState = set()
    ProbSonState = dict()  
    if LatencyFactor == 1 : 
        for j in FatherState:
            qsame = (StatesIndex[j][0]+StatesIndex[j][1]) 
            qopp = StatesIndex[j][2] 
            lambdaPlusOpp= IntensFunc(qsame, qopp,'OppPlus') # intensité insertion Ask
            lambdaMoinsOpp= IntensFunc(qsame, qopp,'OppMoins') # intensité annulation Ask
            lambdaPlusSame= IntensFunc(qsame, qopp,'SamePlus')  # intensité insertion Bid
            lambdaMoinsSame= IntensFunc(qsame, qopp,'SameMoins') # intensité annulation Bid
            FatherProbTrans=ProbTrans(lambdaPlusSame,lambdaMoinsSame,lambdaPlusOpp,lambdaMoinsOpp,TimeStep)
        
            SonStatesize = len(bsgraph[j])
            for k in range(ctrl,SonStatesize,2) :
                son = bsgraph[j][k]
                Utility+= UtilityAfter[son]*FatherProbTrans[k//2]*ProbFatherState[j]
        return Utility 
    if LatencyFactor > 1 :
        for j in FatherState:
            qsame = (StatesIndex[j][0]+StatesIndex[j][1]) 
            qopp = StatesIndex[j][2] 
            lambdaPlusOpp= IntensFunc(qsame, qopp,'OppPlus') # intensité insertion Ask
            lambdaMoinsOpp= IntensFunc(qsame, qopp,'OppMoins') # intensité annulation Ask
            lambdaPlusSame= IntensFunc(qsame, qopp,'SamePlus')  # intensité insertion Bid
            lambdaMoinsSame= IntensFunc(qsame, qopp,'SameMoins') # intensité annulation Bid
            FatherProbTrans=ProbTrans(lambdaPlusSame,lambdaMoinsSame,lambdaPlusOpp,lambdaMoinsOpp,TimeStep)

            SonStatesize  = len(bsgraph[j])
            for k in range(ctrl,SonStatesize,2) : 
                son = bsgraph[j][k]
                SonState.add(son)
                if son in ProbSonState :
                    ProbSonState[son] += FatherProbTrans[k//2]*ProbFatherState[j]
                else : 
                    ProbSonState[son] = FatherProbTrans[k//2]*ProbFatherState[j]            
                
        return ComputeLatencyUtility(ProbSonState,SonState,ctrl,UtilityAfter,bsgraph,StatesIndex,LatencyFactor-1,IntensFunc,TimeStep)