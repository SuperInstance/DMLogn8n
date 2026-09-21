#!/usr/bin/env python3
"""
Life Creation Engine - Abiogenesis and Synthetic Life Generation
Create life from non-living materials through abiogenesis simulation

This system provides:
- Prebiotic chemistry simulation
- RNA world hypothesis modeling
- Protocell formation and division
- Metabolic pathway emergence
- Genetic code evolution
- Synthetic cell design
- Artificial life creation
- Origins of life simulation
"""

import numpy as np
import math
import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
from collections import defaultdict
import hashlib

class PrebioticMolecule(Enum):
    """Types of prebiotic molecules"""
    AMINO_ACID = "amino_acid"
    NUCLEOTIDE = "nucleotide"
    LIPID = "lipid"
    SUGAR = "sugar"
    PHOSPHATE = "phosphate"
    METAL_ION = "metal_ion"
    SIMPLE_ORGANIC = "simple_organic"
    POLYMER = "polymer"

class ProtocellType(Enum):
    """Types of protocells"""
    LIPOID_VESICLE = "lipoid_vesicle"
    COACERVATE = "coacervate"
    MICELLE = "micelle"
    OIL_DROPLET = "oil_droplet"
    MINERAL_SURFACE = "mineral_surface"
    SYNTHETIC_VESICLE = "synthetic_vesicle"

class GeneticSystem(Enum):
    """Types of genetic systems"""
    RNA_WORLD = "rna_world"
    DNA_WORLD = "dna_world"
    PNA_WORLD = "pna_world"  # Peptide nucleic acid
    XNA_WORLD": "xna_world"  # Xenonucleic acid
    HYBRID = "hybrid"
    SYNTHETIC = "synthetic"

class MetabolismType(Enum):
    """Types of metabolic systems"""
    CHEMOSYNTHESIS = "chemosynthesis"
    PHOTOSYNTHESIS = "photosynthesis"
    FERMENTATION = "fermentation"
    RESPIRATION = "respiration"
    METHANOGENESIS = "methanogenesis"
    SYNTHETIC = "synthetic"

@dataclass
class Molecule:
    """Individual molecule in prebiotic soup"""
    id: str
    type: PrebioticMolecule
    composition: Dict[str, int]  # element counts
    structure: str  # SMILES-like representation
    energy: float  # Gibbs free energy
    concentration: float
    position: np.ndarray
    velocity: np.ndarray
    reactive_sites: List[str]
    catalytic_properties: Dict

@dataclass
class Protocell:
    """Protocell structure"""
    id: str
    type: ProtocellType
    membrane: List[Molecule]
    interior: List[Molecule]
    size: float  # diameter in nm
    volume: float  # volume in nm³
    ph: float
    temperature: float
    energy_level: float
    division_threshold: float
    genetic_material: Optional[List[Molecule]]
    metabolic_reactions: List[Dict]
    age: float

@dataclass
class GeneticCode:
    """Genetic code system"""
    codon_table: Dict[str, str]
    amino_acids: List[str]
    code_degeneracy: Dict[str, int]
    error_tolerance: float
    redundancy: float
    evolution_history: List[str]

@dataclass
class MetabolicPathway:
    """Metabolic pathway"""
    id: str
    name: str
    reactions: List[Dict]
    enzymes: List[Molecule]
    cofactors: List[Molecule]
    energy_yield: float
    thermodynamics: Dict[str, float]

@dataclass
class SyntheticCell:
    """Complete synthetic cell"""
    id: str
    protocell: Protocell
    genome: Optional[GeneticCode]
    metabolism: List[MetabolicPathway]
    proteins: List[Molecule]
    rna: List[Molecule]
    organelles: List[Dict]
    life_status: bool
    reproduction_rate: float
    fitness: float
    complexity: float

