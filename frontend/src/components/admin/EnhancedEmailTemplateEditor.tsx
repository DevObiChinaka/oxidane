'use client';

import { useState, useEffect } from 'react';
import { adminAPI } from '../../app/admin/utils/api';
import { EmailTemplate, EmailTemplateType } from '../../types/admin';

// Comprehensive pre-built template designs for all template types
const TEMPLATE_DESIGNS = {
  welcome: {
    name: 'Welcome Email - New User Onboarding',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .welcome-badge { background: #E0E7FF; color: #3730A3; padding: 8px 16px; border-radius: 20px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 500; }
    .button { background: #4F46E5; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; transition: background 0.3s; }
    .features { background: #F8FAFC; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .feature-item { margin: 10px 0; display: flex; align-items: center; }
    .checkmark { color: #10B981; font-weight: bold; margin-right: 10px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 28px;">Welcome to OxiWorld!</h1>
      <p style="margin: 10px 0 0; opacity: 0.9; font-size: 16px;">Your Forex Trading Journey Begins Now</p>
    </div>
    <div class="content">
      <div class="welcome-badge">Account Created Successfully</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Welcome to OxiWorld! We're thrilled to have you join our community of successful forex traders.</p>
      
      <div class="features">
        <h3 style="margin: 0 0 15px; color: #1F2937;">What's waiting for you:</h3>
        <div class="feature-item"><span class="checkmark">•</span> <span>Expert-led forex trading courses</span></div>
        <div class="feature-item"><span class="checkmark">•</span> <span>Real-time market analysis and insights</span></div>
        <div class="feature-item"><span class="checkmark">•</span> <span>Interactive trading simulators</span></div>
        <div class="feature-item"><span class="checkmark">•</span> <span>24/7 community support</span></div>
      </div>

      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Ready to start your forex mastery journey?</p>
      <a href="{{custom.dashboard_url}}" class="button">Access Your Dashboard</a>
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">Need help getting started? Our support team is here to assist you every step of the way.</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Welcome aboard!<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">You're receiving this because you created an account with us.</p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Welcome to OxiWorld, {{user.first_name}} - Your Trading Journey Starts Here',
    text: `Hi {{user.first_name}},

Welcome to OxiWorld! 

Your account has been successfully created and you're ready to start your forex trading journey.

What's waiting for you:
• Expert-led forex trading courses
• Real-time market analysis and insights  
• Interactive trading simulators
• 24/7 community support

Get started: {{custom.dashboard_url}}

Need help? Our support team is here to assist you every step of the way.

Welcome aboard!
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.`
  },

  verification: {
    name: 'Email Verification - Account Security',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #1E40AF; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .verification-badge { background: #DBEAFE; color: #1E40AF; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .verify-button { background: #1E40AF; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .security-info { background: #F0F9FF; border-left: 4px solid #1E40AF; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> Verify Your Email</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Secure your OxiWorld account</p>
    </div>
    <div class="content">
      <div class="verification-badge"> Email Verification Required</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">To complete your OxiWorld account setup and ensure the security of your trading account, please verify your email address.</p>
      
      <div class="security-info">
        <p style="margin: 0; color: #1E40AF; font-weight: 600;">Why verify your email?</p>
        <ul style="margin: 10px 0 0; color: #374151; padding-left: 20px;">
          <li>Secure account recovery options</li>
          <li>Important trading alerts and notifications</li>
          <li>Account security confirmations</li>
        </ul>
      </div>

      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Click the button below to verify your email address:</p>
      <a href="{{custom.verification_url}}" class="verify-button">Verify Email Address</a>
      
      <div style="background: #FFFBEB; border: 1px solid #FCD34D; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #92400E; font-size: 14px;"><strong> Time Sensitive:</strong> This verification link will expire in 24 hours for security reasons.</p>
      </div>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">If the button doesn't work, copy and paste this link into your browser:<br>
      <span style="word-break: break-all; color: #1E40AF;">{{custom.verification_url}}</span></p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Security Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">If you didn't create an account with us, please ignore this email.</p>
    </div>
  </div>
</body>
</html>`,
    subject: ' Verify Your OxiWorld Account - Action Required',
    text: `Hi {{user.first_name}},

 Email Verification Required

To complete your OxiWorld account setup and ensure security, please verify your email address.

Why verify your email?
• Secure account recovery options
• Important trading alerts and notifications
• Account security confirmations

Verify your email: {{custom.verification_url}}

 Time Sensitive: This verification link will expire in 24 hours for security reasons.

Best regards,
The OxiWorld Security Team

© 2025 OxiWorld. All rights reserved.
If you didn't create an account with us, please ignore this email.`
  },

  password_reset: {
    name: 'Password Reset - Secure Access Recovery',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #DC2626; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .reset-badge { background: #FEE2E2; color: #DC2626; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .reset-button { background: #DC2626; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .security-warning { background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Password Reset Request</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Secure your account access</p>
    </div>
    <div class="content">
      <div class="reset-badge">Reset Password Request</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We received a request to reset the password for your OxiWorld trading account. If you made this request, click the button below to create a new password.</p>
      
      <a href="{{custom.reset_url}}" class="reset-button">Reset My Password</a>
      
      <div class="security-warning">
        <p style="margin: 0; color: #92400E; font-weight: 600;">Security Notice:</p>
        <ul style="margin: 10px 0 0; color: #92400E; padding-left: 20px;">
          <li>This reset link expires in 1 hour for your security</li>
          <li>Only use this link if you requested the password reset</li>
          <li>Never share this link with anyone</li>
        </ul>
      </div>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">If the button doesn't work, copy and paste this link into your browser:<br>
      <span style="word-break: break-all; color: #DC2626;">{{custom.reset_url}}</span></p>
      
      <div style="background: #FECACA; border: 1px solid #DC2626; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #991B1B; font-size: 14px;"><strong>Didn't request this?</strong> If you didn't request a password reset, please ignore this email or contact our security team immediately.</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Stay secure,<br><strong>The OxiWorld Security Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">This is an automated security email. Please do not reply.</p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Reset Your OxiWorld Password - Expires in 1 Hour',
    text: `Hi {{user.first_name}},

Password Reset Request

We received a request to reset your OxiWorld account password. If you made this request, use the link below to create a new password.

Reset your password: {{custom.reset_url}}

Security Notice:
• This reset link expires in 1 hour for your security
• Only use this link if you requested the password reset  
• Never share this link with anyone

Didn't request this? If you didn't request a password reset, please ignore this email or contact our security team immediately.

Stay secure,
The OxiWorld Security Team

© 2025 OxiWorld. All rights reserved.`
  },

  notification: {
    name: 'General Notification - Important Updates',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #0891B2; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .notification-badge { background: #CFFAFE; color: #0891B2; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .action-button { background: #0891B2; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; }
    .info-box { background: #F0F9FF; border-left: 4px solid #0891B2; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">Important Update</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Stay informed about your account</p>
    </div>
    <div class="content">
      <div class="notification-badge">Account Notification</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We wanted to inform you about an important update regarding your OxiWorld account.</p>
      
      <div class="info-box">
        <h3 style="margin: 0 0 10px; color: #0891B2;">{{notification.title}}</h3>
        <p style="margin: 0; color: #374151; line-height: 1.6;">{{notification.message}}</p>
      </div>

      <p style="font-size: 16px; line-height: 1.6; color: #374151;">{{custom.additional_message}}</p>
      
      <a href="{{custom.action_url}}" class="action-button">{{custom.action_text}}</a>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">If you have any questions, please don't hesitate to contact our support team.</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">You're receiving this because of your account settings preferences.</p>
    </div>
  </div>
</body>
</html>`,
    subject: '{{notification.title}} - OxiWorld Account Update',
    text: `Hi {{user.first_name}},

Important Update

{{notification.title}}

{{notification.message}}

{{custom.additional_message}}

Take action: {{custom.action_url}}

If you have any questions, please contact our support team.

Best regards,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.`
  },

  marketing: {
    name: 'Marketing Campaign - Trading Success',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .promo-badge { background: #D1FAE5; color: #065F46; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .cta-button { background: #10B981; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; text-align: center; }
    .features-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 25px 0; }
    .feature-card { background: #F0FDF4; padding: 15px; border-radius: 8px; text-align: center; }
    .stats-section { background: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 28px;"> Unlock Trading Success</h1>
      <p style="margin: 10px 0 0; opacity: 0.9; font-size: 16px;">Master Forex Trading with Expert Guidance</p>
    </div>
    <div class="content">
      <div class="promo-badge"> Limited Time Offer</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Ready to take your forex trading to the next level? Join thousands of successful traders who've transformed their financial future with OxiWorld.</p>
      
      <div class="stats-section">
        <h3 style="margin: 0 0 15px; color: #065F46;">OxiWorld Success Stories</h3>
        <div style="display: flex; justify-content: space-around; text-align: center;">
          <div>
            <div style="font-size: 24px; font-weight: bold; color: #10B981;">95%</div>
            <div style="font-size: 12px; color: #374151;">Success Rate</div>
          </div>
          <div>
            <div style="font-size: 24px; font-weight: bold; color: #10B981;">10K+</div>
            <div style="font-size: 12px; color: #374151;">Active Traders</div>
          </div>
          <div>
            <div style="font-size: 24px; font-weight: bold; color: #10B981;">$2M+</div>
            <div style="font-size: 12px; color: #374151;">Profits Made</div>
          </div>
        </div>
      </div>

      <div class="features-grid">
        <div class="feature-card">
          <div style="font-size: 24px; margin-bottom: 10px;"></div>
          <div style="font-weight: 600; color: #065F46;">Expert Courses</div>
          <div style="font-size: 12px; color: #374151;">Comprehensive trading education</div>
        </div>
        <div class="feature-card">
          <div style="font-size: 24px; margin-bottom: 10px;"></div>
          <div style="font-weight: 600; color: #065F46;">Live Analysis</div>
          <div style="font-size: 12px; color: #374151;">Real-time market insights</div>
        </div>
        <div class="feature-card">
          <div style="font-size: 24px; margin-bottom: 10px;"></div>
          <div style="font-weight: 600; color: #065F46;">Community</div>
          <div style="font-size: 12px; color: #374151;">24/7 trader support</div>
        </div>
        <div class="feature-card">
          <div style="font-size: 24px; margin-bottom: 10px;"></div>
          <div style="font-weight: 600; color: #065F46;">Signals</div>
          <div style="font-size: 12px; color: #374151;">Profitable trade alerts</div>
        </div>
      </div>

      <div style="background: #FEF3C7; border: 1px solid #F59E0B; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
        <p style="margin: 0; color: #92400E; font-weight: 600;"> Special Offer: 50% OFF Premium Membership</p>
        <p style="margin: 5px 0 0; color: #92400E; font-size: 14px;">Limited time - Expires {{custom.offer_expiry}}</p>
      </div>

      <a href="{{custom.upgrade_url}}" class="cta-button" style="display: block; text-decoration: none; color: white;"> Claim Your Discount Now</a>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">Join the ranks of successful traders today. Your financial freedom is just one click away.</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">To your trading success,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;"><a href="{{custom.unsubscribe_url}}" style="color: #64748B;">Unsubscribe</a> | <a href="{{custom.preferences_url}}" style="color: #64748B;">Manage Preferences</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: '{{user.first_name}}, Unlock 50% OFF Premium Trading - Limited Time',
    text: `Hi {{user.first_name}},

 Unlock Trading Success

Ready to take your forex trading to the next level? Join thousands of successful traders who've transformed their financial future with OxiWorld.

OxiWorld Success Stories:
• 95% Success Rate
• 10K+ Active Traders  
• $2M+ Profits Made

What you get:
 Expert Courses - Comprehensive trading education
 Live Analysis - Real-time market insights
 Community - 24/7 trader support
 Signals - Profitable trade alerts

 Special Offer: 50% OFF Premium Membership
Limited time - Expires {{custom.offer_expiry}}

Claim Your Discount: {{custom.upgrade_url}}

Join the ranks of successful traders today. Your financial freedom is just one click away.

To your trading success,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.
Unsubscribe: {{custom.unsubscribe_url}}`
  },

  newsletter: {
    name: 'Newsletter - Weekly Market Insights',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #7C3AED; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .newsletter-badge { background: #EDE9FE; color: #7C3AED; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .article-card { border: 1px solid #E5E7EB; border-radius: 8px; padding: 20px; margin: 20px 0; }
    .article-title { color: #1F2937; font-size: 18px; font-weight: 600; margin: 0 0 10px; }
    .article-summary { color: #6B7280; font-size: 14px; line-height: 1.5; margin: 0 0 15px; }
    .read-more { color: #7C3AED; text-decoration: none; font-weight: 500; font-size: 14px; }
    .market-data { background: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .data-row { display: flex; justify-content: space-between; margin: 10px 0; padding: 10px 0; border-bottom: 1px solid #D1D5DB; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> Weekly Market Report</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">{{newsletter.week_date}} - Expert Analysis & Insights</p>
    </div>
    <div class="content">
      <div class="newsletter-badge"> Market Intelligence</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Welcome to your weekly dose of market intelligence. Here are the key insights and opportunities from this week's trading sessions.</p>
      
      <div class="market-data">
        <h3 style="margin: 0 0 15px; color: #1F2937;"> This Week's Performance</h3>
        <div class="data-row">
          <span style="font-weight: 600;">EUR/USD</span>
          <span style="color: #10B981;">+0.85% ?</span>
        </div>
        <div class="data-row">
          <span style="font-weight: 600;">GBP/USD</span>
          <span style="color: #EF4444;">-0.32% ?</span>
        </div>
        <div class="data-row">
          <span style="font-weight: 600;">USD/JPY</span>
          <span style="color: #10B981;">+1.12% ?</span>
        </div>
        <div class="data-row" style="border-bottom: none;">
          <span style="font-weight: 600;">Gold (XAU/USD)</span>
          <span style="color: #10B981;">+2.45% ?</span>
        </div>
      </div>

      <div class="article-card">
        <h3 class="article-title"> Trade Opportunity: EUR/USD Breakout</h3>
        <p class="article-summary">The EUR/USD pair has shown strong bullish momentum this week, breaking through key resistance levels. Our technical analysis suggests potential for further upside movement.</p>
        <a href="{{newsletter.article_1_url}}" class="read-more">Read Full Analysis ?</a>
      </div>

      <div class="article-card">
        <h3 class="article-title"> Strategy Spotlight: Risk Management</h3>
        <p class="article-summary">This week we dive deep into advanced risk management techniques that can protect your capital while maximizing profit potential in volatile markets.</p>
        <a href="{{newsletter.article_2_url}}" class="read-more">Learn More ?</a>
      </div>

      <div class="article-card">
        <h3 class="article-title"> Next Week's Calendar</h3>
        <p class="article-summary">Key economic events to watch: Federal Reserve minutes, ECB policy decision, and non-farm payrolls. Get prepared with our event impact analysis.</p>
        <a href="{{newsletter.calendar_url}}" class="read-more">View Calendar ?</a>
      </div>

      <div style="background: #EDE9FE; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
        <p style="margin: 0; color: #5B21B6; font-weight: 600;"> Want more exclusive insights?</p>
        <p style="margin: 10px 0 15px; color: #5B21B6; font-size: 14px;">Upgrade to Premium for daily analysis, live trading sessions, and personalized trade alerts.</p>
        <a href="{{custom.upgrade_url}}" style="background: #7C3AED; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Upgrade Now</a>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Happy trading,<br><strong>The OxiWorld Research Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;"><a href="{{custom.unsubscribe_url}}" style="color: #64748B;">Unsubscribe</a> | <a href="{{custom.preferences_url}}" style="color: #64748B;">Manage Preferences</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Weekly Market Report: {{newsletter.week_date}} - Key Opportunities',
    text: `Hi {{user.first_name}},

 Weekly Market Report - {{newsletter.week_date}}

Welcome to your weekly dose of market intelligence. Here are the key insights from this week's trading sessions.

 This Week's Performance:
• EUR/USD: +0.85% ?
• GBP/USD: -0.32% ?  
• USD/JPY: +1.12% ?
• Gold (XAU/USD): +2.45% ?

 Trade Opportunity: EUR/USD Breakout
The EUR/USD pair has shown strong bullish momentum, breaking through key resistance levels.
Full Analysis: {{newsletter.article_1_url}}

 Strategy Spotlight: Risk Management  
Advanced risk management techniques for volatile markets.
Learn More: {{newsletter.article_2_url}}

 Next Week's Calendar
Key events: Federal Reserve minutes, ECB policy decision, and non-farm payrolls.
View Calendar: {{newsletter.calendar_url}}

 Want more exclusive insights? Upgrade to Premium for daily analysis and live trading sessions.
Upgrade: {{custom.upgrade_url}}

Happy trading,
The OxiWorld Research Team

© 2025 OxiWorld. All rights reserved.`
  },

  reminder: {
    name: 'Account Reminder - Stay Active',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #F59E0B; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .reminder-badge { background: #FEF3C7; color: #92400E; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .action-button { background: #F59E0B; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; }
    .reminder-info { background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .progress-section { background: #F9FAFB; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> We Miss You!</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Continue your trading journey</p>
    </div>
    <div class="content">
      <div class="reminder-badge"> Activity Reminder</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We noticed you haven't been active on OxiWorld recently. Your trading education journey is important to us, and we're here to help you succeed!</p>
      
      <div class="reminder-info">
        <p style="margin: 0; color: #92400E; font-weight: 600;"> Your Current Progress:</p>
        <ul style="margin: 10px 0 0; color: #92400E; padding-left: 20px;">
          <li>Course completion: {{user.course_progress}}%</li>
          <li>Last login: {{user.last_login_date}}</li>
          <li>Trading level: {{user.trading_level}}</li>
        </ul>
      </div>

      <div class="progress-section">
        <h3 style="margin: 0 0 15px; color: #1F2937;"> Ready to Continue?</h3>
        <p style="margin: 0; color: #374151; font-size: 14px;">Pick up where you left off and keep building your trading expertise:</p>
        <ul style="margin: 15px 0 0; color: #374151; font-size: 14px; padding-left: 20px;">
          <li>Complete your next lesson</li>
          <li>Check out new market analysis</li>
          <li>Practice with trading simulators</li>
          <li>Join live community discussions</li>
        </ul>
      </div>

      <a href="{{custom.dashboard_url}}" class="action-button">Continue Learning</a>
      
      <div style="background: #E0E7FF; border: 1px solid #6366F1; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #3730A3; font-size: 14px;"><strong> New This Week:</strong> {{custom.latest_feature}} - Don't miss out on the latest tools to boost your trading performance!</p>
      </div>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">Remember, consistent learning is the key to trading success. Even 10 minutes a day can make a significant difference!</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We're rooting for your success,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Too many emails? <a href="{{custom.preferences_url}}" style="color: #64748B;">Update your preferences</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: '{{user.first_name}}, Ready to Continue Your Trading Journey?',
    text: `Hi {{user.first_name}},

 We Miss You!

We noticed you haven't been active on OxiWorld recently. Your trading education journey is important to us!

 Your Current Progress:
• Course completion: {{user.course_progress}}%
• Last login: {{user.last_login_date}}  
• Trading level: {{user.trading_level}}

 Ready to Continue?
Pick up where you left off:
• Complete your next lesson
• Check out new market analysis
• Practice with trading simulators
• Join live community discussions

Continue Learning: {{custom.dashboard_url}}

 New This Week: {{custom.latest_feature}} - Don't miss out on the latest tools!

Remember, consistent learning is the key to trading success. Even 10 minutes a day can make a difference!

We're rooting for your success,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.`
  },

  support: {
    name: 'Customer Support - Help & Assistance',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #6366F1; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .support-badge { background: #E0E7FF; color: #3730A3; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .help-button { background: #6366F1; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; }
    .support-options { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 25px 0; }
    .support-card { background: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 8px; text-align: center; }
    .contact-info { background: #F0F9FF; border-left: 4px solid #6366F1; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> We're Here to Help</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">OxiWorld Customer Support</p>
    </div>
    <div class="content">
      <div class="support-badge"> Support Response</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">{{support.message}}</p>
      
      <div class="contact-info">
        <p style="margin: 0; color: #3730A3; font-weight: 600;"> Ticket Information:</p>
        <ul style="margin: 10px 0 0; color: #3730A3; padding-left: 20px; list-style: none;">
          <li><strong>Ticket ID:</strong> {{support.ticket_id}}</li>
          <li><strong>Subject:</strong> {{support.subject}}</li>
          <li><strong>Status:</strong> {{support.status}}</li>
          <li><strong>Priority:</strong> {{support.priority}}</li>
        </ul>
      </div>

      <div class="support-options">
        <div class="support-card">
          <div style="font-size: 24px; margin-bottom: 10px;"></div>
          <div style="font-weight: 600; color: #1F2937;">Live Chat</div>
          <div style="font-size: 12px; color: #6B7280;">Instant support 24/7</div>
        </div>
        <div class="support-card">
          <div style="font-size: 24px; margin-bottom: 10px;"></div>
          <div style="font-weight: 600; color: #1F2937;">Email Support</div>
          <div style="font-size: 12px; color: #6B7280;">Response within 4 hours</div>
        </div>
        <div class="support-card">
          <div style="font-size: 24px; margin-bottom: 10px;"></div>
          <div style="font-weight: 600; color: #1F2937;">Help Center</div>
          <div style="font-size: 12px; color: #6B7280;">Self-service resources</div>
        </div>
        <div class="support-card">
          <div style="font-size: 24px; margin-bottom: 10px;"></div>
          <div style="font-weight: 600; color: #1F2937;">Video Tutorials</div>
          <div style="font-size: 12px; color: #6B7280;">Step-by-step guides</div>
        </div>
      </div>

      <a href="{{custom.support_url}}" class="help-button">Visit Support Center</a>
      
      <div style="background: #DBEAFE; border: 1px solid #3B82F6; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #1E40AF; font-size: 14px;"><strong> Quick Tip:</strong> For faster resolution, please include your account email and describe the issue in detail when contacting support.</p>
      </div>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">Our support team is dedicated to helping you succeed. Don't hesitate to reach out whenever you need assistance!</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Here to help,<br><strong>The OxiWorld Support Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Support available 24/7 | <a href="{{custom.help_url}}" style="color: #64748B;">Help Center</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: '{{support.subject}} - OxiWorld Support [Ticket #{{support.ticket_id}}]',
    text: `Hi {{user.first_name}},

 OxiWorld Customer Support

{{support.message}}

 Ticket Information:
• Ticket ID: {{support.ticket_id}}
• Subject: {{support.subject}}
• Status: {{support.status}}
• Priority: {{support.priority}}

Support Options:
 Live Chat - Instant support 24/7
 Email Support - Response within 4 hours  
 Help Center - Self-service resources
 Video Tutorials - Step-by-step guides

Visit Support Center: {{custom.support_url}}

 Quick Tip: For faster resolution, include your account email and describe the issue in detail.

Our support team is dedicated to helping you succeed!

Here to help,
The OxiWorld Support Team

© 2025 OxiWorld. All rights reserved.`
  },

  subscription_success: {
    name: 'Subscription Success - Payment Confirmation',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #10B981; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .success-badge { background: #D1FAE5; color: #065F46; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .amount { font-size: 28px; font-weight: bold; color: #10B981; text-align: center; margin: 20px 0; }
    .plan-details { background: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .button { background: #10B981; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .benefits { background: #F0FDF4; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .benefit-item { margin: 10px 0; display: flex; align-items: center; }
    .checkmark { color: #10B981; font-weight: bold; margin-right: 10px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 28px;"> Payment Successful!</h1>
      <p style="margin: 10px 0 0; opacity: 0.9; font-size: 16px;">Welcome to Premium Trading</p>
    </div>
    <div class="content">
      <div class="success-badge"> Payment Confirmed</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Congratulations! Your subscription payment has been successfully processed and your premium account is now active.</p>
      
      <div class="amount">{{subscription.currency}} {{subscription.amount_paid}}</div>
      
      <div class="plan-details">
        <h3 style="margin: 0 0 15px; color: #065F46;"> Subscription Details</h3>
        <p style="margin: 5px 0; color: #374151;"><strong>Plan:</strong> {{subscription.plan_type}} Subscription</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Billing Cycle:</strong> {{subscription.billing_cycle}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Next Billing:</strong> {{subscription.next_billing_date}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Payment Method:</strong> {{subscription.payment_method}}</p>
      </div>

      <div class="benefits">
        <h3 style="margin: 0 0 15px; color: #065F46;"> Your Premium Benefits</h3>
        <div class="benefit-item"><span class="checkmark"></span> <span>Access to all premium courses and content</span></div>
        <div class="benefit-item"><span class="checkmark"></span> <span>Daily market analysis and trading signals</span></div>
        <div class="benefit-item"><span class="checkmark"></span> <span>Live trading sessions with expert traders</span></div>
        <div class="benefit-item"><span class="checkmark"></span> <span>Priority customer support</span></div>
        <div class="benefit-item"><span class="checkmark"></span> <span>Advanced trading tools and indicators</span></div>
        <div class="benefit-item"><span class="checkmark"></span> <span>Exclusive community access</span></div>
      </div>

      <a href="{{custom.dashboard_url}}" class="button" style="display: block; text-align: center; text-decoration: none; color: white;">Access Your Premium Dashboard</a>
      
      <div style="background: #DBEAFE; border: 1px solid #3B82F6; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #1E40AF; font-size: 14px;"><strong> Getting Started:</strong> Check out your premium dashboard to explore new features and start your advanced trading journey!</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Thank you for choosing OxiWorld Premium. We're excited to support your trading success!</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Welcome to the next level,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Questions about your subscription? <a href="{{custom.support_url}}" style="color: #64748B;">Contact Support</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Welcome to OxiWorld Premium - Payment Confirmed for {{subscription.plan_type}}',
    text: `Hi {{user.first_name}},

 Payment Successful!

Congratulations! Your subscription payment has been successfully processed and your premium account is now active.

Amount Paid: {{subscription.currency}} {{subscription.amount_paid}}

 Subscription Details:
• Plan: {{subscription.plan_type}} Subscription
• Billing Cycle: {{subscription.billing_cycle}}
• Next Billing: {{subscription.next_billing_date}}
• Payment Method: {{subscription.payment_method}}

 Your Premium Benefits:
 Access to all premium courses and content
 Daily market analysis and trading signals
 Live trading sessions with expert traders
 Priority customer support
 Advanced trading tools and indicators
 Exclusive community access

Access Your Premium Dashboard: {{custom.dashboard_url}}

 Getting Started: Check out your premium dashboard to explore new features and start your advanced trading journey!

Thank you for choosing OxiWorld Premium. We're excited to support your trading success!

Welcome to the next level,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.`
  },

  payment_failed: {
    name: 'Payment Failed - Action Required',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #EF4444; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .alert-badge { background: #FEE2E2; color: #DC2626; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .retry-button { background: #EF4444; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .payment-info { background: #FEF2F2; border-left: 4px solid #EF4444; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .help-section { background: #F9FAFB; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> Payment Failed</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Action required to maintain access</p>
    </div>
    <div class="content">
      <div class="alert-badge"> Payment Issue Detected</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We were unable to process your recent payment for your OxiWorld subscription. To continue enjoying uninterrupted access to your trading education, please update your payment method.</p>
      
      <div class="payment-info">
        <p style="margin: 0; color: #DC2626; font-weight: 600;"> Payment Details:</p>
        <ul style="margin: 10px 0 0; color: #DC2626; padding-left: 20px; list-style: none;">
          <li><strong>Amount:</strong> {{subscription.currency}} {{subscription.amount_due}}</li>
          <li><strong>Plan:</strong> {{subscription.plan_type}} Subscription</li>
          <li><strong>Attempt Date:</strong> {{payment.failed_date}}</li>
          <li><strong>Reason:</strong> {{payment.failure_reason}}</li>
        </ul>
      </div>

      <div style="background: #FFFBEB; border: 1px solid #F59E0B; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #92400E; font-size: 14px;"><strong> Time Sensitive:</strong> Please update your payment method within 7 days to avoid service interruption.</p>
      </div>

      <a href="{{custom.payment_url}}" class="retry-button" style="display: block; text-align: center; text-decoration: none; color: white;">Update Payment Method</a>
      
      <div class="help-section">
        <h3 style="margin: 0 0 15px; color: #1F2937;"> Need Help?</h3>
        <p style="margin: 0; color: #374151; font-size: 14px;">Common solutions:</p>
        <ul style="margin: 10px 0 0; color: #374151; font-size: 14px; padding-left: 20px;">
          <li>Verify your card details and expiration date</li>
          <li>Ensure sufficient funds are available</li>
          <li>Check with your bank for any restrictions</li>
          <li>Try a different payment method</li>
        </ul>
        <p style="margin: 15px 0 0; color: #374151; font-size: 14px;">Still having issues? <a href="{{custom.support_url}}" style="color: #EF4444;">Contact our support team</a> for immediate assistance.</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We appreciate your prompt attention to this matter and look forward to continuing your trading journey with us.</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Here to help,<br><strong>The OxiWorld Billing Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Questions about billing? <a href="{{custom.billing_support_url}}" style="color: #64748B;">Contact Billing Support</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Action Required: Payment Failed for {{subscription.plan_type}}',
    text: `Hi {{user.first_name}},

 Payment Failed

We were unable to process your recent payment for your OxiWorld subscription. Please update your payment method to continue your access.

 Payment Details:
• Amount: {{subscription.currency}} {{subscription.amount_due}}
• Plan: {{subscription.plan_type}} Subscription
• Attempt Date: {{payment.failed_date}}
• Reason: {{payment.failure_reason}}

 Time Sensitive: Please update your payment method within 7 days to avoid service interruption.

Update Payment Method: {{custom.payment_url}}

 Common Solutions:
• Verify your card details and expiration date
• Ensure sufficient funds are available
• Check with your bank for any restrictions
• Try a different payment method

Still having issues? Contact our support team: {{custom.support_url}}

We appreciate your prompt attention and look forward to continuing your trading journey with us.

Here to help,
The OxiWorld Billing Team

© 2025 OxiWorld. All rights reserved.`
  },

  subscription_expiry: {
    name: 'Subscription Expiry Warning - Urgent Action Required',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #F59E0B; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .expiry-badge { background: #FEF3C7; color: #92400E; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .countdown { font-size: 32px; font-weight: bold; color: #F59E0B; text-align: center; margin: 20px 0; }
    .renew-button { background: #F59E0B; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .benefits-lost { background: #FEF2F2; border-left: 4px solid #EF4444; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> Subscription Expiring Soon</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Don't lose access to premium features</p>
    </div>
    <div class="content">
      <div class="expiry-badge"> Expiration Warning</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Your {{subscription.plan_type}} subscription is about to expire. Don't lose access to the premium trading tools that have been helping you succeed!</p>
      
      <div class="countdown">{{subscription.days_remaining}} Days Left</div>
      
      <div class="benefits-lost">
        <p style="margin: 0; color: #DC2626; font-weight: 600;"> What you'll lose access to:</p>
        <ul style="margin: 10px 0 0; color: #DC2626; padding-left: 20px;">
          <li>Premium trading courses and advanced strategies</li>
          <li>Daily market analysis and profitable signals</li>
          <li>Live trading sessions with expert traders</li>
          <li>Priority customer support</li>
          <li>Exclusive community discussions</li>
        </ul>
      </div>

      <div style="background: #ECFDF5; border: 1px solid #10B981; padding: 15px; border-radius: 6px; margin: 20px 0; text-align: center;">
        <p style="margin: 0; color: #065F46; font-weight: 600;"> Renew now and continue your trading success!</p>
        <p style="margin: 10px 0 0; color: #065F46; font-size: 14px;">Keep building your financial freedom with OxiWorld Premium</p>
      </div>

      <a href="{{custom.renewal_url}}" class="renew-button" style="display: block; text-align: center; text-decoration: none; color: white;">Renew My Subscription</a>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Don't let this opportunity slip away. Renew today and keep growing your trading expertise!</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">To your continued success,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Questions? <a href="{{custom.support_url}}" style="color: #64748B;">Contact Support</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Your {{subscription.plan_type}} Subscription Expires in {{subscription.days_remaining}} Days',
    text: `Hi {{user.first_name}},

 Subscription Expiring Soon

Your {{subscription.plan_type}} subscription is about to expire in {{subscription.days_remaining}} days.

 What you'll lose access to:
• Premium trading courses and advanced strategies
• Daily market analysis and profitable signals
• Live trading sessions with expert traders
• Priority customer support
• Exclusive community discussions

 Renew now and continue your trading success!

Renew My Subscription: {{custom.renewal_url}}

Don't let this opportunity slip away. Keep growing your trading expertise!

To your continued success,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.`
  },

  subscription_renewal: {
    name: 'Subscription Renewal Confirmation - Welcome Back',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #10B981; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .renewal-badge { background: #D1FAE5; color: #065F46; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .renewal-details { background: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .access-button { background: #10B981; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .whats-new { background: #F0FDF4; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 28px;"> Renewal Successful!</h1>
      <p style="margin: 10px 0 0; opacity: 0.9; font-size: 16px;">Welcome back to OxiWorld Premium</p>
    </div>
    <div class="content">
      <div class="renewal-badge"> Subscription Renewed</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Great news! Your {{subscription.plan_type}} subscription has been successfully renewed. Your premium access continues without interruption.</p>
      
      <div class="renewal-details">
        <h3 style="margin: 0 0 15px; color: #065F46;"> Renewal Details</h3>
        <p style="margin: 5px 0; color: #374151;"><strong>Plan:</strong> {{subscription.plan_type}} Premium</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Renewal Date:</strong> {{subscription.renewal_date}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Next Billing:</strong> {{subscription.next_billing_date}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Amount:</strong> {{subscription.currency}} {{subscription.amount}}</p>
      </div>

      <div class="whats-new">
        <h3 style="margin: 0 0 15px; color: #065F46;"> What's New This Month</h3>
        <ul style="margin: 0; color: #374151; padding-left: 20px;">
          <li>Advanced risk management calculator</li>
          <li>New EUR/USD trading strategy course</li>
          <li>Enhanced mobile trading app features</li>
          <li>Weekly live Q&A sessions with pro traders</li>
        </ul>
      </div>

      <a href="{{custom.dashboard_url}}" class="access-button" style="display: block; text-align: center; text-decoration: none; color: white;">Access Your Premium Dashboard</a>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Thank you for continuing your journey with OxiWorld. Here's to another successful period of trading and learning!</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Happy trading,<br><strong>The OxiWorld Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Manage your subscription: <a href="{{custom.billing_url}}" style="color: #64748B;">Billing Settings</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Subscription Renewed Successfully - {{subscription.plan_type}}',
    text: `Hi {{user.first_name}},

 Renewal Successful!

Your {{subscription.plan_type}} subscription has been successfully renewed. Your premium access continues without interruption.

 Renewal Details:
• Plan: {{subscription.plan_type}} Premium
• Renewal Date: {{subscription.renewal_date}}
• Next Billing: {{subscription.next_billing_date}}
• Amount: {{subscription.currency}} {{subscription.amount}}

 What's New This Month:
• Advanced risk management calculator
• New EUR/USD trading strategy course
• Enhanced mobile trading app features
• Weekly live Q&A sessions with pro traders

Access Your Premium Dashboard: {{custom.dashboard_url}}

Thank you for continuing your journey with OxiWorld!

Happy trading,
The OxiWorld Team

© 2025 OxiWorld. All rights reserved.`
  },

  payment_success: {
    name: 'Payment Success - Transaction Confirmation',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #10B981; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .success-badge { background: #D1FAE5; color: #065F46; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .payment-amount { font-size: 32px; font-weight: bold; color: #10B981; text-align: center; margin: 20px 0; }
    .transaction-details { background: #ECFDF5; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .receipt-button { background: #10B981; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> Payment Successful!</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Transaction completed successfully</p>
    </div>
    <div class="content">
      <div class="success-badge"> Payment Confirmed</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Your payment has been processed successfully. Thank you for your purchase!</p>
      
      <div class="payment-amount">{{payment.currency}} {{payment.amount}}</div>
      
      <div class="transaction-details">
        <h3 style="margin: 0 0 15px; color: #065F46;"> Transaction Details</h3>
        <p style="margin: 5px 0; color: #374151;"><strong>Transaction ID:</strong> {{payment.transaction_id}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Date:</strong> {{payment.date}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Payment Method:</strong> {{payment.method}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Description:</strong> {{payment.description}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Status:</strong> <span style="color: #10B981; font-weight: 600;">Completed</span></p>
      </div>

      <div style="background: #DBEAFE; border: 1px solid #3B82F6; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #1E40AF; font-size: 14px;"><strong> Receipt:</strong> A detailed receipt has been sent to your email and is available in your account dashboard.</p>
      </div>

      <a href="{{custom.receipt_url}}" class="receipt-button">View Receipt</a>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">If you have any questions about this transaction, please don't hesitate to contact our support team.</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Thank you for choosing OxiWorld,<br><strong>The OxiWorld Billing Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Questions about billing? <a href="{{custom.billing_support_url}}" style="color: #64748B;">Contact Support</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Payment Successful - {{payment.amount}} {{payment.currency}}',
    text: `Hi {{user.first_name}},

 Payment Successful!

Your payment has been processed successfully. Thank you for your purchase!

Amount: {{payment.currency}} {{payment.amount}}

 Transaction Details:
• Transaction ID: {{payment.transaction_id}}
• Date: {{payment.date}}
• Payment Method: {{payment.method}}
• Description: {{payment.description}}
• Status: Completed

 Receipt: A detailed receipt has been sent to your email and is available in your account dashboard.

View Receipt: {{custom.receipt_url}}

If you have any questions about this transaction, please contact our support team.

Thank you for choosing OxiWorld,
The OxiWorld Billing Team

© 2025 OxiWorld. All rights reserved.`
  },

  payment_refunded: {
    name: 'Payment Refund Processed - Confirmation',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #3B82F6; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .refund-badge { background: #DBEAFE; color: #1E40AF; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .refund-amount { font-size: 32px; font-weight: bold; color: #3B82F6; text-align: center; margin: 20px 0; }
    .refund-details { background: #F0F9FF; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .timeline-info { background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> Refund Processed</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Your refund is on the way</p>
    </div>
    <div class="content">
      <div class="refund-badge"> Refund Confirmed</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Your refund request has been processed successfully. The refunded amount will be returned to your original payment method.</p>
      
      <div class="refund-amount">{{refund.currency}} {{refund.amount}}</div>
      
      <div class="refund-details">
        <h3 style="margin: 0 0 15px; color: #1E40AF;"> Refund Details</h3>
        <p style="margin: 5px 0; color: #374151;"><strong>Refund ID:</strong> {{refund.refund_id}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Original Transaction:</strong> {{refund.original_transaction_id}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Refund Date:</strong> {{refund.processed_date}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Reason:</strong> {{refund.reason}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Refund Method:</strong> {{refund.method}}</p>
      </div>

      <div class="timeline-info">
        <p style="margin: 0; color: #92400E; font-weight: 600;"> Processing Timeline:</p>
        <ul style="margin: 10px 0 0; color: #92400E; padding-left: 20px;">
          <li>Credit/Debit Cards: 3-5 business days</li>
          <li>PayPal: 1-2 business days</li>
          <li>Bank Transfer: 5-7 business days</li>
        </ul>
      </div>

      <div style="background: #DBEAFE; border: 1px solid #3B82F6; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #1E40AF; font-size: 14px;"><strong> Track Status:</strong> You can track your refund status in your account dashboard or contact support for updates.</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">If you don't see the refund in your account within the expected timeframe, please contact our support team for assistance.</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Thank you for your patience,<br><strong>The OxiWorld Billing Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Questions about your refund? <a href="{{custom.billing_support_url}}" style="color: #64748B;">Contact Support</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Refund Processed - {{refund.amount}} {{refund.currency}}',
    text: `Hi {{user.first_name}},

 Refund Processed

Your refund request has been processed successfully. The refunded amount will be returned to your original payment method.

Refund Amount: {{refund.currency}} {{refund.amount}}

 Refund Details:
• Refund ID: {{refund.refund_id}}
• Original Transaction: {{refund.original_transaction_id}}
• Refund Date: {{refund.processed_date}}
• Reason: {{refund.reason}}
• Refund Method: {{refund.method}}

 Processing Timeline:
• Credit/Debit Cards: 3-5 business days
• PayPal: 1-2 business days
• Bank Transfer: 5-7 business days

 Track Status: You can track your refund status in your account dashboard or contact support for updates.

If you don't see the refund within the expected timeframe, please contact our support team.

Thank you for your patience,
The OxiWorld Billing Team

© 2025 OxiWorld. All rights reserved.`
  },

  telegram_added: {
    name: 'Telegram Group Access Granted - Welcome',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #0088CC; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .telegram-badge { background: #E1F5FE; color: #0277BD; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .join-button { background: #0088CC; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .group-features { background: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .feature-item { margin: 10px 0; display: flex; align-items: center; }
    .telegram-icon { color: #0088CC; font-weight: bold; margin-right: 10px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> Welcome to Telegram!</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Premium group access granted</p>
    </div>
    <div class="content">
      <div class="telegram-badge"> Telegram Access Granted</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Great news! You've been granted access to our exclusive OxiWorld Premium Telegram group: <strong>{{telegram.group_name}}</strong></p>
      
      <div class="group-features">
        <h3 style="margin: 0 0 15px; color: #1F2937;"> What's inside the group:</h3>
        <div class="feature-item"><span class="telegram-icon"></span> <span>Real-time trading discussions</span></div>
        <div class="feature-item"><span class="telegram-icon"></span> <span>Exclusive market analysis</span></div>
        <div class="feature-item"><span class="telegram-icon"></span> <span>Live trading signals and alerts</span></div>
        <div class="feature-item"><span class="telegram-icon"></span> <span>Direct access to expert traders</span></div>
        <div class="feature-item"><span class="telegram-icon"></span> <span>Educational resources and tips</span></div>
        <div class="feature-item"><span class="telegram-icon"></span> <span>Success stories and strategies</span></div>
      </div>

      <div style="background: #FEF3C7; border: 1px solid #F59E0B; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #92400E; font-size: 14px;"><strong> Group Guidelines:</strong> Please respect all members, avoid spam, and keep discussions trading-related. Enjoy the community!</p>
      </div>

      <a href="{{telegram.join_url}}" class="join-button" style="display: block; text-align: center; text-decoration: none; color: white;">Join Telegram Group</a>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">If you have trouble joining, make sure you have Telegram installed and try the link again. Contact support if you need assistance.</p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Welcome to the community!<br><strong>The OxiWorld Community Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Having issues? <a href="{{custom.support_url}}" style="color: #64748B;">Contact Support</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Welcome to OxiWorld Premium Telegram - {{telegram.group_name}}',
    text: `Hi {{user.first_name}},

 Welcome to Telegram!

You've been granted access to our exclusive OxiWorld Premium Telegram group: {{telegram.group_name}}

 What's inside the group:
 Real-time trading discussions
 Exclusive market analysis
 Live trading signals and alerts
 Direct access to expert traders
 Educational resources and tips
 Success stories and strategies

 Group Guidelines: Please respect all members, avoid spam, and keep discussions trading-related.

Join Telegram Group: {{telegram.join_url}}

If you have trouble joining, make sure you have Telegram installed and try the link again.

Welcome to the community!
The OxiWorld Community Team

© 2025 OxiWorld. All rights reserved.`
  },

  telegram_removed: {
    name: 'Telegram Group Access Removed - Update',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #6B7280; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .removal-badge { background: #F3F4F6; color: #4B5563; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .upgrade-button { background: #4F46E5; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .reason-info { background: #F9FAFB; border-left: 4px solid #6B7280; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> Telegram Access Update</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Group access changes</p>
    </div>
    <div class="content">
      <div class="removal-badge"> Access Updated</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We're writing to inform you that your access to the Telegram group <strong>{{telegram.group_name}}</strong> has been updated.</p>
      
      <div class="reason-info">
        <p style="margin: 0; color: #4B5563; font-weight: 600;"> Reason for change:</p>
        <p style="margin: 10px 0 0; color: #4B5563;">{{telegram.removal_reason}}</p>
      </div>

      <div style="background: #EDE9FE; border: 1px solid #8B5CF6; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #5B21B6; font-weight: 600;"> Want to regain access?</p>
        <p style="margin: 10px 0 0; color: #5B21B6; font-size: 14px;">Upgrade to premium or resolve any subscription issues to rejoin our exclusive Telegram communities.</p>
      </div>

      <a href="{{custom.upgrade_url}}" class="upgrade-button" style="display: block; text-align: center; text-decoration: none; color: white;">Restore Access</a>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">If you believe this was done in error or have questions about your account status, please don't hesitate to contact our support team.</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Community Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Questions? <a href="{{custom.support_url}}" style="color: #64748B;">Contact Support</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'Telegram Access Update - {{telegram.group_name}}',
    text: `Hi {{user.first_name}},

 Telegram Access Update

Your access to the Telegram group {{telegram.group_name}} has been updated.

 Reason for change:
{{telegram.removal_reason}}

 Want to regain access? Upgrade to premium or resolve any subscription issues to rejoin our exclusive Telegram communities.

Restore Access: {{custom.upgrade_url}}

If you believe this was done in error or have questions, please contact our support team.

Best regards,
The OxiWorld Community Team

© 2025 OxiWorld. All rights reserved.`
  },

  signin_notification: {
    name: 'Sign-in Security Notification - New Device Alert',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #1E40AF; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .security-badge { background: #DBEAFE; color: #1E40AF; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .signin-details { background: #F0F9FF; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .secure-button { background: #DC2626; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .location-info { background: #ECFDF5; border-left: 4px solid #10B981; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> New Sign-in Detected</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Account security notification</p>
    </div>
    <div class="content">
      <div class="security-badge"> Security Alert</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">We detected a new sign-in to your OxiWorld account. If this was you, no action is needed. If this wasn't you, please secure your account immediately.</p>
      
      <div class="signin-details">
        <h3 style="margin: 0 0 15px; color: #1E40AF;"> Sign-in Details</h3>
        <p style="margin: 5px 0; color: #374151;"><strong>Date & Time:</strong> {{signin.datetime}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Device:</strong> {{signin.device}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>Browser:</strong> {{signin.browser}}</p>
        <p style="margin: 5px 0; color: #374151;"><strong>IP Address:</strong> {{signin.ip_address}}</p>
      </div>

      <div class="location-info">
        <p style="margin: 0; color: #065F46; font-weight: 600;"> Approximate Location:</p>
        <p style="margin: 10px 0 0; color: #065F46;">{{signin.location}}</p>
      </div>

      <div style="background: #FEE2E2; border: 1px solid #EF4444; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #DC2626; font-weight: 600;"> Wasn't you?</p>
        <p style="margin: 10px 0 0; color: #DC2626; font-size: 14px;">If you didn't sign in, someone may have access to your account. Secure it immediately by changing your password.</p>
      </div>

      <a href="{{custom.security_url}}" class="secure-button" style="display: block; text-align: center; text-decoration: none; color: white;">Secure My Account</a>
      
      <div style="background: #F0FDF4; border: 1px solid #22C55E; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #166534; font-size: 14px;"><strong> This was me?</strong> No action needed. You can ignore this email if you recognize this sign-in activity.</p>
      </div>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Stay secure,<br><strong>The OxiWorld Security Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">Security questions? <a href="{{custom.security_support_url}}" style="color: #64748B;">Contact Security Team</a></p>
    </div>
  </div>
</body>
</html>`,
    subject: 'New Sign-in Detected - {{user.first_name}}, Was This You?',
    text: `Hi {{user.first_name}},

 New Sign-in Detected

We detected a new sign-in to your OxiWorld account. If this was you, no action is needed.

 Sign-in Details:
• Date & Time: {{signin.datetime}}
• Device: {{signin.device}}
• Browser: {{signin.browser}}
• IP Address: {{signin.ip_address}}

 Approximate Location: {{signin.location}}

 Wasn't you? If you didn't sign in, someone may have access to your account. Secure it immediately by changing your password.

Secure My Account: {{custom.security_url}}

 This was me? No action needed. You can ignore this email if you recognize this activity.

Stay secure,
The OxiWorld Security Team

© 2025 OxiWorld. All rights reserved.`
  },

  email_verification: {
    name: 'Email Address Verification - Account Security',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #1E40AF; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .verification-badge { background: #DBEAFE; color: #1E40AF; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .verify-button { background: #1E40AF; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .security-info { background: #F0F9FF; border-left: 4px solid #1E40AF; padding: 15px 20px; margin: 20px 0; border-radius: 4px; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;"> Verify Your Email</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">Secure your OxiWorld account</p>
    </div>
    <div class="content">
      <div class="verification-badge"> Email Verification Required</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">To complete your OxiWorld account setup and ensure the security of your trading account, please verify your email address.</p>
      
      <div class="security-info">
        <p style="margin: 0; color: #1E40AF; font-weight: 600;">Why verify your email?</p>
        <ul style="margin: 10px 0 0; color: #374151; padding-left: 20px;">
          <li>Secure account recovery options</li>
          <li>Important trading alerts and notifications</li>
          <li>Account security confirmations</li>
        </ul>
      </div>

      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Click the button below to verify your email address:</p>
      <a href="{{custom.verification_url}}" class="verify-button" style="display: block; text-align: center; text-decoration: none; color: white;">Verify Email Address</a>
      
      <div style="background: #FFFBEB; border: 1px solid #FCD34D; padding: 15px; border-radius: 6px; margin: 20px 0;">
        <p style="margin: 0; color: #92400E; font-size: 14px;"><strong> Time Sensitive:</strong> This verification link will expire in 24 hours for security reasons.</p>
      </div>
      
      <p style="font-size: 14px; line-height: 1.6; color: #6B7280;">If the button doesn't work, copy and paste this link into your browser:<br>
      <span style="word-break: break-all; color: #1E40AF;">{{custom.verification_url}}</span></p>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Best regards,<br><strong>The OxiWorld Security Team</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">If you didn't create an account with us, please ignore this email.</p>
    </div>
  </div>
</body>
</html>`,
    subject: ' Verify Your OxiWorld Account - Action Required',
    text: `Hi {{user.first_name}},

 Email Verification Required

To complete your OxiWorld account setup and ensure security, please verify your email address.

Why verify your email?
• Secure account recovery options
• Important trading alerts and notifications
• Account security confirmations

Verify your email: {{custom.verification_url}}

 Time Sensitive: This verification link will expire in 24 hours for security reasons.

Best regards,
The OxiWorld Security Team

© 2025 OxiWorld. All rights reserved.
If you didn't create an account with us, please ignore this email.`
  },

  custom: {
    name: 'Custom Template - Flexible Content',
    html: `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    .email-container { max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
    .header { background: #6366F1; color: white; padding: 40px 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { padding: 40px 30px; background: white; }
    .custom-badge { background: #E0E7FF; color: #3730A3; padding: 10px 20px; border-radius: 25px; display: inline-block; margin: 20px 0; font-size: 14px; font-weight: 600; }
    .action-button { background: #6366F1; color: white; padding: 16px 32px; text-decoration: none; border-radius: 8px; display: inline-block; margin: 25px 0; font-weight: 600; font-size: 16px; }
    .content-section { background: #F8FAFC; padding: 20px; border-radius: 8px; margin: 20px 0; }
    .footer { background: #F1F5F9; padding: 30px 20px; text-align: center; color: #64748B; font-size: 14px; border-radius: 0 0 8px 8px; }
  </style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1 style="margin: 0; font-size: 26px;">{{custom.title}}</h1>
      <p style="margin: 10px 0 0; opacity: 0.9;">{{custom.subtitle}}</p>
    </div>
    <div class="content">
      <div class="custom-badge"> {{custom.badge_text}}</div>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">Hi {{user.first_name}},</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">{{custom.intro_message}}</p>
      
      <div class="content-section">
        <h3 style="margin: 0 0 15px; color: #1F2937;">{{custom.section_title}}</h3>
        <div style="color: #374151; line-height: 1.6;">{{custom.section_content}}</div>
      </div>

      {{custom.additional_content}}

      <a href="{{custom.action_url}}" class="action-button" style="display: block; text-align: center; text-decoration: none; color: white;">{{custom.action_text}}</a>
      
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">{{custom.closing_message}}</p>
      <p style="font-size: 16px; line-height: 1.6; color: #374151;">{{custom.signature}}<br><strong>{{custom.sender_name}}</strong></p>
    </div>
    <div class="footer">
      <p style="margin: 0;">© 2025 OxiWorld. All rights reserved.</p>
      <p style="margin: 10px 0 0; font-size: 12px;">{{custom.footer_text}}</p>
    </div>
  </div>
</body>
</html>`,
    subject: '{{custom.subject}} - OxiWorld',
    text: `Hi {{user.first_name}},

{{custom.title}}

{{custom.intro_message}}

{{custom.section_title}}
{{custom.section_content}}

{{custom.additional_content}}

{{custom.action_text}}: {{custom.action_url}}

{{custom.closing_message}}

{{custom.signature}}
{{custom.sender_name}}

© 2025 OxiWorld. All rights reserved.`
  }
};

// Comprehensive smart suggestions for ALL template types
const SMART_SUGGESTIONS = {
  welcome: {
    name: 'Welcome Email Template',
    description: 'Sent to new users when they sign up for an account',
    from_name: 'OxiWorld Team',
    subject_template: 'Welcome to OxiWorld, {{user.first_name}}!  Your Trading Journey Starts Here',
  },
  subscription_success: {
    name: 'Subscription Success Notification',
    description: 'Sent when a subscription payment is successfully processed',
    from_name: 'OxiWorld Billing Team',
    subject_template: ' Welcome to OxiWorld Premium! Payment Confirmed - {{subscription.plan_type}}',
  },
  subscription_expiry: {
    name: 'Subscription Expiry Warning',
    description: 'Sent to warn users about upcoming subscription expiration',
    from_name: 'OxiWorld Team',
    subject_template: ' Your {{subscription.plan_type}} Subscription Expires Soon - Renew Now',
  },
  subscription_renewal: {
    name: 'Subscription Renewal Confirmation',
    description: 'Sent when a subscription is successfully renewed',
    from_name: 'OxiWorld Billing Team',
    subject_template: ' Subscription Renewed Successfully - {{subscription.plan_type}}',
  },
  payment_success: {
    name: 'Payment Success Confirmation',
    description: 'Sent when any payment is successfully processed',
    from_name: 'OxiWorld Billing Team',
    subject_template: ' Payment Successful - {{payment.amount}} {{payment.currency}}',
  },
  payment_failed: {
    name: 'Payment Failed Notification',
    description: 'Sent when a payment fails and requires user action',
    from_name: 'OxiWorld Billing Team',
    subject_template: ' Action Required: Payment Failed for {{subscription.plan_type}} - Update Now',
  },
  payment_refunded: {
    name: 'Payment Refund Notification',
    description: 'Sent when a payment refund is processed',
    from_name: 'OxiWorld Billing Team',
    subject_template: ' Refund Processed - {{refund.amount}} {{refund.currency}}',
  },
  renewal_reminder: {
    name: 'Subscription Renewal Reminder',
    description: 'Sent to remind users about upcoming subscription renewals',
    from_name: 'OxiWorld Team',
    subject_template: ' {{user.first_name}}, Ready to Continue Your Trading Journey?',
  },
  telegram_added: {
    name: 'Telegram Group Access Granted',
    description: 'Sent when user is added to premium Telegram groups',
    from_name: 'OxiWorld Community Team',
    subject_template: ' Welcome to OxiWorld Premium Telegram - {{telegram.group_name}}',
  },
  telegram_removed: {
    name: 'Telegram Group Access Removed',
    description: 'Sent when user is removed from Telegram groups',
    from_name: 'OxiWorld Community Team',
    subject_template: ' Telegram Access Update - {{telegram.group_name}}',
  },
  signin_notification: {
    name: 'Sign-in Security Notification',
    description: 'Sent when user signs in from new device or location',
    from_name: 'OxiWorld Security Team',
    subject_template: ' New Sign-in Detected - {{user.first_name}}, Was This You?',
  },
  password_reset: {
    name: 'Password Reset Request',
    description: 'Sent when user requests to reset their password',
    from_name: 'OxiWorld Security Team',
    subject_template: ' Reset Your OxiWorld Password - Expires in 1 Hour',
  },
  email_verification: {
    name: 'Email Address Verification',
    description: 'Sent to verify user email addresses for account security',
    from_name: 'OxiWorld Security Team',
    subject_template: ' Verify Your OxiWorld Account - Action Required',
  },
  notification: {
    name: 'General Account Notification',
    description: 'Sent for general account updates and important announcements',
    from_name: 'OxiWorld Team',
    subject_template: ' {{notification.title}} - OxiWorld Account Update',
  },
  marketing: {
    name: 'Marketing Campaign Email',
    description: 'Sent for promotional offers and marketing campaigns',
    from_name: 'OxiWorld Marketing Team',
    subject_template: ' {{user.first_name}}, Unlock 50% OFF Premium Trading - Limited Time!',
  },
  newsletter: {
    name: 'Weekly Newsletter',
    description: 'Sent for weekly market insights and educational content',
    from_name: 'OxiWorld Research Team',
    subject_template: ' Weekly Market Report: {{newsletter.week_date}} - Key Opportunities Inside',
  },
  reminder: {
    name: 'Account Activity Reminder',
    description: 'Sent to re-engage inactive users and encourage activity',
    from_name: 'OxiWorld Team',
    subject_template: ' {{user.first_name}}, Ready to Continue Your Trading Journey?',
  },
  support: {
    name: 'Customer Support Response',
    description: 'Sent for customer support responses and help tickets',
    from_name: 'OxiWorld Support Team',
    subject_template: ' {{support.subject}} - OxiWorld Support [Ticket #{{support.ticket_id}}]',
  },
  custom: {
    name: 'Custom Template',
    description: 'Custom email template for specific use cases',
    from_name: 'OxiWorld Team',
    subject_template: 'OxiWorld - {{custom.subject}}',
  }
};

interface EnhancedEmailTemplateEditorProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (template: EmailTemplate) => void;
  template?: EmailTemplate | null;
  templateTypes: EmailTemplateType[];
}

export default function EnhancedEmailTemplateEditor({
  isOpen,
  onClose,
  onSave,
  template,
  templateTypes
}: EnhancedEmailTemplateEditorProps) {
  const [formData, setFormData] = useState<EmailTemplate>({
    name: '',
    template_type: '',
    template_type_display: '',
    status: 'draft',
    subject_template: '',
    html_content: '',
    text_content: '',
    description: '',
    is_default: false,
    from_email: '',
    from_name: ''
  });

  const [availableVariables, setAvailableVariables] = useState<Record<string, string>>({});
  const [showVariables, setShowVariables] = useState(false);
  const [activeTab, setActiveTab] = useState<'builder' | 'html' | 'text' | 'preview'>('builder');
  const [previewData, setPreviewData] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);

  // Load form data when template changes
  useEffect(() => {
    if (template) {
      setFormData({
        ...template,
        from_email: template.from_email || '',
        from_name: template.from_name || ''
      });
      setAvailableVariables(template.available_variables || {});
    } else {
      setFormData({
        name: '',
        template_type: '',
        template_type_display: '',
        status: 'draft',
        subject_template: '',
        html_content: '',
        text_content: '',
        description: '',
        is_default: false,
        from_email: '',
        from_name: ''
      });
      setAvailableVariables({});
    }
    setErrors({});
  }, [template]);

  // Auto-fill suggestions when template type changes
  useEffect(() => {
    if (formData.template_type && !template) {
      applySuggestions(formData.template_type);
    }
  }, [formData.template_type, template]);

  const applySuggestions = (templateType: string) => {
    const suggestions = SMART_SUGGESTIONS[templateType as keyof typeof SMART_SUGGESTIONS];
    if (suggestions) {
      setFormData(prev => ({
        ...prev,
        ...suggestions,
        template_type_display: templateTypes.find(t => t.value === templateType)?.label || ''
      }));
    }

    // Load default variables for template type
    const defaultVariables = {
      'user.first_name': 'User\'s first name',
      'user.last_name': 'User\'s last name', 
      'user.email': 'User\'s email address',
    };

    if (templateType.includes('subscription') || templateType.includes('payment')) {
      Object.assign(defaultVariables, {
        'subscription.plan_type': 'Subscription plan type',
        'subscription.amount_paid': 'Amount paid',
        'subscription.currency': 'Currency',
      });
    }

    if (templateType === 'renewal_reminder') {
      Object.assign(defaultVariables, {
        'custom.days_remaining': 'Days until renewal',
        'custom.renewal_link': 'Renewal link URL',
      });
    }

    if (templateType === 'welcome') {
      Object.assign(defaultVariables, {
        'custom.dashboard_url': 'Dashboard URL',
      });
    }

    if (templateType === 'payment_failed') {
      Object.assign(defaultVariables, {
        'custom.payment_url': 'Payment update URL',
      });
    }

    setAvailableVariables(defaultVariables);
  };

  const usePrebuiltTemplate = (templateType: string) => {
    const design = TEMPLATE_DESIGNS[templateType as keyof typeof TEMPLATE_DESIGNS];
    if (design) {
      setFormData(prev => ({
        ...prev,
        html_content: design.html,
        text_content: design.text,
        subject_template: design.subject
      }));
      setShowTemplateSelector(false);
      setActiveTab('builder');
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when field is modified
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const insertVariable = (variable: string) => {
    const variableTag = `{{${variable}}}`;
    
    if (activeTab === 'html') {
      const textarea = document.getElementById('html-content') as HTMLTextAreaElement;
      if (textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const newText = text.substring(0, start) + variableTag + text.substring(end);
        
        setFormData(prev => ({ ...prev, html_content: newText }));
        
        setTimeout(() => {
          textarea.focus();
          textarea.setSelectionRange(start + variableTag.length, start + variableTag.length);
        }, 0);
      }
    } else if (activeTab === 'text') {
      const textarea = document.getElementById('text-content') as HTMLTextAreaElement;
      if (textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const text = textarea.value;
        const newText = text.substring(0, start) + variableTag + text.substring(end);
        
        setFormData(prev => ({ ...prev, text_content: newText }));
        
        setTimeout(() => {
          textarea.focus();
          textarea.setSelectionRange(start + variableTag.length, start + variableTag.length);
        }, 0);
      }
    }
  };

  const generatePreview = async () => {
    if (!formData.template_type) return;
    
    try {
      let templateId = formData.id;
      
      // If creating new template, we need to save it first to preview
      if (!templateId) {
        const tempTemplate = await adminAPI.createEmailTemplate({
          ...formData,
          name: formData.name || 'Preview Template',
          status: 'draft'
        });
        
        if (!tempTemplate.success) {
                    return;
        }
        
        templateId = tempTemplate.template.id;
      }
      
      const response = await adminAPI.previewEmailTemplate(templateId!, {
        sample_data: {
          user: {
            first_name: 'John',
            last_name: 'Doe',
            email: 'john.doe@example.com'
          },
          subscription: {
            plan_type: 'Monthly',
            amount_paid: 99.00,
            currency: 'USD'
          },
          custom: {
            renewal_link: 'https://oxiworld.com/renew/123',
            days_remaining: 7,
            dashboard_url: 'https://oxiworld.com/dashboard',
            payment_url: 'https://oxiworld.com/payment'
          }
        }
      });
      
      if (response.success) {
        setPreviewData(response);
      }
      
      // Clean up temp template if we created one
      if (!formData.id && templateId) {
        await adminAPI.deleteEmailTemplate(templateId);
      }
    } catch (error) {
          }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Template name is required';
    }
    
    if (!formData.template_type) {
      newErrors.template_type = 'Template type is required';
    }
    
    if (!formData.subject_template.trim()) {
      newErrors.subject_template = 'Subject template is required';
    }
    
    if (!formData.html_content.trim()) {
      newErrors.html_content = 'HTML content is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      return;
    }
    
    setSaving(true);
    
    try {
      let response;
      
      // Clean the data - remove frontend-only fields
      const cleanData = {
        name: formData.name,
        template_type: formData.template_type,
        subject_template: formData.subject_template,
        html_content: formData.html_content,
        text_content: formData.text_content,
        description: formData.description,
        status: formData.status,
        is_default: formData.is_default,
        from_email: formData.from_email,
        from_name: formData.from_name,
      };
      
            
      if (template?.id) {
        // Update existing template
        response = await adminAPI.updateEmailTemplate(template.id, cleanData);
      } else {
        // Create new template
        response = await adminAPI.createEmailTemplate(cleanData);
      }
      
      if (response.success) {
        onSave(response.template || formData);
        onClose();
      } else {
        setErrors({ general: response.error || 'Failed to save template' });
      }
    } catch (error) {
            setErrors({ general: error instanceof Error ? error.message : 'Failed to save template' });
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 py-6">
      <div className="relative mx-auto p-6 border w-11/12 max-w-7xl shadow-lg rounded-md bg-white my-6">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b">
          <h3 className="text-lg font-medium text-gray-900">
            {template ? 'Edit Email Template' : 'Create Email Template'}
          </h3>
          <div className="flex items-center space-x-2">
            {!template && (
              <button
                onClick={() => setShowTemplateSelector(!showTemplateSelector)}
                className="px-4 py-2 bg-gray-100 text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
              >
                Use Pre-built Template
              </button>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Pre-built Template Selector */}
        {showTemplateSelector && (
          <div className="mt-4 p-4 bg-gray-100 border border-gray-300 rounded-lg">
            <h4 className="text-md font-medium text-gray-900 mb-3">Choose a Pre-built Template</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(TEMPLATE_DESIGNS).map(([type, design]) => (
                <button
                  key={type}
                  onClick={() => usePrebuiltTemplate(type)}
                  className="p-4 bg-white border border-gray-300 rounded-lg hover:border-gray-400 hover:shadow-md transition-all text-left"
                >
                  <div className="text-sm font-medium text-gray-900">{design.name}</div>
                  <div className="text-xs text-gray-500 mt-1">{type.replace('_', ' ')}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mt-6 grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Panel - Form Fields */}
          <div className="lg:col-span-1 space-y-6">
            {/* Smart Auto-Fill Section */}
            <div className="p-4 bg-gray-100 border border-gray-300 rounded-lg">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Smart Auto-Fill</h4>
              <p className="text-xs text-gray-600 mb-3">Select a template type to auto-fill details</p>
              
              <div>
                <label htmlFor="template_type" className="block text-sm font-medium text-gray-700 mb-1">
                  Template Type *
                </label>
                <select
                  id="template_type"
                  value={formData.template_type}
                  onChange={(e) => handleInputChange('template_type', e.target.value)}
                  className={`w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900 ${
                    errors.template_type ? 'border-red-300' : 'border-gray-300'
                  }`}
                  style={{ color: '#111827' }}
                >
                  <option value="" style={{ color: '#9CA3AF' }}>Select template type...</option>
                  {templateTypes.map(type => (
                    <option key={type.value} value={type.value} style={{ color: '#111827' }}>
                      {type.label}
                    </option>
                  ))}
                </select>
                {errors.template_type && <p className="mt-1 text-sm text-red-600">{errors.template_type}</p>}
              </div>
            </div>

            {/* Basic Info */}
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Template Name *
                </label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className={`mt-1 block w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white ${
                    errors.name ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Enter template name"
                />
                {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
              </div>

              <div>
                <label htmlFor="subject_template" className="block text-sm font-medium text-gray-700">
                  Email Subject *
                </label>
                <input
                  type="text"
                  id="subject_template"
                  value={formData.subject_template}
                  onChange={(e) => handleInputChange('subject_template', e.target.value)}
                  className={`mt-1 block w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white ${
                    errors.subject_template ? 'border-red-300' : 'border-gray-300'
                  }`}
                  placeholder="Enter email subject"
                />
                {errors.subject_template && <p className="mt-1 text-sm text-red-600">{errors.subject_template}</p>}
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  placeholder="Describe when this template is used"
                />
              </div>

              <div>
                <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                  Status
                </label>
                <select
                  id="status"
                  value={formData.status}
                  onChange={(e) => handleInputChange('status', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-gray-900"
                  style={{ color: '#111827' }}
                >
                  <option value="draft" style={{ color: '#111827' }}>Draft</option>
                  <option value="active" style={{ color: '#111827' }}>Active</option>
                  <option value="inactive" style={{ color: '#111827' }}>Inactive</option>
                </select>
              </div>

              <div>
                <label htmlFor="from_name" className="block text-sm font-medium text-gray-700">
                  From Name
                </label>
                <input
                  type="text"
                  id="from_name"
                  value={formData.from_name}
                  onChange={(e) => handleInputChange('from_name', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  placeholder="e.g., OxiWorld Team"
                />
              </div>

              <div>
                <label htmlFor="from_email" className="block text-sm font-medium text-gray-700">
                  From Email
                </label>
                <input
                  type="email"
                  id="from_email"
                  value={formData.from_email}
                  onChange={(e) => handleInputChange('from_email', e.target.value)}
                  className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                  placeholder="Leave blank to use default"
                />
              </div>

              <div>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_default}
                    onChange={(e) => handleInputChange('is_default', e.target.checked)}
                    className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                  />
                  <span className="ml-2 text-sm text-gray-700">Set as default for this type</span>
                </label>
              </div>
            </div>

            {/* Variables Panel */}
            {Object.keys(availableVariables).length > 0 && (
              <div className="border-t pt-4">
                <button
                  type="button"
                  onClick={() => setShowVariables(!showVariables)}
                  className="flex items-center justify-between w-full text-sm font-medium text-gray-700 p-2 bg-gray-50 rounded-lg hover:bg-gray-100"
                >
                  <span> Available Variables</span>
                  <svg
                    className={`w-4 h-4 transform transition-transform ${showVariables ? 'rotate-180' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                {showVariables && (
                  <div className="mt-2 space-y-1 max-h-48 overflow-y-auto">
                    {Object.entries(availableVariables).map(([key, description]) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => insertVariable(key)}
                        className="w-full text-left px-3 py-2 text-xs bg-gray-100 hover:bg-gray-200 rounded border border-gray-300 transition-colors"
                        title={`Click to insert: ${description}`}
                      >
                        <code className="text-gray-900 font-mono">{`{{${key}}}`}</code>
                        <div className="text-gray-600 text-xs mt-1">{description}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Panel - Content Editor */}
          <div className="lg:col-span-3">
            {/* Tabs */}
            <div className="flex border-b border-gray-200 mb-4">
              <button
                onClick={() => setActiveTab('builder')}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'builder'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Visual Builder
              </button>
              <button
                onClick={() => setActiveTab('html')}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'html'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                HTML Code
              </button>
              <button
                onClick={() => setActiveTab('text')}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'text'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Plain Text
              </button>
              <button
                onClick={() => {
                  setActiveTab('preview');
                  generatePreview();
                }}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'preview'
                    ? 'border-gray-900 text-gray-900'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                Preview
              </button>
            </div>

            {/* Tab Content */}
            <div className="min-h-96">
              {activeTab === 'builder' && (
                <div className="space-y-4">
                  <div className="p-6 border-2 border-dashed border-gray-300 rounded-lg text-center bg-gray-50">
                    <div className="mb-4">
                      <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Visual Email Builder</h3>
                    <p className="text-gray-600 mb-4">
                      Choose a pre-built template above or switch to HTML Code tab to create custom designs.
                    </p>
                    {formData.html_content && (
                      <div className="bg-white p-4 rounded border">
                        <iframe
                          srcDoc={formData.html_content}
                          className="w-full h-64 border-0"
                          title="Email Preview"
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'html' && (
                <div>
                  <textarea
                    id="html-content"
                    rows={20}
                    value={formData.html_content}
                    onChange={(e) => handleInputChange('html_content', e.target.value)}
                    className={`w-full border rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white ${
                      errors.html_content ? 'border-red-300' : 'border-gray-300'
                    }`}
                    placeholder="Enter HTML content for the email..."
                  />
                  {errors.html_content && <p className="mt-1 text-sm text-red-600">{errors.html_content}</p>}
                </div>
              )}

              {activeTab === 'text' && (
                <div>
                  <textarea
                    id="text-content"
                    rows={20}
                    value={formData.text_content}
                    onChange={(e) => handleInputChange('text_content', e.target.value)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
                    placeholder="Enter plain text version of the email..."
                  />
                </div>
              )}

              {activeTab === 'preview' && (
                <div className="space-y-4">
                  {previewData ? (
                    <div className="border border-gray-200 rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                        <p className="text-sm text-gray-600">
                          <strong>Subject:</strong> {previewData.subject}
                        </p>
                      </div>
                      <iframe
                        srcDoc={previewData.html_content}
                        className="w-full h-96 border-0"
                        title="Email Preview"
                      />
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-96 border-2 border-dashed border-gray-300 rounded-lg">
                      <div className="text-center">
                        <p className="text-gray-600 mb-4">Preview will appear here</p>
                        <button
                          onClick={generatePreview}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                          Generate Preview
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex justify-between items-center pt-6 pb-4 border-t border-gray-200 mt-6 mb-4">
          <div>
            {errors.general && (
              <p className="text-sm text-red-600">{errors.general}</p>
            )}
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-6 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-3 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {saving ? 'Saving...' : template ? 'Update Template' : 'Create Template'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}