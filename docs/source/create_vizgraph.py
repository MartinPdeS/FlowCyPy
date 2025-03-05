from graphviz import Digraph

def add_population(graph, name):
    """Add a population node with its associated RI and Diameter Distribution nodes."""
    graph.node(name, shape='box', **POP_kwargs)
    graph.node(f'RI_D_{name}', 'RI Distribution', shape='box', **DIST_kwargs)
    graph.node(f'Size_D_{name}', 'Diameter Distribution', shape='box', **DIST_kwargs)
    graph.edge(name, f'RI_D_{name}', fontsize='10', style='solid')
    graph.edge(name, f'Size_D_{name}', fontsize='10', style='solid')

def add_detector_cluster(graph, detector_names):
    """Add a cluster for detectors with the given names."""
    with graph.subgraph(name='cluster_detectors') as det:
        det.attr(label='Detectors', style='rounded,dashed', color='lightgrey', fontsize='12', fontname=fontname)
        for name in detector_names:
            det.node(name, name, shape='box', style='rounded,filled',
                     fillcolor='lightgrey', fontsize='14', fontname=fontname)
        # Enforce same rank for detectors (horizontal alignment)
        det.attr(rank='same')

# Global styling parameters.
fontname = "Times New Roman"
POP_kwargs = {
    'style': 'rounded,filled',
    'fillcolor': 'lightblue',
    'fontsize': '12',
    'fontname': fontname
}
DIST_kwargs = {
    'style': 'rounded,filled',
    'fillcolor': 'lightyellow',
    'fontsize': '12',
    'fontname': fontname
}

# Create the main graph.
dot = Digraph('Architecture', comment='ScattererCollection Architecture', format='png')
dot.attr(rankdir='TB', splines='ortho', fontsize='10', fontname=fontname)

# Main nodes.


with dot.subgraph(name='acq_sub') as cluster:
    cluster.attr(rank='same')
    cluster.node('TriggeringSystem', 'TriggeringSystem', shape='box', style='rounded,filled', fillcolor='lightgrey', fontsize='14', fontname=fontname)
    cluster.node('SignalProcessing', 'SignalProcessing', shape='box', style='rounded,filled', fillcolor='lightgrey', fontsize='14', fontname=fontname)
    cluster.node('Acquisition', 'Acquisition', shape='box', style='rounded,filled', fillcolor='lightgrey', fontsize='14', fontname=fontname)

dot.node('TriggeredAcquisition', 'TriggeredAcquisition', shape='box', style='rounded,filled', fillcolor='lightgrey', fontsize='14', fontname=fontname)
dot.node('FlowCytometer', 'FlowCytometer', shape='box', style='rounded,filled', fillcolor='lightgrey', fontsize='14', fontname=fontname)
dot.node('SignalDigitizer', 'SignalDigitizer', shape='box', style='rounded,filled', fillcolor='lightgrey', fontsize='14', fontname=fontname)
dot.node('FlowCell', 'FlowCell', shape='box', style='rounded,filled', fillcolor='lightgrey', fontsize='14', fontname=fontname)
dot.node('ScattererCollection', 'ScattererCollection', shape='box', style='rounded,filled', fillcolor='lightgrey', fontsize='14', fontname=fontname)

# Add detectors cluster.
add_detector_cluster(dot, ['Detector 1', 'Detector 2'])

# Create a cluster for populations.
with dot.subgraph(name='cluster_populations') as pop_cluster:
    pop_cluster.attr(label='Populations', style='rounded,dashed', fontsize='12', fontname=fontname)
    add_population(pop_cluster, 'Population 0')
    add_population(pop_cluster, 'Population 1')

# Define connections.
dot.edge('Acquisition', 'FlowCytometer', style='solid', fontsize='10')
dot.edge('TriggeredAcquisition', 'Acquisition', style='solid', fontsize='10')
dot.edge('FlowCytometer', 'SignalDigitizer', style='solid', fontsize='10')
dot.edge('FlowCytometer', 'Detector 1', style='solid', fontsize='10')
dot.edge('FlowCytometer', 'Detector 2', style='solid', fontsize='10')
dot.edge('FlowCytometer', 'ScattererCollection', style='solid', fontsize='10')
dot.edge('FlowCytometer', 'FlowCell', style='solid', fontsize='10')
dot.edge('ScattererCollection', 'Population 0', style='solid', fontsize='10')
dot.edge('ScattererCollection', 'Population 1', style='solid', fontsize='10')


dot.edge('SignalProcessing', 'Acquisition', style='solid', fontsize='10', dir='back')
dot.edge('Acquisition', 'TriggeringSystem', style='solid', fontsize='10')




# Render and view the graph.
dot.render('Architecture', view=True)
