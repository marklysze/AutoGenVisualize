from typing import Dict, List
from uuid import uuid4
from graphviz import Digraph
import re
from agvisualize.visualization_tools import *
from agvisualize.log_data import LogAgent, LogEvent, LogClient, LogInvocation, LogSession
from agvisualize.log_processing import load_log_file

def visualize_execution(diagram_name: str, log_file_path: str, directory: str, filename: str, format: str):
    '''Create the diagram of the program execution'''

    design_config: Dict = {
        "canvas_replace_bg": "#123456", # This colour will be replaced by "url(#bg_pattern)" which is a pattern defined in the SVG (added post-creation). Colour should be unique.
        "canvas_pattern_bg": "#222222",
        "canvas_pattern_color": "#2A2A2A",
        "nested_bg": "#18184F",
        "groupchat_bg": "#004F4F",
        "start_bg": "#222222",
        "start_font_color": "#FFFFFF",
        "start_border_color": "#6666FF",
        "fill_color": "#DDFFF7",
        "border_color": "#00BE92",
        "font_color": "#FAFAFA",
        "node_font_color": "#222222",
        "edge_color": "#6666FF",
        "edge_success_color": "#00FF00",
        "edge_unsuccessful_color": "#FF0000",
        "edge_style": "solid",
        "edge_style_silent": "dashed",
        "font_names": "Helvetica, DejaVu Sans, Arial, Courier, sans-serif",
        "label_distance": "5.0",
        "node_pen_width": "3.0",
        "node_shape": {
            "agent": "oval",
            "summary": "parallelogram",
            "terminate": "octagon",
            "invocation": "invhouse",
            "info": "note",
            "code_execution": "cds",
            "human": "Mdiamond"
        },
    }

    def summary_text(summary) -> str:
        """Returns the summary text for a summary result"""

        if isinstance(summary, str):
            return summary
        elif isinstance(summary, dict):
            if 'summary' in summary:
                return summary['summary']['content']
            elif 'content' in summary:
                return summary['content']
            else:
                raise "Can't summarise!"
        else:
            raise "Can't summarise"

    def create_nested_digraph(nested_chat_node_name: str, label: str, color: str) -> Digraph:
        """Creates a nested digraph"""
        nested_graph = Digraph(nested_chat_node_name)
        nested_graph.attr(style='rounded, filled', color=_darken_color(color, 0.1), fillcolor=color, label=label, labeljust="r", labelloc="b", penwidth="5", margin="35", fontcolor=design_config["font_color"], fontname=design_config["font_names"])
        return nested_graph
    
    def process_level(top_level: bool, current_level: Digraph, level_id, items: List, start_index: int, current_nested_chat_id: str, parent_agent: LogAgent) -> int:
        current_agent: LogAgent = None
        last_termination: LogEvent = None
        last_nested_summarize_level_and_event: List[Digraph, LogEvent] = None
        available_invocations = []
        last_nested_agent: LogAgent = None # Coming out of a nested chat, we track the last agent to see if we link to it on the next event

        i = start_index
        while i < len(items):
            item = items[i]

            if isinstance(item, LogClient):
                client: LogClient = item

                # For each client, add the client_id to the wrapper dictionary so we can resolve any client_ids that don't appear in the log file
                # Can occur with group chat's inner auto speaker select chat
                if client.wrapper_id in wrapper_clients:
                    wrapper_clients[client.wrapper_id].append(client.client_id)
                else:
                    wrapper_clients[client.wrapper_id] = [client.client_id]

            elif isinstance(item, LogAgent):
                agent: LogAgent = agents[item.id]

                # Assign an number to the agent as we'll be repeating the agent throughout the diagram
                # Every new instance will have an incremented number
                if not "index" in agent.visualization_params:
                    agent.visualization_params["index"] = 0

                # Assign a colour to the agent
                if not agent.id in agent_colors:
                    _assign_agent_color(agent_colors, agent.id)
                    agent.visualization_params["color"] = agent_colors[agent.id]

            elif isinstance(item, LogEvent):
                event: LogEvent = item

                if event.event_name in ["_summary_from_nested_chat start", "_auto_select_speaker start", "a_auto_select_speaker start"]:
                    nested_chat_id = event.json_state['nested_chat_id' if event.event_name == "_summary_from_nested_chat start" else 'auto_select_speaker_id']
                    next_level_id = str(uuid4())
                    nested_chat_node_name = f'cluster_{next_level_id}'
                    
                    label = "Nested Chat" if event.event_name == "_summary_from_nested_chat start" else "Group Chat Auto Select Speaker"
                    color = design_config["nested_bg"] if event.event_name == "_summary_from_nested_chat start" else design_config["groupchat_bg"]
                    
                    new_nested = create_nested_digraph(nested_chat_node_name, label, color)
                    
                    nested_chats[nested_chat_id] = {
                        "type": "Nested Chat" if event.event_name == "_summary_from_nested_chat start" else "Group Chat",
                        "edge_label": "Nested Chat" if event.event_name == "_summary_from_nested_chat start" else "Auto Select Speaker",
                        "level_index": next_level_id,
                        "parent_agent_node_id": _agent_id_by_name(agents, event.source_name),
                        "nested_chat_node_name": nested_chat_node_name,
                        "linked_to_parent_agent_node": False
                    }
                    nested_graphs[next_level_id] = new_nested
                    
                    i, last_nested_agent = process_level(False, new_nested, next_level_id, items, i + 1, nested_chat_id, current_agent)
                    current_level.subgraph(new_nested)
                    continue

                elif event.event_name in ["_summary_from_nested_chat end", "_auto_select_speaker end", "a_auto_select_speaker end"]:

                    # End the nested chat
                    return i+1, current_agent

                elif event.event_name == "received_message":

                    '''
                    # If we want to ignore silent events, however we do need to show some.
                    if "silent" in event.json_state and event.json_state["silent"] == True:
                        # Ignore silent messages
                        i += 1
                        continue
                    '''

                    is_silent = "silent" in event.json_state and event.json_state["silent"] == True

                    sender_agent = agents[_agent_id_by_name(agents, event.json_state["sender"])]
                    recipient_agent = agents[_agent_id_by_name(agents, event.source_name)]

                    if top_level and current_agent is None:
                        _add_node_agent(design_config, agents, current_level, sender_agent)

                    if not top_level and not nested_chats[current_nested_chat_id]["linked_to_parent_agent_node"]:
                        if nested_chats[current_nested_chat_id]["parent_agent_node_id"] != sender_agent.id:
                            # If the first agent in this nested/group chat is different to the previous agent then we need to create the agent inside and link to it
                            _add_node_agent(design_config, agents, current_level, sender_agent)
                            is_group_chat = nested_chats[current_nested_chat_id]["type"] == "Group Chat"
                            _add_agent_to_agent_edge(
                                design_config,
                                agents,
                                nested_graphs[nested_chats[current_nested_chat_id]["level_index"]], 
                                agents[nested_chats[current_nested_chat_id]["parent_agent_node_id"]], 
                                sender_agent, 
                                nested_chats[current_nested_chat_id]["edge_label"], 
                                dir="both" if is_group_chat else "forward",
                                style=design_config["edge_style" if not is_silent else "edge_style_silent"]
                            )
                        nested_chats[current_nested_chat_id]["linked_to_parent_agent_node"] = True
                    elif last_nested_agent is not None and last_nested_agent.id == sender_agent.id:
                        pass

                    _add_node_agent(design_config, agents, current_level, recipient_agent)

                    edge_text = event.event_name
                    tooltip_text = _create_tooltip(event.json_state["message"])
                    _add_agent_to_agent_edge(design_config, agents, current_level, sender_agent, recipient_agent, edge_text, tooltip_text, style=design_config["edge_style" if not is_silent else "edge_style_silent"])

                    current_agent = recipient_agent
                
                elif event.event_name == "reply_func_executed":
                    # Reply function executed, such as termination, generate oai reply, etc.

                    # We'll only consider the final ones for now
                    if event.json_state["final"]:
                        # Get the name of the function
                        reply_func_name = event.json_state["reply_func_name"]

                        # Specific function handling
                        if reply_func_name == "check_termination_and_human_reply":

                            if event.json_state['reply'] is None:
                                # No human reply or human chose to exit, so this is a termination.

                                # Add summary node
                                _add_node_terminate(design_config, current_level, event)

                                # Link it to the agent
                                _add_agent_to_event_edge(design_config, current_level, current_agent, event, reply_func_name)

                                last_termination = event
                            else:
                                # We have a human reply

                                # Add human node
                                _add_node_human(design_config, current_level, event)

                                # Link it to the agent
                                source_agent = agents[_agent_id_by_name(agents, event.source_name)]
                                _add_event_to_agent_return_edge(design_config, current_level, source_agent, event, reply_func_name, event.json_state['reply']['content'])

                                '''
                                # Add a human node (which we'll denote as a human)
                                if not _have_human_agent(agents):
                                    human_agent = _add_human_agent(agents)

                                    if not "index" in human_agent.visualization_params:
                                        human_agent.visualization_params["index"] = 0

                                    # Assign a colour to the agent
                                    if not human_agent.id in agent_colors:
                                        _assign_agent_color(agent_colors, human_agent.id)
                                        human_agent.visualization_params["color"] = agent_colors[human_agent.id]
                                else:
                                    human_agent = _get_human_agent(agents)

                                # Link to the human node
                                _add_agent_to_agent_edge(design_config, agents, current_level, current_agent, human_agent, reply_func_name, event.json_state['reply']['content'])

                                current_agent = human_agent
                                '''

                        elif reply_func_name == "_summary_from_nested_chats":

                            # Add recipient agent to diagram
                            # recipient_agent = agents[_agent_id_by_name(agents, event.source_name)]
                            # _add_node_agent(design_config, agents, current_level, recipient_agent)

                            # TO DO!
                            # _add_event_to_agent_edge(design_config, current_level, last_nested_summarize_level_and_event[1], recipient_agent, reply_func_name, event.json_state['reply'])

                            pass

                        elif reply_func_name == "generate_code_execution_reply": # Executed code
                            exitcode = _extract_code_exitcode(event.json_state['reply'])

                            if exitcode != -1:
                                # Add the exitcode node and result

                                executing_agent = agents[_agent_id_by_name(agents, event.source_name)]

                                _add_node_code_execution(design_config, current_level, event, exitcode, event.json_state['reply'])

                                # Link it to the agent
                                _add_code_execution_to_agent_return_edge(design_config, current_level, executing_agent, event, exitcode)

                        # If we have available invocations, add them to the agent in a return sequence
                        if len(available_invocations) > 0:
                            for invocation in available_invocations:
                                # Add them to the source agent
                                source_agent = agents[_agent_id_by_name(agents, event.source_name)]

                                _add_invocation_to_agent_return_edge(design_config, current_level, source_agent, invocation, reply_func_name, _extract_invocation_response(invocation))

                            # Once added, we clear the available invocations
                            available_invocations.clear()

                elif event.event_name and event.event_name.startswith("_prepare_and_select_agents:callable:"):
                    # Group Chat callable speaker selection

                    callable_name = event.event_name.split(":")[2]

                    source_agent = agents[_agent_id_by_name(agents, event.source_name)]

                    # Add function call node
                    _add_node_event_reply_func_executed(design_config, dot, event, callable_name, design_config["node_shape"]["code_execution"])

                    # Create the edge loop
                    _add_event_to_agent_return_edge(design_config, current_level, source_agent, event, event.json_state['next_agent'])

                elif event.event_name == "generate_tool_calls_reply" or event.event_name == "a_generate_tool_calls_reply":
                    # Tool calls will be like invocations - it will call the tool and loop back

                    # Add function call node
                    _add_node_event_reply_func_executed(design_config, dot, event, event.json_state["function_name"], design_config["node_shape"]["code_execution"])

                    # Create the edge loop
                    _add_event_to_agent_return_edge(design_config, current_level, current_agent, event, event.event_name, event.json_state['return_value'])

                elif event.event_name == "_reflection_with_llm_as_summary" or event.event_name == "_last_msg_as_summary":
                        
                    # Add summary node
                    _add_node_summary(design_config, current_level, event)

                    # Link it to the agent or termination (which ever is later)
                    summary = summary_text(event.json_state['summary'])
                    if last_termination is not None and last_termination.timestamp > current_agent.current_timestamp:
                        _add_event_to_event_edge(design_config, current_level, last_termination, event, event.event_name, summary)
                    else:
                        _add_agent_to_event_edge(design_config, current_level, current_agent, event, event.event_name, summary)

                    # If we have available invocations, add them to the agent in a return sequence
                    if len(available_invocations) > 0:
                        for invocation in available_invocations:
                            _add_invocation_to_event_return_edge(design_config, current_level, event, invocation, event.event_name, summary)

                        # Once added, we clear the available invocations
                        available_invocations.clear()

                    # If we're at the final stage of a group chat auto select speaker, show the name of the agent selected
                    if current_level.name is not None and current_nested_chat_id in nested_chats and nested_chats[current_nested_chat_id]["type"] == "Group Chat":
                        node_id = _add_node_info(design_config, current_level, _truncate_string(summary, 30))
                        _add_event_to_node_edge(design_config, current_level, event, node_id, "next speaker")

                    # Track last summarize event so we can connect it to the outside
                    # of the nested chat
                    last_nested_summarize_level_and_event = [current_level, event]

                elif event.event_name == "_initiate_chat max_turns":

                    # Maximum turns hit, add a termination node
                    _add_node_terminate(design_config, current_level, event)

                    # Link it to the agent
                    _add_agent_to_event_edge(design_config, current_level, current_agent, event, f"Max turns hit ({event.json_state['turns']})")

                    last_termination = event

                else:
                    pass

            elif isinstance(item, LogInvocation):
                invocation: LogInvocation = item

                # Add the invocation node
                _add_node_invocation(design_config, clients, wrapper_clients, dot, invocation)

                available_invocations.append(invocation)

            i += 1

        return i

    # Initialize the main diagram
    dot = Digraph(comment=diagram_name)
    dot.attr(bgcolor=design_config["canvas_replace_bg"])

    clients: Dict[int, LogClient] = {}
    agents: Dict[int, LogAgent] = {}
    events: Dict[float, LogEvent] = {}
    invocations: Dict[str, LogInvocation] = {}
    all_ordered: List[LogClient | LogAgent | LogEvent | LogInvocation | LogSession] = []

    # Keep track of wrapper_ids and client_ids, this can help us reconcile when a client_id doesn't exist we can use a previous client with the same wrapper
    wrapper_clients: Dict[int, List] = {}

    # Agent's colors
    agent_colors = {}

    # Nested graphs
    nested_chats: Dict[str, Dict] = {"0": {}}
    nested_graphs: Dict[uuid4, Digraph] = {}

    # Load log data
    load_log_file(log_file_path, clients, wrapper_clients, agents, events, invocations, all_ordered)

    # Start node
    _add_node_start(design_config, dot)

    # Process the entire diagram recursively
    process_level(True, dot, "0", all_ordered, 0, "0", None)

    # Render the diagram
    file_path = dot.render(directory=directory, filename=filename, format=format)

    if format=="svg":
        # post-visualisation, add background definition

        # new_content = '<pattern height="12" id="bg_pattern" patternUnits="userSpaceOnUse" width="15"><circle cx="5" cy="5" fill="' + design_config["canvas_pattern_color"] + '" r="3" /></pattern>'
        background_pattern = '<pattern height="40" width="40" id="bg_pattern" patternUnits="userSpaceOnUse"><rect x="0" y="0" width="40" height="40" fill="' + design_config["canvas_pattern_bg"] + '" /><circle cx="15" cy="15" r="14" stroke="' + design_config["canvas_pattern_color"] + '" stroke-width="1" fill="none" /><text x="7" y="19" font-family="Arial" font-size="12" fill="' + design_config["canvas_pattern_color"] + '">AG</text></pattern>'
        post_svg(design_config, directory, filename + ".svg", background_pattern)

