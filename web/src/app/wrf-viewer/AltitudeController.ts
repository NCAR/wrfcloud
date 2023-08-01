/**
 * The abstract base class for GUI widgets that allow the user to select an altitude.
 * This class notifies listeners that implement a altitudeChanged() function when
 * a new altitude has been selected
 * @constructor
 * @memberof ral.controller
 *
 * @param {object} options the options object
 * @param {string} options.target Required. The id of the target element to append to
 * @param {string} options.units Required. The unit string for the altitude controller units
 * @param {number} options.minAlt Required if options.altitudes is undefined. The minimum selectable altitude.
 * @param {number} options.maxAlt Required if options.altitudes is undefined. The maximum selectable altitude.
 * @param {number} options.step Required if options.altitudes is undefined. The step size between min and max altitudes
 * @param {array} options.altitudes Optional. A list of altitude values to choose from.
 * @param {number} options.defaultAlt Required. The default selected altitude
 * @param {array} options.listeners Optional. A list of objects that listen to events fired by this controller.
 */
export class AltitudeController
{
  private target: string;
  private readonly units: string;
  private selectedAltitude: number;
  private readonly minAlt: number = 0;
  private readonly maxAlt: number = 0;
  private readonly step: number = 1;
  private altitudes: number[];
  private listeners: any[];
  private slider: any;
  private includeUpDown: boolean;
  private labelPosition: string;


  /**
   * Construct the altitude controller
   * @param options
   */
  constructor(options: AltitudeControllerOptions)
  {
    this.labelPosition = "top";
    this.slider = null;
    this.includeUpDown = false;

    if ('labelPosition' in options)
    {
      this.labelPosition = options.labelPosition;
    }
    if ('includeUpDown' in options)
    {
      this.includeUpDown = options.includeUpDown;
    }

    // required options
    this.target = options.target;
    this.units = options.units;
    this.selectedAltitude = options.defaultAlt;

    // get either the altitude steps, or create them
    if (options.altitudes === undefined)
    {
      this.minAlt = options.minAlt;
      this.maxAlt = options.maxAlt;
      this.step = options.step;

      this.altitudes = [];

      if (this.minAlt < this.maxAlt)
      {
        for (let i = this.minAlt; i <= this.maxAlt; i += this.step)
        {
          this.altitudes.push(i);
        }
      } else
      {
        for (let i = this.minAlt; i >= this.maxAlt; i -= this.step)
        {
          this.altitudes.push(i);
        }
      }
    } else
    {
      this.altitudes = options.altitudes;
    }

    // OPTIONAL
    if (typeof options.listeners !== "undefined")
    {
      this.listeners = options.listeners;
    } else
    {
      this.listeners = []
    }

    this.initView();
  }

  /**
   * Initialize the GUI components
   * @abstract
   */
  public initView(): void
  {}

  /**
   * Get the currently selected altitude
   * @return {number} the currently selected altitude
   */
  public getSelectedAltitude(): number
  {
    return this.selectedAltitude;
  }

  /**
   * Get the units string for the altitude values
   * @return {string} The altitude units string
   */
  public getAltitudeUnits(): string
  {
    return this.units;
  }


  /**
   * Set the selected altitude and notify all listeners
   * @param {number} altitude The new altitude
   * @param {boolean} updateSlider
   */
  public setSelectedAltitude(altitude: number, updateSlider: boolean): void
  {
    this.selectedAltitude = altitude;

    if (updateSlider)
    {
      let index = -1;
      for (let i = 0; i < this.altitudes.length; i++)
      {
        if (this.altitudes[i] === this.selectedAltitude)
        {
          index = i;
          break;
        }
      }
      if (index >= 0)
      {
        this.slider.slider('value', index);
      }
    }

    this.fireAltitudeChangedEvent();
  }

  /**
   * Notify listeners that the altitude has changed
   * @private
   */
  public fireAltitudeChangedEvent()
  {
    for (let i = 0; i < this.listeners.length; i++)
    {
      if (this.listeners[i].hasOwnProperty('altitudeChanged'))
      {
        this.listeners[i].altitudeChanged({value: this.getSelectedAltitude(), units: this.getAltitudeUnits()});
      }
    }
  }

  /**
   * Add a single listener
   * @param {Object} listener The listener object
   */
  public addListener(listener: Function): void
  {
    if (typeof listener === "undefined" || listener === null)
      return;

    this.listeners.push(listener);
  }

  /**
   * Remove a single listener.
   * @public
   *
   * @param listener {Function} Listener to remove from the set of listeners.
   */
  public removeListener(listener: Function): void
  {
    for (let i = 0; i < this.listeners.length; i++)
    {
      if (this.listeners[i] == listener)
      {
        this.listeners.splice(i, 1);
      }
    }
  }

  /**
   * Remove all listeners
   * @public
   */
  public removeAllListeners(): void
  {
    this.listeners = [];
  }


  /**
   * Updates the altitudes with the given altitudes, preserving the selected altitude, if possible.
   *
   * @param altitudes an Array of altitudes to replace the current altitudes
   */
  public update(altitudes: number[]): void
  {
    this.altitudes = altitudes;
    this.initView();
  }
}


export interface AltitudeControllerOptions
{
  labelPosition: string;
  includeUpDown: boolean;
  target: string;
  units: string;
  defaultAlt: number;
  minAlt: number;
  maxAlt: number;
  step: number;
  altitudes?: number[];
  listeners?: any[];
}

