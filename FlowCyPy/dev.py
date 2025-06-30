import numpy as np
import pandas as pd
from FlowCyPy import units
from PyMieSim import experiment
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from FlowCyPy.triggering_system import DynamicWindow
from typing import Union, Sequence, Optional

import numpy as np
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from typing import Optional, Sequence, Union
import pandas as pd
import itertools
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.population import Sphere
from FlowCyPy import (
    peak_locator,
    GaussianBeam,
    ScattererCollection,
    SignalDigitizer,
    Detector,
    TransimpedanceAmplifier,
    FlowCytometer
)

def regression_for_J(dataframe: pd.DataFrame, diameter: float) -> tuple:
    """
    Extracts the calibration slope J from the relationship between the robust
    coefficient of variation (rCV) and the inverse square root of the median
    signal for a specified bead diameter.

    In scenarios where photon (shot) noise dominates, the robust CV (rCV) should
    vary approximately as 1/sqrt(median signal). By performing a linear regression on
    the plot of rCV versus 1/sqrt(median signal), the slope obtained (J) represents the
    calibration factor that links these two quantities.

    Parameters:
        dataframe (pd.DataFrame): A DataFrame containing at least the columns 'SignalMedian' and 'rCV'. The DataFrame should have a MultiIndex with one level labeled 'BeadDiameter' indicating bead diameters.
        bead_diameter (float): The bead diameter (in nanometers) for which to perform the regression.

    Returns:
        J_fit (float): The slope of the linear regression (calibration factor J).
        inv_sqrt_signal (np.ndarray): The independent variable (1/sqrt of median signal values).
        rCV_values (np.ndarray): The dependent variable (rCV values).
    """
    # Extract the subset of data for the specified bead diameter using the MultiIndex level 'BeadDiameter'
    bead_data = dataframe.xs(diameter, level='BeadDiameter')

    # Get the median signal values from the data and compute their inverse square roots
    median_signal = bead_data['SignalMedian'].values
    inv_sqrt_signal = 1 / np.sqrt(median_signal)

    # Extract the robust coefficient of variation (rCV) values
    rCV_values = bead_data['rCV'].values

    # Perform a linear regression (degree-1 polynomial fit) on (inv_sqrt_signal, rCV_values)
    # This fit gives us the slope J (assuming a zero intercept)
    J_fit = np.polyfit(inv_sqrt_signal, rCV_values, deg=1)[0]

    return J_fit, inv_sqrt_signal, rCV_values


def regression_for_K(dataframe: pd.DataFrame, power: float) -> tuple:
    """
    Extracts the calibration slope K from the relationship between the scattering
    cross section (Csca) and the median background-corrected signal across different
    bead sizes at a fixed illumination power.

    The idea is that the measured median signal (in arbitrary units) is assumed to be
    proportional to the bead's scattering cross section (Csca, in nm²). Thus, by performing
    a linear regression (with zero intercept) of Csca versus the median signal, the slope (K)
    serves as the conversion factor between the measured signal and the known scattering
    cross section.

    Parameters:
        dataframe (pd.DataFrame): A DataFrame that contains data for different illumination powers and bead sizes.
        illumination_power (float): The specific illumination power (e.g., in mW) for which the regression is performed.

    Returns:
        K_fit (float): The estimated slope from the regression, representing the conversion factor.
        median_signals (np.ndarray): An array of background-corrected median signals for each bead size.
        sigma_values (np.ndarray): An array of scattering cross section values (Csca) corresponding to each bead size.
    """
    # Select the data corresponding to the desired illumination power.
    bead_data_at_power = dataframe.loc[power]

    # Extract the median signals and scattering cross section values.
    median_signals = bead_data_at_power['SignalMedian'].values
    sigma_values = bead_data_at_power['Csca'].values

    # Perform a linear regression (with zero intercept) on the data.
    # The regression equation is: sigma_values = K * median_signals,
    # so we extract the slope K.
    K_fit = np.polyfit(median_signals, sigma_values, deg=1)[0]

    return K_fit, median_signals, sigma_values

class NameSpace():
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)


    def __repr__(self):
        output = ""
        for k, v in self.kwargs.items():
            output += f"{k} \t\t {v}\n"

        return output

    def __str__(self):
        return self.__repr__()

def compute_robust_stats(data):
    """
    Computes robust statistics from an array of event signals.
    Uses the 84.13th and 15.87th percentiles to compute a robust standard deviation.

    Parameters:
        data (ndarray): 1D array of event signals.

    Returns:
        median (float): Median of the data.
        rSD (float): Robust standard deviation.
        rCV (float): Robust coefficient of variation (rSD/median).
    """
    median = np.median(data)
    perc84 = np.percentile(data, 84.13)
    perc15 = np.percentile(data, 15.87)
    robust_standard_deviation = (perc84 - perc15) / 2.0
    robust_coefficient_of_variation = robust_standard_deviation / median if median != 0 else np.nan

    standard_deviation = np.std(data)
    coefficient_of_variation = standard_deviation / median if median != 0 else np.nan

    return NameSpace(
        median=median,
        robust_coefficient_of_variation=robust_coefficient_of_variation,
        robust_standard_deviation=robust_standard_deviation,
        standard_deviation=standard_deviation,
        coefficient_of_variation=coefficient_of_variation,
        mean=np.mean(data)
    )

