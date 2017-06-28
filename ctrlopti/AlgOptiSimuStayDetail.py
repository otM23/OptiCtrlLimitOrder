# -*- coding: utf-8 -*-
"""
Created on Thu Jan 19 05:26:18 2017

@author: Otm
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Nov 23 20:unit0:unit5 20unit6

@author: Otm
"""

## Import libraries
import numpy as np
import pandas as pd
import copy
import BasicFunctions


## Optimisation :
class CtrlOptiSimuStay (object): 

    
    def __init__(self,QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinalConstraint,UnitQuant,PriceJump): 
        """Define attributes"""
        self.QAftI = QAftI
        self.QBefI = QBefI
        self.QOppI = QOppI
        self.P0 = P0
        self.TimeStep = TimeStep
        self.nbIter = nbIter
        self.IntensFunc = IntensFunc
        self.DiscQtyFunc = DiscQtyFunc
        self.FinalConstraint = FinalConstraint
        self.UnitQuant = UnitQuant
        self.PriceJump = PriceJump

    def forwardsimulationOpti(self):
        #Initialization
        StatesIndex=list()
        IdStatesIndex=set()
        fsGraphSons = dict()
        IndexNextStates=list()
        separation = [0]*(self.nbIter) # index of last reached state at each period
        ProbPeriod= np.zeros((self.nbIter+1,2)) # sum of proba for unexecuted states (first column) and already executed states (second column) during each period. Check that sum of proba equal to 1 (no loss of information)
        MeanPriceMove = [0]*(self.nbIter+1) # Mean price move at each period
        CountStates=0
    
        # Probabilities of transition
        qsame = (self.QAftI+self.QBefI) 
        qopp = self.QOppI 
        lambdaPlusOpp= self.IntensFunc(qsame, qopp,'OppPlus') # intensité insertion Ask
        lambdaMoinsOpp= self.IntensFunc(qsame, qopp,'OppMoins') # intensité annulation Ask
        lambdaPlusSame= self.IntensFunc(qsame, qopp,'SamePlus')  # intensité insertion Bid
        lambdaMoinsSame= self.IntensFunc(qsame, qopp,'SameMoins') # intensité annulation Bid
        [q1,q2,q3,q4,q5]=BasicFunctions.ProbTrans(lambdaPlusSame,lambdaMoinsSame,lambdaPlusOpp,lambdaMoinsOpp,self.TimeStep)
        
        # Create First State
        InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,self.QAftI,self.QOppI,ExecI=0,ChangePrice=0)
        StatesIndex.append(InitialStateMain)
        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
        fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[1])
        separation[0]=1
        ProbPeriod[0,0]=1 # initialisation : the initial state is fixed and has proba 1

        # The initial State can have 5 son States
        priceMovePeriod = 0
        # First Case : 1 unit quantity is added to QOpp (Under control c)
        CountStateSon = CountStates+1
        InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,self.QAftI,(self.QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
        StatesIndex.append(InitialStateMain)
        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
        fsGraphSons[CountStates][0].append(CountStateSon)
        fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q1])
        IndexNextStates.append(CountStateSon)
    
        # Second Case : 1 unit quantity is cancelled from QOpp (Under control c)
        # The price isn't modified in this Sub-Case
        if (self.QOppI >= 2*self.UnitQuant):
            CountStateSon +=1
            InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,self.QAftI,(self.QOppI-self.UnitQuant),ExecI=0,ChangePrice=0)
            StatesIndex.append(InitialStateMain)
            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
            fsGraphSons[CountStates][0].append(CountStateSon)
            fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q2])
            IndexNextStates.append(CountStateSon)
        # The price is modified in this Sub-Case
        if (self.QOppI < 2*self.UnitQuant):
            priceMovePeriod += self.PriceJump*q2
            [qdisc,qins] = self.DiscQtyFunc(qopp,qsame) 
            InitialStateMain = BasicFunctions.CreateElmt1(qins,0,qdisc,ExecI=0,ChangePrice=1)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex=StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates][0].append(SonIndex)
                fsGraphSons[SonIndex][1][0] += 1
                fsGraphSons[SonIndex][2][0] += q2  
            if not (IsOldState) :
                CountStateSon +=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates][0].append(CountStateSon)
                fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q2])
                IndexNextStates.append(CountStateSon)
    
        # Third Case : 1 unit quantity is added to QSame (Under Control c)
        InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,(self.QAftI+self.UnitQuant),self.QOppI,ExecI=0,ChangePrice=0)
        IdState=BasicFunctions.IdStates(InitialStateMain)
        IsOldState = (IdState in IdStatesIndex)
        if IsOldState :
            SonIndex = StatesIndex.index(InitialStateMain)
            fsGraphSons[CountStates][0].append(SonIndex)
            fsGraphSons[SonIndex][1][0] += 1
            fsGraphSons[SonIndex][2][0] += q3
        if not (IsOldState) :
            CountStateSon+=1
            StatesIndex.append(InitialStateMain)
            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
            fsGraphSons[CountStates][0].append(CountStateSon)
            fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q3])
            IndexNextStates.append(CountStateSon)
    
        # Fourth Case : 1 unit quantity is cancelled from QSame (Under control c)
        # In this Sub-Case the price doesn't change
        if (self.QBefI>= 2*self.UnitQuant):
            InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI-self.UnitQuant),self.QAftI,self.QOppI,ExecI=0,ChangePrice=0)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex = StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates][0].append(SonIndex)
                fsGraphSons[SonIndex][1][0] += 1
                fsGraphSons[SonIndex][2][0] += q4
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates][0].append(CountStateSon)
                fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q4])
                IndexNextStates.append(CountStateSon)
        # In this Sub-Case the order is executed but the price doesn't change 
        if ((self.QBefI < 2*self.UnitQuant)and(self.QAftI + self.QBefI >= 2*self.UnitQuant)):
            InitialStateMain = BasicFunctions.CreateElmt1((self.QAftI + self.QBefI -self.UnitQuant),0,self.QOppI,ExecI=1,ChangePrice=0)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex = StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates][0].append(SonIndex)
                fsGraphSons[SonIndex][1][0] += 1
                fsGraphSons[SonIndex][2][0] += q4
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates][0].append(CountStateSon)
                fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q4])
                IndexNextStates.append(CountStateSon)
        # Under control "c" : In this sub case the order is executed and the price changes
        if (self.QBefI+self.QAftI < 2*self.UnitQuant) :
            priceMovePeriod -= self.PriceJump*q4
            [qdisc,qins] = self.DiscQtyFunc(qsame,qopp) 
            InitialStateMain = BasicFunctions.CreateElmt1(qdisc,0,qins,ExecI=1,ChangePrice=-1)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex=StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates][0].append(SonIndex)
                fsGraphSons[SonIndex][1][0] += 1
                fsGraphSons[SonIndex][2][0] += q4
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates][0].append(CountStateSon)
                fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q4])
                IndexNextStates.append(CountStateSon)

    
        # Fifth case : Nothing happens under control c
        fsGraphSons[CountStates][0].append(CountStates)
        fsGraphSons[CountStates][1].append(1)
        fsGraphSons[CountStates][2].append(q5)
    
        CountStates+=CountStateSon
        if (self.QBefI >= 2*self.UnitQuant):
            ProbPeriod[1,0]=(q1+q2+q3+q4+q5) # all states are unexecuted
        if (self.QBefI < 2*self.UnitQuant):
            ProbPeriod[1,0]=(q1+q2+q3+q5) # unexecuted states
            ProbPeriod[1,1]=q4 # executed states
        MeanPriceMove[1]=priceMovePeriod
    
        ## Main program Before the final time period Tmax
        for i in range(self.nbIter-1):
            separation[i+1]=(CountStates+1)
            sizeP = len(IndexNextStates)
            IndexNextStates2=[0]*(9*sizeP)
            count=0
            sumProbExec=0
            sumProbUnExec=0
            priceMovePeriod=0
            ## Step 1 : we instantiate the new values of variables : NbPassingTime and ProbaPassingTime
            for j in range(CountStates+1):
                NbPassingTimePeriodBefore = fsGraphSons[j][1][-1] # Old value of NbPassingTime
                ProbaPassingTimePeriodBefore = fsGraphSons[j][2][-1] # Old value ProbaPassingTime
                fsGraphSons[j][1].append(NbPassingTimePeriodBefore) # instantiate the new NbPassingTime
                ExecState = StatesIndex[j][3]
                if (ExecState == 0):
                    ProbaPassingTimeNew = ProbaPassingTimePeriodBefore*q5 # new value of proba passing time
                    fsGraphSons[j][2].append(ProbaPassingTimeNew) # instantiate and update (partially) by the way the new ProbaPassingTime
                    sumProbUnExec += ProbaPassingTimeNew
                    
                if (ExecState == 1):
                    fsGraphSons[j][2].append(ProbaPassingTimePeriodBefore) # instantiate and update (partially) by the way the new ProbaPassingTime
                    sumProbExec += ProbaPassingTimePeriodBefore
            
            ## Step 2 : update the variables (partially - for the already visited states): NbPassingTime, ProbaPassingTime, pricemovePeriod, sumProbExec and sumProbUnExec
            for j in range(separation[i]):
                ExecState = StatesIndex[j][3]
                if (ExecState==0):
                    qsame = (StatesIndex[j][0]+StatesIndex[j][1]) 
                    qopp = StatesIndex[j][2]
                    lambdaPlusOpp= self.IntensFunc(qsame, qopp,'OppPlus') # intensité insertion Ask
                    lambdaMoinsOpp= self.IntensFunc(qsame, qopp,'OppMoins') # intensité annulation Ask
                    lambdaPlusSame= self.IntensFunc(qsame, qopp,'SamePlus')  # intensité insertion Bid
                    lambdaMoinsSame= self.IntensFunc(qsame, qopp,'SameMoins') # intensité annulation Bid
                    ProbTransI=BasicFunctions.ProbTrans(lambdaPlusSame,lambdaMoinsSame,lambdaPlusOpp,lambdaMoinsOpp,self.TimeStep)
                    ProbaPassingTimePeriodBefore=fsGraphSons[j][2][-2]
                    NbPassingTimePeriodBefore = fsGraphSons[j][1][-2]
                    # Update ProbaExec and PriceMove
                    [sumProbExecAuxi,sumProbUnExecAuxi,pricemoveAuxi] = BasicFunctions.UpdateProbTransPriceMoveStay(j,fsGraphSons,StatesIndex,ProbaPassingTimePeriodBefore,NbPassingTimePeriodBefore,ProbTransI,self.PriceJump,self.UnitQuant)
                    sumProbExec += sumProbExecAuxi
                    sumProbUnExec += sumProbUnExecAuxi
                    priceMovePeriod += pricemoveAuxi

                            
            ## Step 3 : update the variables (for the new visited states) : NbPassingTime, ProbaPassingTime and pricemovePeriod
            for j in IndexNextStates :
                ExecState = StatesIndex[j][3] 
                if (ExecState==0): # Check whether the order is executed or not
                    QBefI= StatesIndex[j][0]
                    QAftI= StatesIndex[j][1]
                    QSameI = QBefI+QAftI
                    QOppI= StatesIndex[j][2]
                    lambdaPlusOpp= self.IntensFunc(qsame, qopp,'OppPlus') # intensité insertion Ask
                    lambdaMoinsOpp= self.IntensFunc(qsame, qopp,'OppMoins') # intensité annulation Ask
                    lambdaPlusSame= self.IntensFunc(qsame, qopp,'SamePlus')  # intensité insertion Bid
                    lambdaMoinsSame= self.IntensFunc(qsame, qopp,'SameMoins') # intensité annulation Bid
                    [q1,q2,q3,q4,q5]=BasicFunctions.ProbTrans(lambdaPlusSame,lambdaMoinsSame,lambdaPlusOpp,lambdaMoinsOpp,self.TimeStep)
                    ProbState=fsGraphSons[j][2][-2]
                    NbPassingTimePeriodBefore = fsGraphSons[j][1][-2]
                    priceMovePeriodAuxi = 0 # When price moves at next period for state j
                    # The initial State can have 5 son States
                    # First Case : 1 unit quantity is added to QOpp (Under control c)
                    InitialStateMain = BasicFunctions.CreateElmt1(QBefI,QAftI,(QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
                    IdState=BasicFunctions.IdStates(InitialStateMain)
                    IsOldState = (IdState in IdStatesIndex)
                    if IsOldState :
                        SonIndex=StatesIndex.index(InitialStateMain)
                        fsGraphSons[j][0].append(SonIndex)
                        fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                        fsGraphSons[SonIndex][2][-1]+=ProbState*q1
                    if not (IsOldState) :
                        CountStates+=1
                        StatesIndex.append(InitialStateMain)
                        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                        fsGraphSons[j][0].append(CountStates)
                        fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q1])
                        IndexNextStates2[count]=CountStates
                        count+=1
    
                    # Second Case : 1 unit quantity is cancelled from QOpp (Under control c)
                    # The price isn't modified in this Sub-Case
                    if (QOppI >= 2*self.UnitQuant):
                        InitialStateMain = BasicFunctions.CreateElmt1(QBefI,QAftI,(QOppI-self.UnitQuant),ExecI=0,ChangePrice=0)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState :
                            SonIndex=StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q2
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q2])
                            IndexNextStates2[count]=CountStates
                            count+=1
                    # The price is modified in this Sub-Case
                    if (QOppI < 2*self.UnitQuant):
                        [qdisc,qins] = self.DiscQtyFunc(QOppI,QSameI) 
                        InitialStateMain = BasicFunctions.CreateElmt1(qins,0,qdisc,ExecI=0,ChangePrice=1)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        priceMovePeriodAuxi += self.PriceJump*ProbState*q2
                        if IsOldState :
                            SonIndex=StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q2
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q2])
                            IndexNextStates2[count]=CountStates
                            count+=1
    
                    # Third Case : 1 unit quantity is added to QSame (Under Control c)
                    InitialStateMain = BasicFunctions.CreateElmt1(QBefI,(QAftI+self.UnitQuant),QOppI,ExecI=0,ChangePrice=0) 
                    IdState=BasicFunctions.IdStates(InitialStateMain)
                    IsOldState = (IdState in IdStatesIndex)
                    if IsOldState : 
                        SonIndex = StatesIndex.index(InitialStateMain)
                        fsGraphSons[j][0].append(SonIndex)
                        fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                        fsGraphSons[SonIndex][2][-1]+=ProbState*q3
                    if not (IsOldState) :
                        CountStates+=1
                        StatesIndex.append(InitialStateMain)
                        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                        fsGraphSons[j][0].append(CountStates)
                        fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q3])
                        IndexNextStates2[count]=CountStates
                        count+=1
    
                    # Fourth Case : 1 unit quantity is cancelled from QSame (Under control c)
                    # In this Sub-Case the price doesn't change
                    if (QBefI >= 2*self.UnitQuant):
                        InitialStateMain = BasicFunctions.CreateElmt1((QBefI-self.UnitQuant),QAftI,QOppI,ExecI=0,ChangePrice=0) 
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState : 
                            SonIndex = StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q4 
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q4])
                            IndexNextStates2[count]=CountStates
                            count+=1
    
                    # In this Sub-Case the order is executed but the price doesn't change 
                    if ((QBefI < 2*self.UnitQuant) and (QAftI + QBefI >= 2*self.UnitQuant)):
                        InitialStateMain = BasicFunctions.CreateElmt1((QBefI + QAftI - self.UnitQuant),0,QOppI,ExecI=1,ChangePrice=0)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState : 
                            SonIndex = StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q4
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q4])
                            IndexNextStates2[count]=CountStates
                            count+=1
                    # Under control "c" : In this sub case the order is executed and the price changes    
                    if (QBefI+QAftI < 2*self.UnitQuant) :
                        [qdisc,qins] = self.DiscQtyFunc(QSameI,QOppI)
                        InitialStateMain = BasicFunctions.CreateElmt1(qdisc,0,qins,ExecI=1,ChangePrice=-1)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        priceMovePeriodAuxi -= self.PriceJump*ProbState*q4
                        if IsOldState : 
                            SonIndex=StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q4
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q4])
                            IndexNextStates2[count]=CountStates
                            count+=1
    
                    # Fifth case : Nothing happens
                    # Under control c 
                    fsGraphSons[j][0].append(j)
    
                    if (QBefI >= 2*self.UnitQuant):
                        sumProbUnExec += ProbState*(q1+q2+q3+q4) 
                    if (QBefI < 2*self.UnitQuant):
                        sumProbExec += ProbState*q4
                        sumProbUnExec += ProbState*(q1+q2+q3)
                    priceMovePeriod += priceMovePeriodAuxi
   
            ProbPeriod[(i+2),0]=sumProbUnExec # unexecuted states
            ProbPeriod[(i+2),1]=sumProbExec # executed states
            MeanPriceMove[i+2]=priceMovePeriod
            IndexNextStates = IndexNextStates2[:count]
    
        return({"Element":StatesIndex,"Graph":fsGraphSons,"Separation":separation,"ProbPeriod":ProbPeriod,"MeanPriceMove":MeanPriceMove})

    def backwardsimulationOpti(self,graph):
        ##Initialization :
        bsGraph = graph["Graph"] ## Sons of all visited states
        StatesIndex = graph["Element"] ## All visited states
        separation=  graph["Separation"] ## Index of the newest states at each period
        NbStates = len(StatesIndex)
        UtilityAfter = np.ndarray((NbStates,), dtype=float, order='F')
        OptimalStrategy = np.ndarray((NbStates,), dtype=np.dtype((str,2*(self.nbIter+1))), order='F')
        for i in range(NbStates):
            DeltaT = self.nbIter*self.TimeStep
            qsame = (StatesIndex[i][0]+StatesIndex[i][1]) ; qopp = StatesIndex[i][2] ; Exec = StatesIndex[i][3] ; changePrice = StatesIndex[i][4] ; [qdisc,qins] = self.DiscQtyFunc(qopp,qsame) 
            UtilityAfter[i] = self.FinalConstraint(qsame,qopp,self.P0,Exec,qdisc,qins,changePrice,DeltaT)
            OptimalStrategy[i] = "1"
        UtilityBefore=copy.copy(UtilityAfter)
        
        # General Backward Routine
        for i in range(self.nbIter):
            sep = separation[self.nbIter-(i+1)]
            UtilityAfter = copy.copy(UtilityBefore)
            for j in range(sep):
                ExecState = StatesIndex[j][3]
                # When Order not executed
                if (ExecState==0) :
                    qsame = (StatesIndex[j][0]+StatesIndex[j][1]) 
                    qopp = StatesIndex[j][2] 
                    lambdaPlusOpp= self.IntensFunc(qsame, qopp,'OppPlus') # intensité insertion Ask
                    lambdaMoinsOpp= self.IntensFunc(qsame, qopp,'OppMoins') # intensité annulation Ask
                    lambdaPlusSame= self.IntensFunc(qsame, qopp,'SamePlus')  # intensité insertion Bid
                    lambdaMoinsSame= self.IntensFunc(qsame, qopp,'SameMoins') # intensité annulation Bid
                    [q1,q2,q3,q4,q5]=BasicFunctions.ProbTrans(lambdaPlusSame,lambdaMoinsSame,lambdaPlusOpp,lambdaMoinsOpp,self.TimeStep)
                
                    # control 'c'
                    u1 = q5*UtilityAfter[bsGraph[j][0][4]]+q4*UtilityAfter[bsGraph[j][0][3]]+q3*UtilityAfter[bsGraph[j][0][2]]+q2*UtilityAfter[bsGraph[j][0][1]]+q1*UtilityAfter[bsGraph[j][0][0]]    
                    UtilityBefore[j]=u1
                    ctrl='0'
                    if (len(OptimalStrategy[j])<=(i+1)):
                        OptimalStrategy[j] = ctrl + OptimalStrategy[j]
                # When order Executed
                if (ExecState==1) :
                    DeltaT= (self.nbIter-(i+1))*self.TimeStep
                    qsame = (StatesIndex[j][0]+StatesIndex[j][1]) ; qopp = StatesIndex[j][2] ; Exec = StatesIndex[j][3] ; changePrice = StatesIndex[j][4] ; [qdisc,qins] = self.DiscQtyFunc(qopp,qsame) 
                    UtilityBefore[j] = self.FinalConstraint(qsame,qopp,self.P0,Exec,qdisc,qins,changePrice,DeltaT)
                    OptimalStrategy[j] = "1"

        UtilityAfter = pd.DataFrame(UtilityAfter)
        UtilityBefore = pd.DataFrame(UtilityBefore)
        OptimalStrategy = pd.DataFrame(OptimalStrategy)
        Results=pd.concat([UtilityBefore,UtilityAfter,OptimalStrategy],axis=1)
        Results.columns = ["UtilityBefore","UtilityAfter","OptiStrategy"]
        return({"Element":StatesIndex,"Graph":bsGraph,"Results":Results})