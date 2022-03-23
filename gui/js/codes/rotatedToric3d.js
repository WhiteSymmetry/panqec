import * as THREE from 'https://cdn.skypack.dev/three@v0.130.1';

import { AbstractCubicCode, AbstractRpCubicCode} from './base/abstractCubicCode.js';

export {RotatedToric3DCode, RpRotatedToric3DCode};

class RotatedToric3DCode extends AbstractCubicCode {
    constructor(size, Hx, Hz, qubitIndex, stabilizerIndex, qubitAxis, scene) {
        super(size, Hx, Hz, qubitIndex, stabilizerIndex, qubitAxis, scene);
    }

    buildQubit(x, y, z) {
        let length = this.SIZE.lengthEdge
        const geometry = new THREE.CylinderGeometry(this.SIZE.radiusEdge, this.SIZE.radiusEdge, this.SIZE.lengthEdge, 32);
    
        const material = new THREE.MeshPhongMaterial({color: this.COLOR.deactivatedEdge, 
                                                      opacity: this.OPACITY.maxDeactivatedQubit, 
                                                      transparent: true});
        const edge = new THREE.Mesh(geometry, material);
    
        edge.position.x = (length * Math.SQRT2 / 4) * x - this.offset.x;
        edge.position.y = (length * Math.SQRT2 / 4) * y - this.offset.y;
        edge.position.z = length * z / 2 - this.offset.z;

        let key = `[${x}, ${y}, ${z}]`;
    
        if (this.qubitAxis[key] == 2) {
            edge.rotateX(Math.PI / 2);
        }
        else if (this.qubitAxis[key] == 0) {
            edge.rotateZ(Math.PI / 4);
        }
        else if (this.qubitAxis[key] == 1) {
            edge.rotateZ(-Math.PI / 4);
        }
        else {
            console.error("Coordinate (",x, y, z, ") is not correct")
        }
    
        edge.hasError = {'X': false, 'Z': false};
        let index = this.getIndexQubit(x, y, z)
        edge.index = index;
        edge.location = [x, y, z];

        this.qubits[index] = edge;

        this.scene.add(edge);
    }

    buildVertex(x, y, z) {
        let length = this.SIZE.lengthEdge;
        const geometry = new THREE.SphereGeometry(this.SIZE.radiusVertex, 32, 32);
    
        const material = new THREE.MeshToonMaterial({color: this.COLOR.deactivatedVertex, 
                                                     opacity: this.OPACITY.maxDeactivatedStabilizer['vertex'], 
                                                     transparent: true});
        const sphere = new THREE.Mesh(geometry, material);
    
        sphere.position.x = (length * Math.SQRT2 / 4) * x - this.offset.x;
        sphere.position.y = (length * Math.SQRT2 / 4) * y - this.offset.y;
        sphere.position.z = length * z / 2 - this.offset.z;
    
        let index = this.getIndexVertex(x, y, z);
    
        sphere.index = index;
        sphere.location = [x, y, z];
        sphere.type = 'vertex'
        sphere.isActivated = false;
    
        this.stabilizers[index] = sphere;
    
        this.scene.add(sphere);
    }

    buildFace(x, y, z) {
        let length = this.SIZE.lengthEdge
        const geometry = new THREE.PlaneGeometry(this.SIZE.lengthEdge-0.3, this.SIZE.lengthEdge-0.3);
    
        const material = new THREE.MeshToonMaterial({color: this.COLOR.activatedFace, 
                                                     opacity: this.OPACITY.maxDeactivatedStabilizer['face'], 
                                                     transparent: true, 
                                                     side: THREE.DoubleSide});
        const face = new THREE.Mesh(geometry, material);
    
        face.position.x = (length * Math.SQRT2 / 4) * x - this.offset.x;
        face.position.y = (length * Math.SQRT2 / 4) * y - this.offset.y;
        face.position.z = length * z / 2 - this.offset.z;

        face.rotateZ(Math.PI/4)

        if (z % 2 == 0) {
            face.rotateX(Math.PI/2)

            if ((x + y) % 4 == 0) {
                face.rotateY(Math.PI/2)
            }
        }
    
        let index = this.getIndexFace(x, y, z);
    
        face.index = index;
        face.location = [x, y, z];
        face.type = 'face';
        face.isActivated = false;
    
        this.stabilizers[index] = face;
    
        this.scene.add(face);
    }
}

