const EventEmitter = require('events');
const axios = require('axios');

class MultiLanguageSupportSystem extends EventEmitter {
  constructor(options = {}) {
    super();

    // Translation providers
    this.providers = {
      google: null,
      deepl: null,
      azure: null,
      aws: null,
      local: null
    };

    // Language mappings
    this.languageMappings = new Map();
    this.initializeLanguageMappings();

    // Cultural context handlers
    this.culturalContextHandlers = new Map();
    this.initializeCulturalContextHandlers();

    // D&D-specific terminology
    this.dndTerminology = new Map();
    this.initializeDNDTerminology();

    // Fantasy languages
    this.fantasyLanguages = new Map();
    this.initializeFantasyLanguages();

    // Translation cache
    this.translationCache = new Map();
    this.cacheStats = {
      hits: 0,
      misses: 0,
      translations: 0
    };

    // Configuration
    this.options = {
      defaultProvider: options.defaultProvider || 'google',
      cacheSize: options.cacheSize || 10000,
      enableContextPreservation: options.enableContextPreservation !== false,
      enableCulturalNuance: options.enableCulturalNuance !== false,
      enableFantasyLanguageTranslation: options.enableFantasyLanguageTranslation !== false,
      preserveFormatting: options.preserveFormatting !== false,
      autoDetectLanguage: options.autoDetectLanguage !== false,
      maxRetries: options.maxRetries || 3,
      timeout: options.timeout || 10000,
      ...options
    };

    // Initialize providers
    this.initializeProviders();

    // Start cache cleanup
    this.startCacheCleanup();
  }

  initializeLanguageMappings() {
    // Real-world languages
    this.languageMappings.set('en', {
      name: 'English',
      code: 'en',
      region: 'global',
      dndContext: 'Common',
      culturalMarkers: ['the', 'and', 'is', 'are'],
      formality: 'medium',
      direction: 'ltr'
    });

    this.languageMappings.set('es', {
      name: 'Español',
      code: 'es',
      region: 'spain/latin_america',
      dndContext: 'Común',
      culturalMarkers: ['el', 'la', 'y', 'es', 'son'],
      formality: 'medium-high',
      direction: 'ltr'
    });

    this.languageMappings.set('fr', {
      name: 'Français',
      code: 'fr',
      region: 'france',
      dndContext: 'Commun',
      culturalMarkers: ['le', 'la', 'et', 'est', 'sont'],
      formality: 'high',
      direction: 'ltr'
    });

    this.languageMappings.set('de', {
      name: 'Deutsch',
      code: 'de',
      region: 'germany',
      dndContext: 'Gemeinsprache',
      culturalMarkers: ['der', 'die', 'das', 'und', 'ist'],
      formality: 'medium-high',
      direction: 'ltr'
    });

    this.languageMappings.set('ja', {
      name: '日本語',
      code: 'ja',
      region: 'japan',
      dndContext: '共通語',
      culturalMarkers: ['の', 'に', 'は', 'です', 'ます'],
      formality: 'high',
      direction: 'ltr',
      honorifics: true
    });

    this.languageMappings.set('zh', {
      name: '中文',
      code: 'zh',
      region: 'china',
      dndContext: '通用语',
      culturalMarkers: ['的', '了', '和', '是', '在'],
      formality: 'high',
      direction: 'ltr'
    });

    this.languageMappings.set('ru', {
      name: 'Русский',
      code: 'ru',
      region: 'russia',
      dndContext: 'Общий',
      culturalMarkers: ['и', 'в', 'на', 'есть', 'суть'],
      formality: 'medium',
      direction: 'ltr'
    });

    this.languageMappings.set('ar', {
      name: 'العربية',
      code: 'ar',
      region: 'middle_east',
      dndContext: 'اللغة المشتركة',
      culturalMarkers: ['في', 'من', 'و', 'هو', 'هي'],
      formality: 'high',
      direction: 'rtl'
    });
  }

