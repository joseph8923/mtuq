

Imports="""
import os
import sys
import numpy as np
import mtuq.dataset.sac
import mtuq.greens_tensor.fk

from os.path import basename, join
from mtuq.grid_search import DCGridRandom
from mtuq.grid_search import grid_search_mpi
from mtuq.misfit.cap import misfit
from mtuq.process_data.cap import process_data
from mtuq.util.cap_util import trapezoid_rise_time, Trapezoid
from mtuq.util.plot import plot_waveforms
from mtuq.util.util import AttribDict, cross, root


"""


DocstringDC3Serial="""
if __name__=='__main__':
    #
    # Double-couple inversion example
    # 
    # Carries out grid search over 50,000 randomly chosen double-couple 
    # moment tensors
    #
    # USAGE
    #   python GridSearchDC3Serial.py
    #
    # A typical runtime is about 60 minutes. For faster results, try 
    # GridSearchDC3.py, which runs the same inversion in parallel rather than
    # serial
    #


"""


DocstringDC3="""
if __name__=='__main__':
    #
    # Double-couple inversion example
    # 
    # Carries out grid search over 50,000 randomly chosen double-couple 
    # moment tensors
    #
    # USAGE
    #   mpirun -n <NPROC> python GridSearchDC3.py


"""


DocstringDC5="""
if __name__=='__main__':
    #
    # Double-couple inversion example
    # 
    # Carries out grid search over source orientation, magnitude and depth
    #
    # USAGE
    #   mpirun -n <NPROC> python GridSearchDC5.py


"""


DocstringFMT5="""
if __name__=='__main__':
    #
    # Full moment tensor inversion example
    # 
    # Carries out grid search over all moment tensor parameters except
    # magnitude 
    #
    # USAGE
    #   mpirun -n <NPROC> python GridSearchFullMT.py


"""


DocstringCAPUAF="""
if __name__=='__main__':
    # to benchmark against CAPUAF:
    # cap.pl -H0.02 -P1/15/60 -p1 -S2/10/0 -T15/150 -D1/1/0.5 -C0.25/0.6667/0.025/0.0625 -Y1 -Zweight_test.dat -Mscak_34 -m4.3 -I1 -R0/0/0/0/180/180/0.5/0.5/0/0 20090407201255351


"""



DefinitionsPaths="""
    #
    # Here we specify the data used for the inversion. The event is an 
    # Mw~4 Alaska earthquake. For now, these paths exist only in my personal 
    # environment.  Eventually we need to include sample data in the 
    # repository or make it available for download
    #
    paths = AttribDict({
        'data':    join(root(), 'tests/data/20090407201255351'),
        'weights': join(root(), 'tests/data/20090407201255351/weights.dat'),
        'greens':  join(os.getenv('CENTER1'), 'data/wf/FK_SYNTHETICS/scak'),
        })

    event_name = '20090407201255351'



"""


DefinitionsDataProcessing="""
    #
    # Here we specify all the data processing and misfit settings used in the
    # inversion.  For this example, body- and surface-waves are processed
    # separately, and misfit is a sum of indepdendent body- and surface-wave
    # contributions. (For a more flexible way of specifying parameters based on
    # command-line argument passing rather than scripting, see
    # mtuq/scripts/cap_inversion.py)
    #

    process_bw = process_data(
        filter_type='Bandpass',
        freq_min= 0.25,
        freq_max= 0.667,
        pick_type='from_fk_database',
        fk_database=paths.greens,
        window_type='cap_bw',
        window_length=15.,
        padding_length=2.,
        weight_type='cap_bw',
        weight_file=paths.weights,
        )

    process_sw = process_data(
        filter_type='Bandpass',
        freq_min=0.025,
        freq_max=0.0625,
        pick_type='from_fk_database',
        fk_database=paths.greens,
        window_type='cap_sw',
        window_length=150.,
        padding_length=10.,
        weight_type='cap_sw',
        weight_file=paths.weights,
        )

    process_data = {
       'body_waves': process_bw,
       'surface_waves': process_sw,
       }


"""


