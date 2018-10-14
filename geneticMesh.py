import bpy
import bmesh
from enum import Enum
import random
import numpy
import mathutils

class MeshOperation(Enum):
	SELECT_FACE = 1
	SELECT_VERTEX = 2
	SELECT_EDGE = 3
	DESELECT_ALL = 4
	
	MOVE_SELECTED_VERTS = 5
	ROTATE_SELECTION = 6
	EXTRUDE_SELECTED_FACES = 7
	
class MeshInstruction:
	operation = ''
	operands = []
	
	def __init__(self, meshOp, meshOperands):
		self.operation = meshOp
		self.operands = meshOperands
	
class MeshDNA:
	instructions = []
	
	def __init__(self, meshInstruction):
		self.instructions.append(meshInstruction)

def selectFace(bm, operands):
	print("selectFace", operands)
	
	for fid in operands:
		if fid < len(bm.faces):
			bm.faces[fid].select = True

	
def selectVertex(bm, operands):
	print("selectVertex", operands)
	
	for vid in operands:
		if vid < len(bm.verts):
			bm.verts[vid].select = True
	

def selectEdge(bm):
	print("selectEdge")
	
def deselectAll(bm):
	print("deselectAll")
	
	for v in bm.verts:
		v.select = False
		
	for f in bm.faces:
		f.select = False
		
	for e in bm.edges:
		e.select = False
	
def moveSelectedVerts(bm, operands):
	print("moveSelectedVerts", operands)
	
	for v in bm.verts:
		if v.select == True:
			v.co = v.co + operands[0]

def rotateSelection(bm):
	print("rotateSelection")
	
def extrudeSelectedFaces(bm):
	print("extrudeSelectedFaces")
	
	extrudeFaces = []
	for f in bm.faces:
		if f.select == True:
			extrudeFaces.append(f)
	
	#bmesh.ops.extrude_discrete_faces(bm, extrudeFaces)
	extruded = bmesh.ops.extrude_face_region(bm, geom=extrudeFaces)
	print("extruded: ", extruded)



def executeMeshInstruction(bm, instruction):
	#print("executeMeshInstruction")
	
	bm.verts.ensure_lookup_table()
	bm.faces.ensure_lookup_table()

	op = instruction.operation
	if op == MeshOperation.SELECT_FACE:
		selectFace(bm, instruction.operands)
	elif op == MeshOperation.SELECT_VERTEX:
		selectVertex(bm, instruction.operands)
	elif op == MeshOperation.SELECT_EDGE:
		selectEdge(bm)
	elif op == MeshOperation.DESELECT_ALL:
		deselectAll(bm)
	elif op == MeshOperation.MOVE_SELECTED_VERTS:
		moveSelectedVerts(bm, instruction.operands)
	elif op == MeshOperation.ROTATE_SELECTION:
		rotateSelection(bm)
	elif op == MeshOperation.EXTRUDE_SELECTED_FACES:
		extrudeSelectedFaces(bm)
	else:
		print("Invalid operation!")
		
def generateOperands(opID):
	operands = []
	if opID == MeshOperation.SELECT_VERTEX or opID == MeshOperation.SELECT_FACE or opID == MeshOperation.SELECT_EDGE:
		for i in range(0, random.randint(1, 10)):
			operands.append(random.randint(1,10)) #todo: track vertex count
	elif opID == MeshOperation.MOVE_SELECTED_VERTS:
		magnitude = 0.02
		offset = mathutils.Vector((random.uniform(-magnitude, magnitude), random.uniform(-magnitude, magnitude), random.uniform(-magnitude, magnitude)))
		operands.append(offset)
	
	return operands
		
		
# generate a random-length dna sequence of mesh instructions
def generateDNA():
	dnaSeq = MeshDNA(MeshInstruction(MeshOperation.DESELECT_ALL, 0))
	sequenceLength = random.randint(5000, 10000)
	for i in range(0, sequenceLength):
		opID = random.randint(1, 7)
		operands = generateOperands(MeshOperation(opID))
		mo = MeshOperation(opID)
		mi = MeshInstruction(mo, operands)
		dnaSeq.instructions.append(mi)
		
	return dnaSeq
		
def main():
	# Get the active mesh
	me = bpy.context.object.data

	# Get a BMesh representation
	bm = bmesh.new()   # create an empty BMesh
	bm.from_mesh(me)   # fill it in from a Mesh
	
	#instruction = MeshInstruction(MeshOperation.SELECT_FACE, 3)
	#dna = MeshDNA(instruction)
	dna = generateDNA()
	
	# loop through each instruction in the dna sequence
	for i in dna.instructions:
		executeMeshInstruction(bm, i)

	# Finish up, write the bmesh back to the mesh
	bm.to_mesh(me)
	bm.free()  # free and prevent further access

main()