  initializeCulturalContextHandlers() {
    // Cultural nuance handlers for different regions
    this.culturalContextHandlers.set('japan', {
      formality: {
        levels: ['casual', 'polite', 'formal', 'honorific'],
        defaultLevel: 'polite',
        contextRules: {
          stranger: 'formal',
          friend: 'casual',
          elder: 'honorific',
          superior: 'honorific'
        }
      },
      honorifics: {
        '-san': 'mr/ms',
        '-sama': 'lord/lady',
        '-sensei': 'master/teacher',
        '-kun': 'young boy',
        '-chan': 'young girl/close friend'
      },
      culturalNotes: {
        directness: 'indirect',
        emotionExpression: 'subtle',
        hierarchy: 'important',
        groupHarmony: 'valued'
      }
    });

    this.culturalContextHandlers.set('germany', {
      formality: {
        levels: ['informal', 'formal'],
        defaultLevel: 'formal',
        contextRules: {
          stranger: 'formal',
          friend: 'informal',
          professional: 'formal'
        }
      },
      titles: {
        'Herr': 'Mr.',
        'Frau': 'Ms.',
        'Dr.': 'Dr.',
        'Prof.': 'Prof.'
      },
      culturalNotes: {
        directness: 'direct',
        precision: 'valued',
        punctuality: 'important',
        structure: 'preferred'
      }
    });

    this.culturalContextHandlers.set('latin_america', {
      formality: {
        levels: ['informal', 'formal'],
        defaultLevel: 'formal',
        contextRules: {
          stranger: 'formal',
          friend: 'informal',
          elder: 'formal',
          family: 'informal'
        }
      },
      culturalNotes: {
        warmth: 'high',
        family: 'important',
        personalRelationships: 'valued',
        flexibility: 'appreciated'
      }
    });
  }

  initializeDNDTerminology() {
    // D&D-specific terminology translations
    const dndTerms = {
      'hit points': {
        es: 'puntos de golpe',
        fr: 'points de vie',
        de: 'Trefferpunkte',
        ja: 'ヒットポイント',
        zh: '生命值',
        ru: 'попадания'
      },
      'armor class': {
        es: 'clase de armadura',
        fr: 'classe d\'armure',
        de: 'Rüstungsklasse',
        ja: 'アーマークラス',
        zh: '护甲等级',
        ru: 'класс брони'
      },
      'saving throw': {
        es: 'tirada de salvación',
        fr: 'jet de sauvegarde',
        de: 'Rettungswurf',
        ja: 'セービングスロー',
        zh: '豁免检定',
        ru: 'спасбросок'
      },
      'skill check': {
        es: 'tirada de habilidad',
        fr: 'jet de compétence',
        de: 'Fertigkeitswurf',
        ja: '技能判定',
        zh: '技能检定',
        ru: 'проверка навыка'
      },
      'critical hit': {
        es: 'golpe crítico',
        fr: 'coup critique',
        de: 'kritischer Treffer',
        ja: 'クリティカルヒット',
        zh: '重击',
        ru: 'критический удар'
      },
      'natural 20': {
        es: '20 natural',
        fr: '20 naturel',
        de: 'natürliche 20',
        ja: 'ナチュラル20',
        zh: '自然20',
        ru: 'натуральная 20'
      },
      'dragon': {
        es: 'dragón',
        fr: 'dragon',
        de: 'Drache',
        ja: 'ドラゴン',
        zh: '龙',
        ru: 'дракон'
      },
      'dungeon': {
        es: 'mazmorra',
        fr: 'donjon',
        de: 'Verlies',
        ja: 'ダンジョン',
        zh: '地城',
        ru: 'подземелье'
      },
      'quest': {
        es: 'misión',
        fr: 'quête',
        de: 'Quest',
        ja: 'クエスト',
        zh: '任务',
        ru: 'квест'
      },
      'magic': {
        es: 'magia',
        fr: 'magie',
        de: 'Magie',
        ja: '魔法',
        zh: '魔法',
        ru: 'магия'
      }
    };

    for (const [term, translations] of Object.entries(dndTerms)) {
      this.dndTerminology.set(term.toLowerCase(), translations);
    }
  }