class RpRotatedToric3DCode extends AbstractRpCubicCode {
    constructor(size, Hx, Hz, qubitIndex, stabilizerIndex, qubitAxis, scene) {
        super(size, Hx, Hz, qubitIndex, stabilizerIndex, qubitAxis, scene);
    }

    buildQubit(x, y, z) {
        let length = this.SIZE.lengthEdge;
        const geometry = new THREE.SphereGeometry(this.SIZE.radiusVertex, 32, 32);

        const material = new THREE.MeshToonMaterial({color: this.COLOR.deactivatedQubit, 
                                                     opacity: this.OPACITY.maxDeactivatedQubit,
                                                     transparent: true});
        const sphere = new THREE.Mesh(geometry, material);

        sphere.position.x = (length * Math.SQRT2 / 4) * x - this.offset.x;
        sphere.position.y = (length * Math.SQRT2 / 4) * y - this.offset.y;
        sphere.position.z = length * z / 2 - this.offset.z;

        sphere.hasError = {'X': false, 'Z': false};
        let index = this.getIndexQubit(x, y, z)
        sphere.index = index;
        sphere.location = [x, y, z];

        this.qubits[index] = sphere;

        this.scene.add(sphere);
    }

    buildOctahedron(x, y, z) {
        let length = this.SIZE.lengthEdge
        const geometry = new THREE.OctahedronGeometry(this.SIZE.lengthEdge/2);

        const material = new THREE.MeshToonMaterial({color: this.COLOR.activatedOctahedron, 
                                                     opacity: this.OPACITY.maxDeactivatedStabilizer['octahedron'], 
                                                     transparent: true, side: THREE.DoubleSide});
        const octa = new THREE.Mesh(geometry, material);

        octa.position.x = (length * Math.SQRT2 / 4) * x - this.offset.x;
        octa.position.y = (length * Math.SQRT2 / 4) * y - this.offset.y;
        octa.position.z = length * z / 2 - this.offset.z;

        octa.rotateZ(Math.PI/4)

        if (z % 2 == 0) {
            octa.rotateX(Math.PI/2)

            if ((x + y) % 4 == 0) {
                octa.rotateY(Math.PI/2)
            }
        }

        let index = this.getIndexOctahedron(x, y, z);

        octa.index = index;
        octa.location = [x, y, z];
        octa.type = 'octahedron';
        octa.isActivated = false;

        this.stabilizers[index] = octa;

        this.scene.add(octa);
    }

    buildFace(x, y, z) {
        let length = this.SIZE.lengthEdge
        const geometry = new THREE.PlaneGeometry(this.SIZE.lengthEdge-0.3, this.SIZE.lengthEdge-0.3);

        const material = new THREE.MeshToonMaterial({color: this.COLOR.activatedFace, 
                                                     opacity: this.OPACITY.maxDeactivatedStabilizer['face'], 
                                                     transparent: true, side: THREE.DoubleSide});
        const face = new THREE.Mesh(geometry, material);

        face.position.x = (length * Math.SQRT2 / 4) * x - this.offset.x;
        face.position.y = (length * Math.SQRT2 / 4) * y - this.offset.y;
        face.position.z = length * z / 2 - this.offset.z;

        if (z % 2 == 0) {
            face.rotateX(Math.PI/2)

            if ((x + y) % 4 != 0) {
                face.rotateY(Math.PI/4)
            }
            else {
                face.rotateY(-Math.PI/4)
            }
            
            face.rotateZ(Math.PI/4)
        }

        let index = this.getIndexFace(x, y, z);

        face.index = index;
        face.location = [x, y, z];
        face.type = 'face';
        face.isActivated = false;

        this.stabilizers[index] = face;

        this.scene.add(face);
    }
}
