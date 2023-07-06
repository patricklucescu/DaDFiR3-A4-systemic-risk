# Bridge A4 - Risk Transfer and Systemic Risk

The current repository provides a simulation framework to analyze the impact of risk transfer on systemic risk. 
The code is based on the work of Leduc et al. (2016) and Gatti et al. (2011). In contrast to their approach, we consider
only two types of agents in our model: firms and banks.

## Overview

In order to understand the underlying role of the CDS market on the financial network we simulate a 
multi-period interbank model which has interactions with a group of firms within the economy. As such, the two types of 
agents in our simulations are firms and banks.

These two types of agents can interact on three markets:

- Firms and banks interact on the *credit market*.
- Banks interact with banks on the *interbank market for loans*.
- Banks interact with banks on the *interbank market for Credit Default Swaps (CDS)*.

## Agents

The current subsection describes the two types of agents in our simulation.

### Firms

- There are *F* firms that produce a homogenous product and compete on the Goods Market.
- At every time step, each firm computes its expected demand *s<sub>i</sub>(t)* and an estimated price 
*p<sub>i</sub>(t)* for their goods.
- Following Gatti et al. (2011), *s<sub>i</sub>(t)* and *p<sub>i</sub>(t)* are computed based on the previous time step 
excess demand and the price deviation from the average price across all firms.
- The *i-th* firm carries on production by means of a constant return to scale technology, with labor *L<sub>it<sub>*
as the only input *Y<sub>it</sub> = &alpha;<sub>it</sub> L<sub>it</sub>*, with &alpha;<sub>it</sub> > 0 being the labour
productivity.
- If the internal equity of the firm is not enough to cover the required wages for the desired production, the firm applies for loans on the Credit 
Market. They do so by approaching *N<sub>C</sub>* banks and selecting the one with the lowest interest rate offer.
- Based on the outcome on the Credit Market, firms adjust their expected supply: Either keep the expected supply at 
the desired level if a loan has been granted, or reduce the expected supply.
- Once the wages are paid, the goods are created and offered on the Consumption Goods Market.
- To simulate the Goods Market we use a Markov Model that characterizes the states of the economy. To keep it simple,
we consider a Markov Model with two states: good and bad economy. Each state is characterized by an average consumption
and consumption standard deviation. For each firm, the consumption of goods follows a normal distribution with the 
associated average and standard deviation for the current state of the economy. 
- A firm is declared bankrupt if it cannot repay its loans after the goods market closes. 
- A defaulted firm pays out to its creditors all available liquidity.

### Banks

- There are *B* banks.
- Each bank is characterized by its current equity and deposits.
- Banks use their deposits to offer loans to either firms or other banks.
- Each bank takes into account the creditworthiness of the counterparty and its own specificity.
- Additionally, banks have a maximum leverage. Once this leverage is achieved, they are not allowed to offer more loans.
- Banks try to provide loans to the firms / banks if they have the necessary liquidity and the total loans are 
smaller than the maximum credit they are allowed to extend.
- If banks lack liquidity, they try to borrow funds on the interbank loan market. If unsuccessful, they reject the loan request.
- Every firm loan can be insured by a CDS contract.
- A bank decides with some probability if they want to buy a CDS on a specific firm loan.
- A bank that desires to insure one of its loans approaches *b* random banks and asks them to be the 
counterparty for the CDS contract. 
- We assume a valuation of the CDS contracts that only takes into account the default of the counterparty of the loan. 
However, each bank can have a different view on the probability of default of the underlying.

## Simulation Sequence

In this section we explain step by step the sequence of events that takes place at each individual time step.

The simulation code is contained in `abm_model.abm_simulation.py`. One can define the number of banks and firms
present in the network, the Markov Model that models the goods consumption, and the number `T` of simulation periods.

In the following paragraphs we explain in detail the simulation procedure of one period:

