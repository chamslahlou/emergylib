from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import messagebox
from tkinter import filedialog


import math
import os

import emergylib.system as emsys


nodes = {}
links = {}
num_node = 0

NODE_SIZE_X = 20
NODE_SIZE_Y = 20

selected_node = None

selected_link = None

new_node = None

#history = []


def add_node(x, y):
	global num_node, selected_node, new_node

	num_node = find_new_label()  # internal node number

	label = str(num_node)

	var_label.set(label)

	# tkinter numbers
	id_node = canvas.create_rectangle(x, y, x+NODE_SIZE_X, y+NODE_SIZE_X, fill='light grey', tags='node')
	id_text = canvas.create_text(x+NODE_SIZE_X/2, y+NODE_SIZE_X/2, text=label, tags='node')

	nodes[id_node] = {'label':label, 'x':x, 'y':y, 'type':var_action.get(), 
					  'num':num_node, 
					  'id_text':id_text}

	if var_action.get() == 'source':
		nodes[id_node]['uev'] = 0.0

	select_node(selected_node)
	display_node_informations(selected_node)

	new_node = id_node
	#history.append(('node', id_node))

def set_link_informations(link):
	print('INFO LINKS', links)
	start, end = get_start_end(link)

	print('link =(', start, ',', end, ')')
	var_weight.set(links[(start, end)]['weight'])
	var_length.set(links[(start, end)]['length'])

	var_diameter.set(links[(start, end)]['diameter'])

	var_flow_rate.set(links[(start, end)]['flow_rate'])

	var_mass_density.set(links[(start, end)]['mass_density'])



def display_link_informations(link):

	start, end = get_start_end(link)

	if nodes[start]['type'] == 'split':
		entry_weight.config(state='normal')
	else:
		entry_weight.config(state='disabled')
	
	label_weight.grid(row=0, column=0, sticky='nw')
	entry_weight.grid(row=0, column=1)

	start, end = get_start_end(link)

	is_fast = links[(start, end)]['is_fast']
	var_is_fast.set(is_fast)

	check_is_fast.grid(row=1, column=0, sticky='nw')

	print('IS FAST=', is_fast)
	if not is_fast:

		label_length.grid(row=0, column=0, sticky='nw')
		entry_length.grid(row=0, column=1)

		label_diameter.grid(row=1, column=0, sticky='nw')
		entry_diameter.grid(row=1, column=1)

		label_mass_density.grid(row=2, column=0, sticky='nw')
		entry_mass_density.grid(row=2, column=1)

		label_flow_rate.grid(row=0, column=2, sticky='nw')
		entry_flow_rate.grid(row=0, column=3)


	else:
		init_link(selected_link)

		label_length.grid_remove()
		entry_length.grid_remove()

		label_diameter.grid_remove()
		entry_diameter.grid_remove()

		label_mass_density.grid_remove()
		entry_mass_density.grid_remove()

		label_flow_rate.grid_remove()
		entry_flow_rate.grid_remove()


def hide_link_informations():

	label_weight.grid_remove()
	entry_weight.grid_remove()

	check_is_fast.grid_remove()

	label_length.grid_remove()
	entry_length.grid_remove()

	label_diameter.grid_remove()
	entry_diameter.grid_remove()

	label_mass_density.grid_remove()
	entry_mass_density.grid_remove()

	label_flow_rate.grid_remove()
	entry_flow_rate.grid_remove()



def display_node_informations(node):
	#global selected_node

	print('display', node)
	label_uev.grid_remove()
	entry_uev.grid_remove()

	label_label.grid(row=0, column=0, sticky='w')
	entry_label.grid(row=0, column=1, sticky='w')

	label_type_text.grid(row=1, column=0, sticky='w')
	label_type_value.grid(row=1, column=1, sticky='w')

	if var_action.get() == 'delete':
		entry_uev.config(state='disabled')
	else:
		entry_uev.config(state='normal')

	if node is not None:
		label_type_text.grid(row=1, column=0, sticky='w')
		var_type.set(nodes[node]['type'])
		label_type_value.grid(row=1, column=1, sticky='w')

		if nodes[node]['type'] == 'source':
			label_uev.grid(row=2, column=0, sticky='w')
			var_uev.set(nodes[node]['uev'])
			entry_uev.grid(row=2, column=1)


