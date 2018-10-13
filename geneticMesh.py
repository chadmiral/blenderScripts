import bpy
import bmesh
from enum import Enum
import random

class MeshOperation(Enum):
    SELECT_FACE = 1,
    SELECT_VERTEX = 2,
    SELECT_EDGE = 3,
    
    DESELECT_ALL = 4,
    
    MOVE_SELECTION = 5,
    ROTATE_SELECTION = 6,
    EXTRUDE_SELECTION = 7
    
class MeshInstruction:
    def __init__(self, meshOp, meshOperands):
        self.operation = meshOp
        self.operands = meshOperands
    
class MeshDNA:
    instructions = []
    
    def __init__(self, meshInstruction):
        self.instructions.append(meshInstruction)

# generate a random-length dna sequence of mesh instructions
def generateDNA():
    dnaSeq = MeshDNA(MeshInstruction(DESELECT_ALL))
    sequenceLength = random.randint(4, 10)
    for i in sequenceLength:
        mo = MeshOperation(random.randint(1, 6))
        mi = MeshInstruction(mo, 0)
        dnaSeq.program.append(mi)
        
    return dnaSeq

def executeMeshInstruction(bm, instruction):
    print("executeMeshInstruction")
    #x = instruction.operation
    result = {
        MeshOperation.SELECT_FACE: lambda x: print("SELECT_FACE"),
        MeshOperation.SELECT_VERTEX: lambda x: print("SELECT_VERTEX"),
        MeshOperation.SELECT_EDGE: lambda x: print("SELECT_EDGE"),
        MeshOperation.DESELECT_ALL: lambda x: print("DESELECT_ALL"),
        MeshOperation.MOVE_SELECTION: lambda x: print("MOVE_SELECTION"),
        MeshOperation.ROTATE_SELECTION: lambda x: print("ROTATE_SELECTION"),
        MeshOperation.EXTRUDE_SELECTION: lambda x: print("EXTRUDE")
    } [value](x)
        
def main():
    # Get the active mesh
    me = bpy.context.object.data

    # Get a BMesh representation
    bm = bmesh.new()   # create an empty BMesh
    bm.from_mesh(me)   # fill it in from a Mesh
    
    instruction = MeshInstruction(MeshOperation.SELECT_FACE, 3)
    dna = MeshDNA(instruction)
    
    # loop through each instruction in the dna sequence
    for i in dna.instructions:
        executeMeshInstruction(bm, i)
        

    # Modify the BMesh, can do anything here...
    #for v in bm.verts:
    #    v.co.x += 1.0


    # Finish up, write the bmesh back to the mesh
    bm.to_mesh(me)
    bm.free()  # free and prevent further access

main()