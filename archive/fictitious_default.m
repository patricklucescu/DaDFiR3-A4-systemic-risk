clear all;
clc;

%% settings
% general
num_scenarios = 1000;        % size of state space
num_players = 2;            % number players
grid_step_size = 0.05;       % grid size of lambda
alpha = 0.05;               % probability level of risk measure
beta = 0.9;                   % fraction to be paid back to society
a = 2*ones(num_players,1);  % a of beta-distribution
b = 5*ones(num_players,1);  % b of beta-distribution
%a = 2*ones(num_players,1);      % shape of gamma
%b = 0.1*ones(num_players,1);    % scale of gamma
%rho_list = -1:0.2:1;


% for index = 1:length(rho_list)
% rho = rho_list(index);
rho = 0.5;
% covariance
mu = zeros(num_players,1);  % expectation of multivariate normal
Sigma = [1   , rho; 
         rho , 1  ];        % covariance of multivariate normal

% prices
s0 = 0.25*ones(num_players,1);  % price of eligible asset at t=0
ST = 0.275*ones(num_players,1); % price of eligible asset at t=T
x0 = 0.25*ones(num_players,1);  % price of risky position at t=0

% random wealth
XT = mvnrnd(mu,Sigma,num_scenarios); % multivariate normal            
for i = 1:num_players
    XT(:,i) = normcdf(XT(:,i),mu(i),Sigma(i,i));
    XT(:,i) = betainv(XT(:,i),a(i),b(i));
    %XT(:,i) = gaminv(XT(:,i), a(i), b(i));
end
% figure;
% plot(x(:,1),x(:,2),'o');

% liabilities (last column is owed to society)
L = [ 0   , 0.6 , 0.2 ; 
      0.6 , 0   , 0.2 ];
Lbar = sum(L,2);
temp = repmat(1./Lbar, 1, num_players + 1);
temp(temp==Inf) = 0;
Pi = temp.*L;

Lsociety = sum(L(:,end));

% create grid
grid_steps = (0:grid_step_size:1)';
grid = allcomb(grid_steps , grid_steps, 'matlab');
VaR_acc_grid = false(size(grid,1) , 1);
ES_acc_grid = false(size(VaR_acc_grid));

%%
for i = 1:size(grid,1)
    Lambda = zeros(num_scenarios , 1);
    for j = 1:num_scenarios
        % calculate (1-lambda)*X_T + lambda*S_T
        Xlambda = (1-grid(i,:))'.*XT(j,:)' + grid(i,:)'.*ST.*x0./s0;
        payments = calc_payments(Xlambda , Lbar, Pi(:,1:num_players));
        Lambda(j) = payments'*Pi(:,end) - beta*Lsociety;
    end
    
    Lambda = sort(Lambda);
    VaR_index = find(Lambda >= 0 , 1);
    if VaR_index/num_scenarios <= alpha
        VaR_acc_grid(i) = true;
    end
    if sum(Lambda(1:floor(alpha*num_scenarios))) / floor(alpha*num_scenarios) >= 0
        ES_acc_grid(i) = true;
    end
       
    
    if mod(i , 100 ) == 0
        fprintf("%d / %d \n", i, size(grid,1));
    end 
    
end

%%

% VaR_acc_grid_boundary = false(size(VaR_acc_grid));
% temp = VaR_acc_grid(2:end) - VaR_acc_grid(1:end-1);
% for i=2:length(VaR_acc_grid_boundary)
%     if temp(i-1) == 1
%         VaR_acc_grid_boundary(i) = true;
%     end
% end


figure; hold on;

plot(grid(VaR_acc_grid,1),grid(VaR_acc_grid,2),'bo');
% plot(grid(VaR_acc_grid_boundary,1),grid(VaR_acc_grid_boundary,2),'ko');
plot(grid(ES_acc_grid,1),grid(ES_acc_grid,2),'ro');
axis equal;
axis([0 1 0 1]);
%axis tight;




%% investigate resulting positions

Xlambda = ((1-[0.6,0.6])'.*XT' + [0.6,0.6]'.*ST.*x0./s0 )';
figure; hold on;
x = [Xlambda(:,1) ; XT(:,1)];
y = [Xlambda(:,2) ; XT(:,2)];
altered_pos = cell(2*num_scenarios,1);
altered_pos(1:num_scenarios) = {'Original position'};
altered_pos(num_scenarios+1:end) = {'Altered position'};
scatterhist(x,y,'Group',altered_pos);
% scatterhist(Xlambda(:,1), Xlambda(:,2));
% scatterhist(XT(:,1), XT(:,2));



%% algorithm to calculate payment vector
function payments = calc_payments(x,Lbar,Pi)
    default = true;
    payments = Lbar;
    while default
        wealth = x + Pi'*payments;
        old_payments = payments;
        default_set = find( wealth - Lbar < 0 );
        payments(default_set) = wealth(default_set);
        if ( sum(abs(payments - old_payments) < 10^(-6)) == length(Lbar) )
            default = false;
        end
    end
end
