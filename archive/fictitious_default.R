fictitious_default <- function(x, L) {
  Lbar <- rowSums(L)
  Pi <- diag(1/Lbar)%*%L
  Pi[Lbar==0,] <- 0
  default <- TRUE
  default_set <- numeric(0)
  payments <- Lbar
  while(default){
    wealth <- x + t(Pi)%*%payments
    old_payments <- payments
    default_set <- which((wealth - Lbar)<0)
    payments[default_set] <- wealth[default_set]
    if(sum(payments == old_payments) == length(Lbar)) {
      default <- FALSE
  }
  payments
  }
}