"""
Module to convert WRF output to JSON containing vector info, e.g. wind
"""
import os
import pkgutil
from concurrent.futures import ProcessPoolExecutor, wait
from typing import Union, List
from gzip import compress
import json
from argparse import ArgumentParser
import yaml
import netCDF4
from numpy.ma.core import MaskedArray
from datetime import datetime

from wrfcloud.jobs.job import WrfLayer
from wrfcloud.log import Logger
from wrfcloud.system import init_environment


class VectorJson:
    """
    Class to convert WRF output to JSON vector format
    """

    def __init__(self, wrf_file: str, variable: str, input_variables: dict,
                 z_level: Union[int, None] = None):
        """
        Construct a WRF to vector JSON converter
        :param wrf_file: Full path to the WRF output file
        :param variable: Name of the variable to create
        :param input_variables: Dictionary of input var names in the NetCDF file
        :param z_level: Height level in the to convert
        """
        self.log = Logger(self.__class__.__name__)
        self.wrf_file = wrf_file
        self.variable = variable
        self.input_variables = input_variables
        self.z_level = z_level
        self.grid = None
        self.grid_lat = None
        self.grid_lon = None
        self.time_step = 0

    def convert(self, out_file: Union[str, None]) -> Union[None, dict]:
        """
        Convert a field in a WRF output file to vector JSON
        :param out_file: Full path to the output file (directory must exist) or
         None to get the vector JSON data returned as a dictionary
        """
        # log status info
        self.log.info(f'Converting {self.variable} to {out_file}')

        try:
            # get the data, lat, and lon grids of each field
            grids = {}
            for var_id, var_name in self.input_variables.items():
                grid, grid_lat, grid_lon = self._read_var_from_netcdf(var_name)
                grids[var_id] = grid
                # save grid lat/lon arrays and ensure they match
                if self.grid_lat is None or self.grid_lon is None:
                    self.grid_lat, self.grid_lon = grid_lat, grid_lon
                else:
                    assert len(self.grid_lat) == len(grid_lat)
                    assert len(self.grid_lon) == len(grid_lon)

            # loop through grid points and create vector JSON file
            items = []
            first_field = list(grids.keys())[0]
            for y, row in enumerate(grids[first_field]):
                for x in range(0, len(row)):
                    lon, lat = self._grid_to_lonlat(x, y)
                    item = {'coord': {'lon': str(lon), 'lat': str(lat)},
                            self.variable: {}}
                    for field, grid in grids.items():
                        item[self.variable][field] = str(grid[y][x])
                    items.append(item)
            doc = {'vectors': items}

            # return the document if no output file was provided
            if out_file is None:
                return doc

            # write the data to a file or return as a string if no data were
            with open(out_file, 'wb') as file:
                file.write(compress(json.dumps(doc).encode()))
                file.flush()
                file.close()
        except Exception as e:
            self.log.error(f'Exception occurred trying to create {out_file}: {e}')

        return None

    def _read_var_from_netcdf(self, variable: str) -> (MaskedArray, MaskedArray, MaskedArray):
        """
        Read the variable data, latitude, and longitude grids from a NetCDF file
        :return: data, latitude, longitude
        """
        # open the NetCDF file and get the requested horizontal slice
        # pylint thinks that the Dataset class does not exist in netCDF4 pylint: disable=E1101
        wrf = netCDF4.Dataset(self.wrf_file)
        data = wrf[variable]
        time_index = 0
        grid = data[:] if data.dimensions[0] != 'Time' else data[time_index]
        if self.z_level:
            z_index = None
            for idx, z_val in enumerate(wrf[data.dimensions[0]]):
                if int(z_val) == self.z_level:
                    z_index = idx
            if z_index is None:
                self.log.error(f'Could not find z level: {self.z_level}')
            grid = grid[z_index]

        # get the latitude and longitude grids
        grid_lat = wrf['XLAT'][0]
        grid_lon = wrf['XLONG'][0]

        return grid, grid_lat, grid_lon

    def _grid_to_lonlat(self, x: float, y: float) -> (float, float):
        """
        Convert grid XY coordinates to longitude and latitude
        :param x: The X position on the grid
        :param y: The Y position on the grid
        :return: Longitude and latitude
        """
        # TODO: move this to common area since it is here and geojson.py
        # get the integer grid indices
        x1 = int(x)
        y1 = int(y)
        x2 = int(x) + 1 if x1 != round(x, 5) else x1
        y2 = int(y) + 1 if y1 != round(y, 5) else y1

        # get bounding lat/lon values for a linear interpolation
        lat1 = self.grid_lat[y1][x1]
        lon1 = self.grid_lon[y1][x1]
        lat2 = self.grid_lat[y2][x2]
        lon2 = self.grid_lon[y2][x2]

        # get the x and y grid value fractions for a linear interpolation
        x_frac = x - x1
        y_frac = y - y1

        # compute lat/lon values with a linear interpolation
        lat = lat1 + ((lat2 - lat1) * y_frac)
        lon = lon1 + ((lon2 - lon1) * x_frac)

        return round(lon, 5), round(lat, 5)


