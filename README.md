# Open Questions
## Q-learning
- Should it be "r" or "(1-alpha)*Q_old+alpha*r" when S,a lead to a terminal state? I think it should be the latter!
- alpha=0.1?
- Boltzmann distribution for selectoing actions?
- Batch update or only on event? Or both?
- Is the basic Q-learning formula OK for my scenario? I think yes, because the action of the other player could be
considered a "random" element of the environment's state transition.
- Illegal moves need to lead to instant updates of Q -- otherwise we may get endless loops. I am doing that, but I wonder if this is some sort of double counting?


## Other