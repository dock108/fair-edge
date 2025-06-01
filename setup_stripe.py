#!/usr/bin/env python3
"""
Simple setup script to help configure Stripe integration
This script will guide you through setting up Stripe for bet-intel
"""
import sys
from pathlib import Path

def main():
    print("🚀 Stripe Integration Setup for bet-intel")
    print("=" * 50)
    
    # Check if .env exists
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found!")
        print("Please copy .env.example to .env first:")
        print("cp .env.example .env")
        return
    
    print("✅ Found .env file")
    
    # Read current .env content
    with open('.env', 'r') as f:
        env_content = f.read()
    
    # Check if Stripe variables are already configured
    stripe_vars = [
        'STRIPE_SECRET_KEY=',
        'STRIPE_WEBHOOK_SECRET=',
        'STRIPE_PREMIUM_PRICE='
    ]
    
    configured_vars = []
    for var in stripe_vars:
        if var in env_content and not env_content.split(var)[1].split('\n')[0].strip().startswith('sk_test_your_') and not env_content.split(var)[1].split('\n')[0].strip().startswith('whsec_your_') and not env_content.split(var)[1].split('\n')[0].strip().startswith('price_your_'):
            configured_vars.append(var.replace('=', ''))
    
    if len(configured_vars) == 3:
        print("✅ Stripe appears to be already configured!")
        print("Configured variables:", ', '.join(configured_vars))
    else:
        print(f"⚠️  Stripe configuration incomplete ({len(configured_vars)}/3 variables set)")
        print()
        print("📋 To complete Stripe setup:")
        print()
        print("1. 🏢 Set up Stripe Account")
        print("   - Go to https://stripe.com and create an account")
        print("   - Complete account verification")
        print()
        print("2. 🛍️ Create Product & Price")
        print("   - Go to Stripe Dashboard → Products")
        print("   - Create 'Premium Subscription' product")
        print("   - Set price to $29/month (or your preferred amount)")
        print("   - Copy the Price ID (starts with 'price_')")
        print()
        print("3. 🔑 Get API Keys")
        print("   - Go to Stripe Dashboard → Developers → API keys")
        print("   - Copy your Secret key (starts with 'sk_test_' for test mode)")
        print()
        print("4. 🔗 Set up Webhook")
        print("   - Go to Stripe Dashboard → Webhooks")
        print("   - Add endpoint: https://your-domain.com/api/billing/stripe/webhook")
        print("   - Select events: checkout.session.completed, customer.subscription.deleted")
        print("   - Copy the webhook secret (starts with 'whsec_')")
        print()
        print("5. ✏️  Update .env file")
        print("   Edit .env and set:")
        print("   STRIPE_SECRET_KEY=sk_test_your_actual_key")
        print("   STRIPE_WEBHOOK_SECRET=whsec_your_actual_secret")
        print("   STRIPE_PREMIUM_PRICE=price_your_actual_price_id")
        print()
    
    # Test current configuration
    print("\n🧪 Testing current configuration...")
    try:
        # Add the current directory to Python path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from core.config import settings
        
        print("✅ Configuration loaded successfully")
        print(f"   Stripe configured: {'Yes' if settings.stripe_configured else 'No'}")
        print(f"   Secret key: {'Set' if settings.stripe_secret_key else 'Not set'}")
        print(f"   Webhook secret: {'Set' if settings.stripe_webhook_secret else 'Not set'}")
        print(f"   Premium price: {'Set' if settings.stripe_premium_price else 'Not set'}")
        print(f"   Success URL: {settings.checkout_success_url}")
        print(f"   Cancel URL: {settings.checkout_cancel_url}")
        
        if settings.stripe_configured:
            print("\n🎉 Stripe is fully configured and ready to use!")
        else:
            print("\n⚠️  Stripe configuration is incomplete.")
            print("The app will work, but billing features will be disabled.")
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        print("This might indicate an issue with your .env file or dependencies.")
    
    print("\n" + "=" * 50)
    print("Next steps:")
    print("1. Run the database migration: python scripts/add_stripe_columns.py")
    print("2. Test the integration: python tests/test_stripe_integration.py")
    print("3. Start the app: python app.py")
    print()
    print("📚 For detailed instructions, see: STRIPE_IMPLEMENTATION.md")

if __name__ == "__main__":
    main() 