def hide_node_informations():
	label_type_text.grid_remove()
	label_type_value.grid_remove()

	label_label.grid_remove()
	entry_label.grid_remove()

	label_uev.grid_remove()
	entry_uev.grid_remove()


def get_node(id_obj):
	print("   get_node", id_obj)
	print("      nodes =", nodes)
	for node in nodes:
		print("       node=", node)
		print("       id_text", nodes[node]['id_text'])
		if id_obj == node or id_obj == nodes[node]['id_text']:
			return node

def select_node(node):
	global selected_node

	if selected_node is not None:
		canvas.itemconfigure(selected_node, outline='black', width=1)
	
	selected_node = node

	if selected_node is not None:
		canvas.itemconfigure(selected_node, outline='red', width=2)
		var_type.set(nodes[selected_node]['type'])

	print('SELECTED NODE:', selected_node)


def find_new_label():
	num_nodes = [nodes[node]['num'] for node in nodes]

	if num_nodes == []:
		return 0

	for i in range(max(num_nodes)+1):
		if not i in num_nodes:
			print(i, 'est absent')
			return i

	return max(num_nodes)+1


def delete_node(node):

	removed_links = []
	for start, end in links:

		if start == node or end == node:
			removed_links.append((start, end))
	
	for start, end in removed_links:
		id_arrow = links[(start, end)]['id_arrow']
		canvas.delete(id_arrow)
		del links[(start, end)]
		
	canvas.delete(nodes[node]['id_text'])
	canvas.delete(node)
	del nodes[node]

	select_node(None)
	select_link(None)


def get_start_end(link):
	for start, end in links:
		if links[(start, end)]['id_arrow'] == link:
			return (start, end)


def delete_link(link):
	print('DELETE LINK', link)
	canvas.delete(link)
	
	start, end = get_start_end(link)
	del links[(start, end)]

	select_node(None)
	select_link(None)



def move_node(node, x, y):
	nodes[node]['x'] = x
	nodes[node]['y'] = y
	canvas.coords(node, x, y, x+NODE_SIZE_X, y+NODE_SIZE_X) 
	canvas.coords(nodes[node]['id_text'], x+NODE_SIZE_X/2, y+NODE_SIZE_X/2)

	for start, end in links:
		id_arrow = links[(start, end)]['id_arrow']
		x1 = x + NODE_SIZE_X/2
		y1 = y + NODE_SIZE_Y/2  

		if start == node:
			x2 = nodes[end]['x'] + NODE_SIZE_X/2
			y2 = nodes[end]['y'] + NODE_SIZE_Y/2
			canvas.coords(id_arrow, x1, y1, x2, y2)

		elif end == node:
			x2 = nodes[start]['x'] + NODE_SIZE_X/2
			y2 = nodes[start]['y'] + NODE_SIZE_Y/2
			canvas.coords(id_arrow, x2, y2, x1, y1)         

		select_link(None)


def add_link(start, end):
	global selected_node

	link_weight = 1.0

	if (start, end) not in links:

		if nodes[start]['type'] in ['source', 'tank']:
			print(start, end)
			print(links)
			suc_start = [j for (i, j) in links if i == start]
			if suc_start != []:
				end_source = suc_start[0]
				delete_link(links[(start, end_source)]['id_arrow'])

		if nodes[start]['type'] == 'split':
			link_weight = 0.0
			entry_weight.config(state='normal')

		else:
			entry_weight.config(state='disabled')

		x1 = nodes[start]['x'] + NODE_SIZE_X/2
		y1 = nodes[start]['y'] + NODE_SIZE_Y/2
		x2 = nodes[end]['x'] + NODE_SIZE_X/2
		y2 = nodes[end]['y'] + NODE_SIZE_Y/2

		link = canvas.create_line(x1, y1, x2, y2, arrow='last', tags="arrow")

		var_weight.set(link_weight)

		set_fast_link_values()
		links[(start, end)] = {'id_arrow':link,
							   'weight':link_weight,
							   'is_fast':True,
							   'length':1.0,
							   'diameter':1.0,
							   'mass_density':1000.0,
							   'flow_rate':1000.0}

		label_weight.grid(row=0, column=0, sticky='nw')
		entry_weight.grid(row=0, column=1, sticky='nw')

		check_is_fast.grid(row=1, column=0, sticky='nw')

		select_link(link)
		select_node(None)

		#history.append(('link', start, end))


