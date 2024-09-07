import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
from graphviz import Digraph

class LogSession:
    def __init__(self, session_id: str):
        self.session_id = session_id

class LogClient:
    def __init__(self, client_id: int, wrapper_id: int, session_id: str, class_name: str, json_state: str, timestamp: str, thread_id: int):
        self.client_id = client_id
        self.wrapper_id = wrapper_id
        self.session_id = session_id
        if class_name.endswith("Client"):
            self.class_name = class_name.replace("Client", "")
        else:
            self.class_name = class_name
        self.json_state = json_state
        self.timestamp = timestamp
        self.thread_id = thread_id

    def __str__(self):
        return f"Client ({self.client_id}) - {self.class_name}"

class LogAgent:
    def __init__(self, id: int, agent_name: str, wrapper_id: int, session_id: str, current_time: str, agent_type: str, args: Dict, thread_id: int):
        self.id = id
        self.agent_name = agent_name
        self.wrapper_id = wrapper_id
        self.session_id = session_id
        self.current_time = current_time
        self.agent_type = agent_type
        self.args = args
        self.thread_id = thread_id

        self.visualization_params = {} # For tracking colours and what index we're up to

    def __str__(self):
        return f"Agent ({self.id}) - {self.agent_name}"

class LogEvent:
    def __init__(self, source_id: int, source_name: str, event_name: str, agent_module: str, agent_class: str, json_state: str, timestamp: str, thread_id: int):
        self.source_id = source_id
        self.source_name = source_name
        self.event_name = event_name
        self.agent_module = agent_module
        self.agent_class = agent_class
        self.json_state = json.loads(json_state) if json_state else "{}"
        self.timestamp = timestamp
        self.thread_id = thread_id
        self.event_id = self.get_id_str()

        '''
        event_name == "received_message"
            # json_state
            # '{"message": "We\'re launching a new drink, it\'s flavoured like water and is called \'h2-oh\'.\\nKey facts are:\\n- No calories, sugar-free\\n- Can be enjoyed hot or cold\\n- No expiry date\\n- One ingredient, water\\n\\nTargeted to everyone.\\n\\nPlease prepare a brief with this structure:\\nA. Taglines:\\n\\nB. Short-form video summary:\\n\\nC. Alternative product names:\\n", "sender": "user_proxy", "valid": true}'
        
        event_name == "reply_func_executed"
            # json_state
            # '{"reply_func_module": "autogen.agentchat.conversable_agent", "reply_func_name": "check_termination_and_human_reply", "final": false, "reply": null}'
            # '{"reply_func_module": "autogen.agentchat.conversable_agent", "reply_func_name": "generate_function_call_reply", "final": false, "reply": null}'
            # '{"reply_func_module": "autogen.agentchat.conversable_agent", "reply_func_name": "generate_tool_calls_reply", "final": false, "reply": null}'
            # '{"reply_func_module": "autogen.agentchat.conversable_agent", "reply_func_name": "generate_oai_reply", "final": true, "reply": {"content": "Agency Red: \\n\\nHere\'s our pitch for the \'h2-oh\' campaign:\\n\\n**A. Taglines:**\\n1. \\"Pure, Simple, Refreshing\\"\\n2. \\"Water, Evolved.\\"\\n3. \\"The Drink that\'s Still Water.\\"\\n\\n**B. Short-form video summary:** \\n(60-second spot)\\n\\n[Scene 1: Close-up of a person taking a sip from a glass of \'h2-oh\']\\nNarrator (Voiceover): \\"We drink it every day, but never truly see it.\\"\\n[Scene 2: A splashy montage of people drinking \'h2-oh\' in different settings]\\nNarrator (Voiceover): \\"Introducing h2-oh, water that\'s still water.\\"\\n[Scene 3: Close-up of the \'h2-oh\' bottle with the label and tagline on screen]\\nNarrator (Voiceover): \\"No calories, no sugar, just pure refreshment.\\"\\n[Scene 4: People enjoying \'h2-oh\' hot and cold]\\nNarrator (Voiceover): \\"Enjoy it hot or cold, whenever you need it.\\"\\n[Scene 5: Close-up of the person taking a sip again with a satisfied expression]\\nNarrator (Voiceover): \\"Experience water, reimagined.\\"\\n\\n**C. Alternative product names:**\\n1. AquaFresh\\n2. Purezza\\n3. HydroFlow", "refusal": null, "role": "assistant", "function_call": null, "tool_calls": null}}'

        event_name == "_summary_from_nested_chat start"
            # json_state
            # '{"nested_chat_id": "7cadd935-2408-4a6b-90e1-06a8b25b1a82", "chat_queue": [{"recipient": "<<non-serializable: ConversableAgent>>", "message": "<<non-serializable: function>>", "summary_method": "last_msg", "max_turns": 1}], "sender": "agency_red"}'

        event_name == "_summary_from_nested_chat end"
            # json_state
            # '{"nested_chat_id": "7cadd935-2408-4a6b-90e1-06a8b25b1a82"}'
        '''

    def __str__(self):
        return f"Event ({self.timestamp}) - {self.source_name}, {self.event_name}, {self.agent_module}, {self.agent_class}"

    # Timestamp will be key, convert to a number
    def to_unix_timestamp(self) -> float:
        dt = datetime.fromisoformat(self.timestamp)
        return dt.timestamp()
    
    def get_id_str(self) -> str:
        id = str(self.to_unix_timestamp())
        return id
    
