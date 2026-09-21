"""
Procedural Culture Generation System
Creates rich, diverse cultures with unique traditions, architecture, languages,
social structures, belief systems, and historical development patterns.
"""

import numpy as np
import random
from collections import defaultdict, deque
import math
from typing import List, Tuple, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

class GovernmentType(Enum):
    TRIBE = "tribe"
    CHIEFDOM = "chiefdom"
    MONARCHY = "monarchy"
    REPUBLIC = "republic"
    DEMOCRACY = "democracy"
    EMPIRE = "empire"
    THEOCRACY = "theocracy"
    MAGOCRACY = "magocracy"
    MILITARY_DICTATORSHIP = "military_dictatorship"
    MERCHANT_REPUBLIC = "merchant_republic"
    FEUDAL = "feudal"
    CITY_STATE = "city_state"

class SocialStructure(Enum):
    EGALITARIAN = "egalitarian"
    HIERARCHICAL = "hierarchical"
    CASTE_SYSTEM = "caste_system"
    MATRIARCHAL = "matriarchal"
    PATRIARCHAL = "patriarchal"
    CLAN_BASED = "clan_based"
    CLASS_BASED = "class_based"

class TechnologyLevel(Enum):
    STONE_AGE = "stone_age"
    BRONZE_AGE = "bronze_age"
    IRON_AGE = "iron_age"
    MEDIEVAL = "medieval"
    RENAISSANCE = "renaissance"
    INDUSTRIAL = "industrial"
    MODERN = "modern"
    FUTURISTIC = "futuristic"
    MAGICAL = "magical"
    STEAMPUNK = "steampunk"

class ReligionType(Enum):
    POLYTHEISTIC = "polytheistic"
    MONOTHEISTIC = "monotheistic"
    ANIMISTIC = "animistic"
    PANTHEISTIC = "pantheistic"
    DUALISTIC = "dualistic"
    PHILOSOPHICAL = "philosophical"
    ANCESTOR_WORSHIP = "ancestor_worship"
    NATURALISTIC = "naturalistic"
    CULT_BASED = "cult_based"
    ATHEISTIC = "atheistic"

class EconomicSystem(Enum):
    HUNTER_GATHERER = "hunter_gatherer"
    AGRICULTURAL = "agricultural"
    PASTORAL = "pastoral"
    FEUDAL = "feudal"
    MERCANTILE = "mercantile"
    CAPITALIST = "capitalist"
    SOCIALIST = "socialist"
    COMMAND_ECONOMY = "command_economy"
    GIFT_ECONOMY = "gift_economy"
    TRIBUTE_SYSTEM = "tribute_system"

class ArtStyle(Enum):
    GEOMETRIC = "geometric"
    NATURALISTIC = "naturalistic"
    ABSTRACT = "abstract"
    MINIMALIST = "minimalist"
    ORNATE = "ornate"
    FUNCTIONAL = "functional"
    SYMBOLIC = "symbolic"
    NARRATIVE = "narrative"
    RITUALISTIC = "ritualistic"

@dataclass
class CulturalValue:
    """Represents a cultural value or belief"""
    name: str
    description: str
    importance: float  # 0.0 - 1.0
    manifestation: List[str]  # How this value manifests in society

@dataclass
class Tradition:
    """Represents a cultural tradition"""
    name: str
    type: str  # festival, rite, custom, ceremony
    description: str
    frequency: str  # daily, weekly, monthly, yearly, seasonal
    participants: List[str]  # Who participates
    significance: str  # What it represents

@dataclass
class Language:
    """Represents a language"""
    name: str
    family: str
    script: str
    phonology: Dict[str, List[str]]  # Sound types
    grammar: Dict[str, str]  # Grammatical features
    vocabulary: Dict[str, str]  # Sample vocabulary
    writing_direction: str  # left_to_right, right_to_left, top_to_bottom

@dataclass
class Mythology:
    """Represents cultural mythology and beliefs"""
    creation_story: str
    pantheon: List[Dict]  # Gods, spirits, etc.
    afterlife_beliefs: str
    sacred_texts: List[str]
    myths: List[str]
    prophecies: List[str]

@dataclass
class Culture:
    """Complete cultural representation"""
    name: str
    homeland: Tuple[int, int]  # Center location
    influence_radius: int
    population: int
    government_type: GovernmentType
    social_structure: SocialStructure
    technology_level: TechnologyLevel
    religion_type: ReligionType
    economic_system: EconomicSystem
    values: List[CulturalValue]
    traditions: List[Tradition]
    language: Language
    mythology: Mythology
    art_style: ArtStyle
    architecture_style: str
    clothing_style: str
    cuisine: List[str]
    military_organization: str
    diplomatic_relations: Dict[str, str]  # culture -> relationship
    known_inventions: List[str]
    cultural_age: int  # Years since founding
    major_cities: List[str]
    allies: List[str] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)
    trade_partners: List[str] = field(default_factory=list)

