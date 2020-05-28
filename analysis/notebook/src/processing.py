# coding: utf-8

import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt

from bokeh.models import Legend, HoverTool, WheelZoomTool
from bokeh.plotting import figure, show, reset_output, ColumnDataSource
from bokeh.io import output_notebook

from ipywidgets import widgets
from IPython.display import display, clear_output

from component import Component

from models import scale


def rreplace(s, old, new, occurrence=1):
    li = s.rsplit(old, occurrence)
    return new.join(li)


class Process:
    def __init__(self, coil, tube):
        self.coil = coil
        coil.tube = tube
        self.tube = tube
        tube.coil = coil
        self.component = Component()

        self._units = {
            'wire diameter': 'm',
            'length': 'm',
            'volume': u"m\u00B3",
            'mass': 'g',
            'resistance': u"\u2126",
            'current': 'A',
            'voltage': 'V',
            'power': 'W',
            'force': 'N',
            'wire_d': 'mm',
            'extension': 'm',
            'layers': ''}

    def explore_wire_diameter(self, debug=False, resolution=0.01):
        options = ['resistance', 'length', 'mass', 'volume', 'current', 'voltage', 'power']

        _analyser = Analyser()
        _analyser.units = self._units

        def create_graph(val):
            clear_output(wait=True)
            output_notebook(hide_banner=True)

            if val is None:
                pass
            elif val['owner'].layout.grid_area == "explore":  # disable unused selects
                _analyser.data["explore"] = val['new']
                for key, child in _analyser.unit_children.items():
                    child.disabled = key not in _analyser.data["explore"]
            else:
                _analyser.data[val['owner'].layout.grid_area] = val['new']
            display(_analyser.gui)
            for i in range(1):
                import time
                time.sleep(1)
            _analyser.explore_wire_diameter(self.coil, self.tube,
                                            params=list(_analyser.data["explore"]),
                                            units=_analyser.units,
                                            _start_d=_analyser.data["wire_d_range"][0],
                                            _end_d=_analyser.data["wire_d_range"][1] + resolution,
                                            _increment_d=resolution,
                                            _coil_layer_height=_analyser.data["coil_layer_height"],
                                            debug=debug)

        def update_units(val):
            _analyser.units[val.owner.layout.grid_area] = val.new
            create_graph(None)  # update

        # create unit selections
        units = ["G", "M", "k", "", "c", "m", '\u03BC', "n"]
        _analyser.unit_children = {opt: self.component.select(update_units, _analyser,
                                                              options=[s + self._units[opt] for s in units],
                                                              variable=opt,
                                                              index=3,
                                                              width='35px',
                                                              height='13px',
                                                              disabled=True)
                                   for opt in options}

        unit_layout = ('"%s"\n' * len(options)) % tuple(options)

        template_rows = (("%.1f" % (100. / len(options)) + "% ") * len(options))[:-1]
        unit_gui = self.component.pack(children=list(_analyser.unit_children.values()),
                                       layout=unit_layout,
                                       template_columns='100%',
                                       template_rows=template_rows,
                                       width="55px")

        children = [unit_gui,
                    self.component.multi_select(create_graph, _analyser, options=options,
                                                description="Explore Coil ", variable="explore",
                                                width='100%', rows=len(options)),
                    self.component.title('Wire Diameter (mm)', name='wire_title'),
                    self.component.range_slider(create_graph, _analyser,
                                                description="Range", variable="wire_d_range",
                                                range=(0.2, 1.2), step=resolution, max=2,
                                                readout_format='.{}f'.format(str(resolution).count("0"))),
                    self.component.title('Coil Height (mm)', name='coil_title'),
                    self.component.slider(create_graph, _analyser,
                                          description="Value", variable="coil_layer_height", increment=1)]

        _analyser.gui = self.component.pack(children=children,
                                            layout=
                                            '".. .. .. .."' +
                                            ('"explore grid .. .."' * len(options)) +
                                            '''
                                            ".. .. .. .."
                                            "wire_title .. .. .."
                                            "wire_d_range wire_d_range wire_d_range wire_d_range"
                                            ".. .. .. .."
                                            "coil_title .. .. .."
                                            "coil_layer_height coil_layer_height coil_layer_height coil_layer_height"
                                            ".. .. .. .."
                                            ''',
                                            template_columns='30% 12.5% 12.5% 45%',
                                            width='650px')

        create_graph(None)  # trigger update

    def explore_actuator_force(self):
        _analyser = Analyser()
        if self.coil.get_layer_count():
            display(self.component.title('Coil Layers set to %i. Please unset this if you wish to explore.'
                                         % self.coil.layer_count))
            b = self.component.button('Unset Coil Layers')

            def on_click_cb(b):
                self.coil.set_layer_count(None)
                self.explore_actuator_force()
                return
            display(b)
            b.on_click(on_click_cb)

            _analyser.explore_actuator_force(self.coil, self.tube, self._units)
            return

        def create_graph(val):
            clear_output(wait=True)
            output_notebook(hide_banner=True)

            if val is None:
                pass
            else:
                _analyser.data[val['owner'].layout.grid_area] = val['new']
            display(_analyser.gui)

            _analyser.explore_actuator_force(self.coil, self.tube, self._units,
                                             _start=_analyser.data["Range"][0], _end=_analyser.data["Range"][1] + 1,
                                             _increment=_analyser.data["Increment"])

        children = [self.component.title('Coil Layers'),
                    self.component.range_slider(create_graph, _analyser, description="Range", variable="Range",
                                                range=(0, 10), max=100),
                    self.component.slider(create_graph, _analyser, description="Increment", variable="Increment",
                                          increment=10, min=1)]

        _analyser.gui = self.component.pack(children=children,
                                            layout='''
                            ".. .. .."
                            "title title title"
                            "Range Range Range"
                            "Increment Increment Increment"
                            ''')

        create_graph(None)  # trigger update

    def out(self, s):
        return self.component.title(s)


