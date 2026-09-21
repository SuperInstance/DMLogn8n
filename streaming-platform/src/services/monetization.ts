import { EventEmitter } from 'events';
import Stripe from 'stripe';
import paypal from 'paypal-rest-sdk';
import axios from 'axios';
import { DatabaseService, IDonation } from './database';
import { logger } from '@/utils/logger';

interface DonationData {
  platform: string;
  amount: number;
  currency: string;
  donorName: string;
  message?: string;
  email?: string;
  isAnonymous: boolean;
  sessionId?: string;
  rewardTier?: string;
}

interface SubscriptionTier {
  id: string;
  name: string;
  price: number;
  currency: string;
  billingInterval: 'month' | 'year';
  benefits: string[];
  customRewards: string[];
  isActive: boolean;
  maxSubscribers?: number;
  currentSubscribers: number;
}

interface MerchandiseItem {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  category: string;
  imageUrl?: string;
  inventory: {
    total: number;
    available: number;
    reserved: number;
  };
  variants: {
    size?: string;
    color?: string;
    style?: string;
  }[];
  isActive: boolean;
  isDigital: boolean;
  digitalFileUrl?: string;
}

interface SponsorshipTier {
  id: string;
  name: string;
  price: number;
  currency: string;
  duration: number; // in days
  benefits: string[];
  logoPlacement?: {
    position: string;
    duration: number;
  };
  mentionsPerStream: number;
  customIntegration: boolean;
  isActive: boolean;
}

interface RevenueBreakdown {
  period: {
    start: Date;
    end: Date;
  };
  donations: {
    amount: number;
    count: number;
    byPlatform: { [platform: string]: number };
  };
  subscriptions: {
    amount: number;
    count: number;
    byTier: { [tier: string]: number };
    churnRate: number;
  };
  merchandise: {
    amount: number;
    count: number;
    byItem: { [item: string]: number };
  };
  sponsorships: {
    amount: number;
    count: number;
    byTier: { [tier: string]: number };
  };
  total: number;
  fees: number;
  net: number;
}

export class MonetizationService extends EventEmitter {
  private static instance: MonetizationService;
  private stripe: Stripe;
  private paypal: any;
  private patreon: any;
  private subscriptionTiers: Map<string, SubscriptionTier> = new Map();
  private merchandiseItems: Map<string, MerchandiseItem> = new Map();
  private sponsorshipTiers: Map<string, SponsorshipTier> = new Map();
  private isInitialized = false;

