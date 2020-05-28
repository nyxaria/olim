# coding: utf-8

import math

magnitudes = {'G': 9,
              'M': 6,
              'k': 3,
              '': 0,
              '0': 0,
              'c': -2,
              'm': -3,
              '\u03BC': -6,
              'n': -9}

scale_transforms = {u"m\u00B2": "m"}

def scale(var, to, _from='x', mag=1, inverse=False):
    if to == _from or not to:
        return var
    else:
        to = scale_transforms.get(to, to)
        _from = scale_transforms.get(_from, _from)
        if len(to) == 1:
            to = '0' + to
        if len(_from) == 1:
            _from = '0' + _from
        to = to[0]
        _from = _from[0]

    if to not in magnitudes.keys() or _from not in magnitudes.keys():
        print('Invalid units "%s" "%s". Fix your shit!' % (to, _from))
    return var * pow(10,(magnitudes.get(_from, 0) - magnitudes.get(to, 0))*mag*(-1 if inverse else 1))


class Tube:
    def __init__(self, OD, ID, effective_length, unit='mm'):
        if not (unit == 'mm' or unit == 'm'):
            print('Invalid unit "%s". Assigning "mm" for now.' % unit)
            unit = 'mm'

        if unit != 'm':
            OD = scale(OD, to="m", _from=unit)
            ID = scale(ID, to="m", _from=unit)
            effective_length = scale(effective_length, to="m", _from=unit)

        self.coil = None
        self.OD = OD
        self.ID = ID
        self.effective_length = effective_length


