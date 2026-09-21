/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.seed = async function(knex) {
  // Deletes ALL existing entries
  await knex('item_categories').del();

  // Inserts seed entries
  await knex('item_categories').insert([
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Weapons',
      description: 'Various weapons for combat',
      icon: 'sword',
      sort_order: 1,
      active: true,
      metadata: JSON.stringify({
        damage_types: ['physical', 'magical'],
        slot_types: ['main_hand', 'off_hand']
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Armor',
      description: 'Protective gear and clothing',
      icon: 'shield',
      sort_order: 2,
      active: true,
      metadata: JSON.stringify({
        armor_slots: ['head', 'chest', 'legs', 'feet', 'hands'],
        defense_types: ['physical', 'magical']
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Consumables',
      description: 'Potions, food, and other consumables',
      icon: 'potion',
      sort_order: 3,
      active: true,
      metadata: JSON.stringify({
        effect_types: ['healing', 'buff', 'debuff'],
        duration_types: ['instant', 'temporary', 'permanent']
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Materials',
      description: 'Raw materials for crafting',
      icon: 'ore',
      sort_order: 4,
      active: true,
      metadata: JSON.stringify({
        material_types: ['metal', 'wood', 'cloth', 'gem', 'herb'],
        quality_levels: ['common', 'rare', 'epic']
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Rare Items',
      description: 'Rare and valuable items',
      icon: 'diamond',
      sort_order: 5,
      active: true,
      metadata: JSON.stringify({
        item_types: ['artifact', 'relic', 'treasure'],
        binding_types: ['bind_on_pickup', 'bind_on_equip', 'tradeable']
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Crafting Recipes',
      description: 'Recipes and patterns for crafting',
      icon: 'scroll',
      sort_order: 6,
      active: true,
      metadata: JSON.stringify({
        professions: ['blacksmithing', 'alchemy', 'enchanting', 'tailoring'],
        difficulty_levels: ['apprentice', 'journeyman', 'master', 'grandmaster']
      })
    },
    {
      id: knex.raw('gen_random_uuid()'),
      name: 'Mounts & Pets',
      description: 'Mounts and companion pets',
      icon: 'horse',
      sort_order: 7,
      active: true,
      metadata: JSON.stringify({
        types: ['ground_mount', 'flying_mount', 'water_mount', 'companion_pet'],
        rarity_levels: ['common', 'rare', 'epic', 'legendary']
      })
    }
  ]);
};