from rope.base.project import Project
from rope.refactor.rename import Rename
from rope.contrib import generate
project = Project('.')
pycore = project.pycore
package = pycore.find_module('sindice')
changes = Rename(project, package).get_changes('core')
project.do(changes)