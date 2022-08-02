"""
Module to convert WRF output to GeoJSON
"""


from typing import Union
import json
import netCDF4
from matplotlib import contour
from matplotlib import pyplot
import numpy


class GeoJson:
    """
    Class to convert WRF output to GeoJSON MultiPolygon format
    """
    def __init__(self, wrf_file: str, variable: str, z_level: Union[int, None] = None):
        """
        Construct a WRF to GeoJSON converter
        :param wrf_file: Full path to the WRF output file
        :param variable: Name of the variable in the NetCDF file to convert
        :param z_level: Height level in the to convert
        """
        self.wrf_file = wrf_file
        self.variable = variable
        self.z_level = z_level
        self.grid = None
        self.grid_lat = None
        self.grid_lon = None

    def convert(self, out_file: Union[str, None]) -> Union[None, dict]:
        """
        Convert a field in a WRF output file to GeoJSON
        :param out_file: Full path to the output file (directory must exist) or None to get the
                         GeoJSON data returned as a dictionary
        """
        # open the NetCDF file and get the requested horizontal slice
        # pylint: disable=E1101
        wrf = netCDF4.Dataset(self.wrf_file)
        data = wrf[self.variable]
        time_index = 0
        grid = data[time_index][self.z_level] if self.z_level else data[time_index]

        # get the latitude and longitude grids
        self.grid_lat = wrf['XLAT'][0]
        self.grid_lon = wrf['XLONG'][0]

        # create a set of contours from the data grid
        contours: contour.QuadContourSet = pyplot.contourf(grid)

        # create an array of contour levels, each of which contains a set of multi-polygons
        levels = []
        for contour_line in contours.collections:
            multi_polygon = []
            for path in contour_line.get_paths():
                polygon = self.polygon_to_coord_array(path.to_polygons()[0])
                holes = []
                for hole in path.to_polygons()[1:]:
                    holes.append(self.polygon_to_coord_array(hole))
                multi_polygon.append({'p': polygon, 'h': holes})
            levels.append(multi_polygon)

        # create a list of MultiPolygon features to put in the GeoJSON file
        features = []
        for (i, level) in enumerate(levels):
            # get the hex color code for this level's color
            r = ('00' + hex(int(contours.tcolors[i][0][0] * 255))[2:])[-2:]
            g = ('00' + hex(int(contours.tcolors[i][0][1] * 255))[2:])[-2:]
            b = ('00' + hex(int(contours.tcolors[i][0][2] * 255))[2:])[-2:]
            level_color = f'#{r}{g}{b}'

            # Add all the MultiPolygon features for this contour level
            for multi_polygon in level:
                polygon_string = self.polygon_and_holes_to_multi_polygon(
                    multi_polygon['p'],
                    multi_polygon['h']
                )

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [json.loads(polygon_string)]
                    },
                    "properties": {
                        "stroke-width": 0,
                        "fill": level_color,
                        "fill-opacity": 1
                    }
                }
                features.append(feature)

        # create the GeoJSON document
        doc = {
            "type": "FeatureCollection",
            "features": features
        }

        # return the document if no output file was provided
        if out_file is None:
            return doc

        # write the data to a file or return as a string if no data were
        print(f'Writing to {out_file}.')
        with open(out_file, 'w') as f:
            f.write(json.dumps(doc))
            f.flush()
            f.close()
        print('Done.')
        return None

    def grid_to_lonlat(self, x: float, y: float) -> (float, float):
        """
        Convert grid XY coordinates to longitude and latitude
        :param x: The X position on the grid
        :param y: The Y position on the grid
        :return: Longitude and latitude
        """
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

    def polygon_to_coord_array(self, polygon: numpy.ndarray) -> list[(float, float)]:
        """
        Convert a polygon contour path to a coordinate array
        """
        points = []
        for point in polygon:
            lonlat_point = self.grid_to_lonlat(point[0], point[1])
            points.append(lonlat_point)

        return points

    @staticmethod
    def polygon_and_holes_to_multi_polygon(polygon: list[list[float]], holes: list[list[list[float]]]) -> str:
        """
        Convert a polygon and zero or more holes to a GeoJSON multi-polygon coordinate string
        :param polygon: List of polygon coordinates
        :param holes: List of holes, where each hole is a list of polygon coordinates
        :return: GeoJSON-formatted MultiPolygon coordinate string
        """
        mp_str = str([[point[0], point[1]] for point in polygon])
        for hole in holes:
            mp_str += ',' + str([[point[0], point[1]] for point in hole])
        return '[' + mp_str + ']'


def main():
    """
    Command line entry point to run the converter
    """
    from argparse import ArgumentParser
    from argparse import ArgumentDefaultsHelpFormatter as HelpFormatter

    # parse the command line parameters
    parser = ArgumentParser(description='Convert WRF to GeoJSON format', formatter_class=HelpFormatter)
    parser.add_argument('--in-file', type=str, help='Full path to the WRF file', required=True)
    parser.add_argument('--out-file', type=str, help='Full path to the output file', required=False)
    parser.add_argument('--variable', type=str, help='Variable name from the WRF file', required=True)
    parser.add_argument('--z-level', type=int, help='Z-level if a 3D field', required=False)
    args = parser.parse_args()

    # get the command line parameters
    wrf_file = args.in_file
    out_file = args.out_file or None
    variable = args.variable
    z_level = args.z_level or None

    # convert the WRF data to GeoJSON
    converter = GeoJson(wrf_file, variable, z_level)
    output = converter.convert(out_file)

    # print the output to stdout if we do not have an output file
    if output is not None:
        print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()
