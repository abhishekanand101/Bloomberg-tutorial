import matplotlib.pyplot as plt
import matplotlib.colors
import ipywidgets
from IPython.display import display
import numpy as np
import pandas as pd


class HeatMap(object):
    def __init__(self, dataframe, colormap_name=None, title=None, layout_dict=None, column_text_color=None, button_css=None, include_index=True):
        self.widgets            = dict()
        self.data               = dataframe
        self.colormap_name      = colormap_name
        self.title              = title
        self.layout_dict        = layout_dict
        self.button_css         = button_css
        self.include_index      = include_index
        self.column_text_color  = column_text_color
        self.__sorted_vals      = sorted([x for x in dataframe.values.flatten() if not pd.isnull(x)])
        self.__colormap         = None
        self.__final_gui        = None
        self.__selected_vals    = list()

        self.__build_widget()

    def __get_colormap(self):
        """
        Summary:
            gets the colormap object from matplotlib
            based on the number of Non-NaN data points
        """
        if self.__colormap is None:
            # how many non-nan are in the data
            non_nan_ct = self.data.count().sum()
            # if i dont have a colormap loaded then load one
            if self.colormap_name is not None:
                cmap = plt.get_cmap(self.colormap_name, non_nan_ct)
                colors = [matplotlib.colors.rgb2hex(cmap(x)[:3]) for x in range(non_nan_ct)]
            else:
                # if not colormap is specified then everything will be white
                colors = ['white'] * non_nan_ct
            self.__colormap = colors
        else:
            colors = self.__colormap
        return colors

    def __build_html_column_widget(self, column_name):
        """
        Summary:
            builds a column widget in HTML to display column names
        """
        # set color of text in column
        if self.column_text_color is None:
            column_color = 'lightgreen'
        else:
            column_color = self.column_color
        # write column HTML string
        column_html_str_raw = "<b><center><font color='{color}'>{text}</b></center></font>"
        column_html_str = column_html_str_raw.format(color=column_color,
                                                     text=column_name)
        # make a widget
        column_widget = ipywidgets.HTML(column_html_str,
                                        layout=self.layout_dict)
        return column_widget

    def __button_callback(self, btn_obj):
        btn_location = self.widgets[btn_obj._model_id][0]
        if btn_obj.layout.border is None:
            new_border = '2px solid aqua'
            self.__selected_vals.append(btn_location)
        else:
            new_border = None
            self.__selected_vals.remove(btn_location)
        
        btn_obj.layout.border = new_border

    def __build_button(self, value):
        """
        Summary:
            generic function for creating buttons that are
            part of the colormap
        """
        colors = self.__get_colormap()
        # if the value isn't NaN then add coloring
        if not pd.isnull(value):
            val_position = self.__sorted_vals.index(value)
            color = colors[val_position]
            disabled=False
            val = str(round(value,1))

        else:
            # the value is NaN so make color dark gray
            color = 'dimgray'
            disabled = True
            val = str("-")

        # make the widget
        button = ipywidgets.Button(description=val,
                                   disbaled=disabled,
                                   layout=self.layout_dict,
                                   style={'button_color' : color})

        # add html css class to html rendered on app
        if self.button_css is not None:
            button.add_class(self.button_css)

        button.on_click(self.__button_callback)

        return button

    def __resolve_pixel_length_of_index(self, index):
        """
        Summary:
            Tries to solve the length a label widget
            should be, in pixels, based on the data
            that it needs to display
        """
        n_chars = [len(x) for x in index]
        n_pixels = [(z * 7) + 20 for z in n_chars]
        pixel_len = max(n_pixels)
        return pixel_len

    def __build_index_widgets(self, index):
        """
        Summary:
            for every sector we need to make a label widget
        """
        label_len = self.__resolve_pixel_length_of_index(index)
        lbl_layout = {'width' : '%spx' % label_len,
                      'min_width' : '%spx' % label_len,
                      'align_items' : 'center',
                      'align_content' : 'center',
                      'display' : 'flex',
                      'justify_content' : 'flex-end',
                      'justify_items' : 'center'}
        # make a list of label widgets
        index_label_list = [ipywidgets.Label(x, layout=lbl_layout) for x in index]
        # insert an empty label widget at the beginning of the list
        index_label_list.insert(0, ipywidgets.Label("", layout=lbl_layout))
        # reshape the list into an n X 1 array to stack with the heatmap buttons
        index_widgets = np.array(index_label_list).reshape((-1,1))
        return index_widgets

    def __build_title_widget_hbox(self, widget_matrix):
        """
        Summary:
            adds a title and index to the buttons of the heatmap widget
        """
        title_widget = self.__build_title_widget()

        if self.include_index:
            empty_layout = widget_matrix[-1,0].layout
            empty_widget = ipywidgets.Label("", layout=empty_layout)
            final_title_box = ipywidgets.HBox([empty_widget, title_widget])
        else:
            final_title_box = title_widget
        return final_title_box

    def __build_title_widget(self):
        html_str_raw = "<b><center><font color='{color}'>{text}</b></center></font>"
        html_str = html_str_raw.format(color="coral",
                                       text=self.title)
        title_html = ipywidgets.HTML(html_str, layout={'width' : '100%'})
        return title_html

    def __build_widget(self):
        """
        Summary:
            Builds a heatmap widget based on the data and styling
            provided to the class
        """
        # create an N x M matrix to store each button widget
        empty_matrix = np.empty(self.data.shape, dtype=object)

        # make a list to store all the column labeled widgets
        col_label_widgets = list()
        for col_num, col_name in enumerate(self.data.columns):
            # get the data series (column of data)
            data_series = self.data[col_name]
            # get the column name widget
            col_widget = self.__build_html_column_widget(col_name)
            col_label_widgets.append(col_widget)
            # for every value in the column we need to make a button and associate
            # a key with it
            for idx_num, (idx_name, value) in enumerate(data_series.iteritems()):
                key = (idx_name, col_name)
                button = self.__build_button(value)
                self.widgets[button._model_id] = (key, button)
                # store the button in our empty matrix
                empty_matrix[idx_num, col_num] = button
        # transform the empty matrix of buttons into one with column labels
        widget_matrix = np.vstack((np.array(col_label_widgets),empty_matrix))
        # check to see if we need to include the index (Sectors)
        if self.include_index:
            index_widgets = self.__build_index_widgets(self.data.index)
            widget_matrix = np.hstack((index_widgets, widget_matrix))
        # combine the column widgets of data into an HBox
        hbox_layout = {'overflow_x' : 'hidden'}
        widget_hboxes = [ipywidgets.HBox(row.tolist(), layout=hbox_layout) for row in widget_matrix]
        # check to see if we need to add a title to the entire heatmap
        if self.title is not None:
            title_box = self.__build_title_widget_hbox(widget_matrix)
            widget_hboxes.insert(0, title_box)
        # save the final heatmap widget
        final_widget = ipywidgets.VBox(widget_hboxes,
                                       layout={'overflow_x' : 'hidden'})
        self.__final_gui = final_widget

    def get_selected_indices(self):
        return self.__selected_vals

    def get_widget(self):
        """
        Summary:
            public method for exposing the gui
        """
        return self.__final_gui

    def add_key_to_widgets(self, new_key):
        """
        Summary:
            adds a new key to the tuple key that currently exists
        """
        for model_id, (key_tuple, obj) in self.widgets.items():
            new_key_tuple = key_tuple + (new_key,)
            self.widgets[model_id] = (new_key_tuple, obj)

    def close_widgets(self):
        for model_id, (key_tuple, obj) in self.widgets.items():
            obj.close()