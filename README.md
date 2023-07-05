# Bridge A4 - Risk Transfer and Systemic Risk

The current repository provides a simulation framework to analyze the impact of risk transfer on systemic risk. 
The code is based on the work of Leduc et al. (2016) and Gatti et al. (2011). In contrast to their approach we consider
only two types of agents in our model: firms and banks.

## Overview

In order to understand the underlying role of the CDS market on the financial network we simulate a 
multi-period interbank model which has interactions with a group of firms within the economy. As such the to types of 
agents in our simulations are firms and banks.

These two types of agents can interact on three markets:

- Firms and banks interact on the *credit market*.
- Banks interact with banks on the *interbank market for loans*.
- Banks interact with banks on the *interbank market for Credit Default Swaps (CDS)*.

## Agents

Current subsection describes the two types of agents in our simulation.

### Firms

There are *F* firms that produce the same product and compete on the Goods Market.
At every time step, each firm computes its expected demand *s<sub>i</sub>(t)* and an estimated price 
*p<sub>i</sub>(t)* for their goods. 

















## References
 - Leduc, Matt V., Sebastian Poledna, and Stefan Thurner. 
"Systemic risk management in financial networks with credit default swaps." arXiv preprint arXiv:1601.02156 (2016).
 - Gatti, D. D., Desiderio, S., Gaffeo, E., Cirillo, P., and Gallegati, M. 2011. 
   Macroeconomics from the Bottom-up. Vol. 1. Springer Science & Business Media.