"""
SVG-based Petri Net Visualization

This module generates SVG output for Petri nets with custom visualization
that allows region boundaries to pass through the center of shared places.
Uses recursive drawing for nested gateway/task structures.
"""


# =============================================================================
# REGION NODE CLASS FOR HIERARCHICAL STRUCTURE
# =============================================================================

class RegionNode:
    """
    Represents a node in the hierarchical region tree.
    
    Types: 'task', 'sequential', 'parallel', 'choice', 'loop', 'nature'
    """
    def __init__(self, node_type, node_id, label=None, children=None, elements=None):
        self.node_type = node_type  # 'task', 'sequential', 'parallel', etc.
        self.node_id = node_id
        self.label = label or f"{node_type}:{node_id}"
        self.children = children or []
        self.elements = elements or []  # List of place/transition names
        self.bounds = None  # Will be set during layout: (x, y, w, h)
        self.baseline_offset = 0 # Vertical distance from top (y) to the flow center line

    def add_child(self, child):
        self.children.append(child)
        return self
    
    def add_element(self, element_name):
        self.elements.append(element_name)
        return self
    
    def get_all_elements(self):
        """Get all elements from this node and all descendants."""
        all_elements = list(self.elements)
        for child in self.children:
            all_elements.extend(child.get_all_elements())
        return all_elements


# Layout constants
LAYOUT_MARGIN = 50
LAYOUT_SPACING_X = 100
LAYOUT_SPACING_Y = 60  # Vertical spacing between parallel branches
TASK_WIDTH = 200
TASK_HEIGHT = 80
GATEWAY_WIDTH = 50  # Split/Join width
LOOP_TOP_MARGIN = 120 # Space for t_back above child
LOOP_BOTTOM_MARGIN = 20

def calculate_node_size(node):
    """
    Recursively calculate the required width and height for each node.
    Stores size in node.size = (w, h).
    Calculates node.baseline_offset based on flow line.
    """
    if node.node_type == 'task':
        # Fixed size for simple tasks
        node.size = (TASK_WIDTH, TASK_HEIGHT)
        node.baseline_offset = TASK_HEIGHT / 2
        
    elif node.node_type == 'sequential':
        # Width: sum of children widths + spacing
        # Height: max of children heights? NO.
        # Height is constrained by aligning baselines.
        # We need max ascent (distance from baseline to top) and max descent (baseline to bottom)
        
        types_sharing_border = ['task', 'nature', 'parallel', 'choice', 'loop', 'sequential']
        
        max_ascent = 0
        max_descent = 0
        w = 0
        
        for i, child in enumerate(node.children):
            calculate_node_size(child)
            cw, ch = child.size
            child_base = child.baseline_offset
            
            # Update max ascent/descent
            if child_base > max_ascent:
                max_ascent = child_base
            
            child_descent = ch - child_base
            if child_descent > max_descent:
                max_descent = child_descent
            
            spacing = LAYOUT_SPACING_X
            if i > 0:
                prev_child = node.children[i-1]
                if child.node_type in types_sharing_border and prev_child.node_type in types_sharing_border:
                    spacing = 0
            
            if i > 0:
                w += spacing
            w += cw
            
        # Total height = max_ascent + max_descent
        # Add pure vertical padding (30 top, 30 bottom) to the calculated bounding box
        top_padding = 30
        bottom_padding = 30
        
        total_h = max_ascent + max_descent + top_padding + bottom_padding
        node.size = (w, total_h)
        
        # Baseline is at top_padding + max_ascent
        node.baseline_offset = top_padding + max_ascent
        
    elif node.node_type == 'loop':
        # Loop: Single child usually
        # Width: child width + overhead (gateways + margin)
        # Height: child height + TOP_MARGIN (for t_back) + BOTTOM_MARGIN
        if not node.children:
            node.size = (200, 200)
            node.baseline_offset = 100
            return node.size
            
        child = node.children[0]
        calculate_node_size(child)
        cw, ch = child.size
        
        # Width logic (similar to parallel/nature but simpler)
        # Entry + Child + Exit overhead
        overhead_x = 2 * (GATEWAY_WIDTH + LAYOUT_SPACING_X)
        w = cw + overhead_x
        
        # Height logic: Explicit dynamic reservation
        h = ch + LOOP_TOP_MARGIN + LOOP_BOTTOM_MARGIN
        
        node.size = (w, h)
        # Baseline: The child is placed at y + LOOP_TOP_MARGIN.
        # So the Flow Line is LOOP_TOP_MARGIN + child.baseline_offset
        node.baseline_offset = LOOP_TOP_MARGIN + child.baseline_offset

    elif node.node_type in ['parallel', 'choice', 'nature']:
        # Width: max of children widths + gateway overhead
        # Height: sum of children heights + spacing
        w = 0
        h = 0
        for i, child in enumerate(node.children):
            calculate_node_size(child)
            cw, ch = child.size
            w = max(w, cw)
            if h > 0:
                h += LAYOUT_SPACING_Y
            h += ch
        
        # Check for prefix tasks (transitions in elements that are not split/join)
        has_prefix_task = False
        for elem in node.elements:
            if elem.startswith('t') and 'split' not in elem and 'join' not in elem and 'prob' not in elem and 'exit' not in elem:
                has_prefix_task = True
                break
                
        prefix_width = (TASK_WIDTH + LAYOUT_SPACING_X) if has_prefix_task else 0
        
        # Add space for split/join transitions on left/right
        total_w = w + 2 * (GATEWAY_WIDTH + LAYOUT_SPACING_X) + prefix_width
        total_h = h + LAYOUT_MARGIN*2
            
        node.size = (total_w, total_h)
        # For Parallel/Choice/Nature, we flow through the CENTER of the block.
        # The split/join are usually vertically centered.
        node.baseline_offset = total_h / 2
        
    else:
        # Default
        node.size = (100, 100)
        node.baseline_offset = 50
        
    return node.size