class LanguageGenerator:
    """Generates procedural languages"""

    def __init__(self):
        self.language_families = [
            "Proto-Indo-European", "Sino-Tibetan", "Afro-Asiatic",
            "Austronesian", "Niger-Congo", "Trans-New Guinea",
            "Japonic", "Dravidian", "Altaic", "Uralic",
            "Ainu", "Basque", "Etruscan", "Elamite"
        ]

        self.scripts = [
            "Alphabetic", "Syllabic", "Logographic", "Abugida",
            "Runes", "Hieroglyphs", "Cuneiform", "Featural"
        ]

        self.phoneme_sets = {
            "consonants": {
                "stops": ["p", "t", "k", "b", "d", "g"],
                "fricatives": ["f", "s", "h", "v", "z", "ʃ"],
                "nasals": ["m", "n", "ŋ"],
                "liquids": ["l", "r"],
                "semivowels": ["w", "j"]
            },
            "vowels": {
                "front": ["i", "e", "ɛ", "a"],
                "central": ["ə", "ɨ"],
                "back": ["u", "o", "ɔ", "ɑ"]
            }
        }

        self.grammar_types = {
            "word_order": ["SVO", "SOV", "VSO", "VOS", "OVS", "OSV"],
            "case_system": ["nominative-accusative", "ergative-absolutive", "tripartite"],
            "gender_system": ["masculine-feminine", "masculine-feminine-neuter", "animate-inanimate", "none"],
            "number_system": ["singular-plural", "singular-dual-plural", "singular-trial-plural"],
            "tense_system": ["past-present-future", "nonfuture-past", "remote-recent-present"]
        }

    def generate_language(self, seed: Optional[int] = None) -> Language:
        """Generate a complete language"""
        if seed is not None:
            random.seed(seed)

        # Language name
        name = self._generate_language_name()

        # Language family
        family = random.choice(self.language_families)

        # Script
        script = random.choice(self.scripts)

        # Phonology
        phonology = self._generate_phonology()

        # Grammar
        grammar = self._generate_grammar()

        # Vocabulary sample
        vocabulary = self._generate_vocabulary(phonology)

        # Writing direction
        writing_direction = random.choice(["left_to_right", "right_to_left", "top_to_bottom"])

        return Language(
            name=name,
            family=family,
            script=script,
            phonology=phonology,
            grammar=grammar,
            vocabulary=vocabulary,
            writing_direction=writing_direction
        )

    def _generate_language_name(self) -> str:
        """Generate a language name"""
        syllables = ["ka", "li", "to", "ma", "nu", "shi", "ra", "te", "mo", "lo",
                    "gi", "ve", "an", "du", "po", "ri", "se", "ko", "ba", "lu"]
        num_syllables = random.randint(2, 4)
        name = "".join(random.choice(syllables) for _ in range(num_syllables))
        return name.capitalize()

    def _generate_phonology(self) -> Dict[str, List[str]]:
        """Generate phonology for the language"""
        phonology = {}

        # Select consonants
        consonants = []
        for category, phones in self.phoneme_sets["consonants"].items():
            if random.random() < 0.7:  # 70% chance to include each category
                selected = random.sample(phones, min(len(phones), random.randint(2, len(phones))))
                consonants.extend(selected)

        # Select vowels
        vowels = []
        for category, phones in self.phoneme_sets["vowels"].items():
            if random.random() < 0.8:  # 80% chance to include each category
                selected = random.sample(phones, min(len(phones), random.randint(2, len(phones))))
                vowels.extend(selected)

        phonology["consonants"] = consonants if consonants else self.phoneme_sets["consonants"]["stops"]
        phonology["vowels"] = vowels if vowels else self.phoneme_sets["vowels"]["front"]

        return phonology

    def _generate_grammar(self) -> Dict[str, str]:
        """Generate grammatical features"""
        grammar = {}
        for feature, options in self.grammar_types.items():
            grammar[feature] = random.choice(options)
        return grammar

    def _generate_vocabulary(self, phonology: Dict[str, List[str]]) -> Dict[str, str]:
        """Generate sample vocabulary"""
        all_phonemes = phonology["consonants"] + phonology["vowels"]
        if not all_phonemes:
            all_phonemes = ["a", "e", "i", "o", "u", "k", "t", "m", "n"]

        # Basic vocabulary items
        basic_words = [
            "water", "fire", "earth", "sky", "sun", "moon", "star",
            "man", "woman", "child", "family", "home", "food",
            "love", "hate", "life", "death", "war", "peace",
            "one", "two", "three", "big", "small", "good", "bad"
        ]

        vocabulary = {}
        for word in basic_words:
            # Generate word by combining phonemes
            syllable_count = random.randint(1, 3)
            word_phonemes = []

            for _ in range(syllable_count):
                # Consonant + vowel pattern
                if random.random() < 0.8 and phonology["consonants"]:
                    word_phonemes.append(random.choice(phonology["consonants"]))
                if phonology["vowels"]:
                    word_phonemes.append(random.choice(phonology["vowels"]))

            vocabulary[word] = "".join(word_phonemes)

        return vocabulary

