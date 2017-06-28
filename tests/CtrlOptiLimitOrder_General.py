# -*- coding: utf-8 -*-
"""
Created on Sat Jun 24 15:14:13 2017

@author: Otm
"""

# import libraries 
import sys
pathLib = 'D:\\etude\\charles-albert\\travail_rendu2\\FinalVersionsOptiBouclage\\CtrlOptiF\\CtrlOpti\\AlgoOptiSimuTheoTerminal_Revision5\\CtrlOptiLimitOrder' # Use the right path
sys.path.insert(0,pathLib)
import ctrlopti.AlgOptiSimu as AlgOptiSimu
import numpy as np
import pandas as pd
import math

#from pylab import *

# pour avoir des beaux dessins LaTeX
import matplotlib.pyplot as plt
import matplotlib as mpl
label_size = 18
mpl.rcParams['xtick.labelsize'] = label_size 
mpl.rcParams['ytick.labelsize'] = label_size 
mpl.rcParams.update({"text.usetex": True,                # use LaTeX to write all text
    "font.family": "serif",
    "font.serif": [],                   # blank entries should cause plots to inherit fonts from the document
    "font.sans-serif": [],
    "font.monospace": [],
    "pgf.preamble": [
        r"\usepackage[utf8x]{inputenc}",    # use utf8 fonts becasue your computer can handle it :)
        r"\usepackage[T1]{fontenc}",        # plots will be generated using this preamble
        ] })
## Testing code :
## testing optimized method 


#####################################################################################################################
#####################################################################################################################
############################################## Auxiliary Functions ##################################################
#####################################################################################################################
#####################################################################################################################

## Plot data
def plotData(x,y,xlabel='',ylabel='',title='',loc='best',fontsize=10,ax=None,**kwargs):        
    if ax is None:
        plt.subplot(1,1,1)
    else:
        plt.axes(ax)
    
    plt.scatter(x,y,color="r",label= "",alpha=0.8,s=60)
    plt.plot(x,y,color='r', **kwargs)
    plt.title(title,fontsize=fontsize,weight='bold')
    plt.xlabel(xlabel,weight='bold')
    plt.ylabel(ylabel,weight='bold')
    plt.legend(loc=loc)
    plt.grid()
    
# The following function computes a constant discovered and inserted quantities
def DiscQtyFunc0(Qopp,Qsame,qdisc0,qins0):
    qdisc = qdisc0
    qins = qins0
    return [qdisc,qins]
# The following function computes discovered and inserted quantities that depends on the imbalance   
def DiscQtyFunc1(q0,q01,Qopp,Qsame,tau1=1,tau2=1,q1=0,Q=0,theta1=3,theta2=0.5,option=1):
    if (option == 1) :
        qdisc = q0 + tau1*math.ceil((Qopp)/((Qsame+q1)+ Qopp))
        qins = q01 + tau2* qdisc
        
    if (option == 2):
        qdisc = Q*theta1
        qins = Q*theta2
    return [qdisc,qins]
# The following function computes constant intensities
def IntensFunc0 (qbid,qask,option='SamePlus',lambdaInser=0.0606,lambdaCancel=0.103):
    if option == 'SamePlus' :
        res = lambdaInser
    if option == 'SameMoins' :
        res = lambdaCancel
    if option == 'OppPlus' :
        res = lambdaInser
    if option == 'OppMoins' :
        res = lambdaCancel
    return res
    
# The following function computes intensities that depends on the imbalance    
def IntensFunc1 (qbid,qask,option='SamePlus',alpha=5,alpha2=5,lambdaInser=0.0606,lambdaCancel=0.103):
    if option == 'SamePlus' :
        res = lambdaInser+alpha*qbid/(qbid+qask)
    if option == 'SameMoins' :
        res = lambdaCancel+alpha2*qask/(qbid+qask)
    if option == 'OppPlus' :
        res = lambdaInser+alpha*qask/(qbid+qask)
    if option == 'OppMoins' :
        res = lambdaCancel+alpha2*qbid/(qbid+qask)
    return res
    
def MicroPrice(QSame,QOpp,Price,tau):
    """The microprice"""
    return Price -tau*(QOpp-QSame)/(2.*(QOpp+QSame))

# The following function computes the final constraint
def FinalConstraint(QSame,QOpp,Price,Exec,quantiteDisc,quantiteIns,tau,ChangePrice=1,unitQuant=1,spread=1,delta=1):
    if (((Exec == 1.0) or (Exec <= -1.0)) and (ChangePrice == 0)):
        return (MicroPrice(QSame,QOpp,Price,tau) - (Price - (spread*0.5))) 
    if (((Exec == 1.0) or (Exec <= -1.0)) and (ChangePrice != 0)):# a reformuler
        return (MicroPrice(QSame,QOpp,Price,tau) - (Price + (spread*0.5)))
    if (Exec == 0) :
        return (MicroPrice(QSame,QOpp-unitQuant,Price,tau) - (Price + (spread*0.5))) if (QOpp>=2*unitQuant) else (MicroPrice(
            quantiteIns,quantiteDisc,Price+delta,tau) - (Price + (spread*0.5)))

# The following function computes the final constraint with the associated waiting cost
def FinalConstraintWaitCost(QSame,QOpp,Price,Exec,quantiteDisc,quantiteIns,tau,ChangePrice=1,unitQuant=1,spread=1,delta=1,DeltaT=0,WaitCost=0):
    return float(FinalConstraint(QSame,QOpp,Price,Exec,quantiteDisc,quantiteIns,tau,ChangePrice,unitQuant,spread,delta) - WaitCost*DeltaT*unitQuant)

##################################################################################################
############################## Testing the Algorithm #############################################
##################################################################################################

