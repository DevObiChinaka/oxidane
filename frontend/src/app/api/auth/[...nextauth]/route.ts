import NextAuth from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        try {
          // Call your Django backend to verify credentials
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          })

          if (!response.ok) {
            return null
          }

          const user = await response.json()
          
          return {
            id: user.id,
            email: user.email,
            name: user.name || user.first_name + ' ' + user.last_name,
            image: user.avatar,
          }
        } catch (error) {
          console.error('Authentication error:', error)
          return null
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account, profile }) {
      // Persist OAuth access token and user info
      if (account && user) {
        console.log('[NextAuth JWT] New authentication detected');
        console.log('[NextAuth JWT] Provider:', account.provider);
        console.log('[NextAuth JWT] User:', user.email);
        
        token.accessToken = account.access_token
        token.provider = account.provider
        
        // Send OAuth data to Django backend
        if (account.provider === 'google') {
          try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL;
            console.log('[NextAuth JWT] API URL:', apiUrl);
            
            if (!apiUrl) {
              console.error('[NextAuth JWT] NEXT_PUBLIC_API_URL is not set!');
              throw new Error('NEXT_PUBLIC_API_URL environment variable is missing');
            }

            const userInfo = {
              email: user.email,
              name: user.name,
              picture: user.image,
              given_name: profile?.given_name || user.name?.split(' ')[0] || '',
              family_name: profile?.family_name || user.name?.split(' ').slice(1).join(' ') || '',
              sub: profile?.sub || user.id,
            }

            console.log('[NextAuth JWT] Calling backend OAuth endpoint...');
            console.log('[NextAuth JWT] User info:', userInfo);

            const backendUrl = `${apiUrl}/api/auth/oauth/`;
            console.log('[NextAuth JWT] Full URL:', backendUrl);

            const response = await fetch(backendUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                provider: account.provider,
                access_token: account.access_token,
                user_info: userInfo,
              }),
            })
            
            console.log('[NextAuth JWT] Backend response status:', response.status);
            
            if (response.ok) {
              const backendUser = await response.json()
              console.log('[NextAuth JWT] Backend sync successful');
              console.log('[NextAuth JWT] Backend user ID:', backendUser.id);
              console.log('[NextAuth JWT] Has access token:', !!backendUser.access_token);
              console.log('[NextAuth JWT] Has refresh token:', !!backendUser.refresh_token);
              
              token.backendUser = backendUser
              token.backendId = backendUser.id
              token.backendAccessToken = backendUser.access_token
              token.backendRefreshToken = backendUser.refresh_token
            } else {
              const errorText = await response.text()
              console.error('[NextAuth JWT] Backend OAuth sync failed');
              console.error('[NextAuth JWT] Status:', response.status);
              console.error('[NextAuth JWT] Response:', errorText);
            }
          } catch (error) {
            console.error('[NextAuth JWT] Backend OAuth sync error:', error);
            console.error('[NextAuth JWT] Error details:', error instanceof Error ? error.message : String(error));
          }
        }
      }
      
      return token
    },
    async session({ session, token }) {
      // Send properties to the client
      session.accessToken = token.accessToken as string
      session.provider = token.provider as string
      session.backendUser = token.backendUser
      session.backendAccessToken = token.backendAccessToken as string
      session.backendRefreshToken = token.backendRefreshToken as string
      
      return session
    },
  },
  session: {
    strategy: "jwt",
  },
})

export { handler as GET, handler as POST }