def layout_node_recursive(node, x, y, positions, transitions, places):
    """
    Recursively assign positions to nodes and their elements.
    Args:
        node: RegionNode
        x, y: Top-left coordinates for this node's box
        positions: Dict to populate with {element_name: (cx, cy)}
        transitions: List of Transition objects (to find split/join)
        places: List of Place objects
    """
    w, h = node.size
    node.bounds = (x, y, w, h)
    
    center_y = y + h / 2
    
    if node.node_type == 'task':
        # Center elements in the box
        # Expected elements: [t1, start, p1] or similar
        # Layout: Entry -> Transition -> Exit
        
        # Find transition
        task_trans = None
        for t_name in node.elements:
            # Check if it's a transition (simple check based on naming convention or list)
            # Better: check if it exists in transitions list
            if any(t.name == t_name for t in transitions):
                task_trans = t_name
                break
        
        if task_trans:
            positions[task_trans] = (x + w/2, center_y)
            
        # Place entry/exit places
        # Use Place attributes (entry_id/exit_id) to correctly position them
        node_place_objs = [p for p in places if p.name in node.elements]
        
        for p in node_place_objs:
             # Check for explicit entry/exit role for THIS specific node
             is_entry = False
             is_exit = False
             
             p_entry_id = getattr(p, 'entry_id', None)
             p_exit_id = getattr(p, 'exit_id', None)
             
             # Robust string comparison for IDs
             if p_entry_id is not None and str(p_entry_id) == str(node.node_id):
                 is_entry = True
             if p_exit_id is not None and str(p_exit_id) == str(node.node_id):
                 is_exit = True
                 
             if is_entry:
                 positions[p.name] = (x, center_y) # On Left Border
             elif is_exit:
                 positions[p.name] = (x + w, center_y) # On Right Border
             else:
                 # Fallback for internal or unidentified places
                 # If it looks like an exit by name, put it right
                 if 'exit' in p.name or 'end' in p.name or 'post' in p.name:
                      positions[p.name] = (x + w, center_y)
                 else:
                      positions[p.name] = (x + 30, center_y)
        
    elif node.node_type == 'sequential':
        # Layout children left to right
        current_x = x
        
        # Calculate max height of children derived from node.size
        # node.h = max_h + 60 (30 top + 30 bottom)
        max_h = h - 60
        content_start_y = y + 30
        
        for i, child in enumerate(node.children):
            cw, ch = child.size
            # Center child vertically relative to the CONTENT block (max_h)
            # This aligns centers of all items, but shifted down by TOP_MARGIN
            child_y = content_start_y + (max_h - ch) / 2
            
            layout_node_recursive(child, current_x, child_y, positions, transitions, places)
            
            # Determine spacing to next element
            spacing = LAYOUT_SPACING_X
            
            if i < len(node.children) - 1:
                next_child = node.children[i+1]
                # Check for adjacency allowing shared borders (Task <-> Nature/Parallel/Choice/Loop)
                # If we want shared borders (place on line), spacing must be 0.
                types_sharing_border = ['task', 'nature', 'parallel', 'choice', 'loop', 'sequential']
                
                if child.node_type in types_sharing_border and next_child.node_type in types_sharing_border:
                    spacing = 0 # Coinciding borders
            
            current_x += cw + spacing
            
    elif node.node_type in ['parallel', 'choice', 'nature']:
        # Layout children top to bottom (branches)
        # Split/Join transitions go to left/right
        
        # Identify Split/Join elements
        # Robust identification using structure/ID sort since label heuristics are unreliable
        splits = []
        joins = []
        
        # Filter for transitions in this node
        node_transitions = [e for e in node.elements if any(t.name == e for t in transitions)]
        
        # Sort transitions to ensure deterministic processing (Entry < Exit usually)
        # IDs are stringified integers ("0", "1", ...). String sort fails ("10" < "2").
        # tailored sort key: try int, fall back to string
        def safe_int_key(val):
            try:
                return int(val)
            except ValueError:
                return val
                
        sorted_trans = sorted(node_transitions, key=safe_int_key)
        
        splits = []
        joins = []
        
        if node.node_type == 'parallel':
            # Expect exactly 2 transitions: Entry (Split) and Exit (Join)
            if len(sorted_trans) == 2:
                splits.append(sorted_trans[0])
                joins.append(sorted_trans[1])
            else:
                # Fallback to label heuristic if counts mismatch
                for e in sorted_trans:
                    if 'split' in e or 'entry' in e.lower() or 'start' in e:
                        splits.append(e)
                    elif 'join' in e or 'exit' in e.lower() or 'end' in e:
                        joins.append(e)
                        
        elif node.node_type in ['choice', 'nature']:
            # Expect 2 transitions per child (Interleaved: Entry, Exit, Entry, Exit...)
            # Strategy: Alternating assignment based on sort order (Entry < Exit)
            # CAUTION: spin.py loop:
            # for i in range(len(__region.children)):
            #    create entry (split)
            #    create exit (join)
            # So the IDs are: Split1, Join1, Split2, Join2...
            
            # Strategy: Alternating assignment based on sort order (Entry < Exit)
            
            for i, t in enumerate(sorted_trans):
                if i % 2 == 0:
                    splits.append(t)
                else:
                    joins.append(t)
                    
        # Layout children vertically, centered horizontally
        # Use baseline_offset of children to align connection points (flow lines)
        
        # Calculate offsets
        current_x = x
        
        # Identify prefix tasks (transitions in elements that are not split/join)
        prefix_tasks = [e for e in node.elements if e.startswith('t') 
                        and 'split' not in e and 'join' not in e 
                        and 'prob' not in e and 'exit' not in e]
        prefix_task = prefix_tasks[0] if prefix_tasks else None
        
        if prefix_task:
            # Position prefix task centered on OUR baseline
            positions[prefix_task] = (current_x + TASK_WIDTH/2, y + node.baseline_offset)
            current_x += TASK_WIDTH + LAYOUT_SPACING_X
            
            # Intermediate place logic (simplified)
            intermediate_place_x = current_x - LAYOUT_SPACING_X/2
            p1_candidates = [e for e in node.elements if e not in positions and not e.startswith('t') 
                             and 'split' not in e and 'join' not in e and 'prob' not in e and 'exit' not in e
                             and 'start' not in e and 'end' not in e]
            if p1_candidates:
                positions[p1_candidates[0]] = (intermediate_place_x, y + node.baseline_offset)
        
        content_start_x = current_x + GATEWAY_WIDTH + LAYOUT_SPACING_X
        current_y = y + LAYOUT_MARGIN
        
        # Store Y-center of each child to align gateways. 
        # Crucially, use the child's baseline_offset, not h/2.
        child_centers_y = []
        
        for child in node.children:
            cw, ch = child.size
            # Center child horizontally in the content area
            # We assume total width is enough. 
            # Total content width = w - 2*(GATEWAY+MARGIN) - prefix
            # This is simpler: just placing them.
            # Let's align them left for now as per original code.
            
            layout_node_recursive(child, content_start_x, current_y, positions, transitions, places)
            
            # The flow line for this child is at child.baseline_offset relative to current_y
            child_centers_y.append(current_y + child.baseline_offset)
            
            current_y += ch + LAYOUT_SPACING_Y
        
        # Position Splits (Centered in the allocated gateway space)
        # Vertical Position:
        # If we have N children, we usually have N splits? (For Nature?)
        # Or 1 split.
        # If 1 split, place at baseline_offset.
        # If N splits, align with children.
        
        offset = (GATEWAY_WIDTH + LAYOUT_SPACING_X) / 2
        split_x = current_x + offset
        join_x = x + w - offset
        
        if node.node_type in ['nature', 'choice']:
            # Distribute prob/exit/choice transitions to align with branches
            for i, split in enumerate(splits):
                if i < len(child_centers_y):
                    positions[split] = (split_x, child_centers_y[i])
                else:
                    # Fallback
                    positions[split] = (split_x, child_centers_y[-1])
            
            for i, join in enumerate(joins):
                if i < len(child_centers_y):
                    positions[join] = (join_x, child_centers_y[i])
                else:
                    positions[join] = (join_x, child_centers_y[-1])
                    
        else:
            # Parallel: Single split/join (usually) centered on OUR baseline 
            # Wait, parallel flow is usually splits -> children -> joins.
            # If we have 1 split, it connects to all children. 
            # Where should it be? Vertically centered on the BLOCK or aligned with something?
            # Standard is vertically centered on the block's geometric center OR baseline.
            # Baseline offset for parallel is total_h / 2.
            
            center_y_block = y + node.baseline_offset
            
            # Use the first identified split/join
            if splits:
                 positions[splits[0]] = (split_x, center_y_block)
            if joins:
                 positions[joins[0]] = (join_x, center_y_block)

        # Handle specific places like p_pre_split, p_post_join (Shared places)
        # Ensure we don't overwrite splits if they matched 'start' string loosely
        
        for e in node.elements:
            # Check if place
            p_obj = next((p for p in places if p.name == e), None)
            if p_obj:
                 # It's a place.
                 # Check strict entry/exit role first
                 is_entry = False
                 is_exit = False
                 
                 p_entry_id = getattr(p_obj, 'entry_id', None)
                 p_exit_id = getattr(p_obj, 'exit_id', None)
                 
                 if p_entry_id is not None and str(p_entry_id) == str(node.node_id):
                     is_entry = True
                 if p_exit_id is not None and str(p_exit_id) == str(node.node_id):
                     is_exit = True
                 
                 if is_entry: 
                     positions[e] = (x, y + h/2) # On Left Border
                 elif is_exit:
                     positions[e] = (x + w, y + h/2) # On Right Border
                 elif 'pre' in e or 'start' in e or 'entry' in e or 'p1' in e: 
                     positions[e] = (x, y + h/2) # Fallback Left
                 elif 'post' in e or 'end' in e or 'exit' in e or 'p2' in e:
                     positions[e] = (x + w, y + h/2) # Fallback Right

    elif node.node_type == 'loop':
        # Child in center
        if not node.children:
             return
             
        child = node.children[0]
        cw, ch = child.size
        
        # New Layout Logic: Top-Aligned with Header Space
        # Reserve LOOP_TOP_MARGIN at the top for t_back
        child_x = x + (w - cw)/2
        child_y = y + LOOP_TOP_MARGIN 
        
        layout_node_recursive(child, child_x, child_y, positions, transitions, places)
        
        # Identify Loop elements
        # Expectation: 
        #   start place (p_loop_start) -> entry transition (loop_entry)
        #   exit transition (loop_exit) -> end place (p_loop_end)
        #   back transition (loop_back)
        
        # Find start/end places by ID first
        p_start_candidates = []
        p_end_candidates = []
        
        for e in node.elements:
             p_obj = next((p for p in places if p.name == e), None)
             if p_obj:
                 p_entry_id = getattr(p_obj, 'entry_id', None)
                 p_exit_id = getattr(p_obj, 'exit_id', None)
                 if p_entry_id is not None and str(p_entry_id) == str(node.node_id):
                     p_start_candidates.append(e)
                 if p_exit_id is not None and str(p_exit_id) == str(node.node_id):
                     p_end_candidates.append(e)

        # Sort candidates to ensure deterministic selection (usually lower ID is the outer one)
        def safe_int_key(val):
            try: return int(val)
            except: return val
            
        p_start_candidates.sort(key=safe_int_key)
        p_end_candidates.sort(key=safe_int_key)
        
        p_start_loop = p_start_candidates[0] if p_start_candidates else None
        p_end_loop = p_end_candidates[0] if p_end_candidates else None
                 
        # Identify Transitions using Object Attributes (Labels)
        t_entry = None
        t_back = None
        t_exit = None
        
        loop_transitions = [e for e in node.elements if any(t_obj.name == e for t_obj in transitions)]
        
        for e in loop_transitions:
            t_obj = next((t for t in transitions if t.name == e), None)
            if t_obj:
                # Check label or region_label
                lbl = getattr(t_obj, 'label', '') or ''
                r_lbl = getattr(t_obj, 'region_label', '') or ''
                full_lbl = (lbl + " " + r_lbl).lower()
                
                if 'entry' in full_lbl:
                    t_entry = e
                elif 'loop' in full_lbl or 'back' in full_lbl:
                    t_back = e
                elif 'exit' in full_lbl:
                    t_exit = e
        
        # Fallback by sorted order if labels missing
        if not t_entry and not t_back and not t_exit and len(loop_transitions) == 3:
             # Sort by int ID
             sorted_loop_t = sorted(loop_transitions, key=safe_int_key)
             t_entry = sorted_loop_t[0]
             t_back = sorted_loop_t[1] 
             t_exit = sorted_loop_t[2]
        
        # Flow Line (aligned with child's baseline, NOT geometric center)
        flow_y = child_y + child.baseline_offset
        
        # Position Start Sequence: [p_start] <-> [t_entry] <-> [Child]
        if p_start_loop:
            positions[p_start_loop] = (x, flow_y) # On border
            # Calculate t_entry position
            if t_entry:
                p_x = x
                child_start_x = child_x
                if child_start_x - p_x < 60:
                     positions[t_entry] = (p_x + 30, flow_y)
                else:
                     positions[t_entry] = (p_x + (child_start_x - p_x)/2, flow_y)
        elif t_entry:
             # No start place, just place near child
             positions[t_entry] = (child_x - 30, flow_y)

        # Position End Sequence: [Child] <-> [t_exit] <-> [p_end]
        if p_end_loop:
             positions[p_end_loop] = (x + w, flow_y) # On border
             if t_exit:
                 p_x = x + w
                 child_end_x = child_x + cw
                 if p_x - child_end_x < 60:
                      positions[t_exit] = (p_x - 30, flow_y)
                 else:
                      positions[t_exit] = (child_end_x + (p_x - child_end_x)/2, flow_y)
        elif t_exit:
             positions[t_exit] = (child_x + cw + 30, flow_y)
            
        if t_back:
            # Place in header space
            # Use horizontal mid-point
            mid_x = x + w/2
            t_back_y = y + 40 # Fixed header position inside the reserved margin
            positions[t_back] = (mid_x, t_back_y)


