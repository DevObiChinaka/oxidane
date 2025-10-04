'use client';

import { useState } from 'react';
import { EmailTemplate } from '../../types/admin';

interface TemplateBuilderProps {
  templateType: string;
  onTemplateGenerated: (template: Partial<EmailTemplate>) => void;
}

const EMAIL_TEMPLATES = {
  welcome: {
    name: 'Welcome Email',
    subject_template: 'Welcome to {{company_name}}, {{user.first_name}}!',
    html_content: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to {{company_name}}</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; }
        .content { padding: 30px 20px; background: #ffffff; }
        .footer { padding: 20px; background: #f8f9fa; text-align: center; font-size: 14px; color: #666; }
        .button { display: inline-block; background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to {{company_name}}!</h1>
            <p>We're excited to have you join our community</p>
        </div>
        
        <div class="content">
            <h2>Hi {{user.first_name}},</h2>
            
            <p>Thank you for joining {{company_name}}! We're thrilled to welcome you to our community of learners and innovators.</p>
            
            <p>Here's what you can do next:</p>
            <ul>
                <li>Complete your profile setup</li>
                <li>Browse our course catalog</li>
                <li>Join our community discussions</li>
                <li>Start your first course</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{dashboard_link}}" class="button">Get Started</a>
            </div>
            
            <p>If you have any questions, feel free to reach out to our support team.</p>
            
            <p>Best regards,<br>The {{company_name}} Team</p>
        </div>
        
        <div class="footer">
            <p>&copy; {{current_year}} {{company_name}}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>`,
    text_content: `Welcome to {{company_name}}, {{user.first_name}}!

Hi {{user.first_name}},

Thank you for joining {{company_name}}! We're thrilled to welcome you to our community of learners and innovators.

Here's what you can do next:
- Complete your profile setup
- Browse our course catalog
- Join our community discussions
- Start your first course

Get started: {{dashboard_link}}

If you have any questions, feel free to reach out to our support team.

Best regards,
The {{company_name}} Team

© {{current_year}} {{company_name}}. All rights reserved.`
  },
  
  subscription_success: {
    name: 'Subscription Confirmed',
    subject_template: 'Subscription Confirmed - Welcome to {{subscription.plan_name}}!',
    html_content: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Subscription Confirmed</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 40px 20px; text-align: center; }
        .content { padding: 30px 20px; background: #ffffff; }
        .success-box { background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 20px; margin: 20px 0; }
        .plan-details { background: #f8f9fa; border-radius: 5px; padding: 20px; margin: 20px 0; }
        .footer { padding: 20px; background: #f8f9fa; text-align: center; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Subscription Confirmed!</h1>
            <p>Thank you for your purchase</p>
        </div>
        
        <div class="content">
            <div class="success-box">
                <h3>Payment Successful</h3>
                <p>Your subscription to <strong>{{subscription.plan_name}}</strong> has been activated!</p>
            </div>
            
            <h2>Hi {{user.first_name}},</h2>
            
            <p>We're excited to confirm that your subscription is now active. You now have full access to all premium features.</p>
            
            <div class="plan-details">
                <h4>Subscription Details:</h4>
                <ul>
                    <li><strong>Plan:</strong> ` + '{{subscription.plan_name}}' + `</li>
                    <li><strong>Amount:</strong> $` + '{{subscription.amount}}' + `</li>
                    <li><strong>Billing Cycle:</strong> ` + '{{subscription.billing_cycle}}' + `</li>
                    <li><strong>Next Billing Date:</strong> ` + '{{subscription.next_billing_date}}' + `</li>
                </ul>
            </div>
            
            <p>You can manage your subscription and billing details in your account dashboard.</p>
            
            <p>Thank you for choosing {{company_name}}!</p>
            
            <p>Best regards,<br>The {{company_name}} Team</p>
        </div>
        
        <div class="footer">
            <p>&copy; {{current_year}} {{company_name}}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>`,
    text_content: `Subscription Confirmed - Welcome to {{subscription.plan_name}}!

Hi {{user.first_name}},

✅ Payment Successful
Your subscription to {{subscription.plan_name}} has been activated!

We're excited to confirm that your subscription is now active. You now have full access to all premium features.

Subscription Details:
- Plan: ` + '{{subscription.plan_name}}' + `
- Amount: $` + '{{subscription.amount}}' + `
- Billing Cycle: ` + '{{subscription.billing_cycle}}' + `
- Next Billing Date: ` + '{{subscription.next_billing_date}}' + `

You can manage your subscription and billing details in your account dashboard.

Thank you for choosing {{company_name}}!

Best regards,
The {{company_name}} Team

© {{current_year}} {{company_name}}. All rights reserved.`
  },
  
  payment_failed: {
    name: 'Payment Failed Notice',
    subject_template: 'Action Required: Payment Issue with Your {{company_name}} Subscription',
    html_content: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Payment Issue</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); color: white; padding: 40px 20px; text-align: center; }
        .content { padding: 30px 20px; background: #ffffff; }
        .alert-box { background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 20px; margin: 20px 0; }
        .button { display: inline-block; background: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
        .footer { padding: 20px; background: #f8f9fa; text-align: center; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚠️ Payment Issue</h1>
            <p>Action required for your subscription</p>
        </div>
        
        <div class="content">
            <div class="alert-box">
                <h3>Payment Failed</h3>
                <p>We were unable to process your payment for {{subscription.plan_name}}.</p>
            </div>
            
            <h2>Hi {{user.first_name}},</h2>
            
            <p>We attempted to charge your payment method for your {{company_name}} subscription, but the payment was declined.</p>
            
            <p><strong>What happens next?</strong></p>
            <ul>
                <li>Your subscription remains active for {{grace_period_days}} days</li>
                <li>We'll retry the payment in {{retry_days}} days</li>
                <li>Please update your payment method to avoid service interruption</li>
            </ul>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{payment_update_link}}" class="button">Update Payment Method</a>
            </div>
            
            <p>If you have any questions or need assistance, please contact our support team.</p>
            
            <p>Best regards,<br>The {{company_name}} Team</p>
        </div>
        
        <div class="footer">
            <p>&copy; {{current_year}} {{company_name}}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>`,
    text_content: `Action Required: Payment Issue with Your {{company_name}} Subscription

Hi {{user.first_name}},

⚠️ Payment Failed
We were unable to process your payment for {{subscription.plan_name}}.

We attempted to charge your payment method for your {{company_name}} subscription, but the payment was declined.

What happens next?
- Your subscription remains active for {{grace_period_days}} days
- We'll retry the payment in {{retry_days}} days
- Please update your payment method to avoid service interruption

Update your payment method: {{payment_update_link}}

If you have any questions or need assistance, please contact our support team.

Best regards,
The {{company_name}} Team

© {{current_year}} {{company_name}}. All rights reserved.`
  },
  
  renewal_reminder: {
    name: 'Subscription Renewal Reminder',
    subject_template: 'Your {{company_name}} subscription renews in {{days_until_renewal}} days',
    html_content: `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Renewal Reminder</title>
    <style>
        .container { max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }
        .header { background: linear-gradient(135deg, #17a2b8 0%, #138496 100%); color: white; padding: 40px 20px; text-align: center; }
        .content { padding: 30px 20px; background: #ffffff; }
        .info-box { background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 20px; margin: 20px 0; }
        .button { display: inline-block; background: #17a2b8; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; }
        .footer { padding: 20px; background: #f8f9fa; text-align: center; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔄 Renewal Reminder</h1>
            <p>Your subscription renews soon</p>
        </div>
        
        <div class="content">
            <h2>Hi {{user.first_name}},</h2>
            
            <p>This is a friendly reminder that your {{company_name}} subscription will automatically renew in {{days_until_renewal}} days.</p>
            
            <div class="info-box">
                <h4>Renewal Details:</h4>
                <ul>
                    <li><strong>Plan:</strong> ` + '{{subscription.plan_name}}' + `</li>
                    <li><strong>Renewal Date:</strong> ` + '{{renewal_date}}' + `</li>
                    <li><strong>Amount:</strong> $` + '{{subscription.amount}}' + `</li>
                    <li><strong>Payment Method:</strong> ` + '{{payment_method_last4}}' + `</li>
                </ul>
            </div>
            
            <p>No action is required - your subscription will renew automatically. If you need to make any changes to your plan or payment method, you can do so in your account settings.</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{account_settings_link}}" class="button">Manage Subscription</a>
            </div>
            
            <p>Thank you for being a valued {{company_name}} member!</p>
            
            <p>Best regards,<br>The {{company_name}} Team</p>
        </div>
        
        <div class="footer">
            <p>&copy; {{current_year}} {{company_name}}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>`,
    text_content: `Your {{company_name}} subscription renews in {{days_until_renewal}} days

Hi {{user.first_name}},

This is a friendly reminder that your {{company_name}} subscription will automatically renew in {{days_until_renewal}} days.

Renewal Details:
- Plan: ` + '{{subscription.plan_name}}' + `
- Renewal Date: ` + '{{renewal_date}}' + `
- Amount: $` + '{{subscription.amount}}' + `
- Payment Method: ` + '{{payment_method_last4}}' + `

No action is required - your subscription will renew automatically. If you need to make any changes to your plan or payment method, you can do so in your account settings.

Manage your subscription: {{account_settings_link}}

Thank you for being a valued {{company_name}} member!

Best regards,
The {{company_name}} Team

© {{current_year}} {{company_name}}. All rights reserved.`
  }
};

export default function TemplateBuilder({ templateType, onTemplateGenerated }: TemplateBuilderProps) {
  const [isGenerating, setIsGenerating] = useState(false);

  const generateTemplate = () => {
    setIsGenerating(true);
    
    // Simulate generation time
    setTimeout(() => {
      const template = EMAIL_TEMPLATES[templateType as keyof typeof EMAIL_TEMPLATES];
      if (template) {
        onTemplateGenerated({
          name: template.name,
          template_type: templateType,
          subject_template: template.subject_template,
          html_content: template.html_content,
          text_content: template.text_content,
          status: 'draft',
          description: `Auto-generated ${template.name} template with responsive design and professional styling.`,
          is_default: false
        });
      }
      setIsGenerating(false);
    }, 1500);
  };

  const templateExists = EMAIL_TEMPLATES[templateType as keyof typeof EMAIL_TEMPLATES];

  if (!templateExists) {
    return null;
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-medium text-blue-900">✨ Auto-Generate Template</h4>
          <p className="text-sm text-blue-700">
            Generate a professional, responsive email template with pre-built content for {templateType.replace('_', ' ')} emails.
          </p>
        </div>
        <button
          type="button"
          onClick={generateTemplate}
          disabled={isGenerating}
          className="ml-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isGenerating ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Generating...
            </>
          ) : (
            <>
              🎨 Generate Template
            </>
          )}
        </button>
      </div>
    </div>
  );
}