DefinitionsMisfit="""
    misfit_bw = misfit(
        time_shift_max=2.,
        time_shift_groups=['ZR'],
        )

    misfit_sw = misfit(
        time_shift_max=10.,
        time_shift_groups=['ZR','T'],
        )

    misfit = {
        'body_waves': misfit_bw,
        'surface_waves': misfit_sw,
        }


"""


GridDC3="""
    grid = DCGridRandom(
        npts=50000,
        Mw=4.5)

    rise_time = trapezoid_rise_time(Mw=4.5)
    wavelet = Trapezoid(rise_time)


"""


GridDC5="""
    grid = DCGridRandom(
        npts=50000,
        Mw=4.5)

    origins = OriginGrid(depth=np.arange(2500.,20000.,2500.),
        latitude=origin.latitude,
        longitude=origin.longitude)

    rise_time = trapezoid_rise_time(Mw=4.5)
    wavelet = Trapezoid(rise_time)

"""


GridFMT5="""
    grid = MTGridRandom(
        npts=1000000,
        Mw=4.5)

    rise_time = trapezoid_rise_time(Mw=4.5)
    wavelet = Trapezoid(rise_time)

"""


GridSearchSerial="""
    #
    # The main work of the grid search starts now
    #

    print 'Reading data...\\n'
    data = mtuq.dataset.sac.reader(paths.data, wildcard='*.[zrt]')
    data.sort_by_distance()

    stations  = []
    for stream in data:
        stations += [stream.station]
    origin = data.get_origin()


    print 'Processing data...\\n'
    processed_data = {}
    for key in ['body_waves', 'surface_waves']:
        processed_data[key] = data.map(process_data[key])
    data = processed_data


    print 'Reading Greens functions...\\n'
    factory = mtuq.greens_tensor.fk.GreensTensorFactory(paths.greens)
    greens = factory(stations, origin)


    print 'Processing Greens functions...\\n'
    greens.convolve(wavelet)
    processed_greens = {}
    for key in ['body_waves', 'surface_waves']:
        processed_greens[key] = greens.map(process_data[key])
    greens = processed_greens


    print 'Carrying out grid search...\\n'
    results = grid_search_serial(data, greens, misfit, grid)


    print 'Saving results...\\n'
    grid.save(event_name+'.h5', {'misfit': results})
    best_mt = grid.get(results.argmin())


    print 'Plotting waveforms...\\n'
    synthetics = {}
    for key in ['body_waves', 'surface_waves']:
        synthetics[key] = greens[key].get_synthetics(best_mt)
    plot_waveforms(event_name+'.png', data, synthetics, misfit)


"""


GridSearchMPI="""
    #
    # The main work of the grid search starts now
    #
    from mpi4py import MPI
    comm = MPI.COMM_WORLD


    if comm.rank==0:
        print 'Reading data...\\n'
        data = mtuq.dataset.sac.reader(paths.data, wildcard='*.[zrt]')
        data.sort_by_distance()

        stations  = []
        for stream in data:
            stations += [stream.station]
        origin = data.get_origin()

        print 'Processing data...\\n'
        processed_data = {}
        for key in ['body_waves', 'surface_waves']:
            processed_data[key] = data.map(process_data[key])
        data = processed_data

        print 'Reading Greens functions...\\n'
        GreensTensorFactory = mtuq.greens_tensor.fk.GreensTensorFactory(paths.greens)
        greens = GreensTensorFactory(stations, origin)

        print 'Processing Greens functions...\\n'
        greens.convolve(wavelet)
        processed_greens = {}
        for key in ['body_waves', 'surface_waves']:
            processed_greens[key] = greens.map(process_data[key])
        greens = processed_greens

    else:
        data = None
        greens = None

    data = comm.bcast(data, root=0)
    greens = comm.bcast(greens, root=0)


    if comm.rank==0:
        print 'Carrying out grid search...\\n'
    results = grid_search_mpi(data, greens, misfit, grid)
    results = comm.gather(results, root=0)


    if comm.rank==0:
        print 'Saving results...\\n'
        results = np.concatenate(results)
        grid.save(event_name+'.h5', {'misfit': results})
        best_mt = grid.get(results.argmin())


    if comm.rank==0:
        print 'Plotting waveforms...\\n'
        synthetics = {}
        for key in ['body_waves', 'surface_waves']:
            synthetics[key] = greens[key].get_synthetics(best_mt)
        plot_waveforms(event_name+'.png', data, synthetics, misfit)


"""



