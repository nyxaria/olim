------------------------------------------
-- Analysis of OLIM	                --
--                                      --
-- George Hartt                         --
-- george.hartt@icloud.com              --
--                                      --
-- 25 Nov 2019                          --
--                                      --
------------------------------------------

-- This is a modified version of the 'Woofer Motor' analysis script given at http://www.femm.info/wiki/Woofer by David Meeker.


-- This script reads an existing geometry info FEMM and analyses it at a number
-- of different coil locations. It is assumed that the linear motor has been
-- drawn with all elements for the plunger in group 1, and the copper coil belonging
-- to group number 2, so that the plunger can be easily selected and moved by
-- the script and the copper coil can be selected for intergration.  It is also assumed
-- that the .fem file describing the motor is located in the same directory as the
-- script. Lastly, the plunger in the .fem file should be in the home/zero position.

-- This script prints the results in FEMM, as well as storing it in a text file of the name "{ModelName}_analysis_{YYMMDD}_{HH:MM}.csv" in the directory of this script.

--------------------------------------
-- Design - Specific Parameters
--------------------------------------

-- Model Name
ModelName = 'olim';

-- Maximum extension from zero/home position
Xlim = 150;

-- Movement increments used during the analysis
dX = 1;

--------------------------------------
-- Analysis Routines
--------------------------------------

-- Analyze BL and incremental inductance at 1 mm steps between - Xlim and + Xlim
open(ModelName .. ".FEM");
mi_saveas('temp.fem');

root = ModelName .. "_analysis_" .. date("%y%m%d_%I%M")
bl_curve_log = ModelName .. "_BL_curve.csv";
execute("mkdir " .. root)
handle = openfile(root .. "/" .. bl_curve_log, "w");
write(handle, "Displacement (mm),BL(N/A)\n");
closefile(handle);
showconsole();
clearconsole();

print('---------------------------------------------')
print(' OLIM Analysis Script');
print('');
print('---------------------------------------------');
print('');
print('Disp(mm)','BL(N/A)');
for k=0, Xlim, dX do
    mi_modifycircprop('Coil',1,1);
    mi_analyze(1);
    mi_loadsolution();
    mo_zoom(0,-238,190,97);
    mo_showdensityplot(1,0,1.5,0.005,"mag");
    -- mo_hidecontourplot()
    mo_hidepoints();
    mo_savebitmap(root .. "/" .. "render_x=" .. k .. ".png");
      mo_groupselectblock(2);
    fz = mo_blockintegral(12);
    mo_close();
    -- print(fz)
    -- fz = mo_blockintegral(12);
    -- mo_close();
    -- print(fz)
    -- parm1,R,fl1 = mo_getcircuitproperties('Coil');
    -- mi_modifycircprop('Coil', 1, 0);
    -- mi_analyze(1);
    -- mi_loadsolution();
    -- parm1,parm2,fl0 = mo_getcircuitproperties('Coil');
    -- L = (fl1 - fl0)*10^6;
    print(k, fz);
    handle = openfile(root .. "/" .. bl_curve_log, "a");
    write(handle, k .. "," .. fz .. "\n");
    closefile(handle);
    mi_selectgroup(1);
    mi_movetranslate(0, -1);
end

closefile(handle);
mi_close();
remove('temp.fem');
remove('temp.ans');

print('');
print('DC coil resistance = ',R);
