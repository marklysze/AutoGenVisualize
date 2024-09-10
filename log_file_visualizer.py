import json
from uuid import uuid4
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
        self.current_timestamp = datetime.fromisoformat(current_time).timestamp()
        self.agent_type = agent_type
        self.args = args
        self.thread_id = thread_id

        self.visualization_params = {} # For tracking colours and what index we're up to

    def __str__(self):
        return f"Agent ({self.id}) - {self.agent_name}"

class LogEvent:
    def __init__(self, source_id: int, source_name: str, event_name: str, agent_module: str, agent_class: str, json_state: str, timestamp: str, thread_id: int):
        self.event_id = self.get_id_str(timestamp)
        self.source_id = source_id
        self.source_name = source_name
        self.event_name = event_name
        self.agent_module = agent_module
        self.agent_class = agent_class
        self.json_state = json.loads(json_state) if json_state else "{}"
        self.timestamp = self.to_unix_timestamp(timestamp)
        self.thread_id = thread_id

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

        event_name == "generate_tool_calls_reply"
            # json_state
            # {"tool_call_id": "ollama_manual_func_1546", "function_name": "currency_calculator", "function_arguments": "{\"base_amount\": 123.45, \"base_currency\": \"EUR\", \"quote_currency\": \"USD\"}", "return_value": "135.80 USD", "sender": "chatbot"}
        '''

    def __str__(self):
        return f"Event ({self.timestamp}) - {self.source_name}, {self.event_name}, {self.agent_module}, {self.agent_class}"

    # Timestamp will be key, convert to a number
    def to_unix_timestamp(self, timestamp_str: str) -> float:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.timestamp()
    
    def get_id_str(self, timestamp_str: str) -> str:
        id = str(self.to_unix_timestamp(timestamp_str))
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
    if event.timestamp not in log_events:
        log_events[event.timestamp] = event
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

    standard_canvas_bg_color = "#222222"
    standard_nested_bg_color = "#08004F"
    standard_groupchat_bg_color= "#004F4F"
    standard_fill_color = "#EEEEEE"
    standard_border_color = "#AAAAAA"
    standard_font_color = "#FAFAFA"
    standard_node_font_color = "#222222"
    standard_edge_color = "#AAAAFF"
    standard_fontname="Helvetica, DejaVu Sans, Arial, sans-serif"
    standard_label_distance="5.0"
    standard_node_shape_agent="egg"
    standard_node_shape_summary="parallelogram"
    standard_node_shape_terminate="octagon"
    standard_node_shape_invocation="invhouse"
    standard_node_shape_info="note"

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
    
    def _client_by_id(client_id: int, wrapper_id: int) -> LogClient:
        """Retrieves a client by id. If it can't find it, look up a client based on the wrapper_id"""
        if client_id in clients:
            return clients[client_id]
        elif wrapper_id in wrapper_clients:
            return clients[wrapper_clients[wrapper_id][0]] # Return the first client in the wrapper
        else:
            raise Exception(f"Unknown client, id: {client_id}. Additionally, can't find other clients with wrapper_id: {wrapper_id}")
    
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
        dot.node(node_id, f"{agent.agent_name} ({agent.visualization_params['index']})", shape=standard_node_shape_agent, color=_darken_color(color, 0.2), style='filled', fillcolor=color, fontcolor=standard_node_font_color, fontname=standard_fontname)

    def _add_node_summary(dot: Digraph, event: LogEvent):
        """Add a summary node to the diagram"""
        
        dot.node(event.event_id, "Summarize", shape=standard_node_shape_summary, color=standard_border_color, style='filled', fillcolor=standard_fill_color, fontcolor=standard_node_font_color, fontname=standard_fontname)

    def _add_node_terminate(dot: Digraph, event: LogEvent):
        """Add a termination node to the diagram"""

        dot.node(event.event_id, "Termination", shape=standard_node_shape_terminate, color=standard_border_color, style='filled', fillcolor=standard_fill_color, fontcolor=standard_node_font_color, fontname=standard_fontname)

    def _add_node_event_reply_func_executed(dot: Digraph, event: LogEvent, event_name: str, shape_name: str):
        """Add an event node to the diagram"""

        dot.node(event.event_id, event_name, shape=shape_name, color=standard_border_color, style='filled', fillcolor=standard_fill_color, fontcolor=standard_node_font_color, fontname=standard_fontname)

    def _add_node_invocation(dot: Digraph, invocation: LogInvocation):
        """Add an invocation node to the diagram"""

        client_name = _client_by_id(invocation.client_id, invocation.wrapper_id).class_name

        dot.node(invocation.invocation_id, client_name, shape=standard_node_shape_invocation, color=standard_border_color, style='filled', fillcolor=standard_fill_color, fontcolor=standard_node_font_color, fontname=standard_fontname)

    def _add_node_info(dot: Digraph, event_name: str) -> str:
        """Add an info node to the diagram an returns the name of the node"""

        new_id = str(uuid4())

        dot.node(new_id, event_name, shape=standard_node_shape_info, color=standard_border_color, style='filled', fillcolor=standard_fill_color, fontcolor=standard_node_font_color, fontname=standard_fontname)

        return new_id

    def _add_agent_to_agent_edge(dot: Digraph, sender_agent: LogAgent, recipient_agent: LogAgent, edge_text: str, tooltip_text: str = "", href_text: str = "", dir: str = "forward"):
        """Adds an edge between nodes"""

        # Ensure the agent nodes exist (e.g. they aren't index 0)
        if sender_agent.visualization_params['index'] == 0:
            _add_node_agent(dot, sender_agent)

        if recipient_agent.visualization_params['index'] == 0:
            _add_node_agent(dot, recipient_agent)

        dot.edge(_get_agent_node_id(sender_agent), _get_agent_node_id(recipient_agent), label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, dir=dir, labeldistance=standard_label_distance, fontcolor=standard_font_color, color=standard_edge_color, fontname=standard_fontname)

    def _add_agent_to_event_edge(dot: Digraph, agent: LogAgent, event: LogEvent, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between an agent and an event"""

        dot.edge(_get_agent_node_id(agent), event.event_id, label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance=standard_label_distance, fontcolor=standard_font_color, color=standard_edge_color, fontname=standard_fontname)

    def _add_event_to_event_edge(dot: Digraph, event_one: LogEvent, event_two: LogEvent, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between two events"""

        dot.edge(event_one.event_id, event_two.event_id, label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance=standard_label_distance, fontcolor=standard_font_color, color=standard_edge_color, fontname=standard_fontname)

    def _add_event_to_node_edge(dot: Digraph, event: LogEvent, node_id: str, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between an event and a node"""

        dot.edge(event.event_id, node_id, label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance=standard_label_distance, fontcolor=standard_font_color, color=standard_edge_color, fontname=standard_fontname)

    def _add_event_to_agent_edge(dot: Digraph, event: LogEvent, agent: LogAgent, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between an event and an agent"""

        dot.edge(event.event_id, _get_agent_node_id(agent), label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance=standard_label_distance, fontcolor=standard_font_color, color=standard_edge_color, fontname=standard_fontname)

    def _add_invocation_to_agent_return_edge(dot: Digraph, agent: LogAgent, invocation: LogInvocation, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between agent and invocation and a return edge"""

        dot.edge(_get_agent_node_id(agent), invocation.invocation_id, label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance=standard_label_distance, fontcolor=standard_font_color, color=standard_edge_color, fontname=standard_fontname)
        dot.edge(invocation.invocation_id, _get_agent_node_id(agent), color=standard_edge_color)

    def _add_invocation_to_event_return_edge(dot: Digraph, event: LogEvent, invocation: LogInvocation, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between event and invocation and a return edge"""

        dot.edge(event.event_id, invocation.invocation_id, label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance=standard_label_distance, fontcolor=standard_font_color, color=standard_edge_color, fontname=standard_fontname)
        dot.edge(invocation.invocation_id, event.event_id, color=standard_edge_color)

    def _add_event_to_agent_return_edge(dot: Digraph, agent: LogAgent, event: LogEvent, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an edge between agent and invocation and a return edge"""

        dot.edge(_get_agent_node_id(agent), event.event_id, label=edge_text, labeltooltip=tooltip_text, labelhref=href_text, labeldistance=standard_label_distance, fontcolor=standard_font_color, color=standard_edge_color, fontname=standard_fontname)
        dot.edge(event.event_id, _get_agent_node_id(agent), color=standard_edge_color)

    def _add_invocation_to_event_edge(dot: Digraph, event: LogEvent, invocation: LogInvocation, label: str):
        """Adds an edge between an event and an invocation"""
        
        dot.edge(event.event_id, invocation.invocation_id, label, color=standard_edge_color)

    def _add_agent_info_loop_edge(dot: Digraph, agent: LogAgent, edge_text: str, tooltip_text: str = "", href_text: str = ""):
        """Adds an information-only loop edge to/from an agent"""

        dot.edge(_get_agent_node_id(agent), _get_agent_node_id(agent), label=edge_text, color=standard_edge_color)

    def create_nested_digraph(nested_chat_node_name: str, label: str, color: str) -> Digraph:
        """Creates a nested digraph"""
        
        nested_graph = Digraph(nested_chat_node_name)
        nested_graph.attr(style='rounded, filled', color=color, fillcolor=_darken_color(color), label=label, labeljust="r", labelloc="b", penwidth="2", margin="30", fontcolor=standard_font_color, fontname=standard_fontname)

        return nested_graph
        
    # Create a Digraph object
    dot = Digraph(comment=diagram_name)
    dot.attr(bgcolor=standard_canvas_bg_color)

    # Current level of the diagram (supports nested diagrams)
    current_level: Digraph = dot
    current_level_index = 0 # K
    nested_graphs: Dict[str, Digraph] = {} # Nested graphs
    nested_parent_graphs: Dict[str, Digraph] = {} # Parent of a nested graph
    nested_chats: Dict[str, Dict] = {
        "0": {}
    } # Nested chats, we include and represent the top level chat as 0
    nested_parents: Dict[str, str] = {} # Parent of a nested chat
    current_nested_chat_id = "0"

    # Create agent-color dictionary
    agent_colors = {}

    # Current agent
    current_agent: LogAgent = None

    # Current termination
    last_termination: LogEvent = None

    # Last nested chat summarise node
    last_nested_summarize_level_and_event: List[Digraph, LogEvent] = None

    # Available invocation (invocations occur before the event that ran them, so we keep it and connect it to the following event)
    available_invocations = []

    # Keep track of wrapper_ids and client_ids, this can help us reconcile when a client_id doesn't exist we can use a previous client with the same wrapper
    wrapper_clients: Dict[int, List] = {}

    # Summary nodes, no ids so 

    # Run through all execution points in the log, in order of execution
    for i, item in enumerate(all_ordered):

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

            #agent_color = agent_colors[agent.id]

            #dot.node(str(i), agent.agent_name, shape=standard_node_shape_agent, color=_darken_color(agent_color), style='filled', fillcolor=agent_color)

        elif isinstance(item, LogEvent):

            event: LogEvent = item

            if event.event_name == "received_message":

                # A message from one agent to another
                sender_agent = agents[_agent_id_by_name(event.json_state["sender"])]
                recipient_agent = agents[_agent_id_by_name(event.source_name)]

                # If we don't already have the sender agent on the diagram, add them in
                if current_agent is None:
                    _add_node_agent(current_level, sender_agent)

                # If we are in a nested chat and we haven't linked to the parent agent node, link it
                if current_nested_chat_id != "0" and not nested_chats[current_nested_chat_id]["linked_to_parent_agent_node"]:

                    # If the sender is not the parent of this nested chat, we need to create a link between the parent node and the new sender
                    if nested_chats[current_nested_chat_id]["parent_agent_node_id"] != sender_agent.id:

                        # Add the sender agent to the nested chat (as it's not the parent agent so we create a new agent node)
                        _add_node_agent(current_level, sender_agent)

                        # Then link the parent to this sender node
                        is_group_chat = nested_chats[current_nested_chat_id]["type"] == "Group Chat"
                        _add_agent_to_agent_edge(nested_parent_graphs[nested_chats[current_nested_chat_id]["level_index"]], agents[nested_chats[current_nested_chat_id]["parent_agent_node_id"]], sender_agent, nested_chats[current_nested_chat_id]["edge_label"], dir="both" if is_group_chat else "forward")

                    nested_chats[current_nested_chat_id]["linked_to_parent_agent_node"] = True

                # Add recipient agent to diagram
                _add_node_agent(current_level, recipient_agent)

                # Create edge between agents
                edge_text = event.event_name

                # Create tool tip with message
                if isinstance(event.json_state["message"], str):
                    tooltip_text = event.json_state["message"]
                else:
                    tooltip_text = event.json_state["message"]["content"]
                    if "tool_calls" in event.json_state["message"] and event.json_state["message"]["tool_calls"] is not None:
                        for tool_call in event.json_state["message"]["tool_calls"]:
                            if len(tooltip_text) > 0:
                                tooltip_text += "\n"
                            tooltip_text += f"Tool call: {json.dumps(tool_call['function'])}"

                _add_agent_to_agent_edge(current_level, sender_agent, recipient_agent, edge_text, tooltip_text)

                # We're now at the recipient agent
                current_agent = recipient_agent
            
            elif event.event_name == "reply_func_executed":
                # Reply function executed, such as termination, generate oai reply, etc.

                # We'll only consider the final ones for now
                if event.json_state["final"]:
                    # Get the name of the function
                    reply_func_name = event.json_state["reply_func_name"]

                    # Specific function handling
                    if reply_func_name == "check_termination_and_human_reply":

                        # Add summary node
                        _add_node_terminate(current_level, event)

                        # Link it to the agent
                        _add_agent_to_event_edge(current_level, current_agent, event, reply_func_name)

                        last_termination = event

                    if reply_func_name == "_summary_from_nested_chats":

                        # Add recipient agent to diagram
                        recipient_agent = agents[_agent_id_by_name(event.source_name)]
                        _add_node_agent(current_level, recipient_agent)

                        _add_event_to_agent_edge(current_level, last_nested_summarize_level_and_event[1], recipient_agent, reply_func_name, event.json_state['reply'])

                    # If we have available invocations, add them to the agent in a return sequence
                    if len(available_invocations) > 0:
                        for invocation in available_invocations:
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

                nested_chat_id = event.json_state['nested_chat_id']

                # Moving down into a nested chat
                current_level_index = current_level_index + 1
                nested_chat_node_name = 'cluster_' + str(current_level_index)
                new_nested = create_nested_digraph(nested_chat_node_name=nested_chat_node_name, label="Nested Chat", color=standard_nested_bg_color)
                # new_nested = Digraph(nested_chat_node_name)  # Use 'cluster_' to treat it as a subgraph
                
                # Style the subgraph
                # new_nested.attr(style='rounded, filled', color=standard_nested_bg_color, fillcolor=_darken_color(standard_nested_bg_color), label="Nested Chat", labeljust="r", labelloc="b", penwidth="2", margin="30", fontcolor=standard_font_color, fontname=standard_fontname)

                # Track parent and current graphs
                nested_parent_graphs[current_level_index] = current_level
                nested_graphs[current_level_index] = new_nested

                # Keep track of this nested chat by id
                # and the parent node
                nested_chats[nested_chat_id] = {
                    "type": "Nested Chat",
                    "edge_label": "Nested Chat", # nested or group chat
                    "level_index": current_level_index,
                    "parent_agent_node_id": _agent_id_by_name(event.source_name),
                    "nested_chat_node_name": nested_chat_node_name,
                    "linked_to_parent_agent_node": False # Whether wwe have linked to the parent agent node
                    }

                # Move to the new level
                current_level = new_nested
                
                nested_parents[nested_chat_id] = current_nested_chat_id
                current_nested_chat_id = nested_chat_id

            elif event.event_name == "_summary_from_nested_chat end":

                # Style the subgraph
                #current_level.attr(style='rounded, filled', color='#123456', fillcolor='#e6e6ff')

                # Moving up out of a nested chat, add the graph to the parent one
                nested_parent_graphs[current_level_index].subgraph(current_level)

                # Move back to the parent
                current_level = nested_parent_graphs[current_level_index]

            elif event.event_name == "_auto_select_speaker start":

                # MS TEMP - TRY TO USE SAME AS NESTED CHAT CODE
                nested_chat_id = event.json_state['auto_select_speaker_id']

                # Moving down into a nested chat
                current_level_index = current_level_index + 1
                nested_chat_node_name = 'cluster_' + str(current_level_index)
                new_nested = create_nested_digraph(nested_chat_node_name=nested_chat_node_name, label="Group Chat Auto Select Speaker", color=standard_groupchat_bg_color)

                # Track parent and current graphs
                nested_parent_graphs[current_level_index] = current_level
                nested_graphs[current_level_index] = new_nested

                # Keep track of this nested chat by id
                # and the parent node
                nested_chats[nested_chat_id] = {
                    "type": "Group Chat",
                    "edge_label": "Auto Select Speaker", # nested or group chat
                    "level_index": current_level_index,
                    "parent_agent_node_id": _agent_id_by_name(event.source_name),
                    "nested_chat_node_name": nested_chat_node_name,
                    "linked_to_parent_agent_node": False # Whether wwe have linked to the parent agent node
                    }

                # Move to the new level
                current_level = new_nested
                
                nested_parents[nested_chat_id] = current_nested_chat_id
                current_nested_chat_id = nested_chat_id
                
            elif event.event_name == "_auto_select_speaker end":

                # Moving up out of a nested chat, add the graph to the parent one
                nested_parent_graphs[current_level_index].subgraph(current_level)

                # Move back to the parent
                current_level = nested_parent_graphs[current_level_index]

            elif event.event_name == "_reflection_with_llm_as_summary" or event.event_name == "_last_msg_as_summary":
                    
                # Add summary node
                _add_node_summary(current_level, event)

                # Link it to the agent or termination (which ever is later)
                if last_termination is not None and last_termination.timestamp > current_agent.current_timestamp:
                    _add_event_to_event_edge(current_level, last_termination, event, event.event_name, event.json_state['summary'])
                else:
                    _add_agent_to_event_edge(current_level, current_agent, event, event.event_name, event.json_state['summary'])

                # If we have available invocations, add them to the agent in a return sequence
                if len(available_invocations) > 0:
                    for invocation in available_invocations:
                        _add_invocation_to_event_return_edge(current_level, event, invocation, event.event_name)

                    # Once added, we clear the available invocations
                    available_invocations.clear()

                # If we're at the final stage of a group chat auto select speaker, show the name of the agent selected
                if current_level.name is not None and current_nested_chat_id in nested_chats and nested_chats[current_nested_chat_id]["type"] == "Group Chat":
                    node_id = _add_node_info(current_level, event.json_state['summary'])
                    _add_event_to_node_edge(current_level, event, node_id, "next speaker")

                # Track last summarize event so we can connect it to the outside
                # of the nested chat
                last_nested_summarize_level_and_event = [current_level, event]

            elif event.event_name == "_initiate_chat max_turns":

                # Maximum turns hit, add a termination node
                _add_node_terminate(current_level, event)

                # Link it to the agent
                _add_agent_to_event_edge(current_level, current_agent, event, f"Max turns hit ({event.json_state['turns']})")

                last_termination = event

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


# Print the extracted information
#print(f"\n\nSession ID: {session_id}")

for object in all_ordered:
    print(object)

# session_id = load_log_file('./autogen_logs/20240904_035445_runtime_nested_chat.log', clients, agents, events, invocations, all_ordered)

# session_id = load_log_file('./autogen_logs/20240908_040602_runtime_function_call.log', clients, agents, events, invocations, all_ordered)
# visualize_execution('Visualize!', 'ms_graphviz/diagrams', 'diagram_function_call', 'svg', all_ordered, clients, agents, events, invocations)

# session_id = load_log_file('./autogen_logs/20240908_050458_runtime_dual_function_call.log', clients, agents, events, invocations, all_ordered)
# visualize_execution('Visualize!', 'ms_graphviz/diagrams', 'diagram_dual_function_call', 'svg', all_ordered, clients, agents, events, invocations)

# session_id = load_log_file('./autogen_logs/20240908_042901_runtime_terminate.log', clients, agents, events, invocations, all_ordered)
# visualize_execution('Visualize!', 'ms_graphviz/diagrams', 'diagram_terminate', 'svg', all_ordered, clients, agents, events, invocations)

# session_id = load_log_file('./autogen_logs/20240908_051130_runtime_max_turns.log', clients, agents, events, invocations, all_ordered)
# visualize_execution('Visualize!', 'ms_graphviz/diagrams', 'diagram_max_turns', 'svg', all_ordered, clients, agents, events, invocations)

# session_id = load_log_file('./autogen_logs/20240908_185246_runtime_chess.log', clients, agents, events, invocations, all_ordered)
# visualize_execution('Visualize!', 'ms_graphviz/diagrams', 'diagram_chess', 'svg', all_ordered, clients, agents, events, invocations)

# session_id = load_log_file('./autogen_logs/20240909_091217_runtime_groupchat_debate-SHORT.log', clients, agents, events, invocations, all_ordered)
# visualize_execution('Visualize!', 'ms_graphviz/diagrams', 'diagram_groupchat_debate', 'svg', all_ordered, clients, agents, events, invocations)

# session_id = load_log_file('./autogen_logs/20240909_225202_runtime_dlcourse.log', clients, agents, events, invocations, all_ordered)
# visualize_execution('Visualize!', 'ms_graphviz/diagrams', 'diagram_dlcourse', 'svg', all_ordered, clients, agents, events, invocations)

session_id = load_log_file('./autogen_logs/20240909_234743_notebook_research_multiagent_groupchat.log', clients, agents, events, invocations, all_ordered)
visualize_execution('Visualize!', 'ms_graphviz/diagrams', 'diagram_notebook_research_multiagent_groupchat', 'svg', all_ordered, clients, agents, events, invocations)
