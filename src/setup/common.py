"""This is a set of commonly useful distutils enhancements,
designed to be 'execfile()'d in a 'setup.py' file.  Don't import it,
it's not a package!  It also doesn't get installed with the rest of
the package; it's only actually used while 'setup.py' is running."""

# Set up default parameters

if 'HAPPYDOC_OUTPUT_PATH' not in globals():
    HAPPYDOC_OUTPUT_PATH = 'docs/html/reference'

if 'HAPPYDOC_IGNORE' not in globals():
    HAPPYDOC_IGNORE = ['-i', 'tests']

if 'HAPPYDOC_TITLE' not in globals():
    HAPPYDOC_TITLE = PACKAGE_NAME + ' API Reference'


from setuptools import Command
from distutils.command.sdist import sdist as old_sdist






















class happy(Command):

    """Command to generate documentation using HappyDoc

        I should probably make this more general, and contribute it to either
        HappyDoc or the distutils, but this does the trick for PEAK for now...
    """

    description = "Generate docs using happydoc"

    user_options = []

    def initialize_options(self):
        self.happy_options = None
        self.doc_output_path = None


    def finalize_options(self):

        if self.doc_output_path is None:
            self.doc_output_path = HAPPYDOC_OUTPUT_PATH

        if self.happy_options is None:
            self.happy_options = [
                '-t', HAPPYDOC_TITLE, '-d', self.doc_output_path,
            ] + HAPPYDOC_IGNORE + [ '.' ]
            if not self.verbose: self.happy_options.insert(0,'-q')

    def run(self):
        from distutils.dir_util import remove_tree, mkpath
        from happydoclib import HappyDoc

        mkpath(self.doc_output_path, 0755, self.verbose, self.dry_run)
        remove_tree(self.doc_output_path, self.verbose, self.dry_run)

        if not self.dry_run:
            HappyDoc(self.happy_options).run()




class sdist(old_sdist):

    """Variant of 'sdist' that (re)builds the documentation first"""

    def run(self):
        # Build docs before source distribution
        try:
            import happydoclib
        except ImportError:
            pass
        else:
            self.run_command('happy')

        # Run the standard sdist command
        old_sdist.run(self)


SETUP_COMMANDS = {
    'sdist': sdist,
    'happy': happy,
    'sdist_nodoc': old_sdist,
}



















