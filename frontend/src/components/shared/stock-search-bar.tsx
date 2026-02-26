"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

interface StockSearchBarProps {
  variant?: "hero" | "compact";
  onSearch?: (symbol: string) => void;
  placeholder?: string;
}

export function StockSearchBar({
  variant = "compact",
  onSearch,
  placeholder = "Enter stock symbol (e.g., AAPL)",
}: StockSearchBarProps) {
  const router = useRouter();
  const [searchSymbol, setSearchSymbol] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const symbol = searchSymbol.trim().toUpperCase();

    if (symbol) {
      if (onSearch) {
        onSearch(symbol);
      } else {
        // Default behavior: navigate to analysis page
        router.push(`/analysis/${symbol}`);
      }
      setSearchSymbol("");
    }
  };

  const isHero = variant === "hero";

  return (
    <form
      onSubmit={handleSubmit}
      className={
        isHero ? "flex gap-2 max-w-2xl mx-auto" : "flex-1 max-w-md flex gap-2"
      }
    >
      <div className="relative flex-1">
        <Search
          className={`absolute left-3 top-1/2 -translate-y-1/2 ${
            isHero ? "h-5 w-5" : "h-4 w-4"
          } text-slate-400`}
        />
        <Input
          value={searchSymbol}
          onChange={(e) => setSearchSymbol(e.target.value)}
          placeholder={placeholder}
          className={isHero ? "pl-10 h-14 text-lg" : "pl-9 h-10"}
          required
        />
      </div>
      <Button
        type="submit"
        size={isHero ? "lg" : "sm"}
        className={isHero ? "h-14 px-8 text-lg" : "h-10"}
      >
        Analyze
      </Button>
    </form>
  );
}
