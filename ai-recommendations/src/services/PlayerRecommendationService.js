const winston = require('winston');

class PlayerRecommendationService {
    constructor(hybridRecommender, contentService) {
        this.hybridRecommender = hybridRecommender;
        this.contentService = contentService;
        this.classBuilds = this.initializeClassBuilds();
        this.equipmentOptimizations = this.initializeEquipmentOptimizations();
        this.spellSynergies = this.initializeSpellSynergies();
    }

    // Initialize class build templates
    initializeClassBuilds() {
        return {
            fighter: {
                tank: {
                    name: 'Immortal Tank',
                    description: 'Maximize survivability and crowd control',
                    stats: { strength: 15, constitution: 15, dexterity: 14 },
                    feats: ['Heavy Armor Master', 'Sentinel', 'Tough', 'Resilient (Constitution)'],
                    equipment: ['tower shield', 'plate armor', '+2 longsword', 'belt of giant strength'],
                    playstyle: 'defensive',
                    tags: ['tank', 'defense', 'crowd_control']
                },
                damage: {
                    name: 'Blade Master',
                    description: 'Maximize melee damage output',
                    stats: { strength: 16, dexterity: 14, constitution: 14 },
                    feats: ['Great Weapon Master', 'Polearm Master', 'Savage Attacker'],
                    equipment: ['greatsword +2', 'gauntlets of ogre power', 'boots of speed'],
                    playstyle: 'offensive',
                    tags: ['damage', 'melee', 'critical']
                },
                ranged: {
                    name: 'Arery Specialist',
                    description: 'Master of ranged combat',
                    stats: { dexterity: 16, constitution: 14, wisdom: 14 },
                    feats: ['Sharpshooter', 'Crossbow Expert', 'Elven Accuracy'],
                    equipment: ['longbow +2', 'bracers of archery', 'cloak of protection'],
                    playstyle: 'ranged',
                    tags: ['ranged', 'precision', 'mobility']
                }
            },
            wizard: {
                control: {
                    name: ' battlefield Controller',
                    description: 'Control the battlefield with spells',
                    stats: { intelligence: 16, constitution: 14, dexterity: 14 },
                    feats: ['War Caster', 'Resilient (Constitution)', 'Spell Sniper'],
                    equipment: ['staff of power', 'amulet of the devout', 'robe of the archmagi'],
                    playstyle: 'control',
                    tags: ['control', 'debuff', 'area_effect']
                },
                damage: {
                    name: 'Arcane Destroyer',
                    description: 'Maximum spell damage output',
                    stats: { intelligence: 16, constitution: 14, dexterity: 14 },
                    feats: ['Elemental Adept (Fire)', 'Metamagic Adept', 'Fey Touched'],
                    equipment: ['wand of fireballs', 'ioun stone of intellect', 'circlet of blasting'],
                    playstyle: 'damage',
                    tags: ['damage', 'evocation', 'metamagic']
                },
                utility: {
                    name: 'Master of Magic',
                    description: 'Versatile spellcaster with utility focus',
                    stats: { intelligence: 16, wisdom: 14, charisma: 14 },
                    feats: ['Skill Expert', 'Keen Mind', 'Telekinetic'],
                    equipment: ['staff of the magi', 'headband of intellect', 'ring of spell storing'],
                    playstyle: 'utility',
                    tags: ['utility', 'versatility', 'support']
                }
            },
            rogue: {
                assassin: {
                    name: 'Shadow Assassin',
                    description: 'Master of stealth and surprise attacks',
                    stats: { dexterity: 16, intelligence: 14, charisma: 14 },
                    feats: ['Alert', 'Actor', 'Skulker'],
                    equipment: ['rapier +2', 'cloak of elvenkind', 'boots of elvenkind'],
                    playstyle: 'stealth',
                    tags: ['stealth', 'surprise', 'critical']
                },
                trickster: {
                    name: 'Arcane Trickster',
                    description: 'Blend of stealth and magic',
                    stats: { dexterity: 16, intelligence: 15, charisma: 13 },
                    feats: ['War Caster', 'Fey Touched', 'Metamagic Adept'],
                    equipment: ['dagger of venom', 'cloak of protection', 'gloves of thievery'],
                    playstyle: 'utility',
                    tags: ['magic', 'stealth', 'deception']
                },
                scout: {
                    name: 'Master Scout',
                    description: 'Expert in exploration and reconnaissance',
                    stats: { dexterity: 16, wisdom: 15, constitution: 13 },
                    feats: ['Observant', 'Sharpshooter', 'Mobile'],
                    equipment: ['shortbow +2', 'cloak of protection', 'medallion of thoughts'],
                    playstyle: 'exploration',
                    tags: ['exploration', 'perception', 'mobility']
                }
            }
            // Additional classes can be added here
        };
    }

    // Initialize equipment optimization data
    initializeEquipmentOptimizations() {
        return {
            weaponTypes: {
                martial: {
                    twoHanded: ['greatsword', 'maul', 'greataxe', 'halberd', 'glaive'],
                    oneHanded: ['longsword', 'battleaxe', 'warhammer', 'scimitar'],
                    ranged: ['longbow', 'heavy crossbow', 'hand crossbow'],
                    finesse: ['rapier', 'shortsword', 'whip']
                },
                simple: {
                    twoHanded: ['quarterstaff', 'spear', 'mace'],
                    oneHanded: ['dagger', 'club', 'light hammer'],
                    ranged: ['shortbow', 'light crossbow', 'sling']
                }
            },
            armorTypes: {
                heavy: ['plate', 'splint', 'chain mail', 'scale mail', 'ring mail'],
                medium: ['breastplate', 'half plate', 'hide', 'chain shirt'],
                light: ['leather', 'studded leather', 'padded']
            },
            magicalBonuses: {
                common: '+1',
                uncommon: '+2',
                rare: '+3',
                veryRare: '+3 with special ability',
                legendary: '+3 with multiple abilities'
            },
            synergies: {
                'great weapon master': ['maul', 'greatsword', 'greataxe'],
                'polearm master': ['halberd', 'glaive', 'quarterstaff'],
                'sharpshooter': ['longbow', 'heavy crossbow'],
                'dual wielder': ['scimitar', 'shortsword', 'rapier'],
                'heavy armor master': ['plate', 'splint', 'chain mail']
            }
        };
    }