def display_label(node):
	id_text = nodes[node]['id_text']
	label = nodes[node]['label']
	canvas.itemconfigure(id_text, text=label)


def set_label(*args):
	global selected_node

	try:
		if var_action.get() != 'delete':
			new_label = entry_label.get()
			if new_label in [nodes[node]['label'] for node in nodes]:
				return

			print('SET LABEL')
			if selected_node is not None:
				node_id = selected_node
			elif new_node is not None:
				node_id = new_node

			nodes[node_id]['label'] = new_label

			if new_label.isdigit():
				nodes[node_id]['num'] = int(new_label)

			# mise à jour 'entry'
			var_label.set(new_label)

			# affichage label dans le canevas
			id_text = nodes[node_id]['id_text']
			canvas.itemconfigure(id_text, text=str(new_label))
			
			select_node(None)   # cancel selected node
			hide_node_informations()

	except ValueError:
		pass

def set_uev(*args):
	
	try:
		print(entry_uev.get())
		label = str(selected_node)
		nodes[selected_node]['uev'] = var_uev.get()
	except ValueError:
		pass


def set_weight(*args):
	
	try:
		print(entry_weight.get())
		start, end = get_start_end(selected_link)
		
		weight = var_weight.get()

		# link_weights = sum([float(links[(i, j)]['weight']) for (i,j) in links if i == start])
		# print('link weight', link_weights)
		# print('var weight', float(var_weight.get()))
		
		# if link_weights + float(weight) > 1:
		# 	msg = 'Links originating from node ' + str(nodes[start]['label']) +\
		# 		  ':\nsum of weights cannot be greater than 1'

		# 	messagebox.showerror(title=None, message=msg)
			
		# 	return

		links[(start, end)]['weight'] = weight

	except ValueError:
		pass


def set_length(*args):
	
	try:
		print(entry_length.get())
		start, end = get_start_end(selected_link)
		links[(start, end)]['length'] = var_length.get()
	except ValueError:
		pass


def set_diameter(*args):
	
	try:
		print(entry_dialmeter.get())
		start, end = get_start_end(selected_link)
		links[(start, end)]['diameter'] = var_diameter.get()
	except ValueError:
		pass


def set_flow_rate(*args):
	
	try:
		print(entry_flow_rate.get())
		start, end = get_start_end(selected_link)
		links[(start, end)]['flow_rate'] = var_flow_rate.get()
	except ValueError:
		pass


def set_mass_density(*args):
	
	try:
		print(entry_mass_density.get())
		start, end = get_start_end(selected_link)
		links[(start, end)]['mass_density'] = var_mass_density.get()
	except ValueError:
		pass



def check_split_weights(node):
	link_weights = sum([float(links[(i, j)]['weight']) for (i,j) in links if i == node])

	if link_weights > 1:
		print('check_split', nodes[node]['label'],'->', link_weights)
		return False
	else:
		return True


def check_validity():
	print("Check Validity")

	err_nodes = []
	err_splits = []

	if links == {}:
		for node in nodes:
			label = nodes[node]['label']
			err_nodes.append(label)

	else:
		for node in nodes:
			connected = False
			for (start, end) in links:
				if node == start or node == end:
					connected = True

			if not connected:
				label = nodes[node]['label']
				err_nodes.append(label)

			if nodes[node]['type'] == 'split':
				print('check', nodes[node]['label'])
				if not check_split_weights(node):
					label = nodes[node]['label']
					err_splits.append(label)				

	return err_nodes, err_splits


#def find_node_label(x, y):
#	for node in nodes:
#		x_node = nodes[node]['x']
#		y_node = nodes[node]['y']
#		if (x_node <= x and x <= x_node + NODE_SIZE_X) and (y_node <= y and y <= y_node + NODE_SIZE_Y):
#			return node
#	return None


def get_node_id_of_label(label):
	for node in nodes:
		if nodes[node]['label'] == label:
			return node

	return None


def reset_selection():
	select_node(None)
	select_link(None)
	hide_node_informations()
	hide_link_informations()


def donothing():
	pass