  initializeFantasyLanguages() {
    // Fantasy language translations
    this.fantasyLanguages.set('dwarvish', {
      name: 'Dwarvish',
      script: 'runic',
      characteristics: ['harsh', 'guttural', 'resonant'],
      commonPhrases: {
        'hello': 'Berrûn',
        'goodbye': 'Khazâd',
        'thank you': 'Mahal',
        'yes': 'Khad',
        'no': 'Nag',
        'friend': 'Baraz',
        'enemy': 'Gund',
        'stone': 'Gundabad',
        'gold': 'Thang',
        'axe': 'Azan'
      },
      culturalContext: {
        importance: ['mining', 'craftsmanship', 'honor', 'tradition'],
        values: ['loyalty', 'strength', 'endurance'],
        speechPatterns: ['direct', 'formal', 'respectful']
      }
    });

    this.fantasyLanguages.set('elvish', {
      name: 'Elvish',
      script: 'elvish',
      characteristics: ['melodic', 'flowing', 'elegant'],
      commonPhrases: {
        'hello': 'Amin mela lle',
        'goodbye': 'Namarie',
        'thank you': 'Hantanyel',
        'yes': 'Amin',
        'no': 'Av\'est',
        'friend': 'Mellon',
        'enemy': 'Host',
        'star': 'Elen',
        'forest': 'Taur',
        'magic': 'Magia'
      },
      culturalContext: {
        importance: ['nature', 'beauty', 'wisdom', 'art'],
        values: ['harmony', 'patience', 'perfection'],
        speechPatterns: ['poetic', 'formal', 'elegant']
      }
    });

    this.fantasyLanguages.set('draconic', {
      name: 'Draconic',
      script: 'draconic',
      characteristics: ['ancient', 'powerful', 'majestic'],
      commonPhrases: {
        'hello': 'Vercath',
        'goodbye': 'Thric',
        'thank you': 'Zhaan',
        'yes': 'Ith',
        'no': 'Neg',
        'power': 'Thak',
        'wisdom': 'Skaath',
        'fire': 'Ignis',
        'mortal': 'Thrae',
        'eternal': 'Aevum'
      },
      culturalContext: {
        importance: ['power', 'knowledge', 'longevity', 'magic'],
        values: ['dominance', 'wisdom', 'patience'],
        speechPatterns: ['authoritative', 'deliberate', 'ancient']
      }
    });

    this.fantasyLanguages.set('orcish', {
      name: 'Orcish',
      script: 'angular',
      characteristics: ['aggressive', 'simple', 'direct'],
      commonPhrases: {
        'hello': 'Lok\'tar',
        'goodbye': 'Dabu',
        'thank you': 'Gar\'shak',
        'yes': 'Da',
        'no': 'Ne',
        'fight': 'Grom',
        'strong': 'Mak\'gora',
        'victory': 'Lok\'tar ogar',
        'weak': 'Nag\'gar',
        'chief': 'Warchief'
      },
      culturalContext: {
        importance: ['strength', 'honor', 'victory', 'clan'],
        values: ['power', 'courage', 'loyalty'],
        speechPatterns: ['direct', 'simple', 'forceful']
      }
    });
  }

  initializeProviders() {
    // Initialize Google Translate
    if (process.env.GOOGLE_TRANSLATE_API_KEY) {
      this.providers.google = {
        apiKey: process.env.GOOGLE_TRANSLATE_API_KEY,
        endpoint: 'https://translation.googleapis.com/language/translate/v2'
      };
    }

    // Initialize DeepL
    if (process.env.DEEPL_API_KEY) {
      this.providers.deepl = {
        apiKey: process.env.DEEPL_API_KEY,
        endpoint: 'https://api-free.deepl.com/v2/translate'
      };
    }

    // Initialize Azure Translator
    if (process.env.AZURE_TRANSLATOR_KEY && process.env.AZURE_TRANSLATOR_REGION) {
      this.providers.azure = {
        apiKey: process.env.AZURE_TRANSLATOR_KEY,
        region: process.env.AZURE_TRANSLATOR_REGION,
        endpoint: 'https://api.cognitive.microsofttranslator.com'
      };
    }

    // Local translation fallback
    this.providers.local = {
      available: true,
      translations: new Map() // Simple local translation cache
    };
  }

