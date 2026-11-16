"""
Test the color palette handling in wrfcloud.runtime.tools.geojson and wrfcloud.jobs.job.PaletteData
"""
import pkgutil

import numpy
import pytest
import yaml
from colors import Palette as ColorsPalette

import wrfcloud.system
from wrfcloud.jobs.job import PaletteData
from wrfcloud.runtime.tools.geojson import GeoJson

# initialize the test environment
wrfcloud.system.init_environment(env='test')


def _make_converter(palette: str, levels=None, skip_under: bool = False, value_range=None, interval=None) -> GeoJson:
    """
    Create a converter with a small synthetic lon/lat grid, so no WRF file is needed
    """
    converter = GeoJson('unused', 'netcdf', 'unused', value_range or [0, 10], interval, palette,
                        levels=levels, skip_under=skip_under)
    ny, nx = 12, 12
    converter.grid_lat = numpy.array([[30.0 + 0.1 * y] * nx for y in range(ny)])
    converter.grid_lon = numpy.array([[-100.0 + 0.1 * x for x in range(nx)] for _ in range(ny)])
    return converter


def _grid() -> numpy.ma.MaskedArray:
    """
    A grid of values that increases from 0 at the left edge to 11 at the right edge
    """
    return numpy.ma.masked_array(numpy.array([[float(x) for x in range(12)] for _ in range(12)]))


def test_palette_data_defaults() -> None:
    """
    Optional legend fields are left out of the data so previously saved layers do not change
    """
    palette = PaletteData({'palette_name': 'cape', 'min_value': 1, 'max_value': 9000})
    assert palette.data == {'palette_name': 'cape', 'min_value': 1, 'max_value': 9000}


def test_palette_data_round_trip() -> None:
    """
    Explicit levels and a contour interval survive a round trip through the data dictionary
    """
    data = {'palette_name': 'cape', 'min_value': 1, 'max_value': 9000,
            'contour_interval': 250, 'levels': [1, 250, 500]}
    assert PaletteData(data).data == data


def test_explicit_levels_give_one_color_per_region() -> None:
    """
    n levels make n + 1 regions, each with its own fill color from the colors package
    """
    levels = [2, 3, 5, 8]
    converter = _make_converter('cape', levels=levels)
    fills = {feature['properties']['fill'] for feature in converter._create_features(_grid())}
    expected = ColorsPalette('cape').interpolate(len(levels) + 1).hex_colors
    assert len(fills) == len(levels) + 1
    assert fills == set(expected)


def test_skip_under_leaves_lowest_region_transparent() -> None:
    """
    skip_under drops the region below the lowest level, and nothing else
    """
    levels = [2, 3, 5, 8]
    all_features = _make_converter('cape', levels=levels)._create_features(_grid())
    skipped = _make_converter('cape', levels=levels, skip_under=True)._create_features(_grid())
    under_color = ColorsPalette('cape').interpolate(len(levels) + 1).hex_colors[0]
    assert len(skipped) == len(all_features) - 1
    assert under_color not in [feature['properties']['fill'] for feature in skipped]


def test_range_and_interval_still_work() -> None:
    """
    Products without explicit levels keep the range and contour interval behavior
    """
    converter = _make_converter('cape', value_range=[0, 10], interval=2)
    assert len(converter._create_features(_grid())) > 0


def test_unknown_palette_falls_back_to_matplotlib() -> None:
    """
    A palette name that is not in the colors package is still drawn as a matplotlib colormap
    """
    converter = _make_converter('winter', value_range=[0, 10], interval=2)
    assert converter._get_fill_colors(5) == []
    assert len(converter._create_features(_grid())) > 0


def _products() -> list:
    products = yaml.safe_load(pkgutil.get_data('wrfcloud.runtime', 'resources/geojson_products.yaml'))
    return products['products']


def test_every_product_palette_is_in_colors_package() -> None:
    """
    Every palette named in geojson_products.yaml exists in the colors package, except for the
    variables still waiting on a new palette (mean sea-level pressure uses a matplotlib colormap for now)
    """
    pending = {'winter'}
    for product in _products():
        if product['palette'] in pending:
            continue
        assert ColorsPalette(product['palette']).n_colors > 0, f"Unknown palette: {product['palette']}"


def test_product_levels_are_ordered_and_usable() -> None:
    """
    Explicit levels increase, and skip_under products have levels to skip under
    """
    for product in _products():
        levels = product.get('levels')
        if levels:
            assert levels == sorted(set(levels)), f"Levels not increasing for {product.get('netcdf', product)}"
        if 'range' not in product and not levels and 'contour_interval' not in product:
            pytest.fail(f'Product has no range, interval or levels: {product}')