    // Initialize spell synergy data
    initializeSpellSynergies() {
        return {
            combinations: [
                {
                    spells: ['haste', 'blur'],
                    synergy: 'Enhanced mobility and defense',
                    classes: ['wizard', 'sorcerer', 'bard']
                },
                {
                    spells: ['fireball', 'scorching ray'],
                    synergy: 'Maximum fire damage output',
                    classes: ['wizard', 'sorcerer']
                },
                {
                    spells: ['counterspell', 'dispel magic'],
                    synergy: 'Complete magical defense',
                    classes: ['wizard', 'sorcerer', 'bard', 'cleric']
                },
                {
                    spells: ['bless', 'spiritual weapon'],
                    synergy: 'Support and offense combination',
                    classes: ['cleric', 'paladin']
                },
                {
                    spells: ['mage armor', 'shield'],
                    synergy: 'Maximum magical defense',
                    classes: ['wizard', 'sorcerer']
                },
                {
                    spells: [' hunters mark', 'colossal slayer'],
                    synergy: 'Ranged damage maximization',
                    classes: ['ranger', 'fighter']
                },
                {
                    spells: ['suggestion', 'charm person'],
                    synergy: 'Social manipulation',
                    classes: ['bard', 'sorcerer', 'warlock']
                },
                {
                    spells: ['web', 'fireball'],
                    synergy: 'Area control and damage',
                    classes: ['wizard', 'sorcerer']
                }
            ],
            schoolSynergies: {
                evocation: ['fireball', 'lightning bolt', 'cone of cold'],
                illusion: ['major image', 'invisibility', 'mirror image'],
                enchantment: ['charm person', 'hold person', 'suggestion'],
                necromancy: ['inflict wounds', 'ray of enfeeblement', 'animate dead'],
                abjuration: ['shield', 'mage armor', 'dispel magic'],
                conjuration: ['misty step', 'summon lesser demons', 'teleport'],
                divination: ['detect magic', 'identify', 'clairvoyance'],
                transmutation: ['polymorph', 'fly', 'haste']
            }
        };
    }

    // Generate character build recommendations
    async generateCharacterBuildRecommendations(userId, characterInfo, numRecommendations = 5) {
        try {
            const { class: characterClass, level, playstyle, stats } = characterInfo;

            // Get base recommendations from hybrid system
            const baseRecommendations = await this.hybridRecommender.generateRecommendations(userId, {
                numRecommendations: numRecommendations * 2,
                filters: {
                    category: 'character',
                    type: 'build',
                    class: characterClass
                }
            });

            // Generate build-specific recommendations
            const buildRecommendations = this.generateBuildSpecificRecommendations(
                characterClass, level, playstyle, stats
            );

            // Combine and rank recommendations
            const combinedRecommendations = this.combineCharacterRecommendations(
                baseRecommendations, buildRecommendations, characterInfo
            );

            // Generate detailed build suggestions
            const detailedBuilds = combinedRecommendations.slice(0, numRecommendations)
                .map(rec => this.generateDetailedBuild(rec, characterInfo));

            return {
                builds: detailedBuilds,
                reasoning: this.generateBuildReasoning(characterInfo),
                alternatives: this.generateBuildAlternatives(characterInfo, numRecommendations)
            };

        } catch (error) {
            winston.error('Error generating character build recommendations:', error);
            return { builds: [], reasoning: '', alternatives: [] };
        }
    }

    // Generate build-specific recommendations
    generateBuildSpecificRecommendations(characterClass, level, playstyle, stats) {
        const recommendations = [];
        const classBuilds = this.classBuilds[characterClass.toLowerCase()];

        if (!classBuilds) return recommendations;

        Object.entries(classBuilds).forEach(([buildType, build]) => {
            // Calculate compatibility score
            let score = 0;

            // Playstyle matching
            if (build.playstyle === playstyle) {
                score += 0.4;
            }

            // Stat compatibility
            score += this.calculateStatCompatibility(build.stats, stats);

            // Level appropriateness
            score += this.calculateLevelAppropriateness(build, level);

            recommendations.push({
                contentId: `build_${characterClass}_${buildType}`,
                score: score,
                build: build,
                type: 'character_build',
                method: 'template_matching'
            });
        });

        return recommendations.sort((a, b) => b.score - a.score);
    }

    // Calculate stat compatibility
    calculateStatCompatibility(buildStats, userStats) {
        if (!userStats) return 0.5;

        let compatibility = 0;
        const statNames = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'];

        statNames.forEach(stat => {
            const buildValue = buildStats[stat] || 0;
            const userValue = userStats[stat] || 0;
            const difference = Math.abs(buildValue - userValue);
            compatibility += Math.max(0, 1 - difference / 10);
        });

        return compatibility / statNames.length;
    }