def add_background_to_dataframe(dataframe, gain, detection_efficiency, background_level, powers, N_events):
    """
    Simulates background-only events at a given illumination power.

    Parameters:
        power (float): IlluminationPower power in mW.
        detection_efficiency (float): Detection efficiency at the given power.
        gain (float): Gain factor.
        background_level (float): Background level (in nm² units).
        N_events (int): Number of events to simulate.
    """
    df = dataframe.unstack('BeadDiameter')

    for power in powers:
        Q = detection_efficiency * (power / 20)

        bg_mean = gain * Q * background_level

        bg_events = np.random.poisson(lam=bg_mean, size=N_events)

        df.loc[power] = np.median(bg_events)

    return df.stack('BeadDiameter', future_stack=True).reset_index().set_index(['IlluminationPower', 'BeadDiameter'])

def add_Csca_to_dataframe(dataframe, wavelength, diameters: list):
    source = experiment.source.Gaussian(
        NA=0.3 * units.RIU,
        wavelength=wavelength * units.nanometer,
        polarization=0 * units.degree,
        optical_power=5 * units.milliwatt
    )

    sphere = experiment.scatterer.Sphere(
        diameter=diameters * units.nanometer,
        medium_property=1.0 * units.RIU,
        property=1.4 * units.RIU,
        source=source
    )

    setup = experiment.setup.Setup(source=source, scatterer=sphere)


    data = setup.get('Csca', as_numpy=True)

    df = dataframe.unstack('IlluminationPower')
    for diameter, Csca in zip(diameters, data):
        df.loc[diameter, 'Csca'] = Csca * (1e9 ** 2)

    return df.stack('IlluminationPower', future_stack=True).reset_index().set_index(['IlluminationPower', 'BeadDiameter'])


def create_dataframe(illumination_powers, bead_diameters):
    index = pd.MultiIndex.from_product(
        [illumination_powers, bead_diameters],
        names=['IlluminationPower', 'BeadDiameter']
    )

    dataframe = pd.DataFrame(index=index, columns=['SignalMedian', 'rCV', 'Csca', 'BackGroundMedian'])

    return dataframe.astype(float)

def add_signal_to_dataframe(
    dataframe: pd.DataFrame,
    gain: float,
    illumination_powers: list,
    detection_efficiency: float,
    background_level: float,
    diameters: list,
    number_of_bead_events: int
) -> pd.DataFrame:
    """
    Simulate and incorporate signal acquisition results into a MultiIndex DataFrame
    for various illumination powers and bead diameters.

    For each combination of illumination power and bead diameter, the function:
      - Scales the detection efficiency (electrons per nm²) relative to a 20 mW baseline.
      - Computes the mean background signal based on the gain, detection efficiency, and a constant background level.
      - Retrieves the theoretical scattering cross section (from column 'Csca') for that bead size.
      - Simulates the bead's particle signal (using a Poisson process) and the background signal.
      - Sums the signals and then performs background correction using a precomputed background median
        (assumed to be stored in the 'BackGroundMedian' column of the DataFrame).
      - Computes robust statistics (median signal and the robust coefficient of variation)
        from the background-corrected events.
      - Updates the DataFrame (which is indexed by (illumination_power, bead_diameter))
        with the median signal (in column 'SignalMedian') and robust coefficient of variation
        (in column 'rCV').

    Parameters:
        dataframe (pd.DataFrame):
            A MultiIndex DataFrame indexed by (illumination_power, bead_diameter) that contains,
            at a minimum, the following columns:
              - 'Csca': The theoretical scattering cross section (nm²) for each bead.
              - 'BackGroundMedian': The precomputed median background signal.
        gain (float):
            The gain factor (in arbitrary units per photoelectron).
        illumination_powers (list of float):
            A list of illumination power values (e.g., in mW) for which to simulate the signals.
        detection_efficiency (float):
            The detection efficiency (photoelectrons per nm²) measured at 20 mW.
        background_level (float):
            The constant representing the background level (in nm²) used in calculating the background signal.
        diameters (list of float):
            A list of bead diameters (in nm) to simulate.
        number_of_bead_events (int):
            The number of bead events to simulate for each (illumination_power, bead_diameter) condition.

    Returns:
        pd.DataFrame:
            The updated DataFrame with columns 'SignalMedian' (the median signal) and 'rCV'
            (the robust coefficient of variation) for each condition.
    """
    for power in illumination_powers:
        # Scale detection efficiency relative to 20 mW.
        detection_efficiency = detection_efficiency * (power / 20)
        # Compute the mean background signal (in photoelectrons, then converted using gain)
        background_mean_signal = gain * detection_efficiency * background_level

        for diameter in diameters:
            index = (power, diameter)
            # Retrieve the scattering cross section for this bead size
            scattering_cross_section = dataframe.loc[index, 'Csca']
            # Compute the mean bead (particle) signal without background
            bead_particle_mean_signal = gain * detection_efficiency * scattering_cross_section

            # Simulate the bead's particle signal events using a Poisson process.
            particle_signal_events = np.random.poisson(
                lam=bead_particle_mean_signal, size=number_of_bead_events
            )

            # Simulate the background events using a Poisson process.
            background_events = np.random.poisson(
                lam=background_mean_signal, size=number_of_bead_events
            )

            # Total simulated events are the sum of the bead signal and background.
            total_events = particle_signal_events + background_events

            # Apply background correction by subtracting the precomputed background median.
            corrected_events = total_events - dataframe.loc[index, 'BackGroundMedian']

            # Compute robust statistics: median signal and robust coefficient of variation.
            data = compute_robust_stats(corrected_events)

            # Update the DataFrame with the computed values.
            dataframe.loc[index, 'SignalMedian'] = data.median
            dataframe.loc[index, 'rCV'] = data.coefficient_of_variation

    return dataframe


