
import os
import sys
import numpy as np
import mtuq.io
import mtuq.greens.fk
import mtuq.misfit

from os.path import join
from mtuq.grid_search import grid_search_serial
from mtuq.grids import DCGridRandom
from mtuq.misfit import cap_bw, cap_sw
from mtuq.process_data import process_data
from mtuq.util.cap import parser
from mtuq.util.util import Struct, root
from mtuq.util.wavelets import trapezoid


# eventually we need to include sample data in the mtuq repository;
# file size prevents us from doing so right away
paths = Struct({
    'data': join(root(), 'tests/data/20090407201255351'),
    'weights': join(root(), 'tests/data/20090407201255351/weight.dat'),
    'greens': os.getenv('CENTER1')+'/'+'data/wf/FK_SYNTHETICS/scak',
    })

data_format = 'sac'


# body and surface waves are processed separately
process_bw = process_data(
    filter_type='Bandpass',
    freq_min= 0.25,
    freq_max= 0.667,
    window_length=15.,
    #window_type='cap_bw',
    )

process_sw = process_data(
    filter_type='Bandpass',
    freq_min=0.025,
    freq_max=0.0625,
    window_length=150.,
    #window_type='cap_sw',
    )

process_data = {
   'body_waves': process_bw,
   'surface_waves': process_sw,
   }


# total misfit is a sum of body- and surface-wave contributions
misfit_bw = cap_bw(
    max_shift=2.,
    weights=parser(paths.weights)
    )

misfit_sw = cap_sw(
    max_shift=10.,
    weights=parser(paths.weights)
    )

misfit = {
    'body_waves': misfit_bw,
    'surface_waves': misfit_sw,
    }

# search over 50,000 randomly-chosen double-couple moment tensors
grid = DCGridRandom(
    npts=50000,
    Mw=4.5,
    )


if __name__=='__main__':
    """ Carries out grid search over double-couple moment tensor parameters,
       keeping magnitude, depth, and location fixed
    """
    data = mtuq.io.read(data_format, paths.data, wildcard='*.[zrt]')
    origin = mtuq.io.get_origin(data_format, data)
    stations = mtuq.io.get_stations(data_format, data)

    print 'Processing data...\n'
    processed_data = {}
    for key in process_data:
        processed_data[key] = data.map(process_data[key], stations)

    print 'Reading Greens functions...\n'
    generator = mtuq.greens.fk.Generator(paths.greens)
    greens = generator(stations, origin)
    #greens.convolve(trapezoid(rise_time=1., delta=0.2))

    print 'Processing Greens functions...\n'
    processed_greens = {}
    for key in process_data:
        processed_greens[key] = greens.map(process_data[key], stations)

    print 'Carrying out grid search...\n'
    grid_search_serial(processed_data, processed_greens, misfit, grid)