  async translateText(text, targetLanguage, sourceLanguage = 'auto', context = {}) {
    try {
      // Generate cache key
      const cacheKey = this.generateCacheKey(text, sourceLanguage, targetLanguage, context);

      // Check cache
      if (this.translationCache.has(cacheKey)) {
        this.cacheStats.hits++;
        return this.translationCache.get(cacheKey);
      }

      this.cacheStats.misses++;

      // Auto-detect source language if needed
      const detectedLanguage = sourceLanguage === 'auto'
        ? await this.detectLanguage(text)
        : sourceLanguage;

      // Pre-process text with D&D terminology
      const processedText = this.preProcessText(text, detectedLanguage, targetLanguage);

      // Translate text
      const translatedText = await this.translateWithProviders(
        processedText,
        detectedLanguage,
        targetLanguage,
        context
      );

      // Post-process translation
      const finalTranslation = this.postProcessTranslation(
        translatedText,
        detectedLanguage,
        targetLanguage,
        context
      );

      // Cache result
      this.cacheTranslation(cacheKey, finalTranslation);
      this.cacheStats.translations++;

      this.emit('textTranslated', {
        originalText: text,
        translatedText: finalTranslation,
        sourceLanguage: detectedLanguage,
        targetLanguage,
        context,
        timestamp: new Date().toISOString()
      });

      return finalTranslation;

    } catch (error) {
      console.error('Translation error:', error);
      this.emit('translationError', {
        text,
        sourceLanguage,
        targetLanguage,
        error: error.message,
        timestamp: new Date().toISOString()
      });
      throw new Error(`Translation failed: ${error.message}`);
    }
  }

  async detectLanguage(text) {
    if (!this.options.autoDetectLanguage) {
      return 'en'; // Default to English
    }

    try {
      // Simple language detection based on character patterns
      const detected = this.simpleLanguageDetection(text);
      if (detected.confidence > 0.7) {
        return detected.language;
      }

      // Fallback to provider detection if available
      if (this.providers.google) {
        const response = await axios.post(
          `${this.providers.google.endpoint}/detect`,
          {
            q: text,
            key: this.providers.google.apiKey
          },
          { timeout: this.options.timeout }
        );

        return response.data.data.detections[0][0].language;
      }

      return 'en'; // Default fallback

    } catch (error) {
      console.warn('Language detection failed, defaulting to English:', error.message);
      return 'en';
    }
  }

  simpleLanguageDetection(text) {
    const textLower = text.toLowerCase();
    const detections = [];

    // Check for language markers
    for (const [code, lang] of this.languageMappings) {
      let score = 0;
      const markers = lang.culturalMarkers || [];

      markers.forEach(marker => {
        const occurrences = (textLower.match(new RegExp(marker, 'g')) || []).length;
        score += occurrences;
      });

      if (score > 0) {
        detections.push({ language: code, score, confidence: Math.min(score * 0.1, 1.0) });
      }
    }

    detections.sort((a, b) => b.confidence - a.confidence);
    return detections[0] || { language: 'en', confidence: 0.5 };
  }

  preProcessText(text, sourceLanguage, targetLanguage) {
    let processedText = text;

    // Handle D&D terminology preservation
    processedText = this.handleDNDTerminology(processedText, sourceLanguage, targetLanguage);

    // Handle fantasy languages
    if (this.options.enableFantasyLanguageTranslation) {
      processedText = this.handleFantasyLanguages(processedText, sourceLanguage, targetLanguage);
    }

    // Preserve formatting
    if (this.options.preserveFormatting) {
      processedText = this.preserveFormatting(processedText);
    }

    return processedText;
  }

  handleDNDTerminology(text, sourceLanguage, targetLanguage) {
    let processedText = text;

    // Find and protect D&D terms
    const dndTermPattern = /\b(hit points|armor class|saving throw|skill check|critical hit|natural 20|dragon|dungeon|quest|magic)\b/gi;

    processedText = processedText.replace(dndTermPattern, (match) => {
      return `[DND_TERM:${match.toLowerCase()}]`;
    });

    return processedText;
  }

