import { Button } from "@/components/ui/button";
import { TrendingUp } from "lucide-react";

export function Header() {
  return (
    <header className="border-b bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-8 w-8 text-blue-600" />
          <span className="text-2xl font-bold bg-linear-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            CFAI
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost">Login</Button>
          <Button>Sign Up</Button>
        </div>
      </div>
    </header>
  );
}
