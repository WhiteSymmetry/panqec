import numpy as np

from flask import Flask, send_from_directory, request, json, render_template
from bn3d.tc3d import (
    ToricCode3D, RotatedPlanarCode3D, RotatedToricCode3D, SweepMatchDecoder,
    RotatedSweepMatchDecoder
)
from bn3d.tc2d import Toric2DPymatchingDecoder
from qecsim.models.toric import ToricCode
from bn3d.rhombic import RhombicCode
from bn3d.bp_os_decoder import BeliefPropagationOSDDecoder
from bn3d.noise import PauliErrorModel
from bn3d.deform import (
    DeformedXZZXErrorModel, DeformedXYErrorModel, DeformedSweepMatchDecoder
)

import webbrowser
# from threading import Timer


app = Flask(__name__)


def open_browser(port):
    webbrowser.open_new_tab(f'http://127.0.0.1:{port}/')


@app.route('/')
def send_index():
    return render_template('index.html')


@app.route('/2d')
def send_index_2d():
    return render_template('gui.html')


@app.route('/3d')
def send_index_3d():
    return render_template('gui.html')


@app.route('/main.css')
def css():
    return send_from_directory('static/css/main.css')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static/favicon.ico')


@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)


@app.route('/stabilizer-matrix', methods=['POST'])
def send_stabilizer_matrix():
    Lx = request.json['Lx']
    Ly = request.json['Ly']
    if 'Lz' in request.json:
        Lz = request.json['Lz']
    code_name = request.json['code_name']

    indices = {}

    if code_name == 'toric2d':
        code = ToricCode(Lx, Ly)

        n_qubits = code.n_k_d[0]
        n_stabilizers = code.stabilizers.shape[0]
        n_vertices = int(np.product(code.size))
        n_faces = n_stabilizers - n_vertices

        Hz = code.stabilizers[:n_faces, n_qubits:]
        Hx = code.stabilizers[n_faces:, :n_qubits]

    elif code_name == 'cubic':
        code = ToricCode3D(Lx, Ly, Lz)

        Hz = code.Hz
        Hx = code.Hx

        qubit_index = code.qubit_index
        qubit_index = {str(list(coord)): i for coord, i in qubit_index.items()}

        vertex_index = code.vertex_index
        vertex_index = {
            str(list(coord)): i for coord, i in vertex_index.items()
        }

        face_index = code.face_index
        face_index = {str(list(coord)): i for coord, i in face_index.items()}

        indices = {
            'qubit': qubit_index, 'vertex': vertex_index, 'face': face_index
        }

    elif code_name == 'rhombic':
        code = RhombicCode(Lx, Ly, Lz)

        Hz = code.Hz
        Hx = code.Hx

        qubit_index = code.qubit_index
        qubit_index = {str(list(coord)): i for coord, i in qubit_index.items()}

        triangle_index = code.triangle_index
        triangle_index = {
            str(list(coord)): i for coord, i in triangle_index.items()
        }

        cube_index = code.cube_index
        cube_index = {str(list(coord)): i for coord, i in cube_index.items()}

        indices = {
            'qubit': qubit_index, 'triangle': triangle_index,
            'cube': cube_index
        }

    elif code_name == 'rotated-planar':
        code = RotatedPlanarCode3D(Lx, Ly, Lz)

        Hz = code.Hz
        Hx = code.Hx

        qubit_index = code.qubit_index
        qubit_index = {str(list(coord)): i for coord, i in qubit_index.items()}

        vertex_index = code.vertex_index
        vertex_index = {
            str(list(coord)): i for coord, i in vertex_index.items()
        }

        face_index = code.face_index
        face_index = {str(list(coord)): i for coord, i in face_index.items()}

        indices = {
            'qubit': qubit_index, 'vertex': vertex_index, 'face': face_index
        }

    elif code_name == 'rotated-toric':
        code = RotatedToricCode3D(Lx, Ly, Lz)

        Hz = code.Hz
        Hx = code.Hx

        qubit_index = code.qubit_index
        qubit_index = {str(list(coord)): i for coord, i in qubit_index.items()}

        vertex_index = code.vertex_index
        vertex_index = {
            str(list(coord)): i for coord, i in vertex_index.items()
        }

        face_index = code.face_index
        face_index = {str(list(coord)): i for coord, i in face_index.items()}

        indices = {
            'qubit': qubit_index, 'vertex': vertex_index, 'face': face_index
        }

    n_qubits = code.n_k_d[0]
    logical_z = code.logical_zs
    logical_x = code.logical_xs

    return json.dumps({'Hx': Hx.tolist(),
                       'Hz': Hz.tolist(),
                       'indices': indices,
                       'logical_z': logical_z[:, n_qubits:].tolist(),
                       'logical_x': logical_x[:, :n_qubits].tolist()})


