const winston = require('winston');

class DMRecommendationService {
    constructor(hybridRecommender, contentService) {
        this.hybridRecommender = hybridRecommender;
        this.contentService = contentService;
        this.encounterTemplates = this.initializeEncounterTemplates();
        this.storyHooks = this.initializeStoryHooks();
        this.npcTemplates = this.initializeNPCTemplates();
        this.treasureDistributions = this.initializeTreasureDistributions();
        this.difficultyFormulas = this.initializeDifficultyFormulas();
    }

    // Initialize encounter templates
    initializeEncounterTemplates() {
        return {
            combat: {
                singleBoss: {
                    name: 'Single Boss Encounter',
                    description: 'One powerful enemy against the party',
                    difficultyMultiplier: 1.5,
                    recommendedActions: ['legendary_actions', 'lair_actions', 'multiattack'],
                    tactics: ['focus_fire', 'action_economy_disruption', 'environment_advantage'],
                    themes: ['epic', 'climactic', 'personal_stakes'],
                    setupComplexity: 'low'
                },
                multipleEnemies: {
                    name: 'Multiple Enemies Encounter',
                    description: 'Several enemies working together',
                    difficultyMultiplier: 1.0,
                    recommendedActions: ['coordinate_attacks', 'flanking', 'support_roles'],
                    tactics: ['divide_and_conquer', 'prioritize_threats', 'area_control'],
                    themes: ['tactical', 'teamwork', 'strategy'],
                    setupComplexity: 'medium'
                },
                horde: {
                    name: 'Horde Encounter',
                    description: 'Many weaker enemies overwhelming the party',
                    difficultyMultiplier: 0.8,
                    recommendedActions: ['swarm_tactics', 'surround', 'attrition'],
                    tactics: ['area_effects', 'choke_points', 'morale_checks'],
                    themes: ['desperate', 'overwhelming', 'survival'],
                    setupComplexity: 'low'
                },
                mixedForce: {
                    name: 'Mixed Force Encounter',
                    description: 'Variety of enemy types with different roles',
                    difficultyMultiplier: 1.2,
                    recommendedActions: ['role_specialization', 'combined_arms', 'support'],
                    tactics: ['target_prioritization', 'adaptation', 'synergy'],
                    themes: ['complex', 'strategic', 'dynamic'],
                    setupComplexity: 'high'
                }
            },
            social: {
                negotiation: {
                    name: 'Negotiation Encounter',
                    description: 'Social interaction with consequences',
                    difficultyMultiplier: 0.5,
                    recommendedSkills: ['persuasion', 'deception', 'insight', 'intimidation'],
                    outcomes: ['favorable_terms', 'information_gathering', 'alliance_building'],
                    themes: ['diplomacy', 'intrigue', 'compromise'],
                    setupComplexity: 'medium'
                },
                investigation: {
                    name: 'Investigation Encounter',
                    description: 'Gathering clues and solving mysteries',
                    difficultyMultiplier: 0.7,
                    recommendedSkills: ['investigation', 'perception', 'insight', 'arcana'],
                    challenges: ['hidden_clues', 'misinformation', 'time_pressure'],
                    themes: ['mystery', 'discovery', 'puzzle_solving'],
                    setupComplexity: 'high'
                },
                persuasion: {
                    name: 'Persuasion Encounter',
                    description: 'Convincing NPCs to take specific actions',
                    difficultyMultiplier: 0.6,
                    recommendedSkills: ['persuasion', 'performance', 'deception'],
                    approaches: ['emotional_appeal', 'logical_argument', 'bargaining'],
                    themes: ['influence', 'leadership', 'charisma'],
                    setupComplexity: 'low'
                }
            },
            exploration: {
                dungeonCrawl: {
                    name: 'Dungeon Crawl',
                    description: 'Systematic exploration of dangerous location',
                    difficultyMultiplier: 1.0,
                    challenges: ['traps', 'puzzles', 'resource_management'],
                    rewards: ['treasure', 'lore', 'story_progression'],
                    themes: ['adventure', 'discovery', 'danger'],
                    setupComplexity: 'high'
                },
                wilderness: {
                    name: 'Wilderness Exploration',
                    description: 'Navigation through natural hazards',
                    difficultyMultiplier: 0.8,
                    challenges: ['navigation', 'weather', 'natural_dangers', 'random_encounters'],
                    skills: ['survival', 'nature', 'perception'],
                    themes: ['nature', 'survival', 'journey'],
                    setupComplexity: 'medium'
                },
                urban: {
                    name: 'Urban Exploration',
                    description: 'Navigating city environments and social structures',
                    difficultyMultiplier: 0.7,
                    challenges: ['social_navigation', 'information_gathering', 'urban_dangers'],
                    skills: ['investigation', 'persuasion', 'stealth', 'insight'],
                    themes: ['civilization', 'intrigue', 'opportunity'],
                    setupComplexity: 'high'
                }
            },
            puzzle: {
                environmental: {
                    name: 'Environmental Puzzle',
                    description: 'Using environment to solve challenges',
                    difficultyMultiplier: 0.6,
                    elements: ['mechanisms', 'physics', 'pattern_recognition'],
                    skills: ['investigation', 'perception', 'athletics', 'arcana'],
                    themes: ['intellectual', 'creative', 'observational'],
                    setupComplexity: 'medium'
                },
                riddle: {
                    name: 'Riddle Challenge',
                    description: 'Wordplay and lateral thinking puzzles',
                    difficultyMultiplier: 0.5,
                    elements: ['wordplay', 'logic', 'creativity', 'knowledge'],
                    skills: ['investigation', 'arcana', 'history', 'religion'],
                    themes: ['intellectual', 'mysterious', 'cerebral'],
                    setupComplexity: 'low'
                },
                mechanical: {
                    name: 'Mechanical Puzzle',
                    description: 'Complex devices and mechanisms',
                    difficultyMultiplier: 0.7,
                    elements: ['gears', 'levers', 'timing', 'coordination'],
                    skills: ['investigation', 'tinker_tools', 'athletics'],
                    themes: ['technical', 'precise', 'collaborative'],
                    setupComplexity: 'high'
                }
            }
        };
    }

