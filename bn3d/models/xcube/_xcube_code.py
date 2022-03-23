import itertools
from typing import Tuple, Dict
import numpy as np
from bn3d.models import StabilizerCode

Indexer = Dict[Tuple[int, int], int]  # coordinate to index


class XCubeCode(StabilizerCode):
    @property
    def dimension(self) -> int:
        return 3

    @property
    def label(self) -> str:
        return 'XCube {}x{}x{}'.format(*self.size)

    def _vertex(self, location: Tuple[int, int, int], deformed_axis: int = None) -> Dict[str, Tuple]:
        r"""Apply cube operator on sites around cubes.

        Parameters
        ----------
        operator: str
            Pauli operator in string format.
        location: Tuple[int, int, int]
            The (x, y, z) location of the cube
        """

        if location not in self.vertex_index:
            raise ValueError(f"Invalid coordinate {location} for a vertex")

        pauli = 'Z'
        deformed_pauli = 'X'

        delta = [(1, 1, 0), (-1, -1, 0), (1, -1, 0), (-1, 1, 0),
                 (-1, 0, -1), (1, 0, -1), (0, -1, -1), (0, 1, -1),
                 (-1, 0, 1), (1, 0, 1), (0, -1, 1), (0, 1, 1)]

        operator = dict()
        for d in delta:
            qubit_location = tuple(np.add(location, d) % (2*np.array(self.size)))

            if self.is_qubit(qubit_location):
                is_deformed = (self.axis(qubit_location) == deformed_axis)
                operator[qubit_location] = deformed_pauli if is_deformed else pauli

        return operator

    def _face(self, location: Tuple[int, int, int], deformed_axis: int = None) -> Dict[str, Tuple]:
        r"""Apply face operator on sites neighboring vertex.

        Parameters
        ----------
        operator: str
            Pauli operator in string format.
        location: Tuple[int, int, int]
            The (axis, x, y, z) location and orientation of the face
        """

        axis, x, y, z = location

        if location not in self.face_index:
            raise ValueError(f"Invalid coordinate {location} for a face")

        pauli = 'X'
        deformed_pauli = 'Z'

        delta = [[], [], []]

        delta[self.X_AXIS] = [(0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
        delta[self.Y_AXIS] = [(1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)]
        delta[self.Z_AXIS] = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)]

        operator = dict()
        for d in delta[axis]:
            qubit_location = tuple(np.add([x, y, z], d) % (2*np.array(self.size)))

            if self.is_qubit(qubit_location):
                is_deformed = (self.axis(qubit_location) == deformed_axis)
                operator[qubit_location] = deformed_pauli if is_deformed else pauli

        return operator

    def axis(self, location):
        x, y, z = location

        if (z % 2 == 0) and (x % 2 == 1) and (y % 2 == 0):
            axis = self.X_AXIS
        elif (z % 2 == 0) and (x % 2 == 0) and (y % 2 == 1):
            axis = self.Y_AXIS
        elif (z % 2 == 1) and (x % 2 == 0) and (y % 2 == 0):
            axis = self.Z_AXIS
        else:
            raise ValueError(f'Location {location} does not correspond to a qubit')

        return axis

    def _create_qubit_indices(self) -> Indexer:
        coordinates = []
        Lx, Ly, Lz = self.size

        # Qubits along e_x
        for x in range(1, 2*Lx, 2):
            for y in range(0, 2*Ly, 2):
                for z in range(0, 2*Lz, 2):
                    coordinates.append((x, y, z))

        # Qubits along e_y
        for x in range(0, 2*Lx, 2):
            for y in range(1, 2*Ly, 2):
                for z in range(0, 2*Lz, 2):
                    coordinates.append((x, y, z))

        # Qubits along e_z
        for x in range(0, 2*Lx, 2):
            for y in range(0, 2*Ly, 2):
                for z in range(1, 2*Lz, 2):
                    coordinates.append((x, y, z))

        coord_to_index = {coord: i for i, coord in enumerate(coordinates)}

        return coord_to_index

    def _create_vertex_indices(self) -> Indexer:
        """ Vertex = cube stabilizer"""
        Lx, Ly, Lz = self.size

        ranges = [range(1, 2*Lx, 2), range(1, 2*Ly, 2), range(1, 2*Lz, 2)]
        coordinates = []
        for x, y, z in itertools.product(*ranges):
            coordinates.append((x, y, z))

        coord_to_index = {coord: i for i, coord in enumerate(coordinates)}

        return coord_to_index

    def _create_face_indices(self) -> Indexer:
        """ Face stabilizer (three at each vertex)"""

        coordinates = []
        Lx, Ly, Lz = self.size

        for x in range(0, 2*Lx, 2):
            for y in range(0, 2*Ly, 2):
                for z in range(0, 2*Lz, 2):
                    for axis in range(3):
                        coordinates.append((axis, x, y, z))

        coord_to_index = {coord: i for i, coord in enumerate(coordinates)}

        return coord_to_index

    def _get_logicals_x(self) -> np.ndarray:
        """The 3 logical X operators."""

        Lx, Ly, Lz = self.size
        logicals = []

        # String of parallel X operators along the x direction
        operator = dict()
        for x in range(0, 2*Lx, 2):
            operator[(x, 1, 0)] = 'X'
        logicals.append(operator)

        # String of parallel X operators normal to the y direction
        operator = dict()
        for y in range(0, 2*Ly, 2):
            operator[(1, y, 0)] = 'X'
        logicals.append(operator)

        # String of parallel X operators normal to the z direction
        operator = dict()
        for z in range(0, 2*Lz, 2):
            operator[(0, 1, z)] = 'X'
        logicals.append(operator)

        return logicals

    def _get_logicals_z(self) -> np.ndarray:
        """The 3 logical Z operators."""
        Lx, Ly, Lz = self.size
        logicals = []

        # Line of parallel Z operators along the x direction
        operator = dict()
        for x in range(1, 2*Lx, 2):
            operator[(x, 0, 0)] = 'Z'
        logicals.append(operator)

        # Line of parallel Z operators along the y direction
        operator = dict()
        for y in range(1, 2*Ly, 2):
            operator[(0, y, 0)] = 'Z'
        logicals.append(operator)

        # Line of parallel Z operators along the z direction
        operator = dict()
        for z in range(1, 2*Lz, 2):
            operator[(0, 0, z)] = 'Z'
        logicals.append(operator)

        return logicals
