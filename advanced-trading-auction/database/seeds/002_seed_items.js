/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.seed = async function(knex) {
  // Deletes ALL existing entries
  await knex('items').del();

  // Get category IDs
  const categories = await knex('item_categories').select('id', 'name');
  const categoryIdMap = {};
  categories.forEach(cat => {
    categoryIdMap[cat.name] = cat.id;
  });

  // Inserts seed entries
  const items = [
    // Weapons
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Iron Sword',
      description: 'A sturdy iron sword suitable for beginners.',
      category_id: categoryIdMap['Weapons'],
      rarity: 'common',
      base_price: 150,
      max_stack: 1,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        damage: 15,
        speed: 2.5,
        durability: 100,
        level_requirement: 5
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Enchanted Staff',
      description: 'A wooden staff imbued with magical energy.',
      category_id: categoryIdMap['Weapons'],
      rarity: 'rare',
      base_price: 1200,
      max_stack: 1,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        spell_power: 35,
        mana_bonus: 50,
        durability: 80,
        level_requirement: 20
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Legendary Blade of Shadows',
      description: 'A blade forged in darkness, said to consume the souls of its enemies.',
      category_id: categoryIdMap['Weapons'],
      rarity: 'legendary',
      base_price: 15000,
      max_stack: 1,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        damage: 180,
        crit_chance: 0.25,
        shadow_damage: 50,
        durability: 200,
        level_requirement: 60
      })
    },

    // Armor
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Leather Armor',
      description: 'Basic leather armor providing modest protection.',
      category_id: categoryIdMap['Armor'],
      rarity: 'common',
      base_price: 80,
      max_stack: 1,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        defense: 10,
        dodge_bonus: 5,
        durability: 60,
        level_requirement: 3
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Plate Mail of Fortitude',
      description: 'Heavy plate armor that offers excellent protection.',
      category_id: categoryIdMap['Armor'],
      rarity: 'epic',
      base_price: 3500,
      max_stack: 1,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        defense: 85,
        stamina_bonus: 100,
        durability: 150,
        level_requirement: 45
      })
    },

    // Consumables
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Health Potion',
      description: 'Restores 50 health points when consumed.',
      category_id: categoryIdMap['Consumables'],
      rarity: 'common',
      base_price: 25,
      max_stack: 20,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        healing_amount: 50,
        cooldown: 30,
        duration: 'instant'
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Mana Elixir',
      description: 'Restores 100 mana points over 30 seconds.',
      category_id: categoryIdMap['Consumables'],
      rarity: 'uncommon',
      base_price: 45,
      max_stack: 10,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        mana_restoration: 100,
        duration: 30,
        cooldown: 60
      })
    },

    // Materials
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Iron Ore',
      description: 'Raw iron ore used in blacksmithing.',
      category_id: categoryIdMap['Materials'],
      rarity: 'common',
      base_price: 15,
      max_stack: 100,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        material_type: 'metal',
        quality: 'standard',
        crafting_skill: 'blacksmithing'
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Dragon Scale',
      description: 'A rare scale from a mighty dragon.',
      category_id: categoryIdMap['Materials'],
      rarity: 'epic',
      base_price: 2500,
      max_stack: 10,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        material_type: 'scale',
        quality: 'exceptional',
        crafting_skill: 'armorsmithing',
        fire_resistance: 50
      })
    },

    // Rare Items
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Ancient Artifact',
      description: 'A mysterious artifact of unknown origin and power.',
      category_id: categoryIdMap['Rare Items'],
      rarity: 'legendary',
      base_price: 25000,
      max_stack: 1,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        item_type: 'artifact',
        binding_type: 'bind_on_pickup',
        mysterious_powers: true,
        lore_value: 'extreme'
      })
    },

    // Crafting Recipes
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Master Swordsmithing Pattern',
      description: 'Advanced pattern for crafting master-quality swords.',
      category_id: categoryIdMap['Crafting Recipes'],
      rarity: 'rare',
      base_price: 800,
      max_stack: 1,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        profession: 'blacksmithing',
        difficulty: 'master',
        skill_requirement: 250
      })
    },

    // Mounts & Pets
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Swift Brown Horse',
      description: 'A reliable mount for fast travel.',
      category_id: categoryIdMap['Mounts & Pets'],
      rarity: 'uncommon',
      base_price: 5000,
      max_stack: 1,
      tradeable: true,
      auctionable: true,
      properties: JSON.stringify({
        type: 'ground_mount',
        speed_bonus: 60,
        stamina: 100
      })
    }
  ];

  await knex('items').insert(items);
};