    // Calculate level appropriateness
    calculateLevelAppropriateness(build, level) {
        // Build is more appropriate for certain level ranges
        const levelScores = {
            1: 0.8, 2: 0.8, 3: 0.8, 4: 0.9, 5: 0.9,
            6: 0.9, 7: 0.9, 8: 1.0, 9: 1.0, 10: 1.0,
            11: 0.9, 12: 0.9, 13: 0.9, 14: 0.8, 15: 0.8,
            16: 0.8, 17: 0.7, 18: 0.7, 19: 0.7, 20: 0.6
        };

        return levelScores[level] || 0.5;
    }

    // Combine character recommendations
    combineCharacterRecommendations(baseRecommendations, buildRecommendations, characterInfo) {
        const combined = new Map();

        // Add base recommendations
        baseRecommendations.forEach(rec => {
            combined.set(rec.contentId, {
                ...rec,
                sources: ['hybrid']
            });
        });

        // Add build recommendations
        buildRecommendations.forEach(rec => {
            if (combined.has(rec.contentId)) {
                const existing = combined.get(rec.contentId);
                existing.score = (existing.score + rec.score) / 2;
                existing.sources.push('template');
            } else {
                combined.set(rec.contentId, {
                    ...rec,
                    sources: ['template']
                });
            }
        });

        return Array.from(combined.values())
            .sort((a, b) => b.score - a.score);
    }

    // Generate detailed build information
    generateDetailedBuild(recommendation, characterInfo) {
        const build = recommendation.build;
        const { class: characterClass, level } = characterInfo;

        return {
            name: build.name,
            description: build.description,
            playstyle: build.playstyle,
            tags: build.tags,
            stats: this.adjustStatsForLevel(build.stats, level),
            feats: this.adjustFeatsForLevel(build.feats, level),
            equipment: this.adjustEquipmentForLevel(build.equipment, level),
            progression: this.generateProgressionPlan(build, level),
            strengths: this.identifyBuildStrengths(build),
            weaknesses: this.identifyBuildWeaknesses(build),
            recommendedSpells: this.getRecommendedSpells(characterClass, build.playstyle, level),
            equipmentPath: this.generateEquipmentPath(build, level),
            score: recommendation.score,
            sources: recommendation.sources
        };
    }

    // Adjust stats for level
    adjustStatsForLevel(baseStats, level) {
        const adjustedStats = { ...baseStats };

        // Add level-based increases
        const asiLevels = [4, 8, 12, 16, 19];
        const asiCount = asiLevels.filter(lvl => lvl <= level).length;

        // Prioritize main stats for increases
        const sortedStats = Object.entries(adjustedStats)
            .sort((a, b) => b[1] - a[1]);

        for (let i = 0; i < asiCount && i < sortedStats.length; i++) {
            const [stat, value] = sortedStats[i];
            if (value < 20) {
                adjustedStats[stat] = Math.min(20, value + 2);
            }
        }

        return adjustedStats;
    }

    // Adjust feats for level
    adjustFeatsForLevel(baseFeats, level) {
        const featLevels = [4, 8, 12, 16, 19];
        const availableFeats = featLevels.filter(lvl => lvl <= level).length;
        return baseFeats.slice(0, availableFeats);
    }

    // Adjust equipment for level
    adjustEquipmentForLevel(baseEquipment, level) {
        // Filter equipment based on level appropriateness
        return baseEquipment.filter(item => {
            if (item.includes('+1') && level < 5) return false;
            if (item.includes('+2') && level < 11) return false;
            if (item.includes('+3') && level < 17) return false;
            return true;
        });
    }

    // Generate progression plan
    generateProgressionPlan(build, currentLevel) {
        const progression = [];
        const maxLevel = 20;

        for (let level = currentLevel + 1; level <= maxLevel; level++) {
            const milestone = this.getLevelMilestone(level, build);
            if (milestone) {
                progression.push({
                    level,
                    milestone: milestone.description,
                    priority: milestone.priority,
                    choices: milestone.choices
                });
            }
        }

        return progression;
    }

    // Get level milestone
    getLevelMilestone(level, build) {
        const milestones = {
            4: {
                description: 'Ability Score Improvement or Feat',
                priority: 'high',
                choices: ['Increase main stat', 'Take recommended feat']
            },
            8: {
                description: 'Ability Score Improvement or Feat',
                priority: 'high',
                choices: ['Increase main stat', 'Take recommended feat']
            },
            12: {
                description: 'Ability Score Improvement or Feat',
                priority: 'medium',
                choices: ['Increase secondary stat', 'Take specialized feat']
            },
            16: {
                description: 'Ability Score Improvement or Feat',
                priority: 'medium',
                choices: ['Increase tertiary stat', 'Take advanced feat']
            },
            19: {
                description: 'Final Ability Score Improvement',
                priority: 'low',
                choices: ['Max out main stat', 'Fill weakness']
            }
        };

        return milestones[level] || null;
    }

    // Identify build strengths
    identifyBuildStrengths(build) {
        const strengths = [];

        if (build.playstyle === 'tank') {
            strengths.push('High durability', 'Crowd control', 'Party protection');
        } else if (build.playstyle === 'damage') {
            strengths.push('High damage output', 'Quick combat resolution', 'Threat generation');
        } else if (build.playstyle === 'control') {
            strengths.push('Battlefield control', 'Debuffing enemies', 'Tactical advantage');
        } else if (build.playstyle === 'support') {
            strengths.push('Party enhancement', 'Healing capabilities', 'Utility spells');
        }

        return strengths;
    }

