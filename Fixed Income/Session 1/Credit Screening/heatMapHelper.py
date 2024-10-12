import ipywidgets
import heatMap
from IPython.display import display
import importlib
importlib.reload(heatMap)


class HeatMapHelper(object):
    def __init__(self):
        self.widgets = dict()
        self.heatmaps = dict()

        self.__build_widget()
        self.__load_button_css_props()

    def __build_widget(self):
        heatmap_container = ipywidgets.HBox([])
        self.widgets['heatmap_container'] = heatmap_container

    def __load_button_css_props(self):
        # create a custom css class for styling the buttons
        # in the heatmap
        btn_css = ('<style>'
                    '.go-btn{font-family:Calibri!important;'
                    'font-size:14px!important;'
                    'border-radius:5px!important;'
                    'font-weight: bold!important;'
                    'color:black!important;}'

                    '.go-btn:hover{background-color:aqua!important;'
                    'color:black!important;}'

                    '.go-btn:active{background-color:transparent!important;}'
                    '</style>'
                    )
        # push the css class to the juypter environment to
        # render the HTML/CSS
        display(ipywidgets.HTML(btn_css))

    def get_widget(self):
        return self.widgets['heatmap_container']

    def get_selected_cells(self):
        selected_cells = list()
        for hm_title, hm_obj in self.heatmaps.items():
            # [(AAA, Tech), ]
            selected_vals = hm_obj.get_selected_indices()
            if bool(selected_vals):
                if hm_title is not None:
                    selected_vals = [x + (hm_title,) for x in selected_vals]

                selected_cells += selected_vals

        return selected_cells

    def __display_heatmap_loading(self):
        w = self.widgets.get('heatmap_loading')
        if w is None:
            html_str = """
                        <center>
                            <p style = "font-size: 30px; color: lime;">Loading Heatmap</p>
                            <i class="fa fa-spinner fa-spin" style="color:lime; font-size: 50px;"></i>
                        </center>
                       """

            w = ipywidgets.HTML(html_str, layout={'min_height' : '400px'})
            w = ipywidgets.VBox([w], layout={'justify_content' : 'center',
                                             'align_items' : 'center'})
            self.widgets['heatmap_loading'] = w

        self.widgets['heatmap_container'].children = [w]

    def __close_old_heatmaps(self):
        for heatmap_title, heatmap_obj in self.heatmaps.items():
            heatmap_obj.close_widgets()

    def generate_heatmaps(self, name_and_df_list):
        # display heatmap loading
        self.__display_heatmap_loading()
        self.__close_old_heatmaps()
        # name_and_df_list = [('SHORT', short_df), ('MID', mid_df)]

        button_layout_dict = {'height' : '30px',
                              'width' : '60px',
                              'min_width' : '60px'}

        heatmaps = list()
        for n, (title, df) in enumerate(name_and_df_list):
            if n == 0:
                include_index = True
            else:
                include_index = False

            heatmap = heatMap.HeatMap(df,
                                      colormap_name='YlOrRd', # you can change with YlOrRd :)
                                      title=title,
                                      layout_dict=button_layout_dict,
                                      column_text_color=None,
                                      button_css='go-btn',
                                      include_index=include_index)
            heatmap_widget_vbox = heatmap.get_widget()

            self.heatmaps[title] = heatmap

            if n > 0:
                empty_box = ipywidgets.Label("", layout={'min_width' : '20px'})
                heatmaps.append(empty_box)

            heatmaps.append(heatmap_widget_vbox)

        self.widgets['heatmap_container'].children = heatmaps