class MythologyGenerator:
    """Generates cultural mythology and belief systems"""

    def __init__(self):
        self.creation_themes = [
            "primordial_chaos", "divine_creation", "emergence_from_underworld",
            "world_tree", "cosmic_egg", "earth_diver", "ex_nihilo",
            "dreamtime", "ancestral_beings", "separation_of_powers"
        ]

        self.afterlife_concepts = [
            "paradise_garden", "underworld_realm", "reincarnation_cycle",
            "ancestral_spirit_world", "eternal_hunting_grounds", "star_journey",
            "void_of_nothingness", "continuation_of_service", "spirit_transformation"
        ]

        self.deity_domains = [
            "sky", "earth", "sea", "death", "love", "war", "knowledge",
            "fertility", "crafts", "travel", "healing", "trickery",
            "storms", "fire", "agriculture", "music", "wisdom", "chaos"
        ]

    def generate_mythology(self, religion_type: ReligionType,
                          culture_name: str, seed: Optional[int] = None) -> Mythology:
        """Generate mythology based on religion type"""
        if seed is not None:
            random.seed(seed)

        # Creation story
        creation_story = self._generate_creation_story(religion_type)

        # Pantheon
        pantheon = self._generate_pantheon(religion_type, culture_name)

        # Afterlife beliefs
        afterlife_beliefs = self._generate_afterlife_beliefs(religion_type)

        # Sacred texts
        sacred_texts = self._generate_sacred_texts(religion_type, culture_name)

        # Myths
        myths = self._generate_myths(religion_type, pantheon)

        # Prophecies
        prophecies = self._generate_prophecies(religion_type, culture_name)

        return Mythology(
            creation_story=creation_story,
            pantheon=pantheon,
            afterlife_beliefs=afterlife_beliefs,
            sacred_texts=sacred_texts,
            myths=myths,
            prophecies=prophecies
        )

    def _generate_creation_story(self, religion_type: ReligionType) -> str:
        """Generate creation story based on religion type"""
        themes = {
            ReligionType.POLYTHEISTIC: ["divine_council", "primordial_battle", "world_crafting"],
            ReligionType.MONOTHEISTIC: ["divine_word", "seven_days", "thought_creation"],
            ReligionType.ANIMISTIC: ["spirit_awakening", "natural_emergence", "ancestral_dreaming"],
            ReligionType.PANTHEISTIC: ["cosmic_consciousness", "universal_oneness", "natural_harmony"],
            ReligionType.ANCESTOR_WORSHIP: ["first_ancestors", "spirit_journey", "realm_emergence"]
        }

        possible_themes = themes.get(religion_type, self.creation_themes)
        theme = random.choice(possible_themes)

        story_templates = {
            "primordial_chaos": "In the beginning, there was only {chaos_element}. From this {chaos_element}, emerged the {first_beings} who shaped the {world_element}.",
            "divine_creation": "The {creator_deity} spoke the {magic_words}, and {creation_method} brought forth the {world_name} from {source_material}.",
            "world_tree": "The great {tree_type} grew from {seed_origin}, its branches forming the {upper_realm} and roots reaching into the {lower_realm}.",
            "emergence_from_underworld": "The {first_people} journeyed upward from the {underworld_name}, passing through {num_worlds} worlds until reaching the {surface_world}."
        }

        template = story_templates.get(theme, story_templates["divine_creation"])

        return template.format(
            chaos_element=random.choice(["darkness", "void", "waters", "formlessness"]),
            first_beings=random.choice(["ancient gods", "primordial spirits", "cosmic entities"]),
            world_element=random.choice(["mountains", "seas", "skies", "lands"]),
            creator_deity=random.choice(["Great Spirit", "Creator", "Architect", "Source"]),
            magic_words=random.choice(["sacred words", "divine command", "cosmic harmony"]),
            creation_method=random.choice(["thought", "breath", "song", "dance"]),
            world_name=random.choice(["mortal realm", "middle world", "earth sphere"]),
            source_material=random.choice(["starlight", "cosmic dust", "primordial waters"]),
            tree_type=random.choice(["World Ash", "Cosmic Oak", "Heavenly Cedar", "Divine Banyan"]),
            seed_origin=random.choice(["cosmic seed", "divine acorn", "sacred spore"]),
            upper_realm=random.choice(["heavens", "celestial realm", "sky world"]),
            lower_realm=random.choice(["underworld", "abyss", "netherworld"]),
            first_people=random.choice(["First Humans", "Ancestors", "Star People"]),
            underworld_name=random.choice(["Lower World", "Dark Realm", "Underground"]),
            num_worlds=str(random.randint(3, 9)),
            surface_world=random.choice(["Surface World", "Middle Earth", "Sunlit Realm"])
        )

    def _generate_pantheon(self, religion_type: ReligionType, culture_name: str) -> List[Dict]:
        """Generate pantheon of deities/spirits"""
        pantheon = []

        if religion_type == ReligionType.MONOTHEISTIC:
            # Single supreme deity
            deity = {
                "name": f"The {random.choice(['Great', 'Supreme', 'Eternal', 'Almighty'])} {random.choice(['One', 'Creator', 'Light', 'Source'])}",
                "domain": "all",
                "attributes": [random.choice(["merciful", "just", "wise", "powerful", "loving"])],
                "symbols": [random.choice(["light", "circle", "star", "sun", "infinity"])],
                "worship_methods": ["prayer", "meditation", "ritual", "sacrifice"]
            }
            pantheon.append(deity)

        elif religion_type == ReligionType.POLYTHEISTIC:
            # Multiple deities
            num_deities = random.randint(5, 12)
            domains = random.sample(self.deity_domains, min(num_deities, len(self.deity_domains)))

            for domain in domains:
                deity = {
                    "name": self._generate_deity_name(domain),
                    "domain": domain,
                    "attributes": [random.choice(["fierce", "gentle", "wise", "trickster", "protector", "destroyer"])],
                    "symbols": [random.choice(["lightning", "hammer", "sword", "staff", "moon", "fire", "water"])],
                    "worship_methods": [random.choice(["prayer", "offering", "festival", "pilgrimage", "meditation"])]
                }
                pantheon.append(deity)

        elif religion_type == ReligionType.ANIMISTIC:
            # Nature spirits
            spirit_types = ["river", "mountain", "forest", "wind", "fire", "stone", "animal", "plant"]
            for spirit_type in random.sample(spirit_types, random.randint(3, 7)):
                spirit = {
                    "name": f"The {spirit_type.title()} Spirit",
                    "domain": spirit_type,
                    "attributes": [random.choice(["ancient", "wise", "capricious", "protective", "wild"])],
                    "symbols": [spirit_type],
                    "worship_methods": ["offering", "respect", "ceremony", "ritual dance"]
                }
                pantheon.append(spirit)

        elif religion_type == ReligionType.ANCESTOR_WORSHIP:
            # Founding ancestors and hero spirits
            ancestor_types = ["First Mother", "Great Father", "Culture Hero", "Warrior Chief", "Wise Elder"]
            for ancestor_type in random.sample(ancestor_types, random.randint(2, 5)):
                ancestor = {
                    "name": f"The {ancestor_type}",
                    "domain": "ancestors",
                    "attributes": [random.choice(["benevolent", "wise", "powerful", "protective"])],
                    "symbols": [random.choice(["totem", "weapon", "tool", "jewel"])],
                    "worship_methods": ["ancestor veneration", "offering", "storytelling", "ritual feast"]
                }
                pantheon.append(ancestor)

        return pantheon

    def _generate_deity_name(self, domain: str) -> str:
        """Generate deity name based on domain"""
        prefixes = {
            "sky": ["Celest", "Astra", "Uran", "Cael", "Sky"],
            "earth": ["Geo", "Terra", "Gaia", "Erda", "Tellus"],
            "sea": ["Mar", "Aqua", "Thal", "Ocean", "Pontus"],
            "war": ["Bel", "Mar", "Tyr", "Ares", "Mars"],
            "love": ["Venu", "Amor", "Aphro", "Eros", "Cupid"]
        }

        suffixes = ["us", "a", "on", "os", "an", "el", "ra", "ia", "or", "is"]

        domain_prefixes = prefixes.get(domain, ["De", "Di", "Lo", "Al", "El"])
        prefix = random.choice(domain_prefixes)
        suffix = random.choice(suffixes)

        return prefix + suffix

    def _generate_afterlife_beliefs(self, religion_type: ReligionType) -> str:
        """Generate afterlife beliefs"""
        concepts = {
            ReligionType.MONOTHEISTIC: [
                "Righteous souls ascend to the heavenly paradise to serve eternally.",
                "The faithful are judged and rewarded with eternal peace in divine presence.",
                "Through divine grace, believers achieve union with the ultimate reality."
            ],
            ReligionType.POLYTHEISTIC: [
                "Warriors feast in the hall of heroes while farmers till eternal fields.",
                "Souls journey to the realm of their patron deity for eternal service.",
                "The dead cross the river to the underworld where they continue their mortal trades."
            ],
            ReligionType.ANIMISTIC: [
                "Spirits of the dead join their ancestors in the spirit world, guiding the living.",
                "The soul becomes one with nature, watching over their descendants as guardian spirits.",
                "Death is transformation, with spirits taking new forms in the natural world."
            ],
            ReligionType.REINCARNATION: [
                "The soul is reborn in a new form based on deeds in the previous life.",
                "Through cycles of birth and death, the soul learns and evolves toward perfection.",
                "All living beings are part of the great cycle of death and rebirth."
            ]
        }

        possible_concepts = concepts.get(religion_type, self.afterlife_concepts)
        return random.choice(possible_concepts)

    def _generate_sacred_texts(self, religion_type: ReligionType, culture_name: str) -> List[str]:
        """Generate names of sacred texts"""
        text_templates = {
            ReligionType.MONOTHEISTIC: [
                "The Holy {book} of {culture}",
                "The {adjective} Testament",
                "The {divine_name} Covenant",
                "The {symbol} Scriptures"
            ],
            ReligionType.POLYTHEISTIC: [
                "Tales of the {adjective} Gods",
                "The {number} Divine Chronicles",
                "Hymns to the {pantheon_type}",
                "The {element} Codex"
            ],
            ReligionType.ANIMISTIC: [
                "Whispers of the {spirit_type}",
                "The {nature_element} Wisdom",
                "Songs of the {ancestor_type}",
                "The {time_period} Traditions"
            ]
        }

        templates = text_templates.get(religion_type, ["The Sacred Texts of {culture}"])
        texts = []

        for template in random.sample(templates, random.randint(1, 3)):
            text = template.format(
                book=random.choice(["Book", "Word", "Law", "Path", "Way"]),
                culture=culture_name,
                adjective=random.choice(["Eternal", "Divine", "Sacred", "Holy", "Blessed"]),
                divine_name=random.choice(["Creator", "Source", "Light", "Truth"]),
                symbol=random.choice(["Sun", "Moon", "Star", "Light", "Dawn"]),
                number=random.choice(["Twelve", "Seven", "Nine", "Five"]),
                pantheon_type=random.choice(["Olympians", "Asgardians", "Celestials", "Eternals"]),
                element=random.choice(["Storm", "Fire", "Earth", "Water", "Sky"]),
                spirit_type=random.choice(["Ancestors", "Spirits", "Guides", "Guardians"]),
                nature_element=random.choice(["Forest", "Mountain", "River", "Ocean"]),
                ancestor_type=random.choice(["First People", "Ancients", "Elders", "Founders"]),
                time_period=random.choice(["Ancient", "Primordial", "First", "Old"])
            )
            texts.append(text)

        return texts

    def _generate_myths(self, religion_type: ReligionType, pantheon: List[Dict]) -> List[str]:
        """Generate cultural myths"""
        myths = []

        if pantheon:
            # Create myths featuring the pantheon
            myth_templates = [
                "The {deity} stole the {stolen_item} from {other_deity}, bringing {consequence} to humanity.",
                "When the {deity} wept, their tears formed the {geographical_feature}, blessing the {people}.",
                "The great {conflict_type} between {deity1} and {deity2} shaped the {aspect_of_world}.",
                "The {deity} taught humanity the {skill}, but only the {worthy_group} could master it.",
                "During the {cosmic_event}, the {deity} {action}, creating the {natural_phenomenon}."
            ]

            for _ in range(random.randint(3, 7)):
                if len(pantheon) >= 2:
                    deity1 = random.choice(pantheon)["name"]
                    deity2 = random.choice([d["name"] for d in pantheon if d["name"] != deity1])
                else:
                    deity1 = pantheon[0]["name"]
                    deity2 = "the forces of chaos"

                myth = random.choice(myth_templates).format(
                    deity=random.choice([d["name"] for d in pantheon]),
                    stolen_item=random.choice(["fire", "wisdom", "agriculture", "language", "immortality"]),
                    other_deity=deity2,
                    consequence=random.choice(["knowledge", "hardship", "civilization", "mortality"]),
                    geographical_feature=random.choice(["mountains", "rivers", "valleys", "seas", "forests"]),
                    people=random.choice(["tribes", "nations", "mortals", "children"]),
                    conflict_type=random.choice(["war", "contest", "argument", "struggle"]),
                    aspect_of_world=random.choice(["seasons", "day and night", "weather", "life and death"]),
                    skill=random.choice(["agriculture", "metallurgy", "magic", "medicine", "art"]),
                    worthy_group=random.choice(["priests", "warriors", "artists", "scholars"]),
                    cosmic_event=random.choice(["first dawn", "great flood", "long night", "star fall"]),
                    action=random.choice(["sang", "danced", "fought", "wept", "laughed"]),
                    natural_phenomenon=random.choice(["rain", "thunder", "earthquakes", "rainbows", "aurora"])
                )
                myths.append(myth)

        return myths

    def _generate_prophecies(self, religion_type: ReligionType, culture_name: str) -> List[str]:
        """Generate cultural prophecies"""
        prophecy_templates = [
            "When the {celestial_event} occurs {time_marker}, the {prophesied_figure} shall {action} and bring {outcome}.",
            "The {sign} will appear in the {location}, signaling the {event_type} that will {consequence}.",
            "In the {time_period}, the {chosen_people} will {great_deed}, fulfilling the {ancient_promise}.",
            "The {prophetic_beast} will {prophetic_action} when {condition} is met, ushering in the {new_age}."
        ]

        prophecies = []
        for _ in range(random.randint(2, 4)):
            prophecy = random.choice(prophecy_templates).format(
                celestial_event=random.choice(["blood moon", "comet", "eclipse", "planetary alignment"]),
                time_marker=random.choice(["twice", "thrice", "at dawn", "during solstice"]),
                prophesied_figure=random.choice(["chosen one", "dark lord", "great leader", "divine messenger"]),
                action=random.choice(["rise again", "return from exile", "unite the tribes", "bring enlightenment"]),
                outcome=random.choice(["golden age", "destruction", "transformation", "liberation"]),
                sign=random.choice(["burning star", "falling star", "dark sun", "blood red sky"]),
                location=random.choice(["eastern mountains", "western seas", "northern forests", "southern deserts"]),
                event_type=random.choice(["end times", "new beginning", "great change", "final judgment"]),
                consequence=random.choice(["liberate the oppressed", "punish the wicked", "transform the world", "fulfill destiny"]),
                time_period=random.choice(["final days", "dawning age", "darkest hour", "time of trial"]),
                chosen_people=[f"{culture_name} people", "faithful", "pure of heart", "worthy souls"],
                great_deed=random.choice(["reclaim their homeland", "defeat darkness", "achieve enlightenment", "unite all nations"]),
                ancient_promise=random.choice(["covenant", "prophecy", "destiny", "divine plan"]),
                prophetic_beast=random.choice(["white stag", "black dragon", "phoenix", "world serpent"]),
                prophetic_action=random.choice(["be reborn", "awaken", "rise from the depths", "descend from heavens"]),
                condition=random.choice(["the people are ready", "the stars align", "the ancient words are spoken", "the sacred artifact is found"]),
                new_age=random.choice(["eternal peace", "enlightenment", "paradise", "transformation"])
            )
            prophecies.append(prophecy)

        return prophecies