def plot_J(dataframe: pd.DataFrame, bead_diameters: list):
    """
    Plot the robust coefficient of variation versus the inverse square root
    of the median signal for multiple bead diameters and overlay linear regression
    lines to extract calibration slopes (denoted as J).

    For each specified bead diameter, the function:
      - Extracts the data (median signal and robust CV) for that bead diameter from
        the provided DataFrame. (The DataFrame is assumed to have a MultiIndex level
        named 'BeadSize' that contains the bead diameters.)
      - Computes the inverse square root of the median signal.
      - Computes a linear regression (using regression_for_J) between the robust CV and
        1/sqrt(median signal) to obtain the slope (J).
      - Plots the data points as a scatter plot and overlays the regression line, labeling
        each curve with the bead diameter and the computed slope.

    Parameters:
        dataframe (pd.DataFrame): A DataFrame that contains at least the columns
                                  'SignalMedian' and 'rCV', indexed by a MultiIndex that
                                  includes a level named 'BeadSize'.
        bead_diameters (list): A list of bead diameters (in nm) for which the regression
                               is to be performed and plotted.

    Returns:
        None. The function creates and displays a matplotlib plot.
    """
    with plt.style.context(mps):
        figure, ax = plt.subplots(1, 1, figsize=(10, 5))

        ax.set_xlabel('1 / sqrt(Median signal)')
        ax.set_ylabel('Robust CV')
        ax.set_title('Regression for J (across bead diameters)')

        for idx, diameter in enumerate(bead_diameters):
            color = f'C{idx}'
            # Compute regression for the given bead diameter.
            J_fit, x_data, y_data = regression_for_J(dataframe=dataframe, diameter=diameter)

            # Create fitted regression line data.
            x_fit = np.linspace(x_data.min(), x_data.max(), 100)
            y_fit = J_fit * x_fit

            ax.scatter(x_data, y_data, color=color,
                       label=f'{diameter} nm | Fit: slope={J_fit:.3f}')
            ax.plot(x_fit, y_fit, color=color)

        ax.legend(fontsize=14)
        plt.tight_layout()
        plt.show()


def plot_K(dataframe: pd.DataFrame, illumination_powers: list):
    """
    Plot the relationship between the background-corrected median signal and the
    theoretical scattering cross section for various illumination powers and overlay
    linear regression lines to extract conversion slopes (denoted as K).

    For each illumination power provided in the list, the function:
      - Extracts data for that power from the DataFrame. (The DataFrame is assumed to be
        indexed by illumination power.)
      - Retrieves the background-corrected median signal ('SignalMedian') and the scattering
        cross section ('Csca') for different bead sizes.
      - Performs a linear regression (using regression_for_K) of the scattering cross section
        versus the median signal, yielding the slope K.
      - Plots the data points and the corresponding regression line, labeling each curve with
        the illumination power and the computed slope.

    Parameters:
        dataframe (pd.DataFrame): A DataFrame that contains the columns 'SignalMedian' and 'Csca'.
        illumination_powers (list): A list of illumination power values (e.g., in mW) for which the regression and plotting are to be performed.

    Returns:
        None. The function creates and displays a matplotlib plot.
    """
    with plt.style.context(mps):
        figure, ax = plt.subplots(1, 1, figsize=(10, 5))

        ax.set_xlabel('Median background-corrected signal (a.u.)')
        ax.set_ylabel(r'Scattering cross section $\sigma_s$ (nm$^2$)')
        ax.set_title('Regression for K at various illumination powers')

        for idx, power in enumerate(illumination_powers):
            # Compute regression for the given illumination power.
            K_fit, median_signals, sigma_values = regression_for_K(dataframe=dataframe, power=power)

            color = f'C{idx}'
            x_fit = np.linspace(median_signals.min(), median_signals.max(), 100)
            y_fit = K_fit * x_fit

            ax.scatter(median_signals, sigma_values, color=color,
                       label=f'{power} mW | Fit: slope={K_fit:.1f}')
            ax.plot(x_fit, y_fit, color=color)

        ax.legend(fontsize=14)
        plt.tight_layout()
        plt.show()











