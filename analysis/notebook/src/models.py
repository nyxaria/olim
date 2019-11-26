# coding: utf-8

import math

magnitudes = {'G': 9,
              'M': 6,
              'k': 3,
              '': 0,
              'c': -2,
              'm': -3,
              '\u03BC': -6,
              'n': -9}


def scale(var, unit="", _to=None, _from=None, inverse=False):
    if _to is None and _from is None:
        _from = ''
        _to = unit[0] if len(unit) > 1 else unit
    else:
        if len(_to) > 0:
            _to = _to[0]
        if len(_from) > 0:
            _from = _from[0]

    if _to not in magnitudes.keys() or _from not in magnitudes.keys():
        print('Invalid units "%s" "%s". Fix your shit!' % (_to, _from))
    return var * pow(10, magnitudes.get(_from) - magnitudes.get(_to, 0))


class Tube:
    def __init__(self, OD, ID, effective_length, unit='mm'):
        if not (unit == 'mm' or unit == 'm'):
            print('Invalid unit "%s". Assigning "mm" for now.' % unit)
            unit = 'mm'

        if unit != 'm':
            OD = scale(OD, unit[:-1], _from=unit[0], _to="")
            ID = scale(ID, unit[:-1], _from=unit[0], _to="")
            effective_length = scale(effective_length, _from=unit[0], _to="")

        self.OD = OD
        self.ID = ID
        self.effective_length = effective_length


