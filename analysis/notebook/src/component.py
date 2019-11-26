# coding: utf-8

from ipywidgets import widgets


class Component:

    def __init__(self):
        self.desc_width = 75
        self.slider_width = 550

    def title(self, text="", name="title"):
        return widgets.HTML(
            text.replace('\n', "<br/>"),
            layout=widgets.Layout(width='99%', grid_area=name)
        )

    def multi_select(self, callback_method, _analyser, options, rows=6, description="", variable="", width='100%'):
        _analyser.data[variable] = []
        multi_select = widgets.SelectMultiple(
            options=options,
            rows=rows,
            description=description,
            disabled=False,
            layout=widgets.Layout(width=width, grid_area=variable))

        multi_select.observe(callback_method, ['value'])

        return multi_select

    def select(self, callback_method, _analyser, options, variable="", description="",
               index=0, width='100%', height='100%', disabled=False):
        _analyser.data[variable] = [options[index]]
        select = widgets.Select(
            options=options,
            value=options[index],
            rows=1,
            description=description,
            disabled=disabled,
            indent=False,
            layout=widgets.Layout(width=width, height=height, grid_area=variable))

        select.observe(callback_method, ['value'])
        return select

    def slider(self, callback_method, _analyser, variable="", description="", increment=0, disabled=False, min=1):
        _analyser.data[variable] = increment

        increment_slider = widgets.IntSlider(
            value=increment,
            min=min,
            max=50,
            step=1,
            description=description,
            disabled=disabled,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format='d',
            layout=widgets.Layout(width='{}px'.format(self.slider_width), grid_area=variable)
        )

        increment_slider.style.description_width = '{}px'.format(self.desc_width)
        increment_slider.observe(callback_method, ['value'])

        return increment_slider

    def range_slider(self, callback_method, _analyser,
                     variable="", description="",
                     range=(0,0), max=500, step=1,
                     readout_format='d'):
        _analyser.data[variable] = range

        range_slider = widgets.FloatRangeSlider(
            value=range,
            min=0,
            max=max,
            step=step,
            description=description,
            disabled=False,
            continuous_update=False,
            orientation='horizontal',
            readout=True,
            readout_format=readout_format,
            layout=widgets.Layout(width='{}px'.format(self.slider_width), grid_area=variable)
        )

        range_slider.style.description_width = '{}px'.format(self.desc_width)
        range_slider.observe(callback_method, ['value'])
        return range_slider

    def button(self, text="Button"):
        return widgets.Button(description=text)

    def pack(self, children, layout, template_rows="auto auto auto", template_columns="33% 34% 33%", name="grid", width="100%"):

        return widgets.GridBox(children=children,
                               layout=widgets.Layout(
                                   width=width,
                                   grid_gap='0px 0px',
                                   grid_template_rows=template_rows,
                                   grid_template_columns=template_columns,
                                   grid_template_areas=layout,
                                   grid_area=name)
                               )