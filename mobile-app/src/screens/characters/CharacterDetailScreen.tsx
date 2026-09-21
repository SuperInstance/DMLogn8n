import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Share,
  Animated,
  PanGestureHandler,
  Dimensions,
} from 'react-native';
import {
  Card,
  Button,
  Icon,
  Avatar,
  Chip,
  Divider,
  Badge,
  LinearProgress,
} from '@rneui/themed';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { updateCharacter, updateCharacterHealth, addCharacterMemory } from '../../store/slices/characterSlice';
import { Character } from '../../types';
import { colors, spacing, typography } from '../../theme/theme';
import { HapticsService } from '../../services/hapticsService';
import { DiceService } from '../../services/diceService';
import { VoiceService } from '../../services/voiceService';

interface CharacterDetailScreenProps {
  route: {
    params: {
      characterId: string;
    };
  };
}

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

const CharacterDetailScreen: React.FC<CharacterDetailScreenProps> = ({ route }) => {
  const { characterId } = route.params;
  const dispatch = useAppDispatch();
  const { activeCharacter, isLoading } = useAppSelector(state => state.character);

  // Local state
  const [activeTab, setActiveTab] = useState<'stats' | 'abilities' | 'equipment' | 'spells' | 'memories'>('stats');
  const [isEditing, setIsEditing] = useState(false);
  const [healthAnimation] = useState(new Animated.Value(0));

  // Swipe gesture handling
  const panGestureRef = useRef<Animated.Value>(new Animated.Value(0)).current;

  useEffect(() => {
    // Trigger health animation on component mount
    Animated.timing(healthAnimation, {
      toValue: 1,
      duration: 1000,
      useNativeDriver: false,
    }).start();
  }, []);

  // Handle swipe gestures for tab navigation
  const handleSwipe = (event: any) => {
    const { translationX } = event.nativeEvent;
    const threshold = 50;

    if (translationX > threshold) {
      // Swipe right - previous tab
      const tabs: Array<'stats' | 'abilities' | 'equipment' | 'spells' | 'memories'> =
        ['stats', 'abilities', 'equipment', 'spells', 'memories'];
      const currentIndex = tabs.indexOf(activeTab);
      if (currentIndex > 0) {
        setActiveTab(tabs[currentIndex - 1]);
        HapticsService.impactLight();
      }
    } else if (translationX < -threshold) {
      // Swipe left - next tab
      const tabs: Array<'stats' | 'abilities' | 'equipment' | 'spells' | 'memories'> =
        ['stats', 'abilities', 'equipment', 'spells', 'memories'];
      const currentIndex = tabs.indexOf(activeTab);
      if (currentIndex < tabs.length - 1) {
        setActiveTab(tabs[currentIndex + 1]);
        HapticsService.impactLight();
      }
    }

    Animated.event([null, { translateX: panGestureRef }], { useNativeDriver: false })(event);
  };

  const handleHealthChange = async (type: 'damage' | 'heal' | 'temp', amount: number) => {
    if (!activeCharacter) return;

    HapticsService.impactMedium();

    let newHealth = { ...activeCharacter.health };

    switch (type) {
      case 'damage':
        const totalDamage = amount - (newHealth.temp || 0);
        newHealth.temp = Math.max(0, (newHealth.temp || 0) - amount);
        newHealth.current = Math.max(0, newHealth.current - Math.max(0, totalDamage));
        break;
      case 'heal':
        newHealth.current = Math.min(newHealth.max, newHealth.current + amount);
        break;
      case 'temp':
        newHealth.temp = (newHealth.temp || 0) + amount;
        break;
    }

    await dispatch(updateCharacterHealth({
      characterId: activeCharacter.id,
      health: newHealth,
    }));

    // Animate health bar
    Animated.sequence([
      Animated.timing(healthAnimation, { toValue: 0.8, duration: 100, useNativeDriver: false }),
      Animated.timing(healthAnimation, { toValue: 1, duration: 900, useNativeDriver: false }),
    ]).start();
  };

  const handleRollSkillCheck = async (skillName: string, modifier: number) => {
    if (!activeCharacter) return;

    HapticsService.impactHeavy();

    const roll = await DiceService.rollD20();
    const total = roll + modifier;

    // Voice feedback
    await VoiceService.speak(`${skillName} check: ${roll} plus ${modifier} equals ${total}`);

    Alert.alert(
      `${skillName} Check`,
      `You rolled a ${roll} + ${modifier} = ${total}`,
      [
        { text: 'OK', onPress: () => HapticsService.notificationSuccess() },
        { text: 'Reroll', onPress: () => handleRollSkillCheck(skillName, modifier) },
      ]
    );

    // Add to memories
    await dispatch(addCharacterMemory({
      characterId: activeCharacter.id,
      memory: {
        title: `Skill Check: ${skillName}`,
        content: `Rolled ${roll} + ${modifier} = ${total}`,
        importance: 2,
        tags: ['skill-check', skillName.toLowerCase()],
        isPrivate: true,
      },
    }));
  };

  const shareCharacter = async () => {
    if (!activeCharacter) return;

    try {
      const characterText = `
${activeCharacter.name} - Level ${activeCharacter.level} ${activeCharacter.race} ${activeCharacter.class}

HP: ${activeCharacter.health.current}/${activeCharacter.health.max}
AC: ${activeCharacter.stats.armorClass || 10}
Proficiency Bonus: +${activeCharacter.proficiencyBonus}

Stats:
STR: ${activeCharacter.stats.strength} (${activeCharacter.stats.strengthMod >= 0 ? '+' : ''}${activeCharacter.stats.strengthMod})
DEX: ${activeCharacter.stats.dexterity} (${activeCharacter.stats.dexterityMod >= 0 ? '+' : ''}${activeCharacter.stats.dexterityMod})
CON: ${activeCharacter.stats.constitution} (${activeCharacter.stats.constitutionMod >= 0 ? '+' : ''}${activeCharacter.stats.constitutionMod})
INT: ${activeCharacter.stats.intelligence} (${activeCharacter.stats.intelligenceMod >= 0 ? '+' : ''}${activeCharacter.stats.intelligenceMod})
WIS: ${activeCharacter.stats.wisdom} (${activeCharacter.stats.wisdomMod >= 0 ? '+' : ''}${activeCharacter.stats.wisdomMod})
CHA: ${activeCharacter.stats.charisma} (${activeCharacter.stats.charismaMod >= 0 ? '+' : ''}${activeCharacter.stats.charismaMod})
      `.trim();

      await Share.share({
        message: characterText,
        title: `${activeCharacter.name} - D&D Character Sheet`,
      });
    } catch (error) {
      Alert.alert('Error', 'Failed to share character');
    }
  };

  const renderHealthSection = () => {
    if (!activeCharacter) return null;

    const healthPercentage = (activeCharacter.health.current / activeCharacter.health.max) * 100;
    const tempHealth = activeCharacter.health.temp || 0;

    return (
      <Card containerStyle={styles.card}>
        <View style={styles.healthHeader}>
          <Text style={styles.sectionTitle}>Health</Text>
          <View style={styles.healthActions}>
            <TouchableOpacity
              style={styles.healthButton}
              onPress={() => handleHealthChange('damage', 1)}
            >
              <Icon name="remove" size={20} color={colors.error} />
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.healthButton}
              onPress={() => handleHealthChange('heal', 1)}
            >
              <Icon name="add" size={20} color={colors.success} />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.healthDisplay}>
          <View>
            <Text style={styles.healthText}>
              {activeCharacter.health.current}/{activeCharacter.health.max}
            </Text>
            {tempHealth > 0 && (
              <Text style={styles.tempHealthText}>
                +{tempHealth} Temp
              </Text>
            )}
          </View>
          <Animated.View style={[styles.healthBarContainer, { opacity: healthAnimation }]}>
            <LinearProgress
              value={healthPercentage}
              color={healthPercentage > 50 ? colors.success : healthPercentage > 25 ? colors.warning : colors.error}
              style={styles.healthBar}
              variant="determinate"
            />
          </Animated.View>
        </View>

        <View style={styles.quickHealthButtons}>
          <TouchableOpacity
            style={[styles.quickHealthBtn, { backgroundColor: colors.error }]}
            onPress={() => handleHealthChange('damage', 5)}
          >
            <Text style={styles.quickHealthText}>-5</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.quickHealthBtn, { backgroundColor: colors.success }]}
            onPress={() => handleHealthChange('heal', 5)}
          >
            <Text style={styles.quickHealthText}>+5</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.quickHealthBtn, { backgroundColor: colors.info }]}
            onPress={() => handleHealthChange('temp', 5)}
          >
            <Text style={styles.quickHealthText}>+5 Temp</Text>
          </TouchableOpacity>
        </View>
      </Card>
    );
  };

  const renderStatsSection = () => {
    if (!activeCharacter) return null;

    const stats = [
      { name: 'Strength', value: activeCharacter.stats.strength, mod: activeCharacter.stats.strengthMod, color: colors.class.fighter },
      { name: 'Dexterity', value: activeCharacter.stats.dexterity, mod: activeCharacter.stats.dexterityMod, color: colors.class.rogue },
      { name: 'Constitution', value: activeCharacter.stats.constitution, mod: activeCharacter.stats.constitutionMod, color: colors.class.barbarian },
      { name: 'Intelligence', value: activeCharacter.stats.intelligence, mod: activeCharacter.stats.intelligenceMod, color: colors.class.wizard },
      { name: 'Wisdom', value: activeCharacter.stats.wisdom, mod: activeCharacter.stats.wisdomMod, color: colors.class.druid },
      { name: 'Charisma', value: activeCharacter.stats.charisma, mod: activeCharacter.stats.charismaMod, color: colors.class.bard },
    ];

    return (
      <View style={styles.statsGrid}>
        {stats.map((stat) => (
          <TouchableOpacity
            key={stat.name}
            style={[styles.statCard, { borderColor: stat.color }]}
            onPress={() => handleRollSkillCheck(stat.name, stat.mod)}
            activeOpacity={0.7}
          >
            <Text style={styles.statName}>{stat.name.substring(0, 3)}</Text>
            <Text style={styles.statValue}>{stat.value}</Text>
            <Text style={[styles.statMod, { color: stat.mod >= 0 ? colors.success : colors.error }]}>
              {stat.mod >= 0 ? '+' : ''}{stat.mod}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const renderSkillsSection = () => {
    if (!activeCharacter) return null;

    const skills = activeCharacter.skills.filter(skill => skill.proficiency || skill.expertise);

    return (
      <ScrollView style={styles.skillsContainer}>
        {skills.map((skill) => (
          <TouchableOpacity
            key={skill.name}
            style={styles.skillItem}
            onPress={() => handleRollSkillCheck(skill.name, skill.mod)}
            activeOpacity={0.7}
          >
            <View style={styles.skillInfo}>
              <Text style={styles.skillName}>{skill.name}</Text>
              <View style={styles.skillBadges}>
                {skill.expertise && <Badge value="Expertise" status="primary" />}
                {skill.proficiency && !skill.expertise && <Badge value="Proficient" status="success" />}
              </View>
            </View>
            <Text style={styles.skillMod}>
              {skill.mod >= 0 ? '+' : ''}{skill.mod}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'stats':
        return (
          <View>
            {renderHealthSection()}
            {renderStatsSection()}
          </View>
        );
      case 'abilities':
        return (
          <ScrollView style={styles.tabContent}>
            {activeCharacter?.features.map((feature) => (
              <Card key={feature.id} containerStyle={styles.card}>
                <Text style={styles.featureName}>{feature.name}</Text>
                <Text style={styles.featureDescription}>{feature.description}</Text>
                {feature.uses && (
                  <View style={styles.usesContainer}>
                    <Text style={styles.usesText}>
                      Uses: {feature.uses.current}/{feature.uses.max}
                    </Text>
                    <LinearProgress
                      value={(feature.uses.current / feature.uses.max) * 100}
                      color={colors.primary}
                      style={styles.usesBar}
                    />
                  </View>
                )}
              </Card>
            ))}
          </ScrollView>
        );
      case 'equipment':
        return (
          <ScrollView style={styles.tabContent}>
            {activeCharacter?.equipment.map((item) => (
              <Card key={item.id} containerStyle={styles.card}>
                <View style={styles.equipmentItem}>
                  <View style={styles.equipmentInfo}>
                    <Text style={styles.equipmentName}>{item.name}</Text>
                    <Text style={styles.equipmentType}>{item.type}</Text>
                    <Text style={styles.equipmentDescription}>{item.description}</Text>
                  </View>
                  <View style={styles.equipmentStatus}>
                    <Chip
                      title={item.equipped ? 'Equipped' : 'In Bag'}
                      type={item.equipped ? 'solid' : 'outline'}
                      color={item.equipped ? colors.success : colors.textSecondary}
                      size="sm"
                    />
                    {item.attuned && (
                      <Chip
                        title="Attuned"
                        type="solid"
                        color={colors.primary}
                        size="sm"
                        containerStyle={{ marginTop: 4 }}
                      />
                    )}
                  </View>
                </View>
              </Card>
            ))}
          </ScrollView>
        );
      case 'spells':
        return (
          <ScrollView style={styles.tabContent}>
            {activeCharacter?.spells.map((spell) => (
              <TouchableOpacity
                key={spell.id}
                style={styles.spellItem}
                activeOpacity={0.7}
              >
                <View style={styles.spellHeader}>
                  <Text style={styles.spellName}>{spell.name}</Text>
                  <View style={styles.spellMeta}>
                    <Chip title={`Level ${spell.level}`} size="sm" type="outline" />
                    {spell.concentration && (
                      <Chip title="Concentration" size="sm" type="outline" />
                    )}
                  </View>
                </View>
                <Text style={styles.spellDescription}>{spell.description}</Text>
                <View style={styles.spellDetails}>
                  <Text style={styles.spellDetail}>Casting Time: {spell.castingTime}</Text>
                  <Text style={styles.spellDetail}>Range: {spell.range}</Text>
                  <Text style={styles.spellDetail}>Duration: {spell.duration}</Text>
                </View>
              </TouchableOpacity>
            ))}
          </ScrollView>
        );
      case 'memories':
        return (
          <ScrollView style={styles.tabContent}>
            {activeCharacter?.memories.map((memory) => (
              <Card key={memory.id} containerStyle={styles.card}>
                <Text style={styles.memoryTitle}>{memory.title}</Text>
                <Text style={styles.memoryContent}>{memory.content}</Text>
                <View style={styles.memoryFooter}>
                  <Text style={styles.memoryDate}>
                    {new Date(memory.createdAt).toLocaleDateString()}
                  </Text>
                  <View style={styles.memoryTags}>
                    {memory.tags.slice(0, 3).map((tag) => (
                      <Chip key={tag} title={tag} size="sm" type="outline" />
                    ))}
                  </View>
                </View>
              </Card>
            ))}
          </ScrollView>
        );
      default:
        return null;
    }
  };

  if (!activeCharacter) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.loadingText}>Loading character...</Text>
      </View>
    );
  }

  return (
    <PanGestureHandler onGestureEvent={handleSwipe}>
      <Animated.View style={[styles.container, { transform: [{ translateX: panGestureRef }] }]}>
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity style={styles.avatarContainer}>
            <Avatar
              size="large"
              rounded
              source={{ uri: activeCharacter.portrait }}
              title={activeCharacter.name.substring(0, 2).toUpperCase()}
              containerStyle={styles.avatar}
            />
            <View style={[styles.classBadge, { backgroundColor: colors.class[activeCharacter.class.toLowerCase()] || colors.primary }]}>
              <Text style={styles.levelText}>Lvl {activeCharacter.level}</Text>
            </View>
          </TouchableOpacity>

          <View style={styles.characterInfo}>
            <Text style={styles.characterName}>{activeCharacter.name}</Text>
            <Text style={styles.characterClass}>
              {activeCharacter.race} {activeCharacter.class}
              {activeCharacter.subclass && ` (${activeCharacter.subclass})`}
            </Text>
            <View style={styles.characterMeta}>
              <Text style={styles.proficiencyBonus}>
                Proficiency: +{activeCharacter.proficiencyBonus}
              </Text>
              <Text style={styles.experienceText}>
                XP: {activeCharacter.experience}
              </Text>
            </View>
          </View>

          <TouchableOpacity style={styles.shareButton} onPress={shareCharacter}>
            <Icon name="share" size={24} color={colors.primary} />
          </TouchableOpacity>
        </View>

        {/* Tab Navigation */}
        <View style={styles.tabBar}>
          {[
            { key: 'stats', label: 'Stats', icon: 'assessment' },
            { key: 'abilities', label: 'Features', icon: 'stars' },
            { key: 'equipment', label: 'Equipment', icon: 'backpack' },
            { key: 'spells', label: 'Spells', icon: 'auto-stories' },
            { key: 'memories', label: 'Memories', icon: 'psychology' },
          ].map((tab) => (
            <TouchableOpacity
              key={tab.key}
              style={[styles.tab, activeTab === tab.key && styles.activeTab]}
              onPress={() => {
                setActiveTab(tab.key as any);
                HapticsService.selectionChanged();
              }}
            >
              <Icon
                name={tab.icon}
                size={20}
                color={activeTab === tab.key ? colors.primary : colors.textSecondary}
              />
              <Text style={[
                styles.tabLabel,
                activeTab === tab.key && styles.activeTabLabel
              ]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Tab Content */}
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {renderTabContent()}
        </ScrollView>

        {/* Quick Action Buttons */}
        <View style={styles.quickActions}>
          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={() => setIsEditing(!isEditing)}
          >
            <Icon name="edit" size={20} color={colors.text} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={() => handleRollSkillCheck('Perception', activeCharacter.skills.find(s => s.name === 'Perception')?.mod || 0)}
          >
            <Icon name="visibility" size={20} color={colors.text} />
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.quickActionButton}
            onPress={() => handleRollSkillCheck('Initiative', activeCharacter.stats.dexterityMod)}
          >
            <Icon name="flash-on" size={20} color={colors.text} />
          </TouchableOpacity>
        </View>
      </Animated.View>
    </PanGestureHandler>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  loadingText: {
    color: colors.text,
    fontSize: 16,
    fontFamily: 'Lato-Regular',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.lg,
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.primary + '30',
  },
  avatarContainer: {
    position: 'relative',
  },
  avatar: {
    borderWidth: 3,
    borderColor: colors.primary,
  },
  classBadge: {
    position: 'absolute',
    bottom: -5,
    right: -5,
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  levelText: {
    color: colors.text,
    fontSize: 10,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  characterInfo: {
    flex: 1,
    marginLeft: spacing.md,
  },
  characterName: {
    color: colors.text,
    fontSize: 24,
    fontWeight: 'bold',
    fontFamily: 'Cinzel-Regular',
  },
  characterClass: {
    color: colors.textSecondary,
    fontSize: 16,
    fontFamily: 'Lato-Regular',
    marginTop: 2,
  },
  characterMeta: {
    flexDirection: 'row',
    marginTop: 4,
  },
  proficiencyBonus: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
    marginRight: spacing.md,
  },
  experienceText: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
  },
  shareButton: {
    padding: spacing.sm,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: colors.primary + '30',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: spacing.sm,
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: colors.primary,
  },
  tabLabel: {
    color: colors.textSecondary,
    fontSize: 10,
    fontFamily: 'Lato-Regular',
    marginTop: 2,
  },
  activeTabLabel: {
    color: colors.primary,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
  },
  tabContent: {
    padding: spacing.md,
  },
  card: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primary + '30',
    borderRadius: 12,
    marginBottom: spacing.md,
  },
  healthHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'Cinzel-Regular',
  },
  healthActions: {
    flexDirection: 'row',
  },
  healthButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.primary + '50',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: spacing.sm,
  },
  healthDisplay: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  healthText: {
    color: colors.text,
    fontSize: 24,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  tempHealthText: {
    color: colors.info,
    fontSize: 14,
    fontFamily: 'Lato-Regular',
  },
  healthBarContainer: {
    flex: 1,
    marginLeft: spacing.md,
  },
  healthBar: {
    height: 8,
    borderRadius: 4,
  },
  quickHealthButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  quickHealthBtn: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  quickHealthText: {
    color: colors.text,
    fontSize: 12,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    padding: spacing.md,
  },
  statCard: {
    width: '30%',
    backgroundColor: colors.surface,
    borderWidth: 2,
    borderRadius: 12,
    padding: spacing.sm,
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  statName: {
    color: colors.text,
    fontSize: 12,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    textTransform: 'uppercase',
  },
  statValue: {
    color: colors.text,
    fontSize: 20,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  statMod: {
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  skillsContainer: {
    padding: spacing.md,
  },
  skillItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: 8,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.primary + '20',
  },
  skillInfo: {
    flex: 1,
  },
  skillName: {
    color: colors.text,
    fontSize: 16,
    fontFamily: 'Lato-Regular',
  },
  skillBadges: {
    flexDirection: 'row',
    marginTop: 4,
  },
  skillMod: {
    color: colors.primary,
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  featureName: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    marginBottom: spacing.sm,
  },
  featureDescription: {
    color: colors.textSecondary,
    fontSize: 14,
    fontFamily: 'Lato-Regular',
    lineHeight: 20,
  },
  usesContainer: {
    marginTop: spacing.sm,
  },
  usesText: {
    color: colors.text,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
    marginBottom: 4,
  },
  usesBar: {
    height: 4,
    borderRadius: 2,
  },
  equipmentItem: {
    flexDirection: 'row',
  },
  equipmentInfo: {
    flex: 1,
  },
  equipmentName: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
  },
  equipmentType: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
    marginTop: 2,
  },
  equipmentDescription: {
    color: colors.textSecondary,
    fontSize: 14,
    fontFamily: 'Lato-Regular',
    marginTop: 4,
  },
  equipmentStatus: {
    alignItems: 'flex-end',
  },
  spellItem: {
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: 8,
    marginBottom: spacing.sm,
    borderWidth: 1,
    borderColor: colors.primary + '20',
  },
  spellHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  spellName: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    flex: 1,
  },
  spellMeta: {
    flexDirection: 'row',
  },
  spellDescription: {
    color: colors.textSecondary,
    fontSize: 14,
    fontFamily: 'Lato-Regular',
    lineHeight: 20,
    marginBottom: spacing.sm,
  },
  spellDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  spellDetail: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
    marginRight: spacing.md,
    marginBottom: 4,
  },
  memoryTitle: {
    color: colors.text,
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'Lato-Bold',
    marginBottom: spacing.sm,
  },
  memoryContent: {
    color: colors.textSecondary,
    fontSize: 14,
    fontFamily: 'Lato-Regular',
    lineHeight: 20,
    marginBottom: spacing.sm,
  },
  memoryFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  memoryDate: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: 'Lato-Regular',
  },
  memoryTags: {
    flexDirection: 'row',
  },
  quickActions: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    flexDirection: 'column',
  },
  quickActionButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
});

export default CharacterDetailScreen;