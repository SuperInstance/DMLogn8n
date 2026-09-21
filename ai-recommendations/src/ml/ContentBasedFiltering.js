const natural = require('natural');
const winston = require('winston');

class ContentBasedFiltering {
    constructor(options = {}) {
        this.tfidf = new natural.TfIdf();
        this.tokenizer = new natural.WordTokenizer();
        this.stemmer = natural.PorterStemmer;
        this.contentFeatures = new Map();
        this.userProfiles = new Map();
        this.minFeatureWeight = options.minFeatureWeight || 0.01;
        this.maxFeatures = options.maxFeatures || 1000;
        this.decayFactor = options.decayFactor || 0.95;
    }

    // Extract features from D&D content
    extractContentFeatures(content) {
        try {
            const features = {
                // Text features
                keywords: this.extractTextFeatures(content.description || ''),
                title: this.extractTextFeatures(content.title || ''),
                tags: content.tags || [],

                // D&D specific features
                class: content.class || [],
                level: content.level || 0,
                school: content.school || '',
                type: content.type || '',
                rarity: content.rarity || '',
                difficulty: content.difficulty || 0,
                duration: content.duration || '',
                components: content.components || [],

                // Categorical features
                category: content.category || '',
                subcategory: content.subcategory || '',
                source: content.source || '',
                author: content.author || '',

                // Numerical features
                rating: content.rating || 0,
                downloads: content.downloads || 0,
                likes: content.likes || 0,

                // Metadata
                created: new Date(content.createdAt || Date.now()),
                updated: new Date(content.updatedAt || Date.now())
            };

            // Process and normalize features
            return this.processFeatures(features);
        } catch (error) {
            winston.error('Error extracting content features:', error);
            return this.getDefaultFeatures();
        }
    }

    // Extract text features using NLP
    extractTextFeatures(text) {
        try {
            if (!text || typeof text !== 'string') return [];

            // Tokenize and stem
            const tokens = this.tokenizer.tokenize(text.toLowerCase());
            const stemmedTokens = tokens.map(token => this.stemmer.stem(token));

            // Remove stopwords and short words
            const stopWords = natural.stopwords;
            const filteredTokens = stemmedTokens.filter(token =>
                token.length > 2 && !stopWords.includes(token)
            );

            // Extract D&D specific terms
            const dndTerms = this.extractDnDTerms(text);
            const allTokens = [...filteredTokens, ...dndTerms];

            // Remove duplicates and return
            return [...new Set(allTokens)];
        } catch (error) {
            winston.error('Error extracting text features:', error);
            return [];
        }
    }

    // Extract D&D specific terminology
    extractDnDTerms(text) {
        const dndPatterns = {
            classes: /\\b(wizard|fighter|rogue|cleric|paladin|bard|druid|ranger|monk|barbarian|sorcerer|warlock|artificer)\\b/gi,
            races: /\\b(human|elf|dwarf|halfling|gnome|dragonborn|tiefling|half-elf|half-orc|aasimar|genasi|goliath|firbolg|kenku|lizardfolk|tabaxi|triton|bugbear|goblin|hobgoblin|kobold|orc|yuan-ti-pureblood)\\b/gi,
            abilities: /\\b(strength|dexterity|constitution|intelligence|wisdom|charisma|str|dex|con|int|wis|cha)\\b/gi,
            skills: /\\b(acrobatics|athletics|deception|history|insight|intimidation|investigation|medicine|nature|perception|performance|persuasion|religion|sleight of hand|stealth|survival|arcana|animal handling)\\b/gi,
            conditions: /\\b(blinded|charmed|deafened|exhaustion|frightened|grappled|incapacitated|invisible|paralyzed|petrified|poisoned|prone|restrained|stunned|unconscious)\\b/gi,
            damage: /\\b(acid|bludgeoning|cold|fire|force|lightning|necrotic|piercing|poison|psychic|radiant|slashing|thunder)\\b/gi,
            schools: /\\b(abjuration|conjuration|divination|enchantment|evocation|illusion|necromancy|transmutation)\\b/gi,
            levels: /\\b(cantrip|level [1-9]|1st level|2nd level|3rd level|4th level|5th level|6th level|7th level|8th level|9th level)\\b/gi,
            rarities: /\\b(common|uncommon|rare|very rare|legendary|artifact)\\b/gi,
            alignments: /\\b(lawful good|neutral good|chaotic good|lawful neutral|true neutral|chaotic neutral|lawful evil|neutral evil|chaotic evil|lg|ng|cg|ln|n|cn|le|ne|ce)\\b/gi
        };

        const terms = [];
        Object.values(dndPatterns).forEach(pattern => {
            const matches = text.match(pattern);
            if (matches) {
                terms.push(...matches.map(m => m.toLowerCase()));
            }
        });

        return [...new Set(terms)];
    }