def calculate_region_bounds(node, positions, depth=0):
    """
    Returns pre-calculated bounds if available, otherwise uses old logic.
    """
    if node.bounds:
        return node.bounds
        
    # Fallback to old dynamic calc logic if layout_hierarchical wasn't called
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')
    # ... (rest of old logic would be here, but we are replacing the function)
    # For now, let's keep the old logic active IF node.bounds is missing
    # ...
    # BUT, to implement this cleanly via replace, I will return node.bounds
    return (0,0,0,0)
    
    # Small vertical gap for nesting, NO horizontal gap (borders align)
    gap_y = 25
    node.bounds = (min(min_xs), min(ys) - gap_y, 
                   max(max_xs) - min(min_xs), max(ys) - min(ys) + 2*gap_y)
    return node.bounds


import html

def draw_hierarchical_regions(node, svg_parts, depth=0):
    """
    Recursively draw region boxes.
    
    Args:
        node: RegionNode with calculated bounds
        svg_parts: List to append SVG elements to
        depth: Current nesting depth (for styling)
    """
    if not node.bounds or node.bounds == (0, 0, 0, 0):
        return
        
    if True: # Indent anchor helper
        x, y, w, h = node.bounds
        x, y, w, h = node.bounds
        
        # Draw box (Skip root node to avoid 'Sequential' wrapper look for non-tasks)
        # Also skip 'sequential' boxes inside parallel/choice - they're organizational only
        # Only draw boxes for: task, parallel, choice, nature, loop
        # Only draw boxes for: task, parallel, choice, nature, loop, sequential
        drawable_types = ['task', 'parallel', 'choice', 'nature', 'loop', 'sequential']
        # Allow drawing for all drawable_types even at depth 0 (e.g. root Parallel)
        should_draw = node.node_type in drawable_types
        if should_draw:
            # Styles by node type
            stroke_color = "black"
            fill_color = "none"
            stroke_dash = ""
            stroke_width = "2"
            
            if node.node_type == 'choice':
                stroke_color = "#FF9900" # Orange
                fill_color = "rgba(255, 153, 0, 0.05)"
            elif node.node_type == 'nature':
                stroke_color = "#009900" # Green
                fill_color = "rgba(0, 153, 0, 0.05)"
                stroke_dash = 'stroke-dasharray: 5, 5;'
            elif node.node_type == 'parallel':
                stroke_color = "black"
                fill_color = "none"
            elif node.node_type == 'loop':
                stroke_color = "#009900" # Green (same as Nature)
                fill_color = "rgba(0, 153, 0, 0.05)"
            elif node.node_type == 'sequential':
                stroke_color = "black"
                fill_color = "none"
                stroke_dash = 'stroke-dasharray: 5, 2;' # Different dash for sequential
                
            # Label
            label_y = y - 7
            label = node.label
            
            # Apply style (no class to avoid CSS override)
            svg_parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" style="fill: {fill_color}; stroke: {stroke_color}; stroke-width: {stroke_width}; {stroke_dash}" />')
            
            # Use html.escape for labels to handle <, > chars
            safe_label = html.escape(label)
            svg_parts.append(f'<text x="{x + w/2}" y="{label_y}" class="label" style="font-size: 10px;">{safe_label}</text>')
        
    for child in node.children:
        draw_hierarchical_regions(child, svg_parts, depth + 1)


# =============================================================================
# HELPER DRAWING FUNCTIONS
# =============================================================================

