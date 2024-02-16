meshbooleanplugin
======
<img src="https://github.com/SalomePlatform/meshbooleanplugin/assets/52162083/1bea24a5-e2bd-43bb-8eb4-49f801b2675a" alt="bool" width="500" align="left"/>
<img src="https://github.com/SalomePlatform/meshbooleanplugin/assets/52162083/e23f5412-cb16-4f2e-a54d-cf7f363fa0e6" alt="smesh" width="500" align="left"/>
<img src="https://github.com/SalomePlatform/meshbooleanplugin/assets/52162083/eb701b12-8572-47e3-8726-d4a40fdd8415" alt="smeshbool" width="500" align="left"/>
 
The meshing world is growing and evolving at a rapid pace, be it for computer graphics, numerical simulations, texture, or other applications. A novelty in the meshing world is "mesh boolean". This refers to post-processing existing meshes via boolean operations such as union, subtraction, and intersection, such that a new more desired mesh is obtained.  For example for two meshes, $\Omega_1^h$ and $\Omega_2^h$, we could be interested in boolean operation $\mathcal{B}(\Omega^h_1, \Omega_2^h)$, i.e, we search  for a new mesh $\Omega_3^h : \mathcal{B}(\Omega^h_1, \Omega_2^h) \rightarrow \Omega_3^h$ which is obtained via:

- union operation:
  
	 $\Omega_3^h = \Omega_1^h \cup \Omega_2^h = \{\Omega_{1,1}^h , \Omega_{2,2}^h\}$
- intersection operation

   $\Omega_3^h = \Omega_1^h \cap \Omega_2^h = \{\Omega_{1,2}^h , \Omega_{2,1}^h\}$
- subtraction operation
  
$\Omega_3^h = \Omega_1^h \backslash \Omega_2^h  = \{\Omega_{1,1}^h , \Omega_{2,1}^h\}$  or

$\Omega_3^h = \Omega_2^h \backslash \Omega_1^h =  \{\Omega_{1,2}^h , \Omega_{2,2}^h\}$

You can see an example of union mesh operation on the left, performed via this plugin. 

Such meshing operations could be of interest for  multiple reasons, e.g, in evolving mesh simulations, in crash simulations, for creating and edit digital shapes, and for optical tomography based mesh construction.

This plugin provides an interface for performing boolean operations on meshes in SALOME, the plugin attaches itself to SMESH (Salome Mesh) module, and provides SALOME uses with possiblity of performing boolean operations via five diffrent boolean engines. 


How to attach this plugin to my SMESH ? 
=======


To try the plugin locally, follow these steps:
1. Clone the repo to `$SMESH_ROOT_DIR/share/salome/plugins/smesh/`

2. Append the following code to the end of the file `$SMESH_ROOT_DIR/share/salome/plugins/smesh/smesh_plugins.py`:
   
```python
# mesh boolean plugin for SALOME
try:
	from meshbooleanplugin.mesh_boolean_plugin import MeshBoolean
	salome_pluginsmanager.AddFunction('Boolean Mesh Operations', 'Perform boolean operations on meshes', MeshBoolean)
except Exception as e:
	salome_pluginsmanager.logger.info('ERROR: MeshBoolean plug-in is unavailable: {}'.format(e))
	pass
```

this can be easily performed via the following command 
```bash
echo "\n# mesh boolean plugin for SALOME\ntry:\n\tfrom meshbooleanplugin.mesh_boolean_plugin import MeshBoolean\n\tsalome_pluginsmanager.AddFunction('Boolean Mesh Operations', 'Perform boolean operations on meshes', MeshBoolean)\nexcept Exception as e:\n\tsalome_pluginsmanager.logger.info('ERROR: MeshBoolean plug-in is unavailable: {}'.format(e))\n\tpass" >> smesh_plugins.py
```
4. Prepare the plugin, this involes preparing `*.ui` files and downloading the boolean operation engines:
```bash
cd meshbooleanplugin 
make all
```   
5. Compile the project with
```bash
mkdir -p build
cd build
cmake ..
make
```
have a look at the `CmakeList.txt` to compile the backend engines of your choice. 

6. Install the Python requirements with
```bash
salome context
pip install -r requirements.txt
```

How to use this plugin ?
=======
1. start salome
```bash
./salome
```
2. open SMESH and browse to `Mesh > SMESH plugins > Boolean Mesh Operations`, this shoudl open the widget for perfroming boolean operations for the mesh

 <img src="https://github.com/SalomePlatform/meshbooleanplugin/assets/52162083/c46a7ac8-e24a-41b2-9c1f-77ec60a34bd4" alt="bool" width="600" align="center"/>

3. You can then add meshes (`Left Mesh` and `Right Mesh`) via SMESH object browser or upload a mesh.
4. Choose what kind of boolean operation you would like to perform in the `Operator` section of the widget.
5. Choose the backend engine from the dropdown list in `Engine` section, and click `compute`.
6. Your mesh should appear in teh SMESH object browser.  