    // Initialize story hooks
    initializeStoryHooks() {
        return {
            personal: [
                {
                    title: 'Family in Peril',
                    description: 'A family member is kidnapped, threatened, or in trouble',
                    emotionalWeight: 'high',
                    playerInvolvement: 'direct',
                    complexity: 'medium',
                    themes: ['family', 'responsibility', 'time_pressure'],
                    potentialTwists: ['family_member_complicit', 'misunderstanding', 'larger_conspiracy']
                },
                {
                    title: 'Lost Heritage',
                    description: 'Discovering secrets about the character\'s ancestry',
                    emotionalWeight: 'medium',
                    playerInvolvement: 'direct',
                    complexity: 'high',
                    themes: ['identity', 'destiny', 'legacy'],
                    potentialTwists: ['unexpected_lineage', 'cursed_bloodline', 'hidden_powers']
                },
                {
                    title: 'Old Enemy Returns',
                    description: 'A past adversary seeks revenge or reconciliation',
                    emotionalWeight: 'high',
                    playerInvolvement: 'direct',
                    complexity: 'medium',
                    themes: ['revenge', 'forgiveness', 'growth'],
                    potentialTwists: ['misunderstood_motives', 'third_party_manipulation', 'change_of_heart']
                }
            ],
            world: [
                {
                    title: 'Ancient Evil Awakens',
                    description: 'A primordial threat stirs after centuries of dormancy',
                    emotionalWeight: 'epic',
                    playerInvolvement: 'indirect',
                    complexity: 'high',
                    themes: ['good_vs_evil', 'prophecy', 'sacrifice'],
                    potentialTwists: ['evil_misunderstood', 'players_part_of_prophecy', 'alternative_solutions']
                },
                {
                    title: 'Political Intrigue',
                    description: 'Kingdom-level politics and power struggles',
                    emotionalWeight: 'strategic',
                    playerInvolvement: 'indirect',
                    complexity: 'very_high',
                    themes: ['power', 'loyalty', 'morality'],
                    potentialTwists: ['double_agents', 'hidden_agendas', 'moral_ambiguity']
                },
                {
                    title: 'Natural Disaster',
                    description: 'Catastrophic events threaten civilization',
                    emotionalWeight: 'urgent',
                    playerInvolvement: 'indirect',
                    complexity: 'medium',
                    themes: ['survival', 'cooperation', 'sacrifice'],
                    potentialTwists: ['supernatural_cause', 'opportunistic_villains', 'unexpected_ally']
                }
            ],
            mystery: [
                {
                    title: 'Series of Disappearances',
                    description: 'People vanishing without explanation',
                    emotionalWeight: 'investigative',
                    playerInvolvement: 'investigative',
                    complexity: 'medium',
                    themes: ['mystery', 'danger', 'discovery'],
                    potentialTwists: ['supernatural_cause', 'government_conspiracy', 'mass_hallucination']
                },
                {
                    title: 'Strange Phenomenon',
                    description: 'Unnatural events defying explanation',
                    emotionalWeight: 'curious',
                    playerInvolvement: 'investigative',
                    complexity: 'high',
                    themes: ['unknown', 'discovery', 'reality_questioning'],
                    potentialTwists: ['experiment_gone_wrong', 'alternate_dimension', 'divine_intervention']
                },
                {
                    title: 'Historical Inconsistency',
                    description: 'Discovering that recorded history is wrong',
                    emotionalWeight: 'intellectual',
                    playerInvolvement: 'academic',
                    complexity: 'very_high',
                    themes: ['truth', 'knowledge', 'consequences'],
                    potentialTwists: ['intentional_deception', 'parallel_timelines', 'reality_glitch']
                }
            ],
            moral: [
                {
                    title: 'Lesser of Two Evils',
                    description: 'Forced choice between terrible options',
                    emotionalWeight: 'heavy',
                    playerInvolvement: 'direct',
                    complexity: 'high',
                    themes: ['morality', 'consequence', 'sacrifice'],
                    potentialTwists: ['third_option', 'hidden_consequences', 'moral_ambiguity']
                },
                {
                    title: 'Enemy with Just Cause',
                    description: 'Antagonist with understandable motivations',
                    emotionalWeight: 'conflicted',
                    playerInvolvement: 'emotional',
                    complexity: 'very_high',
                    themes: ['empathy', 'justice', 'understanding'],
                    potentialTwists: ['mutual_enemy', 'moral_alignment', 'peaceful_resolution']
                },
                {
                    title: 'Power Temptation',
                    description: 'Opportunity to gain power at moral cost',
                    emotionalWeight: 'tempting',
                    playerInvolvement: 'personal',
                    complexity: 'medium',
                    themes: ['corruption', 'power', 'choices'],
                    potentialTwists: ['power_with_price', 'unexpected_benefits', 'moral_transformation']
                }
            ]
        };
    }

    // Initialize NPC templates
    initializeNPCTemplates() {
        return {
            allies: {
                mentor: {
                    name: 'Mentor Figure',
                    role: 'guidance, training, wisdom',
                    personality: ['wise', 'patient', 'mysterious'],
                    appearance: ['aged', 'distinguished', 'knowledgeable'],
                    motivations: ['passing_knowledge', 'correcting_past_mistakes', 'finding_successor'],
                    complications: ['hidden_agenda', 'personal_tragedy', 'power_limitations'],
                    storyFunction: 'quest_giver'
                },
                specialist: {
                    name: 'Specialist Expert',
                    role: 'specific skills, knowledge, or services',
                    personality: ['focused', 'eccentric', 'professional'],
                    appearance: ['distinctive', 'practical', 'skilled'],
                    motivations: ['professional_pride', 'personal_interest', 'payment'],
                    complications: ['rival_competitors', 'dangerous_knowledge', 'moral_boundaries'],
                    storyFunction: 'resource_provider'
                },
                contact: {
                    name: 'Information Broker',
                    role: 'gathering and trading information',
                    personality: ['well_connected', 'discreet', 'opportunistic'],
                    appearance: ['unremarkable', 'adaptable', 'observant'],
                    motivations: ['profit', 'power', 'curiosity'],
                    complications: ['dangerous_clients', 'conflicting_loyalties', 'targeted_by_enemies'],
                    storyFunction: 'information_source'
                }
            },
            neutrals: {
                merchant: {
                    name: 'Merchant Trader',
                    role: 'buying and selling goods',
                    personality: ['pragmatic', 'negotiating', 'opportunistic'],
                    appearance: ['wealthy', 'travelled', 'well-equipped'],
                    motivations: ['profit', 'expansion', 'security'],
                    complications: ['competition', 'dangerous_routes', 'rare_items'],
                    storyFunction: 'service_provider'
                },
                guard: {
                    name: 'Authority Figure',
                    role: 'maintaining order and security',
                    personality: ['authoritative', 'by_the_book', 'protective'],
                    appearance: ['uniformed', 'vigilant', 'armed'],
                    motivations: ['duty', 'order', 'citizen_safety'],
                    complications: ['corruption', 'bureaucracy', 'underfunded'],
                    storyFunction: 'obstacle_or_ally'
                },
                scholar: {
                    name: 'Knowledge Seeker',
                    role: 'research and learning',
                    personality: ['curious', 'methodical', 'absent-minded'],
                    appearance: ['scholarly', 'bookish', 'intense'],
                    motivations: ['discovery', 'preservation', 'understanding'],
                    complications: ['dangerous_knowledge', 'academic_rivalry', 'obsession'],
                    storyFunction: 'information_source'
                }
            },
            villains: {
                mastermind: {
                    name: 'Mastermind',
                    role: 'planning complex schemes',
                    personality: ['intelligent', 'patient', 'manipulative'],
                    appearance: ['refined', 'controlled', 'unassuming'],
                    motivations: ['power', 'control', 'ideology'],
                    complications: ['overconfidence', 'emotional_weakness', 'betrayal'],
                    storyFunction: 'primary_antagonist'
                },
                brute: {
                    name: 'Enforcer',
                    role: 'physical intimidation and force',
                    personality: ['aggressive', 'direct', 'intimidating'],
                    appearance: ['powerful', 'imposing', 'armed'],
                    motivations: ['power', 'respect', 'basic_needs'],
                    complications: ['simple_minded', 'easily_manipulated', 'honor_code'],
                    storyFunction: 'physical_threat'
                },
                charmer: {
                    name: 'Manipulator',
                    role: 'social influence and deception',
                    personality: ['charismatic', 'deceptive', 'adaptable'],
                    appearance: ['attractive', 'stylish', 'persuasive'],
                    motivations: ['personal_gain', 'admiration', 'control'],
                    complications: ['narcissism', 'underestimation', 'emotional_vulnerability'],
                    storyFunction: 'social_antagonist'
                }
            },
            wildcards: {
                trickster: {
                    name: 'Trickster',
                    role: 'chaos and unpredictability',
                    personality: ['mischievous', 'unreliable', 'clever'],
                    appearance: ['variable', 'eye-catching', 'expressive'],
                    motivations: ['entertainment', 'chaos', 'personal_amusement'],
                    complications: ['unpredictable', 'hidden_agenda', 'accidental_help'],
                    storyFunction: 'chaotic_element'
                },
                outcast: {
                    name: 'Outcast',
                    role: 'outsider perspective',
                    personality: ['wary', 'independent', 'misunderstood'],
                    appearance: ['weathered', 'self-sufficient', 'guarded'],
                    motivations: ['survival', 'acceptance', 'revenge'],
                    complications: ['trust_issues', 'social_inexperience', 'dangerous_secrets'],
                    storyFunction: 'unexpected_ally'
                },
                fanatic: {
                    name: 'Zealot',
                    role: 'unwavering belief system',
                    personality: ['devout', 'uncompromising', 'passionate'],
                    appearance: 'dedicated',
                    motivations: ['faith', 'ideology', 'purpose'],
                    complications: ['blind_faith', 'extreme_methods', 'manipulation'],
                    storyFunction: 'ideological_obstacle'
                }
            }
        };
    }

