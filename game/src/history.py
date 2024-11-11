import json
import os

class HistoryLog:
    def __init__(self):
        pass

    def append(self, session, log):
        file_path = f"history-{session.ws_token}.json"
        new_log_entry = json.dumps(log, indent=4)
        print(new_log_entry)

        try:
            if not os.path.isfile(file_path):
                # If file doesn't exist, create a new JSON array with the log entry
                with open(file_path, "w") as json_file:
                    json_file.write("[\n" + new_log_entry + "\n]")
            else:
                with open(file_path, "r+") as json_file:
                    # Move cursor to end of file and search backwards for the last ']'
                    json_file.seek(0, os.SEEK_END)
                    pos = json_file.tell() - 1

                    while pos > 0:
                        json_file.seek(pos)
                        char = json_file.read(1)
                        if char == "]":
                            break
                        pos -= 1

                    # Move back one position to be before the ']'
                    json_file.seek(pos)

                    # Write the new log entry as a JSON object in the array format
                    json_file.write(",\n" + new_log_entry + "\n]")

        except Exception as e:
            print(f"Error writing to {file_path}: {e}")