def get_acquisition(background_fraction, optical_power, run_time, processing_steps, plot_analog = False, plot_digital = False, bit_depth = '14bit', saturation_levels = 'auto', populations=[]):
    background_power = background_fraction * optical_power

    # Set up the flow cell.
    flow_cell = FlowCell(
        sample_volume_flow=80 * units.microliter / units.minute / 10,
        sheath_volume_flow=1 * units.milliliter / units.minute / 10,
        width=100 * units.micrometer,
        height=100 * units.micrometer,
        event_scheme='uniform-random'
    )

    source = GaussianBeam(
        numerical_aperture=0.1 * units.AU,
        wavelength=450 * units.nanometer,
        optical_power=optical_power,
        RIN=-140
    )

    # Configure the signal digitizer.
    digitizer = SignalDigitizer(
        bit_depth=bit_depth,
        saturation_levels=saturation_levels,
        sampling_rate=60 * units.megahertz,
    )

    # Configure the detector.
    detector_ = Detector(
        name='forward',
        phi_angle=0 * units.degree,
        numerical_aperture=0.8 * units.AU,
        responsivity=1 * units.ampere / units.watt,
    )

    # Set up the transimpedance amplifier.
    amplifier = TransimpedanceAmplifier(
        gain=10 * units.volt / units.ampere,
        bandwidth=10 * units.megahertz,
        voltage_noise_density=1 * units.nanovolt / units.sqrt_hertz,
        current_noise_density=2 * units.femtoampere / units.sqrt_hertz
    )

    scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)


    for population in populations:
        scatterer_collection.add_population(population)


    if len(populations) != 0:
        print('Simulating configuration', f"{populations[0].diameter}, {background_power = :~P}, {optical_power = :~P}, {run_time = :~P}, {bit_depth = }, {saturation_levels = }")
    else:
        print('Simulating configuration', f"{background_power = :~P}, {optical_power = :~P}, {run_time = :~P}, {bit_depth = }, {saturation_levels = }")
    # Create the flow cytometer.
    cytometer = FlowCytometer(
        source=source,
        transimpedance_amplifier=amplifier,
        scatterer_collection=scatterer_collection,
        digitizer=digitizer,
        detectors=[detector_],
        flow_cell=flow_cell,
        background_power=background_power
    )

    # Prepare the acquisition for the specified run time.
    cytometer.prepare_acquisition(run_time=run_time, compute_cross_section=True)
    acquisition = cytometer.get_acquisition(processing_steps=processing_steps)

    if plot_analog:
        acquisition.plot()

    if plot_digital:
        acquisition.digitalize(digitizer=digitizer).plot()

    return acquisition, cytometer


def get_acquisition_analog_metrics(
    diameter_list: Sequence[float],
    index_list: Sequence[float],
    optical_power: Union[float, Sequence[float]],
    background_fraction=0,
    run_time = 5 * units.millisecond,
    particle_count: int = 100,
    plot_analog: bool = False,
    processing_steps: Optional[list] = []
) -> pd.DataFrame:
    """
    Compute bead metrics for each combination of diameter, optical_power, and background_power.

    Parameters
    ----------
    diameter_list : sequence of float
        List of bead diameters to process.
    optical_power : float or sequence of float
        Illumination power(s). If a single value is provided, it will be wrapped in a list.
    background_power : float or sequence of float
        Background illumination power(s). If a single value is provided, it will be wrapped in a list.
    threshold : float
        Peak detection threshold.
    bit_depth : str
        Detector bit depth.
    saturation_levels : str
        Levels for digital saturation.
    plot_analog : bool, optional
        Whether to plot analog traces.
    plot_digital : bool, optional
        Whether to plot digital traces.
    processing_steps : list, optional
        Additional processing steps for data.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame indexed by (diameter, optical_power, background_power)
        containing computed metrics (including Csca).
    """
    optical_powers = np.atleast_1d(optical_power)
    background_fractions = np.atleast_1d(background_fraction)

    length = len(diameter_list) * len(optical_powers) * len(background_fraction)
    df = pd.DataFrame(index=range(length), columns=['Mean', 'Median', 'STD', 'CV', 'InvSqrtMedian', 'Run'])

    for run_id, ((diameter, refractive_index), op, bf) in enumerate(itertools.product(zip(diameter_list, index_list), optical_powers, background_fractions)):

        if diameter is not None and refractive_index is not None:
            populations = [
                Sphere(
                    name=f'Population: [{diameter}nm, {refractive_index}]',
                    particle_count=particle_count * units.particle,
                    diameter=diameter,
                    refractive_index=refractive_index
                )
            ]
        else:
            populations = []

        acquisition, _ = get_acquisition(
            populations=populations,
            optical_power=op,
            background_fraction=bf,
            run_time=run_time,
            processing_steps=processing_steps,
            bit_depth='15bit',
            saturation_levels='auto',
            plot_analog=plot_analog,
            plot_digital=False
        )

        signal = acquisition['forward'].pint.to('V').pint.quantity.magnitude

        data = compute_robust_stats(signal)

        df.loc[run_id, 'Run'] = run_id
        df.loc[run_id, 'Mean'] = data.mean
        df.loc[run_id, 'Median'] = data.median
        df.loc[run_id, 'STD'] = data.standard_deviation
        df.loc[run_id, 'CV'] = data.coefficient_of_variation
        df.loc[run_id, 'rSTD'] = data.robust_standard_deviation
        df.loc[run_id, 'rCV'] = data.robust_coefficient_of_variation
        df.loc[run_id, 'OpticalPower'] = op.to('mW').magnitude
        df.loc[run_id, 'BackgroundPower'] = (bf * op).to('mW').magnitude
        df.loc[run_id, 'BackgroundFraction'] = bf
        df.loc[run_id, 'InvSqrtMedian'] = 1 / (np.sqrt(df.loc[run_id, 'Median']))


    return df.set_index('Run')

