import os

import numpy as np
from wrf import getvar, vinterp
from netCDF4 import Dataset

from wrfcloud.log import Logger


def derive_fields(in_file: str, out_dir: str):
    log = Logger()
    os.makedirs(out_dir, exist_ok=True)
    out_file = f"{os.path.basename(in_file).replace('wrfout', 'wrfderive')}.nc"
    out_file = os.path.join(out_dir, out_file)

    # list of dictionaries defining fields to process
    # name = input field name, out_name (optional) = field name to write
    # args (optional) = dictionary of options to add to getvar command
    # levels (optional) = If set and True, interpolate at pressure levels
    fields = [
        {'name': 'T2', 'out_name': 'temp_2m'},
        {'name': 'wspd', 'out_name': 'wind_speed_10', 'args': {'units': 'kt'}},
        {'name': 'wdir', 'out_name': 'wind_dir_10', 'args': {'units': 'kt'}},
        {'name': 'slp', 'out_name': 'prmsl'},
        {'name': 'td2', 'out_name': 'dewpt_2m', 'args': {'units': 'C'}},
        {'name': 'rh2', 'out_name': 'rh_2m'},
        {'name': 'mdbz', 'out_name': 'max_refl'},
        {'name': 'total_precip'},
        {'name': 'rh', 'out_name': 'rh_pres', 'levels': True},
        {'name': 'wspd', 'out_name': 'wind_speed_pres', 'args': {'units': 'kt'}, 'levels': True},
        {'name': 'wdir', 'out_name': 'wind_dir_pres', 'args': {'units': 'kt'}, 'levels': True},
        {'name': 'temp', 'out_name': 'temp_pres', 'args': {'units': 'C'}, 'levels': True},
        {'name': 'wa', 'out_name': 'vvel_pres', 'levels': True},
    ]
    # pressure levels to interpolate fields if levels is in fields dictionary
    interp_levels = [1000, 925, 850, 700, 500, 300, 250, 100]
    field_attrs_to_copy = ['FieldType', 'MemoryOrder', 'description', 'units', 'stagger', 'coordinates']

    try:
        with Dataset(in_file) as in_data, Dataset(out_file, mode='w') as out_data:
            # set global attributes
            out_data.setncatts(in_data.__dict__)
            # update title global attribute to note data is derived
            out_data.TITLE = f'DERIVED{out_data.TITLE}'
            # copy dimensions
            for name, dimension in in_data.dimensions.items():
                out_data.createDimension(
                    name,
                    (len(dimension) if not dimension.isunlimited() else None))

            # add interp_levels dimension and dimension variable
            out_data.createDimension('interp_level', len(interp_levels))
            interp_lev = out_data.createVariable('interp_level', np.float32, ('interp_level',))
            interp_lev.units = 'hPa'
            interp_lev.long_name = 'interpolated pressure levels'
            interp_lev[:] = interp_levels

            # add latitude, longitude, and time variables
            for name in ('XLAT', 'XLONG', 'Times'):
                var = in_data.variables[name]
                out_data.createVariable(name, var.datatype, var.dimensions)
                out_data[name][:] = in_data[name][:]
                out_data[name].setncatts(in_data[name].__dict__)

            for field in fields:
                field_name = field['name']
                out_name = field_name if 'out_name' not in field else field['out_name']
                field_args = {} if 'args' not in field else field['args']

                # compute total accum precip by adding rain c and rain nc
                if field_name.lower() == 'total_precip':
                    var1 = getvar(in_data, 'RAINNC')
                    var2 = getvar(in_data, 'RAINC')
                    var = var1 + var2
                else:
                    var = getvar(in_data, field_name, **field_args)

                # interpolate pressure levels
                if 'levels' in field and field['levels'] is True:
                    var = vinterp(in_data, field=var, vert_coord='pressure',
                                  interp_levels=interp_levels, extrapolate=True)

                # convert 2m temp to Celsius because units is not an option
                if field_name == 'T2':
                    var.values = var.values - 273.15
                    var.attrs['units'] = 'C'

                out_data.createVariable(out_name, var.dtype, var.dims)
                out_data[out_name][:] = var.values
                for attr in field_attrs_to_copy:
                    if attr in var.attrs:
                        out_data[out_name].setncattr(attr, var.attrs[attr])
    except Exception as e:
        log.error('Could not derive fields: ', e)
        return None

    return out_file