    // Initialize treasure distributions
    initializeTreasureDistributions() {
        return {
            byChallenge: {
                trivial: {
                    copper: '10-50',
                    silver: '5-20',
                    gold: '0-5',
                    gems: 'rare',
                    magicItems: 'very_rare',
                    consumables: 'common'
                },
                easy: {
                    copper: '50-200',
                    silver: '20-100',
                    gold: '10-50',
                    gems: 'uncommon',
                    magicItems: 'rare',
                    consumables: 'common'
                },
                medium: {
                    copper: '200-500',
                    silver: '100-300',
                    gold: '50-150',
                    gems: 'common',
                    magicItems: 'uncommon',
                    consumables: 'common'
                },
                hard: {
                    copper: '500-1000',
                    silver: '300-600',
                    gold: '150-400',
                    gems: 'common',
                    magicItems: 'uncommon',
                    consumables: 'uncommon'
                },
                deadly: {
                    copper: '1000-2000',
                    silver: '600-1200',
                    gold: '400-800',
                    gems: 'uncommon',
                    magicItems: 'rare',
                    consumables: 'uncommon'
                },
                legendary: {
                    copper: '2000+',
                    silver: '1200+',
                    gold: '800+',
                    gems: 'rare',
                    magicItems: 'very_rare',
                    consumables: 'rare'
                }
            },
            byLevel: {
                '1-4': {
                    totalValue: '100-500 gp',
                    magicItems: 'common_consumables',
                    gems: 'ornamental_stones',
                    art: 'minor_artwork'
                },
                '5-10': {
                    totalValue: '500-4000 gp',
                    magicItems: 'common_uncommon',
                    gems: 'semiprecious_stones',
                    art: 'quality_artwork'
                },
                '11-16': {
                    totalValue: '4000-25000 gp',
                    magicItems: 'uncommon_rare',
                    gems: 'precious_stones',
                    art: 'valuable_artwork'
                },
                '17-20': {
                    totalValue: '25000+ gp',
                    magicItems: 'rare_very_rare',
                    gems: 'gemstones',
                    art: 'masterwork_artwork'
                }
            },
            byType: {
                hoard: {
                    description: 'Large collection of wealth',
                    composition: 'mostly_coins',
                    specialItems: 'jewelry, art objects',
                    magicItems: 'varied'
                },
                equipment: {
                    description: 'Weapons, armor, tools',
                    composition: 'mostly_equipment',
                    specialItems: 'masterwork_items',
                    magicItems: 'focused_on_function'
                },
                knowledge: {
                    description: 'Books, maps, information',
                    composition: 'mostly_information',
                    specialItems: 'rare_books, maps',
                    magicItems: 'scrolls, tombs'
                },
                consumables: {
                    description: 'Potions, scrolls, one-use items',
                    composition: 'mostly_consumables',
                    specialItems: 'rare_potions',
                    magicItems: 'single_use'
                }
            }
        };
    }

    // Initialize difficulty formulas
    initializeDifficultyFormulas() {
        return {
            // Encounter difficulty calculations based on DMG guidelines
            thresholds: {
                1: { easy: 25, medium: 50, hard: 75, deadly: 100 },
                2: { easy: 50, medium: 100, hard: 150, deadly: 200 },
                3: { easy: 75, medium: 150, hard: 225, deadly: 350 },
                4: { easy: 125, medium: 250, hard: 375, deadly: 500 },
                5: { easy: 250, medium: 500, hard: 750, deadly: 1000 },
                6: { easy: 300, medium: 600, hard: 900, deadly: 1400 },
                7: { easy: 350, medium: 750, hard: 1100, deadly: 1600 },
                8: { easy: 450, medium: 900, hard: 1400, deady: 2100 },
                9: { easy: 550, medium: 1100, hard: 1600, deadly: 2400 },
                10: { easy: 600, medium: 1200, hard: 1900, deadly: 2800 },
                11: { easy: 800, medium: 1600, hard: 2400, deadly: 3600 },
                12: { easy: 1000, medium: 2000, hard: 3000, deadly: 4500 },
                13: { easy: 1100, medium: 2200, hard: 3400, deadly: 5100 },
                14: { easy: 1250, medium: 2500, hard: 3800, deadly: 5700 },
                15: { easy: 1400, medium: 2800, hard: 4300, deadly: 6400 },
                16: { easy: 1600, medium: 3200, hard: 4800, deadly: 7200 },
                17: { easy: 2000, medium: 3900, hard: 5900, deadly: 8800 },
                18: { easy: 2100, medium: 4200, hard: 6300, deadly: 9500 },
                19: { easy: 2400, medium: 4900, hard: 7300, deadly: 10900 },
                20: { easy: 2800, medium: 5700, hard: 8500, deadly: 12700 }
            },
            multipliers: {
                1: 1,
                2: 1.5,
                3: 2,
                4: 2.5,
                5: 3,
                6: 4,
                7: 5,
                8: 6,
                9: 7,
                10: 8,
                11: 9,
                12: 10,
                13: 11,
                14: 12,
                15: 13,
                16: 14
            }
        };
    }

    // Generate encounter difficulty recommendations
    async generateEncounterRecommendations(userId, partyInfo, campaignContext, numRecommendations = 5) {
        try {
            const { level, size, composition, experience } = partyInfo;
            const { environment, theme, recentEncounters } = campaignContext;

            // Calculate party capabilities
            const partyCapabilities = this.calculatePartyCapabilities(partyInfo);

            // Generate encounter suggestions
            const encounterRecommendations = [];

            // Combat encounters
            const combatEncounters = this.generateCombatEncounters(
                partyCapabilities, campaignContext, numRecommendations
            );
            encounterRecommendations.push(...combatEncounters);

            // Social encounters
            const socialEncounters = this.generateSocialEncounters(
                partyCapabilities, campaignContext, Math.ceil(numRecommendations / 2)
            );
            encounterRecommendations.push(...socialEncounters);

            // Exploration encounters
            const explorationEncounters = this.generateExplorationEncounters(
                partyCapabilities, campaignContext, Math.ceil(numRecommendations / 2)
            );
            encounterRecommendations.push(...explorationEncounters);

            // Sort by relevance and variety
            const sortedRecommendations = this.rankEncounterRecommendations(
                encounterRecommendations, partyCapabilities, campaignContext
            );

            return {
                encounters: sortedRecommendations.slice(0, numRecommendations),
                difficultyAnalysis: this.analyzePartyDifficulty(partyCapabilities),
                balancingTips: this.generateBalancingTips(partyCapabilities),
                varietySuggestions: this.generateVarietySuggestions(recentEncounters)
            };

        } catch (error) {
            winston.error('Error generating encounter recommendations:', error);
            return { encounters: [], difficultyAnalysis: {}, balancingTips: [], varietySuggestions: [] };
        }
    }