def get_acquisition_digital_metrics(
    diameter_list: Sequence[float],
    index_list: Sequence[float],
    optical_power: Union[float, Sequence[float]],
    background_fraction=0,
    bit_depth: str = '15bit',
    saturation_levels: str = 'auto',
    run_time = 5 * units.millisecond,
    particle_count: int = 100,
    plot_analog: bool = False,
    plot_digital: bool = False,
    processing_steps: Optional[list] = []
) -> pd.DataFrame:
    """
    Compute bead metrics for each combination of diameter, optical_power, and background_power.

    Parameters
    ----------
    diameter_list : sequence of float
        List of bead diameters to process.
    optical_power : float or sequence of float
        Illumination power(s). If a single value is provided, it will be wrapped in a list.
    background_power : float or sequence of float
        Background illumination power(s). If a single value is provided, it will be wrapped in a list.
    threshold : float
        Peak detection threshold.
    bit_depth : str
        Detector bit depth.
    saturation_levels : str
        Levels for digital saturation.
    plot_analog : bool, optional
        Whether to plot analog traces.
    plot_digital : bool, optional
        Whether to plot digital traces.
    processing_steps : list, optional
        Additional processing steps for data.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame indexed by (diameter, optical_power, background_power)
        containing computed metrics (including Csca).
    """
    optical_powers = np.atleast_1d(optical_power)
    background_fractions = np.atleast_1d(background_fraction)

    length = len(diameter_list) * len(optical_powers) * len(background_fractions)
    df = pd.DataFrame(index=range(length), columns=['Mean', 'Median', 'STD', 'CV', 'InvSqrtMedian', 'Run'])

    for run_id, ((diameter, refractive_index), op, bf) in enumerate(itertools.product(zip(diameter_list, index_list), optical_powers, background_fractions)):

        if diameter is not None and refractive_index is not None:
            populations = [
                Sphere(
                    name=f'Population: [{diameter}nm, {refractive_index}]',
                    particle_count=particle_count * units.particle,
                    diameter=diameter,
                    refractive_index=refractive_index
                )
            ]
        else:
            populations = []

        acquisition, cytometer = get_acquisition(
            populations=populations,
            optical_power=op,
            background_fraction=bf,
            run_time=run_time,
            processing_steps=processing_steps,
            bit_depth=bit_depth,
            saturation_levels=saturation_levels,
            plot_analog=plot_analog,
            plot_digital=plot_digital
        )

        signal = acquisition.digitalize(digitizer=cytometer.digitizer)['forward'].pint.to('bit_bins').pint.quantity.magnitude

        data = compute_robust_stats(signal)

        df.loc[run_id, 'Run'] = run_id
        df.loc[run_id, 'Mean'] = data.mean
        df.loc[run_id, 'Median'] = data.median
        df.loc[run_id, 'STD'] = data.standard_deviation
        df.loc[run_id, 'CV'] = data.coefficient_of_variation
        df.loc[run_id, 'rSTD'] = data.robust_standard_deviation
        df.loc[run_id, 'rCV'] = data.robust_coefficient_of_variation
        df.loc[run_id, 'OpticalPower'] = op.to('mW').magnitude
        df.loc[run_id, 'BackgroundPower'] = (bf * op).to('mW').magnitude
        df.loc[run_id, 'BackgroundFraction'] = bf
        df.loc[run_id, 'InvSqrtMedian'] = 1 / (np.sqrt(df.loc[run_id, 'Median']))

    return df.set_index('Run')