  private constructor() {
    super();
    this.stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
      apiVersion: '2023-10-16'
    });

    // Configure PayPal
    paypal.configure({
      mode: process.env.PAYPAL_MODE || 'sandbox',
      client_id: process.env.PAYPAL_CLIENT_ID!,
      client_secret: process.env.PAYPAL_CLIENT_SECRET!
    });
  }

  public static getInstance(): MonetizationService {
    if (!MonetizationService.instance) {
      MonetizationService.instance = new MonetizationService();
    }
    return MonetizationService.instance;
  }

  public static async initialize(): Promise<void> {
    const service = MonetizationService.instance;

    try {
      // Initialize default subscription tiers
      await service.initializeSubscriptionTiers();

      // Initialize default merchandise
      await service.initializeMerchandise();

      // Initialize sponsorship tiers
      await service.initializeSponsorshipTiers();

      // Set up webhooks
      service.setupWebhooks();

      service.isInitialized = true;
      logger.info('Monetization Service initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Monetization Service:', error);
      throw error;
    }
  }

  private async initializeSubscriptionTiers(): Promise<void> {
    const defaultTiers: SubscriptionTier[] = [
      {
        id: 'bronze',
        name: 'Bronze Adventurer',
        price: 4.99,
        currency: 'USD',
        billingInterval: 'month',
        benefits: [
          'Custom Discord role',
          'Access to subscriber-only Discord channels',
          'Vote on campaign decisions',
          'Monthly supporter shoutout'
        ],
        customRewards: [],
        isActive: true,
        currentSubscribers: 0
      },
      {
        id: 'silver',
        name: 'Silver Hero',
        price: 9.99,
        currency: 'USD',
        billingInterval: 'month',
        benefits: [
          'All Bronze tier benefits',
          'Exclusive Discord voice chat access',
          'Character name in credits',
          'Monthly Q&A session access',
          'Custom emoji access'
        ],
        customRewards: ['Character cameo in session'],
        isActive: true,
        currentSubscribers: 0
      },
      {
        id: 'gold',
        name: 'Gold Legend',
        price: 24.99,
        currency: 'USD',
        billingInterval: 'month',
        benefits: [
          'All Silver tier benefits',
          'One-on-one DM consultation per month',
          'Custom character portrait',
          'Early access to VODs',
          'Signed merchandise'
        ],
        customRewards: ['NPC design collaboration', 'Loot drop design'],
        isActive: true,
        maxSubscribers: 10,
        currentSubscribers: 0
      }
    ];

    defaultTiers.forEach(tier => {
      this.subscriptionTiers.set(tier.id, tier);
    });
  }

  private async initializeMerchandise(): Promise<void> {
    const defaultMerch: MerchandiseItem[] = [
      {
        id: 'tshirt-basic',
        name: 'D&D Campaign T-Shirt',
        description: 'Premium quality t-shirt with custom campaign artwork',
        price: 24.99,
        currency: 'USD',
        category: 'Apparel',
        inventory: {
          total: 100,
          available: 100,
          reserved: 0
        },
        variants: [
          { size: 'S', color: 'Black' },
          { size: 'M', color: 'Black' },
          { size: 'L', color: 'Black' },
          { size: 'XL', color: 'Black' },
          { size: '2XL', color: 'Black' }
        ],
        isActive: true,
        isDigital: false
      },
      {
        id: 'dice-set',
        name: 'Custom D&D Dice Set',
        description: 'Professional quality dice set with custom campaign symbols',
        price: 34.99,
        currency: 'USD',
        category: 'Gaming',
        inventory: {
          total: 50,
          available: 50,
          reserved: 0
        },
        variants: [
          { color: 'Blue' },
          { color: 'Red' },
          { color: 'Green' },
          { color: 'Purple' }
        ],
        isActive: true,
        isDigital: false
      },
      {
        id: 'campaign-guide',
        name: 'Digital Campaign Guide',
        description: 'Complete digital guide to the current campaign world',
        price: 9.99,
        currency: 'USD',
        category: 'Digital',
        inventory: {
          total: -1, // Unlimited digital
          available: -1,
          reserved: 0
        },
        variants: [],
        isActive: true,
        isDigital: true,
        digitalFileUrl: '/digital/campaign-guide.pdf'
      }
    ];

    defaultMerch.forEach(item => {
      this.merchandiseItems.set(item.id, item);
    });
  }

  private async initializeSponsorshipTiers(): Promise<void> {
    const defaultSponsors: SponsorshipTier[] = [
      {
        id: 'copper-sponsor',
        name: 'Copper Sponsor',
        price: 100,
        currency: 'USD',
        duration: 30,
        benefits: [
          'Logo in stream overlay',
          '2 mentions per stream',
          'Social media shoutout'
        ],
        mentionsPerStream: 2,
        customIntegration: false,
        isActive: true
      },
      {
        id: 'silver-sponsor',
        name: 'Silver Sponsor',
        price: 250,
        currency: 'USD',
        duration: 30,
        benefits: [
          'Prominent logo placement',
          '5 mentions per stream',
          'Product demonstration segment',
          'Social media campaign'
        ],
        logoPlacement: {
          position: 'bottom-right',
          duration: 30
        },
        mentionsPerStream: 5,
        customIntegration: true,
        isActive: true
      },
      {
        id: 'gold-sponsor',
        name: 'Gold Sponsor',
        price: 500,
        currency: 'USD',
        duration: 30,
        benefits: [
          'Featured sponsor status',
          'Unlimited mentions',
          'Custom integration segment',
          'Sponsored giveaway items',
          'Full social media campaign'
        ],
        logoPlacement: {
          position: 'top-banner',
          duration: 60
        },
        mentionsPerStream: 999,
        customIntegration: true,
        isActive: true
      }
    ];

    defaultSponsors.forEach(tier => {
      this.sponsorshipTiers.set(tier.id, tier);
    });
  }

  private setupWebhooks(): void {
    // Stripe webhook handler would be set up here
    // This would handle payment confirmations, subscription updates, etc.
  }

  // Donation processing
  public static async processDonation(donationData: DonationData): Promise<IDonation> {
    const service = MonetizationService.instance;

    try {
      // Store donation in database
      const donation = await DatabaseService.createDonation({
        platform: donationData.platform,
        amount: donationData.amount,
        currency: donationData.currency,
        donorName: donationData.donorName,
        message: donationData.message,
        streamSession: donationData.sessionId,
        status: 'completed',
        metadata: {
          isAnonymous: donationData.isAnonymous
        }
      });

      // Trigger donation alert
      service.emit('donationAlert', {
        ...donationData,
        donationId: donation._id,
        timestamp: new Date()
      });

      // Update stream session revenue
      if (donationData.sessionId) {
        await service.updateSessionRevenue(donationData.sessionId, donationData.amount);
      }

      logger.info(`Processed ${donationData.platform} donation: ${donationData.amount} ${donationData.currency} from ${donationData.donorName}`);

      return donation;

    } catch (error) {
      logger.error('Failed to process donation:', error);
      throw error;
    }
  }

  private async updateSessionRevenue(sessionId: string, amount: number): Promise<void> {
    try {
      const session = await DatabaseService.getStreamSession(sessionId);
      if (session) {
        await DatabaseService.updateStreamSession(sessionId, {
          revenue: {
            ...session.revenue,
            donations: session.revenue.donations + amount,
            total: session.revenue.total + amount
          }
        });
      }
    } catch (error) {
      logger.error('Failed to update session revenue:', error);
    }
  }

  // Stripe payment processing
  public static async createStripePaymentIntent(amount: number, currency: string = 'usd'): Promise<{ clientSecret: string }> {
    const service = MonetizationService.instance;

    try {
      const paymentIntent = await service.stripe.paymentIntents.create({
        amount: Math.round(amount * 100), // Convert to cents
        currency,
        automatic_payment_methods: {
          enabled: true
        },
        metadata: {
          platform: 'stripe'
        }
      });

      return { clientSecret: paymentIntent.client_secret };

    } catch (error) {
      logger.error('Failed to create Stripe payment intent:', error);
      throw error;
    }
  }

  // PayPal payment processing
  public static async createPayPalPayment(amount: number, currency: string = 'USD'): Promise<any> {
    return new Promise((resolve, reject) => {
      const payment = {
        intent: 'sale',
        payer: {
          payment_method: 'paypal'
        },
        redirect_urls: {
          return_url: `${process.env.BASE_URL}/api/paypal/return`,
          cancel_url: `${process.env.BASE_URL}/api/paypal/cancel`
        },
        transactions: [{
          amount: {
            total: amount.toFixed(2),
            currency: currency
          },
          description: 'D&D Stream Donation'
        }]
      };

      paypal.payment.create(payment, (error: any, payment: any) => {
        if (error) {
          logger.error('PayPal payment creation failed:', error);
          reject(error);
        } else {
          resolve(payment);
        }
      });
    });
  }

  // Subscription management
  public static async createSubscription(tierId: string, customerId: string): Promise<any> {
    const service = MonetizationService.instance;
    const tier = service.subscriptionTiers.get(tierId);

    if (!tier) {
      throw new Error('Invalid subscription tier');
    }

    try {
      const price = await service.stripe.prices.create({
        unit_amount: Math.round(tier.price * 100),
        currency: tier.currency.toLowerCase(),
        recurring: {
          interval: tier.billingInterval
        },
        product_data: {
          name: tier.name,
          description: tier.benefits.join(', ')
        }
      });

      const subscription = await service.stripe.subscriptions.create({
        customer: customerId,
        items: [{ price: price.id }],
        payment_behavior: 'default_incomplete',
        expand: ['latest_invoice.payment_intent']
      });

      return subscription;

    } catch (error) {
      logger.error('Failed to create subscription:', error);
      throw error;
    }
  }

  // Merchandise management
  public static async purchaseMerchandise(
    itemId: string,
    quantity: number,
    customerInfo: any
  ): Promise<any> {
    const service = MonetizationService.instance;
    const item = service.merchandiseItems.get(itemId);

    if (!item) {
      throw new Error('Item not found');
    }

    if (!item.isDigital && item.inventory.available < quantity) {
      throw new Error('Insufficient inventory');
    }

    try {
      // Create payment intent
      const totalAmount = item.price * quantity;
      const paymentIntent = await service.stripe.paymentIntents.create({
        amount: Math.round(totalAmount * 100),
        currency: item.currency.toLowerCase(),
        metadata: {
          type: 'merchandise',
          itemId,
          quantity: quantity.toString()
        }
      });

      // Reserve inventory
      if (!item.isDigital) {
        item.inventory.reserved += quantity;
        item.inventory.available -= quantity;
      }

      return {
        clientSecret: paymentIntent.client_secret,
        totalAmount,
        item
      };

    } catch (error) {
      logger.error('Failed to process merchandise purchase:', error);
      throw error;
    }
  }

  // Sponsorship management
  public static async purchaseSponsorship(
    tierId: string,
    sponsorInfo: any
  ): Promise<any> {
    const service = MonetizationService.instance;
    const tier = service.sponsorshipTiers.get(tierId);

    if (!tier) {
      throw new Error('Sponsorship tier not found');
    }

    try {
      const paymentIntent = await service.stripe.paymentIntents.create({
        amount: Math.round(tier.price * 100),
        currency: tier.currency.toLowerCase(),
        metadata: {
          type: 'sponsorship',
          tierId,
          sponsorName: sponsorInfo.name,
          duration: tier.duration.toString()
        }
      });

      return {
        clientSecret: paymentIntent.client_secret,
        tier,
        sponsorInfo
      };

    } catch (error) {
      logger.error('Failed to process sponsorship purchase:', error);
      throw error;
    }
  }

  // Revenue analytics
  public static async getRevenueBreakdown(
    startDate: Date,
    endDate: Date
  ): Promise<RevenueBreakdown> {
    try {
      const analytics = await DatabaseService.getStreamAnalytics({
        start: startDate,
        end: endDate
      });

      const donations = await DatabaseService.getDonationsBySession('');

      // Process donations by platform
      const donationsByPlatform: { [platform: string]: number } = {};
      let totalDonations = 0;

      donations.forEach(donation => {
        if (donation.status === 'completed') {
          donationsByPlatform[donation.platform] =
            (donationsByPlatform[donation.platform] || 0) + donation.amount;
          totalDonations += donation.amount;
        }
      });

      // Calculate fees (approximately 3% for payment processing)
      const totalRevenue = totalDonations + analytics.totalRevenue;
      const fees = totalRevenue * 0.03;

      return {
        period: {
          start: startDate,
          end: endDate
        },
        donations: {
          amount: totalDonations,
          count: donations.filter(d => d.status === 'completed').length,
          byPlatform: donationsByPlatform
        },
        subscriptions: {
          amount: analytics.totalRevenue * 0.6, // Estimate
          count: 0, // Would need to query subscription data
          byTier: {},
          churnRate: 0.05 // Estimate
        },
        merchandise: {
          amount: analytics.totalRevenue * 0.3, // Estimate
          count: 0,
          byItem: {}
        },
        sponsorships: {
          amount: analytics.totalRevenue * 0.1, // Estimate
          count: 0,
          byTier: {}
        },
        total: totalRevenue,
        fees,
        net: totalRevenue - fees
      };

    } catch (error) {
      logger.error('Failed to generate revenue breakdown:', error);
      throw error;
    }
  }

  // Tier management
  public static getSubscriptionTiers(): SubscriptionTier[] {
    const service = MonetizationService.instance;
    return Array.from(service.subscriptionTiers.values()).filter(tier => tier.isActive);
  }

  public static getMerchandiseItems(): MerchandiseItem[] {
    const service = MonetizationService.instance;
    return Array.from(service.merchandiseItems.values()).filter(item => item.isActive);
  }

  public static getSponsorshipTiers(): SponsorshipTier[] {
    const service = MonetizationService.instance;
    return Array.from(service.sponsorshipTiers.values()).filter(tier => tier.isActive);
  }

  public static updateSubscriptionTier(tierId: string, updates: Partial<SubscriptionTier>): void {
    const service = MonetizationService.instance;
    const tier = service.subscriptionTiers.get(tierId);
    if (tier) {
      service.subscriptionTiers.set(tierId, { ...tier, ...updates });
    }
  }

  public static updateMerchandiseItem(itemId: string, updates: Partial<MerchandiseItem>): void {
    const service = MonetizationService.instance;
    const item = service.merchandiseItems.get(itemId);
    if (item) {
      service.merchandiseItems.set(itemId, { ...item, ...updates });
    }
  }

  // Payment webhook handlers
  public static async handleStripeWebhook(event: Stripe.Event): Promise<void> {
    const service = MonetizationService.instance;

    try {
      switch (event.type) {
        case 'payment_intent.succeeded':
          const paymentIntent = event.data.object as Stripe.PaymentIntent;
          await service.handleSuccessfulPayment(paymentIntent);
          break;

        case 'invoice.payment_succeeded':
          const invoice = event.data.object as Stripe.Invoice;
          await service.handleSuccessfulSubscriptionPayment(invoice);
          break;

        case 'customer.subscription.deleted':
          const subscription = event.data.object as Stripe.Subscription;
          await service.handleSubscriptionCancellation(subscription);
          break;

        default:
          logger.info(`Unhandled Stripe webhook event: ${event.type}`);
      }
    } catch (error) {
      logger.error('Error handling Stripe webhook:', error);
      throw error;
    }
  }

  private async handleSuccessfulPayment(paymentIntent: Stripe.PaymentIntent): Promise<void> {
    const metadata = paymentIntent.metadata;

    if (metadata.type === 'merchandise') {
      // Complete merchandise order
      const itemId = metadata.itemId;
      const quantity = parseInt(metadata.quantity);

      const item = this.merchandiseItems.get(itemId);
      if (item && !item.isDigital) {
        item.inventory.reserved -= quantity;
        // Order fulfillment logic would go here
      }
    }

    this.emit('paymentSucceeded', { paymentIntent, metadata });
  }

  private async handleSuccessfulSubscriptionPayment(invoice: Stripe.Invoice): Promise<void> {
    this.emit('subscriptionPaymentSucceeded', { invoice });
  }

  private async handleSubscriptionCancellation(subscription: Stripe.Subscription): Promise<void> {
    this.emit('subscriptionCancelled', { subscription });
  }
}

export default MonetizationService;