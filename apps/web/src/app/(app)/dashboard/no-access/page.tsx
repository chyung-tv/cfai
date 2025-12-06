import { Button } from "@/components/ui/button";
import { ShieldAlert, Mail } from "lucide-react";
import Link from "next/link";

export default function NoAccessPage() {
  return (
    <div className="flex min-h-[calc(100vh-200px)] items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8 text-center">
        <div className="flex justify-center">
          <ShieldAlert className="h-20 w-20 text-amber-500" />
        </div>

        <div className="space-y-3">
          <h1 className="text-3xl font-bold tracking-tight">
            Beta Access Required
          </h1>
          <p className="text-lg text-muted-foreground">
            Thank you for your interest in CFAI! We&apos;re currently in closed
            beta and your account doesn&apos;t have access yet.
          </p>
        </div>

        <div className="rounded-lg border bg-muted/50 p-6 space-y-3">
          <div className="flex items-center justify-center gap-2 text-sm font-medium">
            <Mail className="h-4 w-4" />
            <span>Contact Us for Access</span>
          </div>
          <p className="text-sm text-muted-foreground">
            Please reach out to our team to request beta access:
          </p>
          <a
            href="mailto:beta@cfai.com"
            className="text-lg font-semibold text-blue-600 hover:underline"
          >
            beta@cfai.com
          </a>
        </div>

        <div className="pt-4">
          <Link href="/dashboard">
            <Button variant="outline" size="lg">
              Return to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