class LogInvocation:
    def __init__(self, invocation_id: str, client_id: int, wrapper_id: int, request: Dict, response: Any, is_cached: int, cost: float, start_time: str, end_time: str, thread_id: int, source_name: str):
        self.invocation_id = invocation_id
        self.client_id = client_id
        self.wrapper_id = wrapper_id
        self.request = request
        self.response = response
        self.is_cached = is_cached
        self.cost = cost
        self.start_time = start_time
        self.end_time = end_time
        self.thread_id = thread_id
        self.source_name = source_name

    def __str__(self):
        return f"Invocation ({self.invocation_id})"

def parse_log_line(line_data: Dict) -> Union[LogSession, LogClient, LogEvent, LogAgent, LogInvocation, None]:
    """Parses a line of log data and returns the corresponding object.

    Args:
        line_data (Dict): The log data as a dictionary.

    Returns:
        Union[LogSession, LogClient, LogEvent, LogAgent, LogInvocation, None]: The parsed object, or None if the line cannot be parsed.
    """

    # Check for session ID
    if "Session ID:" in line_data:
        session_id = line_data.split("Session ID: ")[-1].strip()
        return LogSession(session_id)

    # Check for client data
    if next(iter(line_data)) == "client_id" and "class" in line_data: # First key is client_id
        return LogClient(
            client_id=line_data.get("client_id"),
            wrapper_id=line_data.get("wrapper_id"),
            session_id=line_data.get("session_id"),
            class_name=line_data.get("class"),
            json_state=line_data.get("json_state"),
            timestamp=line_data.get("timestamp"),
            thread_id=line_data.get("thread_id"),
        )

    # Check for agent data
    if next(iter(line_data)) == "id" and "agent_name" in line_data:
        return LogAgent(
            id=line_data.get("id"),
            agent_name=line_data.get("agent_name"),
            wrapper_id=line_data.get("wrapper_id"),
            session_id=line_data.get("session_id"),
            current_time=line_data.get("current_time"),
            agent_type=line_data.get("agent_type"),
            args=line_data.get("args"),
            thread_id=line_data.get("thread_id"),
        )

    # Check for event data
    if next(iter(line_data)) == "source_id" and "source_name" in line_data:
        return LogEvent(
            source_id=line_data.get("source_id"),
            source_name=line_data.get("source_name"),
            event_name=line_data.get("event_name"),
            agent_module=line_data.get("agent_module"),
            agent_class=line_data.get("agent_class"),
            json_state=line_data.get("json_state"),
            timestamp=line_data.get("timestamp"),
            thread_id=line_data.get("thread_id"),
        )

    # Check for invocation data
    if "invocation_id" in line_data:
        return LogInvocation(
            invocation_id=line_data.get("invocation_id"),
            client_id=line_data.get("client_id"),
            wrapper_id=line_data.get("wrapper_id"),
            request=line_data.get("request"),
            response=line_data.get("response"),
            is_cached=line_data.get("is_cached"),
            cost=line_data.get("cost"),
            start_time=line_data.get("start_time"),
            end_time=line_data.get("end_time"),
            thread_id=line_data.get("thread_id"),
            source_name=line_data.get("source_name"),
        )

    return None

