/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function(knex) {
  return knex.schema.createTable('market_listings', function(table) {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.uuid('seller_id').notNullable();
    table.uuid('item_id').notNullable();
    table.integer('quantity').notNullable().defaultTo(1);
    table.decimal('price', 15, 2).notNullable();
    table.string('region_id').notNullable().defaultTo('global');
    table.enum('listing_type', ['fixed', 'negotiable']).defaultTo('fixed');
    table.decimal('minimum_offer', 15, 2); // For negotiable listings
    table.decimal('auto_accept_price', 15, 2); // Auto-accept offers at this price
    table.text('description');
    table.json('tags'); // Searchable tags
    table.enum('status', ['active', 'sold', 'expired', 'cancelled']).defaultTo('active');
    table.integer('views').defaultTo(0);
    table.timestamp('created_at').defaultTo(knex.fn.now());
    table.timestamp('updated_at').defaultTo(knex.fn.now());
    table.timestamp('expires_at').notNullable();

    // Foreign keys
    table.foreign('seller_id').references('id').inTable('players').onDelete('CASCADE');
    table.foreign('item_id').references('id').inTable('items').onDelete('CASCADE');

    // Indexes
    table.index(['seller_id']);
    table.index(['item_id']);
    table.index(['status']);
    table.index(['region_id']);
    table.index(['listing_type']);
    table.index(['price']);
    table.index(['expires_at']);
    table.index(['created_at']);
    table.index(['views']);
  });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function(knex) {
  return knex.schema.dropTable('market_listings');
};