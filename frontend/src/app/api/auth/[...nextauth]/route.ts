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
        token.accessToken = account.access_token
        token.provider = account.provider
        
        // Send OAuth data to Django backend
        if (account.provider === 'google') {
          try {
            const userInfo = {
              email: user.email,
              name: user.name,
              picture: user.image,
              given_name: profile?.given_name || user.name?.split(' ')[0] || '',
              family_name: profile?.family_name || user.name?.split(' ').slice(1).join(' ') || '',
              sub: profile?.sub || user.id,
            }

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/oauth/`, {
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
            } else {
              console.error('Backend OAuth sync failed:', await response.text())
            }
          } catch (error) {
            console.error('Backend OAuth sync error:', error)
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
      return session
    },
  },
  session: {
    strategy: "jwt",
  },
})

export { handler as GET, handler as POST }