class CultureGenerator:
    """Main culture generation system"""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed or random.randint(0, 2**31 - 1)
        random.seed(self.seed)
        np.random.seed(self.seed)

        self.language_generator = LanguageGenerator()
        self.mythology_generator = MythologyGenerator()

        self.cultural_values_pool = [
            ("honor", "Personal and family honor is paramount", ["dueling", "family reputation", "oath-keeping"]),
            ("community", "The group is more important than the individual", ["communal meals", "shared housing", "collective decision-making"]),
            ("knowledge", "Wisdom and learning are the highest virtues", ["schools", "libraries", "storytelling", "scholarship"]),
            ("courage", "Bravery in the face of adversity", ["warrior culture", "coming of age trials", "battle honors"]),
            ("harmony", "Living in balance with nature and each other", ["environmental protection", "mediation", "peaceful conflict resolution"]),
            ("tradition", "Ancestors' ways must be preserved", ["ceremonies", "rituals", "oral histories", "artisan guilds"]),
            ("innovation", "Progress and change bring improvement", ["inventors", "exploration", "scientific method", "new technologies"]),
            ("spirituality", "Connection to the divine is essential", ["temples", "meditation", "pilgrimage", "divination"]),
            ("wealth", "Material prosperity indicates divine favor", ["merchant culture", "banking", "trade routes", "luxury goods"]),
            ("freedom", "Individual liberty must be protected", ["democratic institutions", "individual rights", "rebellion against tyranny"])
        ]

        self.tradition_types = [
            "festival", "rite_of_passage", "coming_of_age", "marriage", "funeral",
            "harvest", "religious_ceremony", "military_honor", "seasonal", "healing_ritual"
        ]

    def generate_culture(self, location: Tuple[int, int], terrain_type: str,
                        neighboring_cultures: Optional[List[str]] = None) -> Culture:
        """Generate a complete culture"""
        # Culture name
        name = self._generate_culture_name(location, terrain_type)

        # Core characteristics
        population = random.randint(5000, 500000)
        government_type = self._determine_government_type(population, terrain_type)
        social_structure = self._determine_social_structure(government_type, terrain_type)
        technology_level = self._determine_technology_level(terrain_type, neighboring_cultures)
        religion_type = self._determine_religion_type(terrain_type, social_structure)
        economic_system = self._determine_economic_system(terrain_type, technology_level)

        # Generate language
        language = self.language_generator.generate_language(self.seed + hash(name) % 10000)

        # Generate mythology
        mythology = self.mythology_generator.generate_mythology(religion_type, name, self.seed + hash(name) % 10000)

        # Generate cultural values
        values = self._generate_cultural_values(government_type, religion_type, terrain_type)

        # Generate traditions
        traditions = self._generate_traditions(values, religion_type, terrain_type)

        # Art style
        art_style = self._determine_art_style(values, terrain_type)

        # Other cultural aspects
        architecture_style = self._generate_architecture_style(terrain_type, technology_level, values)
        clothing_style = self._generate_clothing_style(terrain_type, values, climate=self._get_climate(terrain_type))
        cuisine = self._generate_cuisine(terrain_type, economic_system)
        military_organization = self._generate_military_organization(government_type, technology_level)

        # Known inventions based on technology level
        known_inventions = self._generate_known_inventions(technology_level)

        return Culture(
            name=name,
            homeland=location,
            influence_radius=random.randint(5, 50),
            population=population,
            government_type=government_type,
            social_structure=social_structure,
            technology_level=technology_level,
            religion_type=religion_type,
            economic_system=economic_system,
            values=values,
            traditions=traditions,
            language=language,
            mythology=mythology,
            art_style=art_style,
            architecture_style=architecture_style,
            clothing_style=clothing_style,
            cuisine=cuisine,
            military_organization=military_organization,
            diplomatic_relations={},
            known_inventions=known_inventions,
            cultural_age=random.randint(100, 2000),
            major_cities=self._generate_city_names(random.randint(1, 5))
        )

    def _generate_culture_name(self, location: Tuple[int, int], terrain_type: str) -> str:
        """Generate culture name based on location and terrain"""
        prefixes = {
            "mountain": ["Stone", "Rock", "Peak", "Summit", "Cliff", "Crag"],
            "forest": ["Green", "Wood", "Leaf", "Forest", "Wild", "Deep"],
            "plains": ["Grass", "Wind", "Sky", "Plain", "Field", "Dawn"],
            "desert": ["Sand", "Sun", "Dune", "Heat", "Gold", "Mirage"],
            "coastal": ["Wave", "Sea", "Storm", "Tide", "Shell", "Salt"],
            "river": ["River", "Flow", "Water", "Current", "Stream", "Flood"],
            "arctic": ["Ice", "Snow", "Frost", "Winter", "Cold", "North"],
            "swamp": ["Mud", "Swamp", "Marsh", "Reed", "Fen", "Bog"]
        }

        suffixes = [
            "people", "folk", "tribe", "nation", "kingdom", "clan",
            "dwellers", "children", "keepers", "guardians", "speakers"
        ]

        terrain_prefixes = prefixes.get(terrain_type, ["Ancient", "Old", "Great", "High"])
        prefix = random.choice(terrain_prefixes)
        suffix = random.choice(suffixes)

        return f"{prefix} {suffix}"

    def _determine_government_type(self, population: int, terrain_type: str) -> GovernmentType:
        """Determine government type based on population and terrain"""
        if population < 10000:
            return random.choice([GovernmentType.TRIBE, GovernmentType.CHIEFDOM])
        elif population < 50000:
            if terrain_type in ["mountain", "plains"]:
                return random.choice([GovernmentType.CHIEFDOM, GovernmentType.MONARCHY])
            else:
                return random.choice([GovernmentType.MONARCHY, GovernmentType.REPUBLIC])
        elif population < 200000:
            if terrain_type == "coastal":
                return random.choice([GovernmentType.REPUBLIC, GovernmentType.MERCHANT_REPUBLIC])
            else:
                return random.choice([GovernmentType.MONARCHY, GovernmentType.FEUDAL, GovernmentType.REPUBLIC])
        else:
            return random.choice([GovernmentType.EMPIRE, GovernmentType.REPUBLIC, GovernmentType.MILITARY_DICTATORSHIP])

    def _determine_social_structure(self, government_type: GovernmentType, terrain_type: str) -> SocialStructure:
        """Determine social structure based on government and terrain"""
        if government_type in [GovernmentType.TRIBE, GovernmentType.CHIEFDOM]:
            return random.choice([SocialStructure.CLAN_BASED, SocialStructure.EGALITARIAN])
        elif government_type == GovernmentType.THEOCRACY:
            return random.choice([SocialStructure.HIERARCHICAL, SocialStructure.CASTE_SYSTEM])
        elif terrain_type == "mountain":
            return random.choice([SocialStructure.CLAN_BASED, SocialStructure.HIERARCHICAL])
        else:
            return random.choice([SocialStructure.HIERARCHICAL, SocialStructure.CLASS_BASED])

    def _determine_technology_level(self, terrain_type: str, neighboring_cultures: Optional[List[str]]) -> TechnologyLevel:
        """Determine technology level based on terrain and neighbors"""
        # Terrain affects technological development
        terrain_modifiers = {
            "mountain": -1,  # Slower development
            "forest": 0,
            "plains": 1,    # Faster development
            "coastal": 2,   # Trade speeds development
            "river": 1,
            "desert": -1,
            "arctic": -2    # Harsh conditions slow development
        }

        base_level = 2  # Iron Age baseline
        terrain_modifier = terrain_modifiers.get(terrain_type, 0)

        # Neighboring cultures can influence technology
        neighbor_modifier = 0
        if neighboring_cultures:
            neighbor_modifier = len(neighboring_cultures) * 0.5

        final_level = base_level + terrain_modifier + neighbor_modifier
        final_level = max(0, min(9, final_level))  # Clamp to valid range

        levels = list(TechnologyLevel)
        return levels[final_level]

    def _determine_religion_type(self, terrain_type: str, social_structure: SocialStructure) -> ReligionType:
        """Determine religion type based on terrain and social structure"""
        if terrain_type in ["forest", "arctic", "desert"]:
            return random.choice([ReligionType.ANIMISTIC, ReligionType.NATURALISTIC])
        elif social_structure == SocialStructure.CASTE_SYSTEM:
            return random.choice([ReligionType.POLYTHEISTIC, ReligionType.THEOCRACY])
        elif social_structure == SocialStructure.CLAN_BASED:
            return random.choice([ReligionType.ANCESTOR_WORSHIP, ReligionType.ANIMISTIC])
        else:
            return random.choice(list(ReligionType))

    def _determine_economic_system(self, terrain_type: str, technology_level: TechnologyLevel) -> EconomicSystem:
        """Determine economic system based on terrain and technology"""
        if technology_level in [TechnologyLevel.STONE_AGE, TechnologyLevel.BRONZE_AGE]:
            if terrain_type in ["plains", "river"]:
                return EconomicSystem.AGRICULTURAL
            else:
                return EconomicSystem.HUNTER_GATHERER
        elif technology_level in [TechnologyLevel.IRON_AGE, TechnologyLevel.MEDIEVAL]:
            if terrain_type == "coastal":
                return EconomicSystem.MERCANTILE
            else:
                return random.choice([EconomicSystem.AGRICULTURAL, EconomicSystem.FEUDAL])
        elif technology_level in [TechnologyLevel.RENAISSANCE, TechnologyLevel.INDUSTRIAL]:
            return random.choice([EconomicSystem.MERCANTILE, EconomicSystem.CAPITALIST])
        else:
            return EconomicSystem.CAPITALIST

    def _generate_cultural_values(self, government_type: GovernmentType,
                                religion_type: ReligionType, terrain_type: str) -> List[CulturalValue]:
        """Generate cultural values based on society characteristics"""
        # Select values appropriate for this culture
        values = []

        # Government-influenced values
        if government_type in [GovernmentType.MONARCHY, GovernmentType.EMPIRE]:
            values.append(random.choice(["honor", "tradition", "loyalty"]))
        elif government_type in [GovernmentType.REPUBLIC, GovernmentType.DEMOCRACY]:
            values.append(random.choice(["freedom", "community", "knowledge"]))
        elif government_type == GovernmentType.THEOCRACY:
            values.append(random.choice(["spirituality", "tradition", "community"]))

        # Religion-influenced values
        if religion_type == ReligionType.MONOTHEISTIC:
            values.append(random.choice(["spirituality", "knowledge", "community"]))
        elif religion_type == ReligionType.ANIMISTIC:
            values.append("harmony")
        elif religion_type == ReligionType.ANCESTOR_WORSHIP:
            values.append("tradition")

        # Terrain-influenced values
        if terrain_type in ["mountain", "arctic"]:
            values.append("courage")
        elif terrain_type in ["forest", "plains"]:
            values.append("harmony")
        elif terrain_type == "coastal":
            values.append(random.choice(["innovation", "wealth"]))

        # Add some random values
        available_values = [v[0] for v in self.cultural_values_pool if v[0] not in values]
        if available_values:
            values.extend(random.sample(available_values, random.randint(1, 3)))

        # Create CulturalValue objects
        cultural_values = []
        for value_name in values:
            value_data = next(v for v in self.cultural_values_pool if v[0] == value_name)
            importance = random.uniform(0.5, 1.0)

            cultural_value = CulturalValue(
                name=value_data[0],
                description=value_data[1],
                importance=importance,
                manifestation=value_data[2]
            )
            cultural_values.append(cultural_value)

        return cultural_values

    def _generate_traditions(self, values: List[CulturalValue], religion_type: ReligionType,
                           terrain_type: str) -> List[Tradition]:
        """Generate cultural traditions"""
        traditions = []

        # Generate traditions based on values
        for value in values:
            if random.random() < 0.7:  # 70% chance of tradition per value
                tradition_type = random.choice(self.tradition_types)

                tradition = Tradition(
                    name=self._generate_tradition_name(value.name, tradition_type),
                    type=tradition_type,
                    description=self._generate_tradition_description(value.name, tradition_type, terrain_type),
                    frequency=self._generate_tradition_frequency(tradition_type),
                    participants=self._generate_tradition_participants(tradition_type),
                    significance=f"Expression of {value.name}"
                )
                traditions.append(tradition)

        # Add religious traditions
        if religion_type != ReligionType.ATHEISTIC:
            for _ in range(random.randint(2, 4)):
                tradition = Tradition(
                    name=self._generate_religious_tradition_name(),
                    type="religious_ceremony",
                    description=self._generate_religious_tradition_description(religion_type),
                    frequency=random.choice(["daily", "weekly", "monthly", "yearly"]),
                    participants=["priests", "devotees", "community"],
                    significance="Religious observance"
                )
                traditions.append(tradition)

        return traditions

    def _generate_tradition_name(self, value_name: str, tradition_type: str) -> str:
        """Generate tradition name"""
        templates = {
            "festival": ["Festival of {value}", "Celebration of {value}", "{value} Feast"],
            "rite_of_passage": ["{value} Trial", "Path of {value}", "{value} Initiation"],
            "coming_of_age": ["{value} Awakening", "{value} Ceremony", "Rite of {value}"],
            "marriage": ["Bond of {value}", "{value} Union", "{value} Marriage"],
            "funeral": ["{value} Journey", "Return to {value}", "{value} Farewell"],
            "harvest": ["{value} Harvest", "Festival of {value} Bounty", "{value} Thanksgiving"],
            "religious_ceremony": ["{value} Blessing", "Rite of {value}", "{value} Devotion"]
        }

        template = random.choice(templates.get(tradition_type, ["{value} Ceremony"]))
        return template.format(value=value_name.title())

    def _generate_tradition_description(self, value_name: str, tradition_type: str, terrain_type: str) -> str:
        """Generate tradition description"""
        descriptions = {
            "festival": "A joyous celebration where participants {activity} while enjoying {food} and {entertainment}.",
            "rite_of_passage": "A challenging test where candidates must {challenge} to prove their {quality}.",
            "coming_of_age": "A ceremony marking the transition to adulthood with {symbol} and {ritual}.",
            "marriage": "The sacred union of two individuals through {ceremony} and {exchange}.",
            "funeral": "A solemn ceremony honoring the deceased with {ritual} and {offering}.",
            "harvest": "Giving thanks for the bounty through {ceremony} and {celebration}."
        }

        template = descriptions.get(tradition_type, "A ceremonial practice involving {ritual} and {symbolism}.")

        return template.format(
            activity=random.choice(["dance", "sing", "feast", "compete", "share stories"]),
            food=random.choice(["traditional dishes", "sacred foods", "seasonal delicacies", "communal meals"]),
            entertainment=random.choice(["music", "storytelling", "games", "performances"]),
            challenge=random.choice(["endure hardship", "demonstrate skill", "solve puzzles", "face fears"]),
            quality=random.choice(["courage", "wisdom", "strength", "honor", "devotion"]),
            symbol=random.choice(["sacred objects", "traditional clothing", "body paint", "ceremonial items"]),
            ritual=random.choice(["prayer", "meditation", "offering", "chanting", "dancing"]),
            ceremony=random.choice(["vows", "exchange of gifts", "feast", "blessing", "dance"]),
            exchange=random.choice(["rings", "gifts", "promises", "symbols", "blessings"]),
            offering=random.choice(["flowers", "food", "incense", "prayers", "symbolic items"]),
            celebration=random.choice(["feasting", "dancing", "singing", "games", "storytelling"]),
            symbolism=random.choice(["symbolic acts", "sacred words", "ritual gestures", "ceremonial objects"])
        )

    def _generate_tradition_frequency(self, tradition_type: str) -> str:
        """Generate how often a tradition occurs"""
        frequencies = {
            "daily": ["daily", "at dawn", "at dusk", "each morning"],
            "weekly": ["weekly", "every seventh day", "on the holy day"],
            "monthly": ["monthly", "at the new moon", "at the full moon"],
            "yearly": ["yearly", "annually", "once per year", "at the same time each year"],
            "seasonal": ["seasonally", "with each season", "four times a year"],
            "life_cycle": ["at birth", "at coming of age", "at marriage", "at death"]
        }

        possible_frequencies = frequencies.get(tradition_type, ["yearly"])
        return random.choice(possible_frequencies)

    def _generate_tradition_participants(self, tradition_type: str) -> List[str]:
        """Generate who participates in a tradition"""
        participant_groups = {
            "festival": ["entire community", "all ages", "families", "everyone"],
            "rite_of_passage": ["youths", "candidates", "initiates", "young adults"],
            "coming_of_age": ["adolescents", "families", "elders", "community leaders"],
            "marriage": ["couples", "families", "community", "witnesses"],
            "funeral": ["family members", "community", "elders", "mourners"],
            "harvest": ["farmers", "community", "families", "workers"],
            "religious_ceremony": ["priests", "devotees", "believers", "community"]
        }

        return participant_groups.get(tradition_type, ["community"])

    def _generate_religious_tradition_name(self) -> str:
        """Generate religious tradition name"""
        prefixes = ["Sacred", "Holy", "Divine", "Blessed", "Eternal", "Ancient"]
        suffixes = ["Rite", "Ceremony", "Observance", "Ritual", "Devotion", "Blessing"]

        return f"{random.choice(prefixes)} {random.choice(suffixes)}"

    def _generate_religious_tradition_description(self, religion_type: ReligionType) -> str:
        """Generate religious tradition description"""
        descriptions = {
            ReligionType.POLYTHEISTIC: "Honoring the {deity} through {offering} and {ritual} to gain {blessing}.",
            ReligionType.MONOTHEISTIC: "Worshipping the divine through {prayer} and {devotion} to achieve {spiritual_goal}.",
            ReligionType.ANIMISTIC: "Communicating with {spirits} through {ceremony} and {offering} to maintain {balance}.",
            ReligionType.ANCESTOR_WORSHIP: "Honoring the {ancestors} through {ritual} and {offering} to receive {guidance}."
        }

        template = descriptions.get(religion_type, "A sacred observance involving {ritual} and {symbolism}.")

        return template.format(
            deity=random.choice(["gods", "divinities", "celestials", "powers"]),
            offering=random.choice(["offerings", "sacrifices", "gifts", "prayers"]),
            ritual=random.choice(["ritual dance", "sacred chants", "ceremonial acts", "holy words"]),
            blessing=random.choice(["favor", "protection", "wisdom", "prosperity"]),
            prayer=random.choice(["prayer", "meditation", "chanting", "contemplation"]),
            devotion=random.choice(["devotion", "faith", "worship", "service"]),
            spiritual_goal=random.choice(["enlightenment", "salvation", "union with divine", "spiritual peace"]),
            spirits=random.choice(["nature spirits", "ancestral spirits", "elemental beings", "guardian spirits"]),
            ceremony=random.choice(["ceremonial dance", "sacred rites", "ritual acts", "holy ceremonies"]),
            balance=random.choice(["natural balance", "cosmic harmony", "spiritual equilibrium", "environmental peace"]),
            ancestors=random.choice(["ancestors", "forebears", "elders", "first people"]),
            guidance=random.choice(["guidance", "wisdom", "blessing", "protection"])
        )

    def _determine_art_style(self, values: List[CulturalValue], terrain_type: str) -> ArtStyle:
        """Determine art style based on values and terrain"""
        value_names = [v.name for v in values]

        if "tradition" in value_names:
            return random.choice([ArtStyle.SYMBOLIC, ArtStyle.RITUALISTIC, ArtStyle.NARRATIVE])
        elif "knowledge" in value_names:
            return random.choice([ArtStyle.GEOMETRIC, ArtStyle.MINIMALIST])
        elif "harmony" in value_names:
            return random.choice([ArtStyle.NATURALISTIC, ArtStyle.FUNCTIONAL])
        elif "honor" in value_names:
            return random.choice([ArtStyle.ORNATE, ArtStyle.SYMBOLIC])
        else:
            return random.choice(list(ArtStyle))

    def _generate_architecture_style(self, terrain_type: str, technology_level: TechnologyLevel,
                                   values: List[CulturalValue]) -> str:
        """Generate architecture style"""
        terrain_materials = {
            "mountain": ["stone", "timber", "mountain stone"],
            "forest": ["timber", "wood", "carved wood"],
            "plains": ["timber", "stone", "mud brick"],
            "desert": ["sandstone", "adobe", "clay"],
            "coastal": ["coral", "driftwood", "sea stone"],
            "arctic": ["ice", "snow blocks", "animal hides"],
            "swamp": ["stilt houses", "reed", "water-resistant materials"]
        }

        materials = terrain_materials.get(terrain_type, ["stone", "wood", "timber"])

        tech_styles = {
            TechnologyLevel.STONE_AGE: "crude {material} structures",
            TechnologyLevel.BRONZE_AGE: "{material} buildings with bronze accents",
            TechnologyLevel.IRON_AGE: "fortified {material} architecture",
            TechnologyLevel.MEDIEVAL: "grand {material} castles and cathedrals",
            TechnologyLevel.RENAISSANCE: "elegant {material} palaces and temples",
            TechnologyLevel.INDUSTRIAL: "functional {material} buildings with metal supports"
        }

        base_style = tech_styles.get(technology_level, "{material} structures")

        # Add cultural modifiers
        value_names = [v.name for v in values]
        if "tradition" in value_names:
            base_style += " with traditional ornamentation"
        if "spirituality" in value_names:
            base_style += " featuring sacred geometry"
        if "community" in value_names:
            base_style += " designed for communal living"

        return base_style.format(material=random.choice(materials))

    def _generate_clothing_style(self, terrain_type: str, values: List[CulturalValue], climate: str) -> str:
        """Generate clothing style"""
        terrain_materials = {
            "mountain": ["wool", "fur", "leather", "heavy fabrics"],
            "forest": ["leather", "woven fabrics", "natural fibers", "bark cloth"],
            "plains": ["cotton", "linen", "light wool", "woven grasses"],
            "desert": ["light cotton", "linen", "silk", "breathable fabrics"],
            "coastal": ["light fabrics", "sea silk", "coral beads", "shells"],
            "arctic": ["fur", "heavy wool", "animal skins", "insulated materials"],
            "swamp": ["water-resistant materials", "light fabrics", "reeds"]
        }

        materials = terrain_materials.get(terrain_type, ["cotton", "wool", "linen"])

        value_names = [v.name for v in values]
        modifiers = []

        if "honor" in value_names:
            modifiers.append("formal and dignified")
        if "tradition" in value_names:
            modifiers.append("adorned with traditional symbols")
        if "freedom" in value_names:
            modifiers.append("practical and unrestricted")
        if "community" in value_names:
            modifiers.append "featuring communal colors and patterns"

        modifier_text = " and ".join(modifiers) if modifiers else "simple and functional"

        return f"{modifier_text} clothing made from {', '.join(materials[:2])}"

    def _generate_cuisine(self, terrain_type: str, economic_system: EconomicSystem) -> List[str]:
        """Generate cuisine based on terrain and economy"""
        terrain_ingredients = {
            "mountain": ["hardy grains", "root vegetables", "mountain herbs", "preserved meats"],
            "forest": ["wild game", "forest fruits", "nuts", "mushrooms", "honey"],
            "plains": ["grains", "vegetables", "domesticated animals", "dairy products"],
            "desert": ["dates", "figs", "goat meat", "preserved foods", "spices"],
            "coastal": ["seafood", "seaweed", "coastal plants", "salted fish"],
            "arctic": ["seal meat", "fish", "arctic plants", "whale blubber"],
            "swamp": ["fish", "waterfowl", "reeds", "aquatic plants", "insects"]
        }

        ingredients = terrain_ingredients.get(terrain_type, ["grains", "vegetables", "meat"])

        dishes = []
        for ingredient in random.sample(ingredients, min(3, len(ingredients))):
            preparation = random.choice(["stewed", "roasted", "grilled", "fried", "preserved", "raw"])
            dishes.append(f"{preparation} {ingredient}")

        # Add trade goods if mercantile
        if economic_system in [EconomicSystem.MERCANTILE, EconomicSystem.CAPITALIST]:
            trade_ingredients = ["spices", "exotic fruits", "sugar", "rare herbs"]
            dishes.extend([f"{random.choice(trade_ingredients)} flavored dishes"])

        return dishes

    def _generate_military_organization(self, government_type: GovernmentType,
                                     technology_level: TechnologyLevel) -> str:
        """Generate military organization description"""
        if technology_level in [TechnologyLevel.STONE_AGE, TechnologyLevel.BRONZE_AGE]:
            base = "warrior bands"
        elif technology_level in [TechnologyLevel.IRON_AGE, TechnologyLevel.MEDIEVAL]:
            base = "feudal levies and professional soldiers"
        else:
            base = "professional standing army"

        if government_type in [GovernmentType.TRIBE, GovernmentType.CHIEFDOM]:
            return f"Clan-based {base} led by tribal champions"
        elif government_type == GovernmentType.MILITARY_DICTATORSHIP:
            return f"Highly disciplined {base} with strict hierarchy"
        elif government_type == GovernmentType.THEOCRACY:
            return f"Religious {base} serving as holy warriors"
        else:
            return f"Organized {base} with specialized units"

    def _generate_known_inventions(self, technology_level: TechnologyLevel) -> List[str]:
        """Generate list of known inventions based on technology level"""
        inventions = {
            TechnologyLevel.STONE_AGE: ["stone tools", "fire", "clothing", "simple shelters"],
            TechnologyLevel.BRONZE_AGE: ["bronze tools", "writing", "agriculture", "pottery", "simple boats"],
            TechnologyLevel.IRON_AGE: ["iron tools", "coinage", "advanced agriculture", "siege weapons"],
            TechnologyLevel.MEDIEVAL: ["steel weapons", "armor", "castles", "horseback riding", "windmills"],
            TechnologyLevel.RENAISSANCE: ["printing press", "gunpowder weapons", "advanced navigation", "anatomy"],
            TechnologyLevel.INDUSTRIAL: ["steam power", "factories", "railways", "telegraph"],
            TechnologyLevel.MODERN: ["electricity", "automobiles", "aircraft", "telecommunications"],
            TechnologyLevel.FUTURISTIC: ["computers", "space travel", "genetic engineering", "AI"],
            TechnologyLevel.MAGICAL: ["magic spells", "enchantments", "magical artifacts", "teleportation"],
            TechnologyLevel.STEAMPUNK: ["steam-powered automatons", "mechanical computers", "airships", "gear technology"]
        }

        return inventions.get(technology_level, ["basic tools"])

    def _generate_city_names(self, count: int) -> List[str]:
        """Generate city names"""
        prefixes = ["New", "Old", "Grand", "Royal", "Sacred", "Fortress", "Harbor", "Stone", "River", "Mountain"]
        suffixes = ["burg", "ville", "ton", "port", "heim", "gard", "mark", "shire", "worth", "keep"]

        names = []
        for _ in range(count):
            if random.random() < 0.3:
                name = f"{random.choice(prefixes)}{random.choice(suffixes)}"
            else:
                # Generate more unique name
                syllables = ["ka", "li", "mo", "ra", "te", "no", "shi", "ve", "an", "du"]
                num_syllables = random.randint(2, 3)
                name = "".join(random.choice(syllables) for _ in range(num_syllables)).capitalize()
            names.append(name)

        return names

    def _get_climate(self, terrain_type: str) -> str:
        """Get climate based on terrain"""
        climate_map = {
            "arctic": "arctic",
            "desert": "arid",
            "mountain": "alpine",
            "plains": "temperate",
            "forest": "temperate",
            "coastal": "maritime",
            "swamp": "tropical",
            "river": "temperate"
        }
        return climate_map.get(terrain_type, "temperate")