def is_fast_change():
	global selected_link

	start, end = get_start_end(selected_link)

	if not var_is_fast.get():
		links[(start, end)]['is_fast'] = False

		label_length.grid(row=0, column=0, sticky='nw')
		entry_length.grid(row=0, column=1, sticky='nw')

		label_diameter.grid(row=1, column=0, sticky='nw')
		entry_diameter.grid(row=1, column=1, sticky='nw')

		label_mass_density.grid(row=2, column=0, sticky='nw')
		entry_mass_density.grid(row=2, column=1, sticky='nw')

		label_flow_rate.grid(row=0, column=2, sticky='nw')
		entry_flow_rate.grid(row=0, column=3, sticky='nw')

	else:
		links[(start, end)]['is_fast'] = True
		init_link(selected_link)

		label_length.grid_remove()
		entry_length.grid_remove()

		label_diameter.grid_remove()
		entry_diameter.grid_remove()

		label_mass_density.grid_remove()
		entry_mass_density.grid_remove()

		label_flow_rate.grid_remove()
		entry_flow_rate.grid_remove()


def click_on_link(event):
	global selected_link

	select_node(None)
	hide_node_informations()
	
	link = event.widget.find_withtag("current")[0]
	
	if link == selected_link:
		select_link(None)   # cancel selected link
		hide_link_informations()

	elif var_action.get() == 'delete':
		delete_link(link)

	elif var_action.get() == 'link':

		select_link(link)
		set_link_informations(link)
		display_link_informations(link)


def select_link(link):
	global selected_link

	if selected_link is not None:
		canvas.itemconfigure(selected_link, fill='black', width=1)

	selected_link = link

	if selected_link is not None:
		canvas.itemconfigure(selected_link, fill='red', width=2)



def object_at(x, y):
	if nodes:
		for node in nodes:
			x1 = nodes[node]['x']
			y1 = nodes[node]['y']
			if ((x1 <= x <= x1 + NODE_SIZE_X and y1 <= y <= y1 + NODE_SIZE_Y) 
				or
				(x1 <= x + NODE_SIZE_X <= x1 + NODE_SIZE_X and y1 <= y <= y1 + NODE_SIZE_Y)
				or
				(x1 <= x <= x1 + NODE_SIZE_X and y1 <= y + NODE_SIZE_Y <= y1 + NODE_SIZE_Y) 
				or
				(x1 <= x + NODE_SIZE_X <= x1 + NODE_SIZE_X and y1 <= y + NODE_SIZE_Y <= y1 + NODE_SIZE_Y)):
				return True
		return False

	return False


def click_on_canvas(event):
	global selected_node

	x = event.x
	y = event.y

	if object_at(x, y): # on a cliqué sur un objet
		return

	print('\nCLIC CANVAS', x, y, ' -- COMPONENT =', var_action.get())
	
	if var_action.get() != 'link':
		hide_link_informations()

	if selected_node is None:
		print('clic dans le vide',x, y)

		if var_action.get() in ['source', 'split', 'coproduct', 'tank', 
								 'product']:
			add_node(x, y)
			
			label_label.grid(row=0, column=0, sticky='w')

			label_type_text.grid(row=1, column=0, sticky='w')
			var_type.set(var_action.get())
			label_type_value.grid(row=1, column=1, sticky='w')
			
			entry_uev.config(state='normal')
			label_uev.grid(row=2, column=0, sticky='w')
			#var_uev.set(nodes[node]['uev'])
			entry_uev.grid(row=2, column=1)


			#display_node_informations()

			selected_node = None
	else:
		print('SELECTED NODE', selected_node)
		display_node_informations(selected_node)
		if var_action.get() == 'move':
			move_node(selected_node, x, y)


def mouse_over_node(event):
	if var_action.get() == 'delete':
		label_type_text.grid(row=1, column=0, sticky='w')

		node = get_node(event.widget.find_withtag("current")[0])

		display_node_informations(node)


def click_on_node(event):
	global selected_node
	
	select_link(None)
	hide_link_informations()
	
	node = get_node(event.widget.find_withtag("current")[0])
	var_label.set(nodes[node]['label'])
	var_type.set(nodes[node]['type'])

	print('\nclick_on_node ->', node)
	
	if node == selected_node:
		select_node(None)   # cancel selected node
		hide_node_informations()

	elif var_action.get() == 'delete':
		delete_node(node)

	elif var_action.get() == 'link':
		display_node_informations(node)
		if selected_node is not None and nodes[selected_node]['type'] != 'product' and  nodes[node]['type'] != 'source':
			
			print("Type start", nodes[node]['type'])
			print("Type end", nodes[selected_node]['type'])
			add_link(selected_node, node)
			select_link(selected_link)
		else:
			select_node(node)

	else:
		select_node(node)
		display_node_informations(node)


