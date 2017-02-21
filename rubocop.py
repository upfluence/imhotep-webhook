from imhotep.tools import Tool
from collections import defaultdict
import json
import os
import re


class RubyLintLinter(Tool):
    DISABLED_COPS = [
        'Metrics/BlockLength', 'Style/Documentation',
        'Style/MultilineBlockChain']

    def get_configs(self):
        return {'.rubocop.yml', 'rubocop.yml'}

    def invoke(self, dirname, filenames=set(), linter_configs=set()):
        retval = defaultdict(lambda: defaultdict(list))
        config = ''
        for config_file in linter_configs:
            if 'rubocop' in config_file:
                config = "-c %s " % config_file
        if len(filenames) == 0:
            cmd = "find %s -name '*.rb' | xargs rubocop --except %s %s -f j" % (
                dirname, ','.join(self.DISABLED_COPS), config)
        else:
            ruby_files = []
            for f in filenames:
                if re.search('\.rb', f) and not re.search('^db\/', f):
                    ruby_files.append("%s/%s" % (dirname, f))

            cmd = "rubocop %s --except %s  -f j %s" % (
                config, ','.join(self.DISABLED_COPS), ' '.join(ruby_files))
        try:
            output = json.loads(self.executor(cmd))
            for linted_file in output['files']:
                print linted_file
                # The path should be relative to the repo,
                # without a leading slash
                # example db/file.rb
                file_name = os.path.abspath(linted_file['path'])
                file_name = file_name.replace(dirname, "")[1:]
                for offence in linted_file['offenses']:
                    line_number = str(offence['location']['line'])
                    retval[str(file_name)][line_number].append(
                        str(offence['message']))
                    retval[str(file_name)][line_number] = list(set(retval[str(file_name)][line_number]))
        except Exception as e:
            print str(e)

        return retval
