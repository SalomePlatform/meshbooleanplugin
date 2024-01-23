import os
import subprocess
import sys
from itertools import permutations

sys.path.append(os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "plugins", "smesh", "meshbooleanplugin"))
sys.path.append(os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "plugins", "smesh"))

from mesh_boolean_dialog import *


result_dict = {}

ROOT_PATH = os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "plugins", "smesh", "meshbooleanplugin", "tests")
SAMPLES_PATH = os.path.join(ROOT_PATH, 'samples')

OPERATOR_DICT = { 'union' : 0, 'intersection' : 1, 'difference' : 2 }
ENGINE_DICT = { 'cgal' : 0, 'igl' : 1, 'vtk' : 2, 'irmb' : 3, 'cork' : 4, 'mcut' : 5}
BOLD = '\033[1m'
RESET = '\033[0m'

class Test:
    def __init__(self, obj, tool, op, engine):
        self.obj = obj
        self.tool = tool
        self.op = op
        self.engine = engine
    def pretty_print(self):
        symbol = ''
        if self.op == 'union':
            symbol = '\u222A'
        elif self.op == 'intersection':
            symbol = '\u2229'
        else:
            symbol = '\u2216'
        with open('logs.txt', 'a') as file:
            file.write(f'{self.engine}: {BOLD}{self.obj}{RESET} {symbol} {BOLD}{self.tool}{RESET}\n')


def generate_tests(path=SAMPLES_PATH):
    """generate all test cases possible from a directory"""
    def perform_ls(path):
      """perform a simple ls of the path parameter, return a list of files"""
      with subprocess.Popen(["ls", path], stderr = subprocess.PIPE, stdout=subprocess.PIPE, text=True) as ls_process:
        output, _ = ls_process.communicate()
        return [os.path.join("samples", file) for file in output.splitlines()]
    lst = perform_ls(path)
    lst = list(permutations(lst, 2))
    res = []
    for op, _ in OPERATOR_DICT.items():
        for engine, _ in ENGINE_DICT.items():
            res += [Test(elt[0], elt[1], op, engine) for elt in lst]
    return res

def check_ok(test):
    dialog = MeshBooleanDialog()

    # Fake PBMeshFilePressed without Qt interface
    ###
    dialog.LE_MeshFile_L.setText(test.obj)
    dialog.meshIn_L=str(test.obj)
    dialog.isFile_L=True
    dialog.LE_MeshSmesh_L.setText("")
    dialog.__selectedMesh_L=None
    
    dialog.LE_MeshFile_R.setText(test.tool)
    dialog.meshIn_R=str(test.tool)
    dialog.isFile_R=True
    dialog.LE_MeshSmesh_R.setText("")
    dialog.__selectedMesh_R=None
    ###

    # Set all the parameter to be conform with the yaml
    ###
    dialog.COB_Operator.setCurrentIndex(OPERATOR_DICT[test.op])
    dialog.COB_Engine.setCurrentIndex(ENGINE_DICT[test.engine])

    # Compute Mesh
    ###
    res = dialog.PBOKPressed()
    ###

    if dialog.maFenetre is not None:
        dialog.maFenetre.theClose()

    # Close the dialog
    ###
    dialog.PBCancelPressed()
    ###

    test.pretty_print()
    with open('logs.txt', 'a') as file:
        file.write(f'    {res}\n')

    return res

def main():
    tests = generate_tests()
    for test in tests:
        check_ok(test)
   
main()