    // Identify build weaknesses
    identifyBuildWeaknesses(build) {
        const weaknesses = [];

        if (build.playstyle === 'tank') {
            weaknesses.push('Lower damage output', 'Limited mobility', 'Resource dependent');
        } else if (build.playstyle === 'damage') {
            weaknesses.push('Lower defenses', 'Limited utility', 'Vulnerable to control');
        } else if (build.playstyle === 'control') {
            weaknesses.push('Limited direct damage', 'Concentration dependent', 'Resource intensive');
        } else if (build.playstyle === 'support') {
            weaknesses.push('Limited solo capability', 'Dependent on party', 'Low damage output');
        }

        return weaknesses;
    }

    // Get recommended spells
    getRecommendedSpells(characterClass, playstyle, level) {
        const spellProgression = this.getSpellProgression(characterClass, level);
        const recommendedSpells = [];

        // Add spells based on playstyle and level
        if (playstyle === 'damage') {
            recommendedSpells.push(
                ...this.getDamageSpells(characterClass, spellProgression)
            );
        } else if (playstyle === 'control') {
            recommendedSpells.push(
                ...this.getControlSpells(characterClass, spellProgression)
            );
        } else if (playstyle === 'support') {
            recommendedSpells.push(
                ...this.getSupportSpells(characterClass, spellProgression)
            );
        }

        return recommendedSpells;
    }

    // Get spell progression
    getSpellProgression(characterClass, level) {
        const progressions = {
            wizard: {
                1: { cantrips: 3, level1: 2 },
                2: { cantrips: 3, level1: 3 },
                3: { cantrips: 3, level1: 4, level2: 2 },
                4: { cantrips: 4, level1: 4, level2: 3 },
                5: { cantrips: 4, level1: 4, level2: 3, level3: 2 },
                // ... continue for all levels
                20: { cantrips: 4, level1: 4, level2: 3, level3: 3, level4: 3, level5: 3, level6: 2, level7: 2, level8: 1, level9: 1 }
            },
            sorcerer: {
                // Sorcerer progression
            },
            cleric: {
                // Cleric progression
            }
            // Other classes...
        };

        return progressions[characterClass]?.[level] || {};
    }

    // Get damage spells
    getDamageSpells(characterClass, progression) {
        const damageSpells = {
            wizard: ['fireball', 'lightning bolt', 'cone of cold', 'chain lightning', 'meteor swarm'],
            sorcerer: ['fireball', 'lightning bolt', 'cone of cold', 'chain lightning', 'meteor swarm'],
            warlock: ['eldritch blast', 'fireball', 'hunger of hadar', 'finger of death'],
            cleric: ['spiritual weapon', 'flame strike', 'harm', 'divine word']
        };

        return damageSpells[characterClass] || [];
    }

    // Get control spells
    getControlSpells(characterClass, progression) {
        const controlSpells = {
            wizard: ['hold person', 'web', 'hypnotic pattern', 'banishment', 'maze'],
            sorcerer: ['hold person', 'web', 'hypnotic pattern', 'banishment'],
            bard: ['hold person', 'hypnotic pattern', 'suggestion', 'dominate person'],
            druid: ['hold person', 'spike growth', 'sleet storm', 'dominate beast']
        };

        return controlSpells[characterClass] || [];
    }

    // Get support spells
    getSupportSpells(characterClass, progression) {
        const supportSpells = {
            cleric: ['healing word', 'cure wounds', 'bless', 'aid', 'heal'],
            bard: ['healing word', 'inspire courage', 'heroism', 'greater restoration'],
            druid: ['healing word', 'cure wounds', 'goodberry', 'heal'],
            paladin: ['cure wounds', 'lay on hands', 'lesser restoration', 'greater restoration']
        };

        return supportSpells[characterClass] || [];
    }

    // Generate equipment path
    generateEquipmentPath(build, currentLevel) {
        const equipmentPath = [];
        const equipmentLevels = [5, 11, 17];

        equipmentLevels.forEach(level => {
            if (level > currentLevel) {
                const upgrades = this.getEquipmentUpgrades(build, level);
                equipmentPath.push({
                    level,
                    upgrades,
                    priority: this.getUpgradePriority(upgrades)
                });
            }
        });

        return equipmentPath;
    }

    // Get equipment upgrades
    getEquipmentUpgrades(build, targetLevel) {
        const upgrades = [];

        // Weapon upgrades
        if (targetLevel >= 5) {
            upgrades.push({ type: 'weapon', suggestion: '+1 magic weapon' });
        }
        if (targetLevel >= 11) {
            upgrades.push({ type: 'weapon', suggestion: '+2 magic weapon' });
        }
        if (targetLevel >= 17) {
            upgrades.push({ type: 'weapon', suggestion: '+3 magic weapon or legendary weapon' });
        }

        // Armor upgrades
        if (targetLevel >= 11) {
            upgrades.push({ type: 'armor', suggestion: '+1 magic armor' });
        }
        if (targetLevel >= 17) {
            upgrades.push({ type: 'armor', suggestion: '+2 magic armor or legendary armor' });
        }

        // Accessory upgrades
        if (targetLevel >= 5) {
            upgrades.push({ type: 'accessory', suggestion: 'cloak of protection' });
        }
        if (targetLevel >= 11) {
            upgrades.push({ type: 'accessory', suggestion: 'amulet of resistance' });
        }

        return upgrades;
    }

    // Get upgrade priority
    getUpgradePriority(upgrades) {
        const priorities = {
            weapon: 'high',
            armor: 'high',
            accessory: 'medium'
        };

        return upgrades.map(upgrade => ({
            ...upgrade,
            priority: priorities[upgrade.type] || 'low'
        }));
    }

