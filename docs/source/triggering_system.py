import graphviz
fontname = "Times-Bold"

def create_beautiful_flowchart():
    dot = graphviz.Digraph(comment='Dynamic Triggering with Hysteresis and Debounce')

    # dot.attr(bgcolor='white', label='agraph', fontcolor='black', fontname=fontname)
    # Global graph styling
    dot.attr(rankdir='TB', splines='ortho', nodesep='0.6', ranksep='0.8')
    # dot.attr('node', style='filled', shape='box', fontname=fontname, fontsize='10', fixedsize='false', margin='0.2,0.1')

    dot.attr('node', style='filled, rounded', shape='box', fillcolor='grey', fontname=fontname, fontsize='10', fixedsize='false', margin='0.3,0.1')
    dot.attr('edge', style='filled', shape='box', fontname=fontname, fontsize='10', labeldistance='0.001')


    # Define nodes with enhanced styling.
    dot.node('Start', 'Start')
    # dot.node('A', 'Check Rising Edge:\n(signal[i-1] ≤ lower_threshold\nand signal[i] > upper_threshold?)')
    dot.node('A', 'Check Rising Edge')
    dot.node('C', 'Is Debounce Enabled\nand min_duration ≠ -1?')
    dot.node('D', 'Count Consecutive Samples\n> upper_threshold')
    dot.node('E', 'Is Count ≥ min_duration?')
    dot.node('F', 'Not enough samples.\nSkip Candidate (i = j)')
    dot.node('G', 'Proceed\n(Debounce Disabled or Check Passed)')
    dot.node('H', 'Compute Start Index:\nstart = max(i - pre_buffer, 0)')
    dot.node('I', 'Extend Trigger:\nwhile signal > lower_threshold\n(set k)')
    dot.node('J', 'Compute End Index:\nend = min(k - 1 + post_buffer,\nsignal_length - 1)')
    dot.node('K', 'Add Valid Trigger\n(if non overlapping)')
    dot.node('L', 'Update Loop Index:\ni = k')
    dot.node('M', 'Loop back for next trigger')
    dot.node('End', 'End Algorithm')

    # Define edges with styling.
    dot.edge('Start', 'A', color='#34495E')
    dot.edge('A', 'C', xlabel='Yes', fontsize='9')
    dot.edge('C', 'D', xlabel='Yes', fontsize='9')
    dot.edge('C', 'G', xlabel='No', fontsize='9')
    dot.edge('D', 'E')
    dot.edge('E', 'G', xlabel='Yes', fontsize='9')
    dot.edge('E', 'F', xlabel='No', fontsize='9')
    dot.edge('F', 'L', xlabel='Skip Candidate', fontsize='9')
    dot.edge('G', 'H')
    dot.edge('H', 'I')
    dot.edge('I', 'J')
    dot.edge('J', 'K')
    dot.edge('K', 'L')
    dot.edge('L', 'M')
    dot.edge('M', 'A', xlabel='Next Iteration', fontsize='9')
    dot.edge('A', 'End', xlabel='No', style='dashed', fontsize='9', color='#E74C3C')
    return dot

if __name__ == '__main__':
    flowchart = create_beautiful_flowchart()
    # Render and save the flowchart as a PDF and open it.
    flowchart.render(filename='triggering_flowchart', format='pdf', view=True)
