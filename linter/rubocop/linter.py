from imhotep.tools import Tool
import re


class Linter(Tool):
    response_format = re.compile(
        r'^(?P<filename>.*?):(?P<line>\d+):\d+: .: (?P<message>.*)$')

    disable_cops = [
        'Metrics/BlockLength', 'Style/Documentation',
        'Style/MultilineBlockChain']

    def get_command(self, dirname, linter_configs=set()):
        return 'rubocop --except {} -f c'.format(','.join(self.disable_cops))

    def get_file_extensions(self):
        return ['.rb', '.ru']
