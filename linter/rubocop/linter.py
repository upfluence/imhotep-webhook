from imhotep.tools import Tool
import re
import os


class Linter(Tool):
    response_format = re.compile(
        r'^(?P<filename>.*?):(?P<line>\d+):\d+: .: (?P<message>.*)$')

    def process_line(self, dirname, line):
        match = self.response_format.search(line)

        if not match:
            return None

        if len(self.filenames) != 0:
            if match.group('filename') not in self.filenames:
                return None
        filename, line, messages = match.groups()

        if re.search(r'(^|\/)db/', match.group('filename')):
            return None

        return filename, line, messages

    def get_command(self, dirname, linter_configs=set()):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        return 'rubocop --config {}/rubocop.yml --format clang'.format(
            dir_path)

    def get_file_extensions(self):
        return ['.rb', '.ru']