class Coil:
    PARALLEL = 0
    SERIES = 1

    DC = 0
    AC = 1

    _materials = {'copper':
                      {'resistivity': 1.72 * pow(10, -8),
                       'max_current_per_m2': 2500000,
                       '_max_current_per_m2': 0.126 / (0.00005 * 0.00005 * math.pi)}
                  # source: forum.allaboutcircuits.com/threads/
                  # coil-amp-rating-for-magnet-wire.71392/
                  }

    def __init__(self, wired_in, current, wire_d=None, material='copper', unit='mm', mag_Br=None):
        if material not in self._materials:
            print('WARN: Material \'{}\' not defined, using \'copper\' instead.'.format(material))
            material = 'copper'
        assert current == Coil.DC or current == Coil.AC
        assert wired_in == Coil.PARALLEL or wired_in == Coil.SERIES

        # for now we ignore current type -- not implemented yet.

        self.wired = wired_in
        self.wire_d = None
        if wire_d:
            self.set_wire_d(wire_d, unit=unit)
        self.resistivity = self._materials.get(material).get('resistivity')
        self.max_current_per_m2 = self._materials.get(material).get('max_current_per_m2')
        self.max_current = None
        self.current = None
        self.wire_area = None
        self.layer_count = None
        self.layer_height = None
        self.turns = None
        self.mag_Br = mag_Br

    def set_wire_d(self, wire_d, unit="mm"):
        if not wire_d:
            raise ValueError("wire_d not set!")

        if not (unit == 'mm' or unit == 'm'):
            print('Invalid unit "%s". Assigning "mm" for now.')
            unit = 'mm'

        if unit != 'm':
            self.wire_d = scale(wire_d, unit=unit, _to='', _from='m')
        self.max_current = self.max_current_per_m2 * self.get_wire_area()

    def set_current(self, current):
        self.current = current

    def set_layer_count(self, count):
        self.layer_count = count
        if self.wire_d and count:
            self.coil_height = count * self.wire_d

    def set_coil_height(self, height, unit="mm"):
        if not (unit == 'mm' or unit == 'm'):
            print('Invalid unit "%s". Assigning "mm" for now.' % unit)
            unit = 'mm'

        if not self.wire_d:
            raise ValueError("wire_d variable is not set.")
        self.layer_count = height / self.wire_d
        self.coil_height = height
        if unit != 'm':
            self.layer_count = scale(self.layer_count, unit[:-1])
            self.coil_height = scale(self.layer_count, unit[:-1])

    def get_layer_height(self, _layer_count=None, unit='m'):
        if self.layer_height:
            return scale(self.layer_height, unit[:-1])
        else:
            if _layer_count:
                return scale(_layer_count * self.wire_d, unit[:-1])
            elif self.layer_count:
                return scale(self.layer_count * self.wire_d, unit[:-1])
        return None

    def get_coil_length(self, tube, layer_count=0, wire_d=None, unit='m'):
        if layer_count == 0 and self.layer_count:
            layer_count = self.layer_count
        if self.wire_d:
            wire_d = self.wire_d
        elif not wire_d and not self.wire_d:
            raise ValueError("wire_d not set!")
        length = 0.
        for layer in range(int(layer_count)):
            length += (tube.effective_length / wire_d) * math.pi * (tube.OD + wire_d * (layer - 0.5))
        return scale(length, unit=unit[:-1])

    def get_number_of_turns(self, tube, layer_count=0, wire_d=None):
        if layer_count == 0 and self.layer_count:
            layer_count = self.layer_count
        if self.wire_d:
            wire_d = self.wire_d
        elif not wire_d and not self.wire_d:
            raise ValueError("wire_d not set!")
        return layer_count * tube.effective_length / wire_d
        
    def get_coil_mass(self, tube, layer_count=0, wire_d=None, unit='g'):
        return scale(8940000 * self.get_wire_area(wire_d=wire_d) * self.get_coil_length(tube, layer_count=layer_count,
                                                                                        wire_d=wire_d), unit=unit[:-1])

    def get_wire_d(self, unit='m'):
        return scale(self.wire_d, unit=unit[:-1])

    def get_wire_area(self, wire_d=None, unit='m'):
        if self.wire_d and not wire_d:
            wire_d = self.wire_d
        elif not wire_d and not self.wire_d:
            raise ValueError("wire_d not set!")
        return scale(math.pi * pow(wire_d / 2, 2), unit=unit[:-1])

    def get_resistance(self, tube, layer_count=0, wire_d=None, unit=u'\u2126'):
        if layer_count == 0 and self.layer_count:
            layer_count = self.layer_count
        if self.wire_d:
            wire_d = self.wire_d
        elif not wire_d and not self.wire_d:
            raise ValueError("wire_d not set!")
        return scale(
            self.resistivity *
            (1. / layer_count if self.wired == Coil.PARALLEL else 1) *
            self.get_coil_length(tube,
                                 wire_d=wire_d,
                                 layer_count=layer_count) /
            self.get_wire_area(wire_d=wire_d), unit=unit[:-1])

    def get_current(self, tube, wire_d=None, unit='A'):
        if self.current:
            return self.current
        elif self.max_current:
            return self.max_current
        else:
            return self.get_max_current(tube, wire_d=wire_d, unit=unit)

    def get_max_current(self, tube, wire_d=None, unit='A'):
        if wire_d:
            return scale(self.max_current_per_m2 * self.get_wire_area(wire_d=wire_d), unit=unit[:-1])
        if self.max_current:
            return scale(self.max_current, unit[:-1])
        elif self.wire_d:
            return scale(self.resistivity * self.get_coil_length(tube) / self.get_wire_area(), unit=unit[:-1])
        else:
            raise ValueError("wire_d not set!")

    def calculate_magnetic_field(self, tube, coil_layers=None, z=0.0):
        """
        :param z: air gap - rod's distance from top of actuator (m)
        :return: B(z)
        """
        mu = 4.0 * math.pi * pow(10, -7)

        assert (self.current or self.max_current) and (
            self.layer_count or coil_layers) and self.wire_d and tube.effective_length and tube.OD

        if coil_layers:
            _coil_layers = coil_layers
        else:
            _coil_layers = self.layer_count

        coil_height = _coil_layers * self.wire_d
        L = tube.effective_length
        D = tube.OD
        d = D + coil_height
        N = tube.effective_length * _coil_layers / self.wire_d

        if self.current:
            I = self.current
        else:
            I = self.max_current

        # print(coil_height, L, D, d, N, I)
        b_z = ((mu * N * I / (2 * L * (D - d))) * (L + (2 * z)) * \
               math.log((D + math.sqrt(D * D + pow(L + 2 * z, 2))) /
                        (d + math.sqrt(d * d + pow(L + 2 * z, 2)))),
               (mu * N * I / (2 * L * (D - d))) * (L - 2 * z) * \
               math.log((D + math.sqrt(D * D + pow(L + 2 * z, 2))) /
                        (d + math.sqrt(d * d + pow(L + 2 * z, 2)))))  # vector
        return b_z

    def calculate_force_between_plunger_and_coil(self, tube, Bsol_z=None, Bmag=1.35, coil_layers=None, z=0.0):
        if not Bsol_z:
            Bsol_z = self.calculate_magnetic_field(tube, coil_layers=coil_layers, z=z)

        if self.mag_Br:
            Bmag = self.mag_Br

        if coil_layers:
            _coil_layers = coil_layers
        else:
            _coil_layers = self.layer_count

        d = tube.ID
        A = math.pi * pow(d / 2 + (tube.OD - tube.ID) / 2, 2)
        mu = 4.0 * math.pi * pow(10, -7)

        f_z = (Bsol_z[0] - abs(Bsol_z[1])) * Bmag * A / mu
        return f_z