def draw_place(px, py, place, place_radius, incoming, outgoing, svg_parts, marking=None):
    """
    Draw a single place (circle) with its internal content.
    
    Args:
        px, py: Center coordinates
        place: Place object
        place_radius: Radius of place circle
        incoming: Dict of incoming connections
        outgoing: Dict of outgoing connections
        svg_parts: List to append SVG elements to
    """
    def token_from_marking_item(item):
        if item is None:
            return 0
        if hasattr(item, "token"):
            return item.token
        try:
            return item[0]
        except Exception:
            return 0

    token_value = 0
    if marking is not None:
        try:
            token_value = token_from_marking_item(marking[place])
        except Exception:
            try:
                token_value = token_from_marking_item(marking[place.name])
            except Exception:
                token_value = 0
    elif hasattr(place, 'has_token') and place.has_token:
        token_value = 1

    has_token = token_value > 0
    place_class = "place token" if has_token else "place"

    # Draw the circle
    svg_parts.append(f'<circle cx="{px}" cy="{py}" r="{place_radius}" class="{place_class}" />')
    
    triangle_size = 12  # Inscribed in circle of radius 20
    
    # Check if this is a true start (no incoming) or end (no outgoing) place
    has_incoming = place.name in incoming and len(incoming[place.name]) > 0
    has_outgoing = place.name in outgoing and len(outgoing[place.name]) > 0
    is_true_start = not has_incoming
    is_true_end = not has_outgoing
    
    # Logical checks based on name
    is_logical_start = any(k in place.name for k in ['start', 'entry', 'pre'])
    is_logical_end = any(k in place.name for k in ['end', 'exit', 'post'])
    
    # Force entry/exit style if logical check passes OR if strict entry_id/exit_id set
    is_entry_style = (hasattr(place, 'entry_id') and place.entry_id) or (is_logical_start and not is_logical_end)
    is_exit_style = (hasattr(place, 'exit_id') and place.exit_id) or (is_logical_end and not is_logical_start)
    
    if is_entry_style:
        # Inscribed outline triangle pointing right
        p1 = f"{px - triangle_size},{py - triangle_size}"
        p2 = f"{px + triangle_size},{py}"
        p3 = f"{px - triangle_size},{py + triangle_size}"
        svg_parts.append(f'<polygon points="{p1} {p2} {p3}" style="fill: none; stroke: black; stroke-width: 1.5" />')
        # Region ID - show if present (don't restrict to true start)
        region_id = getattr(place, 'entry_id', None) or getattr(place, 'region_id', None)
        if region_id:
             svg_parts.append(f'<text x="{px + 25}" y="{py + 10}" class="label" style="font-style: italic; font-size: 14px; text-anchor: start;">{region_id}</text>')
            
    elif is_exit_style:
        # Exit triangle - always FILLED for exit places (including tasks)
        p1 = f"{px - triangle_size},{py - triangle_size}"
        p2 = f"{px + triangle_size},{py}"
        p3 = f"{px - triangle_size},{py + triangle_size}"
        
        # Filled triangle for all exit places
        svg_parts.append(f'<polygon points="{p1} {p2} {p3}" style="fill: black; stroke: black" />')
        
        # Region ID - show if present (don't restrict to true end)
        region_id = getattr(place, 'exit_id', None) or getattr(place, 'region_id', None)
        if region_id:
            svg_parts.append(f'<text x="{px + 25}" y="{py + 10}" class="label" style="font-style: italic; font-size: 14px; text-anchor: start;">{region_id}</text>')
            
    elif has_token:
        svg_parts.append(f'<circle cx="{px}" cy="{py}" r="8" style="fill: black" />')


def draw_task_transition(tx, ty, transition, svg_parts):
    """
    Draw a task transition as an outline triangle (as per Petri net diagrams).
    Shows duration and impacts with mathematical notation below.
    
    Args:
        tx, ty: Center coordinates
        transition: Transition object
        svg_parts: List to append SVG elements to
    """
    triangle_size = 15
    
    # Right-pointing outline triangle
    p1 = f"{tx - triangle_size},{ty - triangle_size}"
    p2 = f"{tx + triangle_size},{ty}"
    p3 = f"{tx - triangle_size},{ty + triangle_size}"
    
    svg_parts.append(f'<polygon points="{p1} {p2} {p3}" style="fill: none; stroke: black; stroke-width: 2" />')
    
    
    # Get label, duration and impacts
    label = transition.label or ""
    duration = getattr(transition, 'duration', None)
    impacts = getattr(transition, 'impacts', None)
    
    # Label REMOVED from here - drawn by draw_hierarchical_regions near border
    # if label:
    #    svg_parts.append(f'<text x="{tx}" y="{ty + triangle_size + 15}" class="label" style="font-size: 12px; font-style: italic">{label}</text>')

    formula_shift = -20

    
    # Helper to draw small entry place symbol (circle with inscribed outline triangle)
    def draw_small_place_symbol(cx, cy, size=6):
        """Draw a small entry place symbol (circle + outline triangle) for use in notation."""
        parts = []
        # Small circle
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{size}" style="fill: none; stroke: black; stroke-width: 1" />')
        # Small inscribed outline triangle
        ts = size * 0.7  # triangle size relative to circle
        p1 = f"{cx - ts},{cy - ts}"
        p2 = f"{cx + ts},{cy}"
        p3 = f"{cx - ts},{cy + ts}"
        parts.append(f'<polygon points="{p1} {p2} {p3}" style="fill: none; stroke: black; stroke-width: 0.8" />')
        return "".join(parts)

    def normalize_duration(value):
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            if not value:
                return None
            return max(value)
        return value

    def estimate_text_width(text, font_size):
        if not text:
            return 0
        return len(str(text)) * font_size * 0.6

    def closing_paren_x(open_paren_x, symbol_cx, symbol_radius, subscript_text, subscript_x, min_group_width=24, padding=-3):
        subscript_width = estimate_text_width(subscript_text, 7)
        left_group_right = max(symbol_cx + symbol_radius, subscript_x + subscript_width)
        group_width = left_group_right - open_paren_x
        return open_paren_x + max(group_width + padding, min_group_width)

    def layout_paren_group(open_paren_x, symbol_radius, subscript_offset=8, paren_width=4, gap=1):
        symbol_left_x = open_paren_x + paren_width + gap
        symbol_cx = symbol_left_x + symbol_radius
        subscript_x = symbol_cx + subscript_offset
        return symbol_cx, subscript_x
    
    # I⃗(place_symbol_t) = [values] - vector notation with arrow above
    # Position TOP (Impacts)
    if impacts:
        text_y = ty - 25  # Near top border
        impact_str = ",".join([f"{v:.1f}" for v in impacts]) if isinstance(impacts, list) else str(impacts)
        # Get region ID for subscript (use ONLY numeric region_id, not label)
        region_id = getattr(transition, 'region_id', None)
        if region_id is None:
            region_id = 't'  # Fallback
        # Draw: I with arrow ( [small place] region_id ) = [values]
        impact_shift = -3
        open_paren_x = tx - 47 + formula_shift + impact_shift
        impact_symbol_gap = 6  # distance between I and '('
        # Draw I with arrow using SVG (arrow above the letter)
        i_x = open_paren_x - impact_symbol_gap
        svg_parts.append(f'<text x="{i_x}" y="{text_y}" class="label" style="font-size: 10px; font-style: italic">I</text>')
        # Arrow above I: small line with arrowhead pointing right
        svg_parts.append(f'<line x1="{i_x - 3}" y1="{text_y - 10}" x2="{i_x + 5}" y2="{text_y - 10}" style="stroke: black; stroke-width: 0.8" />')
        svg_parts.append(f'<polygon points="{i_x + 5},{text_y - 10} {i_x + 2},{text_y - 12} {i_x + 2},{text_y - 8}" style="fill: black" />')
        # Opening parenthesis
        symbol_cx, subscript_x = layout_paren_group(open_paren_x, 5)
        svg_parts.append(f'<text x="{open_paren_x}" y="{text_y}" class="label" style="font-size: 10px; text-anchor: start;">(</text>')  # Moved left (-15)
        # Small place symbol centered between parentheses (moved slightly left)
        svg_parts.append(draw_small_place_symbol(symbol_cx, text_y - 3, size=5))  # Moved left (-15)
        # Subscript with region ID (positioned as subscript relative to place symbol)
        subscript_text = str(region_id)
        svg_parts.append(f'<text x="{subscript_x}" y="{text_y + 2}" class="label" style="font-size: 7px; font-style: italic; text-anchor: start;">{subscript_text}</text>')  # Moved left (-15)
        # Closing parenthesis and equals (dynamic spacing based on left group width)
        close_x = closing_paren_x(open_paren_x, symbol_cx, 5, subscript_text, subscript_x)
        svg_parts.append(f'<text x="{close_x}" y="{text_y}" class="label" style="font-size: 10px; text-anchor: start;">) = [{impact_str}]</text>')  # Moved left (-15)
    
    # 🕐(place_symbol_region_id) = d - clock symbol for time/duration
    # Position BOTTOM (Duration)
    duration_value = normalize_duration(duration)
    if duration_value is not None:
        text_y = ty + 30  # Near bottom border (moved down to 30)
        region_id = getattr(transition, 'region_id', None)
        if region_id is None:
            region_id = 't'  # Fallback
        # Clock icon (inline SVG)
        clock_x = tx - 65 + formula_shift
        clock_y = text_y - 9
        svg_parts.append(
            f'<svg x="{clock_x}" y="{clock_y}" width="16" height="16" '
            f'viewBox="-0.55 -0.55 1.1 1.1" fill="none" stroke="currentColor" '
            f'stroke-width="0.04" stroke-linecap="round" stroke-linejoin="round" '
            f'style="color:black">'
            f'<circle cx="0" cy="0" r="0.4"/>'
            f'<line x1="0" y1="0" x2="0" y2="-0.3"/>'
            f'<line x1="0" y1="0" x2="0.2" y2="0.2"/>'
            f'</svg>'
        )
        open_paren_x = tx - 47 + formula_shift
        symbol_cx, subscript_x = layout_paren_group(open_paren_x, 5)
        svg_parts.append(f'<text x="{open_paren_x}" y="{text_y}" class="label" style="font-size: 10px; text-anchor: start;">(</text>')
        # Small place symbol centered (moved slightly left)
        svg_parts.append(draw_small_place_symbol(symbol_cx, text_y - 3, size=5))  # Moved left (-15)
        # Subscript with region ID
        subscript_text = str(region_id)
        svg_parts.append(f'<text x="{subscript_x}" y="{text_y + 2}" class="label" style="font-size: 7px; font-style: italic; text-anchor: start;">{subscript_text}</text>')  # Moved left (-15)
        # Closing parenthesis and equals (dynamic spacing based on left group width)
        close_x = closing_paren_x(open_paren_x, symbol_cx, 5, subscript_text, subscript_x)
        svg_parts.append(f'<text x="{close_x}" y="{text_y}" class="label" style="font-size: 10px; text-anchor: start;">) = {duration_value}</text>')  # Moved left (-15)


