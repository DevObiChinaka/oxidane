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
          return null
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account, profile }) {
      // Persist OAuth access token and user info
      if (account && user) {
        token.accessToken = account.access_token
        token.provider = account.provider
        
        // Send OAuth data to Django backend
        if (account.provider === 'google') {
          try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL;
            
            if (!apiUrl) {
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

            const backendUrl = `${apiUrl}/auth/oauth/`;

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
            
            if (response.ok) {
              const backendUser = await response.json()
              
              token.backendUser = backendUser
              token.backendId = backendUser.id
              token.backendAccessToken = backendUser.access_token
              token.backendRefreshToken = backendUser.refresh_token
            }
          } catch (error) {
            // Silent fail - OAuth will still work on frontend
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