    // Calculate party capabilities
    calculatePartyCapabilities(partyInfo) {
        const { level, size, composition, experience } = partyInfo;

        const capabilities = {
            level,
            size,
            averageLevel: level,
            totalLevels: level * size,
            // Calculate CR threshold
            thresholds: this.difficultyFormulas.thresholds[level] || this.difficultyFormulas.thresholds[10],
            // Party composition analysis
            roles: this.analyzePartyRoles(composition),
            // Estimated power level
            powerLevel: this.calculatePowerLevel(level, size, experience),
            // Strengths and weaknesses
            strengths: [],
            weaknesses: []
        };

        // Add role-based strengths
        if (capabilities.roles.tank >= 1) {
            capabilities.strengths.push('front_line_defense', 'damage_absorption');
        }
        if (capabilities.roles.healer >= 1) {
            capabilities.strengths.push('healing', 'sustain');
        }
        if (capabilities.roles.damage >= 2) {
            capabilities.strengths.push('high_damage_output');
        }
        if (capabilities.roles.caster >= 2) {
            capabilities.strengths.push('magical_power', 'versatility');
        }
        if (capabilities.roles.skill >= 2) {
            capabilities.strengths.push('skill_mastery', 'utility');
        }

        // Identify weaknesses
        if (capabilities.roles.tank === 0) {
            capabilities.weaknesses.push('vulnerable_front_line', 'squishy');
        }
        if (capabilities.roles.healer === 0) {
            capabilities.weaknesses.push('limited_healing', 'resource_drain');
        }
        if (capabilities.roles.damage === 0) {
            capabilities.weaknesses.push('low_damage_output');
        }
        if (capabilities.roles.caster === 0) {
            capabilities.weaknesses.push('no_magical_solutions');
        }
        if (size < 3) {
            capabilities.weaknesses.push('action_economy_disadvantage');
        }
        if (size > 6) {
            capabilities.strengths.push('action_economy_advantage');
        }

        return capabilities;
    }

    // Analyze party roles
    analyzePartyRoles(composition) {
        const roles = {
            tank: 0,
            healer: 0,
            damage: 0,
            caster: 0,
            skill: 0,
            support: 0
        };

        composition.forEach(character => {
            const classRoles = this.getClassRoles(character.class);
            Object.keys(classRoles).forEach(role => {
                if (classRoles[role]) {
                    roles[role] += classRoles[role];
                }
            });
        });

        return roles;
    }

    // Get class roles
    getClassRoles(characterClass) {
        const classRoles = {
            fighter: { tank: 1, damage: 1, support: 0.5 },
            paladin: { tank: 1, healer: 0.5, damage: 1, support: 0.5 },
            barbarian: { tank: 1, damage: 1, support: 0 },
            ranger: { damage: 1, skill: 1, support: 0.5 },
            rogue: { damage: 1, skill: 1, support: 0.5 },
            monk: { damage: 1, support: 0.5 },
            wizard: { caster: 1, damage: 1, support: 0.5 },
            sorcerer: { caster: 1, damage: 1, support: 0.3 },
            warlock: { caster: 1, damage: 1, support: 0.3 },
            cleric: { healer: 1, caster: 0.5, support: 1, tank: 0.5 },
            druid: { healer: 0.5, caster: 1, support: 0.5, damage: 0.5 },
            bard: { support: 1, caster: 0.5, healer: 0.5, skill: 1 },
            artificer: { support: 1, damage: 0.5, skill: 0.5 }
        };

        return classRoles[characterClass.toLowerCase()] || { damage: 0.5 };
    }

    // Calculate power level
    calculatePowerLevel(level, size, experience) {
        const basePower = level * size;
        const experienceMultiplier = 1 + (experience * 0.1); // 10% bonus per experience level
        const sizeMultiplier = size < 3 ? 0.8 : size > 6 ? 1.2 : 1;

        return Math.round(basePower * experienceMultiplier * sizeMultiplier);
    }

    // Generate combat encounters
    generateCombatEncounters(partyCapabilities, campaignContext, numRecommendations) {
        const encounters = [];
        const { environment, theme } = campaignContext;

        // Get combat templates
        const combatTypes = Object.keys(this.encounterTemplates.combat);

        combatTypes.forEach(combatType => {
            const template = this.encounterTemplates.combat[combatType];
            const encounter = this.buildCombatEncounter(template, partyCapabilities, campaignContext);

            if (encounter) {
                encounters.push({
                    ...encounter,
                    type: 'combat',
                    subtype: combatType,
                    template: template,
                    score: this.calculateEncounterScore(encounter, partyCapabilities, campaignContext)
                });
            }
        });

        return encounters.sort((a, b) => b.score - a.score);
    }

    // Build combat encounter
    buildCombatEncounter(template, partyCapabilities, campaignContext) {
        const { environment, theme } = campaignContext;
        const thresholds = partyCapabilities.thresholds;

        // Calculate target XP based on difficulty
        const targetXP = {
            easy: thresholds.easy * template.difficultyMultiplier,
            medium: thresholds.medium * template.difficultyMultiplier,
            hard: thresholds.hard * template.difficultyMultiplier,
            deadly: thresholds.deadly * template.difficultyMultiplier
        };

        // Build encounter for each difficulty
        const encounter = {
            name: template.name,
            description: template.description,
            difficulties: {},
            tactics: template.tactics,
            setupComplexity: template.setupComplexity,
            environment: environment,
            theme: theme,
            recommendedActions: template.recommendedActions
        };

        Object.keys(targetXP).forEach(difficulty => {
            const enemies = this.selectEnemiesForXP(targetXP[difficulty], template, campaignContext);
            encounter.difficulties[difficulty] = {
                xp: Math.round(targetXP[difficulty]),
                enemies: enemies,
                adjustments: this.calculateDifficultyAdjustments(enemies, partyCapabilities)
            };
        });

        return encounter;
    }

    // Select enemies for XP budget
    selectEnemiesForXP(targetXP, template, campaignContext) {
        // This would typically query a database of monsters
        // For now, return representative enemy selections
        const enemyOptions = {
            singleBoss: [
                { name: 'Adult Red Dragon', cr: 17, xp: 7600, type: 'dragon', alignment: 'chaotic evil' },
                { name: 'Archmage', cr: 12, xp: 8400, type: 'humanoid', alignment: 'any' },
                { name: 'Ancient Blue Dragon', cr: 23, xp: 25000, type: 'dragon', alignment: 'lawful evil' }
            ],
            multipleEnemies: [
                { name: 'Ogre', cr: 2, xp: 450, type: 'giant', alignment: 'chaotic evil' },
                { name: 'Hobgoblin Captain', cr: 3, xp: 700, type: 'humanoid', alignment: 'lawful evil' },
                { name: 'Veteran', cr: 3, xp: 700, type: 'humanoid', alignment: 'any' }
            ],
            horde: [
                { name: 'Goblin', cr: 0.25, xp: 25, type: 'humanoid', alignment: 'neutral evil' },
                { name: 'Kobold', cr: 0.125, xp: 25, type: 'humanoid', alignment: 'lawful evil' },
                { name: 'Bandit', cr: 0.125, xp: 25, type: 'humanoid', alignment: 'any non-good' }
            ],
            mixedForce: [
                { name: 'Ogre', cr: 2, xp: 450, type: 'giant', alignment: 'chaotic evil' },
                { name: 'Goblin', cr: 0.25, xp: 25, type: 'humanoid', alignment: 'neutral evil' },
                { name: 'Hobgoblin', cr: 1, xp: 200, type: 'humanoid', alignment: 'lawful evil' }
            ]
        };

        const availableEnemies = enemyOptions[template.type] || enemyOptions.multipleEnemies;
        const selectedEnemies = [];
        let currentXP = 0;

        // Greedy selection to match XP budget
        availableEnemies.forEach(enemy => {
            if (currentXP < targetXP) {
                const quantity = Math.min(
                    Math.floor((targetXP - currentXP) / enemy.xp),
                    Math.floor(targetXP / enemy.xp)
                );

                if (quantity > 0) {
                    selectedEnemies.push({
                        ...enemy,
                        quantity: quantity
                    });
                    currentXP += enemy.xp * quantity;
                }
            }
        });

        return selectedEnemies;
    }

