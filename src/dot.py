# BPMN


ACTIVE_BORDER_COLOR = "red"
ACTIVE_BORDER_WIDTH = 4
ACTIVE_STYLE = "solid"


def node_to_dot(_id, shape, label, style, fillcolor, border_color=None, border_size=None):
	other_code = ""
	if border_color is not None:
		other_code += f'color={border_color} '
	if border_size is not None:
		other_code += f'penwidth={border_size} '
	return f'\nnode_{_id}[shape={shape} label="{label or ""}" style="{style or ""}" fillcolor={fillcolor} {other_code or ""}];'


def gateway_to_dot(_id, label, style, fillcolor, border_color=None, border_size=None):
	return node_to_dot(_id, "diamond", label, style, fillcolor, border_color, border_size)


def exclusive_gateway_to_dot(_id, label, style, border_color=None, border_size=None):
	if style is None:
		style = "filled"
	else:
		style = f"filled,{style}"
	return gateway_to_dot(_id, label, style, "orange", border_color, border_size)


def parallel_gateway_to_dot(_id, style, border_color=None, border_size=None):
	return gateway_to_dot(_id, f"+", style, "green", border_color, border_size)


def probabilistic_gateway_to_dot(_id, name, style, border_color=None, border_size=None):
	if style is None:
		style = "filled"
	else:
		style = f"filled,{style}"
	return gateway_to_dot(_id, f"{name}", style, "yellowgreen", border_color, border_size)


def loop_gateway_to_dot(_id, label, style, border_color=None, border_size=None):
	if style is None:
		style = "filled"
	else:
		style = f"filled,{style}"
	return gateway_to_dot(_id, label, style, "yellowgreen", border_color, border_size)


def task_to_dot(_id, name, style, impacts, duration, impacts_names, border_color=None, border_size=None):
	additional_label = ""
	if impacts:
		tmp = ", ".join(f"\\n{key}: {value}" for key, value in zip(impacts_names, impacts))
		additional_label += f"\\n impacts: {tmp}"
	if duration:
		additional_label += f"\\n duration: {duration}"

	if style is None:
		style = "rounded,filled"
	else:
		style = f"rounded,filled,{style}"

	return node_to_dot(
		_id,
		"rectangle",
		f"{name}{additional_label}",
		style,
		"lightblue",
		border_color,
		border_size
	)


def arc_to_dot(from_id, to_id, label=None):
	if label is None:
		return f'\nnode_{from_id} -> node_{to_id};\n'
	else:
		return f'\nnode_{from_id} -> node_{to_id}[label="{label}"];\n'


def wrap_to_dot(region_root, impacts_names, active_regions=None):
	code = "digraph G {\n"
	code += "rankdir=LR;\n"
	code += 'start[label="" style="filled" shape=circle fillcolor=palegreen1]\n'
	code += 'end[label="" style="filled" shape=doublecircle fillcolor=orangered] \n'
	other_code, entry_id, exit_id = region_to_dot(region_root, impacts_names, active_regions)
	code += other_code
	code += f'start -> node_{entry_id};\n'
	code += f'node_{exit_id} -> end;\n'
	code += "\n}"

	return code


def serial_generator():
	"""Generator to create unique IDs."""
	id_counter = 0
	while True:
		yield id_counter
		id_counter += 1


id_generator = serial_generator()


