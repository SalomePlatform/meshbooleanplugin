import os
import subprocess
import sys
import argparse
from itertools import permutations
from PyQt5.QtWidgets import QApplication  # Import QApplication

sys.path.append(os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "plugins", "smesh", "meshbooleanplugin"))
sys.path.append(os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "plugins", "smesh"))

from mesh_boolean_dialog import *

# Initialize QApplication
app = QApplication(sys.argv)

result_dict = {}

ROOT_PATH = os.path.join(os.environ["SMESH_ROOT_DIR"], "share", "salome", "plugins", "smesh", "meshbooleanplugin", "tests")
SAMPLES_PATH = os.path.join(ROOT_PATH, 'samples')


DEFAULT_ENGINE = ['cgal', 'vtk']
DEFAULT_OPERATION = ['union']

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

def check_ok(test, test_number):

    print(f"\nTest #{test_number}: ")
    print(f"   Engine      : {test.engine}")
    print(f"   Operation   : {test.op}")
    print(f"   Tool Mesh   : {test.tool}")
    print(f"   Object Mesh : {test.obj}\n")

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

def main(engine_list, operation_list):
    tests = generate_tests()
    for i, test in enumerate(tests, start=1):
        if test.engine in engine_list and test.op in operation_list:
            check_ok(test, i)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mesh Boolean Tests')
    parser.add_argument('-t', nargs='+', help='Run tests in TUI')
    parser.add_argument('--engine', nargs='+', help='List of engines to test')
    parser.add_argument('--operation', nargs='+', help='List of operations to test')
    args = parser.parse_args()

    # Check if both engine and operation arguments are provided
    if args.engine is None:
        args.engine = DEFAULT_ENGINE
    if args.operation is None:
        args.operation = DEFAULT_OPERATION

    main(args.engine, args.operation)

