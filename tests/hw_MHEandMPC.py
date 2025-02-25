#%%Import packages
import numpy as np
from random import random
from gekko import GEKKO
import matplotlib.pyplot as plt


#%% Process
p = GEKKO()

p.time = [0,.5]

#Parameters
p.u = p.MV()
p.K = p.Param(value=1) #gain
p.tau = p.Param(value=5) #time constant

#variable
p.y = p.SV() #measurement

#Equations
p.Equation(p.tau * p.y.dt() == -p.y + p.K * p.u)

#options
p.options.IMODE = 4


#%% MHE Model
m = GEKKO()

m.time = np.linspace(0,20,41) #0-20 by 0.5 -- discretization must match simulation

#Parameters
m.u = m.MV() #input
m.K = m.FV(value=3, lb=1, ub=3) #gain
m.tau = m.FV(value=4, lb=1, ub=10) #time constant

#Variables
m.y = m.CV() #measurement

#Equations
m.Equation(m.tau * m.y.dt() == -m.y + m.K*m.u)


#Options
m.options.IMODE = 5 #MHE
m.options.EV_TYPE = 1
m.options.DIAGLEVEL = 0

# STATUS = 0, optimizer doesn't adjust value
# STATUS = 1, optimizer can adjust
m.u.STATUS = 0
m.K.STATUS = 1
m.tau.STATUS = 1
m.y.STATUS = 1

# FSTATUS = 0, no measurement
# FSTATUS = 1, measurement used to update model
m.u.FSTATUS = 1
m.K.FSTATUS = 0
m.tau.FSTATUS = 0
m.y.FSTATUS = 1

# DMAX = maximum movement each cycle
m.K.DMAX = 1
m.tau.DMAX = .1

# MEAS_GAP = dead-band for measurement / model mismatch
m.y.MEAS_GAP = 0.25

m.y.TR_INIT = 1


#%% MHE Model
c = GEKKO()

c.time = np.linspace(0,5,11) #0-5 by 0.5 -- discretization must match simulation

#Parameters
c.u = c.MV(lb=-10,ub=10) #input
c.K = c.FV(value=10, lb=1, ub=3) #gain
c.tau = c.FV(value=1, lb=1, ub=10) #time constant

#Variables
c.y = c.CV() #measurement

#Equations
c.Equation(c.tau * c.y.dt() == -c.y + c.u * c.K)


#Options
c.options.IMODE = 6 #MPC
c.options.CV_TYPE = 1

# STATUS = 0, optimizer doesn't adjust value
# STATUS = 1, optimizer can adjust
c.u.STATUS = 1
c.K.STATUS = 0
c.tau.STATUS = 0
c.y.STATUS = 1

# FSTATUS = 0, no measurement
# FSTATUS = 1, measurement used to update model
c.u.FSTATUS = 0
c.K.FSTATUS = 1
c.tau.FSTATUS = 1
c.y.FSTATUS = 1

# DMAX = maximum movement each cycle
c.u.DCOST = .1

#y setpoint
#if CV_TYPE = 1, use SPHI and SPLO
c.y.SPHI = 3.1
c.y.SPLO = 2.9
#if CV_TYPE = 2, use SP
#c.y.SP = 3

c.y.TR_INIT = 0

#%% problem configuration
# number of cycles
cycles = 50
# noise level
noise = 0.25



#%% run process, estimator and control for cycles
y_meas = np.empty(cycles)
y_est = np.empty(cycles)
k_est = np.empty(cycles)
tau_est = np.empty(cycles)
u_cont = np.empty(cycles)


for i in range(cycles):
    ## controller
    #load 
    c.tau.MEAS = m.tau.NEWVAL 
    c.K.MEAS = m.K.NEWVAL 
    if p.options.SOLVESTATUS == 1:
        c.y.MEAS = p.y.MODEL
    #change setpoint at time 25
    if i == 25:
        c.y.SPHI = 6.1
        c.y.SPLO = 5.9
    c.solve(remote=False)
    u_cont[i] = c.u.NEWVAL
    
    ## process simulator
    #load control move
    p.u.MEAS = u_cont[i]
    #simulate
    p.solve(remote=False)
    #load output with white noise
    y_meas[i] = p.y.MODEL + (random()-0.5)*noise
    
    ## estimator
    #load input and measured output
    m.u.MEAS = u_cont[i]
    m.y.MEAS = y_meas[i]
    #optimize parameters
    m.solve(remote=False)
    #store results
    y_est[i] = m.y.MODEL 
    k_est[i] = m.K.NEWVAL 
    tau_est[i] = m.tau.NEWVAL 
    
    

#%% Plot results
plt.figure()
plt.subplot(4,1,1)
plt.plot(y_meas)
plt.plot(y_est)
plt.legend(('meas','pred'))
plt.ylabel('y')
plt.subplot(4,1,2)
plt.plot(np.ones(cycles)*p.K.value[0])
plt.plot(k_est)
plt.legend(('actual','pred'))
plt.ylabel('k')
plt.subplot(4,1,3)
plt.plot(np.ones(cycles)*p.tau.value[0])
plt.plot(tau_est)
plt.legend(('actual','pred'))
plt.ylabel('tau')
plt.subplot(4,1,4)
plt.plot(u_cont)
plt.legend('u')
