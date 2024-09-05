import json
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime

class LogSession:
    def __init__(self, session_id: str):
        self.session_id = session_id

class LogClient:
    def __init__(self, client_id: int, wrapper_id: int, session_id: str, class_name: str, json_state: str, timestamp: str, thread_id: int):
        self.client_id = client_id
        self.wrapper_id = wrapper_id
        self.session_id = session_id
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

    def __str__(self):
        return f"Agent ({self.id}) - {self.agent_name}"

class LogEvent:
    def __init__(self, source_id: int, source_name: str, event_name: str, agent_module: str, agent_class: str, json_state: str, timestamp: str, thread_id: int):
        self.source_id = source_id
        self.source_name = source_name
        self.event_name = event_name
        self.agent_module = agent_module
        self.agent_class = agent_class
        self.json_state = json_state
        self.timestamp = timestamp
        self.thread_id = thread_id

    def __str__(self):
        return f"Event ({self.timestamp}) - {self.source_name}, {self.event_name}, {self.agent_module}, {self.agent_class}"

    # Timestamp will be key, convert to a number
    def to_unix_timestamp(self) -> float:
        dt = datetime.fromisoformat(self.timestamp)
        return dt.timestamp()
    
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

# Read the log file
with open('./autogen_logs/20240904_035445_runtime_nested_chat.log', 'r') as file:
    log_lines = file.readlines()

# Initialize variables to store the extracted information
session_id = None
clients = {}
agents = {}
events = {}
invocations = {}
all_ordered = []

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

# Print the extracted information
print(f"\n\nSession ID: {session_id}")

for object in all_ordered:
    print(object)