    // Generate build reasoning
    generateBuildReasoning(characterInfo) {
        const { class: characterClass, level, playstyle, stats } = characterInfo;

        let reasoning = `Based on your ${characterClass} at level ${level}`;

        if (playstyle) {
            reasoning += ` with a ${playstyle} playstyle`;
        }

        if (stats) {
            const mainStat = Object.entries(stats)
                .sort((a, b) => b[1] - a[1])[0][0];
            reasoning += ` and your ${mainStat} focus`;
        }

        reasoning += '. These builds optimize your character\'s effectiveness while providing clear progression paths and equipment recommendations.';

        return reasoning;
    }

    // Generate build alternatives
    generateBuildAlternatives(characterInfo, numRecommendations) {
        const alternatives = [];
        const { class: characterClass } = characterInfo;

        // Suggest different playstyles
        const playstyles = ['tank', 'damage', 'control', 'support', 'utility'];
        const currentPlaystyle = characterInfo.playstyle;

        playstyles.forEach(playstyle => {
            if (playstyle !== currentPlaystyle && alternatives.length < numRecommendations) {
                alternatives.push({
                    playstyle,
                    description: `Try a ${playstyle} approach for different gameplay experience`,
                    difficulty: this.getPlaystyleDifficulty(playstyle),
                    learningCurve: this.getLearningCurve(playstyle)
                });
            }
        });

        return alternatives;
    }

    // Get playstyle difficulty
    getPlaystyleDifficulty(playstyle) {
        const difficulties = {
            tank: 'medium',
            damage: 'easy',
            control: 'hard',
            support: 'medium',
            utility: 'medium'
        };

        return difficulties[playstyle] || 'medium';
    }

    // Get learning curve
    getLearningCurve(playstyle) {
        const curves = {
            tank: 'gradual',
            damage: 'gentle',
            control: 'steep',
            support: 'moderate',
            utility: 'moderate'
        };

        return curves[playstyle] || 'moderate';
    }

    // Generate equipment recommendations
    async generateEquipmentRecommendations(userId, characterInfo, currentEquipment, numRecommendations = 10) {
        try {
            const { class: characterClass, level, playstyle } = characterInfo;

            // Get optimization goals based on playstyle
            const optimizationGoals = this.getOptimizationGoals(playstyle);

            // Generate equipment recommendations
            const recommendations = [];

            // Weapon recommendations
            const weaponRecs = this.generateWeaponRecommendations(
                characterClass, level, currentEquipment, optimizationGoals
            );
            recommendations.push(...weaponRecs);

            // Armor recommendations
            const armorRecs = this.generateArmorRecommendations(
                characterClass, level, currentEquipment, optimizationGoals
            );
            recommendations.push(...armorRecs);

            // Accessory recommendations
            const accessoryRecs = this.generateAccessoryRecommendations(
                characterClass, level, currentEquipment, optimizationGoals
            );
            recommendations.push(...accessoryRecs);

            // Sort and return top recommendations
            return recommendations
                .sort((a, b) => b.score - a.score)
                .slice(0, numRecommendations);

        } catch (error) {
            winston.error('Error generating equipment recommendations:', error);
            return [];
        }
    }

    // Get optimization goals
    getOptimizationGoals(playstyle) {
        const goals = {
            tank: ['armor_class', 'hit_points', 'resistance', 'crowd_control'],
            damage: ['attack_bonus', 'damage', 'critical_chance', 'action_economy'],
            control: ['spell_save_dc', 'spell_attacks', 'concentration', 'utility'],
            support: ['healing', 'buff_duration', 'save_bonuses', 'utility'],
            utility: ['skill_bonuses', 'movement', 'versatility', 'problem_solving']
        };

        return goals[playstyle] || ['balance'];
    }

    // Generate weapon recommendations
    generateWeaponRecommendations(characterClass, level, currentEquipment, goals) {
        const recommendations = [];
        const weaponTypes = this.getRecommendedWeaponTypes(characterClass, goals);

        weaponTypes.forEach(weaponType => {
            const upgrades = this.getWeaponUpgrades(weaponType, level, currentEquipment);
            upgrades.forEach(upgrade => {
                const score = this.calculateWeaponScore(upgrade, goals, level);
                recommendations.push({
                    ...upgrade,
                    score,
                    type: 'weapon',
                    reasoning: this.getWeaponReasoning(upgrade, goals)
                });
            });
        });

        return recommendations;
    }

    // Get recommended weapon types
    getRecommendedWeaponTypes(characterClass, goals) {
        const classWeapons = {
            fighter: ['greatsword', 'longsword', 'longbow', 'rapier'],
            rogue: ['rapier', 'shortsword', 'shortbow', 'hand crossbow'],
            wizard: ['dagger', 'staff', 'quarterstaff'],
            cleric: ['mace', 'warhammer', 'quarterstaff'],
            ranger: ['longbow', 'shortbow', 'shortsword', 'two shortswords'],
            paladin: ['longsword', 'greatsword', 'warhammer'],
            barbarian: ['greatsword', 'maul', 'greataxe', 'handaxe'],
            monk: ['quarterstaff', 'shortsword', 'unarmed'],
            bard: ['rapier', 'longsword', 'shortsword'],
            druid: ['scimitar', 'quarterstaff', 'spear'],
            sorcerer: ['dagger', 'staff', 'quarterstaff'],
            warlock: ['dagger', 'quarterstaff', 'light crossbow']
        };

        return classWeapons[characterClass] || ['simple'];
    }