    // Process and normalize features
    processFeatures(features) {
        const processed = {
            ...features,
            // Combine all text features
            allTextFeatures: [...new Set([
                ...features.keywords,
                ...features.title,
                ...features.tags
            ])],
            // Normalize numerical features
            normalizedLevel: Math.min(features.level / 20, 1), // Normalize to 0-1
            normalizedDifficulty: Math.min(features.difficulty / 10, 1),
            normalizedRating: Math.min(features.rating / 5, 1),
            // Time-based features
            ageInDays: (Date.now() - features.created.getTime()) / (1000 * 60 * 60 * 24),
            recencyScore: this.calculateRecencyScore(features.created)
        };

        return processed;
    }

    // Calculate recency score
    calculateRecencyScore(date) {
        const daysOld = (Date.now() - date.getTime()) / (1000 * 60 * 60 * 24);
        return Math.exp(-daysOld / 30); // Exponential decay over 30 days
    }

    // Get default features for empty content
    getDefaultFeatures() {
        return {
            keywords: [],
            title: [],
            tags: [],
            class: [],
            level: 0,
            school: '',
            type: '',
            rarity: '',
            difficulty: 0,
            duration: '',
            components: [],
            category: '',
            subcategory: '',
            source: '',
            author: '',
            rating: 0,
            downloads: 0,
            likes: 0,
            allTextFeatures: [],
            normalizedLevel: 0,
            normalizedDifficulty: 0,
            normalizedRating: 0,
            ageInDays: 0,
            recencyScore: 0
        };
    }

    // Build content feature vectors
    buildContentProfiles(contents) {
        try {
            // Reset TF-IDF
            this.tfidf = new natural.TfIdf();

            // Build documents for TF-IDF
            const documents = [];
            const contentMap = new Map();

            contents.forEach(content => {
                const features = this.extractContentFeatures(content);
                const document = features.allTextFeatures.join(' ');

                documents.push(document);
                contentMap.set(content._id.toString(), features);

                // Add to TF-IDF
                this.tfidf.addDocument(document);
            });

            // Store content features
            this.contentFeatures = contentMap;

            // Build feature vectors for all content
            this.contentVectors = new Map();
            contentMap.forEach((features, contentId) => {
                const vector = this.buildContentVector(features, contentId);
                this.contentVectors.set(contentId, vector);
            });

            winston.info(`Built content profiles for ${contents.length} items`);
        } catch (error) {
            winston.error('Error building content profiles:', error);
            throw error;
        }
    }

    // Build feature vector for content
    buildContentVector(features, contentId) {
        const vector = new Map();

        // Add TF-IDF weighted text features
        if (this.tfidf.documents.length > 0) {
            const docIndex = Array.from(this.contentFeatures.keys()).indexOf(contentId);
            if (docIndex >= 0) {
                this.tfidf.listTerms(docIndex).forEach(term => {
                    vector.set(`text_${term.term}`, term.tfidf);
                });
            }
        }

        // Add categorical features
        if (features.category) {
            vector.set(`category_${features.category}`, 1);
        }
        if (features.subcategory) {
            vector.set(`subcategory_${features.subcategory}`, 1);
        }
        if (features.type) {
            vector.set(`type_${features.type}`, 1);
        }
        if (features.school) {
            vector.set(`school_${features.school}`, 1);
        }
        if (features.rarity) {
            vector.set(`rarity_${features.rarity}`, 1);
        }

        // Add class features
        features.class.forEach(cls => {
            vector.set(`class_${cls.toLowerCase()}`, 1);
        });

        // Add numerical features
        vector.set('level', features.normalizedLevel);
        vector.set('difficulty', features.normalizedDifficulty);
        vector.set('rating', features.normalizedRating);
        vector.set('recency', features.recencyScore);

        // Add D&D specific features
        features.allTextFeatures.forEach(term => {
            if (this.isDnDTerm(term)) {
                vector.set(`dnd_${term}`, 1);
            }
        });

        return vector;
    }

