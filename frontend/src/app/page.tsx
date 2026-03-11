export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 p-6 dark:bg-zinc-950">
      <div className="w-full max-w-xl rounded border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <h1 className="text-xl font-semibold">CFAI Frontend</h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Portfolio Home is the primary product path. Maintenance module remains available for internal operations.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <a
            href="/portfolio"
            className="inline-flex rounded bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            Open Portfolio Home
          </a>
          <a
            href="/demo/analysis"
            className="inline-flex rounded border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
          >
            Open Internal Maintenance
          </a>
        </div>
      </div>
    </main>
  );
}
