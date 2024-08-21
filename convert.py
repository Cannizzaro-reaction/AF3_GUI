from Bio.PDB import MMCIFParser, PDBIO
import os


def convert_pdb(cif_file_path, pdb_file_path):

    parser = MMCIFParser()
    structure = parser.get_structure("structure_name", cif_file_path)

    io = PDBIO()
    io.set_structure(structure)
    io.save(pdb_file_path)

    print(f"Converted {cif_file_path} to {pdb_file_path}")
