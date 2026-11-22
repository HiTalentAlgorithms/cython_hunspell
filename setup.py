import os
import sys
import platform
from warnings import warn
from setuptools import setup, Extension
from setuptools.command.build import build
from setuptools.command.build_ext import build_ext
from Cython.Build import cythonize
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# The isolated setuptools backend executes setup.py without adding its directory.
sys.path.insert(0, BASE_DIR)
from build_hunspell import pkgconfig, repair_darwin_link_dep_path
BUILD_ARGS = defaultdict(lambda: ['-O3', '-g0'])
for compiler, args in [
        ('msvc', ['/EHsc', '/MD', '/DHUNSPELL_STATIC']),
        ('gcc', ['-O3', '-g0', '-DHUNSPELL_STATIC'])]:
    BUILD_ARGS[compiler] = args

def cleanup_pycs():
    file_tree = os.walk(os.path.join(BASE_DIR, 'hunspell'))
    to_delete = []
    for root, directory, file_list in file_tree:
        if len(file_list):
            for file_name in file_list:
                if file_name.endswith(".pyc"):
                    to_delete.append(os.path.join(root, file_name))
    for file_path in to_delete:
        try:
            os.remove(file_path)
        except:
            pass

profiling = '--profile' in sys.argv or '-p' in sys.argv
linetrace = '--linetrace' in sys.argv or '-l' in sys.argv
force_rebuild = '--force' in sys.argv or '-f' in sys.argv

if (profiling or linetrace) and not force_rebuild:
    warn("WARNING: profiling or linetracing specified without forced rebuild")

ext_modules = cythonize(
    [Extension(
        'hunspell.hunspell',
        [os.path.join('hunspell', 'hunspell.pyx')],
        **pkgconfig()
    )],
    build_dir=os.path.join('build', 'cython'),
    force=force_rebuild,
    compiler_directives={'language_level': 3},
)

class build_ext_compiler_check(build_ext):
    def build_extensions(self):
        compiler = self.compiler.compiler_type
        args = BUILD_ARGS[compiler]
        for ext in self.extensions:
            ext.extra_compile_args = args
        build_ext.build_extensions(self)

    def run(self):
        cleanup_pycs()
        build_ext.run(self)

class build_darwin_fix(build):
    def run(self):
        build.run(self)
        # OSX build a shared dependency with an absolute path to the hunspell dylib. This fixes that
        if platform.system() == 'Darwin':
            repair_darwin_link_dep_path()

setup(
    ext_modules=ext_modules,
    cmdclass={'build_ext': build_ext_compiler_check, 'build': build_darwin_fix},
)
