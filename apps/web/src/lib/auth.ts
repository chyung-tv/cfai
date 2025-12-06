import NextAuth, { Session } from "next-auth";
import Google from "next-auth/providers/google";
import { PrismaAdapter } from "@auth/prisma-adapter";
import prisma from "@repo/db";

export const { handlers, signIn, signOut, auth } = NextAuth({
  adapter: PrismaAdapter(prisma),
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  session: {
    strategy: "database",
  },
  callbacks: {
    async session({ session, user }) {
      // Add hasAccess from database User to session
      if (session.user) {
        const dbUser = await prisma.user.findUnique({
          where: { id: user.id },
          select: { hasAccess: true },
        });

        // Add hasAccess to session user
        (session.user as any).hasAccess = dbUser?.hasAccess ?? false;
      }
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
});

/**
 * Type-safe helper to get user access status from session
 * @param session - NextAuth session object
 * @returns boolean indicating if user has access
 */
export function getUserAccess(session: Session | null): boolean {
  if (!session?.user) return false;
  return (session.user as any).hasAccess === true;
}
