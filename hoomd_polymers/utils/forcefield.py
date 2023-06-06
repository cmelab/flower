import os
import hoomd
import forcefield_utilities as ffutils
from gmso.parameterization import apply

from .base_types import FF_Types
from .exceptions import MissingPairPotentialError

FF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../library/forcefields'))

def ff_xml_directory():
    ff_xml_directory = dict()
    for (dirpath, dirnames, filenames) in os.walk(FF_DIR):
        for file in filenames:
            if file.endswith('.xml'):
                ff_xml_directory[file.split('.xml')[0]] = os.path.join(dirpath, file)
    return ff_xml_directory


def find_xml_ff(ff_source):
    xml_directory = ff_xml_directory()
    if os.path.isfile(ff_source):
        if not ff_source.endswith(".xml"):
            raise ValueError("ForceField file type must be XML.")
        ff_xml_path = ff_source
        ff_type = FF_Types.custom
    elif not xml_directory.get(ff_source.split('.xml')[0]):
        raise ValueError("{} forcefield is not supported. Supported XML forcefields are {}".
                         format(ff_source, list(xml_directory.keys())))
    else:
        ff_key = ff_source.split('.xml')[0]
        ff_xml_path = xml_directory.get(ff_key)
        ff_type = getattr(FF_Types, ff_key)
    return ff_xml_path, ff_type


def apply_xml_ff(ff_xml_path, gmso_mol):
    gmso_ff = ffutils.FoyerFFs().load(ff_xml_path).to_gmso_ff()
    apply(top=gmso_mol,
          forcefields=gmso_ff,
          identify_connections=True)
    #TODO: Warning if any parameter is missing?
    return gmso_mol


def _validate_hoomd_ff(forcefields, topology_information, remove_hydrogens):
    #TODO: Check if a force exsits for all bonded and non-bonded interaction types.
    pair_forces = []
    special_pair_forces = []
    bond_forces = []
    angle_forces = []
    dihedral_forces = []

    for force in forcefields:
        if isinstance(force, hoomd.md.pair.Pair):
            pair_forces.append(force)
        elif isinstance(force, hoomd.md.special_pair.SpecialPair):
            special_pair_forces.append(force)
        elif isinstance(force, hoomd.md.bond.Bond):
            bond_forces.append(force)
        elif isinstance(force, hoomd.md.angle.Angle):
            angle_forces.append(force)
        elif isinstance(force, hoomd.md.dihedral.Dihedral):
            dihedral_forces.append(force)

    for f in pair_forces:
        for pair in topology_information["pair_types"]:
            params = list(map(list, f.params.keys()))
            if not (list(pair) in params or list(pair[::-1]) in params):
                raise MissingPairPotentialError(pair=tuple(pair), potential_type=type(f))



