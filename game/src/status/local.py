import json
import threading
from status.base import Base
from logger_setup import logger

class LocalStatus(Base):
    def __init__(self):
        self.timers = []  # To store active timers

    def stop(self):
        self._cancel_all_timers()
        pass

    def set(self, session, expressions, inventory):
        # Cancel any existing timers
        self._cancel_all_timers()

        if len(expressions)==0:
            expressions = [{"expression": "neutral","start_time": 0}]

        # Schedule each expression update based on start_time
        for expr in expressions:
            timer = threading.Timer(expr["start_time"]*3, self._update_expression, args=(expr["expression"], inventory))
            timer.start()
            self.timers.append(timer)  # Keep track of timers


    def _update_expression(self, expression, inventory):
        """Helper method to update the expression in the file."""
        data_to_write = {
            "header": "Current System Status",
            "expression": expression,
            "inventory": inventory
        }
        self._write_to_file(data_to_write)


    def _write_to_file(self, data):
        """Writes data to data.json and handles exceptions."""
        try:
            with open("data.json", "w") as json_file:
                json.dump(data, json_file, indent=4)
        except Exception as e:
            logger.error(f"Error writing to data.json: {e}")


    def _cancel_all_timers(self):
        """Cancels all active timers."""
        for timer in self.timers:
            timer.cancel()
        self.timers.clear()