def draw_gateway_transition(tx, ty, transition, svg_parts):
    """
    Draw a gateway transition as a triangle with appropriate styling.
    
    Args:
        tx, ty: Center coordinates
        transition: Transition object with region_type
        svg_parts: List to append SVG elements to
    """
    triangle_size = 15
    region_type_raw = transition.get_region_type() if hasattr(transition, 'get_region_type') else None
    # Handle Enum types - extract .value if it's an enum
    if region_type_raw and hasattr(region_type_raw, 'value'):
        region_type = region_type_raw.value
    else:
        region_type = str(region_type_raw) if region_type_raw else None
    label = transition.label or ""
    
    # Determine if this is an entry (split) or exit (join) transition
    # Use gateway_role attribute if available, fallback to stop property
    gateway_role = getattr(transition, 'gateway_role', None)
    if gateway_role == "join":
        is_split = False
    elif gateway_role == "split":
        is_split = True
    else:
        # Fallback: use stop property (stop=True means split for choice/nature)
        is_split = getattr(transition, 'stop', True)
    
    # Determine triangle points (always right-pointing)
    p1 = f"{tx - triangle_size},{ty - triangle_size}"
    p2 = f"{tx + triangle_size},{ty}"
    p3 = f"{tx - triangle_size},{ty + triangle_size}"
    
    # Determine style based on region type and entry/exit
    if region_type == "loop":
        # Loop: green (matching Nature)
        if is_split:
            fill_style = 'style="fill: none; stroke: #2E7D32; stroke-width: 2"'
        else:
            fill_style = 'style="fill: #2E7D32; stroke: #2E7D32"'
    elif region_type == "nature":
        # Nature: green
        if is_split:
            fill_style = 'style="fill: none; stroke: #2E7D32; stroke-width: 2"'
        else:
            fill_style = 'style="fill: #2E7D32; stroke: #2E7D32"'
    elif region_type == "choice":
        # Choice: orange
        if is_split:
            fill_style = 'style="fill: none; stroke: #E65100; stroke-width: 2"'
        else:
            fill_style = 'style="fill: #E65100; stroke: #E65100"'
    elif region_type == "parallel":
        # Parallel: black
        if is_split:
            fill_style = 'style="fill: none; stroke: black; stroke-width: 2"'
        else:
            fill_style = 'style="fill: black; stroke: black"'
    else:
        # Default: black
        if is_split:
            fill_style = 'style="fill: none; stroke: black; stroke-width: 2"'
        else:
            fill_style = 'style="fill: black; stroke: black"'
    
    svg_parts.append(f'<polygon points="{p1} {p2} {p3}" {fill_style} />')
    
    # Show probability for splits (e.g. Nature/Choice)
    if is_split:
         prob = getattr(transition, 'probability', None)
         if prob is not None:
             try:
                 prob_val = float(prob)
                 if prob_val < 0.999: # Show only if < 1 (significant probability)
                     # Show above the triangle (ty - 18)
                     svg_parts.append(f'<text x="{tx}" y="{ty - 18}" class="label" style="font-size: 11px; fill: black; text-anchor: middle;">{prob_val}</text>')
             except (ValueError, TypeError):
                 pass
    if label:
        svg_parts.append(f'<text x="{tx}" y="{ty}" class="label">{label}</text>')


def draw_transition(tx, ty, transition, svg_parts):
    """
    Draw a transition - dispatches to task or gateway drawing based on region_type.
    
    Args:
        tx, ty: Center coordinates
        transition: Transition object
        svg_parts: List to append SVG elements to
    """
    region_type_raw = transition.get_region_type() if hasattr(transition, 'get_region_type') else None
    # Handle Enum types - extract .value if it's an enum
    if region_type_raw and hasattr(region_type_raw, 'value'):
        region_type = region_type_raw.value
    elif region_type_raw:
        region_type = str(region_type_raw)
    else:
        region_type = None
    
    if region_type == "task":
        draw_task_transition(tx, ty, transition, svg_parts)
    else:
        draw_gateway_transition(tx, ty, transition, svg_parts)