# Add Log_____ objects
def add_log_client(client: LogClient, log_clients: Dict[int, LogClient]) -> bool:
    if client.client_id not in log_clients:
        log_clients[client.client_id] = client
        print(f"Client {client.client_id} added - {client.class_name}.")
        return True
    else:
        print(f"Client {client.client_id} already exists. No duplicate added.")
        return False

def add_log_agent(agent: LogAgent, log_agents: Dict[int, LogAgent]) -> bool:
    if agent.id not in log_agents:
        log_agents[agent.id] = agent
        print(f"Agent {agent.id} added - {agent.agent_name} ({agent.agent_type}).")
        return True
    else:
        log_agents[agent.id] = agent
        print(f"Agent {agent.id} already exists. Updating.")
        return False

# Function to add a new LogEvent to the dictionary
def add_log_event(event: LogEvent, log_events: Dict[float, LogEvent]) -> bool:
    unix_timestamp = event.to_unix_timestamp()
    if unix_timestamp not in log_events:
        log_events[unix_timestamp] = event
        print(f"Event at {event.timestamp} added - {event.source_name}, {event.event_name}.")
        return True
    else:
        print(f"Event at {event.timestamp} already exists. No duplicate added.")
        return False

def add_log_invocation(invocation: LogInvocation, log_invocations: Dict[int, LogInvocation]) -> bool:
    if invocation.invocation_id not in log_invocations:
        log_invocations[invocation.invocation_id] = invocation
        print(f"Invocation {invocation.invocation_id} added.")
        return True
    else:
        print(f"Invocation {invocation.invocation_id} already exists. No duplicate added.")
        return False

def load_log_file(file_and_path: str, clients: Dict, agents: Dict, events: Dict, invocations: Dict, all_ordered: List) -> str:
    '''Loads an AutoGen log file into respective dictionaries and an ordered list, returning the session id'''

    # Read the log file
    with open(file_and_path, 'r') as file:
        log_lines = file.readlines()

    # Iterate over each line in the log
    for line_no, line in enumerate(log_lines):
        # Extract the session ID
        if line.startswith("Started new session with Session ID:"):
            session_id = line.split(':')[-1].strip()
        elif line.startswith("[file_logger]"):
            # Ignore file logging errors
            pass
        else:
            # Can it be converted to JSON
            try:
                line_data = json.loads(line)

                line_object = parse_log_line(line_data=line_data)

                new_object = False

                if isinstance(line_object, LogClient):
                    new_object = add_log_client(line_object, clients)
                elif isinstance(line_object, LogAgent):
                    new_object = add_log_agent(line_object, agents)
                elif isinstance(line_object, LogEvent):
                    new_object = add_log_event(line_object, events)
                elif isinstance(line_object, LogInvocation):
                    new_object = add_log_invocation(line_object, invocations)
                else:
                    print(f"Uh oh, unknown object for the line, type is {type(line_object)}")

                if new_object:
                    all_ordered.append(line_object)

            except json.JSONDecodeError as e:
                print("Note - can't decode line.")


