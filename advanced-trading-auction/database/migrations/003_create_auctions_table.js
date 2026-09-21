/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.up = function(knex) {
  return knex.schema.createTable('auctions', function(table) {
    table.uuid('id').primary().defaultTo(knex.raw('gen_random_uuid()'));
    table.uuid('seller_id').notNullable();
    table.uuid('item_id').notNullable();
    table.integer('quantity').notNullable().defaultTo(1);
    table.decimal('starting_price', 15, 2).notNullable();
    table.decimal('current_bid', 15, 2).notNullable();
    table.decimal('reserve_price', 15, 2); // Optional reserve price
    table.decimal('buyout_price', 15, 2); // Optional buyout price
    table.timestamp('start_time').notNullable().defaultTo(knex.fn.now());
    table.timestamp('end_time').notNullable();
    table.enum('status', ['active', 'sold', 'expired', 'cancelled']).defaultTo('active');
    table.string('region_id').notNullable().defaultTo('global');
    table.boolean('anonymous').defaultTo(false);
    table.boolean('auto_relist').defaultTo(false);
    table.decimal('min_bid_increment', 5, 4).defaultTo(0.05); // 5% default
    table.integer('bid_count').defaultTo(0);
    table.uuid('bidder_id'); // Current highest bidder
    table.text('notes'); // Seller notes
    table.timestamp('created_at').defaultTo(knex.fn.now());
    table.timestamp('updated_at').defaultTo(knex.fn.now());

    // Foreign keys
    table.foreign('seller_id').references('id').inTable('players').onDelete('CASCADE');
    table.foreign('item_id').references('id').inTable('items').onDelete('CASCADE');
    table.foreign('bidder_id').references('id').inTable('players').onDelete('SET NULL');

    // Indexes
    table.index(['seller_id']);
    table.index(['item_id']);
    table.index(['status']);
    table.index(['region_id']);
    table.index(['end_time']);
    table.index(['created_at']);
    table.index(['current_bid']);
  });
};

/**
 * @param { import("knex").Knex } knex
 * @returns { Promise<void> }
 */
exports.down = function(knex) {
  return knex.schema.dropTable('auctions');
};