  handleFantasyLanguages(text, sourceLanguage, targetLanguage) {
    // Check if text contains fantasy language content
    for (const [langName, langData] of this.fantasyLanguages) {
      const phrases = Object.keys(langData.commonPhrases);
      for (const phrase of phrases) {
        if (text.toLowerCase().includes(phrase.toLowerCase())) {
          // Mark for fantasy language handling
          text = text.replace(
            new RegExp(phrase, 'gi'),
            `[FANTASY_LANG:${langName}:${phrase}]`
          );
        }
      }
    }

    return text;
  }

  preserveFormatting(text) {
    // Protect formatting elements
    return text
      .replace(/\*\*(.*?)\*\*/g, '[BOLD]$1[/BOLD]')
      .replace(/\*(.*?)\*/g, '[ITALIC]$1[/ITALIC]')
      .replace(/`(.*?)`/g, '[CODE]$1[/CODE]')
      .replace(/\n/g, '[NEWLINE]')
      .replace(/\t/g, '[TAB]');
  }

  async translateWithProviders(text, sourceLanguage, targetLanguage, context) {
    const providers = this.getAvailableProviders();
    const providerOrder = this.determineProviderOrder(providers);

    for (const providerName of providerOrder) {
      try {
        const result = await this.translateWithProvider(
          text,
          sourceLanguage,
          targetLanguage,
          providerName,
          context
        );
        return result;
      } catch (error) {
        console.warn(`Provider ${providerName} failed:`, error.message);
        continue;
      }
    }

    throw new Error('All translation providers failed');
  }

  getAvailableProviders() {
    return Object.entries(this.providers)
      .filter(([name, provider]) => provider !== null && provider !== undefined)
      .map(([name]) => name);
  }

  determineProviderOrder(providers) {
    // Priority order for providers
    const priority = ['deepl', 'google', 'azure', 'aws', 'local'];

    return priority
      .filter(p => providers.includes(p))
      .concat(providers.filter(p => !priority.includes(p)));
  }

  async translateWithProvider(text, sourceLanguage, targetLanguage, providerName, context) {
    switch (providerName) {
      case 'google':
        return await this.translateWithGoogle(text, sourceLanguage, targetLanguage);
      case 'deepl':
        return await this.translateWithDeepL(text, sourceLanguage, targetLanguage);
      case 'azure':
        return await this.translateWithAzure(text, sourceLanguage, targetLanguage);
      case 'local':
        return await this.translateWithLocal(text, sourceLanguage, targetLanguage);
      default:
        throw new Error(`Unsupported provider: ${providerName}`);
    }
  }

  async translateWithGoogle(text, sourceLanguage, targetLanguage) {
    const response = await axios.post(
      `${this.providers.google.endpoint}`,
      {
        q: text,
        source: sourceLanguage === 'auto' ? undefined : sourceLanguage,
        target: targetLanguage,
        format: 'text',
        key: this.providers.google.apiKey
      },
      { timeout: this.options.timeout }
    );

    return response.data.data.translations[0].translatedText;
  }

