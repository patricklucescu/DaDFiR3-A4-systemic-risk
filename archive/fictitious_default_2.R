fictitious_default <- function(x, L) {
  Lbar <- rowSums(L)
  Pi <- diag(1/Lbar)%*%L
  Pi[Lbar==0,] <- 0
  default <- TRUE
  default_set <- numeric(0)
  payments <- Lbar
  while(default){
    wealth <- x + t(Pi[,1:length(x)])%*%payments
    old_payments <- payments
    default_set <- which((wealth - Lbar)<0)
    payments[default_set] <- wealth[default_set]
    if(sum(payments == old_payments) == length(Lbar)) {
      default <- FALSE
    }
  }
  payments
}


## data generation
require(mvtnorm)
d <- 2
n <- 1000
Sigma <- matrix(rep(0.5,d*d), nrow=d)
diag(Sigma) <- 1
normal <- rmvnorm(n, rep(0,d), sigma=Sigma)  #generate copula
uniform <- matrix(sapply(normal, pnorm),nrow=n)  #transform to uniform
X_T <- matrix(sapply(uniform, function(x) qbeta(x,2,5)), nrow=n)  #transform to beta

x_0 <- rep(0.25,d)

S_T <- rep(0.275, d)

s_0 <- rep(0.25, d)


#generate liabilities
probs <- matrix(runif(d*d),nrow=d)

L <- matrix(rep(0,d*d),nrow=d)
L[probs>0.3] <- 0.6
diag(L) <- 0
L <- cbind(L,rep(.2,d))

Lbar <- rowSums(L)
Pi <- diag(1/Lbar)%*%L
Pi[Lbar==0,] <- 0

Lsociety <- sum(L[,d+1])

# create grid
values <- seq(0,1,by=0.01)
list_values <- lapply(seq_len(d), function(x) values)
grid <- expand.grid(list_values)


# create the r.v. Lambda(X^lambda) for different values of lambda
grid_in <- rep(0,nrow(grid))
for(i in 1:nrow(grid)) {
  Lambda <- rep(0,n)
  for(j in 1:n) {
    Xlambda <- (1-as.numeric(grid[i,]))*X_T[j,] + as.numeric(grid[i,])*S_T*x_0/s_0
    p <- fictitious_default(Xlambda, L)
    Lambda[j] <- p%*%Pi[,d+1] - 0.9*Lsociety
  }
  if(sum(Lambda>=0)>=0.95*n) grid_in[i] <- 1
}



