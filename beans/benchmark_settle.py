#!/usr/bin/env python

import sys
import time
import multiprocessing as mp

import numpy as np
# from astropy.io using table andascii
import astropy
from astropy.io import ascii
# from astropy.table.table_helpers import simple_table

# local modules
sys.path.append('/home/martin/src/CIC/Adele/beans/settle')
sys.path.append('/home/martin/src/CIC/Adele/beans/beans')
import settle
# imported like this it will not be identifiable where grabbed from
# from settle import settle

# MCu Q: what is the purpose of the following code line?
sys.path

# MCu: figuring out WTF is imported and from where
print("sys.path=")
print(sys.path)
print("--------------------")
# MCu note - this olways works (well so far...)
print("settle.__name__=", settle.__name__)

# MCu note - the following one does not work for a sub-module
if hasattr(settle, '__file__'):
    print("settle.__file__=", settle.__file__)
else:
    print("settle does not have attribute __path__")

# MCu note - the following one does not work for a module
if hasattr(settle, '__path__'):
    print("settle.__path__=", settle.__path__)
else:
    print("settle does not have attribute __path__")


def settle_multiprocessing_wrapper(ft_list_item):
    return settle.settle(ft_list_item['Q_b'],
                         ft_list_item['Z'],
                         ft_list_item['X'],
                         ft_list_item['mdot']/(1+ft_list_item['X']),
                         1.0,
                         ft_list_item['M_NS'],
                         ft_list_item['R_NS'])


# ----- Comparison of settle with Kepler

# Here we want to use the concord table and run a settle model
# with each set to compare the results.
# First need to read in the table

# ft = astropy.io.ascii.read('benchmark/table1.mrt')
ft = ascii.read('benchmark/table1.mrt')
print("ft length = ", len(ft))
if hasattr(ft, '__iter__'):
    print("astropy.table.Table ft is iterable")
else:
    print("astropy.table.Table ft is NOT iterable")

# print(ft)

# add your path to the mrt file below
# fixed parameters
M_NS, R_NS, Q_b = 1.4, 10., 0.1

# print (M_NS, R_NS)
# for run in ft:
#     print (run['run'], run['mdot'], run['X'], run['Z'])

# This section was run on xray, where settle works

tdel, E_b, alpha = [], [], []

# settl = se.settle()

t_start = time.process_time()
t1_sum = 0.0
t2_sum = 0.0

num_runs = 1

for j in range(num_runs):
    t2_start = time.process_time()
    for i, run in enumerate(ft['run']):
        # print ('Running settle for run #{}...'.format(run))
        # need to convert the mdot here, I think this is right
        # In the MRT file accretion rate is given as a fraction of the Eddington rate, i.e.
        # Mdot_Edd = 8.8e4/(1+X) g/cm^2/s; and since settle uses fraction of 8.8e4, we have
        # an extra factor of (1+X) in the MRT values that we need to divide by
        t1_start = time.process_time()
        # res = settl.full(Q_b, ft[i]['Z'], ft[i]['X'], ft[i]['mdot']/(1+ft[i]['X']), 1, R_NS, M_NS)
        res = settle.settle(Q_b, ft[i]['Z'], ft[i]['X'], ft[i]['mdot']/(1+ft[i]['X']), 1.0, M_NS, R_NS)
        t1_end = time.process_time()
        t1_sum += (t1_end-t1_start)
        tdel.append(res['tdel'][0])
        E_b.append(res['E_b'][0])
        alpha.append(res['alpha'][0])
    t2_end = time.process_time()
    t2_sum += (t2_end-t2_start)
    print("Cycle #", j, " time = ", (t2_end-t2_start))

t_end = time.process_time()
print("total process time (", num_runs, "loops) = ", t_end - t_start)
print("settle sum time (", num_runs, "loops) = ", t1_sum)
print("loop sum time (", num_runs, "loops) = ", t2_sum)
print("average", len(ft), "row data table one loop run settle sum time = ", t1_sum/num_runs)

