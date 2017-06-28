# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 14:35:42 2017

@author: Otm
"""

## Import libraries
import sys
pathLib = 'D:\\etude\\charles-albert\\travail_rendu2\\FinalVersionsOptiBouclage\\CtrlOptiF\\CtrlOpti\\AlgoOptiSimuTheoTerminal_Revision5\\CtrlOptiLimitOrder\\ctrlopti' # Use the right path
sys.path.insert(0,pathLib)
import numpy as np
import pandas as pd
import copy
import BasicFunctions
import math

## Optimisation :
class CtrlOptiSimu (object): 

    
    def __init__(self,QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinalConstraint,UnitQuant): 
        """Define attributes"""
        self.QAftI = QAftI #  initial  quantity after the unit order
        self.QBefI = QBefI # initial quantity before the unit order
        self.QOppI = QOppI # initial quantity in the opposite side (i.e Ask side)
        self.P0 = P0 # initial mid price
        self.TimeStep = TimeStep # trading frequency
        self.nbIter = nbIter # number of trading periods
        self.IntensFunc = IntensFunc # function computing intensities
        self.DiscQtyFunc = DiscQtyFunc # function computing discovered/inserted quantities
        self.FinalConstraint = FinalConstraint # function computing the terminal constraint
        self.UnitQuant = UnitQuant # quantity added or canceled at each orderbook event
        
    # Forward simulation : simulate all reachable states
    def forwardsimulationOpti(self):
        #Initialization
        StatesIndex=list() # each element is reached state s.t: [QBefI,QAftI,QOppI,Exec,ChangePrice], Exec =1 when order executed and 0 otherwise
        IdStatesIndex=set() # set with a code 'QBefI,QAftI,QOppI,Exec,ChangePrice' to identify each state 
        fsGraphSons = dict() # contains sons of each reached state.
        IndexNextStates=list() # Next period reached states
        separation = [0]*(self.nbIter) # index of last reached state at each period
        CountStates=0 # Count states
    
        # Create First State
        InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,self.QAftI,self.QOppI,ExecI=0,ChangePrice=0)
        StatesIndex.append(InitialStateMain)
        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
        fsGraphSons[CountStates]=list()
        separation[0]=1
    
        # The initial state have 5 son states
        # First Case : 1 unit quantity is added to QOpp (Under control c)
        CountStateSon = CountStates+1
        InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,self.QAftI,(self.QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
        StatesIndex.append(InitialStateMain)
        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
        fsGraphSons[CountStates].append(CountStateSon)
        fsGraphSons[CountStateSon]=list()
        IndexNextStates.append(CountStateSon)
    
        # First Case : 1 unit quantity is added to QOpp (Under control s)
        InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI),0,(self.QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
        IdState=BasicFunctions.IdStates(InitialStateMain)
        IsOldState = (IdState in IdStatesIndex)
        if IsOldState :
            SonIndex=StatesIndex.index(InitialStateMain)
            fsGraphSons[CountStates].append(SonIndex)
        if not (IsOldState) :
            CountStateSon +=1
            StatesIndex.append(InitialStateMain)
            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
            fsGraphSons[CountStates].append(CountStateSon)
            fsGraphSons[CountStateSon]=list()
            IndexNextStates.append(CountStateSon)
    
        # Second Case : 1 unit quantity is cancelled from QOpp (Under control c)
        # The price isn't modified in this Sub-Case
        if (self.QOppI >= 2*self.UnitQuant):
            CountStateSon +=1
            InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,self.QAftI,(self.QOppI-self.UnitQuant),ExecI=0,ChangePrice=0)
            StatesIndex.append(InitialStateMain)
            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
            fsGraphSons[CountStates].append(CountStateSon)
            fsGraphSons[CountStateSon]=list()
            IndexNextStates.append(CountStateSon)
        # The price is modified in this Sub-Case
        if (self.QOppI < 2*self.UnitQuant):
            qsame = self.QBefI+self.QAftI
            qopp = self.QOppI
            [qdisc,qins] = self.DiscQtyFunc(qopp,qsame) 
            InitialStateMain = BasicFunctions.CreateElmt1(qins,0,qdisc,ExecI=0,ChangePrice=1)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex=StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates].append(SonIndex)
            if not (IsOldState) :
                CountStateSon +=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates].append(CountStateSon)
                fsGraphSons[CountStateSon]=list()
                IndexNextStates.append(CountStateSon)
    
        # Second Case : 1 unit quantity is cancelled from QOpp (Under control s)
        # The price isn't modified in this Sub-Case
        if (self.QOppI >= 2*self.UnitQuant):
            InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI),0,(self.QOppI-self.UnitQuant),ExecI=0,ChangePrice=0)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex=StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates].append(SonIndex)
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates].append(CountStateSon)
                fsGraphSons[CountStateSon]=list()
                IndexNextStates.append(CountStateSon)
    
        # The price is modified in this Sub-Case
        if (self.QOppI < 2*self.UnitQuant):
            qsame = self.QBefI+self.QAftI
            qopp = self.QOppI
            [qdisc,qins] = self.DiscQtyFunc(qopp,qsame) 
            InitialStateMain = BasicFunctions.CreateElmt1(qins,0,qdisc,ExecI=0,ChangePrice=1)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex = StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates].append(SonIndex)
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates].append(CountStateSon)
                fsGraphSons[CountStateSon]=list()
                IndexNextStates.append(CountStateSon)
    
        # Third Case : 1 unit quantity is added to QSame (Under Control c)
        InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,(self.QAftI+self.UnitQuant),self.QOppI,ExecI=0,ChangePrice=0)
        IdState=BasicFunctions.IdStates(InitialStateMain)
        IsOldState = (IdState in IdStatesIndex)
        if IsOldState :
            SonIndex = StatesIndex.index(InitialStateMain)
            fsGraphSons[CountStates].append(SonIndex)
        if not (IsOldState) :
            CountStateSon+=1
            StatesIndex.append(InitialStateMain)
            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
            fsGraphSons[CountStates].append(CountStateSon)
            fsGraphSons[CountStateSon]=list()
            IndexNextStates.append(CountStateSon)
    
        # Third Case: 1 unit quantity is added to QSame (Under Control s)
        InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI+self.UnitQuant),0,self.QOppI,ExecI=0,ChangePrice=0)
        IdState=BasicFunctions.IdStates(InitialStateMain)
        IsOldState = (IdState in IdStatesIndex)
        if IsOldState :
            SonIndex=StatesIndex.index(InitialStateMain)
            fsGraphSons[CountStates].append(SonIndex)
        if not (IsOldState) :
            CountStateSon+=1
            StatesIndex.append(InitialStateMain)
            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
            fsGraphSons[CountStates].append(CountStateSon)
            fsGraphSons[CountStateSon]=list()
            IndexNextStates.append(CountStateSon)
    
        # Fourth Case : 1 unit quantity is cancelled from QSame (Under control c)
        # In this Sub-Case the price doesn't change
        if (self.QBefI>= 2*self.UnitQuant):
            InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI-self.UnitQuant),self.QAftI,self.QOppI,ExecI=0,ChangePrice=0)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex = StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates].append(SonIndex)
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates].append(CountStateSon)
                fsGraphSons[CountStateSon]=list()
                IndexNextStates.append(CountStateSon)
        # In this Sub-Case the order is executed but the price doesn't change 
        if ((self.QBefI < 2*self.UnitQuant)and(self.QAftI + self.QBefI >= 2*self.UnitQuant)):
            InitialStateMain = BasicFunctions.CreateElmt1((self.QAftI + self.QBefI -self.UnitQuant),0,self.QOppI,ExecI=1,ChangePrice=0)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex = StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates].append(SonIndex)
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates].append(CountStateSon)
                fsGraphSons[CountStateSon]=list()
                IndexNextStates.append(CountStateSon)
        # Under control "c" : In this sub case the order is executed and the price changes
        if (self.QBefI+self.QAftI < 2*self.UnitQuant) :
            qsame = self.QBefI+self.QAftI
            qopp = self.QOppI
            [qdisc,qins] = self.DiscQtyFunc(qsame,qopp)             
            InitialStateMain = BasicFunctions.CreateElmt1(qdisc,0,qins,ExecI=1,ChangePrice=-1)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex=StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates].append(SonIndex)
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates].append(CountStateSon)
                fsGraphSons[CountStateSon]=list()
                IndexNextStates.append(CountStateSon)
    
        # Fourth Case : 1 unit quantity is cancelled from QSame (Under control s)
        # In this Sub-Case the price doesn't change
        if ((self.QBefI+self.QAftI >= 2*self.UnitQuant)):
            InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI-self.UnitQuant),0,self.QOppI,ExecI=0,ChangePrice=0)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex = StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates].append(SonIndex)
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates].append(CountStateSon)
                fsGraphSons[CountStateSon]=list()
                IndexNextStates.append(CountStateSon)
        if (self.QBefI+self.QAftI < 2*self.UnitQuant):
        # Under control "s" : In this sub case the order isn't executed and the price change 
            qsame = self.QBefI+self.QAftI
            qopp = self.QOppI
            [qdisc,qins] = self.DiscQtyFunc(qsame,qopp)  
            InitialStateMain = BasicFunctions.CreateElmt1(qdisc,0,qins,ExecI=0,ChangePrice=-1)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex = StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates].append(SonIndex)
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates].append(CountStateSon)
                fsGraphSons[CountStateSon]=list()
                IndexNextStates.append(CountStateSon)
    
        # Fifth case : Nothing happens under control c
        fsGraphSons[CountStates].append(CountStates)
    
        # Fifth case : Nothing happens under control s
        InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI),0,self.QOppI,ExecI=0,ChangePrice=0)
        IdState=BasicFunctions.IdStates(InitialStateMain)
        IsOldState = (IdState in IdStatesIndex)
        if IsOldState :
            SonIndex = StatesIndex.index(InitialStateMain)
            fsGraphSons[CountStates].append(SonIndex)
        if not (IsOldState) :
            CountStateSon+=1
            StatesIndex.append(InitialStateMain)
            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
            fsGraphSons[CountStates].append(CountStateSon)
            fsGraphSons[CountStateSon]=list()
            IndexNextStates.append(CountStateSon)
        CountStates+=CountStateSon
    
        ## Main routine
        for i in range(self.nbIter-1):
            separation[i+1]=(CountStates+1)
            sizeP = len(IndexNextStates)
            IndexNextStates2=[0]*(9*sizeP) # Temporary variable with future next period states
            count=0
            for j in IndexNextStates :
                ExecState = StatesIndex[j][3] 
                if (ExecState==0): # Check whether the order is executed or not
                    QBefI= StatesIndex[j][0]
                    QAftI= StatesIndex[j][1]
                    QOppI= StatesIndex[j][2]
                    # The initial State can have 5 son States
                    # First Case : 1 unit quantity is added to QOpp (Under control c)
                    InitialStateMain = BasicFunctions.CreateElmt1(QBefI,QAftI,(QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
                    IdState=BasicFunctions.IdStates(InitialStateMain)
                    IsOldState = (IdState in IdStatesIndex)
                    if IsOldState :
                        SonIndex=StatesIndex.index(InitialStateMain)
                        fsGraphSons[j].append(SonIndex)
                    if not (IsOldState) :
                        CountStates+=1
                        StatesIndex.append(InitialStateMain)
                        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                        fsGraphSons[j].append(CountStates)
                        fsGraphSons[CountStates]=list()
                        IndexNextStates2[count]=CountStates
                        count+=1
                    # First Case : 1 unit quantity is added to QOpp (Under control s)
                    InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI),0,(QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
                    IdState=BasicFunctions.IdStates(InitialStateMain)
                    IsOldState = (IdState in IdStatesIndex)
                    if IsOldState :
                        SonIndex=StatesIndex.index(InitialStateMain)
                        fsGraphSons[j].append(SonIndex)
                    if not (IsOldState) :
                        CountStates+=1
                        StatesIndex.append(InitialStateMain)
                        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                        fsGraphSons[j].append(CountStates)
                        fsGraphSons[CountStates]=list()
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
                            fsGraphSons[j].append(SonIndex)
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j].append(CountStates)
                            fsGraphSons[CountStates]=list()
                            IndexNextStates2[count]=CountStates
                            count+=1
                    # The price is modified in this Sub-Case
                    if (QOppI < 2*self.UnitQuant):
                        qsame = QBefI+QAftI
                        qopp = QOppI
                        [qdisc,qins] = self.DiscQtyFunc(qopp,qsame) 
                        InitialStateMain = BasicFunctions.CreateElmt1(qins,0,qdisc,ExecI=0,ChangePrice=1)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState :
                            SonIndex=StatesIndex.index(InitialStateMain)
                            fsGraphSons[j].append(SonIndex)
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j].append(CountStates)
                            fsGraphSons[CountStates]=list()
                            IndexNextStates2[count]=CountStates
                            count+=1
    
                    # Second Case : 1 unit quantity is cancelled from QOpp (Under control s)
                    # The price isn't modified in this Sub-Case      
                    if (QOppI >= 2*self.UnitQuant):
                        InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI),0,(QOppI-self.UnitQuant),ExecI=0,ChangePrice=0) 
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState :
                            SonIndex=StatesIndex.index(InitialStateMain)
                            fsGraphSons[j].append(SonIndex)
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j].append(CountStates)
                            fsGraphSons[CountStates]=list()
                            IndexNextStates2[count]=CountStates
                            count+=1
    
                    # The price is modified in this Sub-Case
                    if (QOppI < 2*self.UnitQuant):
                        qsame = QBefI+QAftI
                        qopp = QOppI
                        [qdisc,qins] = self.DiscQtyFunc(qopp,qsame) 
                        InitialStateMain = BasicFunctions.CreateElmt1(qins,0,qdisc,ExecI=0,ChangePrice=1)  
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState : 
                            SonIndex = StatesIndex.index(InitialStateMain)
                            fsGraphSons[j].append(SonIndex)
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j].append(CountStates)
                            fsGraphSons[CountStates]=list()
                            IndexNextStates2[count]=CountStates
                            count+=1
    
                    # Third Case : 1 unit quantity is added to QSame (Under Control c)
                    InitialStateMain = BasicFunctions.CreateElmt1(QBefI,(QAftI+self.UnitQuant),QOppI,ExecI=0,ChangePrice=0) 
                    IdState=BasicFunctions.IdStates(InitialStateMain)
                    IsOldState = (IdState in IdStatesIndex)
                    if IsOldState : 
                        SonIndex = StatesIndex.index(InitialStateMain)
                        fsGraphSons[j].append(SonIndex)
                    if not (IsOldState) :
                        CountStates+=1
                        StatesIndex.append(InitialStateMain)
                        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                        fsGraphSons[j].append(CountStates)
                        fsGraphSons[CountStates]=list()
                        IndexNextStates2[count]=CountStates
                        count+=1
    
                    # Third Case: 1 unit quantity is added to QSame (Under Control s)
                    InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI+self.UnitQuant),0,QOppI,ExecI=0,ChangePrice=0) 
                    IdState=BasicFunctions.IdStates(InitialStateMain)
                    IsOldState = (IdState in IdStatesIndex)
                    if IsOldState : 
                        SonIndex=StatesIndex.index(InitialStateMain)
                        fsGraphSons[j].append(SonIndex)
                    if not (IsOldState) :
                        CountStates+=1
                        StatesIndex.append(InitialStateMain)
                        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                        fsGraphSons[j].append(CountStates)
                        fsGraphSons[CountStates]=list()
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
                            fsGraphSons[j].append(SonIndex)
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j].append(CountStates)
                            fsGraphSons[CountStates]=list()
                            IndexNextStates2[count]=CountStates
                            count+=1
    
                    # In this Sub-Case the order is executed but the price doesn't change 
                    if ((QBefI < 2*self.UnitQuant) and (QAftI + QBefI >= 2*self.UnitQuant)):
                        InitialStateMain = BasicFunctions.CreateElmt1((QBefI + QAftI - self.UnitQuant),0,QOppI,ExecI=1,ChangePrice=0)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState : 
                            SonIndex = StatesIndex.index(InitialStateMain)
                            fsGraphSons[j].append(SonIndex)
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j].append(CountStates)
                            fsGraphSons[CountStates]=list()
                            IndexNextStates2[count]=CountStates
                            count+=1
                    # Under control "c" : In this sub case the order is executed and the price changes    
                    if (QBefI+QAftI < 2*self.UnitQuant) :
                        qsame = QBefI+QAftI
                        qopp = QOppI
                        [qdisc,qins] = self.DiscQtyFunc(qsame,qopp) 
                        InitialStateMain = BasicFunctions.CreateElmt1(qdisc,0,qins,ExecI=1,ChangePrice=-1)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState : 
                            SonIndex=StatesIndex.index(InitialStateMain)
                            fsGraphSons[j].append(SonIndex)
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j].append(CountStates)
                            fsGraphSons[CountStates]=list()
                            IndexNextStates2[count]=CountStates
                            count+=1
    
                    # Fourth Case : 1 unit quantity is cancelled from QSame (Under control s)
                    # In this Sub-Case the price doesn't change
                    if (QBefI+QAftI>=2*self.UnitQuant):
                        InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI-self.UnitQuant),0,QOppI,ExecI=0,ChangePrice=0)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState : 
                            SonIndex = StatesIndex.index(InitialStateMain)
                            fsGraphSons[j].append(SonIndex)
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j].append(CountStates)
                            fsGraphSons[CountStates]=list()
                            IndexNextStates2[count]=CountStates
                            count+=1
                    # Under control "s" : In this sub case the order isn't executed and the price change 
                    if (QBefI+QAftI<2*self.UnitQuant):
                        qsame = QBefI+QAftI
                        qopp = QOppI
                        [qdisc,qins] = self.DiscQtyFunc(qsame,qopp) 
                        InitialStateMain = BasicFunctions.CreateElmt1(qdisc,0,qins,ExecI=0,ChangePrice=-1)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState : 
                            SonIndex = StatesIndex.index(InitialStateMain)
                            fsGraphSons[j].append(SonIndex)
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j].append(CountStates)
                            fsGraphSons[CountStates]=list()
                            IndexNextStates2[count]=CountStates
                            count+=1
    
                    # Fifth case : Nothing happens
                    # Under control c and s (it's almost the same thing)
                    fsGraphSons[j].append(j)
    
                    InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI),0,QOppI,ExecI=0,ChangePrice=0)
                    IdState=BasicFunctions.IdStates(InitialStateMain)
                    IsOldState = (IdState in IdStatesIndex)
                    if IsOldState :
                        SonIndex = StatesIndex.index(InitialStateMain)
                        fsGraphSons[j].append(SonIndex)
                    if not (IsOldState) :
                        CountStates+=1
                        StatesIndex.append(InitialStateMain)
                        IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                        fsGraphSons[j].append(CountStates)
                        fsGraphSons[CountStates]=list()
                        IndexNextStates2[count]=CountStates
                        count+=1
            IndexNextStates = IndexNextStates2[:count]
    
        return({"Element":StatesIndex,"Graph":fsGraphSons,"Separation":separation})

    # Backward simulation : compute initial utility
    def backwardsimulationOpti(self,graph):
        ##Initialization :
        bsGraph = graph["Graph"]
        StatesIndex = graph["Element"]
        separation=  graph["Separation"]
        size = len(StatesIndex)
        UtilityAfter = np.ndarray((size,), dtype=float, order='F')
        OptimalStrategy = np.ndarray((size,), dtype=np.dtype((str,2*(self.nbIter+1))), order='F')
        for i in range(size):
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
                    # Probabilities of transition
                    qsame = (StatesIndex[j][0]+StatesIndex[j][1]) 
                    qopp = StatesIndex[j][2] 
                    lambdaPlusOpp= self.IntensFunc(qsame, qopp,'OppPlus') # intensité insertion Ask
                    lambdaMoinsOpp= self.IntensFunc(qsame, qopp,'OppMoins') # intensité annulation Ask
                    lambdaPlusSame= self.IntensFunc(qsame, qopp,'SamePlus')  # intensité insertion Bid
                    lambdaMoinsSame= self.IntensFunc(qsame, qopp,'SameMoins') # intensité annulation Bid
                    [q1,q2,q3,q4,q5]=BasicFunctions.ProbTrans(lambdaPlusSame,lambdaMoinsSame,lambdaPlusOpp,lambdaMoinsOpp,self.TimeStep)
                
                    # control 'c'
                    u1 = q5*UtilityAfter[bsGraph[j][8]]+q4*UtilityAfter[bsGraph[j][6]]+q3*UtilityAfter[bsGraph[j][4]]+q2*UtilityAfter[bsGraph[j][2]]+q1*UtilityAfter[bsGraph[j][0]]
                    # control 's'
                    u2 = q5*UtilityAfter[bsGraph[j][9]]+q4*UtilityAfter[bsGraph[j][7]]+q3*UtilityAfter[bsGraph[j][5]]+q2*UtilityAfter[bsGraph[j][3]]+q1*UtilityAfter[bsGraph[j][1]]
    
                    UtilityBefore[j]=max(u1,u2)
                    ctrl='0' if (u1>=u2) else '1'
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

    # Backward simulation : compute initial utility with latency            
    def backwardsimulationLatencyOpti(self,graph,LatencyFactor):
        ##Initialization :
        MaxIter = math.ceil(self.nbIter/LatencyFactor)
        bsGraph = graph["Graph"]
        StatesIndex = graph["Element"]
        separation=  graph["Separation"]
        size = len(StatesIndex)
        UtilityAfter = np.ndarray((size,), dtype=float, order='F')
        OptimalStrategy = np.ndarray((size,), dtype=np.dtype((str,2*(self.nbIter+1))), order='F')
        for i in range(size):
            DeltaT = self.nbIter*self.TimeStep
            qsame = (StatesIndex[i][0]+StatesIndex[i][1]) ; qopp = StatesIndex[i][2] ; Exec = StatesIndex[i][3] ; changePrice = StatesIndex[i][4] ; [qdisc,qins] = self.DiscQtyFunc(qopp,qsame) 
            UtilityAfter[i] = self.FinalConstraint(qsame,qopp,self.P0,Exec,qdisc,qins,changePrice,DeltaT)
            OptimalStrategy[i] = "1"
        UtilityBefore=copy.copy(UtilityAfter)
    
        # General Backward Routine
        for i in range(MaxIter):
            sep = separation[int(LatencyFactor*(MaxIter-i-1))]
            UtilityAfter = copy.copy(UtilityBefore)
            for j in range(sep):
                ExecState = StatesIndex[j][3]
                # When Order not executed
                if (ExecState==0) :
                    # Probabilities of transition
                    ProbFatherState = {j:1}
                    FatherState = {j}
                    # control 'c'
                    ctrl = 0
                    u1 = BasicFunctions.ComputeLatencyUtility(ProbFatherState,FatherState,ctrl,UtilityAfter,bsGraph,StatesIndex,LatencyFactor,self.IntensFunc,self.TimeStep)
                    # control 's'
                    ctrl = 1
                    u2 = BasicFunctions.ComputeLatencyUtility(ProbFatherState,FatherState,ctrl,UtilityAfter,bsGraph,StatesIndex,LatencyFactor,self.IntensFunc,self.TimeStep)    
                    UtilityBefore[j]=max(u1,u2)
                    ctrl='0' if (u1>=u2) else '1'
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

    # Compute the mean imbalance of the sons of each visited state
    def TestMeanImbalance(self,graph):
        """ graph = corresponds to the ouput of the forward simulation """
        if not (graph) :
            print("Error : graph is empty")
        if (graph):
            bsGraph = graph["Graph"]
            StatesIndex = graph["Element"]
            Separation = graph["Separation"]
            LastElmt = Separation[-1]
            res = pd.DataFrame(np.ones((LastElmt,3)),columns = ["Period","InitialImbalance","MeanImbalance"])
            period = 0
            FirstElmtPeriod = 0
            for sep in Separation :
                for ElmtIndex in range(FirstElmtPeriod,sep):
                    ## Probabilities transition
                    QSame = StatesIndex[ElmtIndex][0] + StatesIndex[ElmtIndex][1]
                    Qopp = StatesIndex[ElmtIndex][2]
                    lambdaPlusOpp= self.IntensFunc(QSame, Qopp,'OppPlus') # intensité insertion Ask
                    lambdaMoinsOpp= self.IntensFunc(QSame, Qopp,'OppMoins') # intensité annulation Ask
                    lambdaPlusSame= self.IntensFunc(QSame, Qopp,'SamePlus')  # intensité insertion Bid
                    lambdaMoinsSame= self.IntensFunc(QSame, Qopp,'SameMoins') # intensité annulation Bid
                    ProbaTransI=BasicFunctions.ProbTrans(lambdaPlusSame,lambdaMoinsSame,lambdaPlusOpp,lambdaMoinsOpp,self.TimeStep)
                    res["Period"][ElmtIndex] = period
                    res["InitialImbalance"][ElmtIndex] = BasicFunctions.ImbalanceI(QSame,Qopp)
                    Sons = bsGraph[ElmtIndex]
                    res["MeanImbalance"][ElmtIndex] = BasicFunctions.ImbalanceS(Sons,StatesIndex,ProbaTransI)
                period += 1
                FirstElmtPeriod = sep 
            
            return(res)
      
    # compute metrics associated to a given strategy 
    def OptiStratMetrics(self,OptiStrat,StatesIndexI,PriceJump): 
        #Initialization
        StatesIndex=list() 
        IdStatesIndex=set()
        fsGraphSons = dict()
        IndexNextStates=set()
        separation = [0]*(self.nbIter) 
        ProbPeriod= np.zeros((self.nbIter+1,2)) # sum of proba for unexecuted states (first column) and already executed states (second column) during each period. Check that sum of proba equal to 1 (no loss of information)
        MeanPriceMove = [0]*(self.nbIter+2) # Mean price move at each period
        OptiGain = 0 # utility of the strategy
        AverageStratDuration = 0 # Average strategy duration
        NbStayCancel = np.zeros((self.nbIter,2)) # stay decisions (first column) and cancel decisions (second column) at each period
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
        ProbPeriod[0,0]=1 ## initialisation : the initial state is fixed and has proba 1
        CtrlState = int(OptiStrat[0][0])
        if CtrlState == 0 :
            NbStayCancel[0,0] +=1
        if CtrlState == 1 :
            NbStayCancel[0,1] +=1
        CountStateSon = CountStates
        priceMovePeriod = 0
        # Initial control is c
        if (CtrlState == 0) :
            # The initial State can have 5 son States
            # First Case : 1 unit quantity is added to QOpp (Under control c)
            CountStateSon += 1
            InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,self.QAftI,(self.QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
            StatesIndex.append(InitialStateMain)
            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
            fsGraphSons[CountStates][0].append(CountStateSon)
            fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q1])
            IndexNextStates.add(CountStateSon)
        
            # Second Case : 1 unit quantity is cancelled from QOpp (Under control c)
            # The price isn't modified in this Sub-Case
            if (self.QOppI >= 2*self.UnitQuant):
                CountStateSon +=1
                InitialStateMain = BasicFunctions.CreateElmt1(self.QBefI,self.QAftI,(self.QOppI-self.UnitQuant),ExecI=0,ChangePrice=0)
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates][0].append(CountStateSon)
                fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q2])
                IndexNextStates.add(CountStateSon)
            # The price is modified in this Sub-Case
            if (self.QOppI < 2*self.UnitQuant):
                priceMovePeriod += PriceJump*q2
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
                    IndexNextStates.add(CountStateSon)
        
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
                IndexNextStates.add(CountStateSon)
        
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
                    IndexNextStates.append(SonIndex)
                if not (IsOldState) :
                    CountStateSon+=1
                    StatesIndex.append(InitialStateMain)
                    IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                    fsGraphSons[CountStates][0].append(CountStateSon)
                    fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q4])
                    IndexNextStates.add(CountStateSon)
            # In this Sub-Case the order is executed but the price doesn't change 
            if ((self.QBefI < 2*self.UnitQuant)and(self.QAftI + self.QBefI >= 2*self.UnitQuant)):
                DeltaT = self.TimeStep
                ChangePrice=0
                ExecI=1
                [qdisc,qins] = self.DiscQtyFunc(qsame,qopp) 
                OptiGain += q4*self.FinalConstraint(qsame,qopp,self.P0,ExecI,qdisc,qins,ChangePrice,DeltaT)
                AverageStratDuration += q4*DeltaT
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
                    IndexNextStates.add(CountStateSon)
            # Under control "c" : In this sub case the order is executed and the price changes
            if (self.QBefI+self.QAftI < 2*self.UnitQuant) :
                DeltaT = self.TimeStep
                ChangePrice=-1
                ExecI=1
                [qdisc,qins] = self.DiscQtyFunc(qsame,qopp) 
                OptiGain += q4*self.FinalConstraint(qsame,qopp,self.P0,ExecI,qdisc,qins,ChangePrice,DeltaT)
                AverageStratDuration += q4*DeltaT
                priceMovePeriod -= PriceJump*q4
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
                    IndexNextStates.add(CountStateSon)
    
        
            # Fifth case : Nothing happens under control c
            fsGraphSons[CountStates][0].append(CountStates)
            fsGraphSons[CountStates][1].append(1)
            fsGraphSons[CountStates][2].append(q5)
            IndexNextStates.add(CountStates)
            
            if (self.QBefI >= 2*self.UnitQuant): 
                ProbPeriod[1,0]=(q1+q2+q3+q4+q5) # unexecuted states proba
            if (self.QBefI < 2*self.UnitQuant):
                ProbPeriod[1,0]=(q1+q2+q3+q5) # unexecuted states proba
                ProbPeriod[1,1]=q4 # executed states proba
        # Initial control is s
        if (CtrlState == 1) :
            # First Case : 1 unit quantity is added to QOpp (Under control s)
            InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI),0,(self.QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex=StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates][0].append(SonIndex)
                fsGraphSons[SonIndex][1][0] += 1
                fsGraphSons[SonIndex][2][0] += q1
            if not (IsOldState) :
                CountStateSon +=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates][0].append(CountStateSon)
                fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q1])
                IndexNextStates.add(CountStateSon)
                
            # Second Case : 1 unit quantity is cancelled from QOpp (Under control s)
            # The price isn't modified in this Sub-Case
            if (self.QOppI >= 2*self.UnitQuant):
                InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI),0,(self.QOppI-self.UnitQuant),ExecI=0,ChangePrice=0)
                IdState=BasicFunctions.IdStates(InitialStateMain)
                IsOldState = (IdState in IdStatesIndex)
                if IsOldState :
                    SonIndex=StatesIndex.index(InitialStateMain)
                    fsGraphSons[CountStates][0].append(SonIndex)
                    fsGraphSons[SonIndex][1][0] += 1
                    fsGraphSons[SonIndex][2][0] += q2
                if not (IsOldState) :
                    CountStateSon+=1
                    StatesIndex.append(InitialStateMain)
                    IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                    fsGraphSons[CountStates][0].append(CountStateSon)
                    fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q2])
                    IndexNextStates.add(CountStateSon)
        
            # The price is modified in this Sub-Case
            if (self.QOppI < 2*self.UnitQuant):
                priceMovePeriod += PriceJump*q2
                [qdisc,qins] = self.DiscQtyFunc(qopp,qsame)
                InitialStateMain = BasicFunctions.CreateElmt1(qins,0,qdisc,ExecI=0,ChangePrice=1)
                IdState=BasicFunctions.IdStates(InitialStateMain)
                IsOldState = (IdState in IdStatesIndex)
                if IsOldState :
                    SonIndex = StatesIndex.index(InitialStateMain)
                    fsGraphSons[CountStates][0].append(SonIndex)
                    fsGraphSons[SonIndex][1][0] += 1
                    fsGraphSons[SonIndex][2][0] += q2
                if not (IsOldState) :
                    CountStateSon+=1
                    StatesIndex.append(InitialStateMain)
                    IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                    fsGraphSons[CountStates][0].append(CountStateSon)
                    fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q2])
                    IndexNextStates.add(CountStateSon)
                    
            # Third Case: 1 unit quantity is added to QSame (Under Control s)
            InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI+self.UnitQuant),0,self.QOppI,ExecI=0,ChangePrice=0)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex=StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates][0].append(SonIndex)
                fsGraphSons[SonIndex][1][0] += 1
                fsGraphSons[SonIndex][2][0] += q3
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates][0].append(CountStateSon)
                fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q3])
                IndexNextStates.add(CountStateSon) 
                
            # Fourth Case : 1 unit quantity is cancelled from QSame (Under control s)
            # In this Sub-Case the price doesn't change
            if ((self.QBefI+self.QAftI >= 2*self.UnitQuant)):
                InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI-self.UnitQuant),0,self.QOppI,ExecI=0,ChangePrice=0)
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
                    IndexNextStates.add(CountStateSon)
            if (self.QBefI+self.QAftI < 2*self.UnitQuant):
            # Under control "s" : In this sub case the order isn't executed and the price change 
                priceMovePeriod -= PriceJump*q4
                [qdisc,qins] = self.DiscQtyFunc(qsame,qopp)
                InitialStateMain = BasicFunctions.CreateElmt1(qdisc,0,qins,ExecI=0,ChangePrice=-1)
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
                    IndexNextStates.add(CountStateSon) 
                    
            # Fifth case : Nothing happens under control s
            InitialStateMain = BasicFunctions.CreateElmt1((self.QBefI+self.QAftI),0,self.QOppI,ExecI=0,ChangePrice=0)
            IdState=BasicFunctions.IdStates(InitialStateMain)
            IsOldState = (IdState in IdStatesIndex)
            if IsOldState :
                SonIndex = StatesIndex.index(InitialStateMain)
                fsGraphSons[CountStates][0].append(SonIndex)
                fsGraphSons[SonIndex][1][0] += 1
                fsGraphSons[SonIndex][2][0] += q5
            if not (IsOldState) :
                CountStateSon+=1
                StatesIndex.append(InitialStateMain)
                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                fsGraphSons[CountStates][0].append(CountStateSon)
                fsGraphSons[CountStateSon]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[q5])
                IndexNextStates.add(CountStateSon)
         
            # All states are unexecuted
            ProbPeriod[1,0]=(q1+q2+q3+q4+q5)
        CountStates+=CountStateSon
        MeanPriceMove[1]=priceMovePeriod
    
        ## Main routine Before the final time period Tmax
        for i in range(self.nbIter-1):
            separation[i+1]=(CountStates+1)
            IndexNextStates2=set()
            sumProbExec=0 # sum executed states proba
            sumProbUnExec=0 # sum unexecuted states proba
            priceMovePeriod=0 
            StayTime=0 # Nb stay time decisions
            CancelTime=0 # Nb cancel time decisions

            ## step 1 : Instantiate new values : NbPassingTime and ProbaPassingTime
            for j in range(CountStates+1):
                fsGraphSons[j][1].append(0) # instantiate new NbPassingTime
                fsGraphSons[j][2].append(0) # instantiate new ProbaPassingTime
                            
            ## Step 2 : update variables (for  new visited states) : NbPassingTime, ProbaPassingTime, pricemovePeriod, sumProbExec, sumProbUnExec, StayTime, CancelTime
            for j in IndexNextStates :
                ExecState = StatesIndex[j][3] 
                if (ExecState == 0): # Check whether the order is executed or not
                    QBefI= StatesIndex[j][0]
                    QAftI= StatesIndex[j][1]
                    qsame = QBefI+QAftI
                    QOppI= StatesIndex[j][2]
                    ProbState=fsGraphSons[j][2][-2]
                    NbPassingTimePeriodBefore = fsGraphSons[j][1][-2]
                    priceMovePeriodAuxi = 0 # When price moves at next period for state j
                    jBis = StatesIndexI.index(StatesIndex[j])
                    FirstPeriod = (self.nbIter + 1) - len(OptiStrat[jBis])
                    CtrlState =  int(OptiStrat[jBis][(i+1) - FirstPeriod])
                    # Initial control is c
                    if (CtrlState == 0) :
                        StayTime += ProbState*NbPassingTimePeriodBefore
                        # The initial State can have 5 son States
                        # First Case : 1 unit quantity is added to QOpp (Under control c)
                        InitialStateMain = BasicFunctions.CreateElmt1(QBefI,QAftI,(QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
                        IdState = BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState :
                            SonIndex=StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q1
                            IsOldNextState = (SonIndex in IndexNextStates2)
                            if not IsOldNextState:
                                    IndexNextStates2.add(SonIndex)                           
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q1])
                            IndexNextStates2.add(CountStates)
        
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
                                IsOldNextState = (SonIndex in IndexNextStates2)
                                if not IsOldNextState:
                                        IndexNextStates2.add(SonIndex)  
                            if not (IsOldState) :
                                CountStates+=1
                                StatesIndex.append(InitialStateMain)
                                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                                fsGraphSons[j][0].append(CountStates)
                                fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q2])
                                IndexNextStates2.add(CountStates)

                        # The price is modified in this Sub-Case
                        if (QOppI < 2*self.UnitQuant):
                            priceMovePeriodAuxi += PriceJump*ProbState*q2
                            [qdisc,qins] = self.DiscQtyFunc(QOppI,qsame) 
                            InitialStateMain = BasicFunctions.CreateElmt1(qins,0,qdisc,ExecI=0,ChangePrice=1)
                            IdState=BasicFunctions.IdStates(InitialStateMain)
                            IsOldState = (IdState in IdStatesIndex)
                            if IsOldState :
                                SonIndex=StatesIndex.index(InitialStateMain)
                                fsGraphSons[j][0].append(SonIndex)
                                fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                                fsGraphSons[SonIndex][2][-1]+=ProbState*q2
                                IsOldNextState = (SonIndex in IndexNextStates2)
                                if not IsOldNextState:
                                        IndexNextStates2.add(SonIndex)  
                            if not (IsOldState) :
                                CountStates+=1
                                StatesIndex.append(InitialStateMain)
                                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                                fsGraphSons[j][0].append(CountStates)
                                fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q2])
                                IndexNextStates2.add(CountStates)
        
                        # Third Case : 1 unit quantity is added to QSame (Under Control c)
                        InitialStateMain = BasicFunctions.CreateElmt1(QBefI,(QAftI+self.UnitQuant),QOppI,ExecI=0,ChangePrice=0) 
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState : 
                            SonIndex = StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q3
                            IsOldNextState = (SonIndex in IndexNextStates2)
                            if not IsOldNextState:
                                    IndexNextStates2.add(SonIndex)  
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q3])
                            IndexNextStates2.add(CountStates)
        
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
                                IsOldNextState = (SonIndex in IndexNextStates2)
                                if not IsOldNextState:
                                        IndexNextStates2.add(SonIndex) 
                            if not (IsOldState) :
                                CountStates+=1
                                StatesIndex.append(InitialStateMain)
                                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                                fsGraphSons[j][0].append(CountStates)
                                fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q4])
                                IndexNextStates2.add(CountStates)

                        # In this Sub-Case the order is executed but the price doesn't change 
                        if ((QBefI < 2*self.UnitQuant) and (QAftI + QBefI >= 2*self.UnitQuant)):
                            DeltaT = (2+i)*self.TimeStep
                            ChangePrice=0
                            ExecI=1  
                            [qdisc,qins] = self.DiscQtyFunc(qsame,QOppI) 
                            OptiGain += ProbState*q4*self.FinalConstraint(qsame,QOppI,self.P0,ExecI,qdisc,qins,ChangePrice,DeltaT)
                            AverageStratDuration += ProbState*q4*DeltaT
                            InitialStateMain = BasicFunctions.CreateElmt1((QBefI + QAftI - self.UnitQuant),0,QOppI,ExecI,ChangePrice)
                            IdState=BasicFunctions.IdStates(InitialStateMain)
                            IsOldState = (IdState in IdStatesIndex)
                            if IsOldState : 
                                SonIndex = StatesIndex.index(InitialStateMain)
                                fsGraphSons[j][0].append(SonIndex)
                                fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                                fsGraphSons[SonIndex][2][-1]+=ProbState*q4
                                IsOldNextState = (SonIndex in IndexNextStates2)
                                if not IsOldNextState:
                                        IndexNextStates2.add(SonIndex) 
                            if not (IsOldState) :
                                CountStates+=1
                                StatesIndex.append(InitialStateMain)
                                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                                fsGraphSons[j][0].append(CountStates)
                                fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q4])
                                IndexNextStates2.add(CountStates)

                        # Under control "c" : In this sub case the order is executed and the price changes    
                        if (QBefI+QAftI < 2*self.UnitQuant) :
                            DeltaT = (2+i)*self.TimeStep
                            ChangePrice=-1
                            ExecI=1
                            [qdisc,qins] = self.DiscQtyFunc(qsame,QOppI) 
                            OptiGain += ProbState*q4*self.FinalConstraint(qsame,QOppI,self.P0,ExecI,qdisc,qins,ChangePrice,DeltaT)
                            AverageStratDuration += ProbState*q4*DeltaT
                            priceMovePeriodAuxi -= PriceJump*ProbState*q4
                            InitialStateMain = BasicFunctions.CreateElmt1(qdisc,0,qins,ExecI,ChangePrice)
                            IdState=BasicFunctions.IdStates(InitialStateMain)
                            IsOldState = (IdState in IdStatesIndex)
                            if IsOldState : 
                                SonIndex=StatesIndex.index(InitialStateMain)
                                fsGraphSons[j][0].append(SonIndex)
                                fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                                fsGraphSons[SonIndex][2][-1]+=ProbState*q4
                                IsOldNextState = (SonIndex in IndexNextStates2)
                                if not IsOldNextState:
                                        IndexNextStates2.add(SonIndex)                                
                            if not (IsOldState) :
                                CountStates+=1
                                StatesIndex.append(InitialStateMain)
                                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                                fsGraphSons[j][0].append(CountStates)
                                fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q4])
                                IndexNextStates2.add(CountStates)
        
                        # Fifth case : Nothing happens
                        # Under control c 
                        fsGraphSons[j][0].append(j)
                        fsGraphSons[j][1][-1]+=NbPassingTimePeriodBefore
                        fsGraphSons[j][2][-1]+=ProbState*q5

                    # Initial control is s
                    if (CtrlState == 1):
                        CancelTime += ProbState*NbPassingTimePeriodBefore
                        # First Case : 1 unit quantity is added to QOpp (Under control s)
                        InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI),0,(QOppI+self.UnitQuant),ExecI=0,ChangePrice=0)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState :
                            SonIndex=StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore 
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q1
                            IsOldNextState = (SonIndex in IndexNextStates2)
                            if not IsOldNextState:
                                IndexNextStates2.add(SonIndex) 
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q1])
                            IndexNextStates2.add(CountStates)
                        
                        # Second Case : 1 unit quantity is cancelled from QOpp (Under control s)
                        # The price isn't modified in this Sub-Case      
                        if (QOppI >= 2*self.UnitQuant):
                            InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI),0,(QOppI-self.UnitQuant),ExecI=0,ChangePrice=0) 
                            IdState=BasicFunctions.IdStates(InitialStateMain)
                            IsOldState = (IdState in IdStatesIndex)
                            if IsOldState :
                                SonIndex=StatesIndex.index(InitialStateMain)
                                fsGraphSons[j][0].append(SonIndex)
                                fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                                fsGraphSons[SonIndex][2][-1]+=ProbState*q2
                                IsOldNextState = (SonIndex in IndexNextStates2)
                                if not IsOldNextState:
                                        IndexNextStates2.add(SonIndex) 
                            if not (IsOldState) :
                                CountStates+=1
                                StatesIndex.append(InitialStateMain)
                                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                                fsGraphSons[j][0].append(CountStates)
                                fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q2])
                                IndexNextStates2.add(CountStates)
        
                        # The price is modified in this Sub-Case
                        if (QOppI < 2*self.UnitQuant):
                            priceMovePeriodAuxi += PriceJump*ProbState*q2
                            [qdisc,qins] = self.DiscQtyFunc(QOppI,qsame)
                            InitialStateMain = BasicFunctions.CreateElmt1(qins,0,qdisc,ExecI=0,ChangePrice=1)  
                            IdState=BasicFunctions.IdStates(InitialStateMain)
                            IsOldState = (IdState in IdStatesIndex)
                            if IsOldState : 
                                SonIndex = StatesIndex.index(InitialStateMain)
                                fsGraphSons[j][0].append(SonIndex)
                                fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                                fsGraphSons[SonIndex][2][-1]+=ProbState*q2
                                IsOldNextState = (SonIndex in IndexNextStates2)
                                if not IsOldNextState:
                                        IndexNextStates2.add(SonIndex) 
                            if not (IsOldState) :
                                CountStates+=1
                                StatesIndex.append(InitialStateMain)
                                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                                fsGraphSons[j][0].append(CountStates)
                                fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q2])
                                IndexNextStates2.add(CountStates)
                        
                        # Third Case: 1 unit quantity is added to QSame (Under Control s)
                        InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI+self.UnitQuant),0,QOppI,ExecI=0,ChangePrice=0) 
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState : 
                            SonIndex=StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q3
                            IsOldNextState = (SonIndex in IndexNextStates2)
                            if not IsOldNextState:
                                IndexNextStates2.add(SonIndex) 
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[1],ProbState=[ProbState*q3])
                            IndexNextStates2.add(CountStates) 
                            
                        # Fourth Case : 1 unit quantity is cancelled from QSame (Under control s)
                        # In this Sub-Case the price doesn't change
                        if (QBefI+QAftI>=2*self.UnitQuant):
                            InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI-self.UnitQuant),0,QOppI,ExecI=0,ChangePrice=0)
                            IdState=BasicFunctions.IdStates(InitialStateMain)
                            IsOldState = (IdState in IdStatesIndex)
                            if IsOldState : 
                                SonIndex = StatesIndex.index(InitialStateMain)
                                fsGraphSons[j][0].append(SonIndex)
                                fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                                fsGraphSons[SonIndex][2][-1]+=ProbState*q4
                                IsOldNextState = (SonIndex in IndexNextStates2)
                                if not IsOldNextState:
                                        IndexNextStates2.add(SonIndex) 
                            if not (IsOldState) :
                                CountStates+=1
                                StatesIndex.append(InitialStateMain)
                                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                                fsGraphSons[j][0].append(CountStates)
                                fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q4])
                                IndexNextStates2.add(CountStates)

                        if (QBefI+QAftI<2*self.UnitQuant):
                        # Under control "s" : In this sub case the order isn't executed and the price change 
                            priceMovePeriodAuxi -= PriceJump*ProbState*q4
                            [qdisc,qins] = self.DiscQtyFunc(qsame,QOppI)
                            InitialStateMain = BasicFunctions.CreateElmt1(qdisc,0,qins,ExecI=0,ChangePrice=-1)
                            IdState=BasicFunctions.IdStates(InitialStateMain)
                            IsOldState = (IdState in IdStatesIndex)
                            if IsOldState : 
                                SonIndex = StatesIndex.index(InitialStateMain)
                                fsGraphSons[j][0].append(SonIndex)
                                fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                                fsGraphSons[SonIndex][2][-1]+=ProbState*q4
                                IsOldNextState = (SonIndex in IndexNextStates2)
                                if not IsOldNextState:
                                        IndexNextStates2.add(SonIndex) 
                            if not (IsOldState) :
                                CountStates+=1
                                StatesIndex.append(InitialStateMain)
                                IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                                fsGraphSons[j][0].append(CountStates)
                                fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q4])
                                IndexNextStates2.add(CountStates) 
                            
                        # Under control s (it's almost the same thing)
                        InitialStateMain = BasicFunctions.CreateElmt1((QBefI+QAftI),0,QOppI,ExecI=0,ChangePrice=0)
                        IdState=BasicFunctions.IdStates(InitialStateMain)
                        IsOldState = (IdState in IdStatesIndex)
                        if IsOldState :
                            SonIndex = StatesIndex.index(InitialStateMain)
                            fsGraphSons[j][0].append(SonIndex)
                            fsGraphSons[SonIndex][1][-1]+=NbPassingTimePeriodBefore
                            fsGraphSons[SonIndex][2][-1]+=ProbState*q5
                            IsOldNextState = (SonIndex in IndexNextStates2)
                            if not IsOldNextState:
                                    IndexNextStates2.add(SonIndex) 
                        if not (IsOldState) :
                            CountStates+=1
                            StatesIndex.append(InitialStateMain)
                            IdStatesIndex.add(BasicFunctions.IdStates(InitialStateMain))
                            fsGraphSons[j][0].append(CountStates)
                            fsGraphSons[CountStates]=BasicFunctions.CreateGraphElmt(Sons=list(),NbPassingTime=[NbPassingTimePeriodBefore],ProbState=[ProbState*q5])
                            IndexNextStates2.add(CountStates)
                            
                    if (QBefI >= 2*self.UnitQuant):
                        sumProbUnExec += ProbState*(q1+q2+q3+q4) 
                    if (QBefI < 2*self.UnitQuant):
                        sumProbExec += ProbState*q4
                        sumProbUnExec += ProbState*(q1+q2+q3)
                    priceMovePeriod += priceMovePeriodAuxi
   
            ProbPeriod[(i+2),0]=sumProbUnExec # we consider both controls
            ProbPeriod[(i+2),1]=sumProbExec # we consider both controls
            MeanPriceMove[i+2]=priceMovePeriod
            NbStayCancel[i+1,0]=StayTime # stay time
            NbStayCancel[i+1,1]=CancelTime # cancel time
            IndexNextStates = IndexNextStates2
        
        ## Final time period Tmax  constraint      
        priceMovePeriod = 0
        for i in IndexNextStates:
                ExecState = StatesIndex[i][3]
                if (ExecState == 0):
                    DeltaT = self.nbIter*self.TimeStep ; ProbState = fsGraphSons[i][2][-1] ; qsame = StatesIndex[i][0]+StatesIndex[i][1] ; qopp = StatesIndex[i][2] ; ExecI = 0 ; [qdisc,qins] = self.DiscQtyFunc(qopp,qsame) ; ChangePrice = StatesIndex[i][4]
                    OptiGain += ProbState*self.FinalConstraint(qsame,qopp,self.P0,ExecI,qdisc,qins,ChangePrice,DeltaT) 
                    AverageStratDuration += ProbState*DeltaT  
                    if (qopp<2*self.UnitQuant) : 
                        priceMovePeriod += ProbState*PriceJump
        MeanPriceMove[self.nbIter+1] = priceMovePeriod                 
        return({"Element":StatesIndex,"Graph":fsGraphSons,"Separation":separation,"ProbPeriod":ProbPeriod,"MeanPriceMove":MeanPriceMove,"OptiGain":OptiGain,"AverageStratDuration":AverageStratDuration,"NbStayCancel":NbStayCancel,"IndexNextStates":IndexNextStates})