    // Check if term is D&D specific
    isDnDTerm(term) {
        const dndTerms = [
            'wizard', 'fighter', 'rogue', 'cleric', 'paladin', 'bard', 'druid',
            'ranger', 'monk', 'barbarian', 'sorcerer', 'warlock', 'artificer',
            'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma',
            'acrobatics', 'athletics', 'deception', 'history', 'insight', 'intimidation',
            'acid', 'bludgeoning', 'cold', 'fire', 'force', 'lightning', 'necrotic',
            'abjuration', 'conjuration', 'divination', 'enchantment', 'evocation',
            'illusion', 'necromancy', 'transmutation', 'cantrip', 'common', 'uncommon',
            'rare', 'legendary', 'artifact'
        ];

        return dndTerms.includes(term.toLowerCase());
    }

    // Build user profile based on interaction history
    buildUserProfile(userId, interactions) {
        try {
            const profile = {
                positiveFeatures: new Map(),
                negativeFeatures: new Map(),
                categoryPreferences: new Map(),
                classPreferences: new Map(),
                levelPreference: 0,
                difficultyPreference: 0,
                recentInteractions: [],
                totalInteractions: interactions.length
            };

            let totalPositiveWeight = 0;
            let totalNegativeWeight = 0;

            interactions.forEach(interaction => {
                const contentId = interaction.contentId;
                const contentFeatures = this.contentFeatures.get(contentId);

                if (!contentFeatures) return;

                const weight = this.getInteractionWeight(interaction);
                const isPositive = this.isPositiveInteraction(interaction);

                if (isPositive) {
                    totalPositiveWeight += weight;
                    this.updateFeatures(profile.positiveFeatures, contentFeatures, weight);
                    this.updateCategoryPreferences(profile.categoryPreferences, contentFeatures, weight);
                    this.updateClassPreferences(profile.classPreferences, contentFeatures, weight);
                    profile.levelPreference += contentFeatures.normalizedLevel * weight;
                    profile.difficultyPreference += contentFeatures.normalizedDifficulty * weight;
                } else {
                    totalNegativeWeight += weight;
                    this.updateFeatures(profile.negativeFeatures, contentFeatures, weight);
                }

                // Track recent interactions
                profile.recentInteractions.push({
                    contentId,
                    action: interaction.action,
                    timestamp: interaction.timestamp,
                    weight
                });
            });

            // Normalize preferences
            if (totalPositiveWeight > 0) {
                profile.levelPreference /= totalPositiveWeight;
                profile.difficultyPreference /= totalPositiveWeight;

                // Normalize feature weights
                for (const [feature, weight] of profile.positiveFeatures) {
                    profile.positiveFeatures.set(feature, weight / totalPositiveWeight);
                }
            }

            // Sort recent interactions by timestamp
            profile.recentInteractions.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            profile.recentInteractions = profile.recentInteractions.slice(0, 50); // Keep last 50

            this.userProfiles.set(userId, profile);

            return profile;
        } catch (error) {
            winston.error('Error building user profile:', error);
            return this.getDefaultUserProfile();
        }
    }

    // Get interaction weight
    getInteractionWeight(interaction) {
        const weights = {
            'view': 1,
            'like': 3,
            'save': 4,
            'share': 5,
            'comment': 3,
            'rating_5': 5,
            'rating_4': 4,
            'rating_3': 3,
            'rating_2': 2,
            'rating_1': 1,
            'purchase': 6,
            'play': 4
        };

        return weights[interaction.action] || 1;
    }