def set_fast_link_values():
	var_is_fast.set(True)
	var_length.set(1.0)
	var_diameter.set(1.0)
	var_mass_density.set(1000.0)
	var_flow_rate.set(1000.0)   


def init_link(link):

	start, end = get_start_end(link)
	set_fast_link_values()

	links[(start, end)] = {'id_arrow':link, 
						   'weight':var_weight.get(),
						   'is_fast':var_is_fast.get(),
						   'length':var_length.get(),
						   'diameter':var_diameter.get(),
						   'mass_density':var_mass_density.get(),
						   'flow_rate':var_flow_rate.get()}

def new_network():
	canvas.delete('all')  # also reset all widget ID's
	nodes.clear()
	links.clear()

	selected_node = None
	selected_link = None
	new_node = None


def open_file():

	root.filename =  filedialog.askopenfilename(title = "Select file",filetypes = (("network files","*.net"),("all files","*.*")))
	print(root.filename)

	with open(root.filename,'r') as input_file:
		
		new_network()

		for line in input_file:
			elements = line.split()
			type_ = elements[0]
			
			if type_ == 'FIG_NODE':

				label, x, y, node_type, num = elements[1:6]

				x, y, num = int(x), int(y), int(num)
				
				id_node = canvas.create_rectangle(x, y, x+NODE_SIZE_X, y+NODE_SIZE_X, fill='light grey', tags='node')
				id_text = canvas.create_text(x+NODE_SIZE_X/2, y+NODE_SIZE_X/2, text=label, tags='node')
				
				nodes[id_node] = {'label':label, 'x':x, 'y':y, 'type':node_type,
								  'num':num, 'id_text':id_text}


				if node_type == 'source':
					nodes[id_node]['uev'] = float(elements[6])


			elif type_ == 'FIG_LINK':
				
				x1, y1, x2, y2 = elements[1:5]
				start, end, is_fast, weight, length = elements[5:10]
				diameter, mass_density, flow_rate = elements[10:]

				x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

				start_label = get_node_id_of_label(start)
				end_label = get_node_id_of_label(end)

				start, end = int(start), int(end)
				is_fast, weight = bool(is_fast), float(weight)
				length, diameter = float(length), float(diameter)
				mass_density, flow_rate = float(mass_density), float(flow_rate)

				x1 += NODE_SIZE_X/2
				y1 += NODE_SIZE_Y/2
				x2 += NODE_SIZE_X/2
				y2 += NODE_SIZE_Y/2

				link = canvas.create_line(x1, y1, x2, y2, arrow='last', tags="arrow")

				links[(start_label, end_label)] = {'id_arrow':link, 'weight':weight,
									   'is_fast':is_fast, 'length':length,
							   		   'diameter':diameter, 
							   		   'mass_density':mass_density,
									   'flow_rate':flow_rate}

				print(nodes)


	print(nodes)
	print(links)