def region_to_dot(region_root, impacts_names, active_regions):
	is_active = region_root.get('id') in active_regions
	if region_root.get("type") == 'task':
		_id = next(id_generator)
		return task_to_dot(
			_id,
			region_root.get('label'),
			ACTIVE_STYLE if is_active else None,
			region_root.get('impacts', []),
			region_root.get('duration'),
			impacts_names,
			border_color=ACTIVE_BORDER_COLOR if is_active else None,
			border_size=ACTIVE_BORDER_WIDTH if is_active else None
		), _id, _id
	elif region_root.get("type") == 'loop':
		entry_id = next(id_generator)
		ext_id = next(id_generator)

		# Entry point
		code = loop_gateway_to_dot(
			entry_id,
			region_root.get('label'),
			style=None,
			border_color=ACTIVE_BORDER_COLOR if is_active else None,
			border_size=ACTIVE_BORDER_WIDTH if is_active else None
		)

		# Exit point
		code += loop_gateway_to_dot(
			ext_id,
			region_root.get('label'),
			region_root.get('style')
		)

		# Child
		other_code, child_entry_id, child_exit_id = region_to_dot(region_root.get('children')[0], impacts_names,
																  active_regions)
		code += other_code
		p = region_root.get('distribution')
		code += arc_to_dot(entry_id, child_entry_id, p)
		code += arc_to_dot(child_exit_id, ext_id, 1 - p)

		return code, entry_id, ext_id
	elif region_root.get("type") == 'choice':
		entry_id = next(id_generator)
		last_exit_id = next(id_generator)

		# Entry point
		code = exclusive_gateway_to_dot(
			entry_id,
			region_root.get('label'),
			ACTIVE_STYLE if is_active else None,
			border_color=ACTIVE_BORDER_COLOR if is_active else None,
			border_size=ACTIVE_BORDER_WIDTH if is_active else None
		)

		# Exit point
		code += exclusive_gateway_to_dot(
			last_exit_id,
			region_root.get('label'),
			style=None
		)

		# Children
		for child in region_root.get('children', []):
			child_code, child_entry_id, child_exit_id = region_to_dot(child, impacts_names, active_regions)
			code += child_code
			code += arc_to_dot(entry_id, child_entry_id)
			code += arc_to_dot(child_exit_id, last_exit_id)

		return code, entry_id, last_exit_id
	elif region_root.get("type") == 'parallel':
		entry_id = next(id_generator)
		last_exit_id = next(id_generator)

		# Entry point
		code = parallel_gateway_to_dot(
			entry_id,
			style=ACTIVE_STYLE if is_active else None,
			border_color=ACTIVE_BORDER_COLOR if is_active else None,
			border_size=ACTIVE_BORDER_WIDTH if is_active else None
		)

		# Exit point
		code += parallel_gateway_to_dot(
			last_exit_id,
			style=None
		)

		# Children
		for child in region_root.get('children', []):
			child_code, child_entry_id, child_exit_id = region_to_dot(child, impacts_names, active_regions)
			code += child_code
			code += arc_to_dot(entry_id, child_entry_id)
			code += arc_to_dot(child_exit_id, last_exit_id)

		return code, entry_id, last_exit_id
	elif region_root.get("type") == 'nature':
		entry_id = next(id_generator)
		last_exit_id = next(id_generator)

		# Entry point
		code = probabilistic_gateway_to_dot(
			entry_id,
			region_root.get('label'),
			style=ACTIVE_STYLE if is_active else None,
			border_color=ACTIVE_BORDER_COLOR if is_active else None,
			border_size=ACTIVE_BORDER_WIDTH if is_active else None
		)

		# Exit point
		code += probabilistic_gateway_to_dot(
			last_exit_id,
			region_root.get('label'),
			style=None
		)

		# Children
		for child, p in zip(region_root.get('children', []), region_root.get("distribution", [])):
			child_code, child_entry_id, child_exit_id = region_to_dot(child, impacts_names, active_regions)
			code += child_code
			code += arc_to_dot(entry_id, child_entry_id, p)
			code += arc_to_dot(child_exit_id, last_exit_id)

		return code, entry_id, last_exit_id
	elif region_root.get("type") == 'sequential':
		code = ""
		entry_id = None
		last_exit_id = None

		for i, child in enumerate(region_root.get('children', [])):
			child_code, child_entry_id, child_exit_id = region_to_dot(child, impacts_names, active_regions)
			code += child_code

			arc = arc_to_dot(last_exit_id, child_entry_id) if last_exit_id is not None else ""
			if entry_id is None:
				entry_id = child_entry_id
				arc = ""

			last_exit_id = child_exit_id
			code += arc

		return code, entry_id, last_exit_id
	else:
		raise ValueError(f"Unknown type: {region_root['type']}")


def get_active_region_by_pn(petri_net, marking):
	active_regions = set()

	for place in petri_net.get("places", []):
		place_id = place["id"]
		entry_region_id = place.get("entry_region_id")
		place_state = marking.get(place_id, {"token": 0})
		if entry_region_id and place_state['token'] > 0:
			active_regions.add(entry_region_id)

	return active_regions


# Execurtion Tree
ACTIVE_NODE_COLOR = "ffa500"        # Orange
INACTIVE_NODE_COLOR = "808080"      # Grey
TEXT_COLOR = "000000"               # Black
ALPHA_ACTIVE_BACKGROUND = "ff"      # Full opacity for visible nodes
ALPHA_ACTIVE_TEXT = "ff"            # Full opacity for visible nodes
ALPHA_INACTIVE_BACKGROUND = "7f"    # Semi-transparent for inactive nodes
ALPHA_INACTIVE_TEXT = "7f"          # Semi-transparent for inactive nodes