    // Check if interaction is positive
    isPositiveInteraction(interaction) {
        const positiveActions = ['like', 'save', 'share', 'comment', 'rating_4', 'rating_5', 'purchase', 'play'];
        const negativeActions = ['rating_1', 'rating_2'];

        if (positiveActions.includes(interaction.action)) return true;
        if (negativeActions.includes(interaction.action)) return false;

        // For neutral actions like 'view', consider them slightly positive
        return true;
    }

    // Update feature weights
    updateFeatures(featureMap, contentFeatures, weight) {
        // Update text features
        contentFeatures.allTextFeatures.forEach(feature => {
            const currentWeight = featureMap.get(`text_${feature}`) || 0;
            featureMap.set(`text_${feature}`, currentWeight + weight);
        });

        // Update categorical features
        if (contentFeatures.category) {
            const currentWeight = featureMap.get(`category_${contentFeatures.category}`) || 0;
            featureMap.set(`category_${contentFeatures.category}`, currentWeight + weight);
        }

        // Update class features
        contentFeatures.class.forEach(cls => {
            const feature = `class_${cls.toLowerCase()}`;
            const currentWeight = featureMap.get(feature) || 0;
            featureMap.set(feature, currentWeight + weight);
        });
    }

    // Update category preferences
    updateCategoryPreferences(categoryMap, contentFeatures, weight) {
        if (contentFeatures.category) {
            const current = categoryMap.get(contentFeatures.category) || 0;
            categoryMap.set(contentFeatures.category, current + weight);
        }
    }

    // Update class preferences
    updateClassPreferences(classMap, contentFeatures, weight) {
        contentFeatures.class.forEach(cls => {
            const current = classMap.get(cls) || 0;
            classMap.set(cls, current + weight);
        });
    }

    // Get default user profile
    getDefaultUserProfile() {
        return {
            positiveFeatures: new Map(),
            negativeFeatures: new Map(),
            categoryPreferences: new Map(),
            classPreferences: new Map(),
            levelPreference: 0.5,
            difficultyPreference: 0.5,
            recentInteractions: [],
            totalInteractions: 0
        };
    }

    // Generate content-based recommendations
    generateRecommendations(userId, numRecommendations = 10) {
        try {
            const userProfile = this.userProfiles.get(userId);
            if (!userProfile || userProfile.totalInteractions === 0) {
                return this.getColdStartRecommendations(numRecommendations);
            }

            const candidateContent = this.getCandidateContent(userId);
            const scoredContent = [];

            candidateContent.forEach(contentId => {
                const score = this.calculateContentScore(contentId, userProfile);
                if (score > 0) {
                    scoredContent.push({
                        contentId,
                        score,
                        type: 'content_based',
                        method: 'feature_matching'
                    });
                }
            });

            // Sort by score and return top recommendations
            return scoredContent
                .sort((a, b) => b.score - a.score)
                .slice(0, numRecommendations);

        } catch (error) {
            winston.error('Error generating content-based recommendations:', error);
            return this.getColdStartRecommendations(numRecommendations);
        }
    }

    // Get candidate content (exclude already interacted content)
    getCandidateContent(userId) {
        const userProfile = this.userProfiles.get(userId);
        if (!userProfile) return [];

        const interactedIds = new Set(
            userProfile.recentInteractions.map(interaction => interaction.contentId)
        );

        return Array.from(this.contentVectors.keys()).filter(contentId =>
            !interactedIds.has(contentId)
        );
    }