## Paramters Initialization :
QAftI=2# Q after initial
QBefI=0 # Q before initial
QOppI=2# Q opposite initial
K = QBefI 
P0=10 # Initial price
TimeStep=1 # the discretization timestep
nbIter=10# number of simulated periods
## constant intensities parameters
quantiteDisc = 6
quantiteIns = 4
lambdaInser = 0.0606
lambdaCancel = 0.5
## variable intensities parameters
alpha = 0.075
alpha2 = 0.25
q0 = 6
q01 =2
q1 = 0
tau1=1
tau2=0
q1=0
Q=0
theta1=3
theta2=0.5
option=1
## Final constraint parameters : 
unitQuant=1
spread=1
delta=1
WaitCost=0
tau = 4
PriceJump = 1 # Price Jump when price moves



## testing algorithm

############################################################################
######################### 1 ################################################
############################################################################

## Try the algorithm :
### 1.1 
print('1.1')
print('Case 1: cste intensities')
IntensFunc = lambda qbid,qask,option: IntensFunc0(qbid,qask,option,lambdaInser,lambdaCancel)
DiscQtyFunc = lambda qopp,qsame:DiscQtyFunc0(qopp,qsame,quantiteDisc,quantiteIns)
FinConstraint = lambda qsame,qopp,P0,Exec,qdisc,qins,changePrice,DeltaT:FinalConstraintWaitCost(qsame,qopp,P0,Exec,qdisc,qins,tau,changePrice,unitQuant,spread,delta,DeltaT,WaitCost)

OptiSimu = AlgOptiSimu.CtrlOptiSimu(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant)
fwdgraph=OptiSimu.forwardsimulationOpti()
bsGraph=OptiSimu.backwardsimulationOpti(fwdgraph) 


## Quick results :
bsgraph = bsGraph["Graph"] ## Sons of all the visited states with no repetition
StatesIndex = bsGraph["Element"] ## All visited states
Results=  bsGraph["Results"] ## Utility in the first and second period and optimal strategies

## Results presentation
sizeStates = len(StatesIndex)
Res1 = pd.DataFrame(np.zeros((sizeStates,7)),columns=["QBef","QAft","QOpp","Exec","UtilityBefore","UtilityAfter","OptiStrat"])
for i  in range(sizeStates):
    Res1.iloc[i,:4] = StatesIndex[i][:4]
    Res1.iloc[i,4] = Results["UtilityBefore"][i]
    Res1.iloc[i,5] = Results["UtilityAfter"][i]
    Res1.iloc[i,6] = Results["OptiStrategy"][i]

print(Res1.head(11))

### 1.2 
print('1.2')
print('Case 2: imbalance dependent intensities')
IntensFunc = lambda qbid,qask,option: IntensFunc1(qbid,qask,option,alpha)
DiscQtyFunc = lambda qopp,qsame:DiscQtyFunc1(q0,q01,qsame,qopp,tau1,tau2,q1,Q,theta1,theta2,option)

OptiSimu = AlgOptiSimu.CtrlOptiSimu(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant)
fwdgraph=OptiSimu.forwardsimulationOpti()
bsGraph=OptiSimu.backwardsimulationOpti(fwdgraph) 


## Quick results :
bsgraph = bsGraph["Graph"] ## Sons of all the visited states with no repetition
StatesIndex = bsGraph["Element"] ## All visited states
Results=  bsGraph["Results"] ## Utility in the first and second period and optimal strategies

## Results presentation
sizeStates = len(StatesIndex)
Res1 = pd.DataFrame(np.zeros((sizeStates,7)),columns=["QBef","QAft","QOpp","Exec","UtilityBefore","UtilityAfter","OptiStrat"])
for i  in range(sizeStates):
    Res1.iloc[i,:4] = StatesIndex[i][:4]
    Res1.iloc[i,4] = Results["UtilityBefore"][i]
    Res1.iloc[i,5] = Results["UtilityAfter"][i]
    Res1.iloc[i,6] = Results["OptiStrategy"][i]

print(Res1.head(11))


## Imbalance Verification :

############################################################################
######################### 2 ################################################
############################################################################

print('2')
IntensFunc = lambda qbid,qask,option: IntensFunc0(qbid,qask,option,lambdaInser,lambdaCancel)
DiscQtyFunc = lambda qopp,qsame:DiscQtyFunc0(qopp,qsame,quantiteDisc,quantiteIns)

OptiSimu = AlgOptiSimu.CtrlOptiSimu(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant)
fwdgraph=OptiSimu.forwardsimulationOpti()
df_verif = OptiSimu.TestMeanImbalance(fwdgraph)
print('Imbalance verification')
print(df_verif.head())


## Compute the mean execution time 

############################################################################
######################### 3 ################################################
############################################################################

print('3')
print('mean execution time ')
OptiSimu = AlgOptiSimu.CtrlOptiSimu(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant)
fwdgraph=OptiSimu.forwardsimulationOpti()
bsGraph=OptiSimu.backwardsimulationOpti(fwdgraph) 
OptiStrat = bsGraph["Results"]["OptiStrategy"]
StatesIndex = fwdgraph["Element"]
PriceJump=1
Res = OptiSimu.OptiStratMetrics(OptiStrat,StatesIndex,PriceJump)
print('Average strategy duration')
print(Res["AverageStratDuration"])
print('Mean price move')
print(sum(Res["MeanPriceMove"]))
print('Strategy utility')
print(Res["OptiGain"])

## Number of stay/cancel time decisions

############################################################################
######################### 5 ################################################
############################################################################

print('5')
nbStay=sum(Res["NbStayCancel"][:,0])
print('nb stay')
print(nbStay)
print('nb cancel')
nbCancel=sum(Res["NbStayCancel"][:,1])
print(nbCancel)