def get_trigger_metrics(
    diameter_list: Sequence[float],
    index_list: Sequence[float],
    optical_power: Union[float, Sequence[float]],
    threshold: float,
    bit_depth: str,
    saturation_levels: str,
    background_fraction=0,
    run_time = 5 * units.millisecond,
    particle_count: int = 100,
    plot_analog: bool = False,
    plot_digital: bool = False,
    plot_trigger: bool = False,
    processing_steps: Optional[list] = []
) -> pd.DataFrame:
    """
    Compute bead metrics for each combination of diameter, optical_power, and background_power.

    Parameters
    ----------
    diameter_list : sequence of float
        List of bead diameters to process.
    optical_power : float or sequence of float
        Illumination power(s). If a single value is provided, it will be wrapped in a list.
    background_power : float or sequence of float
        Background illumination power(s). If a single value is provided, it will be wrapped in a list.
    threshold : float
        Peak detection threshold.
    bit_depth : str
        Detector bit depth.
    saturation_levels : str
        Levels for digital saturation.
    plot_analog : bool, optional
        Whether to plot analog traces.
    plot_digital : bool, optional
        Whether to plot digital traces.
    processing_steps : list, optional
        Additional processing steps for data.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame indexed by (diameter, optical_power, background_power)
        containing computed metrics (including Csca).
    """
    optical_powers = np.atleast_1d(optical_power)
    background_fraction = np.atleast_1d(background_fraction)

    results = []

    for run_id, ((diameter, refractive_index), op, bf) in enumerate(itertools.product(zip(diameter_list, index_list), optical_powers, background_fraction)):

        population = Sphere(
            name=f'Population: [{diameter}nm, {refractive_index}]',
            particle_count=particle_count * units.particle,
            diameter=diameter,
            refractive_index=refractive_index
        )

        acquisition, cytometer = get_acquisition(
            populations=[population],
            optical_power=op,
            background_fraction=bf,
            run_time=run_time,
            processing_steps=processing_steps,
            bit_depth=bit_depth,
            saturation_levels=saturation_levels,
            plot_analog=plot_analog,
            plot_digital=plot_digital
        )

        trigger = DynamicWindow(
            trigger_detector_name='forward',
            signal_dataframe=acquisition,
            digitizer=cytometer.digitizer,

            max_triggers=-1,
            pre_buffer=20,
            post_buffer=20
        )

        triggered_analog = trigger.run(
            threshold=threshold,
        )

        if plot_trigger:
            triggered_analog.plot()

        peak_algorithm = peak_locator.GlobalPeakLocator(compute_width=False)

        digital_trigger = triggered_analog.digitalize(digitizer=cytometer.digitizer)

        peak_dataframe = peak_algorithm.run(signal_dataframe=digital_trigger)

        csca_val = acquisition.scatterer['Csca'].mean().to('nm**2').magnitude

        df = peak_dataframe.copy()
        df['Run'] = run_id
        df['Diameter'] = diameter.to('nm').magnitude
        df['OpticalPower'] = op.to('mW').magnitude
        df['BackgroundPower'] = (bf * op).to('mW').magnitude
        df['BackgroundFraction'] = bf
        df['Csca'] = csca_val
        df['DetectorPower'] = acquisition.scatterer['forward'].mean().to('mW').magnitude

        results.append(df)

    # Concatenate all results
    combined = pd.concat(results, ignore_index=True)

    # Set up multi-index
    combined.set_index(
        ['Diameter', 'OpticalPower', 'BackgroundPower', 'Run'],
        inplace=True
    )

    # Drop unwanted raw columns and ensure numeric types
    cleaned = (
        combined
        .drop(columns=['Detector', 'SegmentID', 'PeakID', 'Area', 'Width', 'Index'], errors='ignore')
        .astype(float)
    )


    df = pd.DataFrame()
    df['Mean'] = cleaned['Height'].groupby(['Diameter', 'OpticalPower', 'BackgroundPower']).apply('mean')
    df['Median'] = cleaned['Height'].groupby(['Diameter', 'OpticalPower', 'BackgroundPower']).apply('median')
    df['STD'] = cleaned['Height'].groupby(['Diameter', 'OpticalPower', 'BackgroundPower']).apply('std')
    df['CV'] = df['STD'] / df['Median']
    df['Csca'] = cleaned['Csca'].groupby(['Diameter', 'OpticalPower', 'BackgroundPower']).apply('mean')

    df['DetectorPower'] = cleaned['DetectorPower'].groupby(['Diameter', 'OpticalPower', 'BackgroundPower']).apply('mean')
    df.attrs['cytometer'] = cytometer
    return df