1. In a first step we compute the expected supply and prices for each bank. 
2. Once these have been computed, we check which firms need a loan to cover the expected supply.
3. The program aggregates the loans to each bank. Afterward, each bank assesses each loan individually. At this step, the bank
follows these steps:
   1. Updates the current deposits, which are set as the value of the deposits of the bank.
   2. Updates the maximum credit for the current period. This is computed as 
   *maximum_credit=deposits / capital_requirement*.
   3. If the notional amount of the loan is bigger than the maximum credit allowed, it rejects the loan.
   4. If the notional amount is smaller than the maximum credit, it offers an interest rate. The interest rate is 
   computed as:

         *r<sub>p</sub> * (1 + γ) * tanh((1 + δ * p<sub>d</sub>) * f)*

      where:
      1. *r<sub>p</sub>* is the policy rate set by the central bank.
      2. *(1 + δ * p<sub>d</sub>)* introduces a bit of randomness in the default probability
      of the borrower. δ is uniformly distributed on [0.9,1.1]
      3. *f* represents the financial fragility of the borrower expressed as credit_demand / equity
      4. *γ* introduces bank specificity into the equation, and it is uniformly sampled from [0,h<sub>θ</sub>], where
      h<sub>θ</sub>=0.1 as in Gatti et al. (2011).
      
4. The framework creates the network interactions by allowing each firm to choose the most attractive loan available. 
The network interactions are created according to the following steps:
   1. We randomize the list of firms. This is done in order to create no preference over which firm decides on loans first.
   2. In the order of the randomized firms, each firm is trying to choose the loan with the smallest interest rate. Here,
   there can arise two cases to consider:
      1. If the chosen bank still has credit available and the sum of all notional amounts is below the deposit level,
      it extends the loan immediately. The notional amount is then subtracted from the `current_deposits` variable.
      2. If the chosen bank still has credit available but has depleted its internal deposits, it tries to apply for an
      interbank loan. This follows a similar procedure as in the case of firm loans, with the bank approaching different
      banks which provide interest rates if funds are available. The interest rate is given by *r<sub>p</sub> * 
      (1 + γ) * tanh(f)*, with the financial fragility of the bank being defined as the sum of all loans' notional amount
      divided by the deposits of the bank.
   3. The firm goes over the list of loans until either a loan is accepted or the list of potential lenders is depleted.
   4. If a firm loan has been extended, banks can now decide to buy CDSs on the newly created loan. 
   5. Each bank decides with a certain probability if they want to buy a CDS and they search for possible counterparties
   in the bank network.
   6. They choose the counterparty with the most attractive spread.
5. Once the network interactions have been created, the Goods Market consumption is simulated using the Markov Model. 
Depending on the state of the economy, each firm's consumption is drawn from the state-dependent distribution.
6. The default of the firms is being considered, with a firm defaulting if it cannot pay its outstanding debts. 
7. Banks incur deposit shocks, either positive or negative. In the case of negative shocks, the banks have to pay 
out depositors prior to the clearing of the banking network.
8. The default of the banks is being considered. This step is not as straightforward as in the case of firms as banks 
have dependencies between them. We employ the Eisenberg & Noe (2001) clearing mechanism to see which banks default on
their debt.
9. Once the defaulting firms and banks have been found, we create new agents from the average of the remaining agents in 
order to keep the number of firms and banks in the system constant.

## TODO:

- It is still unclear how banks decide to be the counterparty for a CDS. Do they offer a spread by default or should 
they consider other factors as well?
- Within the clearing of the banks, the internal remaining deposits of a bank are not used to pay outstanding debt. 
While this would not save a bank from default (as this would mean the internal equity is already gone), it could save 
other banks from defaulting.




## References
- Eisenberg, Larry and Thomas H Noe (2001). “Systemic risk in financial systems”. In:
Management Science 47.2, pp. 236–249.
 - Leduc, Matt V., Sebastian Poledna, and Stefan Thurner. 
"Systemic risk management in financial networks with credit default swaps." arXiv preprint arXiv:1601.02156 (2016).
 - Gatti, D. D., Desiderio, S., Gaffeo, E., Cirillo, P., and Gallegati, M. 2011. 
   Macroeconomics from the Bottom-up. Vol. 1. Springer Science & Business Media.