@app.route('/decode', methods=['POST'])
def send_correction():
    content = request.json
    syndrome = np.array(content['syndrome'])
    Lx = content['Lx']
    Ly = content['Ly']
    if 'Lz' in content:
        Lz = content['Lz']
    p = content['p']
    deformation = content['deformation']
    max_bp_iter = content['max_bp_iter']
    decoder_name = content['decoder']
    error_model_name = content['error_model']
    code_name = content['code_name']

    if code_name == 'toric2d':
        code = ToricCode(Lx, Ly)
    elif code_name == 'cubic':
        code = ToricCode3D(Lx, Ly, Lz)
    elif code_name == 'rhombic':
        code = RhombicCode(Lx, Ly, Lz)
    elif code_name == 'rotated-planar':
        code = RotatedPlanarCode3D(Lx, Ly, Lz)
    elif code_name == 'rotated-toric':
        code = RotatedToricCode3D(Lx, Ly, Lz)
    else:
        raise ValueError('Code not recognized')

    n_qubits = code.n_k_d[0]

    if error_model_name == 'Pure X':
        rx, ry, rz = (1, 0, 0)
    elif error_model_name == 'Pure Z':
        rx, ry, rz = (0, 0, 1)
    elif error_model_name == 'Depolarizing':
        rx, ry, rz = (1/3, 1/3, 1/3)
    else:
        raise ValueError('Error model not recognized')

    if deformation == "None":
        error_model = PauliErrorModel(rx, ry, rz)
    elif deformation == "XZZX":
        error_model = DeformedXZZXErrorModel(rx, ry, rz)
    elif deformation == "XY":
        error_model = DeformedXYErrorModel(rx, ry, rz)
    else:
        raise ValueError("Deformation not recognized")

    if decoder_name == 'bp-osd':
        decoder = BeliefPropagationOSDDecoder(error_model, p,
                                              max_bp_iter=max_bp_iter,
                                              joschka=False)
    elif decoder_name == 'bp-osd-2':
        decoder = BeliefPropagationOSDDecoder(error_model, p,
                                              max_bp_iter=max_bp_iter,
                                              joschka=True)
    elif decoder_name == 'matching':
        decoder = Toric2DPymatchingDecoder()
    elif decoder_name == 'sweepmatch':
        if "Rotated" in code.label:
            decoder = RotatedSweepMatchDecoder()
        elif deformation == "XZZX":
            decoder = DeformedSweepMatchDecoder(error_model, p)
        elif deformation == "None":
            decoder = SweepMatchDecoder()
        elif deformation == "XY":
            raise NotImplementedError("No SweepMatch decoder for XY code")
        else:
            raise ValueError("Deformation not recognized")
    else:
        raise ValueError(f'Decoder {decoder} not recognized')

    correction = decoder.decode(code, syndrome)

    correction_x = correction[:n_qubits]
    correction_z = correction[n_qubits:]

    print(json.dumps({'x': correction_x.tolist(), 'z': correction_z.tolist()}))
    return json.dumps({'x': correction_x.tolist(), 'z': correction_z.tolist()})


@app.route('/new-errors', methods=['POST'])
def send_random_errors():
    content = request.json
    Lx = content['Lx']
    Ly = content['Ly']
    if 'Lz' in content:
        Lz = content['Lz']
    p = content['p']
    deformation = content['deformation']
    error_model_name = content['error_model']
    code_name = content['code_name']

    if code_name == 'toric2d':
        code = ToricCode(Lx, Ly)
    elif code_name == 'cubic':
        code = ToricCode3D(Lx, Ly, Lz)
    elif code_name == 'rhombic':
        code = RhombicCode(Lx, Ly, Lz)
    elif code_name == 'rotated-planar':
        code = RotatedPlanarCode3D(Lx, Ly, Lz)
    elif code_name == 'rotated-toric':
        code = RotatedToricCode3D(Lx, Ly, Lz)
    else:
        raise ValueError('Code not recognized')

    if error_model_name == 'Pure X':
        rx, ry, rz = (1, 0, 0)
    elif error_model_name == 'Pure Z':
        rx, ry, rz = (0, 0, 1)
    elif error_model_name == 'Depolarizing':
        rx, ry, rz = (1/3, 1/3, 1/3)
    else:
        raise ValueError('Error model not recognized')

    if deformation == "None":
        error_model = PauliErrorModel(rx, ry, rz)
    elif deformation == "XZZX":
        error_model = DeformedXZZXErrorModel(rx, ry, rz)
    elif deformation == "XY":
        error_model = DeformedXYErrorModel(rx, ry, rz)
    else:
        raise ValueError('Deformation not recognized')

    errors = error_model.generate(code, p)

    n_qubits = code.n_k_d[0]
    bsf_to_str_map = {(0, 0): 'I', (1, 0): 'X', (0, 1): 'Z', (1, 1): 'Y'}
    error_spec = [
        (
            bsf_to_str_map[
                (errors[i_qubit], errors[i_qubit + n_qubits])
            ],
            [
                coords for coords, index in code.qubit_index.items()
                if index == i_qubit
            ][0]
        )
        for i_qubit in range(n_qubits)
    ]
    error_spec = [spec for spec in error_spec if spec[0] != 'I']
    return json.dumps(errors.tolist())


if __name__ == '__main__':
    port = 5000
    # Timer(1, open_browser, [port]).start()

    app.run(port=port)