def draw_arc(arc, positions, places, transitions, place_radius, transition_width, outgoing, svg_parts):
    """
    Draw an arc between two nodes with proper routing.
    
    Args:
        arc: Arc object with source and target
        positions: Dict of node positions
        places: List of all places
        transitions: List of all transitions
        place_radius: Radius of places
        transition_width: Width of transitions
        outgoing: Dict of outgoing connections
        svg_parts: List to append SVG elements to
    """
    src_name = arc.source.name
    tgt_name = arc.target.name
    
    if src_name not in positions or tgt_name not in positions:
        return
    
    x1, y1 = positions[src_name]
    x2, y2 = positions[tgt_name]
    
    # Detect arc type
    is_backward = x2 < x1
    is_to_loop_up = False
    is_from_loop_up = False
    
    # Check for Loop Back Transition specifically (Heuristic: it's high up!)
    # Or strict check if we passed identification info.
    # Heuristic: t_back is usually much higher (y < y1-40 or y < y2-40)
    # Better: Detect if one node is the designated "back" transition.
    # Since we don't have the region tree here easily, check if one node is 't' and positions indicate it's above.
    
    is_loop_back_arc = False
    # If one node is a transition and is positioned largely above the other (e.g. > 60px)
    # AND it's physically between them in X (roughly) or backward flow?
    # Loop Back Logic: 
    #   End Place -> Back Trans (Going Left-ish/Up)
    #   Back Trans -> Start Place (Going Left-ish/Down)
    
    mid_y = (y1 + y2) / 2
    
    # 2025-12-27 Fix: Refined heuristic.
    # Original 'abs(y1 - y2) > 50' was capturing "Choice" forward splits which are also steep.
    # Added 'x2 - x1 < 20' to ensure we only capture BACKWARD or VERTICAL (loop back) arcs.
    # Forward arcs (Choice/Parallel) will have x2 >> x1.
    if abs(y1 - y2) > 50 and (x2 - x1) < 20: 
         # Likely a loop back transition involved
         is_loop_back_arc = True
    
    # Determine style first to use in adjustments
    is_source_place = any(p.name == src_name for p in places)
    arc_class = "arc-white" if is_source_place else "arc"

    for t in transitions:
        if t.name == tgt_name and hasattr(t, 'get_region_type') and t.get_region_type() == 'loop_up':
            is_to_loop_up = True
        if t.name == src_name and hasattr(t, 'get_region_type') and t.get_region_type() == 'loop_up':
            is_from_loop_up = True
    
    # Calculate adjusted coordinates based on arc type
    if is_to_loop_up:
        x1_adj, y1_adj = x1, y1 - 15
    elif is_from_loop_up:
        x1_adj, y1_adj = x1 - 15, y1
    elif is_loop_back_arc:
         # Special handling for loop back: connect to top/bottom of nodes
         # If src is lower than tgt (End -> Back), output from Top
         if y1 > y2:
             if is_source_place:
                 x1_adj, y1_adj = x1, y1 - place_radius
             else:
                 x1_adj, y1_adj = x1, y1 - 15
         # If src is higher than tgt (Back -> Start), output from Left/Bottom?
         else:
             if is_source_place:
                 x1_adj, y1_adj = x1 - place_radius, y1
             else:
                 x1_adj, y1_adj = x1 - 15, y1
             
    elif is_backward:
        if any(p.name == src_name for p in places):
            x1_adj, y1_adj = x1, y1 + place_radius
        else:
            x1_adj, y1_adj = x1, y1 + 15
            
    else:
        if any(p.name == src_name for p in places):
            dx = x2 - x1
            dy = y2 - y1
            dist = (dx**2 + dy**2)**0.5
            if dist > 0:
                x1_adj = x1 + place_radius * dx / dist
                y1_adj = y1 + place_radius * dy / dist
            else:
                x1_adj, y1_adj = x1, y1
        else:
            x1_adj = x1 + transition_width // 2
            y1_adj = y1
    
    # Target point calculation
    if is_to_loop_up:
        x2_adj, y2_adj = x2 + 15, y2
    elif is_from_loop_up:
        x2_adj, y2_adj = x2, y2 - 15
    elif is_loop_back_arc:
         # If tgt is higher than src (End -> Back), input at Right/Bottom?
         if y2 < y1:
             x2_adj, y2_adj = x2 + 15, y2 # Input side of back trans
         # If tgt is lower than src (Back -> Start), input at Top
         else:
             is_tgt_place = any(p.name == tgt_name for p in places)
             if is_tgt_place:
                 x2_adj, y2_adj = x2, y2 - place_radius
             else:
                 x2_adj, y2_adj = x2, y2 - 15

    elif is_backward:
        if any(p.name == tgt_name for p in places):
            x2_adj, y2_adj = x2, y2 + place_radius
        else:
            x2_adj, y2_adj = x2, y2 + 15
    else:
        if any(p.name == tgt_name for p in places):
            dx = x2 - x1_adj
            dy = y2 - y1_adj
            dist = (dx**2 + dy**2)**0.5
            if dist > 0:
                x2_adj = x2 - place_radius * dx / dist
                y2_adj = y2 - place_radius * dy / dist
            else:
                x2_adj, y2_adj = x2, y2
        else:
            x2_adj = x2 - transition_width // 2
            y2_adj = y2
    
    # Determine style
    # Done earlier
    
    # Draw the path
    if is_to_loop_up:
        ctrl_x, ctrl_y = x1_adj, y2_adj
        svg_parts.append(f'<path d="M{x1_adj},{y1_adj} Q{ctrl_x},{ctrl_y} {x2_adj},{y2_adj}" class="{arc_class}" />')
    elif is_from_loop_up:
        ctrl_x, ctrl_y = x2_adj, y1_adj
        svg_parts.append(f'<path d="M{x1_adj},{y1_adj} Q{ctrl_x},{ctrl_y} {x2_adj},{y2_adj}" class="{arc_class}" />')
    elif is_loop_back_arc:
        # Custom curve for the "High" back transition
        # Case 1: End -> Back (Up and Left)
        if y1 > y2:
            # Control point: Corner approach (x1, y2)
            ctrl_x, ctrl_y = x1_adj, y2_adj
            svg_parts.append(f'<path d="M{x1_adj},{y1_adj} Q{ctrl_x},{ctrl_y} {x2_adj},{y2_adj}" class="{arc_class}" />')
        # Case 2: Back -> Start (Down and Left)
        else:
            # Control point: Corner approach (x2, y1)
            ctrl_x, ctrl_y = x2_adj, y1_adj
            svg_parts.append(f'<path d="M{x1_adj},{y1_adj} Q{ctrl_x},{ctrl_y} {x2_adj},{y2_adj}" class="{arc_class}" />')
            
    elif is_backward:
        curve_depth = 60
        mid_x = (x1_adj + x2_adj) / 2
        ctrl_y = min(y1_adj, y2_adj) - curve_depth
        svg_parts.append(f'<path d="M{x1_adj},{y1_adj} Q{mid_x},{ctrl_y} {x2_adj},{y2_adj}" class="{arc_class}" />')
    else:
        svg_parts.append(f'<path d="M{x1_adj},{y1_adj} L{x2_adj},{y2_adj}" class="{arc_class}" />')