# Utility functions
def generate_world_cultures(width: int, height: int, num_cultures: int,
                          biome_map: np.ndarray, seed: Optional[int] = None) -> List[Culture]:
    """Generate multiple cultures across a world"""
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    cultures = []
    generator = CultureGenerator(seed=seed)

    # Find suitable locations for cultures
    culture_locations = []
    for _ in range(num_cultures * 3):  # Generate more candidates than needed
        x = random.randint(10, width - 10)
        y = random.randint(10, height - 10)
        terrain_type = _get_terrain_type_from_biome(biome_map[y, x])
        culture_locations.append((x, y, terrain_type))

    # Select diverse locations
    selected_locations = []
    terrain_types = set()

    for x, y, terrain in culture_locations:
        if terrain not in terrain_types or len(selected_locations) < num_cultures:
            selected_locations.append((x, y, terrain))
            terrain_types.add(terrain)
            if len(selected_locations) >= num_cultures:
                break

    # Generate cultures
    for i, (x, y, terrain) in enumerate(selected_locations[:num_cultures]):
        existing_cultures = [c.name for c in cultures]
        culture = generator.generate_culture(
            location=(y, x),
            terrain_type=terrain,
            neighboring_cultures=existing_cultures if i > 0 else None
        )
        cultures.append(culture)

    return cultures