GridSearchMPIAlternate="""
    #
    # The main work of the grid search starts now
    #
    from mpi4py import MPI
    comm = MPI.COMM_WORLD


    if comm.rank==0:
        print 'Reading data...\\n'
        data = mtuq.dataset.sac.reader(paths.data, wildcard='*.[zrt]')
        data.sort_by_distance()

        stations  = []
        for stream in data:
            stations += [stream.station]
        origin = data.get_origin()

        print 'Processing data...\\n'
        processed_data = {}
        for key in ['body_waves', 'surface_waves']:
            processed_data[key] = data.map(process_data[key])
        data = processed_data
    else:
        data = None

    data = comm.bcast(data, root=0)


   for origin, magnitude in cross(origins, magnitudes):
        if comm.rank==0:
            print 'Reading Greens functions...\\n'
            factory = mtuq.greens_tensor.fk.GreensTensorFactory(paths.greens)
            greens = factory(stations, origin)

            print 'Processing Greens functions...\\n'
            rise_time = trapezoid_rise_time(magnitude)
            wavelet = Trapezoid(rise_time)
            greens.convolve(wavelet)

            processed_greens = {}
            for key in ['body_waves', 'surface_waves']:
                processed_greens[key] = greens.map(process_data[key])
            greens = processed_greens

        else:
            greens = None

        greens = comm.bcast(greens, root=0)


        if comm.rank==0:
            print 'Carrying out grid search...\\n'
        results = grid_search_mpi(data, greens, misfit, grid)
        results = comm.gather(results, root=0)


        if comm.rank==0:
            print 'Saving results...\\n'
            results = np.concatenate(results)
            grid.save(event_name+'.h5', {'misfit': results})


        if comm.rank==0:
            print 'Plotting waveforms...\\n'
            synthetics = {}
            for key in ['body_waves', 'surface_waves']:
                synthetics[key] = greens[key].get_synthetics(best_mt)
            plot_waveforms(event_name+'.png', data, synthetics, misfit)


"""


if __name__=='__main__':
    import os
    import re

    from mtuq.util.util import root
    os.chdir(root())


    with open('examples/GridSearch.DoubleCouple3.py', 'w') as file:
        file.write(Imports)
        file.write(DocstringDC3)
        file.write(DefinitionsPaths)
        file.write(DefinitionsDataProcessing)
        file.write(DefinitionsMisfit)
        file.write(GridDC3)
        file.write(GridSearchMPI)


    with open('examples/GridSearch.DoubleCouple5.py', 'w') as file:
        file.write(Imports)
        file.write(DocstringDC5)
        file.write(DefinitionsPaths)
        file.write(DefinitionsDataProcessing)
        file.write(DefinitionsMisfit)
        file.write(GridDC5)
        file.write(GridSearchMPIAlternate)


    with open('examples/GridSearch.FullMomentTensor5.py', 'w') as file:
        file.write(Imports)
        file.write(DocstringFMT5)
        file.write(DefinitionsPaths)
        file.write(DefinitionsDataProcessing)
        file.write(DefinitionsMisfit)
        file.write(GridFMT5)
        file.write(GridSearchMPI)


    with open('examples/GridSearch.DoubleCouple3.Serial.py', 'w') as file:
        file.write(re.sub(
            'grid_search_mpi',
            'grid_search_serial',
            Imports))
        file.write(DocstringDC3Serial)
        file.write(DefinitionsPaths)
        file.write(DefinitionsDataProcessing)
        file.write(DefinitionsMisfit)
        file.write(GridDC3)
        file.write(GridSearchSerial)


    with open('tests/integration_grid_search.py', 'w') as file:
        file.write(re.sub(
            'grid_search_mpi',
            'grid_search_serial',
            Imports))
        file.write(DocstringDC3Serial)
        file.write(DefinitionsPaths)
        file.write(DefinitionsDataProcessing)
        file.write(DefinitionsMisfit)
        file.write(GridDC3)
        file.write(re.sub(
            'wildcard=',
            'wildcard=''*BIGB''+',
            GridSearchSerial))


