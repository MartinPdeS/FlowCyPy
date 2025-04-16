import numpy as np
import pandas as pd
from FlowCyPy import units
from PyMieSim import experiment
import matplotlib.pyplot as plt
from MPSPlots.styles import mps
from FlowCyPy.flow_cell import FlowCell
from FlowCyPy.population import Sphere
from FlowCyPy import (
    peak_locator,
    circuits,
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











def get_acquisition(scatterer_collection, background_power, run_time, processing_steps, plot_analog = False):
    # Set up the flow cell.
    flow_cell = FlowCell(
        sample_volume_flow=80 * units.microliter / units.minute,
        sheath_volume_flow=1 * units.milliliter / units.minute,
        width=100 * units.micrometer,
        height=100 * units.micrometer,
    )

    source = GaussianBeam(
        numerical_aperture=0.1 * units.AU,
        wavelength=450 * units.nanometer,
        optical_power=200 * units.milliwatt,
        RIN=-140
    )

    # Configure the signal digitizer.
    signal_digitizer = SignalDigitizer(
        bit_depth='20bit',
        saturation_levels='auto',
        sampling_rate=60 * units.megahertz,
    )

    # Configure the detector.
    detector_ = Detector(
        name='forward',
        phi_angle=0 * units.degree,
        numerical_aperture=0.3 * units.AU,
        responsivity=1 * units.ampere / units.watt,
    )

    # Set up the transimpedance amplifier.
    amplifier = TransimpedanceAmplifier(
        gain=10 * units.volt / units.ampere,
        bandwidth=10 * units.megahertz,
        voltage_noise_density=1 * units.nanovolt / units.sqrt_hertz,
        current_noise_density=2 * units.femtoampere / units.sqrt_hertz
    )

    # Create the flow cytometer.
    cytometer = FlowCytometer(
        source=source,
        transimpedance_amplifier=amplifier,
        scatterer_collection=scatterer_collection,
        signal_digitizer=signal_digitizer,
        detectors=[detector_],
        flow_cell=flow_cell,
        background_power=background_power
    )

    # Prepare the acquisition for the specified run time.
    cytometer.prepare_acquisition(run_time=run_time, compute_cross_section=True)
    acquisition = cytometer.get_acquisition(processing_steps=processing_steps)

    if plot_analog:
        acquisition.analog.plot()

    return acquisition


def get_beads_dataframe(
    diameter_list: list,
    indices_list: list,
    threshold: units.Quantity,
    run_time: units.Quantity,
    medium_refractive_index: units.Quantity,
    background_power: units.Quantity,
    plot_analog: bool = False,
    particle_count: int = 50,
    processing_steps: list = [],
    plot_trigger: bool = False,
) -> any:
    """
    Simulate a flow cytometry acquisition, perform triggering, and detect peaks
    (e.g., peak heights) from the triggered signal using the FlowCyPy library.

    This function sets up a simulated flow cytometer with a Gaussian beam source,
    flow cell, and scatterer collection configured with the specified medium refractive
    index. For each bead population defined by a diameter in 'diameter_list' and
    its corresponding refractive index in 'indices_list', a sphere population is added
    to the scatterer collection.

    The simulation then configures a signal digitizer, detector, and transimpedance
    amplifier before creating a FlowCytometer instance. After preparing an acquisition
    with the specified run time and applying processing steps (baseline restoration
    and low-pass filtering), the function retrieves the analog signal. If requested,
    it plots this raw analog signal.

    Next, the function applies a triggering algorithm on the 'forward' detector using
    the provided threshold (with pre-buffer and post-buffer sizes of 20 samples). If requested,
    the triggered signal is also plotted.

    Finally, a global peak locator algorithm is applied to the triggered acquisition
    to detect and return peak information.

    Parameters:
        diameter_list (list): List of bead diameters (e.g., in nanometers) for the simulated populations.
        indices_list (list): List of refractive indices for each bead population. Must have the same length as diameter_list.
        plot_analog (bool, optional): If True, plot the raw analog acquisition signal. Defaults to False.
        plot_trigger (bool, optional): If True, plot the triggered acquisition signal. Defaults to False.
        threshold (units.Quantity): The threshold value (with appropriate units) for triggering.
        run_time (units.Quantity): The duration of the acquisition (with appropriate units).
        medium_refractive_index (units.Quantity): The refractive index of the medium used in the flow cell.

    Returns:
        any: The detected peaks from the triggered acquisition as returned by the peak locator.
             (The exact type/structure depends on the implementation of peak_locator.GlobalPeakLocator
              and the triggered acquisition's detect_peaks method.)

    Raises:
        ValueError: If the lengths of 'diameter_list' and 'indices_list' do not match.
    """
    # Validate that the bead populations are defined correctly.
    if len(diameter_list) != len(indices_list):
        raise ValueError("The number of diameters must match the number of refractive indices.")

    # Create the scatterer collection with the specified medium refractive index.
    scatterer_collection = ScattererCollection(medium_refractive_index=medium_refractive_index)

    # Add each bead population (represented as a sphere) to the scatterer collection.

    for diameter, refractive_index in zip(diameter_list, indices_list):
        population = Sphere(
            name=f'Population: [{diameter}nm, {refractive_index}]',
            particle_count=particle_count * units.particle,
            diameter=diameter * units.nanometer,
            refractive_index=refractive_index * units.RIU
        )
        scatterer_collection.add_population(population)

    acquisition = get_acquisition(
        scatterer_collection=scatterer_collection,
        background_power=background_power,
        run_time=run_time,
        processing_steps=processing_steps,
        plot_analog=plot_analog
    )

    # Run the triggering algorithm.
    triggered_acquisition = acquisition.run_triggering(
        threshold=threshold,
        trigger_detector_name='forward',
        max_triggers=-1,
        pre_buffer=20,
        post_buffer=20
    )

    # Optionally plot the triggered acquisition signal.
    if plot_trigger:
        triggered_acquisition.analog.plot()

    # Create a global peak locator algorithm (without computing width).
    peak_algorithm = peak_locator.GlobalPeakLocator(compute_width=False)

    digital_signal = triggered_acquisition.get_digital_signal()

    peak_dataframe = peak_algorithm.run(
        signal_dataframe=digital_signal
    )

    return acquisition.scatterer, peak_dataframe


def get_background_dataframe(
    run_time: units.Quantity,
    background_power: units.Quantity,
    plot_analog: bool = False,
    processing_steps: list = [],
) -> any:
    """
    Simulate a flow cytometry acquisition, perform triggering, and detect peaks
    (e.g., peak heights) from the triggered signal using the FlowCyPy library.

    This function sets up a simulated flow cytometer with a Gaussian beam source,
    flow cell, and scatterer collection configured with the specified medium refractive
    index. For each bead population defined by a diameter in 'diameter_list' and
    its corresponding refractive index in 'indices_list', a sphere population is added
    to the scatterer collection.

    The simulation then configures a signal digitizer, detector, and transimpedance
    amplifier before creating a FlowCytometer instance. After preparing an acquisition
    with the specified run time and applying processing steps (baseline restoration
    and low-pass filtering), the function retrieves the analog signal. If requested,
    it plots this raw analog signal.

    Next, the function applies a triggering algorithm on the 'forward' detector using
    the provided threshold (with pre-buffer and post-buffer sizes of 20 samples). If requested,
    the triggered signal is also plotted.

    Finally, a global peak locator algorithm is applied to the triggered acquisition
    to detect and return peak information.

    Parameters:
        diameter_list (list): List of bead diameters (e.g., in nanometers) for the simulated populations.
        indices_list (list): List of refractive indices for each bead population. Must have the same length as diameter_list.
        plot_analog (bool, optional): If True, plot the raw analog acquisition signal. Defaults to False.
        plot_trigger (bool, optional): If True, plot the triggered acquisition signal. Defaults to False.
        threshold (units.Quantity): The threshold value (with appropriate units) for triggering.
        run_time (units.Quantity): The duration of the acquisition (with appropriate units).
        medium_refractive_index (units.Quantity): The refractive index of the medium used in the flow cell.

    Returns:
        any: The detected peaks from the triggered acquisition as returned by the peak locator.
             (The exact type/structure depends on the implementation of peak_locator.GlobalPeakLocator
              and the triggered acquisition's detect_peaks method.)

    Raises:
        ValueError: If the lengths of 'diameter_list' and 'indices_list' do not match.
    """
    # Create the scatterer collection with the specified medium refractive index.
    scatterer_collection = ScattererCollection(medium_refractive_index=1.33 * units.RIU)

    acquisition = get_acquisition(
        scatterer_collection=scatterer_collection,
        background_power=background_power,
        run_time=run_time,
        processing_steps=processing_steps,
        plot_analog=plot_analog
    )

    return acquisition#.get_digital_signal()