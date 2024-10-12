import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt



class Styler(object):
	def __init__(self):
		self.__valid_operators = ['>', '>=', '<', '<=', '==']

		self._elewise_alt_txt_color = 'white'
		self._elewise_alt_bg_color = ''
		self._elewise_style_store = defaultdict(list)

		self._hidden_index = True
		self._hover = True
		self._alt_row_colors = True
		self._leftalign_firstcol = True
		self._precision = 2

		self.__subset = list()
		self.__format = None
		self.__text_fontsize = None
		self.__column_width = '75px'
		self.__column_fontsize = '12pt'
		self.__colidx_color = 'darkorange'
		self.__row_even_bgcolor = 'dimgray'
		self.__row_odd_bgcolor = 'darkgrey'
		self._column_properties = self._get_default_column_properties()

		self.__maxcol_data = False
		self.__maxrow_data = False
		self.__mincol_data = False
		self.__minrow_data = False
		self.__max_color = 'lemonchiffon'
		self.__min_color = 'lightsalmon'

		self.__colormap_row = None
		self.__colormap_col = None

	def _validate_operator(self, op):
		if op not in self.__valid_operators:
			valid_op_strs = ', '.join(self.__valid_operators)
			err = "Operator %s is not valid.\nValid Operators are; %s"
			err = err % (op, valid_op_strs)
			raise NotImplementedError(err)

	def _validate_bool(self, bool_val):
		bools = [True, False]
		if bool_val not in bools:
			err = "Input of %s is not valid. Valid inputs are True and False" % bool_val
			raise NotImplementedError(err)

	def _validate_minmax(self, minmax):
		minmaxs = ['min', 'max']
		if minmax not in minmaxs:
			err = "Input of %s is not valid. Valid inputs are 'min' and 'max'" % minmax
			raise NotImplementedError(err)

	def _validate_subset(self, subset):
		if not isinstance(subset, list):
			subset = [subset]

		return subset

	def _get_default_column_properties(self):
		props = {'width' : self.__column_width,
				 'max-width' : self.__column_width,
				 'text-align': 'center',
				 'background-color' : self.__row_even_bgcolor,
				 'color' : self.__colidx_color,
				 'font-size' : self.__column_fontsize}
		return props

	def set_precision(self, precision_int):
		prec_int = int(precision_int)
		self._precision = prec_int

	def set_default_textcolor(self, color):
		self._elewise_alt_txt_color = color

	def set_column_fontsize(self, fontsize):
		size = str(fontsize).replace('pt', '')
		size += 'pt'
		self.__column_fontsize = size
		self._column_properties['font-size'] = size

	def set_text_fontsize(self, fontsize):
		size = str(fontsize).replace('pt', '')
		size += 'pt'
		self.__text_fontsize = size

	def set_alt_row_colors(self, bool_val, oddcolor = None, evencolor = None):
		self._validate_bool(bool_val)
		self._alt_row_colors = bool_val
		if oddcolor is not None:
			self.__row_odd_bgcolor = oddcolor

		if evencolor is not None:
			self.__row_even_bgcolor = evencolor

	def set_default_bgcolor(self, color):
		col_to_store = color
		self._elewise_alt_bg_color = col_to_store

	def set_default_col_idx_color(self, color):
		col_to_store = color
		self.__colidx_color = col_to_store

	def set_column_width(self, width):
		width_to_store = width
		self._column_width = width_to_store
		self._column_properties['width'] = width_to_store
		self._column_properties['max-width'] = width_to_store

	def set_hidden_index(self, bool_val):
		self._validate_bool(bool_val)
		self._hidden_index = bool_val

	def set_hover(self, bool_val):
		self._validate_bool(bool_val)
		self._hover = bool_val

	def set_subset(self, subset):
		subset = self._validate_subset(subset)
		self.__subset = subset

	def set_leftalign_first_col(self, bool_val):
		self._validate_bool(bool_val)
		self._leftalign_firstcol = bool_val

	def add_textcolor_constraint(self, color, operator, condition_value):
		self._validate_operator(operator)
		# self._validate_subset(subset)
		self._elewise_style_store['color'].append((color, operator, condition_value))

	def add_bgcolor_constraint(self, color, operator, condition_value):
		self._validate_operator(operator)
		self._elewise_style_store['background-color'].append((color, operator, condition_value))

	def add_colormap_col(self, colormap_str):
		cmap = plt.get_cmap(colormap_str)
		self.__colormap_col = cmap

	def add_colormap_row(self, colormap_str):
		cmap = plt.get_cmap(colormap_str)
		self.__colormap_row = cmap

	def add_color_max_row(self, bool_val, color=None):
		self._validate_bool(bool_val)
		if color is not None:
			self.__max_color = color
		self.__maxrow_data = bool_val

	def add_color_min_row(self, bool_val, color=None):
		self._validate_bool(bool_val)
		if color is not None:
			self.__min_color = color
		self.__minrow_data = bool_val

	def add_color_max_col(self, bool_val, color=None):
		self._validate_bool(bool_val)
		if color is not None:
			self.__max_color = color
		self.__maxcol_data = bool_val

	def add_color_min_col(self, bool_val, color=None):
		self._validate_bool(bool_val)
		if color is not None:
			self.__min_color = color
		self.__mincol_data = bool_val

	def add_format(self, format_dict):
		fdict = format_dict
		self.__format = fdict

	def _resolve_func_str_start(self, n):
		if n == 0:
			str_start = 'if'
		else:
			str_start = 'elif'
		return str_start

	def _construct_elewise_func(self, css_element, alt_color, func_name):
		string_list = list()
		for n, (c, op, cv) in enumerate(self._elewise_style_store[css_element]):

			str_start = self._resolve_func_str_start(n)

			ele_str = "{start} val {operator} {cond_val}: ret_val = '{true_color}'"
			ele_str = ele_str.format(start=str_start,
									 operator=op,
									 cond_val=cv,
									 true_color=c)
			string_list.append(ele_str)

		else_str = "else: ret_val = '%s'" % alt_color
		string_list.append(else_str)

		fund_head = "def %s(val): \n " % (func_name)
		func_body = ' \n '.join(string_list)
		func_tail = """\n return '{css}: %s' % (ret_val)""".format(css=css_element)
		func = fund_head + func_body + func_tail

		return func

	def _construct_textcolor_func(self):
		func = self._construct_elewise_func('color', self._elewise_alt_txt_color, "_color_vals")
		return func

	def _construct_bgcolor_func(self):
		func = self._construct_elewise_func('background-color', self._elewise_alt_bg_color, "_bg_color_vals")
		return func

	def _construct_minmax_func(self, color, minmax, func_name):
		self._validate_minmax(minmax)
		string_list = list()

		funcstr = """def {funcname}(s):
					crit = s == s.{minmax}()

					meets_crit = 'background-color: {true_color}'
					not_meets_crit = ''
					ret_val = [meets_crit if v else not_meets_crit for v in crit]
					return ret_val
					""".format(funcname=func_name, minmax=minmax, true_color=color)
		return funcstr

	def _construct_color_max(self):
		func = self._construct_minmax_func(self.__max_color, 'max', '_colormax')
		return func

	def _construct_color_min(self):
		func = self._construct_minmax_func(self.__min_color, 'min', '_colormin')
		return func

	def _clean_dataframe(self):
		th_props = list(self._column_properties.items())
		td_props = [('text-align', 'center')]
		tr_props = [('color', self._elewise_alt_txt_color)]

		if self._leftalign_firstcol:
			td_selector = 'td:not(:nth-child(2))'
			td_addin = {'selector' : 'td:nth-child(2)', 'props' : [('padding-left', '10px')]}
		else:
			td_selector = 'td'
			td_addin = dict()

		if self.__text_fontsize is not None:
			td_props.append(('font-size', self.__text_fontsize))

		table_styles = [{'selector' : 'th', 'props' : th_props},
						{'selector' : td_selector, 'props' : td_props},
						{'selector' : 'tr', 'props' : tr_props}]

		if bool(td_addin):
			table_styles.append(td_addin)
		
		if self._hidden_index:
			table_styles.append({'selector' : 'tr :first-child', 'props' : [('display', 'none')]})

		if self._alt_row_colors:
			odd_props = [('background-color', self.__row_odd_bgcolor)]
			even_props = [('background-color', self.__row_even_bgcolor)]
			table_styles.append({'selector' : 'tr:nth-child(odd)', 'props' : odd_props})
			table_styles.append({'selector' : 'tr:nth-child(even)', 'props' : even_props})

		if self._hover:
			table_styles.append({'selector' : 'tr:hover', 'props' : [('background-color', 'darkred')]})

		return table_styles

	def apply_styling(self, df):
		table_styles = self._clean_dataframe()
		df_styler = df.style.set_table_styles(table_styles).set_precision(self._precision)
		applymap = None
		applyfunc = None
		bg_gradient = None

		if not bool(self.__subset):
			self.__subset = df.columns.tolist()

		if bool(self._elewise_style_store['color']):
			funcstr = self._construct_textcolor_func()
			exec(funcstr)
			exec_func = locals()["_color_vals"]
			if applymap is None:
				applymap = getattr(df_styler, 'applymap')

			applymap(exec_func, subset=self.__subset)

		if bool(self._elewise_style_store['background-color']):
			funcstr = self._construct_bgcolor_func()
			exec(funcstr)
			exec_func = locals()["_bg_color_vals"]
			if applymap is None:
				applymap = getattr(df_styler, 'applymap')

			applymap(exec_func, subset=self.__subset)

		if (bool(self.__maxrow_data)) or (bool(self.__maxcol_data)):
			funcstr = self._construct_color_max()
			exec(funcstr)
			exec_func = locals()["_colormax"]
			if applyfunc is None:
				applyfunc = getattr(df_styler, 'apply')

			if bool(self.__maxrow_data):
				applyfunc(exec_func, axis=1, subset=self.__subset)
			else:
				applyfunc(exec_func, axis=0, subset=self.__subset)

		if (bool(self.__minrow_data)) or (bool(self.__mincol_data)):
			funcstr = self._construct_color_min()
			exec(funcstr)
			exec_func = locals()["_colormin"]
			if applyfunc is None:
				applyfunc = getattr(df_styler, 'apply')

			if bool(self.__minrow_data):
				applyfunc(exec_func, axis=1, subset=self.__subset)
			else:
				applyfunc(exec_func, axis=0, subset=self.__subset)

		if (self.__colormap_row is not None) or (self.__colormap_col is not None):
			if bg_gradient is None:
				bg_gradient = getattr(df_styler, 'background_gradient')

			if (self.__colormap_row is not None):
				bg_gradient(self.__colormap_row, axis=1, subset=self.__subset)
			else:
				bg_gradient(self.__colormap_col, axis=0, subset=self.__subset)

		if (self.__format is not None):
			format_func = getattr(df_styler, 'format')
			format_func(self.__format)

		return df_styler