    // Get weapon upgrades
    getWeaponUpgrades(weaponType, level, currentEquipment) {
        const upgrades = [];
        const hasCurrent = currentEquipment.weapon &&
            currentEquipment.weapon.type === weaponType;

        if (!hasCurrent || level >= 5) {
            upgrades.push({
                name: `${weaponType} +1`,
                type: weaponType,
                bonus: 1,
                rarity: 'uncommon',
                cost: this.getWeaponCost(weaponType, 1)
            });
        }

        if (level >= 11) {
            upgrades.push({
                name: `${weaponType} +2`,
                type: weaponType,
                bonus: 2,
                rarity: 'rare',
                cost: this.getWeaponCost(weaponType, 2)
            });
        }

        if (level >= 17) {
            upgrades.push({
                name: `${weaponType} +3`,
                type: weaponType,
                bonus: 3,
                rarity: 'very rare',
                cost: this.getWeaponCost(weaponType, 3)
            });
        }

        return upgrades;
    }

    // Calculate weapon score
    calculateWeaponScore(upgrade, goals, level) {
        let score = upgrade.bonus * 2;

        // Bonus for goal alignment
        if (goals.includes('attack_bonus')) {
            score += upgrade.bonus * 3;
        }
        if (goals.includes('damage')) {
            score += upgrade.bonus * 2;
        }

        // Level appropriateness
        const levelBonus = Math.min(level / 20, 1);
        score += levelBonus * 2;

        return score;
    }

    // Get weapon reasoning
    getWeaponReasoning(upgrade, goals) {
        let reasoning = `This weapon provides a +${upgrade.bonus} bonus`;

        if (goals.includes('attack_bonus')) {
            reasoning += ' to attack rolls';
        }
        if (goals.includes('damage')) {
            reasoning += ' and damage rolls';
        }

        reasoning += `, making it effective for your ${goals.join(' and ')} goals.`;

        return reasoning;
    }

    // Generate armor recommendations
    generateArmorRecommendations(characterClass, level, currentEquipment, goals) {
        const recommendations = [];
        const armorTypes = this.getRecommendedArmorTypes(characterClass, goals);

        armorTypes.forEach(armorType => {
            const upgrades = this.getArmorUpgrades(armorType, level, currentEquipment);
            upgrades.forEach(upgrade => {
                const score = this.calculateArmorScore(upgrade, goals, level);
                recommendations.push({
                    ...upgrade,
                    score,
                    type: 'armor',
                    reasoning: this.getArmorReasoning(upgrade, goals)
                });
            });
        });

        return recommendations;
    }

    // Get recommended armor types
    getRecommendedArmorTypes(characterClass, goals) {
        const classArmor = {
            fighter: ['plate', 'splint', 'chain mail'],
            paladin: ['plate', 'splint', 'chain mail'],
            barbarian: ['hide', 'chain shirt', 'scale mail'],
            ranger: ['hide', 'chain shirt', 'studded leather'],
            rogue: ['studded leather', 'leather', 'hide'],
            monk: ['none', 'leather'],
            wizard: ['none', 'leather', 'studded leather'],
            sorcerer: ['none', 'leather', 'studded leather'],
            warlock: ['leather', 'studded leather', 'hide'],
            bard: ['studded leather', 'leather', 'hide'],
            cleric: ['chain mail', 'scale mail', 'breastplate'],
            druid: ['hide', 'leather', 'studded leather']
        };

        return classArmor[characterClass] || ['light'];
    }

    // Get armor upgrades
    getArmorUpgrades(armorType, level, currentEquipment) {
        const upgrades = [];
        const hasCurrent = currentEquipment.armor &&
            currentEquipment.armor.type === armorType;

        if (!hasCurrent || level >= 5) {
            upgrades.push({
                name: `${armorType} +1`,
                type: armorType,
                bonus: 1,
                rarity: 'rare',
                cost: this.getArmorCost(armorType, 1)
            });
        }

        if (level >= 11) {
            upgrades.push({
                name: `${armorType} +2`,
                type: armorType,
                bonus: 2,
                rarity: 'very rare',
                cost: this.getArmorCost(armorType, 2)
            });
        }

        return upgrades;
    }

    // Calculate armor score
    calculateArmorScore(upgrade, goals, level) {
        let score = upgrade.bonus * 3;

        // Bonus for goal alignment
        if (goals.includes('armor_class')) {
            score += upgrade.bonus * 4;
        }
        if (goals.includes('defense')) {
            score += upgrade.bonus * 2;
        }

        return score;
    }

    // Get armor reasoning
    getArmorReasoning(upgrade, goals) {
        return `This armor provides a +${upgrade.bonus} bonus to AC, significantly improving your survivability and defense capabilities.`;
    }

    // Generate accessory recommendations
    generateAccessoryRecommendations(characterClass, level, currentEquipment, goals) {
        const recommendations = [];
        const accessories = this.getRecommendedAccessories(characterClass, goals);

        accessories.forEach(accessory => {
            if (this.canUseAccessory(accessory, level)) {
                const score = this.calculateAccessoryScore(accessory, goals, level);
                recommendations.push({
                    ...accessory,
                    score,
                    type: 'accessory',
                    reasoning: this.getAccessoryReasoning(accessory, goals)
                });
            }
        });

        return recommendations;
    }

