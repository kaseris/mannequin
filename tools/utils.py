import os.path as osp

import customtkinter
import numpy as np
from scipy.special import comb

def get_model_name(path_to_obj):
    n1, n2 = osp.splitext(path_to_obj)
    filename = osp.basename(n1)
    return filename.split('_')[0]


def similarity(query, retrieved, ss_mat):
    if ss_mat[retrieved, query] <= 0.0:
        return ss_mat[query, retrieved]
    return ss_mat[retrieved, query]


def create_ss_matrix(path):
    with open(path, 'r') as f:
        for idx, line in enumerate(f):
            l = line.strip().split(',')
            if idx == 0:
                ss = np.zeros((len(l) + 1, len(l) + 1))
            ss[idx, idx + 1:] = [float(el) for el in l]
    return ss


def smoothstep(x, x_min=0, x_max=1, N=1):
    x = np.clip((x - x_min) / (x_max - x_min), 0, 1)

    result = 0
    for n in range(0, N + 1):
         result += comb(N + n, n) * comb(2 * N + 1, N - n) * (-x) ** n

    result *= x ** (N + 1)

    return np.expand_dims(result, axis=1)


class ErrorPopup(customtkinter.CTkToplevel):
    def __init__(self, master, message, geometry):
        super(ErrorPopup, self).__init__(master=master)
        self.geometry(geometry)
        self.title('Error')
        label = customtkinter.CTkLabel(master=self,
                                       text=message,
                                       text_font=('Roboto', 11))
        label.pack()
        button = customtkinter.CTkButton(master=self,
                                         text='OK',
                                         text_font=('Roboto', 11),
                                         command=self.destroy)
        button.pack()

    def run(self):
        self.mainloop()
