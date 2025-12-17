#  -*- coding: iso-8859-1 -*-
# Copyright (C) 2018-2025  CEA, EDF, OPEN CASCADE
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

import unittest
import os
from meshbooleanplugin import mesh_boolean_api

class TestMesh(unittest.TestCase):

  test_counter = 0
  def setUp(self):
    # stuff done before launching test: create input meshes
    from salome.kernel import salome
    salome.salome_init()
    from salome.geom import geomBuilder
    from salome.smesh import smeshBuilder

    geompy = geomBuilder.New()

    O = geompy.MakeVertex(0, 0, 0)
    OX = geompy.MakeVectorDXDYDZ(1, 0, 0)
    OY = geompy.MakeVectorDXDYDZ(0, 1, 0)
    OZ = geompy.MakeVectorDXDYDZ(0, 0, 1)
    box = geompy.MakeBoxDXDYDZ(1, 1, 1)
    geompy.addToStudy( O, 'O' )
    geompy.addToStudy( OX, 'OX' )
    geompy.addToStudy( OY, 'OY' )
    geompy.addToStudy( OZ, 'OZ' )
    geompy.addToStudy( box, 'box' )

    smesh = smeshBuilder.New()
    #smesh.SetEnablePublish( False )
    # Set to False to avoid publish in study if not needed or in some particular situations:
    # multiples meshes built in parallel, complex and numerous mesh edition (performance)

    box_mesh = smesh.Mesh(box,'box_mesh')
    algo1D = box_mesh.Segment()
    LocalLength = algo1D.LocalLength(0.25,None,1e-07)
    algo2D = box_mesh.Quadrangle(algo=smeshBuilder.QUADRANGLE)
    algo3D = box_mesh.Hexahedron(algo=smeshBuilder.Hexa)
    isDone = box_mesh.Compute()
    box_mesh.CheckCompute()

    box_mesh_translated = box_mesh.TranslateObjectMakeMesh( box_mesh, [ 0.125, 0.125, 0.125 ],
                                                                        0, 'box_mesh_translated')

    self.mesh_1 = box_mesh
    self.mesh_2 = box_mesh_translated

    #Automatically detect the presence of the algorithms in the environment
    #if detected => add to algos
    algo_def = {
      'CGAL' : (mesh_boolean_api.CGAL, "CGAL_ROOT_DIR"),
      'MCUT' : (mesh_boolean_api.MCUT, "MCUT_ROOT_DIR"),
      'VTK' : (mesh_boolean_api.VTK, "VTK_ROOT_DIR"),
      'IGL' : (mesh_boolean_api.IGL, "LIBIGL_ROOT_DIR"),
      'CORK' : (mesh_boolean_api.CORK, "CORK_ROOT_DIR"),
      'IRMB' : (mesh_boolean_api.IRMB, "IRMB_ROOT_DIR")
    }
    self.algos = {}
    for name, (algo , env_var) in algo_def.items():
      if os.getenv(env_var):
        self.algos[name] = algo

  #Functions to get the expected area of a mesh so we can compare it with the results of our algorithms
  #put it in fonctions to change it after
  def computeExpectedDifference(self):
    return 6

  def computeExpectedIntersection(self):
    return 4.59375

  def computeExpectedUnion(self):
    return 7.40625

  #Runs the Operation Difference on all the algorithms
  #the following functions are to be kept test_*** to be unittest valid
  def test_difference(self):
    expected_area = self.computeExpectedDifference()
    for algo_name, algo in self.algos.items():
      with self.subTest(algo = algo_name):
        #standard way to use the same test for multiple parameters in unittest
        type(self).test_counter +=1
        result_mesh = mesh_boolean_api.Difference(self.mesh_1, self.mesh_2, algo = algo)
        computed_area = result_mesh.GetArea()
        self.assertAlmostEqual(expected_area, computed_area, delta = 5e-4)

  #Runs the Operation Intersection on all the algorithms
  def test_intersection(self):
    expected_area = self.computeExpectedIntersection()
    for algo_name, algo in self.algos.items():
      with self.subTest(algo = algo_name):
        type(self).test_counter +=1
        result_mesh = mesh_boolean_api.Intersection(self.mesh_1, self.mesh_2, algo = algo)
        computed_area = result_mesh.GetArea()
        self.assertAlmostEqual(expected_area, computed_area, delta = 5e-4)

  #Runs the Operation Union on all the algorithms
  def test_union(self):
    expected_area = self.computeExpectedUnion()
    for algo_name, algo in self.algos.items():
      with self.subTest(algo = algo_name):
        type(self).test_counter +=1
        result_mesh = mesh_boolean_api.Union(self.mesh_1, self.mesh_2, algo = algo)
        computed_area = result_mesh.GetArea()
        self.assertAlmostEqual(expected_area, computed_area, delta = 5e-4)

  def tearDown(self):
    # stuff done after launching test
    # show the exact number of tests run(including the subtests)
    print(f"Total sub-tests ran : {self.test_counter}")

if __name__ == '__main__':
  # launch all tests
  unittest.main(exit = False)

  # or launch only tests specific to the algos installed (by checking environement variable)
