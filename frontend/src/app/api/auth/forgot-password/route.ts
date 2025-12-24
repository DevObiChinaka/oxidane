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

    // Call Django backend to send password reset email
    const backendResponse = await fetch(API_ENDPOINTS.auth.forgotPassword, {
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
        { error: responseData.error || 'Failed to send password reset email' },
        { status: backendResponse.status }
      );
    }

    return NextResponse.json(
      { 
        message: 'Password reset link sent to your email address.'
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