def main():
    """
    Command line entry point to run the converter
    """
    # initialize the CLI environment
    init_environment('cli')

    # parse the command line parameters
    parser = ArgumentParser(description='Convert WRF (netCDF or GRIB2) to vector JSON format')
    parser.add_argument('--in-file', type=str, help='Full path to the WRF file', required=True)
    parser.add_argument('--out-file', type=str, help='Full path to the output file', required=False)
    parser.add_argument('--variable', type=str, help='Variable from the WRF file, required if auto not set', required=False)
    parser.add_argument('--wind_speed', type=str, help='Variable name of wind speed, required if creating wind variable', required=False)
    parser.add_argument('--wind_dir', type=str, help='Variable name of wind direction, required if creating wind variable', required=False)
    parser.add_argument('--z-level', type=int, help='Z-level if a 3D field', required=False)
    parser.add_argument('--auto', help='Automatically creates full output set', required=False, action='store_true')
    args = parser.parse_args()

    # get the command line parameters
    wrf_file = args.in_file
    out_file = args.out_file or None
    variable = args.variable
    z_level = args.z_level or None
    auto = args.auto

    input_vars = {}
    if variable == 'wind':
        input_vars['speed'] = args.wind_speed or None
        input_vars['direction'] = args.wind_dir or None
        if None in input_vars:
            print('ERROR: Must set --wind_speed and --wind_dir if setting --variable wind')
            return
    else:
        print('ERROR: Invalid value set for --variable')
        return

    # select mode and convert the WRF data to GeoJSON
    if not auto:
        _manual_product(wrf_file, out_file, variable, input_vars, z_level)
    else:
        automate_vector_products(wrf_file)


def _manual_product(wrf_file: str, out_file: Union[str, None], variable: str,
                    input_vars: dict, z_level: Union[int, None]) -> None:
    """
    Generate a single product defined by manual CLI inputs
    :param wrf_file: Input file name
    :param out_file: Output file name or None if stdout is desired
    :param variable: Variable to extract
    :param input_vars: Dictionary of input var names in the file
    :param z_level: Vertical level to export, or None if a 2D variable
    """
    # convert the WRF data to vector JSON
    converter = VectorJson(wrf_file, variable, input_vars, z_level)
    output = converter.convert(out_file)

    # print the output to stdout if we do not have an output file
    if output is not None:
        print(json.dumps(output, indent=2))


def automate_vector_products(wrf_file: str) -> List[WrfLayer]:
    """
    Generate all the products defined in the vector_products.yaml file
    :param wrf_file: Input file name
    :return: List of JSON output files
    """
    log = Logger()

    # load the product list from the yaml file
    products_data = pkgutil.get_data('wrfcloud', 'runtime/resources/vector_products.yaml')
    products = yaml.safe_load(products_data)['products']

    # create a process pool for concurrent execution
    ppe = ProcessPoolExecutor(max_workers=8)
    futures = []

    # create each product
    out_layers: List[WrfLayer] = []
    for product in products:
        z_levels = product['z_levels'] if 'z_levels' in product else [None]
        if 'wind' in product:
            variable = 'wind'
            input_vars = {
                'speed': product['wind'].get('speed'),
                'direction': product['wind'].get('direction'),
            }
            if None in input_vars.values():
                log.error('speed and direction must be set for wind vector product')
                continue
        else:
            log.error('Invalid vector product in vector_products.yaml. '
                      'Supported types: wind')
            continue

        for z_level in z_levels:
            # create the output file name
            out_file = (f'{wrf_file}_{variable}' if z_level is None else f'{wrf_file}_{variable}_{z_level}')
            out_file += '.json.gz'

            # create the WRF Layer details for this output product
            wrf_layer = WrfLayer()
            wrf_layer.plot_type = 'vector'
            wrf_layer.variable_name = variable if z_level is None else f'{variable}_3d'
            wrf_layer.display_name = product['display_name']
            wrf_layer.layer_data = out_file
            wrf_layer.z_level = z_level

            # TODO: pull out into function to call hera and geojson.py
            with netCDF4.Dataset(wrf_file) as wrf_nc:
                file_time = wrf_nc['Times'][:].tobytes().decode()
                dt = datetime.strptime(file_time, '%Y-%m-%d_%H:%M:%S')
                wrf_layer.dt = dt.timestamp()

            out_layers.append(wrf_layer)

            # convert the file if it does not already exist
            if not os.path.exists(out_file):
                converter = VectorJson(wrf_file, variable, input_vars, z_level)
                future = ppe.submit(converter.convert, out_file)
                futures.append(future)

    wait(futures)

    # remove any layers if the file does not exist
    existing_layers = []
    for layer in out_layers:
        if os.path.exists(layer.layer_data):
            existing_layers.append(layer)
        else:
            log.error(f'Layer does not exist: {layer.layer_data}')

    return existing_layers


if __name__ == '__main__':
    main()
