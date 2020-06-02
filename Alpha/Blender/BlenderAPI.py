import bpy
import sys
import math


def removeScene():
    node = 0
    objects = len(bpy.context.collection.objects)
    while node < objects:
        bpy.context.collection.objects.unlink(bpy.context.collection.objects[node])
        objects -= 1


def loadLibrary(file_path):
    with bpy.data.libraries.load(file_path) as (src, dst):
        dst.objects = src.objects
    return dst.objects
    

def removeDecorators(objects):
    node = 0
    nodes = len(objects)
    while node < nodes:
        if objects[node].type != "MESH":
            objects.remove(objects[node])
            node -= 1
            nodes -= 1
        node += 1


def findIndexAndLink(objects, index):
    for node in range(len(objects)):
        if node == index:
            bpy.context.collection.objects.link(objects[node])


def repositionObjects():
    # angle = radian / numbers_of_ob
    A = 6.283185307179586476925286766559 / len(bpy.context.collection.objects)

    # radius
    R = 50 * len(bpy.context.collection.objects)

    # loop number_of_ob
    for node in range(len(bpy.context.collection.objects)):
        if bpy.context.collection.objects[node].type == "MESH":
            bpy.context.collection.objects[node].location[0] = math.sin(A*node)*R       # x = sine(angle*i)*radius 
            bpy.context.collection.objects[node].location[1] = math.cos(A*node)*R       # y = cosine(angle*i)*radius
            bpy.context.collection.objects[node].location[2] = 0


def main():
    program = sys.argv[-1]

    if program == 'Count nodes':
        nodes = 0
        for node in range(len(bpy.context.collection.objects)):
            if bpy.context.collection.objects[node].type == "MESH":
                nodes += 1
        print(nodes)

    elif program == 'Single node':
        removeDecorators(bpy.context.collection.objects)
        exec(sys.argv[-2])

    elif program == 'Multiple nodes':
        file_path = sys.argv[-2]
        index = int(sys.argv[-3])

        removeScene()
        
        objects = loadLibrary(file_path)
        removeDecorators(objects)
        
        findIndexAndLink(objects, index)
        
        exec(sys.argv[-4])

    elif program == 'Write':
        blender_files = sys.argv[-2]
        blender_files = blender_files.split(';')
        
        removeScene()

        for file_path in list(filter(None, blender_files)):
            if '_curasplit_' in file_path:
                index = int(file_path[file_path.index('_curasplit_') + 11:][:-6]) - 1
                file_path = '{}.blend'.format(file_path[:file_path.index('_curasplit_')])

                objects = loadLibrary(file_path)
                removeDecorators(objects)

                findIndexAndLink(objects, index)

            else:
                objects = loadLibrary(file_path)
                removeDecorators(objects)
                
                for node in objects:
                    bpy.context.collection.objects.link(node)

        exec(sys.argv[-3])      #load foreign file format (stl, ply, obj, x3d)

        repositionObjects()

        bpy.ops.wm.save_as_mainfile(filepath = '{}'.format(sys.argv[-4]))

    else:
        None
 

if __name__ == "__main__":
    main()