    // Calculate difficulty adjustments
    calculateDifficultyAdjustments(enemies, partyCapabilities) {
        const adjustments = {
            actionEconomy: 0,
            resistances: [],
            vulnerabilities: [],
            tactics: []
        };

        // Count total enemy actions
        const totalEnemyActions = enemies.reduce((sum, enemy) => sum + (enemy.quantity || 1), 0);
        const partyActions = partyCapabilities.size;

        if (totalEnemyActions > partyActions * 1.5) {
            adjustments.actionEconomy = 'disadvantage';
            adjustments.tactics.push('focus_fire', 'priority_targets');
        } else if (totalEnemyActions < partyActions * 0.7) {
            adjustments.actionEconomy = 'advantage';
            adjustments.tactics.push('coordinate_attacks', 'environment_usage');
        }

        // Analyze party strengths vs enemy types
        if (partyCapabilities.strengths.includes('magical_power')) {
            adjustments.vulnerabilities.push('saves_vs_magic', 'concentration_spells');
        }

        if (partyCapabilities.strengths.includes('high_damage_output')) {
            adjustments.tactics.push('hit_and_run', 'defensive_positioning');
        }

        if (partyCapabilities.weaknesses.includes('vulnerable_front_line')) {
            adjustments.tactics.push('focus_ranged', 'mobility_advantage');
        }

        return adjustments;
    }

    // Generate social encounters
    generateSocialEncounters(partyCapabilities, campaignContext, numRecommendations) {
        const encounters = [];
        const { environment, theme } = campaignContext;

        const socialTypes = Object.keys(this.encounterTemplates.social);

        socialTypes.forEach(socialType => {
            const template = this.encounterTemplates.social[socialType];
            const encounter = this.buildSocialEncounter(template, partyCapabilities, campaignContext);

            if (encounter) {
                encounters.push({
                    ...encounter,
                    type: 'social',
                    subtype: socialType,
                    template: template,
                    score: this.calculateEncounterScore(encounter, partyCapabilities, campaignContext)
                });
            }
        });

        return encounters.sort((a, b) => b.score - a.score);
    }

    // Build social encounter
    buildSocialEncounter(template, partyCapabilities, campaignContext) {
        const { environment, theme } = campaignContext;

        const encounter = {
            name: template.name,
            description: template.description,
            recommendedSkills: template.recommendedSkills,
            outcomes: template.outcomes,
            themes: template.themes,
            setupComplexity: template.setupComplexity,
            environment: environment,
            theme: theme,
            challenges: template.challenges || [],
            npcs: this.generateNPCsForEncounter(template, campaignContext),
            complications: this.generateSocialComplications(template, partyCapabilities)
        };

        return encounter;
    }

    // Generate NPCs for encounter
    generateNPCsForEncounter(template, campaignContext) {
        const npcTypes = ['contact', 'specialist', 'authority'];
        const npcs = [];

        npcTypes.forEach(type => {
            const npcTemplate = this.npcTemplates.neutrals[type];
            if (npcTemplate) {
                npcs.push({
                    name: `${npcTemplate.name} of ${campaignContext.environment}`,
                    role: npcTemplate.role,
                    personality: this.shuffleArray(npcTemplate.personality).slice(0, 2),
                    motivations: this.shuffleArray(npcTemplate.motivations).slice(0, 1),
                    complications: this.shuffleArray(npcTemplate.complications).slice(0, 1),
                    storyFunction: npcTemplate.storyFunction
                });
            }
        });

        return npcs;
    }

    // Generate social complications
    generateSocialComplications(template, partyCapabilities) {
        const complications = [];

        if (partyCapabilities.weaknesses.includes('no_magical_solutions')) {
            complications.push('requires_magical_assistance');
        }

        if (partyCapabilities.strengths.includes('skill_mastery')) {
            complications.push('complex_negotiation', 'multiple_parties');
        }

        if (partyCapabilities.size < 4) {
            complications.push('outnumbered', 'intimidation_factors');
        }

        return complications;
    }

    // Generate exploration encounters
    generateExplorationEncounters(partyCapabilities, campaignContext, numRecommendations) {
        const encounters = [];
        const { environment, theme } = campaignContext;

        const explorationTypes = Object.keys(this.encounterTemplates.exploration);

        explorationTypes.forEach(explorationType => {
            const template = this.encounterTemplates.exploration[explorationType];
            const encounter = this.buildExplorationEncounter(template, partyCapabilities, campaignContext);

            if (encounter) {
                encounters.push({
                    ...encounter,
                    type: 'exploration',
                    subtype: explorationType,
                    template: template,
                    score: this.calculateEncounterScore(encounter, partyCapabilities, campaignContext)
                });
            }
        });

        return encounters.sort((a, b) => b.score - a.score);
    }

    // Build exploration encounter
    buildExplorationEncounter(template, partyCapabilities, campaignContext) {
        const { environment, theme } = campaignContext;

        const encounter = {
            name: template.name,
            description: template.description,
            challenges: template.challenges,
            rewards: template.rewards,
            themes: template.themes,
            setupComplexity: template.setupComplexity,
            environment: environment,
            theme: theme,
            skills: template.skills || [],
            obstacles: this.generateExplorationObstacles(template, partyCapabilities),
            discoveries: this.generateExplorationDiscoveries(template, campaignContext)
        };

        return encounter;
    }

    // Generate exploration obstacles
    generateExplorationObstacles(template, partyCapabilities) {
        const obstacles = [];

        if (template.challenges.includes('traps')) {
            obstacles.push({
                type: 'trap',
                difficulty: 'medium',
                skills_required: ['perception', 'investigation', 'thieves_tools'],
                consequence: 'damage_debuff'
            });
        }

        if (template.challenges.includes('puzzles')) {
            obstacles.push({
                type: 'puzzle',
                difficulty: 'medium',
                skills_required: ['investigation', 'arcana', 'history'],
                consequence: 'progress_blocked'
            });
        }

        if (template.challenges.includes('resource_management')) {
            obstacles.push({
                type: 'resource',
                difficulty: 'medium',
                skills_required: ['survival', 'nature'],
                consequence: 'exhaustion'
            });
        }

        return obstacles;
    }

    // Generate exploration discoveries
    generateExplorationDiscoveries(template, campaignContext) {
        return [
            {
                type: 'treasure',
                value: 'moderate',
                description: 'Hidden cache from previous adventurers'
            },
            {
                type: 'lore',
                value: 'high',
                description: 'Ancient inscriptions revealing local history'
            },
            {
                type: 'story_hook',
                value: 'campaign',
                description: 'Clues leading to next major adventure'
            }
        ];
    }

    // Calculate encounter score
    calculateEncounterScore(encounter, partyCapabilities, campaignContext) {
        let score = 0;

        // Base score
        score += 5;

        // Environment match
        if (encounter.environment === campaignContext.environment) {
            score += 3;
        }

        // Theme match
        if (encounter.theme === campaignContext.theme) {
            score += 2;
        }

        // Party size consideration
        if (partyCapabilities.size >= 4 && encounter.setupComplexity === 'high') {
            score += 2;
        } else if (partyCapabilities.size < 4 && encounter.setupComplexity === 'low') {
            score += 2;
        }

        // Party strength/weakness considerations
        if (encounter.type === 'combat' && partyCapabilities.strengths.includes('high_damage_output')) {
            score += 2;
        }

        if (encounter.type === 'social' && partyCapabilities.strengths.includes('skill_mastery')) {
            score += 2;
        }

        if (encounter.type === 'exploration' && partyCapabilities.roles.skill >= 2) {
            score += 2;
        }

        return score;
    }

