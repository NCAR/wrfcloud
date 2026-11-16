import {Palette as ColorsPalette, intToHex} from '@ncar/colors';
import {Palette} from '../client-api';

/** Palette colors by name, so the colors package is asked once per palette (and warns once about an unknown name) */
const paletteCache: Map<string, number[][]|undefined> = new Map();


/**
 * Get a palette's colors by name from the NCAR colors package (a '-inv' suffix reverses the palette)
 *
 * @param name Palette name
 * @returns A list of RGB triples, or undefined if there is no such palette
 */
export function paletteColors(name: string): number[][]|undefined
{
  if (!paletteCache.has(name))
    paletteCache.set(name, new ColorsPalette(name).colorValues ?? undefined);
  return paletteCache.get(name);
}


/**
 * Get the number of contour levels the same way the backend does: range(int(min*10), int(max*10), int(interval*10))
 */
export function contourLevelCount(min: number, max: number, interval: number): number
{
  const start: number = Math.trunc(min * 10);
  const stop: number = Math.trunc(max * 10);
  const step: number = Math.trunc(interval * 10);
  return step > 0 ? Math.max(0, Math.ceil((stop - start) / step)) : 0;
}


/**
 * Get the value to label the high end of the legend with. The backend's max_value is an exclusive upper limit for the contour levels,
 * so with a contour interval the highest level actually drawn is label-worthy instead (49.5, not 49.6)
 *
 * @param palette Palette details from the layer
 * @returns The highest contour level, or max_value if there is no contour interval
 */
export function legendMax(palette: Palette): number
{
  /* explicit levels: the highest one */
  if (palette.levels && palette.levels.length > 0)
    return palette.levels[palette.levels.length - 1];

  if (!palette.contour_interval)
    return palette.max_value;

  const count: number = contourLevelCount(palette.min_value, palette.max_value, palette.contour_interval);
  if (count < 1)
    return palette.max_value;

  /* levels have 0.1 resolution, so round away floating point noise such as 46.79999999999999 */
  return Math.round((palette.min_value + (count - 1) * palette.contour_interval) * 10) / 10;
}


/**
 * Build the CSS background for a layer's color legend.
 *
 * With a contour interval or explicit levels the legend has one solid band per map color, matching the polygons drawn on the map
 * (the backend draws one extra region below the minimum and one above the last level, which are not part of the bar).
 * Without one it is a smooth gradient of the palette's colors.
 *
 * @param palette Palette details from the layer
 * @returns A CSS background-image value, or null if the palette is unknown (use the palette-<name> CSS class instead)
 */
export function legendGradient(palette: Palette): string|null
{
  const colors: number[][]|undefined = paletteColors(palette.palette_name);
  if (colors === undefined)
    return null;
  const base: ColorsPalette = new ColorsPalette();
  base.colorValues = colors;

  /* number of contour levels on the map: an explicit list, or evenly spaced levels from the range and interval */
  const levelCount: number = palette.levels ? palette.levels.length :
    (palette.contour_interval ? contourLevelCount(palette.min_value, palette.max_value, palette.contour_interval) : 0);
  if (levelCount === 0)
    return `linear-gradient(90deg, ${colors.map(intToHex).join(', ')})`;

  /* one color per map region, then drop the under and over regions, which are not part of the bar */
  const regions: number[][] = base.interpolate(levelCount + 1).colorValues!;
  const bands: ColorsPalette = new ColorsPalette();
  bands.colorValues = regions.length > 2 ? regions.slice(1, -1) : regions;
  return bands.getLinearGradient();
}


/**
 * A labeled tick on the legend bar
 */
export interface LegendTick
{
  /** Position along the bar, 0 to 100 percent */
  pos: number;
  /** Text to show */
  label: string;
}


/** Most tick labels to show along a legend bar */
const MAX_TICKS: number = 7;


/**
 * Get the contour levels the same way the backend does: the explicit list, or range(int(min*10), int(max*10), int(interval*10)) / 10
 *
 * @param palette Palette details from the layer
 * @returns The contour levels, or an empty list if the palette has neither levels nor a contour interval
 */
export function legendLevels(palette: Palette): number[]
{
  if (palette.levels && palette.levels.length > 0)
    return palette.levels;

  if (!palette.contour_interval)
    return [];

  const start: number = Math.trunc(palette.min_value * 10);
  const step: number = Math.trunc(palette.contour_interval * 10);
  const count: number = contourLevelCount(palette.min_value, palette.max_value, palette.contour_interval);
  return Array.from({length: count}, (_, k) => (start + k * step) / 10);
}


/**
 * Get the labeled ticks for a layer's color legend.
 *
 * The bar draws one equal-width band between each pair of neighboring contour levels (see legendGradient), so level k sits at
 * k / (number of levels - 1) along the bar even when the levels themselves are unevenly spaced. When there are too many levels to
 * label, every n-th one is labeled and the highest level is always labeled.
 *
 * @param palette Palette details from the layer
 * @returns The ticks from low to high, or an empty list if the legend is a smooth gradient with no levels (label only min and max)
 */
export function legendTicks(palette: Palette): LegendTick[]
{
  const levels: number[] = legendLevels(palette);
  if (levels.length < 2 || paletteColors(palette.palette_name) === undefined)
    return [];

  /* pick every n-th level, the smallest n that fits the label limit */
  const last: number = levels.length - 1;
  let step: number = 1;
  while (Math.floor(last / step) + 1 + (last % step === 0 ? 0 : 1) > MAX_TICKS)
    step++;

  const indexes: number[] = [];
  for (let i = 0; i <= last; i += step)
    indexes.push(i);

  /* always label the highest level, replacing the previous label if it would crowd it */
  if (indexes[indexes.length - 1] !== last)
  {
    if (last - indexes[indexes.length - 1] < step * 0.6)
      indexes.pop();
    indexes.push(last);
  }

  return indexes.map(i => ({pos: i / last * 100, label: String(Math.round(levels[i] * 10) / 10)}));
}
