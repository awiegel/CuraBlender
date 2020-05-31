import bpy
import sys


def main():
    program = sys.argv[-1]

    if program == 'Count nodes':
        nodes = 0
        for node in range(len(bpy.data.objects)):
            if bpy.data.objects[node].name != "Camera" and bpy.data.objects[node].name != "Light" and bpy.data.objects[node].name != "Sun":
                nodes += 1
        print(nodes)
    elif program == 'Single node':
        exec(sys.argv[-2])
    elif program == 'Multiple nodes':
        index = int(sys.argv[-2])
        nodes = []

        for node in range(len(bpy.data.objects)):
            if bpy.data.objects[node].name != "Camera" and bpy.data.objects[node].name != "Light":
                nodes.append(bpy.data.objects[node])

        for node in range(len(nodes)):
            if node != index:
                bpy.data.objects.remove(nodes[node])
                # bpy.context.collection.objects.unlink(nodes[node])
        exec(sys.argv[-3])
    else:
        None
 

if __name__ == "__main__":
    main()