def tree_node_to_dot(_id, p, impacts, execution_time, impacts_name=None, visible=True):
	if impacts_name is None or len(impacts_name) == 0:
		impacts_name = [i+1 for i in range(len(impacts))]

	bg_color = ACTIVE_NODE_COLOR if visible else INACTIVE_NODE_COLOR  # Use active color if visible, inactive if not
	alpha_bg = ALPHA_ACTIVE_BACKGROUND if visible else ALPHA_INACTIVE_BACKGROUND  # Full opacity if visible, semi-transparent if not
	alpha_text = ALPHA_ACTIVE_TEXT if visible else ALPHA_INACTIVE_TEXT  # Full opacity if visible, semi-transparent if not
	impacts_label = f"[{", ".join([f"{name}: {value}" for name, value in zip(impacts_name, impacts)])}]"
	return f'\nnode_{_id}[shape=oval label="ID: {_id}\\nProbability: {p}\\nImpacts:\\n{impacts_label}\\nExecution time: {execution_time}" style="filled" fillcolor="#{bg_color}{alpha_bg}" fontcolor="#{TEXT_COLOR}{alpha_text}"];'

def tree_to_dot(tree_root, impacts_names, path=None):
	"""
	Render the execution tree as a dot representation.
	:param tree_root: Root of the execution tree
	:param impacts_names: Impacts names to display
	:param path: Ids of the nodes in the path to highlight
	:return: Dot representation of the execution tree
	"""
	if path is None:
		path = []

	def apply(root):
		code = ""
		is_active = root.get('id') in path

		node_id = root.get('id')
		snapshot = root.get('snapshot', {})
		p = snapshot.get('p', 1.0)
		impacts = snapshot.get('impacts', [0 for _ in impacts_names])
		execution_time = snapshot.get('execution_time', 0)

		code += tree_node_to_dot(
			node_id,
			p,
			impacts,
			execution_time,
			impacts_name=impacts_names,
			visible=is_active
		)

		for child in root.get("children", []):
			child_code = apply(child)
			code += child_code
			code += f'\nnode_{root.get("id")} -> node_{child.get("id")};\n'

		return code

	return apply(tree_root)

def wrapper_execution_tree_to_dot(tree_root, impacts_names, path=None):
	"""
	Wrapper to create the dot representation of the execution tree.
	:param tree_root: Execution tree object
	:param impacts_names: Impacts names to display
	:param path: Ids of the nodes in the path to highlight
	:return: Dot representation of the execution tree
	"""
	code = "digraph G {\n"
	code += tree_to_dot(tree_root, impacts_names, path)
	code += "\n}"

	return code

def get_path_to_current_node(tree_root, current_node_id):
	"""
	Get the path to the current node in the execution tree.
	:param tree_root: Root of the execution tree
	:param current_node_id: ID of the current node
	:return: List of node IDs in the path to the current node
	"""
	if tree_root.get('id') == current_node_id:
		return [current_node_id]

	for child in tree_root.get("children", []):
		path = get_path_to_current_node(child, current_node_id)
		if path is not None:
			return [tree_root.get('id')] + path

	return None


# Petri Net Visualization

def get_place_style(place):
	"""
	Determine component style for a Place.
	"""
	label = "▷"  # Default 'play' icon
	shape = "circle"
	style = "filled"
	fillcolor = "white"
	fontsize = 20
	penwidth = 1.5
	fontcolor = "black"

	# Check if Start or End place
	if not place.in_arcs:
		label = "▷"
		fontsize = 24
	elif not place.out_arcs:
		label = "▶" # Filled stop/end
		fontsize = 24
	
	# Internal places (often just routing)
	# based on image, they are all circles with play icon
	
	return f'shape={shape} label="{label}" fontsize={fontsize} style="{style}" fillcolor="{fillcolor}" penwidth={penwidth} fontcolor="{fontcolor}" fixedsize=false width=0.6'


