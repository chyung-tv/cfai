"use client";

import { Button } from "@/components/ui/button";
import { StockSearchBar } from "@/components/shared/stock-search-bar";
import { TrendingUp, User } from "lucide-react";
import Link from "next/link";

export function AppHeader() {
  return (
    <header className="border-b bg-white/80 dark:bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between gap-4">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <TrendingUp className="h-8 w-8 text-blue-600" />
            <span className="text-2xl font-bold bg-linear-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              CFAI
            </span>
          </Link>

          <StockSearchBar
            variant="compact"
            placeholder="Search stock symbol..."
          />

          {/* Navigation */}
          <nav className="flex items-center gap-3 shrink-0">
            <Link href="/dashboard">
              <Button variant="ghost" size="sm">
                Dashboard
              </Button>
            </Link>
            <Button variant="ghost" size="sm">
              <User className="h-4 w-4 mr-2" />
              Profile
            </Button>
          </nav>
        </div>
      </div>
    </header>
  );
}