def highlight_anchors(svg_string):
    """Bolds text within anchors and changes cursor to pointer - to indicate hover over"""
    def modify_anchor_and_text(match):
        a_tag = match.group(1)
        text_tag = match.group(2)
        closing_a = match.group(3)

        # Add cursor: pointer to the anchor tag if it's not already there
        if 'style' not in a_tag:
            a_tag = a_tag.replace('>', ' style="cursor: pointer;">', 1)
        elif 'cursor: pointer' not in a_tag:
            a_tag = a_tag.replace('style="', 'style="cursor: pointer; ', 1)

        # Add font-weight: bold to the text tag if it's not already there
        if 'font-weight' not in text_tag:
            text_tag = text_tag.replace('<text', '<text font-weight="bold"', 1)

        return a_tag + text_tag + closing_a
    
    pattern = r'(<a[^>]*>)([\s\S]*?<text[\s\S]*?</text>)([\s\S]*?</a>)'
    return re.sub(pattern, modify_anchor_and_text, svg_string)

def post_svg(design_config: Dict, directory: str, filename: str, background_pattern: str):
    """Post-processing the SVG, adding the background pattern"""

    # Read the original SVG content
    with open(f"{directory}/{filename}", 'r') as file:
        svg_content = file.read()
    
    # Check if <defs> tag exists, if not, insert it before the closing </svg> tag
    if '<defs>' not in svg_content:
        insert_position = svg_content.find('</svg>')
        if insert_position == -1:
            raise ValueError("Invalid SVG file: no closing </svg> tag found.")
        
        # Add <defs> section and new content
        defs_section = f'<defs>{background_pattern}</defs>\n'
        updated_svg = svg_content[:insert_position] + defs_section + svg_content[insert_position:]
    else:
        # If <defs> exists, insert the content inside it
        insert_position = svg_content.find('</defs>') + len('</defs>')
        updated_svg = svg_content[:insert_position] + background_pattern + svg_content[insert_position:]

    # Update the background fill
    updated_svg = updated_svg.replace(design_config["canvas_replace_bg"], "url(#bg_pattern)")

    # Bold text with anchors
    updated_svg = highlight_anchors(updated_svg)
    
    # Write the updated SVG content to a new file or overwrite the original
    output_file = directory + "/" + filename
    with open(output_file, 'w') as file:
        file.write(updated_svg)
