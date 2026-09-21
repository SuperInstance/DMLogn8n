/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function(knex) {
  return knex.schema.createTable('items', function(table) {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.string('name').notNullable();
    table.text('description');
    table.string('icon');
    table.string('category_id').notNullable();
    table.enum('rarity', ['common', 'uncommon', 'rare', 'epic', 'legendary']).defaultTo('common');
    table.decimal('base_price', 15, 2).notNullable().defaultTo(100);
    table.integer('max_stack').defaultTo(1);
    table.boolean('tradeable').defaultTo(true);
    table.boolean('auctionable').defaultTo(true);
    table.json('properties'); // Additional item properties
    table.json('requirements'); // Level/class requirements
    table.timestamp('created_at').defaultTo(knex.fn.now());
    table.timestamp('updated_at').defaultTo(knex.fn.now());

    // Indexes
    table.index(['category_id']);
    table.index(['rarity']);
    table.index(['tradeable']);
    table.index(['auctionable']);
  });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function(knex) {
  return knex.schema.dropTable('items');
};