class LifeCreationEngine:
    """Advanced life creation and abiogenesis simulator"""

    def __init__(self):
        # Prebiotic environment parameters
        self.temperature = 25.0  # Celsius
        self.ph = 7.0
        self.pressure = 1.0  # atm
        self.ionic_strength = 0.1  # M
        self.redox_potential = -0.4  # V

        # Molecule database
        self.molecule_library = self._initialize_molecule_library()

        # Reaction networks
        self.reaction_networks = {
            'miller_urey': self._miller_urey_reactions,
            'formose': self._formose_reactions,
            'prebiotic_synthesis': self._prebiotic_synthesis_reactions,
            'polymerization': self._polymerization_reactions
        }

        # Abiogenesis scenarios
        self.abiogenesis_scenarios = {
            'rna_world': self._rna_world_scenario,
            'metabolism_first': self._metabolism_first_scenario,
            'lipid_world': self._lipid_world_scenario,
            'clay_hypothesis': self._clay_hypothesis_scenario,
            'hydrothermal_vent': self._hydrothermal_vent_scenario,
            'synthetic_creation': self._synthetic_creation_scenario
        }

        # Evolution parameters
        self.mutation_rate = 1e-6
        self.selection_pressure = 0.1
        self.diversity_threshold = 0.05

        # Life criteria
        self.min_complexity_for_life = 100  # Minimum complexity score
        self.min_reproduction_rate = 0.01  # Minimum reproduction rate
        self.min_metabolic_efficiency = 0.1  # Minimum metabolic efficiency

        # Created life forms registry
        self.life_registry = {}
        self.evolution_history = []

    def _initialize_molecule_library(self) -> Dict[str, Dict]:
        """Initialize library of prebiotic molecules"""
        return {
            # Amino acids
            'glycine': {
                'type': PrebioticMolecule.AMINO_ACID,
                'composition': {'C': 2, 'H': 5, 'N': 1, 'O': 2},
                'structure': 'NCC(=O)O',
                'energy': -488.7,  # kJ/mol
                'reactive_sites': ['amine', 'carboxyl']
            },
            'alanine': {
                'type': PrebioticMolecule.AMINO_ACID,
                'composition': {'C': 3, 'H': 7, 'N': 1, 'O': 2},
                'structure': 'C(N)C(=O)O',
                'energy': -563.6,
                'reactive_sites': ['amine', 'carboxyl']
            },
            'aspartic_acid': {
                'type': PrebioticMolecule.AMINO_ACID,
                'composition': {'C': 4, 'H': 7, 'N': 1, 'O': 4},
                'structure': 'C(C(C(=O)O)N)C(=O)O',
                'energy': -973.4,
                'reactive_sites': ['amine', 'carboxyl', 'side_chain']
            },

            # Nucleotides
            'adenine': {
                'type': PrebioticMolecule.NUCLEOTIDE,
                'composition': {'C': 5, 'H': 5, 'N': 5},
                'structure': 'c1[nH]c2nc(nc2n1)',
                'energy': 97.0,
                'reactive_sites': ['hydrogen_bonds']
            },
            'ribose': {
                'type': PrebioticMolecule.SUGAR,
                'composition': {'C': 5, 'H': 10, 'O': 5},
                'structure': 'O[C@@H]([C@@H]([C@@H]([C@H](O)O)O)O)O',
                'energy': -1265.0,
                'reactive_sites': ['hydroxyl']
            },
            'phosphate': {
                'type': PrebioticMolecule.PHOSPHATE,
                'composition': {'P': 1, 'O': 4, 'H': 3},
                'structure': 'O=P(O)(O)O',
                'energy': -1279.0,
                'reactive_sites': ['oxygen']
            },

            # Lipids
            'fatty_acid': {
                'type': PrebioticMolecule.LIPID,
                'composition': {'C': 16, 'H': 32, 'O': 2},
                'structure': 'CCCCCCCCCCCCCCCC(=O)O',
                'energy': -2348.0,
                'reactive_sites': ['carboxyl']
            },
            'glycerol': {
                'type': PrebioticMolecule.SUGAR,
                'composition': {'C': 3, 'H': 8, 'O': 3},
                'structure': 'OCC(O)CO',
                'energy': -1582.0,
                'reactive_sites': ['hydroxyl']
            },

            # Simple organics
            'methane': {
                'type': PrebioticMolecule.SIMPLE_ORGANIC,
                'composition': {'C': 1, 'H': 4},
                'structure': 'C',
                'energy': -74.8,
                'reactive_sites': ['C-H']
            },
            'ammonia': {
                'type': PrebioticMolecule.SIMPLE_ORGANIC,
                'composition': {'N': 1, 'H': 3},
                'structure': 'N',
                'energy': -45.9,
                'reactive_sites': ['lone_pair']
            },
            'hydrogen_cyanide': {
                'type': PrebioticMolecule.SIMPLE_ORGANIC,
                'composition': {'C': 1, 'H': 1, 'N': 1},
                'structure': 'C#N',
                'energy': 135.1,
                'reactive_sites': ['triple_bond']
            },

            # Metal ions
            'iron_sulfur': {
                'type': PrebioticMolecule.METAL_ION,
                'composition': {'Fe': 1, 'S': 1},
                'structure': 'Fe=S',
                'energy': -100.0,
                'reactive_sites': ['coordination']
            },
            'magnesium': {
                'type': PrebioticMolecule.METAL_ION,
                'composition': {'Mg': 1},
                'structure': 'Mg',
                'energy': 0.0,
                'reactive_sites': ['coordination']
            }
        }

    def create_prebiotic_environment(self, environment_type: str, volume: float,
                                   molecule_concentrations: Dict[str, float]) -> List[Molecule]:
        """Create prebiotic environment with specified molecules"""
        print(f"🌍 Creating prebiotic environment")
        print(f"   Environment type: {environment_type}")
        print(f"   Volume: {volume:.2f} L")
        print(f"   Molecule types: {len(molecule_concentrations)}")

        molecules = []
        molecule_id = 0

        for molecule_name, concentration in molecule_concentrations.items():
            if molecule_name in self.molecule_library:
                mol_data = self.molecule_library[molecule_name]
                num_molecules = int(concentration * volume * 6.022e23 / 1000)  # Convert to number of molecules

                for _ in range(min(num_molecules, 10000)):  # Limit for computational efficiency
                    molecule = Molecule(
                        id=f"{molecule_name}_{molecule_id:06d}",
                        type=mol_data['type'],
                        composition=mol_data['composition'],
                        structure=mol_data['structure'],
                        energy=mol_data['energy'],
                        concentration=concentration,
                        position=np.random.randn(3) * 1000,  # Random position in nm
                        velocity=np.random.randn(3) * 100,  # Random velocity in nm/s
                        reactive_sites=mol_data['reactive_sites'],
                        catalytic_properties={}
                    )
                    molecules.append(molecule)
                    molecule_id += 1

        print(f"   Total molecules created: {len(molecules)}")
        return molecules

    def simulate_chemical_evolution(self, molecules: List[Molecule], duration: float,
                                 dt: float = 0.001) -> Tuple[List[Molecule], List[Dict]]:
        """Simulate chemical evolution in prebiotic soup"""
        print(f"⚗️ Simulating chemical evolution")
        print(f"   Initial molecules: {len(molecules)}")
        print(f"   Duration: {duration} seconds")
        print(f"   Time step: {dt} seconds")

        steps = int(duration / dt)
        current_molecules = molecules.copy()
        evolution_history = []

        for step in range(steps):
            current_time = step * dt

            # Apply reactions
            current_molecules = self._apply_chemical_reactions(current_molecules, dt)

            # Apply environmental conditions
            current_molecules = self._apply_environmental_effects(current_molecules, dt)

            # Remove degraded molecules
            current_molecules = self._remove_degraded_molecules(current_molecules)

            # Record history
            if step % (steps // 100) == 0:  # Record 100 snapshots
                composition = self._analyze_composition(current_molecules)
                evolution_history.append({
                    'time': current_time,
                    'total_molecules': len(current_molecules),
                    'composition': composition,
                    'complexity': self._calculate_chemical_complexity(current_molecules)
                })

            # Progress update
            if step % (steps // 10) == 0:
                print(f"   Time: {current_time:.3f}s, Molecules: {len(current_molecules)}")

        print(f"   Final molecules: {len(current_molecules)}")
        print(f"   New molecules formed: {len(current_molecules) - len(molecules)}")
        return current_molecules, evolution_history

    def _apply_chemical_reactions(self, molecules: List[Molecule], dt: float) -> List[Molecule]:
        """Apply chemical reactions between molecules"""
        new_molecules = []
        reaction_count = 0

        # Simple collision-based reactions
        for i, mol1 in enumerate(molecules):
            for j, mol2 in enumerate(molecules[i+1:], i+1):
                distance = np.linalg.norm(mol1.position - mol2.position)

                if distance < 10.0:  # Reaction distance threshold (nm)
                    # Check for possible reactions
                    reaction_products = self._check_reaction(mol1, mol2)

                    if reaction_products:
                        for product_data in reaction_products:
                            product = Molecule(
                                id=f"product_{reaction_count:06d}",
                                type=product_data['type'],
                                composition=product_data['composition'],
                                structure=product_data['structure'],
                                energy=product_data['energy'],
                                concentration=0.001,
                                position=(mol1.position + mol2.position) / 2,
                                velocity=np.random.randn(3) * 50,
                                reactive_sites=product_data['reactive_sites'],
                                catalytic_properties={}
                            )
                            new_molecules.append(product)
                            reaction_count += 1

        # Add new molecules to existing ones
        return molecules + new_molecules

    def _check_reaction(self, mol1: Molecule, mol2: Molecule) -> Optional[List[Dict]]:
        """Check if two molecules can react"""
        # Simplified reaction rules
        reactions = []

        # Amino acid polymerization
        if mol1.type == PrebioticMolecule.AMINO_ACID and mol2.type == PrebioticMolecule.AMINO_ACID:
            if random.random() < 0.01:  # 1% probability
                dipeptide = {
                    'type': PrebioticMolecule.POLYMER,
                    'composition': {
                        **mol1.composition,
                        **{k: mol2.composition.get(k, 0) + v for k, v in mol1.composition.items()}
                    },
                    'structure': f"{mol1.structure}-{mol2.structure}",
                    'energy': mol1.energy + mol2.energy - 20,  # Bond formation releases energy
                    'reactive_sites': ['peptide_bond']
                }
                reactions.append(dipeptide)

        # Nucleotide polymerization
        elif mol1.type == PrebioticMolecule.NUCLEOTIDE and mol2.type == PrebioticMolecule.NUCLEOTIDE:
            if random.random() < 0.005:  # 0.5% probability
                dinucleotide = {
                    'type': PrebioticMolecule.POLYMER,
                    'composition': {
                        **mol1.composition,
                        **{k: mol2.composition.get(k, 0) + v for k, v in mol1.composition.items()}
                    },
                    'structure': f"{mol1.structure}-{mol2.structure}",
                    'energy': mol1.energy + mol2.energy - 25,
                    'reactive_sites': ['phosphodiester_bond']
                }
                reactions.append(dinucleotide)

        # Lipid bilayer formation
        elif mol1.type == PrebioticMolecule.LIPID and mol2.type == PrebioticMolecule.LIPID:
            if random.random() < 0.02:  # 2% probability
                bilayer = {
                    'type': PrebioticMolecule.POLYMER,
                    'composition': {
                        **mol1.composition,
                        **{k: mol2.composition.get(k, 0) + v for k, v in mol1.composition.items()}
                    },
                    'structure': f"({mol1.structure})₂",
                    'energy': mol1.energy + mol2.energy - 30,
                    'reactive_sites': ['hydrophobic_interaction']
                }
                reactions.append(bilayer)

        return reactions if reactions else None

    def _apply_environmental_effects(self, molecules: List[Molecule], dt: float) -> List[Molecule]:
        """Apply environmental effects on molecules"""
        for molecule in molecules:
            # Temperature effects
            if self.temperature > 80:  # High temperature degradation
                if random.random() < dt * 0.01:
                    molecule.energy += 50  # Increase energy (degradation)

            # pH effects
            if abs(self.ph - 7.0) > 2:  # Extreme pH
                if random.random() < dt * 0.005:
                    molecule.energy += 20

            # UV radiation (simplified)
            if random.random() < dt * 0.001:
                molecule.energy += random.uniform(0, 100)

        return molecules

    def _remove_degraded_molecules(self, molecules: List[Molecule]) -> List[Molecule]:
        """Remove molecules that have degraded"""
        stable_molecules = []
        for molecule in molecules:
            # Degradation threshold
            if molecule.type == PrebioticMolecule.SIMPLE_ORGANIC:
                threshold = 0
            elif molecule.type == PrebioticMolecule.AMINO_ACID:
                threshold = -400
            elif molecule.type == PrebioticMolecule.NUCLEOTIDE:
                threshold = 200
            else:
                threshold = -1000

            if molecule.energy < threshold:
                stable_molecules.append(molecule)

        return stable_molecules

    def _analyze_composition(self, molecules: List[Molecule]) -> Dict[str, int]:
        """Analyze composition of molecular mixture"""
        composition = defaultdict(int)
        for molecule in molecules:
            composition[molecule.type.value] += 1
        return dict(composition)

    def _calculate_chemical_complexity(self, molecules: List[Molecule]) -> float:
        """Calculate chemical complexity of mixture"""
        if not molecules:
            return 0.0

        # Count different molecule types
        type_diversity = len(set(mol.type for mol in molecules))
        size_diversity = len(set(len(mol.composition) for mol in molecules))
        polymer_count = sum(1 for mol in molecules if mol.type == PrebioticMolecule.POLYMER)

        # Complexity score
        complexity = (type_diversity * 0.3 + size_diversity * 0.3 + polymer_count * 0.4)

        return complexity

    def form_protocells(self, molecules: List[Molecule], protocell_type: ProtocellType,
                       target_count: int) -> List[Protocell]:
        """Form protocells from available molecules"""
        print(f"🫧 Forming protocells")
        print(f"   Type: {protocell_type.value}")
        print(f"   Target count: {target_count}")

        # Select appropriate molecules for membrane
        if protocell_type == ProtocellType.LIPOID_VESICLE:
            membrane_molecules = [mol for mol in molecules if mol.type == PrebioticMolecule.LIPID]
        elif protocell_type == ProtocellType.COACERVATE:
            membrane_molecules = [mol for mol in molecules if mol.type in [PrebioticMolecule.AMINO_ACID, PrebioticMolecule.POLYMER]]
        else:
            membrane_molecules = molecules[:100]  # Use first 100 molecules

        protocells = []
        for i in range(target_count):
            if len(membrane_molecules) < 20:  # Minimum molecules for protocell
                break

            # Create protocell
            protocell_id = f"protocell_{protocell_type.value}_{i:04d}"
            membrane_size = random.randint(20, min(100, len(membrane_molecules) // 2))
            protocell_membrane = membrane_molecules[:membrane_size]

            # Interior molecules
            interior_size = random.randint(10, 50)
            interior_molecules = random.sample(molecules, min(interior_size, len(molecules)))

            # Calculate size and volume
            size = random.uniform(50, 200)  # nm diameter
            volume = (4/3) * math.pi * (size/2)**3  # nm³

            protocell = Protocell(
                id=protocell_id,
                type=protocell_type,
                membrane=protocell_membrane,
                interior=interior_molecules,
                size=size,
                volume=volume,
                ph=self.ph + random.uniform(-1, 1),
                temperature=self.temperature + random.uniform(-5, 5),
                energy_level=random.uniform(0.3, 0.8),
                division_threshold=random.uniform(0.7, 0.9),
                genetic_material=None,
                metabolic_reactions=[],
                age=0.0
            )

            protocells.append(protocell)

            # Remove used molecules
            membrane_molecules = membrane_molecules[membrane_size:]

        print(f"   Protocells formed: {len(protocells)}")
        return protocells

    def simulate_early_life(self, protocells: List[Protocell], duration: float,
                          scenario: str = 'rna_world') -> List[SyntheticCell]:
        """Simulate emergence of early life from protocells"""
        print(f"🧬 Simulating early life emergence")
        print(f"   Scenario: {scenario}")
        print(f"   Initial protocells: {len(protocells)}")
        print(f"   Duration: {duration} seconds")

        if scenario in self.abiogenesis_scenarios:
            scenario_func = self.abiogenesis_scenarios[scenario]
            synthetic_cells = scenario_func(protocells, duration)
        else:
            synthetic_cells = []

        print(f"   Living cells created: {len(synthetic_cells)}")
        return synthetic_cells

    def _rna_world_scenario(self, protocells: List[Protocell], duration: float) -> List[SyntheticCell]:
        """RNA world abiogenesis scenario"""
        synthetic_cells = []

        for protocell in protocells:
            # Check for RNA molecules in protocell
            rna_molecules = [mol for mol in protocell.interior if mol.type == PrebioticMolecule.POLYMER and 'nucleotide' in mol.structure]

            if len(rna_molecules) >= 3:  # Minimum RNA for ribozyme activity
                # Create simple genetic system
                genetic_code = self._create_rna_genetic_code(rna_molecules)

                # Create simple metabolism
                metabolic_pathways = self._create_rna_metabolism(protocell)

                # Form synthetic cell
                cell = SyntheticCell(
                    id=f"rna_cell_{protocell.id}",
                    protocell=protocell,
                    genome=genetic_code,
                    metabolism=metabolic_pathways,
                    proteins=[],
                    rna=rna_molecules,
                    organelles=[],
                    life_status=True,
                    reproduction_rate=random.uniform(0.001, 0.01),
                    fitness=random.uniform(0.1, 0.3),
                    complexity=self._calculate_cell_complexity(protocell, genetic_code, metabolic_pathways)
                )

                if cell.complexity > self.min_complexity_for_life:
                    synthetic_cells.append(cell)
                    self.life_registry[cell.id] = cell

        return synthetic_cells

    def _metabolism_first_scenario(self, protocells: List[Protocell], duration: float) -> List[SyntheticCell]:
        """Metabolism-first abiogenesis scenario"""
        synthetic_cells = []

        for protocell in protocells:
            # Create autocatalytic metabolic network
            metabolic_pathways = self._create_autocatalytic_metabolism(protocell)

            if metabolic_pathways:
                # Create genetic system later
                genetic_code = self._create_simple_genetic_code()

                cell = SyntheticCell(
                    id=f"metabolism_cell_{protocell.id}",
                    protocell=protocell,
                    genome=genetic_code,
                    metabolism=metabolic_pathways,
                    proteins=[],
                    rna=[],
                    organelles=[],
                    life_status=True,
                    reproduction_rate=random.uniform(0.005, 0.02),
                    fitness=random.uniform(0.2, 0.4),
                    complexity=self._calculate_cell_complexity(protocell, genetic_code, metabolic_pathways)
                )

                if cell.complexity > self.min_complexity_for_life:
                    synthetic_cells.append(cell)
                    self.life_registry[cell.id] = cell

        return synthetic_cells

    def _lipid_world_scenario(self, protocells: List[Protocell], duration: float) -> List[SyntheticCell]:
        """Lipid world abiogenesis scenario"""
        synthetic_cells = []

        for protocell in protocells:
            if protocell.type == ProtocellType.LIPOID_VESICLE:
                # Growth and division based on lipid incorporation
                growth_rate = random.uniform(0.001, 0.005)
                protocell.size += growth_rate * duration

                # Check for division
                if protocell.size > protocell.division_threshold * 100:
                    # Create daughter cell
                    daughter_protocell = self._divide_protocell(protocell)

                    # Simple genetic system
                    genetic_code = self._create_simple_genetic_code()
                    metabolic_pathways = []

                    cell = SyntheticCell(
                        id=f"lipid_cell_{protocell.id}",
                        protocell=daughter_protocell,
                        genome=genetic_code,
                        metabolism=metabolic_pathways,
                        proteins=[],
                        rna=[],
                        organelles=[],
                        life_status=True,
                        reproduction_rate=0.01,
                        fitness=random.uniform(0.1, 0.3),
                        complexity=50  # Simple complexity
                    )

                    synthetic_cells.append(cell)
                    self.life_registry[cell.id] = cell

        return synthetic_cells

    def _create_rna_genetic_code(self, rna_molecules: List[Molecule]) -> GeneticCode:
        """Create RNA-based genetic code"""
        # Simplified RNA codon table
        codon_table = {
            'AAA': 'lysine',
            'AAC': 'asparagine',
            'AAG': 'lysine',
            'AAU': 'asparagine',
            'ACA': 'threonine',
            'ACC': 'threonine',
            'ACG': 'threonine',
            'ACU': 'threonine',
            # Add more codons as needed
        }

        amino_acids = list(set(codon_table.values()))

        return GeneticCode(
            codon_table=codon_table,
            amino_acids=amino_acids,
            code_degeneracy={aa: sum(1 for codon, aa_name in codon_table.items() if aa_name == aa) for aa in amino_acids},
            error_tolerance=0.1,
            redundancy=0.3,
            evolution_history=['RNA world origin']
        )

    def _create_simple_genetic_code(self) -> GeneticCode:
        """Create simple genetic code"""
        # Very simplified code
        codon_table = {
            'A': 'simple_protein_1',
            'C': 'simple_protein_2',
            'G': 'simple_protein_3',
            'U': 'simple_protein_4'
        }

        amino_acids = list(codon_table.values())

        return GeneticCode(
            codon_table=codon_table,
            amino_acids=amino_acids,
            code_degeneracy={aa: 1 for aa in amino_acids},
            error_tolerance=0.2,
            redundancy=0.1,
            evolution_history=['simple origin']
        )

    def _create_rna_metabolism(self, protocell: Protocell) -> List[MetabolicPathway]:
        """Create RNA-based metabolic pathways"""
        pathways = []

        # Simple RNA catalysis
        rna_catalysis = MetabolicPathway(
            id="rna_catalysis",
            name="RNA Catalysis",
            reactions=[
                {'substrates': ['substrate'], 'products': ['product'], 'catalyst': 'ribozyme', 'rate': 0.1}
            ],
            enzymes=[mol for mol in protocell.interior if mol.type == PrebioticMolecule.POLYMER],
            cofactors=[],
            energy_yield=5.0,
            thermodynamics={'delta_g': -10.0}
        )
        pathways.append(rna_catalysis)

        return pathways

    def _create_autocatalytic_metabolism(self, protocell: Protocell) -> List[MetabolicPathway]:
        """Create autocatalytic metabolic network"""
        pathways = []

        # Formose reaction (sugar synthesis)
        formose_reaction = MetabolicPathway(
            id="formose",
            name="Formose Reaction",
            reactions=[
                {'substrates': ['formaldehyde'], 'products': ['glycolaldehyde'], 'rate': 0.05},
                {'substrates': ['glycolaldehyde', 'formaldehyde'], 'products': ['glyceraldehyde'], 'rate': 0.03}
            ],
            enzymes=[],
            cofactors=[mol for mol in protocell.interior if mol.type == PrebioticMolecule.METAL_ION],
            energy_yield=2.0,
            thermodynamics={'delta_g': -5.0}
        )
        pathways.append(formose_reaction)

        return pathways

    def _divide_protocell(self, protocell: Protocell) -> Protocell:
        """Divide protocell into daughter cells"""
        # Create daughter protocell with half the molecules
        membrane_half = protocell.membrane[:len(protocell.membrane)//2]
        interior_half = protocell.interior[:len(protocell.interior)//2]

        daughter = Protocell(
            id=f"{protocell.id}_daughter",
            type=protocell.type,
            membrane=membrane_half,
            interior=interior_half,
            size=protocell.size / 2,
            volume=protocell.volume / 8,
            ph=protocell.ph,
            temperature=protocell.temperature,
            energy_level=protocell.energy_level,
            division_threshold=protocell.division_threshold,
            genetic_material=None,
            metabolic_reactions=[],
            age=0.0
        )

        return daughter

    def _calculate_cell_complexity(self, protocell: Protocell, genome: Optional[GeneticCode],
                                 metabolism: List[MetabolicPathway]) -> float:
        """Calculate complexity score of synthetic cell"""
        complexity = 0.0

        # Membrane complexity
        complexity += len(protocell.membrane) * 0.1

        # Interior complexity
        complexity += len(protocell.interior) * 0.1

        # Genetic complexity
        if genome:
            complexity += len(genome.codon_table) * 2.0
            complexity += len(genome.amino_acids) * 1.0

        # Metabolic complexity
        complexity += len(metabolism) * 5.0
        for pathway in metabolism:
            complexity += len(pathway.reactions) * 0.5

        return complexity

    def _miller_urey_reactions(self, molecules: List[Molecule], dt: float) -> List[Molecule]:
        """Miller-Urey prebiotic reactions"""
        # Simplified implementation
        return molecules

    def _formose_reactions(self, molecules: List[Molecule], dt: float) -> List[Molecule]:
        """Formose reaction (sugar synthesis)"""
        return molecules

    def _prebiotic_synthesis_reactions(self, molecules: List[Molecule], dt: float) -> List[Molecule]:
        """General prebiotic synthesis reactions"""
        return molecules

    def _polymerization_reactions(self, molecules: List[Molecule], dt: float) -> List[Molecule]:
        """Polymerization reactions"""
        return molecules

    def _clay_hypothesis_scenario(self, protocells: List[Protocell], duration: float) -> List[SyntheticCell]:
        """Clay hypothesis abiogenesis scenario"""
        # Similar to RNA world but with clay surface catalysis
        return self._rna_world_scenario(protocells, duration)

    def _hydrothermal_vent_scenario(self, protocells: List[Protocell], duration: float) -> List[SyntheticCell]:
        """Hydrothermal vent abiogenesis scenario"""
        # High temperature, pressure environment
        self.temperature = 80.0
        self.pressure = 200.0
        return self._metabolism_first_scenario(protocells, duration)

    def _synthetic_creation_scenario(self, protocells: List[Protocell], duration: float) -> List[SyntheticCell]:
        """Synthetic life creation scenario"""
        synthetic_cells = []

        for protocell in protocells:
            # Create fully designed synthetic cell
            genetic_code = self._create_synthetic_genetic_code()
            metabolic_pathways = self._create_synthetic_metabolism()

            cell = SyntheticCell(
                id=f"synthetic_cell_{protocell.id}",
                protocell=protocell,
                genome=genetic_code,
                metabolism=metabolic_pathways,
                proteins=self._create_synthetic_proteins(),
                rna=self._create_synthetic_rna(),
                organelles=self._create_synthetic_organelles(),
                life_status=True,
                reproduction_rate=0.05,
                fitness=0.8,
                complexity=200  # High complexity for synthetic design
            )

            synthetic_cells.append(cell)
            self.life_registry[cell.id] = cell

        return synthetic_cells

    def _create_synthetic_genetic_code(self) -> GeneticCode:
        """Create synthetic genetic code with expanded codons"""
        # Expanded genetic code with synthetic amino acids
        codon_table = {
            'AAA': 'lysine',
            'AAC': 'asparagine',
            'AAG': 'lysine',
            'AAU': 'asparagine',
            'NNN': 'synthetic_amino_acid_1',  # Synthetic codon
            'XYZ': 'synthetic_amino_acid_2',  # Another synthetic codon
        }

        amino_acids = list(codon_table.values())

        return GeneticCode(
            codon_table=codon_table,
            amino_acids=amino_acids,
            code_degeneracy={aa: 2 for aa in amino_acids},
            error_tolerance=0.05,  # Low error rate
            redundancy=0.8,  # High redundancy
            evolution_history=['synthetic_design']
        )

    def _create_synthetic_metabolism(self) -> List[MetabolicPathway]:
        """Create synthetic metabolic pathways"""
        pathways = []

        # Synthetic photosynthesis
        synthetic_photosynthesis = MetabolicPathway(
            id="synthetic_photosynthesis",
            name="Synthetic Photosynthesis",
            reactions=[
                {'substrates': ['CO2', 'H2O', 'light'], 'products': ['glucose', 'O2'], 'rate': 0.2}
            ],
            enzymes=[],
            cofactors=[],
            energy_yield=50.0,
            thermodynamics={'delta_g': -2800.0}
        )
        pathways.append(synthetic_photosynthesis)

        # Synthetic nitrogen fixation
        nitrogen_fixation = MetabolicPathway(
            id="synthetic_nitrogen_fixation",
            name="Synthetic Nitrogen Fixation",
            reactions=[
                {'substrates': ['N2', 'H2'], 'products': ['NH3'], 'rate': 0.05}
            ],
            enzymes=[],
            cofactors=[],
            energy_yield=15.0,
            thermodynamics={'delta_g': -30.0}
        )
        pathways.append(nitrogen_fixation)

        return pathways

    def _create_synthetic_proteins(self) -> List[Molecule]:
        """Create synthetic proteins"""
        proteins = []
        for i in range(10):
            protein = Molecule(
                id=f"synthetic_protein_{i:02d}",
                type=PrebioticMolecule.POLYMER,
                composition={'C': 100, 'H': 150, 'N': 25, 'O': 30, 'S': 2},
                structure="synthetic_protein_structure",
                energy=-5000.0,
                concentration=0.01,
                position=np.random.randn(3) * 50,
                velocity=np.random.randn(3) * 10,
                reactive_sites=['active_site', 'binding_site'],
                catalytic_properties={'activity': 0.8}
            )
            proteins.append(protein)
        return proteins

    def _create_synthetic_rna(self) -> List[Molecule]:
        """Create synthetic RNA molecules"""
        rna_molecules = []
        for i in range(20):
            rna = Molecule(
                id=f"synthetic_rna_{i:02d}",
                type=PrebioticMolecule.POLYMER,
                composition={'C': 50, 'H': 60, 'N': 15, 'O': 25, 'P': 10},
                structure="synthetic_rna_structure",
                energy=-2000.0,
                concentration=0.01,
                position=np.random.randn(3) * 50,
                velocity=np.random.randn(3) * 10,
                reactive_sites=['ribozyme_active_site'],
                catalytic_properties={'catalysis_rate': 0.6}
            )
            rna_molecules.append(rna)
        return rna_molecules

    def _create_synthetic_organelles(self) -> List[Dict]:
        """Create synthetic organelles"""
        organelles = [
            {'type': 'synthetic_nucleus', 'function': 'genetic_storage', 'efficiency': 0.9},
            {'type': 'synthetic_mitochondria', 'function': 'energy_production', 'efficiency': 0.85},
            {'type': 'synthetic_chloroplast', 'function': 'photosynthesis', 'efficiency': 0.8},
            {'type': 'synthetic_ribosome', 'function': 'protein_synthesis', 'efficiency': 0.95}
        ]
        return organelles

    def evolve_life(self, initial_cells: List[SyntheticCell], generations: int) -> List[SyntheticCell]:
        """Evolve synthetic life over multiple generations"""
        print(f"🧬 Evolving synthetic life")
        print(f"   Initial cells: {len(initial_cells)}")
        print(f"   Generations: {generations}")

        current_population = initial_cells.copy()
        evolution_history = []

        for generation in range(generations):
            # Selection based on fitness
            current_population.sort(key=lambda cell: cell.fitness, reverse=True)
            survivors = current_population[:len(current_population)//2]  # Keep top 50%

            # Reproduction with mutation
            offspring = []
            for cell in survivors:
                if random.random() < cell.reproduction_rate * 10:  # Increased reproduction probability
                    child = self._reproduce_cell(cell)
                    offspring.append(child)

            # Combine survivors and offspring
            current_population = survivors + offspring

            # Record generation statistics
            avg_fitness = np.mean([cell.fitness for cell in current_population])
            avg_complexity = np.mean([cell.complexity for cell in current_population])

            evolution_history.append({
                'generation': generation,
                'population_size': len(current_population),
                'avg_fitness': avg_fitness,
                'avg_complexity': avg_complexity
            })

            if generation % 10 == 0:
                print(f"   Generation {generation}: Population = {len(current_population)}, "
                      f"Avg fitness = {avg_fitness:.3f}")

        print(f"   Final population: {len(current_population)}")
        return current_population

    def _reproduce_cell(self, parent: SyntheticCell) -> SyntheticCell:
        """Reproduce cell with mutations"""
        # Create copy of parent
        child_id = f"{parent.id}_gen_{random.randint(1000, 9999)}"
        child_protocell = Protocell(
            id=f"{child_id}_protocell",
            type=parent.protocell.type,
            membrane=parent.protocell.membrane.copy(),
            interior=parent.protocell.interior.copy(),
            size=parent.protocell.size * random.uniform(0.9, 1.1),
            volume=parent.protocell.volume * random.uniform(0.8, 1.2),
            ph=parent.protocell.ph + random.uniform(-0.5, 0.5),
            temperature=parent.protocell.temperature + random.uniform(-2, 2),
            energy_level=parent.protocell.energy_level * random.uniform(0.8, 1.0),
            division_threshold=parent.protocell.division_threshold,
            genetic_material=None,
            metabolic_reactions=[],
            age=0.0
        )

        # Mutate genome
        child_genome = self._mutate_genome(parent.genome) if parent.genome else None

        # Mutate metabolism
        child_metabolism = self._mutate_metabolism(parent.metabolism)

        child = SyntheticCell(
            id=child_id,
            protocell=child_protocell,
            genome=child_genome,
            metabolism=child_metabolism,
            proteins=parent.proteins.copy(),
            rna=parent.rna.copy(),
            organelles=parent.organelles.copy(),
            life_status=True,
            reproduction_rate=parent.reproduction_rate * random.uniform(0.8, 1.2),
            fitness=parent.fitness * random.uniform(0.9, 1.1),
            complexity=parent.complexity * random.uniform(0.95, 1.05)
        )

        self.life_registry[child_id] = child
        return child

    def _mutate_genome(self, genome: GeneticCode) -> GeneticCode:
        """Apply mutations to genetic code"""
        # Point mutations in codon table
        mutated_codons = {}
        for codon, amino_acid in genome.codon_table.items():
            if random.random() < self.mutation_rate * 1000:  # Increased mutation rate for evolution
                # Change codon mapping
                mutated_codons[codon] = random.choice(list(genome.amino_acids))
            else:
                mutated_codons[codon] = amino_acid

        return GeneticCode(
            codon_table=mutated_codons,
            amino_acids=genome.amino_acids,
            code_degeneracy=genome.code_degeneracy,
            error_tolerance=genome.error_tolerance * random.uniform(0.9, 1.1),
            redundancy=genome.redundancy,
            evolution_history=genome.evolution_history + ['mutation']
        )

    def _mutate_metabolism(self, metabolism: List[MetabolicPathway]) -> List[MetabolicPathway]:
        """Apply mutations to metabolic pathways"""
        mutated_metabolism = []

        for pathway in metabolism:
            # Mutate reaction rates
            mutated_reactions = []
            for reaction in pathway.reactions:
                mutated_reaction = reaction.copy()
                mutated_reaction['rate'] *= random.uniform(0.8, 1.2)
                mutated_reactions.append(mutated_reaction)

            mutated_pathway = MetabolicPathway(
                id=pathway.id,
                name=pathway.name,
                reactions=mutated_reactions,
                enzymes=pathway.enzymes,
                cofactors=pathway.cofactors,
                energy_yield=pathway.energy_yield * random.uniform(0.9, 1.1),
                thermodynamics=pathway.thermodynamics
            )
            mutated_metabolism.append(mutated_pathway)

        return mutated_metabolism

def main():
    """Demonstration of life creation engine"""
    print("🌱 Life Creation Engine - Abiogenesis and Synthetic Life Generation")
    print("=" * 80)

    life_engine = LifeCreationEngine()

    # Create prebiotic environment
    print(f"\n🌍 Creating prebiotic environment")

    molecule_concentrations = {
        'methane': 0.01,  # M
        'ammonia': 0.005,
        'hydrogen_cyanide': 0.001,
        'water': 55.5,
        'carbon_dioxide': 0.0005,
        'nitrogen': 0.001,
        'hydrogen_sulfide': 0.0001
    }

    prebiotic_molecules = life_engine.create_prebiotic_environment(
        environment_type="primordial_soup",
        volume=1.0,  # 1 liter
        molecule_concentrations=molecule_concentrations
    )

    # Simulate chemical evolution
    print(f"\n⚗️ Simulating chemical evolution")

    evolved_molecules, chemical_history = life_engine.simulate_chemical_evolution(
        molecules=prebiotic_molecules,
        duration=10.0,  # 10 seconds (representing much longer time)
        dt=0.01
    )

    # Analyze chemical evolution results
    if chemical_history:
        final_state = chemical_history[-1]
        print(f"   Final chemical complexity: {final_state['complexity']:.2f}")
        print(f"   Total molecule types: {len(final_state['composition'])}")

    # Form protocells
    print(f"\n🫧 Forming protocells")

    protocells = life_engine.form_protocells(
        molecules=evolved_molecules,
        protocell_type=ProtocellType.LIPOID_VESICLE,
        target_count=50
    )

    # Test different abiogenesis scenarios
    print(f"\n🧬 Testing abiogenesis scenarios")

    scenarios = ['rna_world', 'metabolism_first', 'synthetic_creation']
    all_cells = {}

    for scenario in scenarios:
        print(f"\n   Testing {scenario} scenario")
        cells = life_engine.simulate_early_life(protocells[:20], duration=5.0, scenario=scenario)
        all_cells[scenario] = cells
        print(f"   Cells created: {len(cells)}")

        if cells:
            avg_complexity = np.mean([cell.complexity for cell in cells])
            avg_fitness = np.mean([cell.fitness for cell in cells])
            print(f"   Average complexity: {avg_complexity:.1f}")
            print(f"   Average fitness: {avg_fitness:.3f}")

    # Evolve the most successful scenario
    best_scenario = max(all_cells.keys(), key=lambda k: len(all_cells[k]))
    best_cells = all_cells[best_scenario]

    if best_cells:
        print(f"\n🧬 Evolving life from {best_scenario} scenario")

        evolved_cells = life_engine.evolve_life(best_cells, generations=50)

        # Analyze evolution results
        final_population = len(evolved_cells)
        if final_population > 0:
            final_avg_fitness = np.mean([cell.fitness for cell in evolved_cells])
            final_avg_complexity = np.mean([cell.complexity for cell in evolved_cells])
            max_complexity = max(cell.complexity for cell in evolved_cells)

            print(f"   Final population: {final_population}")
            print(f"   Final average fitness: {final_avg_fitness:.3f}")
            print(f"   Final average complexity: {final_avg_complexity:.1f}")
            print(f"   Maximum complexity: {max_complexity:.1f}")

            # Find most evolved cell
            most_evolved = max(evolved_cells, key=lambda cell: cell.complexity)
            print(f"   Most evolved cell: {most_evolved.id}")
            print(f"      Complexity: {most_evolved.complexity:.1f}")
            print(f"      Fitness: {most_evolved.fitness:.3f}")
            print(f"      Reproduction rate: {most_evolved.reproduction_rate:.4f}")

    # Export results
    results = {
        'prebiotic_environment': {
            'initial_molecules': len(prebiotic_molecules),
            'evolved_molecules': len(evolved_molecules),
            'complexity_increase': final_state['complexity'] if chemical_history else 0
        },
        'protocells_formed': len(protocells),
        'abiogenesis_scenarios_tested': scenarios,
        'cells_created_per_scenario': {scenario: len(cells) for scenario, cells in all_cells.items()},
        'most_successful_scenario': best_scenario,
        'evolution_results': {
            'initial_population': len(best_cells),
            'final_population': final_population if best_cells else 0,
            'generations': 50,
            'final_avg_fitness': final_avg_fitness if best_cells else 0,
            'final_avg_complexity': final_avg_complexity if best_cells else 0,
            'max_complexity': max_complexity if best_cells else 0
        },
        'total_life_forms_created': sum(len(cells) for cells in all_cells.values())
    }

    with open('/home/activeloguser/DMLogn8n/biology/synthetic/life_creation_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✨ Life creation engine demonstration complete!")
    print(f"   Initial prebiotic molecules: {len(prebiotic_molecules)}")
    print(f"   Evolved molecules: {len(evolved_molecules)}")
    print(f"   Protocells formed: {len(protocells)}")
    print(f"   Total life forms created: {results['total_life_forms_created']}")
    print(f"   Most successful scenario: {best_scenario}")
    print(f"   Maximum complexity achieved: {results['evolution_results']['max_complexity']:.1f}")
    print(f"   Results exported to: life_creation_results.json")

if __name__ == "__main__":
    main()