% ActiveFEMM (C)2006 David Meeker, dmeeker@ieee.org

function ho_addcontour(x,y)
if (nargin==2)
	callfemm(['ho_addcontour(' , numc(x) , num(y) , ')' ]);
elseif (nargin==1)
	callfemm(['ho_addcontour(' , numc(x(1)) , num(x(2)) , ')' ]);
end

