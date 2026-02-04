
from lupa import LuaRuntime
from .base import BaseSandbox
import sys

class LuaSandbox(BaseSandbox):
    
    def __init__(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.env = self.lua.globals()
        
        # Capture the initial state of Lua globals (before setting user variables)
        self.initial_globals = set(self.env.keys())
  

    def set_var(self, name, value):
        try:
            if isinstance(value, bool):
                # Lua uses `true` and `false` for booleans
                lua_value = 'true' if value else 'false'
                self.lua.execute(f"{name} = {lua_value}")
            else:
                self.lua.execute(f"{name} = {value}")
        except Exception as e:
            print(f"ERROR: unable to set Lua value with '{name} = {value}': {e}")
            raise


    def get_var(self, name):
        """Gets a Lua variable."""
        return self.lua.globals()[name]

    def get_all_vars(self):
        # Get all current globals and filter out the initial (default) Lua globals
        current_globals = set(self.env.keys())
        user_defined_globals = current_globals - self.initial_globals
        # Create a dictionary of only user-defined variables
        return {key: self.env[key] for key in user_defined_globals}


    def eval(self, code):
        """Evaluates Lua code."""
        try :
            # empty condition == True
            if not code or len(code)==0:
                return True
            
            return self.lua.execute(code)
        except Exception as e:
            print(f"Unable to evaluate: '{code}': {e}")
            return False
