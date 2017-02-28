from imhotep.tools import Tool
import re


class Linter(Tool):
    response_format = re.compile(
        r'^(?P<filename>.*?):(?P<line>\d+):\d+: (?P<message>.*)$')

    blacklist = re.compile(r'should have comment')

    def process_line(self, dirname, line):
        match = self.response_format.search(line)

        if len(self.filenames) != 0:
            if match.group('filename') not in self.filenames:
                return
        filename, line, messages = match.groups()

        if re.blacklist.search(messages):
            return None

        return filename, line, messages

    def get_command(self, dirname, linter_configs=set()):
        return 'golint'

    def get_file_extensions(self):
        return ['.go']
