# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 13:16:09 2017

@author: Otm
"""


##########################################################################################################################
################################################ Influence of Latency ############################################
##########################################################################################################################


# import libraries 
import sys
pathLib = 'D:\\etude\\charles-albert\\travail_rendu2\\FinalVersionsOptiBouclage\\CtrlOptiF\\CtrlOpti\\AlgoOptiSimuTheoTerminal_Revision5\\CtrlOptiPackage' # Use the right path
sys.path.insert(0,pathLib)
import ctrlopti.AlgOptiSimu as AlgOptiSimu
import numpy as np
import pandas as pd
import math

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


##########################################################################################################################
####################################################The influence of some parameters  ####################################
##########################################################################################################################

def ComputeLatency(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,LatencyFactor0,LatencyFactormax):

    res4=np.zeros((LatencyFactormax-1,4))

    ctrlOptiSimGlob0 = AlgOptiSimu.CtrlOptiSimu(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant)
    fwdgraph=ctrlOptiSimGlob0.forwardsimulationOpti()
    bsGraph=ctrlOptiSimGlob0.backwardsimulationOpti(fwdgraph) 
    utilityRef0=bsGraph["Results"]['UtilityBefore'][0]
    
    for i in range(2,(LatencyFactormax+1)):
        # backward simulation 
        bsGraph = ctrlOptiSimGlob0.backwardsimulationLatencyOpti(fwdgraph,i)
        utility1=bsGraph["Results"]['UtilityBefore'][0]
        res4[(i-2),0]=i
        res4[(i-2),1]=utilityRef0-utility1
        res4[(i-2),2]=utilityRef0
        res4[(i-2),3]=utility1
    
    res4 = pd.DataFrame(res4,columns=['Latency','LatencyCost','utilityRef0','utility1'])
    return res4
 
## Plot data
def plotData(x,y,xlabel='',ylabel='',title='',loc='best',col="r",fontsize=10,ax=None,**kwargs):        
    if ax is None:
        plt.subplot(1,1,1)
    else:
        plt.axes(ax)
    
    plt.scatter(x,y,color=col,label= "",alpha=0.8,s=60)
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

    

##########################################################################################################################
########################################## Test #############################################
##########################################################################################################################


## Paramters Initialization :
QAftI=3# Q after initial
QBefI=0 # Q before initial
QOppI=1# Q opposite initial
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
q01 =4
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

LatencyFactor0=0
LatencyFactormax = 5 

## Try the algorithm :
### 1.1 
print('1.1')
print('Case 1: cste intensities')
IntensFunc = lambda qbid,qask,option: IntensFunc0(qbid,qask,option,lambdaInser,lambdaCancel)
DiscQtyFunc = lambda qopp,qsame:DiscQtyFunc0(qopp,qsame,quantiteDisc,quantiteIns)
FinConstraint = lambda qsame,qopp,P0,Exec,qdisc,qins,changePrice,DeltaT:FinalConstraintWaitCost(qsame,qopp,P0,Exec,qdisc,qins,tau,changePrice,unitQuant,spread,delta,DeltaT,WaitCost)

ResLatency = ComputeLatency(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,LatencyFactor0,LatencyFactormax)
print(ResLatency)


fig = plt.figure(figsize=(8,6))
ax1 = plt.subplot(1,1,1) 
xlabel=r'Latency' 
ylabel=r'Latency cost'
title=r' a) Latency cost VS Latency'
loc='best' ## Legend location
col='red'
fontsize = 10
plotData(ResLatency.iloc[:,0],ResLatency.iloc[:,1],xlabel,ylabel,title,loc,col,fontsize,ax=ax1, lw=4,alpha=.7)   

tau = 2
FinConstraint = lambda qsame,qopp,P0,Exec,qdisc,qins,changePrice,DeltaT:FinalConstraintWaitCost(qsame,qopp,P0,Exec,qdisc,qins,tau,changePrice,unitQuant,spread,delta,DeltaT,WaitCost)
ResLatency1 = ComputeLatency(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,LatencyFactor0,LatencyFactormax)
print(ResLatency1)
tau = 5 
FinConstraint = lambda qsame,qopp,P0,Exec,qdisc,qins,changePrice,DeltaT:FinalConstraintWaitCost(qsame,qopp,P0,Exec,qdisc,qins,tau,changePrice,unitQuant,spread,delta,DeltaT,WaitCost)
ResLatency2 = ComputeLatency(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,LatencyFactor0,LatencyFactormax)
print(ResLatency2)
tau = 10 
FinConstraint = lambda qsame,qopp,P0,Exec,qdisc,qins,changePrice,DeltaT:FinalConstraintWaitCost(qsame,qopp,P0,Exec,qdisc,qins,tau,changePrice,unitQuant,spread,delta,DeltaT,WaitCost)
ResLatency3 = ComputeLatency(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,LatencyFactor0,LatencyFactormax)
print(ResLatency3)


x = ResLatency1.iloc[:,0]
y = ResLatency1.iloc[:,1]
x1 = ResLatency2.iloc[:,0] 
y1 = ResLatency2.iloc[:,1]
x2 = ResLatency3.iloc[:,0]
y2 = ResLatency3.iloc[:,1]
xlabel=r'Latency' 
ylabel=r'Latency cost'
title=r' a) Latency cost VS Latency'
loc='best' ## Legend location
col='red'
fig = plt.figure(figsize=(8,6))
plt.subplot(1,1,1)
plt.scatter(x,y,color='g',label= "",alpha=0.8,s=60)
plt.plot(x,y,color='g',label=r"$\alpha =2$",lw=4,alpha=.7)
plt.scatter(x1,y1,color='b',label= "",alpha=0.8,s=60)
plt.plot(x1,y1,color='b',label=r"$\alpha =5$",lw=4,alpha=.7)
plt.scatter(x2,y2,color='r',label= "",alpha=0.8,s=60)
plt.plot(x2,y2,color='r',label=r"$\alpha =10$",lw=4,alpha=.7)
plt.title(title,fontsize=fontsize,weight='bold')
plt.xlabel(xlabel,weight='bold')
plt.ylabel(ylabel,weight='bold')
plt.legend(loc=loc)
plt.grid()

 
### 1.2 
print('1.2')
print('Latency estimate : imbalance dependent intensities new version')
IntensFunc = lambda qbid,qask,option: IntensFunc1(qbid,qask,option,alpha,alpha2,lambdaInser,lambdaCancel)
DiscQtyFunc = lambda qopp,qsame:DiscQtyFunc1(q0,q01,qsame,qopp,tau1,tau2,q1,Q,theta1,theta2,option)

ResLatency = ComputeLatency(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,LatencyFactor0,LatencyFactormax)
print(ResLatency)

fig = plt.figure(figsize=(8,6))
ax1 = plt.subplot(1,1,1) 
xlabel=r'Latency' 
ylabel=r'Latency cost'
title=r' a) Latency cost VS Latency'
loc='best' ## Legend location
col='red'
plotData(ResLatency.iloc[:,0],ResLatency.iloc[:,1],xlabel,ylabel,title,loc,col,ax=ax1, lw=4,alpha=.7)   


tau = 2
FinConstraint = lambda qsame,qopp,P0,Exec,qdisc,qins,changePrice,DeltaT:FinalConstraintWaitCost(qsame,qopp,P0,Exec,qdisc,qins,tau,changePrice,unitQuant,spread,delta,DeltaT,WaitCost)
ResLatency1 = ComputeLatency(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,LatencyFactor0,LatencyFactormax)
print(ResLatency1)
tau = 5 
FinConstraint = lambda qsame,qopp,P0,Exec,qdisc,qins,changePrice,DeltaT:FinalConstraintWaitCost(qsame,qopp,P0,Exec,qdisc,qins,tau,changePrice,unitQuant,spread,delta,DeltaT,WaitCost)
ResLatency2 = ComputeLatency(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,LatencyFactor0,LatencyFactormax)
print(ResLatency2)
tau = 10 
FinConstraint = lambda qsame,qopp,P0,Exec,qdisc,qins,changePrice,DeltaT:FinalConstraintWaitCost(qsame,qopp,P0,Exec,qdisc,qins,tau,changePrice,unitQuant,spread,delta,DeltaT,WaitCost)
ResLatency3 = ComputeLatency(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,LatencyFactor0,LatencyFactormax)
print(ResLatency3)


x = ResLatency1.iloc[:,0]
y = ResLatency1.iloc[:,1]
x1 = ResLatency2.iloc[:,0] 
y1 = ResLatency2.iloc[:,1]
x2 = ResLatency3.iloc[:,0]
y2 = ResLatency3.iloc[:,1]
xlabel=r'Latency' 
ylabel=r'Latency cost'
title=r' a) Latency cost VS Latency'
loc='best' ## Legend location
col='red'
fig = plt.figure(figsize=(8,6))
plt.subplot(1,1,1)
plt.scatter(x,y,color='g',label= "",alpha=0.8,s=60)
plt.plot(x,y,color='g',label=r"$\alpha =2$",lw=4,alpha=.7)
plt.scatter(x1,y1,color='b',label= "",alpha=0.8,s=60)
plt.plot(x1,y1,color='b',label=r"$\alpha =5$",lw=4,alpha=.7)
plt.scatter(x2,y2,color='r',label= "",alpha=0.8,s=60)
plt.plot(x2,y2,color='r',label=r"$\alpha =10$",lw=4,alpha=.7)
plt.title(title,fontsize=fontsize,weight='bold')
plt.xlabel(xlabel,weight='bold')
plt.ylabel(ylabel,weight='bold')
plt.legend(loc=loc)
plt.grid()