def visualize_execution(diagram_name: str, directory: str, filename: str, format: str, all_ordered: List, clients: Dict, agents: Dict[int, LogAgent], events: Dict, invocations: Dict):
    '''Create the diagram of the program execution'''

    standard_fill_color = "#EEEEEE"
    standard_border_color = "#AAAAAA"

    def _assign_agent_color(agent_colors, agent_id) -> str:
        """Assigns a color to an agent in a deterministic order.

        Args:
            agent_colors: A dictionary mapping agent ids to their assigned colors.
            agent_name: The name of the agent to assign a color to.

        Returns:
            The color assigned to the agent.
        """
        available_colors = [
            '#FAF4D0', '#C0DFB7', '#EDB7AD', '#FBDBD5', '#E4EEE9', '#CDD5C6', 
            '#A9C9D4', '#E8C4C6', '#EBCFB9', '#FF0080', '#808080', '#ADD8E6',
            '#90EE90', '#FFFFE0'
        ]
        color_index = len(agent_colors) % len(available_colors)  # Cycle through colors
        color = available_colors[color_index]
        agent_colors[agent_id] = color
        return color
    
    def _darken_color(color, amount=0.1):
        """Darkens a color by a given amount.

        Args:
            color: The color to darken, as a hex string (e.g., '#FF0000').
            amount: The amount to darken (0.0 - 1.0). 0.0 is no change, 1.0 is maximum darkness.

        Returns:
            The darkened color as a hex string.
        """
        c = int(color[1:], 16)
        r = max(0, int((c >> 16) - (255 * amount)))  # Clamp to 0
        g = max(0, int(((c >> 8) & 0xFF) - (255 * amount))) # Clamp to 0
        b = max(0, int((c & 0xFF) - (255 * amount))) # Clamp to 0
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _agent_id_by_name(agent_name: str) -> int:
        """Retrieves an agent id by their name"""
        for agent in agents.values():
            if agent.agent_name == agent_name:
                return agent.id
            
        raise Exception(f"Unknown agent, name: {agent_name}")
    
    def _client_by_id(client_id: int) -> LogClient:
        """Retrieves a client by id"""
        if client_id in clients:
            return clients[client_id]
        else:
            raise Exception(f"Unknown client, id: {client_id}")
    
    def _get_agent_node_id(agent: LogAgent) -> str:
        """Gets the unique node id for an agent node"""
        return f"{agent.id}_{agent.visualization_params['index']}"
    
    def _add_node_agent(dot: Digraph, agent: LogAgent):
        """Add an agent node to the diagram"""

        # Increment the index of the agent
        agent.visualization_params["index"] = agent.visualization_params["index"] + 1

        # Create a unique node id
        node_id = _get_agent_node_id(agent)

        # Add the node to the diagram
        color = agent.visualization_params["color"]
        dot.node(node_id, agent.agent_name, shape='egg', color=_darken_color(color, 0.2), style='filled', fillcolor=color)

    def _add_node_event_reply_func_executed(dot: Digraph, event: LogEvent, event_name: str, shape_name: str):
        """Add an event node to the diagram"""

        dot.node(event.event_id, event_name, shape=shape_name, color=standard_border_color, style='filled', fillcolor=standard_fill_color)

    def _add_node_invocation(dot: Digraph, invocation: LogInvocation):
        """Add an invocation node to the diagram"""

        client_name = _client_by_id(invocation.client_id).class_name

        dot.node(invocation.invocation_id, client_name, shape='invhouse', color=standard_border_color, style='filled', fillcolor=standard_fill_color)

    def _add_agent_to_agent_edge(dot: Digraph, sender_agent: LogAgent, recipient_agent: LogAgent, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between nodes"""

        dot.edge(_get_agent_node_id(sender_agent), _get_agent_node_id(recipient_agent), label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance='5.0')

    def _add_agent_to_event_edge(dot: Digraph, agent: LogAgent, event: LogEvent, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between an agent and an event"""

        dot.edge(_get_agent_node_id(agent), event.event_id, label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance='5.0')

    def _add_invocation_to_agent_return_edge(dot: Digraph, agent: LogAgent, invocation: LogInvocation, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between agent and invocation and a return edge"""

        dot.edge(_get_agent_node_id(agent), invocation.invocation_id, label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance='5.0')
        dot.edge(invocation.invocation_id, _get_agent_node_id(agent))

    def _add_event_to_agent_return_edge(dot: Digraph, agent: LogAgent, event: LogEvent, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between agent and invocation and a return edge"""

        dot.edge(_get_agent_node_id(agent), event.event_id, label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance='5.0')
        dot.edge(event.event_id, _get_agent_node_id(agent))

    def _add_invocation_to_event_edge(dot: Digraph, event: LogEvent, invocation: LogInvocation, label: str):
        """Adds an edge between an event and an invocation"""
        
        dot.edge(event.event_id, invocation.invocation_id, label)

        
    # Create a Digraph object
    dot = Digraph(comment=diagram_name)

    # Current level of the diagram (supports nested diagrams)
    current_level: Digraph = dot
    current_level_index = 0 # K
    nested_graphs: Dict[str, Digraph] = {} # Nested graphs
    nested_parent_graphs: Dict[str, Digraph] = {} # Parent of a nested graph

    # Create agent-color dictionary
    agent_colors = {}

    # Current agent
    current_agent = None

    # Available invocation (invocations occur before the event that ran them, so we keep it and connect it to the following event)
    available_invocations = []

    # Run through all execution points in the log, in order of execution
    for i, item in enumerate(all_ordered):
        
        if isinstance(item, LogAgent):
            agent: LogAgent = agents[item.id]

            # Assign an number to the agent as we'll be repeating the agent throughout the diagram
            # Every new instance will have an incremented number
            if not "index" in agent.visualization_params:
                agent.visualization_params["index"] = 0

            # Assign a colour to the agent
            if not agent.id in agent_colors:
                _assign_agent_color(agent_colors, agent.id)
                agent.visualization_params["color"] = agent_colors[agent.id]

            #agent_color = agent_colors[agent.id]

            #dot.node(str(i), agent.agent_name, shape='egg', color=_darken_color(agent_color), style='filled', fillcolor=agent_color)

        elif isinstance(item, LogEvent):

            event: LogEvent = item

            if event.event_name == "received_message":
                # A message from one agent to another
                sender_agent = agents[_agent_id_by_name(event.json_state["sender"])]
                recipient_agent = agents[_agent_id_by_name(event.source_name)]

                # If we don't already have the sender agent on the diagram, add them in
                if current_agent is None:
                    _add_node_agent(current_level, sender_agent)

                # Add recipient agent to diagram
                _add_node_agent(current_level, recipient_agent)

                # Create edge between agents
                edge_text = event.event_name
                _add_agent_to_agent_edge(current_level, sender_agent, recipient_agent, edge_text)

                # We're now at the recipient agent
                current_agent = recipient_agent

            
            elif event.event_name == "reply_func_executed":
                # Reply function executed, such as termination, generate oai reply, etc.

                # We'll only consider the final ones for now
                if event.json_state["final"]:
                    # Get the name of the function
                    reply_func_name = event.json_state["reply_func_name"]

                    # Add it as a point node
                    # _add_node_event_reply_func_executed(dot, event, reply_func_name)

                    # Link it to the current agent
                    # _add_agent_to_event_edge(dot, current_agent, event, reply_func_name)

                    # If we have available invocations, add them to the agent in a return sequence
                    if len(available_invocations) > 0:
                        for invocation in available_invocations:
                            # _add_invocation_to_event_edge(dot, event, invocation, "!")

                            _add_invocation_to_agent_return_edge(current_level, current_agent, invocation, reply_func_name)

                        # Once added, we clear the available invocations
                        available_invocations.clear()

            elif event.event_name == "generate_tool_calls_reply":
                # Tool calls will be like invocations - it will call the tool and loop back

                # Add function call node
                _add_node_event_reply_func_executed(dot, event, event.json_state["function_name"], "cds")

                # Create the edge loop
                _add_event_to_agent_return_edge(current_level, current_agent, event, event.event_name)

            elif event.event_name == "_summary_from_nested_chat start":
                # Moving down into a nested chat
                current_level_index = current_level_index + 1
                new_nested = Digraph(name='cluster_' + str(current_level_index))  # Use 'cluster_' to treat it as a subgraph
                
                # Style the subgraph
                new_nested.attr(style='rounded, filled', color='#EEF7FF', fillcolor=_darken_color('#EEF7FF'), label="Nested Chat", labeljust="r", labelloc="b", penwidth="2", margin="30")

                # Track parent and current graphs
                nested_parent_graphs[current_level_index] = current_level
                nested_graphs[current_level_index] = new_nested

                # Move to the new level
                current_level = new_nested

            elif event.event_name == "_summary_from_nested_chat end":

                # Style the subgraph
                #current_level.attr(style='rounded, filled', color='#123456', fillcolor='#e6e6ff')

                # Moving up out of a nested chat, add the graph to the parent one
                nested_parent_graphs[current_level_index].subgraph(current_level)

                # Move back to the parent
                current_level = nested_parent_graphs[current_level_index]
            else:
                pass

        elif isinstance(item, LogInvocation):
            invocation: LogInvocation = item

            # Add the invocation node
            _add_node_invocation(dot, invocation)

            available_invocations.append(invocation)

            # Add the edge between agent and invocation
            # _add_agent_to_invocation(dot, current_agent, invocation)


    dot.render(directory=directory, filename=filename, format=format)


# Initialize variables to store the extracted information
clients = {}
agents = {}
events = {}
invocations = {}
all_ordered = []

# session_id = load_log_file('./autogen_logs/20240904_035445_runtime_nested_chat.log', clients, agents, events, invocations, all_ordered)
session_id = load_log_file('./autogen_logs/20240907_005404_runtime_function_call.log', clients, agents, events, invocations, all_ordered)

# Print the extracted information
print(f"\n\nSession ID: {session_id}")

for object in all_ordered:
    print(object)

visualize_execution('Visualize!', 'ms_graphviz/diagrams', 'diagram_function_call', 'svg', all_ordered, clients, agents, events, invocations)