t = astropy.table.Table([ft['run'], tdel[: len(ft)], E_b[: len(ft)], alpha[: len(ft)]])
print(t)
print(type(t))
t.write('se.txt', format='ascii', overwrite=True)
t.write('se.ecsv', format='ascii.ecsv', overwrite=True)

print("======== parallel run ==========")

print("Detected CPUs: ", mp.cpu_count())
pool = mp.Pool(mp.cpu_count())
# pool = mp.Pool(1)

tdel.clear()
E_b.clear()
alpha.clear()

t_start = time.process_time()
t2_sum = 0.0

for j in range(num_runs):
    t2_start = time.process_time()
    # res = settle.settle(Q_b, ft[i]['Z'], ft[i]['X'], ft[i]['mdot']/(1+ft[i]['X']), 1.0, M_NS, R_NS)
    # for i, run in enumerate(ft['run']):
    # add constant columns into astropy table ft
    ft['Q_b'] = Q_b
    ft['M_NS'] = M_NS
    ft['R_NS'] = R_NS
    # print(ft) 
    # need to convert astropy.table.Table to list (of dictionaries)
    ft_list = [dict(zip(ft.colnames, row)) for row in ft]
    # print(ft_list)
    multi_res = pool.map(settle_multiprocessing_wrapper,
                         ft_list, chunksize=8)
    t2_end = time.process_time()
    t2_sum += (t2_end-t2_start)
    print("Cycle #", j, " time = ", (t2_end-t2_start))

# close the process pool
pool.close()
# wait for all tasks to complete
pool.join()

# err print(multi_res['tdel'])

print("len(ft)=", len(ft))
print(type(multi_res))
print(type(multi_res[0]))
print(type(multi_res[0: len(ft)][0]))

# it is impossible to subscript a list -> convert to np.array
multi_res_array = np.array(multi_res)
tdel_wrap1_vector = multi_res_array['tdel']
E_b_wrap1_vector = multi_res_array['E_b']
alpha_wrap1_vector = multi_res_array['alpha']

print("tdel_wrap1_vector =", tdel_wrap1_vector)
print("type(tdel_wrap1_vector) =", type(tdel_wrap1_vector))
print("type(tdel_wrap1_vector[0]) =", type(tdel_wrap1_vector[0]))

# this does not do nothing
# tdel_float_vector = tdel_vector.astype(float)

tdel_wrap2_vector = tdel_wrap1_vector[0]
E_b_wrap2_vector = E_b_wrap1_vector[0]
alpha_wrap2_vector = alpha_wrap1_vector[0]

print("tdel_wrap2_vector =", tdel_wrap2_vector)
print("type(tdel_wrap2_vector) =", type(tdel_wrap2_vector))
print("tdel_wrap2_vector[0] =", tdel_wrap2_vector[0])
print("type(tdel_wrap2_vector[0]) =", type(tdel_wrap2_vector[0]))

tdel_float64_vector = np.array([tdel_float64[0] for tdel_float64 in tdel_wrap1_vector])
E_b_float64_vector = np.array([E_b_float64[0] for E_b_float64 in E_b_wrap1_vector])
alpha_float64_vector = np.array([alpha_float64[0] for alpha_float64 in alpha_wrap1_vector])

# for i in range(len(ft)):
#    tdel_float_vector[i]=float(tdel_string_vector[i])

t_end = time.process_time()
print("total process time (", num_runs, "loops) = ", t_end - t_start)
print("loop sum time (", num_runs, "loops) = ", t2_sum)
print("average", len(ft), "row data table one loop average time = ", t2_sum/num_runs)
t = astropy.table.Table([ft['run'], tdel_float64_vector, E_b_float64_vector, alpha_float64_vector])

print(t)
print(type(t))
t.write('se1.ecsv', format='ascii.ecsv', overwrite=True)
