import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/config/api';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, otp } = body;

    // Validate required fields
    if (!email || !otp) {
      return NextResponse.json(
        { error: 'Email and OTP are required' },
        { status: 400 }
      );
    }

    // Validate OTP format (6 digits)
    if (!/^\d{6}$/.test(otp)) {
      return NextResponse.json(
        { error: 'OTP must be 6 digits' },
        { status: 400 }
      );
    }

    // Call Django backend to verify OTP
    const backendResponse = await fetch(API_ENDPOINTS.auth.verifyEmailOtp, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        otp,
      }),
    });

    const responseData = await backendResponse.json();

    if (!backendResponse.ok) {
      return NextResponse.json(
        { error: responseData.error || 'OTP verification failed' },
        { status: backendResponse.status }
      );
    }

    return NextResponse.json(
      { 
        message: responseData.message,
        user: responseData.user 
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