def save_as_file():

	err_nodes, err_splits = check_validity()

	msg = ''

	if err_nodes != []:
		if len(err_nodes) > 1:
			msg = 'Nodes not connected: '
		else:
			msg = 'Node not connected: '

		msg += ", ".join(err_nodes)

	msg2 =''

	if err_splits != []:
		if len(err_splits) > 1:
			msg2 = 'Splits with sum of weights > 1: '
		else:
			msg2 = 'Split with sum of weights > 1: '

		msg2 += ", ".join(err_splits)

	if msg != '':
		if msg2 != '':
			msg += '\n' + msg2

		messagebox.showerror(title=None, message=msg)
		return

	root.filename = filedialog.asksaveasfilename(title = "Select file",
					filetypes = (("network files","*.net"),("all files","*.*")))


	# for communication with Exel: name of network n a file
	base, network_name = os.path.split(root.filename)
	with open('network_name.dat','w') as output_file:
		output_file.write(network_name)

	# take name without extension for Excel files
	excel_name1 = network_name.split('.')[0] + '1.sim'
	excel_name2 = network_name.split('.')[0] + '2.sim'

	with open(root.filename,'w') as output_file:

		# nodes
		for i in nodes:
			label = nodes[i]['label']
			type_ = nodes[i]['type']
			x = str(nodes[i]['x'])
			y = str(nodes[i]['y'])
			num = str(nodes[i]['num'])
			#id_text = str(nodes[i]['id_text'])
			#id_node = str(i)
			uev = ''

			if type_ == 'source':
				uev = str(nodes[i]['uev'])
				output_file.write('SOURCE ' + ' ' + label + ' ' + uev + '\n')


			elif type_ == 'split':
				output_file.write('SPLIT ' + ' ' + label + '\n')

			elif type_ == 'coproduct':
				output_file.write('COPRODUCT ' + ' ' + label + '\n')

			elif type_ == 'tank':
				output_file.write('TANK ' + ' ' + label + '\n')

			elif type_ == 'product':
				output_file.write('PRODUCT ' + ' ' + label + '\n')

			data = label + ' ' + x + ' ' + y + ' ' + type_
			data +=	' ' + num + ' ' + uev

			output_file.write('FIG_NODE ' + data + '\n')

		# links
		for i, j in links:
			i_label = nodes[i]['label']
			j_label = nodes[j]['label']

			#id_arrow = links[(i,j)]['id_arrow']
			weight = links[(i,j)]['weight']
			is_fast = links[(i,j)]['is_fast']
			length = links[(i,j)]['length']
			diameter = links[(i,j)]['diameter']
			mass_density = links[(i,j)]['mass_density']
			flow_rate = links[(i,j)]['flow_rate']

			data = i_label + ' ' + j_label

			if mass_density != 1000.0:
				data += ' ' + str(weight) + ' ' + str(is_fast) + ' ' + str(mass_density)
			elif is_fast != True:
				data += ' ' + str(weight) + ' ' + str(is_fast)
			elif weight != 1.0:
				data += ' ' + str(weight)
			
			output_file.write('LINK ' + data + '\n')

			x1 = nodes[i]['x']
			y1 = nodes[i]['y']
			x2 = nodes[j]['x']
			y2 = nodes[j]['y']

			data_fig = str(x1) + ' ' + str(y1) + ' ' +  str(x2) + ' ' + str(y2)
			data_fig += ' ' + data
			data_fig += ' ' + str(is_fast) + ' ' + str(weight) + ' ' + str(length)
			data_fig += ' ' +str(diameter) + ' ' + str(mass_density) + ' ' + str(flow_rate)

			output_file.write('FIG_LINK ' + data_fig + '\n')

	# for communication between Excel and python
	network = emsys.System()
	network.load(network_name)
	g = network.graph

	with open(excel_name1, 'w') as output_file:

		# For Excel, values separated by tabs
		print("écriture de la première ligne dans", excel_name1)
		output_file.write('TYPE' + '\t' + 'LABEL' + '\t' + 'UEV' + '\n')

		for i in network.sources:
			uev = str(g.uev[i])
			output_file.write('SOURCE' + '\t' + g.label[i] + '\t' + uev + '\n')

		for i in network.tanks:
			output_file.write('TANK' + '\t' + g.label[i] + '\n')


	with open(excel_name2, 'w') as output_file:
		output_file.write('Time')

		for i in network.sources:
			output_file.write('\t' + g.label[i])

		for i in network.tanks:
			output_file.write('\t' + g.label[i])

		for i, j in network.arcs:
			output_file.write('\t' + g.label[i] + ':' + g.label[j])


# TKINTER
root = Tk()
root.title("emergylib network builder")
root.option_add('*tearOff', FALSE)

mainframe = ttk.Frame(root, padding="3 3 3 3")
mainframe.grid(column=0, row=0, sticky="nwse")

# To avoid moving of frames inside the mainframe
mainframe.rowconfigure(0, minsize=100)
mainframe.columnconfigure(0, minsize=100)
mainframe.columnconfigure(3, minsize=200)   
mainframe.grid_columnconfigure(0, weight=0)
#mainframe.grid_columnconfigure(1, weight=0)
mainframe.grid_columnconfigure(3, weight=1)

# Definition of frames
frame1 = ttk.Frame(mainframe)#, borderwidth=2)#, relief="ridge") #width=100)#, height=100)
frame1.grid(row=0, column=0, sticky='nw')

frame2 = ttk.Frame(mainframe)#, borderwidth=2)#, relief="ridge")#, width=800, height=100)
frame2.grid(row=0, column=1, sticky='nw')

