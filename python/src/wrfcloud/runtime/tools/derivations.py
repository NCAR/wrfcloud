import os
import pkgutil

import numpy as np
# pylint: disable=E0401
from wrf import getvar, vinterp
# pylint: disable=E0401,E0611
from netCDF4 import Dataset
import yaml

from wrfcloud.log import Logger


def derive_fields(in_file: str, out_dir: str):
    """
    Convert units (K to C, gpm to dam, etc.) and derive WRF fields (wind speed
    and direction).
    :param in_file: WRF NetCDF file to process
    :param out_dir: Directory to write derived output file
    """
    log = Logger()
    os.makedirs(out_dir, exist_ok=True)
    out_file = f"{os.path.basename(in_file).replace('wrfout', 'wrfderive')}.nc"
    out_file = os.path.join(out_dir, out_file)

    # read derivation info from YAML file
    derivation_data = pkgutil.get_data('wrfcloud', 'runtime/resources/derive_products.yaml')
    derive_yaml = yaml.safe_load(derivation_data)
    fields = derive_yaml['fields']
    interp_levels = derive_yaml['interp_levels']
    field_attrs_to_copy = derive_yaml['field_attrs_to_copy']

    try:
        with Dataset(in_file) as in_data, Dataset(out_file, mode='w') as out_data:
            # set global attributes
            out_data.setncatts(in_data.__dict__)
            # update title global attribute to note data is derived
            out_data.TITLE = f'DERIVED{out_data.TITLE}'
            # copy dimensions
            for name, dimension in in_data.dimensions.items():
                dim = len(dimension) if not dimension.isunlimited() else None
                out_data.createDimension(name, dim)

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
                # use name as output name if out_name is not set
                out_name = field_name if 'out_name' not in field else field['out_name']
                # add optional arguments to wrf-python getvar function
                field_args = {} if 'args' not in field else field['args']

                # compute total accum precip by adding rain c and rain nc
                if field_name.lower() == 'total_precip':
                    var1 = getvar(in_data, 'RAINNC')
                    var2 = getvar(in_data, 'RAINC')
                    var = var1 + var2
                else:
                    var = getvar(in_data, field_name, **field_args)

                # interpolate fields to pressure levels if requested
                if 'levels' in field and field['levels'] is True:
                    var = vinterp(in_data, field=var, vert_coord='pressure',
                                  interp_levels=interp_levels, extrapolate=True)

                # convert 2m temp to C because units is not an option for T2
                if field_name == 'T2':
                    var.values = var.values - 273.15
                    var.attrs['units'] = 'C'

                # scale values if requested
                if 'scale' in field:
                    var.values = var.values * field['scale']

                # create output variable, copy values and select attributes
                out_data.createVariable(out_name, var.dtype, var.dims)
                out_data[out_name][:] = var.values
                for attr in field_attrs_to_copy:
                    if attr in var.attrs:
                        out_data[out_name].setncattr(attr, var.attrs[attr])
    except Exception as e:
        log.error('Could not derive fields: ', e)
        return None

    return out_file
