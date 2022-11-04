from pathlib import Path

import customtkinter
import tkinter
import vispy
from vispy.io import imread

class Model:

    def __init__(self, file_name=None):

        self.data = []
        self.object_type = None
        if file_name is None:
            # Define unit cube.

            self.data = []
        else:
            self.load_file(file_name)

    def clear(self):
        self.data = []

    def load_file(self, file_name, object_type='image'):
        '''Load mesh from file
        '''
        if object_type == 'mesh':
            vertices, faces, _, _ = vispy.io.read_mesh(file_name)
            self.data.append(Mesh(vertices, faces))
            self.object_type = 'mesh'
        elif object_type == 'image':
            img_data = imread(file_name)
            self.data.append(img_data)
            self.object_type = 'image'

    def get_bounding_box(self):
        bbox = self.data[0].bounding_box
        for mesh in self.data[1:]:
            for i in range(len(bbox)):
                x_i = mesh.bounding_box[i]
                bbox[i][0] = min([bbox[i][0], min(x_i)])
                bbox[i][1] = max([bbox[i][1], max(x_i)])

        return bbox


class Mesh:

    def __init__(self, vertices, faces):
        self.vertices = vertices
        self.faces = faces
        self.bounding_box = self.get_bounding_box()

    def get_vertices(self):
        vertices = []
        for face in self.faces:
            vertices.append([self.vertices[ivt] for ivt in face])

        return vertices

    def get_line_segments(self):
        line_segments = set()
        for face in self.faces:
            for i in range(len(face)):
                iv = face[i]
                jv = face[(i + 1) % len(face)]
                if jv > iv:
                    edge = (iv, jv)
                else:
                    edge = (jv, iv)

                line_segments.add(edge)

        return [[self.vertices[edge[0] - 1], self.vertices[edge[1] - 1]] for edge in line_segments]

    def get_bounding_box(self):
        v = [vti for face in self.get_vertices() for vti in face]
        bbox = []
        for i in range(len(self.vertices[0])):
            x_i = [p[i] for p in v]
            bbox.append([min(x_i), max(x_i)])

        return bbox


class View:

    def __init__(self, model=None):

        if model is None:
            model = Model()
        self.model = model
        self.canvas = None
        self.vpview = None

    def clear(self):
        if self.vpview is not None:
            self.vpview.parent = None

        self.vpview = self.canvas.central_widget.add_view(bgcolor='#4a4949')
        # vispy.scene.visuals.XYZAxis(parent=self.vpview.scene)

    def plot(self, types="solid"):
        self.clear()
        # if isinstance(types, (str,)):
        #     types = [s.strip() for s in types.split('+')]
        if self.model.object_type == 'mesh':
            for mesh in self.model.data:
                msh = vispy.scene.visuals.Mesh(vertices=mesh.vertices,
                                               shading='smooth',
                                               faces=mesh.faces)
                self.vpview.add(msh)
            self.vpview.camera = vispy.scene.TurntableCamera(parent=self.vpview.scene, elevation=90, azimuth=0, roll=90)
        else:
            for im_data in self.model.data:
                image = vispy.scene.visuals.Image(im_data,
                                                  parent=self.vpview)
                self.vpview.add(image)
            self.vpview.camera = vispy.scene.PanZoomCamera(aspect=1)
            self.vpview.camera.flip = (0, 1, 0)
            self.vpview.camera.set_range()
            self.vpview.camera.zoom(1.0, (250, 200))


class Controller:
    TOP_LEVEL_OFFSET_X = 297
    TOP_LEVEL_OFFSET_Y = 70

    def __init__(self, view=None, parent=None):

        root = customtkinter.CTkToplevel(parent)
        root.geometry(f"325x370+{Controller.TOP_LEVEL_OFFSET_X}+{Controller.TOP_LEVEL_OFFSET_Y}")
        root.title("Query Garment")

        if view is None:
            view = View()

        f1 = customtkinter.CTkFrame(root)
        f1.pack(side=tkinter.TOP, anchor=tkinter.CENTER)
        f3 = customtkinter.CTkFrame(f1)
        f3.pack(side=tkinter.TOP, anchor=tkinter.CENTER, padx=(0, 0))
        self.file_name = None
        button_apply = customtkinter.CTkButton(f3, text="apply", command=self.apply)
        button_apply.pack()
        canvas = vispy.scene.SceneCanvas(
            keys='interactive', show=True, parent=root)
        canvas.native.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=True)
        view.canvas = canvas
        root.update_idletasks()

        self.parent = parent
        self.root = root
        self.view = view
        self.model = view.model
        self.drag_id = ''
        self.root.protocol('WM_DELETE_WINDOW', self.disable_event)
        self.root.wm_transient(self.parent)

        view.plot()

    def dragging(self, event):
        if event.widget is self.parent:
            if self.drag_id == '':
                pass
            else:
                self.parent.after_cancel(self.drag_id)
                x = self.parent.winfo_x()
                y = self.parent.winfo_y()
                # logging.info(f"Window position({x}, {y})")
                self.root.geometry(f'400x300+{x + Controller.TOP_LEVEL_OFFSET_X}+{y + Controller.TOP_LEVEL_OFFSET_Y}')
            self.drag_id = self.parent.after(1000, self.stop_drag)

    def stop_drag(self):
        self.drag_id = ''

    def render(self):
        self.root.mainloop()

    def disable_event(self):
        pass

    def open(self):
        file_name = tkinter.filedialog.askopenfilename(title="Select file to open",
                                                       filetypes=(("JPEG Image", "*.jpg"),
                                                                  ("JPEG Image", "*.jpeg"),
                                                                  ("OBJ files", "*.obj"),
                                                                  ("STL Files", "*.stl"),
                                                                  ("all files", "*.*")))
        # logging.info(f'file_name: {file_name}')
        if Path(file_name).suffix == '.obj' or Path(file_name).suffix == '.stl':
            object_type = 'mesh'
        else:
            object_type = 'image'
        # logging.info(f'object_type: {object_type}')
        self.parent.modify_object_type(object_type)
        self.parent.modify_scanned_file(file_name)
        self.model.clear()
        self.model.load_file(file_name, object_type=object_type)
        self.view.plot()
        self.parent.clear_images()
        self.parent.clear_info()
        self.parent._scanned_file = file_name
        self.parent.clear_images()

    def exit(self):
        self.model.clear()
        self.root.model = None
        self.view.clear()
        self.root.view = None
        self.root.destroy()

    def modifyFileName(self, filename):
        self.file_name = filename

    def apply(self):
        self.parent.retrieve()