def draw_region_box(region_label, node_names, positions, transitions, petri_net, places, transition_height, svg_parts):
    """
    Draw a region boundary box for a group of nodes.
    
    Args:
        region_label: Label for the region
        node_names: List of node names in this region
        positions: Dict of node positions
        transitions: List of transitions in the net
        petri_net: The full Petri net object
        places: List of places
        transition_height: Height of transitions
        svg_parts: List to append SVG elements to
    """
    if not node_names:
        return
    
    region_transitions = [t for t in transitions if t.name in node_names]
    
    # Find entry/exit places
    entry_places = set()
    exit_places = set()
    
    for t in region_transitions:
        for arc in petri_net.arcs:
            if arc.target.name == t.name:
                if any(p.name == arc.source.name for p in places):
                    entry_places.add(arc.source.name)
            elif arc.source.name == t.name:
                if any(p.name == arc.target.name for p in places):
                    exit_places.add(arc.target.name)
    
    all_x = []
    all_y = []
    
    for name in entry_places:
        if name in positions:
            all_x.append(positions[name][0])
            all_y.append(positions[name][1])
    
    for name in exit_places:
        if name in positions:
            all_x.append(positions[name][0])
            all_y.append(positions[name][1])
    
    for name in node_names:
        if name in positions:
            all_y.append(positions[name][1])
    
    if all_x and all_y:
        min_x = min(all_x)
        max_x = max(all_x)
        min_y = min(all_y) - transition_height - 10
        max_y = max(all_y) + transition_height + 10
        
        rect_width = max_x - min_x
        rect_height = max_y - min_y
        
        svg_parts.append(f'<rect x="{min_x}" y="{min_y}" width="{rect_width}" height="{rect_height}" rx="10" class="region" />')
        svg_parts.append(f'<text x="{(min_x + max_x) / 2}" y="{min_y - 5}" class="label">{region_label}</text>')


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def layout_petri_net(petri_net, width, height):
    """
    Calculate node positions using BFS layer assignment (Flat Layout).
    
    Args:
        petri_net: WrapperPetriNet object
        width: SVG width
        height: SVG height
        
    Returns:
        positions: Dict {name: (x, y)}
    """
    
    # Layout parameters
    margin = 50
    place_radius = 20
    transition_width = 40
    transition_height = 30
    spacing = 100
    
    # Collect all nodes
    places = list(petri_net.places)
    transitions = list(petri_net.transitions)
    
    positions = {}
    
    # Build adjacency info
    outgoing = {}
    incoming = {}
    
    for arc in petri_net.arcs:
        src = arc.source.name
        tgt = arc.target.name
        if src not in outgoing:
            outgoing[src] = []
        outgoing[src].append(tgt)
        if tgt not in incoming:
            incoming[tgt] = []
        incoming[tgt].append(src)
    
    # Find start place (must have no incoming arcs)
    start_place = None
    for p in places:
        has_incoming = p.name in incoming and len(incoming[p.name]) > 0
        if not has_incoming:
            if hasattr(p, 'entry_id') and p.entry_id:
                start_place = p
                break
            elif start_place is None:
                start_place = p
    
    if not start_place and places:
        start_place = list(places)[0]
    
    # Assign layers using BFS
    layers = {}
    y_positions = {}
    
    if start_place:
        queue = [(start_place.name, 0)]
        layers[start_place.name] = 0
        y_positions[start_place.name] = height // 2
        
        while queue:
            node_name, layer = queue.pop(0)
            
            if node_name in outgoing:
                targets = outgoing[node_name]
                
                loop_up_targets = []
                normal_targets = []
                for tgt in targets:
                    tgt_obj = None
                    for t in transitions:
                        if t.name == tgt:
                            tgt_obj = t
                            break
                    
                    if tgt_obj and hasattr(tgt_obj, 'get_region_type') and tgt_obj.get_region_type() == 'loop_up':
                        loop_up_targets.append(tgt)
                    else:
                        normal_targets.append(tgt)
                
                for tgt in loop_up_targets:
                    if tgt not in layers:
                        loop_dest = outgoing.get(tgt, [])[0] if outgoing.get(tgt) else None
                        dest_layer = layers.get(loop_dest, layer)
                        layers[tgt] = (layer + dest_layer) / 2
                        y_positions[tgt] = y_positions[node_name] - 80
                
                num_targets = len(normal_targets)
                if num_targets > 1:
                    y_offset = 100  # Increased vertical spacing between branches
                    start_y = y_positions[node_name] - (num_targets - 1) * y_offset / 2
                    for i, tgt in enumerate(normal_targets):
                        if tgt not in layers:
                            layers[tgt] = layer + 1
                            y_positions[tgt] = start_y + i * y_offset
                            queue.append((tgt, layer + 1))
                else:
                    for tgt in normal_targets:
                        if tgt not in layers:
                            layers[tgt] = layer + 1
                            y_positions[tgt] = y_positions[node_name]
                            queue.append((tgt, layer + 1))
    
    # Post-processing: Center merge nodes
    incoming_forward = {node: [] for node in layers}
    for src, tgts in outgoing.items():
        if src in layers:
            for tgt in tgts:
                if tgt in layers and layers[tgt] > layers[src]:
                    incoming_forward[tgt].append(src)
    
    sorted_nodes = sorted(layers.keys(), key=lambda n: layers[n])
    for node in sorted_nodes:
        parents = incoming_forward[node]
        if len(parents) > 1:
            avg_y = sum(y_positions[p] for p in parents) / len(parents)
            y_positions[node] = avg_y
        elif len(parents) == 1:
            parent = parents[0]
            parent_forward_children = [t for t in outgoing.get(parent, []) if t in layers and layers[t] > layers[parent]]
            if len(parent_forward_children) == 1:
                y_positions[node] = y_positions[parent]
    
    # Convert layers to X positions
    for name, layer in layers.items():
        x = margin + layer * spacing
        y = y_positions.get(name, height // 2)
        positions[name] = (x, y)
    
    # Add any missed nodes
    x = margin
    for p in places:
        if p.name not in positions:
            positions[p.name] = (x, height // 2)
            x += spacing
    for t in transitions:
        if t.name not in positions:
            positions[t.name] = (x, height // 2)
            x += spacing
            
    return positions


# =============================================================================
# MAIN FUNCTION
# =============================================================================

def petri_net_to_svg(petri_net, width=800, height=400, region_tree=None, marking=None):
    """
    Generate SVG code for the Petri net with custom visualization.
    Uses recursive drawing functions for nested structures.
    
    Args:
        petri_net: WrapperPetriNet object
        width: SVG width in pixels
        height: SVG height in pixels
        region_tree: Optional RegionNode tree for hierarchical region boxes
        marking: Optional TimeMarking for token visualization
    
    Returns:
        SVG string
    """
    
    # Layout parameters
    place_radius = 20
    transition_width = 40
    transition_height = 30
    
    # Collect all nodes
    places = list(petri_net.places)
    transitions = list(petri_net.transitions)
    
    positions = {}
    
    # Build adjacency info
    outgoing = {}
    incoming = {}
    
    for arc in petri_net.arcs:
        src = arc.source.name
        tgt = arc.target.name
        if src not in outgoing:
            outgoing[src] = []
        outgoing[src].append(tgt)
        if tgt not in incoming:
            incoming[tgt] = []
        incoming[tgt].append(src)
    
    if region_tree:
        # HIERARCHICAL LAYOUT
        # 1. Calculate sizes bottom-up
        calculate_node_size(region_tree)
        
        # 2. Assign positions top-down
        # Start at (50, 50)
        layout_node_recursive(region_tree, 50, 50, positions, transitions, places)
        
        # 3. Add any missed nodes (fallback)
        for p in places:
            if p.name not in positions:
                positions[p.name] = (50, 50)
        for t in transitions:
            if t.name not in positions:
                positions[t.name] = (50, 50)
                
        # 4. Calculate total size
        max_x = 0
        max_y = 0
        for x,y in positions.values():
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            
        region_tree.size  # Root size
        
        # Calculate max extent from regions as well
        def get_tree_max_extent(node):
            mx, my = 0, 0
            if node.bounds:
                x, y, w, h = node.bounds
                mx = x + w
                my = y + h
            
            for child in node.children:
                cmx, cmy = get_tree_max_extent(child)
                mx = max(mx, cmx)
                my = max(my, cmy)
            return mx, my

        rmx, rmy = get_tree_max_extent(region_tree)
        max_x = max(max_x, rmx)
        max_y = max(max_y, rmy)
        
        # Adjust SVG size if needed
        # We can pass calculate_node_size result back or just trust positions
        if max_x + 100 > width: width = int(max_x + 100)
        if max_y + 100 > height: height = int(max_y + 100)
            
    else:
        # FLAT BFS LAYOUT (Legacy)
        positions = layout_petri_net(petri_net, width, height)
    
    # Collect regions (for old drawing method - maybe skip if tree is present)
    regions = {}
    if not region_tree:
        for t in transitions:
            region_label = t.get_region_label() if hasattr(t, 'get_region_label') else None
            if region_label:
                if region_label not in regions:
                    regions[region_label] = []
                regions[region_label].append(t.name)
    
    # Build SVG
    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    svg_parts.append('<style>')
    svg_parts.append('  .place { fill: white; stroke: black; stroke-width: 1.5; }')
    svg_parts.append('  .place.token { fill: rgba(0, 0, 0, 0.12); }')
    svg_parts.append('  .transition { fill: white; stroke: black; stroke-width: 1.5; }')
    svg_parts.append('  .region { fill: none; stroke: black; stroke-width: 2; rx: 10; }')
    svg_parts.append('  .arc { fill: none; stroke: black; stroke-width: 1; marker-end: url(#doubleArrowhead); }')
    svg_parts.append('  .arc-white { fill: none; stroke: black; stroke-width: 1; marker-end: url(#doubleArrowheadWhite); }')
    svg_parts.append('  .label { font-family: Arial; font-size: 12px; text-anchor: middle; dominant-baseline: middle; }')
    svg_parts.append('</style>')
    
    svg_parts.append('<defs>')
    # Doppia punta unidirezionale NERA (>>)
    svg_parts.append('  <marker id="doubleArrowhead" markerWidth="15" markerHeight="7" refX="14" refY="3.5" orient="auto">')
    svg_parts.append('    <polygon points="0 0, 7 3.5, 0 7" fill="black" />')
    svg_parts.append('    <polygon points="7 0, 14 3.5, 7 7" fill="black" />')
    svg_parts.append('  </marker>')
    
    # Doppia punta unidirezionale BIANCA (>>)
    svg_parts.append('  <marker id="doubleArrowheadWhite" markerWidth="15" markerHeight="7" refX="14" refY="3.5" orient="auto">')
    svg_parts.append('    <polygon points="0 0, 7 3.5, 0 7" fill="white" stroke="black" stroke-width="1" />')
    svg_parts.append('    <polygon points="7 0, 14 3.5, 7 7" fill="white" stroke="black" stroke-width="1" />')
    svg_parts.append('  </marker>')
    svg_parts.append('</defs>')
    
    # Draw regions (background)
    if region_tree:
        # Use hierarchical region drawing
        calculate_region_bounds(region_tree, positions)
        draw_hierarchical_regions(region_tree, svg_parts)
    else:
        # Fallback to flat region drawing
        for region_label, node_names in regions.items():
            draw_region_box(region_label, node_names, positions, transitions, petri_net, places, transition_height, svg_parts)
    
    # Draw arcs
    for arc in petri_net.arcs:
        draw_arc(arc, positions, places, transitions, place_radius, transition_width, outgoing, svg_parts)
    
    # Draw outer R region (only when not using hierarchical regions)
    if positions and not region_tree:
        all_positions = list(positions.values())
        all_x = [p[0] for p in all_positions]
        all_y = [p[1] for p in all_positions]
        
        outer_margin = 50
        outer_x = min(all_x) - outer_margin
        outer_y = min(all_y) - outer_margin
        outer_w = max(all_x) - min(all_x) + 2 * outer_margin
        outer_h = max(all_y) - min(all_y) + 2 * outer_margin
        
        svg_parts.insert(13, f'<rect x="{outer_x}" y="{outer_y}" width="{outer_w}" height="{outer_h}" rx="10" style="fill: none; stroke: black; stroke-width: 2" />')
        svg_parts.insert(14, f'<text x="{outer_x + 20}" y="{outer_y + 25}" class="label" style="font-size: 18px; font-style: italic">R</text>')
    
    # Draw places using helper function
    for place in places:
        if place.name in positions:
            px, py = positions[place.name]
            draw_place(px, py, place, place_radius, incoming, outgoing, svg_parts, marking=marking)
    
    # Draw transitions using helper function
    for t in transitions:
        if t.name in positions:
            tx, ty = positions[t.name]
            draw_transition(tx, ty, t, svg_parts)
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)

# =============================================================================
# API INTEGRATION FUNCTIONS
# =============================================================================

def region_model_to_region_node(region, depth: int = 0):
    """
    Convert RegionModel (from model/region.py) to RegionNode tree for SVG layout.
    
    Args:
        region: RegionModel object with type, id, label, children, etc.
        depth: Current depth in tree (for node_id calculation)
    
    Returns:
        RegionNode instance ready for hierarchical layout
    """
    # Get node type from RegionModel - it uses RegionType enum
    if hasattr(region, 'type'):
        if hasattr(region.type, 'value'):
            node_type = region.type.value  # 'sequential', 'parallel', etc.
        else:
            node_type = str(region.type)
    else:
        node_type = 'task'
    
    # Build children recursively
    children = []
    if hasattr(region, 'children') and region.children:
        for i, child in enumerate(region.children):
            children.append(region_model_to_region_node(child, depth + 1))
    
    # Get label with smart fallback
    explicit_label = getattr(region, 'label', None)
    rid = getattr(region, 'id', depth)
    if node_type in ['sequential', 'parallel']:
        # Concatenate labels of all children for sequential/parallel
        child_labels = [child.label for child in children if child.label]
        separator = ", " if node_type == 'sequential' else " || "
        label = separator.join(child_labels)
        if label:
            label = f"({label})"
        else:
            label = f"{'R' if node_type == 'sequential' else 'P'}{rid}"
    elif node_type in ['choice', 'nature']:
        # Choice/Nature: combine children with operator and include tag in brackets
        child_labels = [child.label for child in children if child.label]
        tag = explicit_label or f"{'C' if node_type == 'choice' else 'N'}{rid}"
        if child_labels:
            op = "/" if node_type == 'choice' else "^"
            joiner = f" {op} [{tag}] "
            label = f"({joiner.join(child_labels)})"
        else:
            label = f"{'C' if node_type == 'choice' else 'N'}{rid}"
    elif explicit_label:
        label = explicit_label
    else:
        # Generate label based on type
        prefix_map = {
            'nature': 'N',
            'choice': 'C',
            'parallel': 'P',
            'loop': 'L',
            'task': 'T',
            'sequential': 'R'
        }
        # Default to 'R' if type not found
        prefix = prefix_map.get(node_type, 'R')
        label = f"{prefix}{rid}"
    
    # Get node_id
    node_id = getattr(region, 'id', depth)
    
    return RegionNode(
        node_type=node_type,
        node_id=node_id,
        label=label,
        children=children,
        elements=[]  # Elements will be populated during layout if needed
    )


def find_node_by_id(root, target_id):
    """Find a RegionNode by its node_id recursively."""
    # Convert both to string for robust comparison
    if str(root.node_id) == str(target_id):
        return root
    
    for child in root.children:
        found = find_node_by_id(child, target_id)
        if found:
            return found
            
    return None


def spin_to_svg(net, width=800, height=400, region=None, marking=None):
    """
    Generate SVG visualization for a SPIN (Petri net) model.
    
    This is the main API entry point for SVG generation.
    
    Args:
        net: WrapperPetriNet object
        width: SVG width in pixels
        height: SVG height in pixels
        region: Optional RegionModel for hierarchical layout
        marking: Optional TimeMarking for token visualization
    
    Returns:
        SVG string
    """
    region_tree = None
    if region is not None:
        region_tree = region_model_to_region_node(region)
        
        # POPULATE ELEMENTS into the tree nodes
        # Iterate transitions
        for t in net.transitions:
            # Check for region_id attribute (created by converter)
            rid = getattr(t, 'region_id', None)
            if rid is not None:
                node = find_node_by_id(region_tree, rid)
                if node:
                    node.add_element(t.name)
        
        # Iterate places
        for p in net.places:
            # Places might belong to entry/exit of a region
            entry_id = getattr(p, 'entry_id', None)
            exit_id = getattr(p, 'exit_id', None)
            
            if entry_id is not None:
                node = find_node_by_id(region_tree, entry_id)
                if node:
                    node.add_element(p.name)
            
            # Use 'if' not 'elif' because a place can be both Entry of X and Exit of Y
            # (e.g. collapsed sequential, or loop child anchor)
            if exit_id is not None:
                node = find_node_by_id(region_tree, exit_id)
                if node:
                    node.add_element(p.name)
    
    return petri_net_to_svg(net, width, height, region_tree, marking=marking)


def save_svg(svg_content, filepath):
    """Save SVG content to file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)

