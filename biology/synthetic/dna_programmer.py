#!/usr/bin/env python3
"""
DNA Programmer - Revolutionary Genetic Code Design System
Design custom DNA sequences and genetic programs with base-level precision

This system allows players to:
- Design custom DNA sequences with nucleotide precision
- Create synthetic genetic programs with complex logic
- Optimize genetic circuits for specific functions
- Design novel amino acids and codon assignments
- Simulate gene expression and regulation
- Create synthetic organisms with custom genomes
"""

import numpy as np
import random
import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
from collections import defaultdict
import hashlib

class Nucleotide(Enum):
    """DNA nucleotides including synthetic bases"""
    ADENINE = 'A'
    THYMINE = 'T'
    GUANINE = 'G'
    CYTOSINE = 'C'
    # Synthetic nucleotides
    URACIL = 'U'  # RNA-specific
    XANTHINE = 'X'  # Synthetic base
    ISOADENINE = 'I'  # Modified adenine
    THIOCYTOSINE = 'S'  # Modified cytosine
    FLUOROTHYMINE = 'F'  # Fluorinated thymine
    AMINOPURINE = 'P'  # Synthetic purine

class AminoAcidType(Enum):
    """Standard and synthetic amino acids"""
    # Standard amino acids
    PHENYLALANINE = 'F'
    LEUCINE = 'L'
    ISOLEUCINE = 'I'
    METHIONINE = 'M'
    VALINE = 'V'
    SERINE = 'S'
    PROLINE = 'P'
    THREONINE = 'T'
    ALANINE = 'A'
    TYROSINE = 'Y'
    HISTIDINE = 'H'
    GLUTAMINE = 'N'
    ASPARAGINE = 'D'
    LYSINE = 'K'
    GLUTAMIC_ACID = 'E'
    ARGININE = 'R'
    CYSTEINE = 'C'
    TRYPTOPHAN = 'W'
    GLYCINE = 'G'

    # Synthetic amino acids
    Selenocysteine = 'U'
    Pyrrolysine = 'O'
    Bicyclononane = 'B'  # Synthetic cyclic amino acid
    Fluorophenylalanine = 'X'  # Fluorinated amino acid
    Azidophenylalanine = 'Z'  # Contains azide group
    Hydroxyproline = 'H'  # Modified proline
    Methyllysine = 'M'  # Methylated lysine
    Phosphoserine = 'P'  # Phosphorylated serine

@dataclass
class GeneticCircuit:
    """Genetic circuit with regulatory elements"""
    promoter: str
    ribosome_binding_site: str
    coding_sequence: str
    terminator: str
    regulatory_elements: List[str]
    circuit_type: str  # 'AND', 'OR', 'NOT', 'oscillator', 'toggle'

@dataclass
class SyntheticGenome:
    """Complete synthetic genome"""
    species_name: str
    genome_size: int  # in base pairs
    chromosomes: Dict[str, str]  # chromosome name -> DNA sequence
    gene_circuits: List[GeneticCircuit]
    metabolic_pathways: List[str]
    codon_table: Dict[str, AminoAcidType]
    gc_content: float
    replication_origin: str

