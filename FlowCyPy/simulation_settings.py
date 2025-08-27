import warnings


class RestrictiveMeta(type):
    def __setattr__(cls, name, value):
        if not hasattr(cls, name):
            # Collect valid attribute names (excluding private and dunder)
            valid_attrs = [attr for attr in dir(cls) if not attr.startswith("_")]
            warnings.warn(
                f"Attribute '{name}' not recognized in {cls.__name__}. Valid attributes are: {valid_attrs}",
                UserWarning,
            )
            return
        super().__setattr__(name, value)


class SimulationSettings(metaclass=RestrictiveMeta):
    """
    A singleton class to manage noise inclusion settings in simulations.

    This class provides a centralized configuration for enabling or disabling
    various noise components in a simulation. The class is implemented as a
    singleton, ensuring that only one instance exists throughout the application.

    The inclusion of noise components can be toggled globally through the
    `include_noises` attribute, which dynamically updates the individual noise
    settings.

    Attributes
    ----------
    include_noises : bool
        Whether to include noise components in simulations. If set to False,
        all individual noise settings are disabled.
    include_shot_noise : bool
        Whether to include shot noise in simulations. Default is True.
    include_dark_current_noise : bool
        Whether to include dark current noise in simulations. Default is True.
    include_amplifier_noise : bool
        Whether to include amplifier noise in simulations. Default is True.
    include_source_noise : bool
        Whether to include Relative Intensity Noise (RIN) in simulations. Default is True.
    assume_perfect_hydrodynamic_focusing: bool
        Whether to include the noise coming from the transversal sampling of
        the scatterer position regarding beam localization. Default is False.

    Methods
    -------
    __new__(cls, *args, **kwargs):
        Ensures that only a single instance of the class is created (singleton pattern).

    include_noises (property):
        A getter and setter for the `include_noises` attribute that dynamically updates
        other noise settings.

    Notes
    -----
    - The class uses the `RestrictiveMeta` metaclass, preventing the addition of
      new class-level attributes after the class definition.
    - The singleton pattern is enforced by overriding the `__new__` method, ensuring
      a single shared instance.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    _include_noises = True
    include_shot_noise = True
    include_dark_current_noise = True
    include_source_noise = True
    include_amplifier_noise = True
    assume_perfect_hydrodynamic_focusing = False
    assume_amplifier_bandwidth_is_infinite = False
    assume_perfect_digitizer = False
    sorted_population = False
    evenly_spaced_events = False

    @property
    def include_noises(self):
        return self._include_noises

    @include_noises.setter
    def include_noises(self, value):
        self._include_noises = bool(value)
        # Dynamically update other noise components
        if not self._include_noises:
            self.include_shot_noise = False
            self.include_dark_current_noise = False
            self.include_source_noise = False
            self.include_amplifier_noise = False
