function [b, se] = fixedpanel(years,panels)
data = load('data');
y = data.response; % these are the difference in cites
x = data.predictor; % these are the year indicators. 0 until year of grant, then 1 thereafter
x = double(x); % convert to double otherwise matlab complains
y = double(y);

n = years; % over N years
d = panels; %  pairs of (MI, nonenforce)
% reshape to get into a format matlab can use
Y = reshape(y, n, d);

K = n+1; N = n*d;
X = cell(n,1);
% set up the design matrices
for i = 1:n
    x0 = zeros(d,K-1);
    x0(:,i) = 1;
    X{i} = [x0,x(i:n:N)];
end
% run regression
[b,sig,E,V] = mvregress(X,Y,'algorithm','cwls');
csvwrite('coefficients.csv',b);

% compute standard error
XX = cell2mat(X);
S = kron(eye(n),sig);
Vpcse = inv(XX'*XX)*XX'*S*XX*inv(XX'*XX);
se = sqrt(diag(Vpcse));
csvwrite('standarderror.csv',se);

% plot
xx = linspace(min(x),max(x));
axx = repmat(b(1:K-1),1,length(xx));
bxx = repmat(b(K)*xx,n,1);
yhat =  axx + bxx;
hLines = plot(xx,yhat);

