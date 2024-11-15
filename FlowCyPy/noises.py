

class NoiseSetting:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    _include_noises = True
    include_shot_noise = True
    include_dark_current_noise = True
    include_thermal_noise = True
    include_RIN_noise = True

    @property
    def include_noises(self):
        return self._include_noises

    @include_noises.setter
    def include_noises(self, value):
        self._include_noises = value
        # Dynamically update other noise components
        if not value:
            self.include_shot_noise = False
            self.include_dark_current_noise = False
            self.include_thermal_noise = False
            self.include_RIN_noise = False