def get_scatterer_metrics(
    diameter_list: Sequence[float],
    index_list: Sequence[float],
    optical_power: Union[float, Sequence[float]],
    bit_depth: str,
    saturation_levels: str,
    background_fraction: 0,
    run_time = 5 * units.millisecond,
    particle_count: int = 100,
    plot_analog: bool = False,
    plot_digital: bool = False,
    processing_steps: Optional[list] = []
) -> pd.DataFrame:
    """
    Compute bead metrics for each combination of diameter, optical_power, and background_power.

    Parameters
    ----------
    diameter_list : sequence of float
        List of bead diameters to process.
    optical_power : float or sequence of float
        Illumination power(s). If a single value is provided, it will be wrapped in a list.
    background_power : float or sequence of float
        Background illumination power(s). If a single value is provided, it will be wrapped in a list.
    threshold : float
        Peak detection threshold.
    bit_depth : str
        Detector bit depth.
    saturation_levels : str
        Levels for digital saturation.
    plot_analog : bool, optional
        Whether to plot analog traces.
    plot_digital : bool, optional
        Whether to plot digital traces.
    processing_steps : list, optional
        Additional processing steps for data.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame indexed by (diameter, optical_power, background_power)
        containing computed metrics (including Csca).
    """
    optical_powers = np.atleast_1d(optical_power)
    background_fractions = np.atleast_1d(background_fraction)

    results = []

    for run_id, ((diameter, refractive_index), op, bf) in enumerate(itertools.product(zip(diameter_list, index_list), optical_powers, background_fractions)):

        population = Sphere(
            name=f'Population: [{diameter}nm, {refractive_index}]',
            particle_count=particle_count * units.particle,
            diameter=diameter,
            refractive_index=refractive_index
        )

        acquisition, cytometer = get_acquisition(
            populations=[population],
            optical_power=op,
            background_fraction=bf,
            run_time=run_time,
            processing_steps=processing_steps,
            bit_depth=bit_depth,
            saturation_levels=saturation_levels,
            plot_analog=plot_analog,
            plot_digital=plot_digital
        )

        csca_val = acquisition.scatterer['Csca'].mean().to('nm**2').magnitude

        df = acquisition.scatterer.copy()
        df['Run'] = run_id
        df['Diameter'] = diameter.to('nm').magnitude
        df['OpticalPower'] = op.to('mW').magnitude
        df['BackgroundPower'] = (bf * op).to('mW').magnitude
        df['BackgroundFraction'] = bf
        df['Csca'] = csca_val

        results.append(df)

    # Concatenate all results
    combined = pd.concat(results, ignore_index=True)

    # Set up multi-index
    combined.set_index(
        ['Diameter', 'OpticalPower', 'BackgroundPower', 'Run'],
        inplace=True
    )

    cleaned_df = combined.drop(columns=['x', 'y', 'Velocity', 'Widths', 'type', 'RefractiveIndex', 'Time'], errors='ignore')

    return cleaned_df


def get_trigger_signals(
    diameter_list: Sequence[float],
    index_list: Sequence[float],
    optical_power: Union[float, Sequence[float]],
    threshold: float,
    bit_depth: str,
    saturation_levels: str,
    background_fraction=0,
    run_time = 5 * units.millisecond,
    particle_count: int = 100,
    plot_analog: bool = False,
    plot_digital: bool = False,
    plot_trigger: bool = False,
    processing_steps: Optional[list] = []
) -> pd.DataFrame:
    """
    Compute bead metrics for each combination of diameter, optical_power, and background_power.

    Parameters
    ----------
    diameter_list : sequence of float
        List of bead diameters to process.
    optical_power : float or sequence of float
        Illumination power(s). If a single value is provided, it will be wrapped in a list.
    background_power : float or sequence of float
        Background illumination power(s). If a single value is provided, it will be wrapped in a list.
    threshold : float
        Peak detection threshold.
    bit_depth : str
        Detector bit depth.
    saturation_levels : str
        Levels for digital saturation.
    plot_analog : bool, optional
        Whether to plot analog traces.
    plot_digital : bool, optional
        Whether to plot digital traces.
    processing_steps : list, optional
        Additional processing steps for data.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame indexed by (diameter, optical_power, background_power)
        containing computed metrics (including Csca).
    """
    optical_powers = np.atleast_1d(optical_power)
    background_fraction = np.atleast_1d(background_fraction)

    results = []

    for run_id, ((diameter, refractive_index), op, bf) in enumerate(itertools.product(zip(diameter_list, index_list), optical_powers, background_fraction)):

        population = Sphere(
            name=f'Population: [{diameter}nm, {refractive_index}]',
            particle_count=particle_count * units.particle,
            diameter=diameter,
            refractive_index=refractive_index
        )

        acquisition, cytometer = get_acquisition(
            populations=[population],
            optical_power=op,
            background_fraction=bf,
            run_time=run_time,
            processing_steps=processing_steps,
            bit_depth=bit_depth,
            saturation_levels=saturation_levels,
            plot_analog=plot_analog,
            plot_digital=plot_digital
        )

        trigger = TriggeringSystem(
            digitizer=cytometer.digitizer,
            threshold=threshold,
            max_triggers=-1,
            min_window_duration=1 * units.microsecond,
            pre_buffer=20,
            post_buffer=20
        )

        triggered_analog = trigger.run(
            trigger_detector_name='forward',
            signal_dataframe=acquisition

        )

        if plot_trigger:
            triggered_analog.plot()

        peak_algorithm = peak_locator.GlobalPeakLocator(compute_width=False)

        digital_trigger = triggered_analog.digitalize(digitizer=cytometer.digitizer)

        peak_dataframe = peak_algorithm.run(signal_dataframe=digital_trigger)

        csca_val = acquisition.scatterer['Csca'].mean().to('nm**2').magnitude
        peak_dataframe['Csca'] = csca_val

        detector_power = acquisition.scatterer['forward'].mean().to('mW').magnitude
        peak_dataframe['DetectorPower'] = detector_power



        results.append(peak_dataframe)

    output = pd.concat(results, keys=[d.to('nm').magnitude for d in diameter_list]).droplevel(['Detector', 'PeakID'], axis=0).drop(['Index', 'Area', 'Width'], axis=1)

    output.index.names = ['Diameter', 'SegmentID']

    return output




