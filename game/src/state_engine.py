import yaml
import os
import traceback

from jinja2 import Template

from transitions.extensions import HierarchicalGraphMachine
from scripting.lua import LuaSandbox


class StateEngine:
    def __init__(self, yaml_file_path):
        # convert relative to absolute file path
        if not os.path.isabs(yaml_file_path):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            yaml_file_path = os.path.join(current_dir, yaml_file_path)

        self.yaml_file_path = yaml_file_path
        self.calculator = LuaSandbox()
        self.model = None
        self._load()


    def _load(self):
        # Store the current state if the model already exists
        current_state = self.model.state if self.model and hasattr(self.model, 'state') else None
        #print(f"Current state before reload: {current_state}")

        # Read the YAML file and set up the machine
        with open(self.yaml_file_path, 'r') as f:
            self.fsm_config = yaml.safe_load(f)  # Use yaml.safe_load to parse the YAML file

        # Update the inventory and reuse already existing values or set if it is a new one
        inventory = self.fsm_config['metadata'].get('inventory', {})
        for item, value in inventory.items():
            # Do not override a var if it already exists in the sandbox. 
            # We need the old state during hot reload
            if self.calculator.get_var(item) == None:
                self.calculator.set_var(item, value)
                print(f"Set {item} = {value} in Lua sandbox")
            else:
                print(f"Reuse {item} = {self.calculator.get_var(item)} from Lua sandbox")

        self.model_metadata = self.fsm_config.get("metadata", {})
        self.action_metadata = {}
        self.state_metadata = {}
        self.last_transition_error = ""

        clean_states = self._prepare_states(self.fsm_config['states'])
        clean_transitions = self._prepare_transitions(self.fsm_config['transitions'])
            
        # Create the state machine
        self.model = type('Model', (object,), {})()
        self.machine = HierarchicalGraphMachine(
            model=self.model, 
            states=clean_states, 
            transitions=clean_transitions, 
            initial=self.fsm_config['initial'], 
            ignore_invalid_triggers=True
        )

        # Attempt to restore the previous state if it exists in the new state list
        if current_state and current_state in [state['name'] for state in clean_states]:
            #print(f"Restoring previous state: {current_state}")
            self.machine.set_state(current_state)
        else:
            print("Previous state not found in new configuration, using initial state.")
            

    def _prepare_states(self, states):
        default_metadata = {
            "description": "Default metadata",
            "system_prompt": ""
        }

        metadata_freed_states = []
        for state in states:
            metadata = state.get('metadata', default_metadata)
            self.state_metadata[state['name']] = metadata
            # Remove metadata from the state dictionary before passing it to the "transistions" state machine
            state = {key: value for key, value in state.items() if key != 'metadata'}
            metadata_freed_states.append(state)
        return metadata_freed_states


    def _prepare_transitions(self, transitions):
        default_metadata = {
            "description": "Default metadata",
            "system_prompt": ""
        }

        metadata_freed_transitions = []
        for transition in transitions:
            metadata = transition.get('metadata', default_metadata)
            self.action_metadata[transition['trigger']] = metadata
            transition = {key: value for key, value in transition.items() if key != 'metadata'}
             
            transition['after'] = self._create_transition_callback(transition['trigger'])
            transition['conditions'] = [self._create_condition_callback(transition['trigger'])]

            metadata_freed_transitions.append(transition)
        
        return metadata_freed_transitions


    def _create_transition_callback(self, action):
        """
        This creates a callback function that is triggered after a specific transition.
        """
        def callback( *args, **kwargs):
            current_state = self.model.state
            metadata_state = self.state_metadata.get(current_state, {})
            metadata_action = self.action_metadata.get(action, {})
            
            # Execute actions in the LuaSandbox
            # Update states, calculate points, coins,....
            #
            actions = metadata_action.get('actions', [])
            for code in actions:
                if len(code)>0:
                    self.calculator.eval(code)

            if self.session.last_action != action:
                self.session.llm.system(self.get_action_system_prompt(action))
                value = metadata_action.get("sound_effect")
                volume = int(metadata_state.get("sound_effect_volume", "100") or 100)
                if value and value.strip():
                    self.session.jukebox.play_sound(self.session, value, volume, False)

            if self.session.last_state != current_state:
                self.session.llm.system(self.get_state_system_prompt(current_state))
                self.session.jukebox.stop_ambient(self.session)
                value = metadata_state.get("ambient_sound")
                volume = int(metadata_state.get("ambient_sound_volume", "100") or 100)
                if value and value.strip():
                    self.session.jukebox.play_sound(self.session, value, volume)

            self.session.last_action = action
            self.session.last_state = current_state
        
        return callback


    def _create_condition_callback(self, action):
        """
        This creates a condition function that always returns True but can log or handle
        the action in future use cases.
        """
        def condition_callback(*args, **kwargs):
            metadata_action = self.action_metadata.get(action, {})
            conditions = metadata_action.get("conditions", [])

            # Evaluate all conditions using the Lua sandbox (calculator)
            for condition in conditions:
                if len(condition)>0:
                    result = self.calculator.eval(f'return ({condition})')
                    if not result:  # If any condition fails, return False
                        self.last_transition_error = f"Condition '{condition}' failed for '{action}'"
                        print(self.last_transition_error)
                        print(self.calculator.get_all_vars())
                        return False

            # All conditions passed, allow the transition
            return True

        return condition_callback
    

    def get_all_vars(self):
        return { "state":self.get_state(),  **self.calculator.get_all_vars()}
    
    
    def get_var(self, name):
        return self.calculator.get_var(name)
    

    def trigger(self, session, action_id):
        try:
            self.session = session
            return self.model.trigger(action_id)
        except Exception as e:
            traceback.print_exc()
            print(f"Error triggering event '{action_id}': {e}")
            return False
        finally:
            self.session = None


    def get_action_metadata(self, action_id):
        return self.action_metadata.get(action_id, {})


    def get_global_system_prompt(self):
        # determine the current state_node type to know which system_prompt we can return.
        # Right now we have three differnt types:
        # - start
        # - normal
        # - end
        # We can then have three different settings and agent behaviour based on the current node type.
        # Maybe we want to switch the mood or the character at all...averything is possible.
        #
        state = self.get_state()
        state_meta = self.state_metadata[state]
        state_type = state_meta.get("state_type", "normal")

        prompt = self.fsm_config["metadata"][f"{state_type}_prompt"]
        template = Template(prompt)
        return template.render(self.get_all_vars())



    def get_state_system_prompt(self):
        prompt = self.state_metadata[self.get_state()]["system_prompt"]
        template = Template(prompt)
        return template.render(self.get_all_vars())
    

    def get_action_system_prompt(self, action_id):
        prompt = self.action_metadata[action_id]["system_prompt"]
        template = Template(prompt)
        return template.render(self.get_all_vars())


    def get_action_description(self, action_id):
        desc = self.action_metadata[action_id].get("description", "")
        template = Template(desc)
        return template.render(self.get_all_vars())


    def get_action_name(self, action_id):
        #print(self.action_metadata[action])
        return self.action_metadata[action_id].get("name", "")

    
    def get_state(self):
        return self.model.state
    

    def get_action_id(self, action_name):
        current_state = self.model.state
        # Go through machine's events and match transitions that are valid for the current state
        for event_id, event in self.machine.events.items():
            # Filter out the "to_XYZ" transitions and match the valid ones
            if not event_id.startswith("to_"):
                for transition in event.transitions[self.model.state]:
                    # check if the current state matches with the transistion source
                    metadata =  self.action_metadata[event_id]
                    if transition.source == current_state and metadata["name"]==action_name:
                        return event_id

        print(f"Action name not found: {action_name}")
        return None 
    

    def get_possible_action_ids(self):
        current_state = self.model.state
        available_actions = []

        def is_triggerable(event_id):
            metadata_action = self.action_metadata.get(event_id, {})
            conditions = metadata_action.get("conditions", [])
            for condition in conditions:
                if len(condition)>0:
                    result = self.calculator.eval(f'return ({condition})')
                    if not result:
                        return False
            return True 

        # Go through machine's events and match transitions that are valid for the current state
        for event_id, event in self.machine.events.items():
            # Filter out the "to_XYZ" transitions and match the valid ones
            if not event_id.startswith("to_"):
                for transition in event.transitions[self.model.state]:
                    # check if the current state matches with the transistion source
                    if transition.source == current_state and is_triggerable(event_id):
                        available_actions.append(event_id)
        
        return available_actions


    def get_possible_action_names(self):
        return [  self.get_action_name(action)  for action in self.get_possible_action_ids() ]