def _get_terrain_type_from_biome(biome_value: int) -> str:
    """Convert biome value to terrain type"""
    biome_map = {
        0: "ocean", 1: "deep_ocean", 2: "beach", 3: "plains",
        4: "forest", 5: "dense_forest", 6: "jungle", 7: "desert",
        8: "savanna", 9: "tundra", 10: "ice", 11: "mountain",
        12: "high_mountain", 13: "hills", 14: "river", 15: "lake",
        16: "marsh", 17: "swamp"
    }
    return biome_map.get(biome_value, "plains")

def analyze_cultures(cultures: List[Culture]) -> Dict:
    """Analyze generated cultures"""
    analysis = {
        'total_cultures': len(cultures),
        'government_types': defaultdict(int),
        'religion_types': defaultdict(int),
        'technology_levels': defaultdict(int),
        'social_structures': defaultdict(int),
        'economic_systems': defaultdict(int),
        'total_population': sum(c.population for c in cultures),
        'avg_age': sum(c.cultural_age for c in cultures) / len(cultures) if cultures else 0,
        'cultural_values': defaultdict(int),
        'most_common_values': []
    }

    for culture in cultures:
        analysis['government_types'][culture.government_type.value] += 1
        analysis['religion_types'][culture.religion_type.value] += 1
        analysis['technology_levels'][culture.technology_level.value] += 1
        analysis['social_structures'][culture.social_structure.value] += 1
        analysis['economic_systems'][culture.economic_system.value] += 1

        for value in culture.values:
            analysis['cultural_values'][value.name] += 1

    # Find most common values
    if analysis['cultural_values']:
        sorted_values = sorted(analysis['cultural_values'].items(), key=lambda x: x[1], reverse=True)
        analysis['most_common_values'] = sorted_values[:5]

    return analysis

if __name__ == "__main__":
    # Example usage
    print("Generating cultures...")

    # Create sample biome map
    width, height = 50, 50
    biome_map = np.random.randint(0, 18, (height, width))

    # Generate cultures
    cultures = generate_world_cultures(width, height, 5, biome_map, seed=42)

    # Analyze cultures
    analysis = analyze_cultures(cultures)

    print(f"Generated {analysis['total_cultures']} cultures")
    print(f"Total population: {analysis['total_population']:,}")
    print(f"Average cultural age: {analysis['avg_age']:.0f} years")

    print("\nCulture Details:")
    for culture in cultures:
        print(f"\n{culture.name}")
        print(f"  Population: {culture.population:,}")
        print(f"  Government: {culture.government_type.value}")
        print(f"  Religion: {culture.religion_type.value}")
        print(f"  Technology: {culture.technology_level.value}")
        print(f"  Language: {culture.language.name}")
        print(f"  Values: {', '.join(v.name for v in culture.values)}")

    print(f"\nMost common cultural values: {[f'{v[0]} ({v[1]} cultures)' for v in analysis['most_common_values']]}")