class Analyser:
    def __init__(self):
        self.tableau20 = [(31, 119, 180), (174, 199, 232), (255, 127, 14), (255, 187, 120),
                          (44, 160, 44), (152, 223, 138), (214, 39, 40), (255, 152, 150),
                          (148, 103, 189), (197, 176, 213), (140, 86, 75), (196, 156, 148),
                          (227, 119, 194), (247, 182, 210), (127, 127, 127), (199, 199, 199),
                          (188, 189, 34), (219, 219, 141), (23, 190, 207), (158, 218, 229)]
        self.data = {}
        clear_output(wait=True)

    def generic_explore(self, df, x, y, identifier, x_label="", y_label="", title="Title", legend=None, _units={}):
        assert type(y) is list

        p = figure(plot_width=900, plot_height=500,
                   title=title,
                   x_axis_label=x_label, y_axis_label=y_label,
                   tools=["save,pan,wheel_zoom,"])

        legend_items = []
        for i, _id_key in enumerate(reversed(list(df[identifier].keys()))):
            for _y in y:
                source = ColumnDataSource(data={
                    x: df[identifier][_id_key][x],  # python datetime object as X axis
                    _y: df[identifier][_id_key][_y],
                    identifier: [_id_key.lower()] * len(df[identifier][_id_key][x]),
                })

                if "layers" in list(df[identifier][_id_key].keys()):
                    source.data['layers'] = df[identifier][_id_key]["layers"]
                line = p.line(x, _y, line_width=2, source=source,
                              color=self.tableau20[i])
                y_unit = " (%s)" % _units.get(_y, "") if _units.get(_y, "") != "" else ""

                if i == 0:
                    accuracy_x = "{1.111}" if _units.get(x, "") == "mm" else "{1.111}"  # TODO generalize this and tooltips
                    accuracy_y = "{1.111}" if _y == "length" else "{1.111}"  # TODO generalize this and tooltips

                    tips = [(_y.capitalize() + y_unit, "@%s" % _y + "{1.111}"),
                            (x.capitalize() + " (%s)" % _units.get(x, ""), "@%s" % x + accuracy_x)]
                    if "layers" in list(df[identifier][_id_key].keys()):
                        tips += [("Layers", "@layers")]

                    p.add_tools(HoverTool(renderers=[line],
                                          tooltips=tips,
                                          mode='vline'))
                else:
                    p.add_tools(HoverTool(renderers=[line],
                                          tooltips=[(_y.capitalize() + y_unit, "@%s" % _y + "{1.111}")],
                                          mode='vline'))

                legend_items.append((legend[i] if legend else _id_key, [line]))
                i += 1
            i -= 1
        p.toolbar.active_scroll = p.select_one(WheelZoomTool)
        _legend = Legend(items=legend_items)
        p.add_layout(_legend, 'right')
        p.title.align = 'center'
        # p.toolbar_location = None
        show(p)

    def explore_wire_diameter(self, coil, tube, params, units,
                              _increment_d=0.01, _start_d=0, _end_d=2.,
                              _coil_layer_height=50, debug=True):
        if len(params) == 0:
            return
        data = {"coil_height": {}}

        _start_d = _increment_d / 10 if _start_d == 0 else _start_d  # enforce non-zero value
        _start_d /= 1000
        _end_d /= 1000
        _increment_d /= 1000
        wire_dias = np.arange(_start_d, _end_d, _increment_d)

        _coil_layer_height = _end_d if _coil_layer_height < _start_d else _coil_layer_height
        _coil_layer_height /= 1000.
        count = str(_coil_layer_height)
        i = -1
        data["coil_height"][count] = {_param: [] for _param in params + ['wire_d', 'layers']}
        for wire_d in wire_dias:
            data["coil_height"][count]["wire_d"].append(wire_d * 1000)
            layer_count = int((_coil_layer_height / wire_d) + 0.5)
            data["coil_height"][count]["layers"].append(scale(layer_count, units["layers"]))
            i += 1
            if(i % 100 == 0):
                i = 0

            for param in params:
                if param == "length":
                    data["coil_height"][count][param].append(scale(coil.get_wire_length(_wire_d=wire_d,
                                                                                        layer_count=layer_count),
                                                                   units[param]))
                if param == "volume":
                    data["coil_height"][count][param].append(coil.get_volume(_wire_d=wire_d,
                                                                                   layer_count=layer_count,
                                                                                   unit=units[param]))
                if param == "mass":
                    data["coil_height"][count][param].append(scale(coil.get_mass(_wire_d=wire_d,
                                                                                 layer_count=layer_count),
                                                                   units[param]))
                elif param == "resistance":
                    data["coil_height"][count][param].append(scale(coil.get_resistance(_wire_d=wire_d,
                                                                                       layer_count=layer_count),
                                                                   units[param]))
                elif param == "current":
                    data["coil_height"][count][param].append(scale(coil.get_max_current(_wire_d=wire_d),
                                                                   units[param]))
                elif param == "voltage":
                    data["coil_height"][count][param].append(scale(coil.get_max_current(_wire_d=wire_d) *
                                                                   coil.get_resistance(_wire_d=wire_d,
                                                                                       layer_count=layer_count),
                                                                   units[param]))
                elif param == "power":
                    data["coil_height"][count][param].append(scale(coil.get_max_current(_wire_d=wire_d) *
                                                                   coil.get_max_current(_wire_d=wire_d) *
                                                                   coil.get_resistance(_wire_d=wire_d,
                                                                                       layer_count=layer_count),
                                                                   units[param]))
                if i % 100 == 0 and debug:
                    print("wire_d=%.2fmm" % (wire_d * 1000), "layer_count=%.2f" % layer_count,
                          "%s=%.2f" % (param, data["coil_height"][count][param][-1]))

        legend_items = []
        for param in params:
            if units[param] != "":
                legend_items.append("{} ({})".
                                    format(param.capitalize(), units[param]))
            else:
                legend_items.append("Layer Count")

        title = (('%s, ' * len(params) % tuple(params))[:-2]) + \
                " against wire diameter for a fixed {}mm high coil".format(_coil_layer_height * 1000.)
        title = rreplace(title, ',', ' &').capitalize()
        ylabel = ""
        for param in params:
            if (param != 'layers'):
                ylabel += '%s (%s) & ' % (param, units[param])
            else:
                ylabel += "Layer Count & "
        ylabel = ylabel[:-3]
        self.generic_explore(df=pd.DataFrame(data),
                             x="wire_d", y=params, identifier="coil_height",
                             x_label="Wire Diameter (mm)", y_label=ylabel,
                             title=title,
                             legend=legend_items,
                             _units=units)

    def explore_actuator_force(self, coil, tube, units, _increment=10, _start=20, _end=50, debug=False):
        data = {"coil_layers": {}}
        extension = np.arange(0, tube.effective_length + 0.001, 0.001)
        if coil.layer_count:
            _end = coil.layer_count + 1
            _increment = coil.layer_count
            _start = coil.layer_count
        else:
            _start = _increment if _start == 0 else _start  # enforce non-zero value

        for count in np.arange(_start, _end + 1, _increment):
            count = str(count)
            data["coil_layers"][count] = {"force": [], "extension": []}
            for z in extension:
                F = coil.calculate_force_between_plunger_and_coil(  z=z, coil_layers=int(float(count)), Bmag=1.22)
                if F == 0:
                    if coil.get_wire_d() == None:
                        print("coil.wire_d is not set!")
                        return
                data["coil_layers"][count]["force"].append(F)
                data["coil_layers"][count]["extension"].append(z)

        legend_items = []
        for i, layer_count in enumerate(sorted(list(data["coil_layers"].keys()), reverse=True)):
            legend_items.append("%s layers (%.2fmm height)" %
                                (layer_count, coil.get_height(_layer_count=int(float(layer_count)) * 1000)))

        self.generic_explore(df=pd.DataFrame(data),
                             x="extension", y=["force"], identifier="coil_layers",
                             x_label="Extension (m)", y_label="Force (N)",
                             title="Force against extension against {} for {}mm wire".format("coil layers",
                                                                                             coil.wire_d * 1000),
                             legend=legend_items,
                             _units=units)