  async translateWithDeepL(text, sourceLanguage, targetLanguage) {
    const data = new URLSearchParams();
    data.append('text', text);
    data.append('target_lang', targetLanguage.toUpperCase());
    if (sourceLanguage !== 'auto') {
      data.append('source_lang', sourceLanguage.toUpperCase());
    }

    const response = await axios.post(
      this.providers.deepl.endpoint,
      data,
      {
        headers: {
          'Authorization': `DeepL-Auth-Key ${this.providers.deepl.apiKey}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        timeout: this.options.timeout
      }
    );

    return response.data.translations[0].text;
  }

  async translateWithAzure(text, sourceLanguage, targetLanguage) {
    const response = await axios.post(
      `${this.providers.azure.endpoint}/translate`,
      [{ text: text }],
      {
        params: {
          'api-version': '3.0',
          'from': sourceLanguage === 'auto' ? undefined : sourceLanguage,
          'to': targetLanguage
        },
        headers: {
          'Ocp-Apim-Subscription-Key': this.providers.azure.apiKey,
          'Ocp-Apim-Subscription-Region': this.providers.azure.region,
          'Content-Type': 'application/json'
        },
        timeout: this.options.timeout
      }
    );

    return response.data[0].translations[0].text;
  }

  async translateWithLocal(text, sourceLanguage, targetLanguage) {
    // Simple local translation fallback
    // This could use offline translation libraries or cached translations
    const key = `${sourceLanguage}-${targetLanguage}:${text}`;

    if (this.providers.local.translations.has(key)) {
      return this.providers.local.translations.get(key);
    }

    // Fallback: return original text with language indicator
    return `[${targetLanguage.toUpperCase()}] ${text}`;
  }

  postProcessTranslation(translatedText, sourceLanguage, targetLanguage, context) {
    let processedText = translatedText;

    // Restore D&D terminology
    processedText = this.restoreDNDTerminology(processedText, targetLanguage);

    // Restore fantasy languages
    if (this.options.enableFantasyLanguageTranslation) {
      processedText = this.restoreFantasyLanguages(processedText, targetLanguage);
    }

    // Restore formatting
    if (this.options.preserveFormatting) {
      processedText = this.restoreFormatting(processedText);
    }

    // Apply cultural nuances
    if (this.options.enableCulturalNuance) {
      processedText = this.applyCulturalNuances(processedText, targetLanguage, context);
    }

    // Apply context preservation
    if (this.options.enableContextPreservation) {
      processedText = this.preserveContext(processedText, sourceLanguage, targetLanguage, context);
    }

    return processedText;
  }

  restoreDNDTerminology(text, targetLanguage) {
    const termPattern = /\[DND_TERM:(.*?)\]/g;

    return text.replace(termPattern, (match, term) => {
      const translations = this.dndTerminology.get(term);
      if (translations && translations[targetLanguage]) {
        return translations[targetLanguage];
      }
      return term; // Fallback to original term
    });
  }

  restoreFantasyLanguages(text, targetLanguage) {
    const fantasyPattern = /\[FANTASY_LANG:(.*?):(.*?)\]/g;

    return text.replace(fantasyPattern, (match, langName, phrase) => {
      const langData = this.fantasyLanguages.get(langName);
      if (langData) {
        // Either keep in original fantasy language or translate concept
        if (targetLanguage === 'en') {
          return langData.commonPhrases[phrase] || phrase;
        }
        // For other languages, you might want to provide concept translations
        return phrase;
      }
      return phrase;
    });
  }

  restoreFormatting(text) {
    return text
      .replace(/\[BOLD\](.*?)\[\/BOLD\]/g, '**$1**')
      .replace(/\[ITALIC\](.*?)\[\/ITALIC\]/g, '*$1*')
      .replace(/\[CODE\](.*?)\[\/CODE\]/g, '`$1`')
      .replace(/\[NEWLINE\]/g, '\n')
      .replace(/\[TAB\]/g, '\t');
  }

  applyCulturalNuances(text, targetLanguage, context) {
    const langConfig = this.languageMappings.get(targetLanguage);
    if (!langConfig) return text;

    let processedText = text;

    // Apply cultural context handlers
    const region = langConfig.region;
    const culturalHandler = this.culturalContextHandlers.get(region);

    if (culturalHandler) {
      processedText = this.applyCulturalHandler(processedText, culturalHandler, context);
    }

    // Apply direction-specific formatting
    if (langConfig.direction === 'rtl') {
      processedText = this.applyRTLFormatting(processedText);
    }

    return processedText;
  }

  applyCulturalHandler(text, handler, context) {
    let processedText = text;

    // Apply formality levels
    if (handler.formality && context.relationship) {
      const formalityLevel = this.determineFormalityLevel(
        handler.formality,
        context.relationship
      );
      processedText = this.applyFormalityLevel(processedText, handler, formalityLevel);
    }

    // Apply honorifics if applicable
    if (handler.honorifics && context.names) {
      processedText = this.applyHonorifics(processedText, handler.honorifics, context.names);
    }

    // Apply cultural notes
    processedText = this.applyCulturalNotes(processedText, handler.culturalNotes, context);

    return processedText;
  }

  determineFormalityLevel(formalityConfig, relationship) {
    for (const [relationshipType, level] of Object.entries(formalityConfig.contextRules)) {
      if (relationship.type === relationshipType) {
        return level;
      }
    }
    return formalityConfig.defaultLevel;
  }

  applyFormalityLevel(text, handler, level) {
    // This would apply formality-specific transformations
    // Implementation depends on the language and cultural context
    return text;
  }

  applyHonorifics(text, honorifics, names) {
    // Apply appropriate honorifics to names
    let processedText = text;

    for (const [name, info] of Object.entries(names)) {
      const honorific = this.selectHonorific(honorifics, info);
      if (honorific) {
        const regex = new RegExp(`\\b${name}\\b`, 'g');
        processedText = processedText.replace(regex, `${name}${honorific}`);
      }
    }

    return processedText;
  }

  selectHonorific(honorifics, nameInfo) {
    // Select appropriate honorific based on context
    if (nameInfo.age === 'elder') return honorifics['-sama'] || honorifics['-san'];
    if (nameInfo.profession === 'teacher') return honorifics['-sensei'];
    if (nameInfo.age === 'young' && nameInfo.gender === 'male') return honorifics['-kun'];
    if (nameInfo.age === 'young' && nameInfo.gender === 'female') return honorifics['-chan'];
    return honorifics['-san'];
  }

  applyCulturalNotes(text, culturalNotes, context) {
    // Apply cultural-specific adjustments
    let processedText = text;

    if (culturalNotes.directness === 'indirect') {
      processedText = this.makeMoreIndirect(processedText);
    }

    if (culturalNotes.emotionExpression === 'subtle') {
      processedText = this.makeEmotionsMoreSubtle(processedText);
    }

    return processedText;
  }

  makeMoreIndirect(text) {
    // Convert direct statements to more indirect forms
    const indirectReplacements = {
      'I want': 'I would like',
      'Do this': 'Could you please do this',
      'You should': 'It might be helpful to',
      'No': 'I\'m not sure that\'s possible'
    };

    let processedText = text;
    for (const [direct, indirect] of Object.entries(indirectReplacements)) {
      processedText = processedText.replace(new RegExp(direct, 'gi'), indirect);
    }

    return processedText;
  }

  makeEmotionsMoreSubtle(text) {
    // Reduce emotional intensity in expressions
    const emotionReplacements = {
      'very angry': 'concerned',
      'extremely happy': 'pleased',
      'terrible': 'unfortunate',
      'amazing': 'nice'
    };

    let processedText = text;
    for (const [intense, subtle] of Object.entries(emotionReplacements)) {
      processedText = processedText.replace(new RegExp(intense, 'gi'), subtle);
    }

    return processedText;
  }

  applyRTLFormatting(text) {
    // Apply right-to-left formatting if needed
    return text; // Placeholder for RTL formatting
  }

  preserveContext(text, sourceLanguage, targetLanguage, context) {
    // Preserve context-specific elements during translation
    let processedText = text;

    // Preserve character names
    if (context.characterNames) {
      processedText = this.preserveCharacterNames(processedText, context.characterNames);
    }

    // Preserve location names
    if (context.locationNames) {
      processedText = this.preserveLocationNames(processedText, context.locationNames);
    }

    // Preserve proper nouns
    processedText = this.preserveProperNouns(processedText);

    return processedText;
  }

  preserveCharacterNames(text, characterNames) {
    let processedText = text;

    characterNames.forEach(name => {
      const regex = new RegExp(`\\b${name}\\b`, 'gi');
      processedText = processedText.replace(regex, `[CHAR_NAME:${name}]`);
    });

    return processedText;
  }

  preserveLocationNames(text, locationNames) {
    let processedText = text;

    locationNames.forEach(name => {
      const regex = new RegExp(`\\b${name}\\b`, 'gi');
      processedText = processedText.replace(regex, `[LOC_NAME:${name}]`);
    });

    return processedText;
  }

  preserveProperNouns(text) {
    // Identify and preserve proper nouns (capitalized words not at sentence start)
    const properNounPattern = /\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g;
    const properNouns = text.match(properNounPattern) || [];

    let processedText = text;
    properNouns.forEach(noun => {
      if (!this.isCommonWord(noun)) {
        const regex = new RegExp(`\\b${noun}\\b`, 'g');
        processedText = processedText.replace(regex, `[PROPER_NOUN:${noun}]`);
      }
    });

    return processedText;
  }

  isCommonWord(word) {
    const commonWords = [
      'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'What', 'Who', 'Why', 'How',
      'And', 'But', 'Or', 'So', 'For', 'With', 'By', 'From', 'To', 'In', 'On', 'At', 'As'
    ];
    return commonWords.includes(word);
  }

  generateCacheKey(text, sourceLanguage, targetLanguage, context) {
    const keyData = {
      text: text.substring(0, 500), // Limit text length for cache key
      sourceLanguage,
      targetLanguage,
      contextHash: this.hashContext(context)
    };

    return require('crypto')
      .createHash('md5')
      .update(JSON.stringify(keyData))
      .digest('hex');
  }

  hashContext(context) {
    return require('crypto')
      .createHash('md5')
      .update(JSON.stringify(context))
      .digest('hex');
  }

  cacheTranslation(key, translation) {
    this.translationCache.set(key, {
      translation,
      timestamp: Date.now(),
      accessCount: 1
    });

    // Check cache size limit
    if (this.translationCache.size > this.options.cacheSize) {
      this.cleanupCache();
    }
  }

  cleanupCache() {
    const entries = Array.from(this.translationCache.entries());

    // Sort by access count and timestamp
    entries.sort((a, b) => {
      const scoreA = a[1].accessCount / (Date.now() - a[1].timestamp);
      const scoreB = b[1].accessCount / (Date.now() - b[1].timestamp);
      return scoreA - scoreB;
    });

    // Remove least valuable entries (bottom 25%)
    const toRemove = Math.floor(entries.length * 0.25);
    for (let i = 0; i < toRemove; i++) {
      this.translationCache.delete(entries[i][0]);
    }
  }

  startCacheCleanup() {
    setInterval(() => {
      const now = Date.now();
      const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days

      for (const [key, value] of this.translationCache) {
        if (now - value.timestamp > maxAge) {
          this.translationCache.delete(key);
        }
      }
    }, 24 * 60 * 60 * 1000); // Clean daily
  }

  // API Methods
  async translateConversation(conversation, targetLanguage, context = {}) {
    const translatedConversation = {
      ...conversation,
      messages: [],
      translatedAt: new Date().toISOString()
    };

    for (const message of conversation.messages) {
      const translatedMessage = {
        ...message,
        content: await this.translateText(
          message.content,
          targetLanguage,
          'auto',
          { ...context, messageType: message.type }
        ),
        originalContent: message.content
      };
      translatedConversation.messages.push(translatedMessage);
    }

    return translatedConversation;
  }

  getSupportedLanguages() {
    return Array.from(this.languageMappings.entries()).map(([code, lang]) => ({
      code,
      name: lang.name,
      region: lang.region,
      dndContext: lang.dndContext,
      direction: lang.direction
    }));
  }

  getFantasyLanguages() {
    return Array.from(this.fantasyLanguages.entries()).map(([code, lang]) => ({
      code,
      name: lang.name,
      script: lang.script,
      characteristics: lang.characteristics
    }));
  }

  getDNDTerminology() {
    return Object.fromEntries(this.dndTerminology);
  }

  getCacheStatistics() {
    return {
      ...this.cacheStats,
      cacheSize: this.translationCache.size,
      hitRate: this.cacheStats.hits / (this.cacheStats.hits + this.cacheStats.misses) || 0
    };
  }

  clearCache() {
    this.translationCache.clear();
    this.cacheStats = { hits: 0, misses: 0, translations: 0 };
    this.emit('cacheCleared', { timestamp: new Date().toISOString() });
  }

  addDNDTerminology(term, translations) {
    this.dndTerminology.set(term.toLowerCase(), translations);
  }

  addFantasyLanguage(code, languageData) {
    this.fantasyLanguages.set(code, languageData);
  }

  addCulturalContextHandler(region, handler) {
    this.culturalContextHandlers.set(region, handler);
  }
}

module.exports = MultiLanguageSupportSystem;