    // Rank encounter recommendations
    rankEncounterRecommendations(encounters, partyCapabilities, campaignContext) {
        // Ensure variety in encounter types
        const typeCounts = {};
        const ranked = [];

        encounters.forEach(encounter => {
            typeCounts[encounter.type] = (typeCounts[encounter.type] || 0) + 1;

            // Adjust score based on variety
            if (typeCounts[encounter.type] > 2) {
                encounter.score *= 0.7; // Reduce score for too many of same type
            }

            ranked.push(encounter);
        });

        return ranked.sort((a, b) => b.score - a.score);
    }

    // Analyze party difficulty
    analyzePartyDifficulty(partyCapabilities) {
        const analysis = {
            overallLevel: this.assessOverallDifficulty(partyCapabilities),
            strengths: partyCapabilities.strengths,
            weaknesses: partyCapabilities.weaknesses,
            recommendations: []
        };

        // Generate recommendations
        if (partyCapabilities.weaknesses.includes('vulnerable_front_line')) {
            analysis.recommendations.push('Consider fewer heavy melee encounters or provide defensive options');
        }

        if (partyCapabilities.weaknesses.includes('limited_healing')) {
            analysis.recommendations.push('Include more short rest opportunities or healing resources');
        }

        if (partyCapabilities.strengths.includes('high_damage_output')) {
            analysis.recommendations.push('Can handle higher CR enemies with fewer numbers');
        }

        if (partyCapabilities.size < 3) {
            analysis.recommendations.push('Be mindful of action economy disadvantages');
        }

        return analysis;
    }

    // Assess overall difficulty
    assessOverallDifficulty(partyCapabilities) {
        const { level, size, powerLevel } = partyCapabilities;

        if (level <= 3) return 'beginner';
        if (level <= 7) return 'novice';
        if (level <= 11) return 'intermediate';
        if (level <= 15) return 'advanced';
        return 'expert';
    }

    // Generate balancing tips
    generateBalancingTips(partyCapabilities) {
        const tips = [];

        if (partyCapabilities.roles.tank === 0) {
            tips.push('Use terrain and cover to help party survive');
        }

        if (partyCapabilities.roles.healer === 0) {
            tips.push('Provide potions and healing opportunities');
        }

        if (partyCapabilities.size < 4) {
            tips.push('Consider giving players useful magic items to balance action economy');
        }

        if (partyCapabilities.roles.caster >= 3) {
            tips.push('Include enemies with magic resistance or anti-magic abilities');
        }

        if (partyCapabilities.strengths.includes('magical_power')) {
            tips.push('Challenge with puzzles and social encounters that require creativity');
        }

        return tips;
    }

    // Generate variety suggestions
    generateVarietySuggestions(recentEncounters) {
        const recentTypes = recentEncounters.map(e => e.type);
        const suggestions = [];

        const encounterTypes = ['combat', 'social', 'exploration', 'puzzle'];

        encounterTypes.forEach(type => {
            if (!recentTypes.includes(type)) {
                suggestions.push({
                    type: type,
                    reason: `You haven't had a ${type} encounter recently`,
                    priority: recentTypes.length > 0 ? 'medium' : 'high'
                });
            }
        });

        return suggestions;
    }

    // Generate story hook recommendations
    async generateStoryHookRecommendations(userId, campaignContext, partyInfo, numRecommendations = 5) {
        try {
            const { theme, setting, recentEvents } = campaignContext;
            const { background, alignments, classes } = partyInfo;

            const hookRecommendations = [];

            // Get hooks from different categories
            const hookCategories = Object.keys(this.storyHooks);

            hookCategories.forEach(category => {
                const hooks = this.storyHooks[category];
                hooks.forEach(hook => {
                    const score = this.calculateHookScore(hook, campaignContext, partyInfo);
                    hookRecommendations.push({
                        ...hook,
                        category: category,
                        score: score,
                        implementation: this.generateHookImplementation(hook, campaignContext, partyInfo)
                    });
                });
            });

            // Sort and return top recommendations
            return {
                hooks: hookRecommendations
                    .sort((a, b) => b.score - a.score)
                    .slice(0, numRecommendations),
                integrationTips: this.generateIntegrationTips(campaignContext, partyInfo),
                timelineSuggestions: this.generateTimelineSuggestions(recentEvents)
            };

        } catch (error) {
            winston.error('Error generating story hook recommendations:', error);
            return { hooks: [], integrationTips: [], timelineSuggestions: [] };
        }
    }

    // Calculate hook score
    calculateHookScore(hook, campaignContext, partyInfo) {
        let score = 5; // Base score

        const { theme, setting } = campaignContext;
        const { background, alignments, classes } = partyInfo;

        // Theme alignment
        if (hook.themes.includes(theme)) {
            score += 3;
        }

        // Player background alignment
        if (hook.playerInvolvement === 'direct' && background) {
            score += 2;
        }

        // Alignment considerations
        if (alignments && alignments.some(a => a.includes('evil')) && hook.emotionalWeight === 'heavy') {
            score += 2;
        }

        // Class relevance
        if (classes && classes.some(c => ['cleric', 'paladin'].includes(c.toLowerCase())) &&
            hook.themes.includes('religion')) {
            score += 2;
        }

        return score;
    }

    // Generate hook implementation
    generateHookImplementation(hook, campaignContext, partyInfo) {
        const implementation = {
            setupSteps: [],
            keyNPCs: [],
            potentialOutcomes: [],
            followUpHooks: []
        };

        // Generate setup steps based on hook complexity
        if (hook.complexity === 'low') {
            implementation.setupSteps = [
                'Introduce inciting incident',
                'Present clear choice to players',
                'Allow immediate action'
            ];
        } else if (hook.complexity === 'medium') {
            implementation.setupSteps = [
                'Drop clues and foreshadowing',
                'Develop supporting characters',
                'Create decision points',
                'Build tension over multiple sessions'
            ];
        } else if (hook.complexity === 'high') {
            implementation.setupSteps = [
                'Establish multiple plot threads',
                'Create interconnected NPCs',
                'Design moral complexities',
                'Plan long-term consequences',
                'Prepare for player agency'
            ];
        }

        // Generate key NPCs
        implementation.keyNPCs = [
            {
                role: 'quest_giver',
                motivation: 'primary_driver',
                complication: hook.potentialTwists[0] || 'personal_stakes'
            },
            {
                role: 'antagonist',
                motivation: 'opposition',
                complication: 'hidden_agenda'
            }
        ];

        // Generate potential outcomes
        implementation.potentialOutcomes = [
            'success_with_complications',
            'partial_success',
            'unexpected_twist',
            'moral_ambiguity'
        ];

        // Generate follow-up hooks
        implementation.followUpHooks = hook.potentialTwists.map(twist => ({
            title: `The ${twist} Revelation`,
            description: `Story developments following the ${twist} twist`,
            priority: 'medium'
        }));

        return implementation;
    }

    // Generate integration tips
    generateIntegrationTips(campaignContext, partyInfo) {
        const tips = [];

        const { theme, setting } = campaignContext;

        tips.push(`Integrate the hook naturally into the ${setting} environment`);
        tips.push(`Ensure the hook aligns with your campaign's ${theme} theme`);
        tips.push('Create personal connections to party members');
        tips.push('Leave room for player agency and unexpected solutions');
        tips.push('Prepare for multiple potential outcomes');

        return tips;
    }

    // Generate timeline suggestions
    generateTimelineSuggestions(recentEvents) {
        const suggestions = [
            {
                timeframe: 'immediate',
                description: 'Hook that can be introduced in the next session',
                examples: ['messenger_arrives', 'stranger_in_tavern', 'emergency_situation']
            },
            {
                timeframe: 'short_term',
                description: 'Hook that develops over 2-3 sessions',
                examples: ['investigation_clues', 'buildup_events', 'rumors_spread']
            },
            {
                timeframe: 'long_term',
                description: 'Hook that unfolds over multiple sessions or arcs',
                examples: ['prophecy_unfolding', 'conspiracy_development', 'political_shifts']
            }
        ];

        return suggestions;
    }