class DNAProgrammer:
    """Advanced DNA programming and genetic design system"""

    def __init__(self):
        # Standard codon table
        self.standard_codons = {
            'UUU': 'F', 'UUC': 'F', 'UUA': 'L', 'UUG': 'L',
            'UCU': 'S', 'UCC': 'S', 'UCA': 'S', 'UCG': 'S',
            'UAU': 'Y', 'UAC': 'Y', 'UAA': '*', 'UAG': '*',
            'UGU': 'C', 'UGC': 'C', 'UGA': '*', 'UGG': 'W',
            'CUU': 'L', 'CUC': 'L', 'CUA': 'L', 'CUG': 'L',
            'CCU': 'P', 'CCC': 'P', 'CCA': 'P', 'CCG': 'P',
            'CAU': 'H', 'CAC': 'H', 'CAA': 'Q', 'CAG': 'Q',
            'CGU': 'R', 'CGC': 'R', 'CGA': 'R', 'CGG': 'R',
            'AUU': 'I', 'AUC': 'I', 'AUA': 'I', 'AUG': 'M',
            'ACU': 'T', 'ACC': 'T', 'ACA': 'T', 'ACG': 'T',
            'AAU': 'N', 'AAC': 'N', 'AAA': 'K', 'AAG': 'K',
            'AGU': 'S', 'AGC': 'S', 'AGA': 'R', 'AGG': 'R',
            'GUU': 'V', 'GUC': 'V', 'GUA': 'V', 'GUG': 'V',
            'GCU': 'A', 'GCC': 'A', 'GCA': 'A', 'GCG': 'A',
            'GAU': 'D', 'GAC': 'D', 'GAA': 'E', 'GAG': 'E',
            'GGU': 'G', 'GGC': 'G', 'GGA': 'G', 'GGG': 'G'
        }

        # Genetic code properties
        self.codon_usage_bias = self._initialize_codon_bias()
        self.regulatory_sequences = self._initialize_regulatory_sequences()
        self.gene_expression_models = {}

        # Design constraints
        self.max_genome_size = 10**9  # 1 billion base pairs
        self.min_gene_length = 100
        self.max_gene_length = 100000

    def _initialize_codon_bias(self) -> Dict[str, float]:
        """Initialize codon usage bias for optimal expression"""
        return {
            'UUU': 0.17, 'UUC': 0.20, 'UUA': 0.07, 'UUG': 0.13,
            'UCU': 0.15, 'UCC': 0.22, 'UCA': 0.12, 'UCG': 0.07,
            'UAU': 0.12, 'UAC': 0.15, 'UAA': 0.01, 'UAG': 0.01,
            'UGU': 0.07, 'UGC': 0.12, 'UGA': 0.01, 'UGG': 0.10,
            'CUU': 0.13, 'CUC': 0.20, 'CUA': 0.07, 'CUG': 0.40,
            'CCU': 0.17, 'CCC': 0.34, 'CCA': 0.27, 'CCG': 0.11,
            'CAU': 0.15, 'CAC': 0.25, 'CAA': 0.34, 'CAG': 0.32,
            'CGU': 0.08, 'CGC': 0.19, 'CGA': 0.07, 'CGG': 0.20,
            'AUU': 0.36, 'AUC': 0.47, 'AUA': 0.11, 'AUG': 0.28,
            'ACU': 0.18, 'ACC': 0.40, 'ACA': 0.15, 'ACG': 0.06,
            'AAU': 0.53, 'AAC': 0.32, 'AAA': 0.43, 'AAG': 0.57,
            'AGU': 0.12, 'AGC': 0.20, 'AGA': 0.07, 'AGG': 0.20,
            'GUU': 0.18, 'GUC': 0.24, 'GUA': 0.11, 'GUG': 0.28,
            'GCU': 0.27, 'GCC': 0.40, 'GCA': 0.16, 'GCG': 0.07,
            'GAU': 0.46, 'GAC': 0.27, 'GAA': 0.68, 'GAG': 0.32,
            'GGU': 0.16, 'GGC': 0.34, 'GGA': 0.33, 'GGG': 0.16
        }

    def _initialize_regulatory_sequences(self) -> Dict[str, List[str]]:
        """Initialize known regulatory sequences"""
        return {
            'promoters': [
                'TATAAA',  # TATA box
                'CAAT',    # CAAT box
                'GGGCGG',  # GC box
                'ATGCAAAT' # Pribnow box
            ],
            'enhancers': [
                'CCCTCCCC',  # Sp1 binding
                'GGGAGGGG',  # G-rich sequences
                'ATTTGCAA'   # NF-κB binding
            ],
            'silencers': [
                'GCGGGGGCG',  # Repressor binding
                'ATATATAT'    # Silencer elements
            ],
            'ribosome_binding_sites': [
                'AGGAGG',  # Shine-Dalgarno sequence
                'AGGAGGU',
                'GGAGGA'
            ]
        }

    def design_dna_sequence(self, length: int, gc_content: float = 0.5,
                           avoid_patterns: List[str] = None) -> str:
        """Design a DNA sequence with specified properties"""
        if avoid_patterns is None:
            avoid_patterns = []

        sequence = []
        gc_pairs = int(length * gc_content)
        at_pairs = length - gc_pairs

        # Generate base pairs
        bases = ['G', 'C'] * gc_pairs + ['A', 'T'] * at_pairs
        random.shuffle(bases)

        sequence = bases

        # Avoid unwanted patterns
        for pattern in avoid_patterns:
            while pattern in ''.join(sequence):
                # Find and replace pattern
                seq_str = ''.join(sequence)
                start = seq_str.find(pattern)
                # Randomize bases in pattern region
                for i in range(start, start + len(pattern)):
                    sequence[i] = random.choice(['A', 'T', 'G', 'C'])

        return ''.join(sequence)

    def create_synthetic_codon_table(self, amino_acids: List[AminoAcidType]) -> Dict[str, AminoAcidType]:
        """Create a custom codon table for synthetic amino acids"""
        codon_table = {}
        available_codons = [f"{a}{b}{c}" for a in 'UCAG' for b in 'UCAG' for c in 'UCAG']

        # Reserve stop codons
        stop_codons = ['UAA', 'UAG', 'UGA']
        for codon in stop_codons:
            codon_table[codon] = None

        # Assign codons to amino acids
        remaining_codons = [c for c in available_codons if c not in stop_codons]
        random.shuffle(remaining_codons)

        codons_per_amino = len(remaining_codons) // len(amino_acids)

        for i, aa in enumerate(amino_acids):
            start_idx = i * codons_per_amino
            end_idx = start_idx + codons_per_amino
            for codon in remaining_codons[start_idx:end_idx]:
                codon_table[codon] = aa

        return codon_table

    def design_gene_circuit(self, circuit_type: str, target_genes: List[str]) -> GeneticCircuit:
        """Design a genetic circuit with specified logic"""
        promoter = self._select_promoter(circuit_type)
        rbs = random.choice(self.regulatory_sequences['ribosome_binding_sites'])

        coding_sequence = self._design_coding_sequence(target_genes)
        terminator = self._design_terminator()

        regulatory_elements = self._design_regulatory_elements(circuit_type)

        return GeneticCircuit(
            promoter=promoter,
            ribosome_binding_site=rbs,
            coding_sequence=coding_sequence,
            terminator=terminator,
            regulatory_elements=regulatory_elements,
            circuit_type=circuit_type
        )

    def _select_promoter(self, circuit_type: str) -> str:
        """Select appropriate promoter for circuit type"""
        promoters = self.regulatory_sequences['promoters']

        if circuit_type == 'constitutive':
            return 'TATAAA'
        elif circuit_type == 'inducible':
            return 'CAAT'
        elif circuit_type == 'oscillator':
            return 'GGGCGG'
        else:
            return random.choice(promoters)

    def _design_coding_sequence(self, genes: List[str]) -> str:
        """Design coding sequence for target genes"""
        coding_regions = []
        for gene in genes:
            # Convert gene name to protein sequence (simplified)
            protein_length = random.randint(100, 1000)
            protein_seq = self._generate_protein_sequence(protein_length)

            # Convert protein to DNA sequence
            dna_seq = self._protein_to_dna(protein_seq)
            coding_regions.append(dna_seq)

        return ''.join(coding_regions)

    def _generate_protein_sequence(self, length: int) -> str:
        """Generate a random protein sequence"""
        amino_acids = list('ACDEFGHIKLMNPQRSTVWY')
        return ''.join(random.choice(amino_acids) for _ in range(length))

    def _protein_to_dna(self, protein: str) -> str:
        """Convert protein sequence to optimized DNA sequence"""
        dna_sequence = []

        for aa in protein:
            # Find optimal codon for this amino acid
            possible_codons = [codon for codon, aa_code in self.standard_codons.items() if aa_code == aa]

            if possible_codons:
                # Select codon based on usage bias
                codon_scores = [(codon, self.codon_usage_bias.get(codon, 0.1)) for codon in possible_codons]
                codon_scores.sort(key=lambda x: x[1], reverse=True)
                optimal_codon = codon_scores[0][0]

                # Convert RNA to DNA
                dna_codon = optimal_codon.replace('U', 'T')
                dna_sequence.append(dna_codon)

        return ''.join(dna_sequence)

    def _design_terminator(self) -> str:
        """Design transcription terminator"""
        # Create hairpin loop followed by poly-U tract
        stem = ''.join(random.choice('GC') for _ in range(6))
        loop = 'TTAA'
        terminator_sequence = stem + loop + self._reverse_complement(stem) + 'TTTTTT'
        return terminator_sequence

    def _reverse_complement(self, sequence: str) -> str:
        """Get reverse complement of DNA sequence"""
        complement = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
        return ''.join(complement[base] for base in reversed(sequence))

    def _design_regulatory_elements(self, circuit_type: str) -> List[str]:
        """Design regulatory elements for circuit"""
        elements = []

        if circuit_type == 'AND':
            elements.extend(['AGGAGG', 'TATAAA'])
        elif circuit_type == 'OR':
            elements.extend(['CAAT', 'GGGCGG'])
        elif circuit_type == 'NOT':
            elements.extend(['GCGGGGGCG'])
        elif circuit_type == 'oscillator':
            elements.extend(['ATGCAAAT', 'ATATATAT'])
        elif circuit_type == 'toggle':
            elements.extend(['AGGAGG', 'ATATATAT'])

        return elements

    def create_synthetic_genome(self, species_name: str, genome_size: int,
                              num_genes: int, include_synthetic_aa: bool = True) -> SyntheticGenome:
        """Create a complete synthetic genome"""
        if genome_size > self.max_genome_size:
            raise ValueError(f"Genome size exceeds maximum of {self.max_genome_size}")

        # Design chromosomes
        chromosomes = {}
        if genome_size < 10**6:  # Small genome - single chromosome
            chr_name = f"{species_name}_chr1"
            chromosomes[chr_name] = self.design_dna_sequence(genome_size)
        else:  # Large genome - multiple chromosomes
            num_chromosomes = min(10, genome_size // 10**6 + 1)
            remaining_size = genome_size

            for i in range(num_chromosomes):
                if i == num_chromosomes - 1:
                    chr_size = remaining_size
                else:
                    chr_size = remaining_size // (num_chromosomes - i)
                    remaining_size -= chr_size

                chr_name = f"{species_name}_chr{i+1}"
                chromosomes[chr_name] = self.design_dna_sequence(chr_size)

        # Design gene circuits
        gene_circuits = []
        circuit_types = ['AND', 'OR', 'NOT', 'oscillator', 'toggle']

        for i in range(num_genes // 10):  # Groups of 10 genes per circuit
            circuit_type = random.choice(circuit_types)
            genes = [f"gene_{j}" for j in range(i*10, min((i+1)*10, num_genes))]
            circuit = self.design_gene_circuit(circuit_type, genes)
            gene_circuits.append(circuit)

        # Design metabolic pathways
        metabolic_pathways = self._design_metabolic_pathways(num_genes)

        # Create codon table
        amino_acids = list(AminoAcidType)[:20]  # Standard amino acids
        if include_synthetic_aa:
            amino_acids.extend(list(AminoAcidType)[20:25])  # Some synthetic ones

        codon_table = self.create_synthetic_codon_table(amino_acids)

        # Calculate GC content
        total_dna = ''.join(chromosomes.values())
        gc_count = total_dna.count('G') + total_dna.count('C')
        gc_content = gc_count / len(total_dna)

        # Design replication origin
        replication_origin = self._design_replication_origin()

        return SyntheticGenome(
            species_name=species_name,
            genome_size=genome_size,
            chromosomes=chromosomes,
            gene_circuits=gene_circuits,
            metabolic_pathways=metabolic_pathways,
            codon_table=codon_table,
            gc_content=gc_content,
            replication_origin=replication_origin
        )

    def _design_metabolic_pathways(self, num_genes: int) -> List[str]:
        """Design metabolic pathways for the synthetic organism"""
        pathways = []

        # Essential pathways
        pathways.extend([
            'glycolysis',
            'citric_acid_cycle',
            'oxidative_phosphorylation',
            'amino_acid_synthesis',
            'nucleotide_synthesis'
        ])

        # Synthetic capabilities
        if num_genes > 1000:
            pathways.extend([
                'bioluminescence',
                'heavy_metal_chelation',
                'synthetic_polymer_production',
                'quantum_dot_synthesis'
            ])

        if num_genes > 5000:
            pathways.extend([
                'neural_signal_processing',
                'electromagnetic_communication',
                'quantum_entanglement_sensing'
            ])

        return pathways

    def _design_replication_origin(self) -> str:
        """Design origin of replication sequence"""
        # AT-rich region for easy strand separation
        at_region = 'AT' * 50
        # Conserved origin sequences
        ori_sequences = [
            'ATTTAATTTAATTTAA',
            'GATCTAGCTAGCTAGCTA',
            'TTATTTATTTATTTAT'
        ]
        return at_region + random.choice(ori_sequences) + at_region

    def analyze_genome_stability(self, genome: SyntheticGenome) -> Dict[str, float]:
        """Analyze genome stability and potential issues"""
        analysis = {}

        # Analyze each chromosome
        for chr_name, sequence in genome.chromosomes.items():
            chr_analysis = {}

            # GC content variation
            window_size = 1000
            gc_contents = []
            for i in range(0, len(sequence) - window_size, window_size):
                window = sequence[i:i + window_size]
                gc_count = window.count('G') + window.count('C')
                gc_contents.append(gc_count / window_size)

            chr_analysis['gc_variance'] = np.var(gc_contents)

            # Repeat content
            repeats = self._find_repeats(sequence)
            chr_analysis['repeat_content'] = len(repeats) / len(sequence)

            # Palindrome content (potential secondary structures)
            palindromes = self._find_palindromes(sequence)
            chr_analysis['palindrome_content'] = len(palindromes) / len(sequence)

            # Codon optimization score
            if len(sequence) >= 3:
                codons = [sequence[i:i+3] for i in range(0, len(sequence)-2, 3)]
                optimization_score = sum(self.codon_usage_bias.get(codon.replace('T', 'U'), 0)
                                       for codon in codons) / len(codons)
                chr_analysis['codon_optimization'] = optimization_score

            analysis[chr_name] = chr_analysis

        return analysis

    def _find_repeats(self, sequence: str, min_length: int = 10) -> List[str]:
        """Find repeated sequences in DNA"""
        repeats = []
        seen = set()

        for length in range(min_length, 50):
            for i in range(len(sequence) - length + 1):
                substring = sequence[i:i + length]
                if substring in seen and substring not in repeats:
                    repeats.append(substring)
                seen.add(substring)

        return repeats

    def _find_palindromes(self, sequence: str, min_length: int = 6) -> List[str]:
        """Find palindromic sequences (potential hairpin loops)"""
        palindromes = []

        for i in range(len(sequence)):
            for j in range(i + min_length, len(sequence)):
                substring = sequence[i:j]
                if substring == self._reverse_complement(substring):
                    palindromes.append(substring)

        return palindromes

    def optimize_genome(self, genome: SyntheticGenome, optimization_goals: Dict[str, float]) -> SyntheticGenome:
        """Optimize genome for specific goals"""
        optimized_genome = SyntheticGenome(
            species_name=genome.species_name + "_optimized",
            genome_size=genome.genome_size,
            chromosomes={},
            gene_circuits=genome.gene_circuits.copy(),
            metabolic_pathways=genome.metabolic_pathways.copy(),
            codon_table=genome.codon_table.copy(),
            gc_content=0.0,
            replication_origin=genome.replication_origin
        )

        # Optimize each chromosome
        for chr_name, sequence in genome.chromosomes.items():
            optimized_sequence = self._optimize_sequence(sequence, optimization_goals)
            optimized_genome.chromosomes[chr_name] = optimized_sequence

        # Recalculate GC content
        total_dna = ''.join(optimized_genome.chromosomes.values())
        gc_count = total_dna.count('G') + total_dna.count('C')
        optimized_genome.gc_content = gc_count / len(total_dna)

        return optimized_genome

    def _optimize_sequence(self, sequence: str, goals: Dict[str, float]) -> str:
        """Optimize DNA sequence for specific goals"""
        optimized = list(sequence)

        # Optimize for expression
        if goals.get('expression', 0) > 0.5:
            # Use preferred codons
            for i in range(0, len(optimized) - 2, 3):
                codon = ''.join(optimized[i:i+3])
                if codon in self.standard_codons:
                    aa = self.standard_codons[codon.replace('T', 'U')]
                    # Find best codon for this amino acid
                    best_codon = max(
                        [(c, self.codon_usage_bias.get(c, 0))
                         for c, a in self.standard_codons.items()
                         if a == aa],
                        key=lambda x: x[1]
                    )[0]
                    optimized[i:i+3] = list(best_codon.replace('U', 'T'))

        # Optimize for stability
        if goals.get('stability', 0) > 0.5:
            # Reduce repeats and palindromes
            repeats = self._find_repeats(sequence)
            for repeat in repeats[:len(repeats)//2]:  # Remove half the repeats
                positions = [i for i in range(len(sequence) - len(repeat) + 1)
                           if sequence[i:i+len(repeat)] == repeat]
                if positions:
                    pos = random.choice(positions)
                    # Randomize the repeat
                    for j in range(pos, pos + len(repeat)):
                        optimized[j] = random.choice(['A', 'T', 'G', 'C'])

        # Optimize GC content
        target_gc = goals.get('gc_content', 0.5)
        current_gc = sum(1 for base in optimized if base in 'GC') / len(optimized)

        if abs(current_gc - target_gc) > 0.1:
            # Adjust GC content
            gc_diff = target_gc - current_gc
            changes_needed = int(abs(gc_diff) * len(optimized))

            if gc_diff > 0:  # Need more GC
                at_positions = [i for i, base in enumerate(optimized) if base in 'AT']
                for pos in random.sample(at_positions, min(changes_needed, len(at_positions))):
                    optimized[pos] = random.choice(['G', 'C'])
            else:  # Need more AT
                gc_positions = [i for i, base in enumerate(optimized) if base in 'GC']
                for pos in random.sample(gc_positions, min(changes_needed, len(gc_positions))):
                    optimized[pos] = random.choice(['A', 'T'])

        return ''.join(optimized)

    def export_genome(self, genome: SyntheticGenome, filename: str):
        """Export genome to file"""
        genome_data = {
            'species_name': genome.species_name,
            'genome_size': genome.genome_size,
            'gc_content': genome.gc_content,
            'chromosomes': genome.chromosomes,
            'gene_circuits': [
                {
                    'promoter': circuit.promoter,
                    'ribosome_binding_site': circuit.ribosome_binding_site,
                    'coding_sequence': circuit.coding_sequence[:100] + '...',  # Truncate for storage
                    'terminator': circuit.terminator,
                    'regulatory_elements': circuit.regulatory_elements,
                    'circuit_type': circuit.circuit_type
                }
                for circuit in genome.gene_circuits
            ],
            'metabolic_pathways': genome.metabolic_pathways,
            'replication_origin': genome.replication_origin,
            'codon_table': {codon: aa.value if aa else None for codon, aa in genome.codon_table.items()}
        }

        with open(filename, 'w') as f:
            json.dump(genome_data, f, indent=2)

    def create_dna_nanotechnology(self, structure_type: str, size: int) -> Dict[str, str]:
        """Design DNA nanostructures"""
        designs = {}

        if structure_type == 'origami':
            designs['scaffold'] = self.design_dna_sequence(size * 1000, gc_content=0.5)
            designs['staples'] = []
            for i in range(200):  # 200 staple strands
                staple_length = random.randint(20, 50)
                staple = self.design_dna_sequence(staple_length, gc_content=0.6)
                designs['staples'].append(staple)

        elif structure_type == 'tetrahedron':
            # DNA tetrahedron with 6 edges
            edge_length = size
            designs['edges'] = []
            for i in range(6):
                edge = self.design_dna_sequence(edge_length, gc_content=0.5)
                designs['edges'].append(edge)

        elif structure_type == 'nanotube':
            # DNA nanotube design
            helix_repeat = 10.5  # base pairs per turn
            tube_length = size
            designs['helix'] = self.design_dna_sequence(tube_length, gc_content=0.5)
            designs['circular_sequence'] = self.design_dna_sequence(int(helix_repeat * 10), gc_content=0.6)

        return designs

    def simulate_gene_expression(self, genome: SyntheticGenome, environmental_conditions: Dict[str, float]) -> Dict[str, float]:
        """Simulate gene expression under environmental conditions"""
        expression_levels = {}

        # Simulate basic expression based on promoter strength
        for circuit in genome.gene_circuits:
            base_expression = self._calculate_promoter_strength(circuit.promoter)

            # Modify based on environmental conditions
            if environmental_conditions.get('temperature', 37) > 40:
                base_expression *= 0.8  # Heat stress
            elif environmental_conditions.get('temperature', 37) < 20:
                base_expression *= 0.6  # Cold stress

            if environmental_conditions.get('ph', 7.0) < 6.0 or environmental_conditions.get('ph', 7.0) > 8.0:
                base_expression *= 0.7  # pH stress

            if environmental_conditions.get('nutrients', 1.0) < 0.5:
                base_expression *= 1.2  # Nutrient limitation increases some genes

            expression_levels[circuit.circuit_type] = base_expression

        return expression_levels

    def _calculate_promoter_strength(self, promoter: str) -> float:
        """Calculate relative promoter strength"""
        promoter_strengths = {
            'TATAAA': 0.8,    # Strong promoter
            'CAAT': 0.6,      # Moderate promoter
            'GGGCGG': 0.9,    # Very strong promoter
            'ATGCAAAT': 0.5   # Weak promoter
        }

        return promoter_strengths.get(promoter, 0.5)

def main():
    """Demonstration of DNA programming capabilities"""
    print("🧬 DNA Programmer - Revolutionary Genetic Code Design System")
    print("=" * 60)

    programmer = DNAProgrammer()

    # Create synthetic genomes
    genomes = [
        ("Bacterium syntheticus", 1000000, 1000),
        ("Archaeus quantumensis", 2000000, 2000),
        ("Eukarya artificialis", 10000000, 5000)
    ]

    for species_name, genome_size, num_genes in genomes:
        print(f"\n🔬 Creating {species_name}")
        print(f"   Genome size: {genome_size:,} bp")
        print(f"   Number of genes: {num_genes:,}")

        genome = programmer.create_synthetic_genome(
            species_name=species_name,
            genome_size=genome_size,
            num_genes=num_genes,
            include_synthetic_aa=True
        )

        # Analyze genome
        stability = programmer.analyze_genome_stability(genome)
        print(f"   GC content: {genome.gc_content:.2%}")
        print(f"   Number of chromosomes: {len(genome.chromosomes)}")
        print(f"   Metabolic pathways: {len(genome.metabolic_pathways)}")

        # Export genome
        filename = f"/home/activeloguser/DMLogn8n/biology/synthetic/{species_name.replace(' ', '_')}.json"
        programmer.export_genome(genome, filename)
        print(f"   Exported to: {filename}")

    # Create DNA nanostructures
    print(f"\n🔧 Creating DNA nanotechnology")

    nanostructures = programmer.create_dna_nanotechnology('origami', 100)
    print(f"   DNA origami: {len(nanostructures['staples'])} staple strands")

    # Simulate gene expression
    print(f"\n🧪 Simulating gene expression")

    conditions = {
        'temperature': 37,
        'ph': 7.0,
        'nutrients': 1.0
    }

    expression = programmer.simulate_gene_expression(genome, conditions)
    for circuit_type, level in expression.items():
        print(f"   {circuit_type}: {level:.2f}")

    print(f"\n✨ DNA programming complete!")
    print(f"   Synthetic genomes created: {len(genomes)}")
    print(f"   Total genetic code designed: {sum(g[1] for g in genomes):,} base pairs")
    print(f"   Synthetic amino acids incorporated: 5")

if __name__ == "__main__":
    main()