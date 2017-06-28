# -*- coding: utf-8 -*-
"""
Created on Sun Jun 25 20:52:32 2017

@author: Otm
"""


##########################################################################################################################
########################################## Price Move VS Initial Imbalance #############################################
##########################################################################################################################


# import libraries 
import sys
pathLib = 'D:\\etude\\charles-albert\\travail_rendu2\\FinalVersionsOptiBouclage\\CtrlOptiF\\CtrlOpti\\AlgoOptiSimuTheoTerminal_Revision5\\CtrlOptiLimitOrder'
sys.path.insert(0,pathLib)
import ctrlopti.AlgOptiSimu as AlgOptiSimu
import ctrlopti.AlgOptiSimuStayDetail as AlgOptiSimuStayDetail
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
        
        
## Global variable :
unit = 1


## Testing code :
## testing optimized method 
        
        
##########################################################################################################################
########################################## Main function ###########################################################
##########################################################################################################################


def PriceMoveInitImb(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,PriceJump,K) :
    " option equals 1 if we can't cancel our order and  equals 2 for our optimal control problem "
    " option0 equals 1 if we compute Delta P  and  equals 2 for the final Exec price "
    
    size =  (QAftI+QBefI) + (QOppI)-2
    res=np.zeros((size,5))
    label=['']*size
    
    for i in range(1,QAftI+QBefI):
        print("NbIter : ",i)
        QOpp0 = float(i+1)
        QSame = QAftI+QBefI
        ## Opti Strat
        ctrlOptiSimGlob = AlgOptiSimu.CtrlOptiSimu(QAftI,QBefI,QOpp0,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant)
        fwdgraph = ctrlOptiSimGlob.forwardsimulationOpti()
        bsGraph = ctrlOptiSimGlob.backwardsimulationOpti(fwdgraph)
        ## Stay Strat
        OptiSimuCsteS = AlgOptiSimuStayDetail.CtrlOptiSimuStay(QAftI,QBefI,QOpp0,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,PriceJump)
        fwdgraphS=OptiSimuCsteS.forwardsimulationOpti()
        bsGraphS=OptiSimuCsteS.backwardsimulationOpti(fwdgraphS)
        res[(i-1),0]=((QAftI+QBefI)-QOpp0)/(QOpp0 + (QAftI+QBefI))
        res[(i-1),1] = QSame
        res[(i-1),2] = QOpp0
        res[(i-1),3]=bsGraph['Results']["UtilityBefore"][0]
        res[(i-1),4] = bsGraphS['Results']["UtilityBefore"][0]
        label[(i-1)]=bsGraph['Results']["OptiStrategy"][0]

    index = (QAftI+QBefI)-1
    for i in range((QOppI-1),0,-1):
        # i = 9
        print("NbIter : ",index+(QOppI-i))
        QAft0 = max(0,i-K)
        QBef0 = min(K,i) #float(i)
        ctrlOptiSimGlob = AlgOptiSimu.CtrlOptiSimu(QAft0,QBef0,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant)
        fwdgraph = ctrlOptiSimGlob.forwardsimulationOpti()
        bsGraph = ctrlOptiSimGlob.backwardsimulationOpti(fwdgraph)
        ## Stay Strat
        OptiSimuCsteS = AlgOptiSimuStayDetail.CtrlOptiSimuStay(QAft0,QBef0,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,PriceJump)
        fwdgraphS=OptiSimuCsteS.forwardsimulationOpti()
        bsGraphS=OptiSimuCsteS.backwardsimulationOpti(fwdgraphS)
        QSame = QAft0+QBef0
        res[(index+(QOppI-1-i)),0] = (QSame-QOpp0)/(QOpp0 + QSame)
        res[(index+(QOppI-1-i)),1] = QSame
        res[(index+(QOppI-1-i)),2] = QOppI
        res[(index+(QOppI-1-i)),3] = bsGraph['Results']["UtilityBefore"][0]
        res[(index+(QOppI-1-i)),4] = bsGraphS['Results']["UtilityBefore"][0]
        label[(index+(QOppI-1-i))] = bsGraph['Results']["OptiStrategy"][0]
     
    res=pd.DataFrame(res,columns=['Imbalance','Qbid','QAsk','OptiUtility','OptiStayUtility'])
    StratOpti = pd.DataFrame(label,columns=['OptiStrategy'])
    
    return pd.concat([res,StratOpti],axis=1)

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
        return (MicroPrice(QSame,QOpp,Price,tau) - (Price - (spread*unit/2.))) 
    if (((Exec == 1.0) or (Exec <= -1.0)) and (ChangePrice != 0)):# a reformuler
        return (MicroPrice(QSame,QOpp,Price,tau) - (Price + (spread*unit/2.)))
    if (Exec == 0) :
        return (MicroPrice(QSame,QOpp-unit*unitQuant,Price,tau) - (Price + (spread*unit/2.))) if (QOpp>=2*unitQuant) else (MicroPrice(
            quantiteIns,quantiteDisc,Price+unit*delta,tau) - (Price + (spread*unit/2.)))

# The following function computes the final constraint with the associated waiting cost
def FinalConstraintWaitCost(QSame,QOpp,Price,Exec,quantiteDisc,quantiteIns,tau,ChangePrice=1,unitQuant=1,spread=1,delta=1,DeltaT=0,WaitCost=0):
    return float(FinalConstraint(QSame,QOpp,Price,Exec,quantiteDisc,quantiteIns,tau,ChangePrice,unitQuant,spread,delta) - WaitCost*DeltaT*unitQuant)

    