    // Generate NPC recommendations
    async generateNPCRecommendations(userId, npcRequest, numRecommendations = 5) {
        try {
            const { role, setting, purpose, relationship } = npcRequest;

            const npcRecommendations = [];

            // Get appropriate NPC templates
            const applicableTemplates = this.getNPCTemplatesByRole(role);

            applicableTemplates.forEach(template => {
                const npc = this.generateNPCFromTemplate(template, npcRequest);
                const score = this.calculateNPCScore(npc, npcRequest);
                npcRecommendations.push({
                    ...npc,
                    score: score,
                    template: template.name
                });
            });

            // Sort and return top recommendations
            return {
                npcs: npcRecommendations
                    .sort((a, b) => b.score - a.score)
                    .slice(0, numRecommendations),
                roleplayingTips: this.generateRoleplayingTips(role),
                integrationIdeas: this.generateIntegrationIdeas(purpose, relationship)
            };

        } catch (error) {
            winston.error('Error generating NPC recommendations:', error);
            return { npcs: [], roleplayingTips: [], integrationIdeas: [] };
        }
    }

    // Get NPC templates by role
    getNPCTemplatesByRole(role) {
        const roleMap = {
            ally: 'allies',
            enemy: 'villains',
            neutral: 'neutrals',
            contact: 'neutrals',
            mentor: 'allies',
            villain: 'villains',
            informant: 'neutrals',
            merchant: 'neutrals',
            guard: 'neutrals',
            wildcard: 'wildcards'
        };

        const category = roleMap[role.toLowerCase()] || 'neutrals';
        return Object.values(this.npcTemplates[category] || {});
    }

    // Generate NPC from template
    generateNPCFromTemplate(template, npcRequest) {
        const { setting, purpose, relationship } = npcRequest;

        const npc = {
            name: this.generateNPCName(template, setting),
            role: template.role,
            personality: this.shuffleArray(template.personality).slice(0, 3),
            appearance: this.shuffleArray(template.appearance).slice(0, 2),
            motivations: this.shuffleArray(template.motivations).slice(0, 2),
            complications: this.shuffleArray(template.complications).slice(0, 1),
            storyFunction: template.storyFunction,
            setting: setting,
            purpose: purpose,
            relationship: relationship,
            quirks: this.generateNPCQuirks(template),
            secrets: this.generateNPCSecrets(template),
            dialogueStyle: this.generateDialogueStyle(template)
        };

        return npc;
    }

    // Generate NPC name
    generateNPCName(template, setting) {
        const namePrefixes = ['Old', 'Young', 'Master', 'Lady', 'Captain', 'Brother', 'Sister'];
        const names = ['Alistair', 'Brianna', 'Corvus', 'Delilah', 'Emeric', 'Fiona', 'Gideon', 'Helena'];
        const titles = ['the Wise', 'the Bold', 'the Mysterious', 'the Swift', 'the Cunning'];

        const prefix = this.shuffleArray(namePrefixes)[0];
        const name = this.shuffleArray(names)[0];
        const title = this.shuffleArray(titles)[0];

        return `${prefix} ${name} ${title}`;
    }

    // Generate NPC quirks
    generateNPCQuirks(template) {
        const quirks = [
            'always speaks in riddles',
            'collects unusual objects',
            'has distinctive laugh',
            'never makes eye contact',
            'always tells time',
            'hates a specific color',
            'talks to themselves',
            'has specific greeting ritual'
        ];

        return this.shuffleArray(quirks).slice(0, 2);
    }

    // Generate NPC secrets
    generateNPCSecrets(template) {
        const secrets = [
            'hidden noble lineage',
            'secret criminal past',
            'forbidden romance',
            'magical ability',
            'family tragedy',
            'hidden wealth',
            'secret identity',
            'dangerous knowledge'
        ];

        return this.shuffleArray(secrets).slice(0, 1);
    }

    // Generate dialogue style
    generateDialogueStyle(template) {
        const styles = {
            wise: 'speaks in metaphors and proverbs',
            aggressive: 'direct and confrontational',
            charming: 'flattering and persuasive',
            professional: 'formal and precise',
            eccentric: 'unpredictable and colorful'
        };

        const personality = template.personality[0] || 'professional';
        return styles[personality] || styles.professional;
    }

    // Calculate NPC score
    calculateNPCScore(npc, npcRequest) {
        let score = 5; // Base score

        const { role, setting, purpose, relationship } = npcRequest;

        // Role alignment
        if (npc.role.toLowerCase().includes(role.toLowerCase())) {
            score += 3;
        }

        // Purpose alignment
        if (npc.storyFunction === purpose) {
            score += 2;
        }

        // Relationship consideration
        if (relationship && npc.motivations.includes(relationship)) {
            score += 2;
        }

        return score;
    }

    // Generate roleplaying tips
    generateRoleplayingTips(role) {
        const tips = {
            ally: [
                'Show genuine care for party members',
                'Have personal goals that align with party',
                'Show vulnerability to build connection',
                'Celebrate party successes'
            ],
            enemy: [
                'Make motivations understandable',
                'Show competence without being overpowered',
                'Have moments of humanity',
                'Create memorable presence and tactics'
            ],
            neutral: [
                'Have clear self-interest',
                'Be consistent in behavior',
                'Show indifference to party conflicts',
                'Have useful information or services'
            ],
            wildcard: [
                'Keep motivations mysterious',
                'Act unpredictably but consistently',
                'Create moral ambiguity',
                'Challenge player assumptions'
            ]
        };

        return tips[role] || tips.neutral;
    }

    // Generate integration ideas
    generateIntegrationIdeas(purpose, relationship) {
        const ideas = [
            {
                idea: 'pre-existing_connection',
                description: 'NPC already knows party member from past',
                implementation: 'shared_history, mutual_acquaintance, childhood_friend'
            },
            {
                idea: 'situational_introduction',
                description: 'NPC encountered during specific circumstances',
                implementation: 'crisis_situation, mutual_danger, opportunity_arises'
            },
            {
                idea: 'third_party_introduction',
                description: 'NPC introduced through another character',
                implementation: 'recommendation, formal_introduction, chance_meeting'
            }
        ];

        return ideas;
    }

    // Generate treasure distribution recommendations
    async generateTreasureRecommendations(userId, encounterInfo, partyInfo, numRecommendations = 3) {
        try {
            const { challenge, type, environment } = encounterInfo;
            const { level, size, alignment } = partyInfo;

            const treasureRecommendations = [];

            // Generate different distribution approaches
            const approaches = ['balanced', 'story_integrated', 'player_tailored'];

            approaches.forEach(approach => {
                const distribution = this.generateTreasureDistribution(
                    approach, challenge, type, partyInfo, environment
                );
                treasureRecommendations.push(distribution);
            });

            return {
                distributions: treasureRecommendations,
                balancingNotes: this.generateTreasureBalancingNotes(partyInfo),
                presentationIdeas: this.generateTreasurePresentationIdeas(environment),
                economicImpact: this.analyzeEconomicImpact(treasureRecommendations, partyInfo)
            };

        } catch (error) {
            winston.error('Error generating treasure recommendations:', error);
            return { distributions: [], balancingNotes: [], presentationIdeas: [], economicImpact: {} };
        }
    }