    // Calculate content score based on user profile
    calculateContentScore(contentId, userProfile) {
        try {
            const contentVector = this.contentVectors.get(contentId);
            if (!contentVector) return 0;

            let score = 0;

            // Positive feature matching
            for (const [feature, contentWeight] of contentVector) {
                const userWeight = userProfile.positiveFeatures.get(feature) || 0;
                score += contentWeight * userWeight;

                // Penalize negative features
                const negativeWeight = userProfile.negativeFeatures.get(feature) || 0;
                score -= contentWeight * negativeWeight * 0.5;
            }

            // Category preference bonus
            const contentFeatures = this.contentFeatures.get(contentId);
            if (contentFeatures && contentFeatures.category) {
                const categoryPref = userProfile.categoryPreferences.get(contentFeatures.category) || 0;
                score += categoryPref * 0.3;
            }

            // Class preference bonus
            if (contentFeatures && contentFeatures.class) {
                let classBonus = 0;
                contentFeatures.class.forEach(cls => {
                    const classPref = userProfile.classPreferences.get(cls) || 0;
                    classBonus += classPref * 0.2;
                });
                score += classBonus;
            }

            // Level and difficulty matching
            if (contentFeatures) {
                const levelDiff = Math.abs(contentFeatures.normalizedLevel - userProfile.levelPreference);
                const difficultyDiff = Math.abs(contentFeatures.normalizedDifficulty - userProfile.difficultyPreference);

                score += (1 - levelDiff) * 0.2;
                score += (1 - difficultyDiff) * 0.1;
            }

            // Recency bonus (prefer newer content)
            if (contentFeatures) {
                score += contentFeatures.recencyScore * 0.1;
            }

            return Math.max(0, score);
        } catch (error) {
            winston.error('Error calculating content score:', error);
            return 0;
        }
    }

    // Cold start recommendations
    getColdStartRecommendations(numRecommendations = 10) {
        // Return diverse content from different categories
        const recommendations = [];
        const categories = [...new Set(
            Array.from(this.contentFeatures.values()).map(f => f.category).filter(Boolean)
        )];

        categories.forEach(category => {
            const categoryContent = Array.from(this.contentFeatures.entries())
                .filter(([id, features]) => features.category === category)
                .sort((a, b) => (b[1].rating + b[1].downloads * 0.1) - (a[1].rating + a[1].downloads * 0.1))
                .slice(0, 2);

            categoryContent.forEach(([contentId, features]) => {
                recommendations.push({
                    contentId,
                    score: features.rating + features.downloads * 0.1,
                    type: 'content_based',
                    method: 'cold_start',
                    category: features.category
                });
            });
        });

        return recommendations
            .sort((a, b) => b.score - a.score)
            .slice(0, numRecommendations);
    }

    // Update content features
    updateContentFeatures(content) {
        const features = this.extractContentFeatures(content);
        this.contentFeatures.set(content._id.toString(), features);

        const vector = this.buildContentVector(features, content._id.toString());
        this.contentVectors.set(content._id.toString(), vector);
    }

    // Get similar content
    getSimilarContent(contentId, numSimilar = 10) {
        try {
            const targetVector = this.contentVectors.get(contentId);
            if (!targetVector) return [];

            const similarities = [];

            this.contentVectors.forEach((vector, id) => {
                if (id !== contentId) {
                    const similarity = this.calculateCosineSimilarity(targetVector, vector);
                    if (similarity > 0.1) {
                        similarities.push({
                            contentId: id,
                            similarity,
                            type: 'content_similarity'
                        });
                    }
                }
            });

            return similarities
                .sort((a, b) => b.similarity - a.similarity)
                .slice(0, numSimilar);

        } catch (error) {
            winston.error('Error finding similar content:', error);
            return [];
        }
    }

    // Calculate cosine similarity between two feature vectors
    calculateCosineSimilarity(vec1, vec2) {
        let dotProduct = 0;
        let norm1 = 0;
        let norm2 = 0;

        const allFeatures = new Set([...vec1.keys(), ...vec2.keys()]);

        for (const feature of allFeatures) {
            const val1 = vec1.get(feature) || 0;
            const val2 = vec2.get(feature) || 0;

            dotProduct += val1 * val2;
            norm1 += val1 * val1;
            norm2 += val2 * val2;
        }

        if (norm1 === 0 || norm2 === 0) return 0;

        return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
    }
}

module.exports = ContentBasedFiltering;