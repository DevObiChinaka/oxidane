import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/config/api';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email } = body;

    // Validate required fields
    if (!email) {
      return NextResponse.json(
        { error: 'Email is required' },
        { status: 400 }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Invalid email format' },
        { status: 400 }
      );
    }

    // Call Django backend to resend OTP
    const backendResponse = await fetch(API_ENDPOINTS.auth.resendVerificationOtp, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
      }),
    });

    const responseData = await backendResponse.json();

    if (!backendResponse.ok) {
      return NextResponse.json(
        { error: responseData.error || 'Failed to resend OTP' },
        { status: backendResponse.status }
      );
    }

    return NextResponse.json(
      { 
        message: responseData.message,
        debug_otp: responseData.debug_otp // For development
      },
      { status: 200 }
    );

  } catch (error) {

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}