    // Get recommended accessories
    getRecommendedAccessories(characterClass, goals) {
        const commonAccessories = [
            {
                name: 'Cloak of Protection',
                bonus: { ac: 1, saves: 1 },
                rarity: 'uncommon',
                cost: 5000
            },
            {
                name: 'Amulet of Resistance',
                bonus: { saves: 1 },
                rarity: 'rare',
                cost: 8000
            },
            {
                name: 'Ring of Protection',
                bonus: { ac: 1, saves: 1 },
                rarity: 'rare',
                cost: 10000
            },
            {
                name: 'Boots of Speed',
                bonus: { speed: 10 },
                rarity: 'rare',
                cost: 8000
            },
            {
                name: 'Gauntlets of Ogre Power',
                bonus: { strength: 19 },
                rarity: 'uncommon',
                cost: 6000
            }
        ];

        // Class-specific accessories
        const classAccessories = {
            wizard: [
                {
                    name: 'Staff of Power',
                    bonus: { spell_attacks: 2, spell_damage: 2 },
                    rarity: 'very rare',
                    cost: 50000
                },
                {
                    name: 'Amulet of the Devout',
                    bonus: { spell_save_dc: 2 },
                    rarity: 'rare',
                    cost: 15000
                }
            ],
            fighter: [
                {
                    name: 'Belt of Giant Strength',
                    bonus: { strength: 21 },
                    rarity: 'rare',
                    cost: 20000
                },
                {
                    name: 'Boots of Striding and Springing',
                    bonus: { speed: 10, jump: 'double' },
                    rarity: 'uncommon',
                    cost: 4000
                }
            ]
            // Additional classes...
        };

        return [
            ...commonAccessories,
            ...(classAccessories[characterClass] || [])
        ];
    }

    // Check if accessory can be used
    canUseAccessory(accessory, level) {
        const levelRequirements = {
            'uncommon': 1,
            'rare': 5,
            'very rare': 11,
            'legendary': 17
        };

        return level >= (levelRequirements[accessory.rarity] || 1);
    }

    // Calculate accessory score
    calculateAccessoryScore(accessory, goals, level) {
        let score = 0;

        // Calculate score based on bonus types
        Object.entries(accessory.bonus).forEach(([type, value]) => {
            switch (type) {
                case 'ac':
                    if (goals.includes('armor_class')) score += value * 4;
                    else score += value * 2;
                    break;
                case 'saves':
                    if (goals.includes('defense')) score += value * 3;
                    else score += value * 2;
                    break;
                case 'spell_save_dc':
                    if (goals.includes('spell_save_dc')) score += value * 5;
                    else score += value * 2;
                    break;
                case 'spell_damage':
                    if (goals.includes('damage')) score += value * 4;
                    else score += value * 2;
                    break;
                default:
                    score += value;
            }
        });

        // Rarity bonus
        const rarityBonus = {
            'uncommon': 1,
            'rare': 2,
            'very rare': 3,
            'legendary': 4
        };

        score += rarityBonus[accessory.rarity] || 0;

        return score;
    }

    // Get accessory reasoning
    getAccessoryReasoning(accessory, goals) {
        const bonuses = Object.entries(accessory.bonus)
            .map(([type, value]) => {
                if (type === 'ac') return `+${value} AC`;
                if (type === 'saves') return `+${value} to all saves`;
                if (type === 'spell_save_dc') return `+${value} spell save DC`;
                if (type === 'spell_damage') return `+${value} spell damage`;
                if (type === 'speed') return `+${value} speed`;
                if (type === 'strength') return `Strength ${value}`;
                return `+${value} ${type}`;
            })
            .join(', ');

        return `This item provides ${bonuses}, enhancing your character's capabilities for ${goals.join(' and ')} goals.`;
    }

    // Generate spell recommendations
    async generateSpellRecommendations(userId, characterInfo, knownSpells, numRecommendations = 10) {
        try {
            const { class: characterClass, level, playstyle } = characterInfo;

            // Get spell availability for character
            const availableSpells = this.getAvailableSpells(characterClass, level);

            // Filter out already known spells
            const candidateSpells = availableSpells.filter(spell =>
                !knownSpells.includes(spell.name)
            );

            // Score spells based on playstyle and synergy
            const scoredSpells = candidateSpells.map(spell => ({
                ...spell,
                score: this.calculateSpellScore(spell, playstyle, knownSpells),
                reasoning: this.getSpellReasoning(spell, playstyle, knownSpells)
            }));

            // Sort and return top recommendations
            return scoredSpells
                .sort((a, b) => b.score - a.score)
                .slice(0, numRecommendations);

        } catch (error) {
            winston.error('Error generating spell recommendations:', error);
            return [];
        }
    }

    // Get available spells for character
    getAvailableSpells(characterClass, level) {
        // This would typically come from a database of spells
        // For now, return a representative sample
        const allSpells = [
            // Cantrips
            { name: 'fire bolt', level: 0, school: 'evocation', damage: '1d10', casting_time: '1 action' },
            { name: 'mage hand', level: 0, school: 'conjuration', utility: true, casting_time: '1 action' },
            { name: 'light', level: 0, school: 'evocation', utility: true, casting_time: '1 action' },
            { name: 'guidance', level: 0, school: 'divination', utility: true, casting_time: '1 action' },
            { name: 'prestidigitation', level: 0, school: 'transmutation', utility: true, casting_time: '1 action' },

            // Level 1 spells
            { name: 'magic missile', level: 1, school: 'evocation', damage: '3d4+3', casting_time: '1 action' },
            { name: 'shield', level: 1, school: 'abjuration', defense: true, casting_time: '1 reaction' },
            { name: 'mage armor', level: 1, school: 'abjuration', defense: true, casting_time: '1 action' },
            { name: 'detect magic', level: 1, school: 'divination', utility: true, casting_time: '1 action' },
            { name: 'burning hands', level: 1, school: 'evocation', damage: '3d6', casting_time: '1 action' },
            { name: 'charm person', level: 1, school: 'enchantment', control: true, casting_time: '1 action' },
            { name: 'hideous laughter', level: 1, school: 'enchantment', control: true, casting_time: '1 action' },

            // Level 2 spells
            { name: 'fireball', level: 3, school: 'evocation', damage: '8d6', casting_time: '1 action' },
            { name: 'haste', level: 3, school: 'transmutation', buff: true, casting_time: '1 action' },
            { name: 'fly', level: 3, school: 'transmutation', utility: true, casting_time: '1 action' },
            { name: 'counterspell', level: 3, school: 'abjuration', defense: true, casting_time: '1 reaction' },
            { name: 'dispel magic', level: 3, school: 'abjuration', utility: true, casting_time: '1 action' },
            { name: 'lightning bolt', level: 3, school: 'evocation', damage: '8d6', casting_time: '1 action' },
            { name: 'hold person', level: 2, school: 'enchantment', control: true, casting_time: '1 action' },
            { name: 'invisibility', level: 2, school: 'illusion', utility: true, casting_time: '1 action' },
            { name: 'mirror image', level: 2, school: 'illusion', defense: true, casting_time: '1 action' },
            { name: 'misty step', level: 2, school: 'conjuration', utility: true, casting_time: '1 bonus action' },
            { name: 'web', level: 2, school: 'conjuration', control: true, casting_time: '1 action' }
        ];

        // Filter spells by level availability
        const maxSpellLevel = Math.floor((level + 1) / 2);
        return allSpells.filter(spell => spell.level <= maxSpellLevel);
    }