    // Generate treasure distribution
    generateTreasureDistribution(approach, challenge, type, partyInfo, environment) {
        const { level, size, alignment } = partyInfo;
        const distribution = {
            name: `${approach.replace('_', ' ')} treasure distribution`,
            approach: approach,
            totalValue: 0,
            breakdown: {},
            items: [],
            reasoning: ''
        };

        // Calculate base value
        const baseValue = this.calculateBaseTreasureValue(challenge, level, size);
        distribution.totalValue = baseValue;

        // Generate breakdown based on approach
        if (approach === 'balanced') {
            distribution.breakdown = {
                coins: baseValue * 0.6,
                gems: baseValue * 0.2,
                magicItems: baseValue * 0.15,
                consumables: baseValue * 0.05
            };
            distribution.reasoning = 'Standard D&D treasure distribution across all categories';
        } else if (approach === 'story_integrated') {
            distribution.breakdown = {
                coins: baseValue * 0.4,
                storyItems: baseValue * 0.3,
                magicItems: baseValue * 0.2,
                consumables: baseValue * 0.1
            };
            distribution.reasoning = 'Emphasis on items that advance the story and world-building';
        } else if (approach === 'player_tailored') {
            distribution.breakdown = {
                coins: baseValue * 0.3,
                tailoredItems: baseValue * 0.4,
                utilityItems: baseValue * 0.2,
                consumables: baseValue * 0.1
            };
            distribution.reasoning = 'Focus on items specifically useful to party composition';
        }

        // Generate specific items
        distribution.items = this.generateSpecificItems(distribution, partyInfo, environment);

        return distribution;
    }

    // Calculate base treasure value
    calculateBaseTreasureValue(challenge, level, size) {
        // Based on DMG treasure tables and adjusted for party size
        const baseValues = {
            trivial: 50,
            easy: 100,
            medium: 200,
            hard: 400,
            deadly: 800,
            legendary: 1600
        };

        const baseValue = baseValues[challenge] || baseValues.medium;
        const levelMultiplier = 1 + (level * 0.2);
        const sizeMultiplier = size / 4;

        return Math.round(baseValue * levelMultiplier * sizeMultiplier);
    }

    // Generate specific items
    generateSpecificItems(distribution, partyInfo, environment) {
        const items = [];
        const { approach, breakdown } = distribution;
        const { level, composition } = partyInfo;

        // Add coins
        if (breakdown.coins > 0) {
            items.push({
                type: 'coins',
                description: `${Math.round(breakdown.coins)} gp in various denominations`,
                value: breakdown.coins
            });
        }

        // Add gems if applicable
        if (breakdown.gems > 0) {
            items.push({
                type: 'gems',
                description: `${Math.round(breakdown.gems / 100)} assorted gemstones`,
                value: breakdown.gems
            });
        }

        // Add magic items based on approach
        if (approach === 'player_tailored' && composition) {
            const tailoredItems = this.generateTailoredMagicItems(composition, level);
            items.push(...tailoredItems);
        } else if (breakdown.magicItems > 0) {
            const standardItems = this.generateStandardMagicItems(level, environment);
            items.push(...standardItems);
        }

        // Add consumables
        if (breakdown.consumables > 0) {
            const consumables = this.generateConsumables(level);
            items.push(...consumables);
        }

        return items;
    }

    // Generate tailored magic items
    generateTailoredMagicItems(composition, level) {
        const items = [];
        const itemSlots = Math.min(3, Math.ceil(level / 4));

        composition.forEach(character => {
            const classItems = this.getClassSpecificItems(character.class, level);
            const selectedItem = this.shuffleArray(classItems)[0];

            if (selectedItem && items.length < itemSlots) {
                items.push({
                    type: 'magic_item',
                    name: selectedItem.name,
                    description: selectedItem.description,
                    class: character.class,
                    value: selectedItem.value
                });
            }
        });

        return items;
    }

    // Get class specific items
    getClassSpecificItems(characterClass, level) {
        const classItems = {
            fighter: [
                { name: '+1 longsword', description: 'Finely crafted blade', value: 1000 },
                { name: 'Shield of expression', description: 'Emotional shield', value: 1500 }
            ],
            wizard: [
                { name: 'Wand of magic missiles', description: 'Arcane focus', value: 800 },
                { name: 'Robe of useful items', description: 'Utility robe', value: 1200 }
            ],
            rogue: [
                { name: 'Boots of elvenkind', description: 'Silent movement', value: 900 },
                { name: 'Cloak of protection', description: 'Defensive cloak', value: 1600 }
            ],
            cleric: [
                { name: 'Mace of disruption', description: 'Undead bane', value: 1100 },
                { name: 'Amulet of devotion', description: 'Holy symbol', value: 1300 }
            ]
        };

        return classItems[characterClass.toLowerCase()] || classItems.fighter;
    }

    // Generate standard magic items
    generateStandardMagicItems(level, environment) {
        const commonItems = [
            { name: 'Potion of healing', description: 'Restores health', value: 50 },
            { name: 'Scroll of protection', description: 'Magical defense', value: 100 }
        ];

        const uncommonItems = [
            { name: '+1 weapon', description: 'Enhanced combat', value: 1000 },
            { name: 'Cloak of protection', description: 'Defensive boost', value: 1600 }
        ];

        const items = level < 5 ? commonItems : [...commonItems, ...uncommonItems];
        return items.map(item => ({
            type: 'magic_item',
            ...item
        }));
    }

    // Generate consumables
    generateConsumables(level) {
        const consumables = [
            {
                type: 'consumable',
                name: 'Potion of healing',
                description: 'Standard healing potion',
                quantity: Math.min(level, 4),
                value: 50
            },
            {
                type: 'consumable',
                name: 'Scroll of minor utility',
                description: 'Useful utility spell',
                quantity: Math.ceil(level / 3),
                value: 75
            }
        ];

        return consumables;
    }

    // Generate treasure balancing notes
    generateTreasureBalancingNotes(partyInfo) {
        const { level, size, composition } = partyInfo;
        const notes = [];

        if (level > 10) {
            notes.push('Consider using more story-based rewards over pure wealth');
        }

        if (size > 5) {
            notes.push('Ensure equitable distribution of unique items');
        }

        if (composition && composition.some(c => c.class.toLowerCase() === 'monk')) {
            notes.push('Include items useful for unarmed combat');
        }

        notes.push('Watch party wealth accumulation and adjust accordingly');
        notes.push('Consider the economic impact on your campaign world');

        return notes;
    }

    // Generate treasure presentation ideas
    generateTreasurePresentationIdeas(environment) {
        const ideas = [
            {
                idea: 'hidden_compartment',
                description: 'Treasure concealed in furniture or architecture',
                difficulty: 'requires_search'
            },
            {
                idea: 'rewarded_service',
                description: 'Given as payment for completed quest',
                difficulty: 'social'
            },
            {
                idea: 'environmental_challenge',
                description: 'Located in dangerous or hard-to-reach area',
                difficulty: 'exploration'
            },
            {
                idea: 'puzzle_solution',
                description: 'Reward for solving environmental puzzle',
                difficulty: 'intellectual'
            }
        ];

        return ideas;
    }

    // Analyze economic impact
    analyzeEconomicImpact(distributions, partyInfo) {
        const totalValue = distributions.reduce((sum, dist) => sum + dist.totalValue, 0);
        const memberShare = Math.round(totalValue / partyInfo.size);

        return {
            totalPartyValue: totalValue,
            valuePerMember: memberShare,
            economicTier: this.getEconomicTier(memberShare),
            recommendations: [
                'Monitor party wealth progression',
                'Consider magic item limitations',
                'Balance wealth with story rewards'
            ]
        };
    }

    // Get economic tier
    getEconomicTier(valuePerMember) {
        if (valuePerMember < 500) return 'poor';
        if (valuePerMember < 2000) return 'modest';
        if (valuePerMember < 10000) return 'comfortable';
        if (valuePerMember < 50000) return 'wealthy';
        return 'rich';
    }

    // Utility methods
    shuffleArray(array) {
        const shuffled = [...array];
        for (let i = shuffled.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
        }
        return shuffled;
    }
}

module.exports = DMRecommendationService;