def get_transition_style(transition, petri_net=None):
	"""
	Determine component style for a Transition.
	"""
	label = transition.label or ""
	shape = "box"
	style = "rounded,filled"
	fillcolor = "white"
	color = "black"
	fontcolor = "black"
	penwidth = 1.5
	fontsize = 14
	
	# Extract type and properties
	# Note: transition is a WrapperPetriNet.Transition which has .properties['custom']
	region_type = transition.get_region_type()
	probability = transition.get_probability()
	
	# Count incoming/outgoing arcs from the net (since transition.in_arcs may not be updated)
	n_in = 0
	n_out = 0
	if petri_net is not None:
		for arc in petri_net.arcs:
			if arc.target.name == transition.name:
				n_in += 1
			if arc.source.name == transition.name:
				n_out += 1
	
	# Logic
	if region_type == "task":
		# Task: Rounded Box
		shape = "box"
		style = "rounded,filled"
		fillcolor = "white"
		color = "black"
		# Label is already the name
		
	else:
		# Routing / Gateway / Logic
		# These are generally Triangles
		shape = "triangle"
		
		# Default Style (e.g. for unknown types)
		style = "filled"
		fillcolor = "#2E8B57" # SeaGreen
		color = "#2E8B57"
		fontcolor = "white"
		label = "" 
		
		is_probabilistic = False
		# Check for near-1 probability to handle floating point issues
		if probability is not None and probability < 0.999:
			is_probabilistic = True
		
		# Determine if Split or Join based on arc counts
		is_join = n_in > 1
		is_split = n_out > 1
			
		if region_type == "parallel":
			# Parallel: Split = White/Black, Join = Black Filled
			if is_join:
				# Join: Black Filled
				fillcolor = "black"
				color = "black"
				fontcolor = "white"
			else:
				# Split: White with Black Border
				fillcolor = "white"
				color = "black"
				fontcolor = "black"
				
		elif region_type in ["choice", "nature"]:
			# Choice/Nature:
			# Split (probabilistic): White with colored border + probability label
			# Join (deterministic): Colored filled
			if is_probabilistic:
				# Probabilistic Split: White with colored border
				if region_type == "nature":
					fillcolor = "white"
					color = "#2E8B57" # SeaGreen
					fontcolor = "black"
				else:
					fillcolor = "white"
					color = "#ffa500" # Orange
					fontcolor = "black"
				label = f"{probability}"
				fontsize = 12
			else:
				# Deterministic Join: Colored filled
				if region_type == "nature":
					fillcolor = "#2E8B57" # SeaGreen
					color = "#2E8B57"
					fontcolor = "white"
				else:
					fillcolor = "#ffa500" # Orange
					color = "#ffa500"
					fontcolor = "white"
					
		elif region_type == "loop":
			# Loop: All are Green by default
			# (Probabilistic loop back/exit handled by is_probabilistic)
			if is_probabilistic:
				fillcolor = "white"
				color = "#2E8B57" # SeaGreen
				fontcolor = "black"
				label = f"{probability}"
				fontsize = 12
			else:
				fillcolor = "#2E8B57" # SeaGreen
				color = "#2E8B57"
				fontcolor = "white"
		else:
			# Unknown routing type: Green filled
			pass

	base = f'shape={shape} label="{label}" style="{style}" fillcolor="{fillcolor}" color="{color}" fontcolor="{fontcolor}" penwidth={penwidth} fontsize={fontsize}'
	
	if shape == "triangle":
		base += " orientation=-90"
		
	return base


def petri_net_to_dot(petri_net, marking=None, final_marking=None):
	"""
	Generate DOT code for the Petri net with custom visualization.
	Supports region boundaries via subgraph clusters.
	"""
	code = "digraph G {\n"
	code += "rankdir=LR;\n"
	code += "splines=ortho;\n"
	code += "nodesep=0.5;\n"
	code += "ranksep=0.8;\n"
	code += "compound=true;\n"  # Required for cluster edges
	code += 'node [fontname="Arial"];\n'
	code += 'edge [fontname="Arial"];\n'
	
	# Group elements by region_label
	regions = {}  # region_label -> {"places": [], "transitions": []}
	ungrouped_places = []
	ungrouped_transitions = []
	
	for place in petri_net.places:
		region_label = place.get_region_label() if hasattr(place, 'get_region_label') else None
		if region_label:
			if region_label not in regions:
				regions[region_label] = {"places": [], "transitions": []}
			regions[region_label]["places"].append(place)
		else:
			ungrouped_places.append(place)
			
	for t in petri_net.transitions:
		region_label = t.get_region_label() if hasattr(t, 'get_region_label') else None
		if region_label:
			if region_label not in regions:
				regions[region_label] = {"places": [], "transitions": []}
			regions[region_label]["transitions"].append(t)
		else:
			ungrouped_transitions.append(t)
	
	# Generate clusters for each region
	for region_label, elements in regions.items():
		cluster_name = region_label.replace(" ", "_").replace("-", "_")
		code += f'\nsubgraph cluster_{cluster_name} {{\n'
		code += f'label="{region_label}";\n'
		code += 'style="rounded";\n'
		code += 'color="black";\n'
		code += 'bgcolor="white";\n'
		code += 'penwidth=1.5;\n'
		
		for place in elements["places"]:
			style = get_place_style(place)
			code += f'"{place.name}" [{style}];\n'
			
		for t in elements["transitions"]:
			style = get_transition_style(t, petri_net)
			code += f'"{t.name}" [{style}];\n'
			
		code += '}\n'
	
	# Ungrouped elements (not in any region)
	for place in ungrouped_places:
		style = get_place_style(place)
		code += f'"{place.name}" [{style}];\n'
		
	for t in ungrouped_transitions:
		style = get_transition_style(t, petri_net)
		code += f'"{t.name}" [{style}];\n'
		
	# Arcs
	for arc in petri_net.arcs:
		color = "black"
		arrowhead = "normal"
		
		code += f'"{arc.source.name}" -> "{arc.target.name}" [color="{color}" arrowhead="{arrowhead}"];\n'
		
	code += "}"
	return code