class Coil:
    PARALLEL = 0
    SERIES = 1

    DC = 0
    AC = 1

    CIRCLE = 0
    SQUARE = 1

    COPPER = 0
    DYOTEC_SILVER_INK = 1


    _materials = {COPPER:
                      {'resistivity': 1.72 * pow(10, -8),
                       'max_current_per_m2': 2500000,
                       '_max_current_per_m2': 0.126 / (0.00005 * 0.00005 * math.pi),
                       'density': 8960000},
                  DYOTEC_SILVER_INK:
                      {'resistivity': 66 * pow(10, -8),
                       'max_current_per_m2': 500000,
                       '_max_current_per_m2': 0.126 / (0.00005 * 0.00005 * math.pi * 5),
                       'density': 1700000}
                  # source: forum.allaboutcircuits.com/threads/
                  # coil-amp-rating-for-magnet-wire.71392/
                  }

    def __init__(self, wired_in, current, wire_d=None, material=COPPER, wire_geometry=CIRCLE, unit='mm', mag_Br=None):
        if material not in self._materials:
            print('WARNING: Material \'{}\' not defined, using \'copper\' instead.'.format(material))
            material = self.COPPER
        if wire_geometry not in [self.CIRCLE, self.SQUARE]:
            print('WARNING: wire_geometry \'{}\' not defined, using \'CIRCLE\' instead.'.format(wire_geometry))
            wire_geometry = self.CIRCLE

        assert current == self.DC or current == self.AC
        assert wired_in == self.PARALLEL or wired_in == self.SERIES

        # for now we ignore current type -- not implemented yet.
        self.tube = None
        self._wired = wired_in
        self._wire_d = None
        if wire_d:
            self.set_wire_d(wire_d, unit=unit)
        self.resistivity = self._materials.get(material).get('resistivity')
        self.max_current_per_m2 = self._materials.get(material).get('max_current_per_m2')
        self.wire_density = self._materials.get(material).get('density')

        self.wire_geometry = wire_geometry
        self._max_current = None
        self._current = None
        self._wire_area = None
        self._layer_count = None
        self._coil_height = None
        self._turns = None
        self.mag_Br = mag_Br

    def set_wire_d(self, wire_d, unit="mm"):
        if not wire_d:
            raise ValueError("wire_d not set!")

        if not (unit == 'mm' or unit == 'm'):
            print('Invalid unit "%s". Assigning "mm" for now.')
            unit = 'mm'

        if unit != 'm':
            self._wire_d = scale(wire_d, to=unit)
        self._max_current = self.max_current_per_m2 * self.get_wire_area()

    def set_current(self, current):
        self._current = current

    def set_layer_count(self, count):
        self._layer_count = count
        if self._wire_d and count:
            self._coil_height = count * self._wire_d

    def set_height(self, height, unit="mm"):
        if not (unit == 'mm' or unit == 'm'):
            print('Invalid unit "%s". Assigning "mm" for now.' % unit)
            unit = 'mm'

        if not self._wire_d:
            raise ValueError("wire_d variable is not set.")
        self._layer_count = height / self._wire_d
        self._coil_height = height
        if unit != 'm':
            self._layer_count = scale(self._layer_count, unit)
            self._coil_height = scale(self._layer_count, unit)

    def get_height(self, _layer_count=0, unit='m'):
        if self._coil_height:
            return scale(self._coil_height, unit)
        else:
            if _layer_count:
                return scale(_layer_count * self._wire_d, unit)
            elif self._layer_count:
                return scale(self._layer_count * self._wire_d, unit)
        return None
    height = property(get_height)

    def get_OD(self, _layer_count=0, unit='m'):
        if _layer_count == 0 and self._layer_count:
            _layer_count = self._layer_count
        return scale(self.get_height(_layer_count) * 2 + self.tube.OD, unit)
    OD = property(get_OD)

    def get_avg_D(self, _layer_count=0, unit='m'):
        if _layer_count == 0 and self._layer_count:
            _layer_count = self._layer_count
        return scale(self.get_height(_layer_count) + self.tube.OD, unit)
    avg_D = property(get_avg_D)

    def get_ID(self, unit='m'):
        return scale(self.tube.OD, unit)
    ID = property(get_ID)

    def get_length(self, unit='m'):
        return scale(self.tube.effective_length, unit)
    length = property(get_length)

    def get_wire_length(self, layer_count=0, _wire_d=None, unit='m'):
        if layer_count == 0 and self._layer_count:
            layer_count = self._layer_count
        if self._wire_d and not _wire_d:
            _wire_d = self._wire_d
        elif not _wire_d and not self.get_wire_d():
            raise ValueError("wire_d not set!")
        _length = 0.
        for _layer in range(int(layer_count)):
            _length += (self.tube.effective_length / _wire_d) * math.pi * (self.get_ID() + _wire_d * (_layer - 0.5))

        return scale(_length, unit)
    wire_length = property(get_wire_length)

    def get_number_of_turns(self, layer_count=0, _wire_d=None):
        if layer_count == 0 and self._layer_count:
            layer_count = self._layer_count
        if self._wire_d and not _wire_d:
            _wire_d = self._wire_d
        elif not _wire_d and not self.get_wire_d():
            raise ValueError("wire_d not set!")
        return layer_count * self.tube.effective_length / _wire_d
    number_of_turns = property(get_number_of_turns)

    def get_layer_count(self):
        return self._layer_count
    layer_count = property(get_layer_count)

    def get_wire_d(self, unit='m'):
        if self._wire_d:
            return scale(self._wire_d, unit)
        return None
    wire_d = property(get_wire_d)

    def get_wire_area(self, _wire_d=None, unit=u"m\u00B2"):
        if self._wire_d and not _wire_d:
            _wire_d = self._wire_d
        elif not _wire_d and not self.get_wire_d():
            raise ValueError("wire_d not set!")
        if self.wire_geometry == self.CIRCLE:
            return scale(math.pi * pow(_wire_d / 2, 2), unit, mag=2)
        elif self.wire_geometry == self.SQUARE:
            return scale(pow(_wire_d, 2), unit, _from=u"m\u00B2", mag=2)
        else:
            raise ValueError("Unexpected wire_geometry '%s'" % self.wire_geometry)
    wire_area = property(get_wire_area)

    def get_volume(self, layer_count=0, _wire_d=None, unit=u"m\u00B3"):
        if layer_count == 0 and self._layer_count:
            layer_count = self._layer_count
        if self._wire_d and not _wire_d:
            _wire_d = self._wire_d
        elif not _wire_d and not self.get_wire_d():
            raise ValueError("wire_d not set!")
        mag = "" if unit == u"m\u00B3" else unit
        return self.get_wire_length(layer_count=layer_count, _wire_d=_wire_d, unit=mag+"m") * \
               self.get_wire_area(_wire_d=_wire_d, unit=mag+u"m\u00B3")
    volume = property(get_volume)

    def get_mass(self, layer_count=0, _wire_d=None, unit='g'):
        return scale(self.wire_density, unit)  * self.get_wire_area(_wire_d=_wire_d) * self.get_wire_length(layer_count=layer_count,
                                                                                           _wire_d=_wire_d)
    mass = property(get_mass)

    def get_resistance(self, layer_count=0, _wire_d=None, unit=u'\u2126'):
        if layer_count == 0 and self._layer_count:
            layer_count = self._layer_count
        if self._wire_d and not _wire_d:
            _wire_d = self.get_wire_d()
        elif not _wire_d and not self._wire_d:
            raise ValueError("wire_d not set!")
        return scale(
            self.resistivity *
            (1. / layer_count if self._wired == Coil.PARALLEL else 1) *
            self.get_wire_length(_wire_d=_wire_d,
                                 layer_count=layer_count) /
            self.get_wire_area(_wire_d=_wire_d), unit)
    resistance = property(get_resistance)

    def get_current(self, _wire_d=None, unit='A'):
        if self._current:
            return scale(self._current, unit)
        elif self._max_current:
            return scale(self._max_current, unit)
        else:
            return self.get_max_current(_wire_d=_wire_d, unit=unit)
    current = property(get_current)

    def get_max_current(self, _wire_d=None, unit='A'):
        if _wire_d:
            return scale(self.max_current_per_m2 * self.get_wire_area(_wire_d=_wire_d), unit)
        if self._max_current:
            return scale(self.get_max_current, unit)
        elif self._wire_d:
            return scale(self.resistivity * self.get_wire_length / self.get_wire_area, unit)
        else:
            raise ValueError("wire_d not set!")
    max_current = property(get_max_current)

    def calculate_magnetic_field(self, _coil_layers=None, z=0.0):
        """
        :param z: air gap - rod's distance from top of actuator (m)
        :return: B(z)
        """
        mu = 4.0 * math.pi * pow(10, -7)

        if not self._wire_d:
            return None
        assert (self._current or self._max_current) and (
                self._layer_count or _coil_layers) and self._wire_d and self.get_length and self.get_ID

        if _coil_layers:
            _coil_layers = _coil_layers
        else:
            _coil_layers = self._layer_count

        _coil_height = _coil_layers * self.get_wire_d()
        L = self.get_length()
        D = self.get_ID()
        d = D + _coil_height
        N = self.get_length() * _coil_layers / self.get_wire_d()

        if self.get_current():
            I = self.get_current()
        else:
            I = self.get_max_current()

        # print(coil_height, L, D, d, N, I)
        b_z = ((mu * N * I / (2 * L * (D - d))) * (L + (2 * z)) * \
               math.log((D + math.sqrt(D * D + pow(L + 2 * z, 2))) /
                        (d + math.sqrt(d * d + pow(L + 2 * z, 2)))),
               (mu * N * I / (2 * L * (D - d))) * (L - 2 * z) * \
               math.log((D + math.sqrt(D * D + pow(L + 2 * z, 2))) /
                        (d + math.sqrt(d * d + pow(L + 2 * z, 2)))))  # vector
        return b_z

    def calculate_force_between_plunger_and_coil(self, Bsol_z=None, Bmag=1.35, coil_layers=None, z=0.0):
        if not Bsol_z:
            Bsol_z = self.calculate_magnetic_field(_coil_layers=coil_layers, z=z)

        if Bsol_z == None:
            return 0

        if self.mag_Br:
            Bmag = self.mag_Br

        if coil_layers:
            _coil_layers = coil_layers
        else:
            _coil_layers = self._layer_count

        d = self.tube.ID
        A = math.pi * pow(d / 2 + (self.tube.OD - self.tube.ID) / 2, 2)
        mu = 4.0 * math.pi * pow(10, -7)

        f_z = (Bsol_z[0] - abs(Bsol_z[1])) * Bmag * A / mu
        return f_z