##########################################################################################################################
########################################## Test #############################################
##########################################################################################################################


## Paramters Initialization :
QAftI=12# Q after initial
QBefI=0 # Q before initial
QOppI=QAftI+ QBefI# Q opposite initial
K = QBefI 
P0=10 # Initial price
TimeStep=1 # the discretization timestep
nbIter=20# number of simulated periods
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

### 1 
print('Case 1: cste intensities')
IntensFunc = lambda qbid,qask,option: IntensFunc0(qbid,qask,option,lambdaInser,lambdaCancel)
DiscQtyFunc = lambda qopp,qsame:DiscQtyFunc0(qopp,qsame,quantiteDisc,quantiteIns)
FinConstraint = lambda qsame,qopp,P0,Exec,qdisc,qins,changePrice,DeltaT:FinalConstraintWaitCost(qsame,qopp,P0,Exec,qdisc,qins,tau,changePrice,unitQuant,spread,delta,DeltaT,WaitCost)


res1 = PriceMoveInitImb(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,K,PriceJump)
print(res1.head())


### Plot data
StayCtrlNoMrkt =[]
StayImbNoMrkt = []
CancelCtrlNoMrkt = []
CancelImbNoMrkt =[]

size = len(res1)
for j in range(size):
    if res1['OptiStrategy'][j][0]=='0' :
        StayCtrlNoMrkt.append(res1['OptiUtility'][j])
        StayImbNoMrkt.append(res1['Imbalance'][j])
    if res1['OptiStrategy'][j][0]=='1' :
        CancelCtrlNoMrkt.append(res1['OptiUtility'][j])
        CancelImbNoMrkt.append(res1['Imbalance'][j])


Imbalance = np.array(res1['Imbalance'])
OptiUtNoMrkt = np.array(res1['OptiUtility'])
StayUtMrkt = np.array(res1['OptiStayUtility'])
plt.scatter(Imbalance[:-1],StayUtMrkt[:-1],color="green",alpha=0.8,s=60)
plt.plot(Imbalance[:-1],StayUtMrkt[:-1],label='NC',color="blue",alpha=0.8,linewidth=3.0)
plt.plot(Imbalance[:-1],OptiUtNoMrkt[:-1],label='OC',color="red",alpha=0.8,linewidth=3.0)
plt.scatter(StayImbNoMrkt[:-1],StayCtrlNoMrkt[:-1],label='First action is stay',color="green",alpha=0.8,s=60)
plt.scatter(CancelImbNoMrkt,CancelCtrlNoMrkt,label='First action is cancel',color="red",alpha=0.8,s=60)
plt.xlabel("Initial Imbalance")
plt.ylabel(r"$\text{E}_{U_0,\mu}( \Delta \text{P} | \text{Exec} )$")
plt.legend(loc='best')
plt.grid()
plt.tight_layout()
plt.show()


### 2 
print('Case 1: cste intensities')
IntensFunc = lambda qbid,qask,option: IntensFunc1(qbid,qask,option,alpha,alpha2,lambdaInser,lambdaCancel)
DiscQtyFunc = lambda qopp,qsame:DiscQtyFunc1(q0,q01,qsame,qopp,tau1,tau2,q1,Q,theta1,theta2,option)

res2 = PriceMoveInitImb(QAftI,QBefI,QOppI,P0,TimeStep,nbIter,IntensFunc,DiscQtyFunc,FinConstraint,unitQuant,K,PriceJump)
print(res2.head())


## Plot data
StayCtrlNoMrkt =[]
StayImbNoMrkt = []
CancelCtrlNoMrkt = []
CancelImbNoMrkt =[]

size = len(res2)
for j in range(size):
    # j = 8
    if res2['OptiStrategy'][j][0]=='0' :
        StayCtrlNoMrkt.append(res2['OptiUtility'][j])
        StayImbNoMrkt.append(res2['Imbalance'][j])
    if res2['OptiStrategy'][j][0]=='1' :
        CancelCtrlNoMrkt.append(res2['OptiUtility'][j])
        CancelImbNoMrkt.append(res2['Imbalance'][j])

Imbalance = np.array(res2['Imbalance'])
OptiUtNoMrkt = np.array(res2['OptiUtility'])
StayUtMrkt = np.array(res2['OptiStayUtility'])
plt.scatter(Imbalance[:-1],StayUtMrkt[:-1],color="green",alpha=0.8,s=60)
plt.plot(Imbalance[:-1],StayUtMrkt[:-1],label='NC',color="blue",alpha=0.8,linewidth=3.0)
plt.plot(Imbalance[:-1],OptiUtNoMrkt[:-1],label='OC',color="red",alpha=0.8,linewidth=3.0)
plt.scatter(StayImbNoMrkt[:-1],StayCtrlNoMrkt[:-1],label='First action is stay',color="green",alpha=0.8,s=60)
plt.scatter(CancelImbNoMrkt,CancelCtrlNoMrkt,label='First action is cancel',color="red",alpha=0.8,s=60)
plt.xlabel("Initial Imbalance")
plt.ylabel(r"$\text{E}_{U_0,\mu}( \Delta \text{P} | \text{Exec} )$")
plt.legend(loc='best')
plt.grid()
plt.tight_layout()
plt.show()