import numpy as np
import matplotlib.pyplot as plt
from typing import Optional, Union, Sequence

def fit_polynomial(x: np.ndarray, y: np.ndarray, degrees: Optional[Union[int, Sequence[int]]], strict_degree: bool, string_repr: str) -> tuple:
    """Fit a polynomial to the data and return the coefficients, the fitted values, and the R² value."""
    if isinstance(degrees, int):
        degrees_list = [degrees]
    else:
        degrees_list = list(degrees)

    if not strict_degree:
        max_deg = max(degrees_list)
        degrees_list = list(range(0, max_deg + 1))
    else:
        degrees_list = sorted(set(degrees_list))

    # Build design matrix
    X = np.vstack([x**deg for deg in degrees_list]).T
    coeffs = np.linalg.lstsq(X, y, rcond=None)[0]

    # Calculate fitted values
    X_sorted = np.vstack([np.sort(x)**deg for deg in degrees_list]).T
    y_fit = X_sorted @ coeffs

    # Calculate R² (Coefficient of Determination)
    ss_total = np.sum((y - np.mean(y)) ** 2)
    ss_residual = np.sum((y - y_fit) ** 2)

    r2 = 1 - (ss_residual / ss_total)

    # Prepare the label for the equation
    terms = [
        f"{coeffs[i]:{string_repr}} x$^{deg}$" for i, deg in enumerate(degrees_list)
    ]
    label = ' + '.join(terms).replace('$^1$', '')

    return coeffs, y_fit, r2, label

def plot_with_fit(
    x: np.ndarray,
    y: np.ndarray,
    degrees: Optional[Union[int, Sequence[int]]] = None,
    strict_degree: bool = True,
    xlabel: str = 'x',
    ylabel: str = 'y',
    title: Optional[str] = None,
    show_equation: bool = True,
    figsize: tuple = (10, 6),
    fit_colors: Optional[Sequence[str]] = None,
    scatter_kwargs: Optional[dict] = None,
    line_kwargs: Optional[dict] = None,
    ax: plt.Axes = None,
    string_repr: str = '.3f'
) -> plt.Axes:
    """
    Plot data points and polynomial fits of specified degrees or specified monomials.
    """
    # Convert input to numpy arrays
    x, y = np.asarray(x), np.asarray(y)

    indices = np.argsort(y)

    y = y[indices]
    x = x[indices]

    # Default arguments if not provided
    scatter_kwargs = scatter_kwargs or {'s': 50, 'alpha': 0.7, 'label': 'Data'}
    line_kwargs = line_kwargs or {'linestyle': '--', 'linewidth': 2}

    # Create figure and axis
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    # Step 1: Plot scatter data
    ax.scatter(x, y, **scatter_kwargs)

    # Step 2: Fit the polynomial and compute necessary information
    if degrees is not None:
        coeffs, y_fit, r2, label = fit_polynomial(x, y, degrees, strict_degree, string_repr)

        # Step 3: Plot the fitted line
        prop_cycle = plt.rcParams['axes.prop_cycle'].by_key().get('color', None)
        colors = fit_colors or prop_cycle
        ax.plot(np.sort(x), y_fit, label=f"R$^2$: {r2:.4f}", color=colors[0] if colors else None, **line_kwargs)

        # Step 4: Display the equation in a white box
        if show_equation:
            ax.text(0.05, 0.95, f"y = {label}", transform=ax.transAxes, fontsize=12, verticalalignment='top', horizontalalignment='left', bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.5'))

        # Step 5: Add R² to the legend
        ax.legend(loc='upper left')

    # Final formatting
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower right')
    plt.tight_layout()

    return ax, coeffs