    // Calculate spell score
    calculateSpellScore(spell, playstyle, knownSpells) {
        let score = 0;

        // Base score for spell level
        score += spell.level * 2;

        // Playstyle alignment
        if (playstyle === 'damage' && spell.damage) {
            score += 5;
            // Higher damage dice get better scores
            const damageMatch = spell.damage.match(/(\\d+)d(\\d+)/);
            if (damageMatch) {
                score += parseInt(damageMatch[1]) * parseInt(damageMatch[2]) / 10;
            }
        }

        if (playstyle === 'control' && (spell.control || spell.school === 'enchantment')) {
            score += 5;
        }

        if (playstyle === 'support' && (spell.buff || spell.healing)) {
            score += 5;
        }

        if (playstyle === 'defense' && spell.defense) {
            score += 5;
        }

        if (playstyle === 'utility' && spell.utility) {
            score += 5;
        }

        // Synergy with known spells
        const synergyBonus = this.calculateSpellSynergy(spell, knownSpells);
        score += synergyBonus;

        // Casting time bonus (bonus actions and reactions are valuable)
        if (spell.casting_time.includes('bonus')) {
            score += 2;
        }
        if (spell.casting_time.includes('reaction')) {
            score += 3;
        }

        return score;
    }

    // Calculate spell synergy
    calculateSpellSynergy(spell, knownSpells) {
        let synergy = 0;

        this.spellSynergies.combinations.forEach(combination => {
            if (combination.spells.includes(spell.name)) {
                const knownComboSpells = combination.spells.filter(s => knownSpells.includes(s));
                synergy += knownComboSpells.length * 2;
            }
        });

        return synergy;
    }

    // Get spell reasoning
    getSpellReasoning(spell, playstyle, knownSpells) {
        let reasoning = `${spell.name} is a ${spell.level}-level ${spell.school} spell`;

        if (spell.damage) {
            reasoning += ` that deals ${spell.damage} damage`;
        }

        if (spell.control) {
            reasoning += ' that provides excellent battlefield control';
        }

        if (spell.buff) {
            reasoning += ' that enhances your allies';
        }

        if (spell.defense) {
            reasoning += ' that provides strong defensive options';
        }

        if (spell.utility) {
            reasoning += ' that offers versatile utility';
        }

        // Add synergy information
        const synergies = this.spellSynergies.combinations.filter(combination =>
            combination.spells.includes(spell.name) &&
            combination.spells.some(s => knownSpells.includes(s))
        );

        if (synergies.length > 0) {
            reasoning += ` and synergizes well with your known spells`;
        }

        reasoning += '.';

        return reasoning;
    }

    // Helper methods for costs
    getWeaponCost(weaponType, bonus) {
        const baseCosts = {
            'dagger': 2, 'club': 1, 'quarterstaff': 2, 'light hammer': 2,
            'sickle': 1, 'handaxe': 5, 'javelin': 1, 'light hammer': 2,
            'mace': 5, 'spear': 1, 'shortsword': 10, 'longsword': 15,
            'rapier': 25, 'scimitar': 25, 'warhammer': 15, 'battleaxe': 10,
            'flail': 10, 'maul': 10, 'morningstar': 15, 'glaive': 20,
            'greatsword': 50, 'greataxe': 30, 'halberd': 20, 'lance': 10,
            'shortbow': 25, 'longbow': 50, 'light crossbow': 25, 'heavy crossbow': 50
        };

        const baseCost = baseCosts[weaponType] || 10;
        const magicMultiplier = Math.pow(5, bonus); // +1 = 5x, +2 = 25x, +3 = 125x

        return baseCost * magicMultiplier;
    }

    getArmorCost(armorType, bonus) {
        const baseCosts = {
            'padded': 5, 'leather': 10, 'studded leather': 45,
            'hide': 10, 'chain shirt': 50, 'scale mail': 50,
            'breastplate': 400, 'half plate': 750, 'ring mail': 30,
            'chain mail': 75, 'splint': 200, 'plate': 1500
        };

        const baseCost = baseCosts[armorType] || 50;
        const magicMultiplier = Math.pow(4, bonus); // +1 = 4x, +2 = 16x

        return baseCost * magicMultiplier;
    }
}

module.exports = PlayerRecommendationService;