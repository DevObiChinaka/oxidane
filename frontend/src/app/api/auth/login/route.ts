import { NextRequest, NextResponse } from 'next/server';
import { API_ENDPOINTS } from '@/config/api';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    // Validate required fields
    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password are required' },
        { status: 400 }
      );
    }

    // Call Django backend - NEW OTP endpoint with better error handling
    const backendResponse = await fetch(API_ENDPOINTS.auth.loginWithOtp, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
      }),
    });

    const responseData = await backendResponse.json();

    if (!backendResponse.ok) {
      // Return enhanced error messages with specific codes
      return NextResponse.json(
        responseData,
        { status: backendResponse.status }
      );
    }

    return NextResponse.json(
      responseData,
      { status: 200 }
    );

  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}