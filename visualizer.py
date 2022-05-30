import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np




class Data:
	def __init__(self, data_path):
		self.data_path = data_path
		self.data = None
		self.update_data()
	
	def update_data(self):
		data = pd.read_csv(self.data_path)
		data = data[data['m0'] != 0]
		self.data = data

	def get_data(self):
		return self.data

data = Data('data.csv')
df = data.get_data()
df['physical'] = ~df['Mh(1)'].isna()


nan_points = df[df['Mh(1)'].isna()]
points = df.dropna()

def sri_function(m):
	rel= 125. + (m/(m-125.))**(2)
	return rel
colors = ['#ff6d00','#ffc242', '#7b2cbf']

class ScatterPlot:
	def __init__(self, title):
		self.fig = make_subplots(
			rows=2,
			cols=2,
			row_heights=[0.3, 0.7],
			column_widths=[0.8, 0.2],
			vertical_spacing = 0.05,
			horizontal_spacing = 0.02,
			shared_yaxes=True,
			shared_xaxes=True)
		self.fig.update_layout(title=title)

	def add_histogram(self, df,x, color, group, vertical = False):
		"""
		Notes:
		- arg = name, adds the label
		"""
		if vertical:
			row, col = 2, 2
			self.fig.add_trace( go.Histogram(y =df[x], marker_color=color, showlegend=False,
									legendgroup=group, legendgrouptitle_text = group), row =row, col=col)
		else:
			row, col = 1, 1
			self.fig.add_trace( go.Histogram(x =df[x], marker_color=color, showlegend=False,
									legendgroup=group, legendgrouptitle_text = group), row =row, col=col)
		self.fig.update_layout(bargap=0, bargroupgap=0)

	def add_scatter(self, df,x,y, color, group, row=2, col=1):
		self.fig.add_trace(
			go.Scattergl(
				x=df[x],
				y=df[y],
				name = 'samples',
				mode='markers',
				marker=dict(size=2,color=color),
				legendgroup = group,
				legendgrouptitle_text = group), row = row, col = col)
		self.fig.update_xaxes(title_text=x, row=row, col=col)
		self.fig.update_yaxes(title_text=y, row=row, col=col)

##########
# Layout #
##########

st.header('Random Scan BLSSM')
st.write('Data from SPheno, HiggsBounds and HiggsSignals: {} points in total, {} converged into a physical\
 spectrum and {} didn\'t.'.format(len(df), len(points), len(nan_points)))
st.dataframe(df, 799,100)


st.subheader('Plots')

def plot_observables():
	axes = np.array([['Mh(1)', 'Mh(2)'], ['obsratio', 'csq(tot)']])
	axes_sb = axes.flatten()
	selected = points
	for ax in axes_sb:
		values = st.sidebar.slider(
				'Select a range for {}'.format(str(ax)),
				float(points[ax].min()), float(points[ax].max()), 
				(float(points[ax].min()), float(points[ax].max())))
		selected = selected[selected[ax] > values[0]]
		selected = selected[selected[ax] < values[1]]
		st.sidebar.write('Range: ', values)
	st.sidebar.write('Total points: ', len(points))
	st.sidebar.write('Total filtered points: ', len(selected))


	for x,y in axes:

		scatter_one = ScatterPlot(' {} vs {}'.format(y,x))
		if x == axes[0][0]:
			xx = np.linspace(0,115,200)
			yy = sri_function(xx)
			scatter_one.fig.add_trace(
					go.Scatter(
						x=xx,
						y = yy,
						mode='lines',
						name = 'Relation'), row=2, col =1)


		scatter_one.add_histogram(points, x, colors[2], 'Physical')
		scatter_one.add_histogram(points, y,  colors[2],'Physical',True )
		scatter_one.add_scatter(points, x, y, colors[2], 'Physical')

		scatter_one.add_histogram(selected, x, colors[0], 'Physical Filtered')
		scatter_one.add_histogram(selected, y,  colors[0],'Physical Filter',True )
		scatter_one.add_scatter(selected, x, y, colors[0], 'Physical Filter')

		st.plotly_chart(scatter_one.fig)

def plot_parameter_space():
	axes = [['m0', 'm12'], ['a0', 'tanbeta']]
	for x,y in axes:
		scatter_one = ScatterPlot('Parameter Space Random Scan: {} vs {}'.format(y,x))
		scatter_one.add_histogram(points, x, colors[0], 'Physical')
		scatter_one.add_histogram(nan_points, x, colors[2], 'Non-Physical')
		scatter_one.add_histogram(points, y,  colors[0],'Physical',True )
		scatter_one.add_histogram(nan_points, y,  colors[2], 'Non-Physical',True)
		scatter_one.add_scatter(points, x, y, colors[0], 'Physical')
		scatter_one.add_scatter(nan_points, x, y, colors[2], 'Non-Physical')
		st.plotly_chart(scatter_one.fig)
## Test

visualizations = ['Observables', 'Parameter Space']
option = st.sidebar.selectbox(
	'Select visualization:',
	visualizations
	)
if option == visualizations[0]:
	plot_observables()
if option == visualizations[1]:
	plot_parameter_space()

