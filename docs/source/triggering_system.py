import graphviz
fontname = "Times-Bold"

def TB_create_beautiful_flowchart():
    dot = graphviz.Digraph(comment='Dynamic Triggering with Hysteresis and Debounce')

    # dot.attr(bgcolor='white', label='agraph', fontcolor='black', fontname=fontname)
    # Global graph styling
    dot.attr(rankdir='LR', splines='ortho', nodesep='0.6', ranksep='0.8')
    # dot.attr('node', style='filled', shape='box', fontname=fontname, fontsize='10', fixedsize='false', margin='0.2,0.1')

    dot.attr('node', style='filled, rounded', shape='box', fillcolor='lightgrey', fontname=fontname, fontsize='10', fixedsize='false', margin='0.3,0.1')
    dot.attr('edge', style='filled', shape='box', fontname=fontname, fontsize='10', labeldistance='0.001')


    # Define nodes with enhanced styling.
    dot.node('Start', 'Start: index i')
    dot.node('A', 'Check Rising Edge:\ns[i-1] ≤ lower_threshold & s[i] > upper_threshold?')

    dot.node('C', 'Is Debounce Enabled?')

    with dot.subgraph(name='cluster') as cluster:
        cluster.attr(label='Debouncer', style='rounded,dashed', fontsize='12', labelloc='t', labeljust='l')
        cluster.node('D', 'Count Consecutive Samples\n> upper_threshold')
        cluster.node('E', 'Is Count ≥ min_duration?')

    dot.node('F', 'Not enough samples.\nSkip Candidate (i = j)')
    # dot.node('G', 'Proceed\n(Debounce Disabled or Check Passed)')
    dot.node('H', 'Compute Start Index:\nstart = max(i - pre_buffer, 0)')
    dot.node('I', 'Extend Trigger:\nwhile signal > lower_threshold\n(set k)')
    dot.node('J', 'Compute End Index:\nend = min(k - 1 + post_buffer,\nsignal_length - 1)')
    dot.node('K', 'Add Valid Trigger\n(if non overlapping)')
    dot.node('L', 'Update Loop Index:\ni = k')
    dot.node('M', 'Loop back for next trigger')
    dot.node('End', 'End Algorithm')


    NO = 'No  '
    YES = 'Yes  '
    # Define edges with styling.
    dot.edge('Start', 'A', color='#34495E')
    dot.edge('A', 'C', xlabel=YES, fontsize='9')
    dot.edge('C', 'D', xlabel=YES, fontsize='9')
    dot.edge('C', 'H', xlabel='        No', fontsize='9')
    dot.edge('D', 'E')
    dot.edge('E', 'H', xlabel=YES, fontsize='9')
    dot.edge('E', 'F', xlabel=NO, fontsize='9')
    dot.edge('F', 'L', xlabel='Skip Candidate  ', fontsize='9')
    # dot.edge('G', 'H')
    dot.edge('H', 'I')
    dot.edge('I', 'J')
    dot.edge('J', 'K')
    dot.edge('K', 'L')
    dot.edge('L', 'M')
    dot.edge('M', 'A', xlabel='\n Next Iteration  ', fontsize='9')
    dot.edge('A', 'End', xlabel=NO, style='dashed', fontsize='9', color='#E74C3C')
    return dot

def create_compact_flowchart():
    dot = graphviz.Digraph(comment='Compact Dynamic Triggering')

    # Set a horizontal layout with reduced spacing.
    dot.attr(rankdir='LR', splines='ortho', nodesep='0.4', ranksep='0.5')

    # Global node styling: smaller font and margin.
    dot.attr('node', style='filled,rounded', shape='box',
             fillcolor='lightgrey', fontname='Times-Bold', fontsize='8',
             fixedsize='false', margin='0.1,0.1')

    # Global edge styling: use a smaller font.
    dot.attr('edge', fontname='Times-Bold', fontsize='8', labeldistance='0.001')

    # Define nodes (shortened labels for compactness).
    dot.node('A', 'Check Rising Edge:\ns[i-1] ≤ lower & s[i] > upper?')
    dot.node('C', 'Debounce Enabled?')

    # Subgraph for the debouncer.
    with dot.subgraph(name='cluster') as cluster:
        cluster.attr(label='Debouncer', style='rounded,dashed', fontsize='10', labelloc='t', labeljust='l')
        cluster.node('D', 'Count Samples\n> upper')
        cluster.node('E', 'Is Count ≥\nmin_duration?')

    dot.node('F', 'Not enough samples.')
    dot.node('H', 'Compute Start Index:\nstart = max(i - pre, 0)')
    dot.node('I', 'Extend Trigger:\nwhile signal > lower\n(set k)')
    dot.node('J', 'Compute End Index:\nend = min(k - 1 + post,\nlength - 1)')
    # dot.node('K', 'Add Valid Trigger\n(if non overlapping)')
    dot.node('L', 'Update Loop Index:\ni = k')
    dot.node('M', 'Loop for Next Trigger')
    dot.node('End', 'End Algorithm')

    # Define edges with compact labels.
    YES = 'Yes'
    NO  = 'No'
    # dot.edge('Start', 'A', color='#34495E')
    dot.edge('A', 'C',  xlabel=YES, fontsize='8')
    dot.edge('C', 'D', xlabel=YES, fontsize='8')
    dot.edge('C', 'H', xlabel='    No', fontsize='8')  # Padding via spaces
    dot.edge('D', 'E')
    dot.edge('E', 'H', xlabel=YES, fontsize='8')
    dot.edge('E', 'F', xlabel=NO, fontsize='8')
    dot.edge('F', 'L', xlabel='Skip Candidate', fontsize='8')
    dot.edge('H', 'I')
    dot.edge('I', 'J')
    dot.edge('J', 'L')
    # dot.edge('K', 'L')
    dot.edge('L', 'M')
    dot.edge('M', 'A', xlabel='\nNext Iteration', fontsize='8')
    dot.edge('A', 'End', xlabel=NO, style='dashed', fontsize='8', color='#E74C3C')

    return dot

if __name__ == '__main__':
    flowchart = create_compact_flowchart()
    # Render and save the flowchart as a PDF and open it.
    flowchart.render(filename='triggering_flowchart', format='png', view=False)