frame3 = ttk.Frame(mainframe)#, borderwidth=2, relief="ridge")#, width=800, height=100)
frame3.grid(row=0, column=2, sticky='nw')

frame4 = ttk.Frame(mainframe)#, borderwidth=2, relief="ridge")#, width=800, height=100)
frame4.grid(row=0, column=3, sticky='nw')

canvas = Canvas(mainframe, width=1200, height=600, background='white', borderwidth=2, relief='sunken')
canvas.grid(row=1, column=0, columnspan=6, sticky='we')

# ACTIONS
label_add = Label(frame1, text='ADD', font=font.Font(size=14, weight='bold'))
label_add.grid(row=0, column=0, sticky='w')

label_delete = Label(frame1, text='DELETE', font=font.Font(size=14, weight='bold'))
label_delete.grid(row=1, column=0, sticky='w')

label_move = Label(frame1, text='MOVE', font=font.Font(size=14, weight='bold'))
label_move.grid(row=2, column=0, sticky='w')

action_labels = ['source', 'split', 'coproduct', 'tank', 'product', 'link', 'delete', 'move']
var_action = StringVar()
var_action.set(action_labels[0])

# ADD
for i in range(6):
	b1 = ttk.Radiobutton(frame1, variable=var_action, text=action_labels[i], value=action_labels[i],
						 command=reset_selection)
	b1.grid(row=0, column=i+1, padx=5, sticky='w')

# DELETE and MOVE
for i in range(2):
	b1 = ttk.Radiobutton(frame1, variable=var_action, value=action_labels[6+i],
						 command=reset_selection)
	b1.grid(row=1+i, column=1, padx=5, sticky='w')


label_type_text = Label(frame2, text='Type:  ')#, font=font.Font(size=14, weight='bold'))
var_type = StringVar(value='')
label_type_value = Label(frame2, textvariable=var_type)


label_label = Label(frame2, text = "Label")
var_label = StringVar()
entry_label = Entry(frame2, width=7, textvariable=var_label)


var_uev = DoubleVar(value=0.0)
entry_uev = Entry(frame2, width=7, textvariable=var_uev)
label_uev = Label(frame2, text = "UEV")


label_weight = Label(frame3, text = "Weight")
var_weight = StringVar()
entry_weight = Entry(frame3, width=7, textvariable=var_weight)

var_is_fast = BooleanVar()
check_is_fast = ttk.Checkbutton(frame3, text='Fast link', 
		command=is_fast_change, variable=var_is_fast,
		onvalue=True, offvalue=False)

var_length = StringVar()
entry_length = Entry(frame4, width=7, textvariable=var_length)
label_length = Label(frame4, text = "Length")

var_diameter = StringVar()
label_diameter = Label(frame4, text = "Diameter")
entry_diameter = Entry(frame4, width=7, textvariable=var_diameter)

var_mass_density = StringVar()
label_mass_density = Label(frame4, text = "Mass density")
entry_mass_density = Entry(frame4, width=7, textvariable=var_mass_density)

var_flow_rate = DoubleVar()
label_flow_rate = Label(frame4, text = "Flow rate")
entry_flow_rate = Entry(frame4, width=7, textvariable=var_flow_rate)


for child in mainframe.winfo_children(): 
	child.grid_configure(padx=5, pady=5)

# MENU
menubar = Menu(root)
root['menu'] = menubar

menu_file = Menu(menubar)
menubar.add_cascade(menu=menu_file, label='File', command='donothing')

menu_file.add_command(label="New", command=new_network)
menu_file.add_command(label="Open", command=open_file)
menu_file.add_command(label="Save", command=save_as_file)
menu_file.add_command(label="Save as...", command=save_as_file)


# BINDS
canvas.bind('<Button-1>', click_on_canvas)
entry_label.bind('<Return>', set_label)
entry_uev.bind('<Return>', set_uev)

entry_weight.bind('<Return>', set_weight)
entry_length.bind('<Return>', set_length)
entry_diameter.bind('<Return>', set_diameter)
entry_flow_rate.bind('<Return>', set_flow_rate)
entry_mass_density.bind('<Return>', set_mass_density)

canvas.tag_bind("arrow", "<Button-1>", click_on_link)
canvas.tag_bind("node", "<Button-1>", click_on_node)
canvas.tag_bind("node", "<Motion>", mouse_over_node)

def main():
	root.mainloop()

if __name__ == '__main__':
	main()


